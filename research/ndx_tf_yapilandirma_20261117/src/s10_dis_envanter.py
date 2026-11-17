"""Adım 10 — ev dizinindeki (proje dışı) TÜM NASDAQ adlı veri dosyalarının hükmü.

Sınıflar: mum değil (model/rapor/sinyal/olay/temel veri) · türetilemez (günlük/haftalık/aylık/1-4 sa) ·
bilinen beslemenin kopyası (DUKA / MT5 / EET30 / NQ / USTEC — saat yorumu UTC, NY+7, Athens, NY-kapanış denenir) ·
bilinmeyen. Kopyalarda bizim beslemede OLMAYAN işlem günü sayılır (varsa kullanılmamış veri demektir).
Çıktı: results/s10_dis_envanter.csv + .json; DOSYA_HUKUMLERI.md'ye s06 ekler.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import dis_okuyucu as R  # noqa: E402
import kaynak as K  # noqa: E402
import s03_uret as U  # noqa: E402
import s05_ek_kaynak as S  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
H = R.HOME
NAME_KEYS = ("nasdaq", "ndx", "nas100", "ustec", "us100", "usatech", "nsxusd", "ustech")
DATA_EXT = {".csv", ".parquet", ".json", ".zip", ".gz", ".txt", ".xlsx", ".pkl", ".feather", ".npz"}
SKIP_DIRS = ("Desktop/panel/", "Library/", "node_modules/", ".Trash/", "site-packages/", "dukascopy_us100/",
             ".vscode/", ".claude/", "__pycache__/")
NOT_CANDLE_KEYS = ("model", "event", "signal", "trade", "backtest", "policy", "news", "fundament", "report",
                   "metric", "scored", "playbook", "label", "audit", "feature_farklari", "kernel", "symbols",
                   "fear", "calculator", "wave", "pattern", "outcome", "dataset", "eksik")
SAMPLE_ROWS = 200_000
MAX_READ_BYTES = 2_000_000_000


def candidates() -> list[Path]:
    out = []
    for p in H.rglob("*"):
        try:
            if not p.is_file() or p.suffix.lower() not in DATA_EXT:
                continue
        except OSError:
            continue
        rel = str(p.relative_to(H))
        if any(s in rel for s in SKIP_DIRS) or not (p.name.lower().startswith("nq") or any(k in p.name.lower() for k in NAME_KEYS)) \
                or any(k in p.name.lower() for k in ("gdaxi", "dax", "xau", "oil", "spx", "dji")):
            continue
        out.append(p)
    return sorted(out)


def load_any(p: Path) -> pd.DataFrame | None:
    """→ (wall, open, high, low, close) ya da mum değilse None."""
    suf = p.suffix.lower()
    try:
        if suf in (".csv", ".txt"):
            return R.read_ohlc_sample(p, SAMPLE_ROWS)
        if suf == ".parquet":
            d = pd.read_parquet(p)
        elif suf == ".pkl":
            with open(p, "rb") as h:
                d = pickle.load(h)
            if not isinstance(d, pd.DataFrame):
                return None
        else:
            return None
    except Exception:  # noqa: BLE001 — okunamayan/yabancı biçim: mum değil sayılır
        return None
    return R.frame_to_ohlc(d)


def references() -> dict[str, dict[int, pd.DataFrame]]:
    duka = K.load_duka_1m()
    mt = U.mt5_sources()
    h1 = U.union([K.load_mt5_native("H1", K.MT5_DIR_A), U._fresh("H1")], "H1")
    eet = pd.read_parquet(BASE / "out/ek/EET30_kalibre.parquet")
    nq = pd.read_parquet(BASE / "out/ek/NQ_kalibre.parquet")
    us = U.ustec_1m()
    refs = {"DUKA": {1: duka}, "MT5": {1: mt["M1"], 5: mt["M5"], 15: mt["M15"], 30: mt["M30"], 60: h1},
            "EET30": {30: eet}, "NQ": {5: nq}, "USTEC": {1: us}}
    for tf in (5, 15, 30, 60, 240):
        refs["DUKA"][tf] = S.regroup(duka, tf)
    m30x = K.load_duka_m30_export()  # DUKA beslemesinin 2016-03 → 2018-01 parçası bundan üretildi
    refs["DUKA"][30] = pd.concat([m30x[m30x["t"] < refs["DUKA"][30]["t"].min()], refs["DUKA"][30]]).reset_index(drop=True)
    refs["EET30"][60] = S.regroup(eet, 60)
    refs["USTEC"][5] = S.regroup(us, 5)
    return refs


def interpretations(wall: pd.Series, tf: int) -> dict[str, np.ndarray]:
    base = (wall.astype("int64") // 10**9).to_numpy()
    out = {"UTC": base}
    for name, zone, lab in (("NY+7", None, 0), ("Athens", "Europe/Athens", 0), ("NY kapanış", "America/New_York", tf)):
        try:
            if zone is None:
                out[name] = K.server_to_utc(base)
            else:
                loc = wall.dt.tz_localize(zone, ambiguous="NaT", nonexistent="NaT")
                t = (loc.dt.tz_convert("UTC").astype("int64") // 10**9).to_numpy(dtype=float) - lab * 60
                t[loc.isna().to_numpy()] = np.nan
                out[name] = t
        except Exception:  # noqa: BLE001
            continue
    return out


def identify(df: pd.DataFrame, tf: int, refs: dict) -> dict:
    best = {"besleme": None, "r": -1.0}
    for interp, t in interpretations(df["wall"], tf).items():
        c = pd.DataFrame({"t": t, "close": df["close"].to_numpy(), "high": df["high"].to_numpy()}).dropna()
        c["t"] = c["t"].astype(np.int64)
        c = c.drop_duplicates("t")
        for feed, by_tf in refs.items():
            if tf not in by_tf:
                continue
            m = c.merge(by_tf[tf][["t", "close", "high"]], on="t", suffixes=("_f", "_r"))
            if len(m) < 200:
                continue
            r = float(m["close_f"].pct_change().corr(m["close_r"].pct_change()))
            eq = float(((m["close_f"] - m["close_r"]).abs() <= 0.006).mean())
            score = (round(eq, 3), r)  # kimlik: önce birebir eşitlik oranı, sonra korelasyon
            if score > (round(best.get("esit_%", -1) / 100, 3), best["r"]):
                best = {"besleme": feed, "saat": interp, "r": round(r, 4), "esit_%": round(100 * eq, 2),
                        "ortak": int(len(m)), "seviye_farki": round(float((m["close_f"] - m["close_r"]).median()), 2),
                        "t_utc": c["t"].to_numpy()}
    return best


def project_twin(p: Path) -> str | None:
    """Aynı adlı dosya proje klasöründe varsa ve md5'i aynıysa → onun yolu."""
    import hashlib
    proj = H / "Desktop/panel"
    for q in proj.rglob(p.name):
        if "/.claude/" in str(q) or q.stat().st_size != p.stat().st_size:
            continue
        h = [hashlib.md5(x.read_bytes()).hexdigest() for x in (p, q)]
        if h[0] == h[1]:
            return str(q.relative_to(proj))
    return None


