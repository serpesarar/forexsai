"""tazele.py — ileri gölge için veriyi uzatır; mevcut satırlara dokunmaz, yalnız SONA ekler (tarihsel yeniden üretim bozulmaz).

python tazele.py mt5      # kutudan NAS100/US500/US30/US2000 M30 son 650 bar (salt-okuma, emir yok) → csv.gz sonuna ekle
python tazele.py makro    # yfinance ^VIX, ^VIX3M, QQQ günlük → parquet sonuna ekle
python tazele.py hepsi
İlk yazımda özgün dosya `<ad>.bak_20261119` olarak saklanır (git dışı).
"""
from __future__ import annotations

import gzip
import io
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/fx_secim_20261113"))
MT5_DIR = ROOT / "research/c1_turev_20261105/data/mt5"
SYMS = ["NAS100", "US500", "US30", "US2000"]
NBARS = 650                     # ≈ 14 işlem günü; kutu çıktısı uzun olunca kırpılıyor → sembol başına ayrı iş
MAKRO = {"^VIX": ROOT / "research/qs03_akis_takvim_20261111/data/VIX.parquet",
         "^VIX3M": ROOT / "research/son_rapor_20261118/VIX3M.parquet",
         "QQQ": ROOT / "research/nq_yapi2_20261118/data/QQQ.parquet"}
BAK = ".bak_20261119"

CODE = r'''import sys,json,base64,zlib,time
sys.path.insert(0,"remote_agent")
import agent_config as c, MetaTrader5 as m
assert m.initialize(getattr(c,"MT5_TERMINAL_PATH",None)),m.last_error()
ai=m.account_info(); out={"_hesap":[ai.login,ai.server],"_terminal":m.terminal_info().path}
for s in __SYMS__:
  m.symbol_select(s,True); time.sleep(0.3)
  r=m.copy_rates_from_pos(s,m.TIMEFRAME_M30,1,__N__)
  out[s]=[[int(x["time"]),float(x["open"]),float(x["high"]),float(x["low"]),float(x["close"]),int(x["tick_volume"]),int(x["spread"])] for x in r] if r is not None else []
t=m.symbol_info_tick("NAS100"); out["_srv_minus_utc_s"]=int(round((t.time-time.time())/900)*900) if t else None
print("WTI_DATA_BEGIN"+base64.b64encode(zlib.compress(json.dumps(out,separators=(",",":")).encode(),9)).decode()+"WTI_DATA_END");m.shutdown()
'''


def backup(p: Path) -> None:
    b = p.with_name(p.name + BAK)
    if not b.exists():
        shutil.copy2(p, b)


def mt5() -> None:
    from kutu import run
    for s in SYMS:
        data = run(CODE.replace("__SYMS__", repr([s])).replace("__N__", str(NBARS)), f"korku gölge M30 tazeleme {s}", timeout=600)
        print(s, "hesap", data["_hesap"], "sunucu−UTC sn", data["_srv_minus_utc_s"])
        p = MT5_DIR / f"{s}_M30.csv.gz"
        old = pd.read_csv(p)
        new = pd.DataFrame(data[s], columns=["t", "o", "h", "l", "c", "v", "sp"])
        if new.empty:
            print(s, "kutudan bar gelmedi")
            continue
        last = int(old.t.max())
        # özgün dosyanın son barı dışa aktarım anında oluşmakta olabilir → yalnız onu yenisiyle değiştir
        both = new[new.t == last]
        add = new[new.t > last]
        merged = old.copy()
        if len(both):
            merged = merged[merged.t != last]
            add = pd.concat([both, add])
        merged = pd.concat([merged, add]).sort_values("t").drop_duplicates("t")
        if len(merged) == len(old) and add.empty:
            print(s, "yeni bar yok")
            continue
        if new.t.min() > last:
            print(s, "UYARI: boşluk var — kutudan gelen ilk bar eski son bardan sonra; NBARS artırılmalı")
        backup(p)
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as g:
            g.write(merged.to_csv(index=False).encode())
        p.write_bytes(buf.getvalue())
        print(s, "eklenen", len(add) - len(both), "son", pd.to_datetime(merged.t.max(), unit="s"), "(sunucu saati)")


def makro() -> None:
    import yfinance as yf
    for tk, p in MAKRO.items():
        old = pd.read_parquet(p)
        start = (old.index.max() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
        d = yf.Ticker(tk).history(start=start, auto_adjust=False)
        if d.empty:
            print(tk, "veri gelmedi")
            continue
        d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
        d = d[d.index > old.index.max()]
        today = pd.Timestamp.now(tz="America/New_York").normalize().tz_localize(None)
        if pd.Timestamp.now(tz="America/New_York").hour < 17:
            d = d[d.index < today]            # bugünün günlük barı henüz kesin değil
        d = d.reindex(columns=old.columns)
        if d.empty:
            print(tk, "yeni gün yok, son", old.index.max().date())
            continue
        backup(p)
        pd.concat([old, d]).to_parquet(p)
        print(tk, "eklenen", len(d), "son", d.index.max().date())


if __name__ == "__main__":
    arg = sys.argv[1]
    if arg in ("mt5", "hepsi"):
        mt5()
    if arg in ("makro", "hepsi"):
        makro()
