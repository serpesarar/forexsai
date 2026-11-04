"""USDT-M perp BTCUSDT aggTrades → 1 saniyelik akış barları (son 6 ay), akış halinde.

Her gün: zip indir → SHA256 doğrula → CSV oku → 1s bara topla → gün parquet'i yaz
→ zip'i HEMEN sil. Disk kullanımı = eşzamanlı işçi sayısı × ~65 MB.

aggTrades sütunları: agg_trade_id, price, quantity, first_trade_id, last_trade_id,
transact_time, is_buyer_maker. is_buyer_maker=True → alıcı pasif (maker) → agresör
SATICI (taker sell); False → taker BUY.

1s bar (ts = saniye başlangıcı, UTC, [ts, ts+1s)):
  open/high/low/close/vwap (USDT), buy_qty/sell_qty (BTC, taker yönü),
  buy_quote/sell_quote (USDT), n_agg (aggTrade adedi), n_trades (Σ last-first+1),
  max_agg_qty (BTC, saniyedeki en büyük tek aggTrade), large_buy_qty/large_sell_qty
  (≥ LARGE_BTC BTC'lik aggTrade'lerin taker hacmi). İşlem olmayan saniye = satır yok.

Kullanım: python -I 03_aggtrades_stream.py <listing_json> <tmp_zip_dir> <out_dir> <from> <to> [workers]
"""
from __future__ import annotations
import hashlib, io, json, sys, time, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

BASE = "https://data.binance.vision/"
PREFIX = "data/futures/um/daily/aggTrades/BTCUSDT/"
COLS = ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id", "transact_time", "is_buyer_maker"]
LARGE_BTC = 5.0


def fetch(url: str, retries: int = 6) -> bytes:
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if i == retries - 1:
                raise
            time.sleep(3 * (i + 1))
    raise RuntimeError


def parse(raw: bytes) -> tuple[pd.DataFrame, str]:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist() if n.endswith(".csv")]
        assert len(names) == 1, z.namelist()
        b = z.read(names[0])
    header = not b[:1].isdigit()
    df = pd.read_csv(io.BytesIO(b), header=None, names=COLS, skiprows=1 if header else 0,
                     usecols=["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id", "transact_time", "is_buyer_maker"],
                     dtype={"price": "float64", "quantity": "float64", "transact_time": "int64",
                            "first_trade_id": "int64", "last_trade_id": "int64", "agg_trade_id": "int64"})
    t = df["transact_time"]
    unit = "us" if t.iloc[0] > 1e15 else "ms"
    assert ((t > 1e15) == (unit == "us")).all(), "karışık birim"
    df["sec"] = (t // (1_000_000 if unit == "us" else 1000)).astype("int64")
    ibm = df["is_buyer_maker"]
    if ibm.dtype != bool:
        ibm = ibm.astype(str).str.strip().str.lower().map({"true": True, "false": False})
        assert ibm.notna().all()
    df["ibm"] = ibm.astype(bool)
    return df, f"{unit}{' header' if header else ''}"


def to_1s(df: pd.DataFrame) -> pd.DataFrame:
    q, p = df["quantity"].to_numpy(), df["price"].to_numpy()
    buy = ~df["ibm"].to_numpy()
    large = q >= LARGE_BTC
    x = pd.DataFrame({
        "sec": df["sec"].to_numpy(), "price": p, "qty": q, "quote": p * q,
        "buy_qty": np.where(buy, q, 0.0), "sell_qty": np.where(buy, 0.0, q),
        "buy_quote": np.where(buy, p * q, 0.0), "sell_quote": np.where(buy, 0.0, p * q),
        "large_buy_qty": np.where(buy & large, q, 0.0), "large_sell_qty": np.where(~buy & large, q, 0.0),
        "n_tr": (df["last_trade_id"] - df["first_trade_id"] + 1).to_numpy(),
    })
    g = x.groupby("sec", sort=True)
    out = pd.DataFrame({
        "open": g["price"].first(), "high": g["price"].max(), "low": g["price"].min(), "close": g["price"].last(),
        "quote": g["quote"].sum(), "qty": g["qty"].sum(),
        "buy_qty": g["buy_qty"].sum(), "sell_qty": g["sell_qty"].sum(),
        "buy_quote": g["buy_quote"].sum(), "sell_quote": g["sell_quote"].sum(),
        "n_agg": g["qty"].size().astype("int32"), "n_trades": g["n_tr"].sum().astype("int32"),
        "max_agg_qty": g["qty"].max(),
        "large_buy_qty": g["large_buy_qty"].sum(), "large_sell_qty": g["large_sell_qty"].sum(),
    })
    out["vwap"] = out["quote"] / out["qty"]
    out = out.drop(columns=["quote", "qty"]).reset_index()
    out.insert(0, "ts", pd.to_datetime(out.pop("sec"), unit="s", utc=True))
    return out


def day(key: str, tmp: Path, out: Path) -> str:
    name = key.rsplit("/", 1)[-1]
    dest = out / name.replace(".zip", "_1s.parquet")
    if dest.exists():
        return f"{name}\tcached"
    try:
        ck = fetch(BASE + key + ".CHECKSUM").decode().split()[0].strip()
        raw = fetch(BASE + key)
        zpath = tmp / name
        zpath.write_bytes(raw)  # yalnız disk-bütçesi gözlemi için; hemen silinir
        h = hashlib.sha256(raw).hexdigest()
        if h != ck:
            zpath.unlink()
            return f"{name}\tCHECKSUM-MISMATCH"
        df, unit = parse(raw)
        zpath.unlink()
        del raw
        ids = df["agg_trade_id"].to_numpy()
        id_gaps = int((np.diff(ids) != 1).sum())
        bars = to_1s(df)
        bars.to_parquet(dest, index=False)
        return (f"{name}\tok\t{unit}\trows={len(df)}\tsec_bars={len(bars)}\tagg_id_gaps={id_gaps}\t"
                f"first={df['sec'].iloc[0]}\tlast={df['sec'].iloc[-1]}")
    except Exception as e:  # noqa: BLE001
        return f"{name}\tERROR {e}"


def main() -> None:
    listing = json.load(open(sys.argv[1]))
    tmp, out = Path(sys.argv[2]), Path(sys.argv[3])
    a, b = sys.argv[4], sys.argv[5]
    workers = int(sys.argv[6]) if len(sys.argv) > 6 else 3
    tmp.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    keys = [x["key"] for x in listing[PREFIX] if a <= x["key"][-14:-4] <= b]
    log = out / "aggtrades_log.tsv"
    with ThreadPoolExecutor(workers) as ex, open(log, "a") as fh:
        for r in ex.map(lambda k: day(k, tmp, out), keys):
            fh.write(r + "\n")
            fh.flush()
            print(r, flush=True)


if __name__ == "__main__":
    main()