def wide_table(p: Path, refs: dict) -> dict:
    """Çok-TF geniş tablo (open_1, open_5, … open_1440): 1 dk bölümü DUKA ile kıyaslanır."""
    x = pd.read_csv(p, usecols=["datetime", "close_1"])
    x = x[x["close_1"] > 0]
    x["t"] = pd.to_datetime(x["datetime"]).astype("int64") // 10**9
    m = x.merge(refs["DUKA"][1][["t", "close"]], on="t")
    eq = float(((m["close_1"] - m["close"]).abs() <= 0.006).mean()) if len(m) else 0.0
    return {"tf_dk": 1, "besleme": "DUKA", "esit_%": round(100 * eq, 2), "ortak": int(len(m)),
            "hukum": f"çok-TF geniş birleşik tablo (Dukascopy dışa aktarımlarından; dolu 1 dk satırı {len(x)}, DUKA ile eşit "
                     f"%{round(100 * eq, 1)}) — yeni veri yok"}


MAIN_SOURCES = {(H / "Desktop/Trading Projeleri/nasdaq/nasdaq100_30min_full.csv").resolve():
                "ANA KAYNAK: EET30 beslemesi (haftalık kalibre, reddedilen haftalar s08'de)",
                (H / "Desktop/Trading Projeleri/nasdaq/NQ_5Years_8_11_2024.csv").resolve():
                "ANA KAYNAK: NQ beslemesi (haftalık kalibre, reddedilen haftalar s08'de)"}
_NQ_WALL: pd.DataFrame | None = None


def nq_wall_identity(df: pd.DataFrame, tf: int) -> dict | None:
    """NQ_5Years'tan (karışık saat ekseniyle) yeniden örneklenmiş dosya mı? Ham dosyanın DUVAR saatinde kıyaslanır."""
    global _NQ_WALL
    if _NQ_WALL is None:
        _NQ_WALL = R.read_ohlc(H / "Desktop/Trading Projeleri/nasdaq/NQ_5Years_8_11_2024.csv")
    raw = _NQ_WALL
    best = None
    for lab in (0, 5):  # ham dosya kapanış etiketli: türev açılışa çevirmiş olabilir
        t = (raw["wall"].astype("int64") // 10**9).to_numpy() - lab * 60
        k = t - t % (tf * 60)
        g = pd.DataFrame({"k": k, "c": raw["close"].to_numpy(), "h": raw["high"].to_numpy()}).groupby("k").agg(c=("c", "last"), h=("h", "max"))
        f = pd.DataFrame({"k": (df["wall"].astype("int64") // 10**9).to_numpy(), "c": df["close"].to_numpy(), "h": df["high"].to_numpy()})
        m = f.merge(g.reset_index(), on="k", suffixes=("_f", "_r"))
        if len(m) < 200:
            continue
        eq = float(((m["c_f"] - m["c_r"]).abs() <= 0.006).mean())
        if best is None or eq > best[0]:
            best = (eq, len(m))
    if best and best[0] >= 0.95:
        return {"besleme": "NQ(ham duvar saati)", "esit_%": round(100 * best[0], 2), "ortak": best[1],
                "hukum": "NQ_5Years türevi (yeniden örneklenmiş; ham dosyanın karışık saat eksenini taşır) — yeni veri yok"}
    return None


def main() -> None:
    refs = references()
    feed_days = {f: set(np.unique(S.trading_day(np.concatenate([v["t"].to_numpy() for v in by.values()]))))
                 for f, by in refs.items()}
    rows = []
    for p in candidates():
        rel = "~/" + str(p.relative_to(H))
        size = p.stat().st_size
        row = {"dosya": rel, "boyut_MB": round(size / 1e6, 1)}
        low = p.name.lower()
        if "/models/" in rel or any(k in low for k in NOT_CANDLE_KEYS):
            rows.append(row | {"hukum": "mum değil (ad: model/sinyal/olay/rapor/temel veri)"})
            continue
        if p.suffix.lower() in (".zip", ".gz", ".json", ".xlsx", ".npz", ".feather") or size > MAX_READ_BYTES:
            rows.append(row | {"hukum": "arşiv/biçim dışı — içeriği diskte açık kopya olarak ayrıca sınandı" if p.suffix.lower() == ".zip"
                               else "okunmadı (biçim/boyut)"})
            continue
        twin = project_twin(p)
        if twin:
            rows.append(row | {"hukum": f"projedeki {twin} dosyasının birebir kopyası (md5) — orada sınandı"})
            continue
        if p.suffix.lower() == ".csv" and "open_1," in open(p, errors="replace").readline():
            rows.append(row | wide_table(p, refs))
            continue
        df = load_any(p)
        if df is None or len(df) < 50:
            rows.append(row | {"hukum": "mum değil (OHLC sütunu/zaman yok)"})
            continue
        tf = R.tf_minutes(df)
        row |= {"tf_dk": tf, "bas": str(df["wall"].min())[:16], "bit": str(df["wall"].max())[:16], "orneklenen_bar": len(df)}
        if tf >= 1440 or tf in (120, 240) or tf == 0:
            rows.append(row | {"hukum": f"türetilemez ({tf} dk: 2/3/90/210 bundan kurulamaz)"})
            continue
        if p.resolve() in MAIN_SOURCES:
            rows.append(row | {"hukum": MAIN_SOURCES[p.resolve()]})
            continue
        idn = identify(df, tf, refs)
        if (idn["besleme"] is None or idn.get("esit_%", 0) < 95) and tf % 5 == 0:
            w = nq_wall_identity(df, tf)
            if w:
                rows.append(row | w)
                print(rel[:90], w["hukum"])
                continue
        t_utc = idn.pop("t_utc", None)
        row |= {k: v for k, v in idn.items()}
        if 30 % tf:  # 90 ve 210 ancak 30un bölenlerinden (1,2,3,5,6,10,15,30) kurulur; 60 dk vb. yalnız kimlik
            row["hukum"] = (f"türetilemez ({tf} dk: 90/210 bunun katı değil) · kimlik {idn['besleme']}"
                            if idn["besleme"] and idn["r"] >= 0.9 else f"türetilemez ({tf} dk)")
        elif idn["besleme"] is None or idn["r"] < 0.9:
            row["hukum"] = "bilinmeyen besleme / saat ekseni eşleşmedi"
        else:
            days = set(np.unique(S.trading_day(t_utc))) if t_utc is not None else set()
            extra = len(days - feed_days[idn["besleme"]])
            kind = "kopya" if idn["esit_%"] >= 95 else "türev (yeniden örneklenmiş/yuvarlanmış/indikatörlü)"
            row |= {"beslemede_olmayan_gun": extra,
                    "hukum": f"{idn['besleme']} {kind}" + (f" — {extra} ek gün" if extra else " — yeni gün yok")}
        rows.append(row)
        print(rel[:90], row["hukum"])
    out = pd.DataFrame(rows)
    out.to_csv(BASE / "results/s10_dis_envanter.csv", index=False)
    (BASE / "results/s10_dis_envanter.json").write_text(json.dumps(
        {"dosya": len(out), "hukum_dagilimi": out["hukum"].str.split(" —").str[0].value_counts().to_dict()}, indent=1, ensure_ascii=False))
    print(out["hukum"].str.split(" —").str[0].value_counts())


if __name__ == "__main__":
    main()
