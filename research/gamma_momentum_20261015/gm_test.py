"""GM-01 — gamma koşullu son yarım saat momentumu (NDX). Ön-kayıt: PROTOCOL.md (değiştirmeden uygular).

Çalıştır: python3 research/gamma_momentum_20261015/gm_test.py
Çıktı: results/gunler_30m.csv, gunler_1h.csv, sonuc.json + ekrana tablolar.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
NY = "America/New_York"
DEV_START, DEV_END = pd.Timestamp("2021-06-29").date(), pd.Timestamp("2025-11-30").date()
HO_START, HO_END = pd.Timestamp("2025-12-01").date(), pd.Timestamp("2026-10-02").date()
B = 10_000
rng = np.random.default_rng(20261015)


def half_days(years) -> set:
    s = set()
    for y in years:
        for m, dd in ((7, 3), (12, 24)):
            d = pd.Timestamp(year=y, month=m, day=dd)
            if d.weekday() < 5:
                s.add(d.date())
        nov = pd.date_range(f"{y}-11-01", f"{y}-11-30")
        thu = [d for d in nov if d.weekday() == 3][3]
        s.add((thu + pd.Timedelta(days=1)).date())
    return s


def trading_days() -> set:
    m = pd.read_csv(ROOT / "research/ndx_gate_forge/data/macro_daily_patched.csv", usecols=["date", "NDXCASH_close"]).dropna()
    days = set(pd.to_datetime(m.date).dt.date)
    for d in pd.bdate_range("2026-10-01", "2026-10-02"):        # dosya 09-30'da bitiyor; tatil yok
        days.add(d.date())
    return days


def bars(tf: str) -> pd.DataFrame:
    if tf == "30m":
        a = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/long_30m_utc.parquet")[["ts", "close"]]
        b = pd.read_parquet(ROOT / "research/ndx_pattern_motifs/data/bars_15m.parquet")[["ts", "close"]]
        b = b[b.ts.dt.minute % 30 == 15].copy()                  # 30m kovasının ikinci 15m barı → kova kapanışı
        b["ts"] = b.ts - pd.Timedelta(minutes=15)
        ov = a.merge(b, on="ts", suffixes=("", "_15"))
        ov = ov[(ov.ts >= "2026-06-01") & (ov.ts < "2026-07-15")]
        hiz = float((np.abs(ov.close - ov.close_15) <= 0.5).mean()) if len(ov) else np.nan
        d = pd.concat([a, b[b.ts >= "2026-07-15"]]).sort_values("ts").drop_duplicates("ts")
        d.attrs["hizalama_uyum"] = hiz
        return d
    return pd.read_parquet(ROOT / "research/ndx_gate_forge/data/long_1h_utc.parquet")[["ts", "close"]]


def daily_table(tf: str) -> pd.DataFrame:
    d = bars(tf)
    ny = d.ts.dt.tz_convert(NY)
    d = d.assign(date=ny.dt.date, hm=ny.dt.strftime("%H:%M"))
    if tf == "30m":
        p_ref = d[d.hm == "15:00"].set_index("date").close       # 15:00 barının kapanışı = 15:30 fiyatı
        p_cl = d[d.hm == "15:30"].set_index("date").close        # 15:30 barının kapanışı = 16:00
    else:
        p_ref = d[d.hm == "14:00"].set_index("date").close       # 14:00 barı kapanışı = 15:00
        p_cl = d[d.hm == "15:00"].set_index("date").close        # 15:00 barı kapanışı = 16:00
    t = pd.DataFrame({"ref": p_ref, "cl": p_cl}).dropna()
    tdays, hd = trading_days(), half_days(range(2015, 2027))
    t = t[t.index.isin(tdays)]
    t.index = pd.to_datetime(t.index)
    t["prev_cl"] = t.cl.shift(1); t["prev_date"] = t.index.to_series().shift(1)
    t = t[(t.index - t.prev_date).dt.days <= 4]
    excl = set(hd) | {(pd.Timestamp(x) + pd.offsets.BDay(1)).date() for x in hd}
    t = t[[x not in excl for x in t.index.date]]
    t["rROD"] = np.log(t.ref / t.prev_cl); t["rL"] = np.log(t.cl / t.ref)
    g = pd.read_csv(HERE / "data/DIX.csv", parse_dates=["date"]).sort_values("date")
    gd = g.date.values; idx = np.searchsorted(gd, t.index.values, side="left") - 1   # d'den ÖNCEKİ son GEX
    t["gex_prev"] = np.where(idx >= 0, g.gex.values[np.clip(idx, 0, None)], np.nan)
    gl = g.set_index("date").gex
    q20 = gl.rolling(252, min_periods=126).quantile(0.20)
    t["gex_q20_prev"] = np.where(idx >= 0, q20.values[np.clip(idx, 0, None)], np.nan)
    t["kazanc"] = np.sign(t.rROD) * t.rL
    t["kazanc_puan"] = np.sign(t.rROD) * (t.cl - t.ref)
    t["isabet"] = (np.sign(t.rROD) == np.sign(t.rL)).astype(float)
    return t.dropna(subset=["rROD", "rL", "gex_prev"])


def boot_p(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    if len(x) < 5:
        return np.nan
    m = x[rng.integers(0, len(x), size=(B, len(x)))].mean(1)
    return float((m > 0).mean())


def boot_diff(a: np.ndarray, b: np.ndarray) -> float:
    ma = a[rng.integers(0, len(a), size=(B, len(a)))].mean(1); mb = b[rng.integers(0, len(b), size=(B, len(b)))].mean(1)
    return float((ma - mb > 0).mean())


def week_boot_p(t: pd.DataFrame) -> float:
    wk = t.index.to_period("W").astype(str).to_numpy(); u, inv = np.unique(wk, return_inverse=True)
    S = np.bincount(inv, t.kazanc.to_numpy()); N = np.bincount(inv)
    i = rng.integers(0, len(u), size=(B, len(u)))
    return float(((S[i].sum(1) / N[i].sum(1)) > 0).mean())


def summary(t: pd.DataFrame) -> dict:
    if len(t) == 0:
        return {"gun": 0}
    half = t.index >= t.index[len(t) // 2]
    beta = float(np.polyfit(t.rROD, t.rL, 1)[0]) if len(t) > 5 else np.nan
    return {"gun": int(len(t)), "ort_kazanc_bp": 1e4 * float(t.kazanc.mean()), "ort_puan": float(t.kazanc_puan.mean()),
            "isabet_%": 100 * float(t.isabet.mean()), "P_gun": boot_p(t.kazanc.to_numpy()),
            "P_hafta_blok": week_boot_p(t) if len(t) > 10 else np.nan,
            "yari1_bp": 1e4 * float(t.kazanc[~half].mean()), "yari2_bp": 1e4 * float(t.kazanc[half].mean()), "beta": beta}


def run(tf: str) -> dict:
    t = daily_table(tf)
    t.to_csv(OUT / f"gunler_{tf}.csv")
    res = {}
    for nm, (a, b) in {"gelistirme": (DEV_START, DEV_END), "dogrulama": (HO_START, HO_END)}.items():
        x = t[(t.index.date >= a) & (t.index.date <= b)]
        if tf == "1h" and nm == "gelistirme":
            x = t[t.index.date <= DEV_END]                         # ikincil vekil: 2016 → 2025-11
        neg, pos = x[x.gex_prev < 0], x[x.gex_prev >= 0]
        low = x[x.gex_prev <= x.gex_q20_prev]
        res[nm] = {"GEX<0": summary(neg), "GEX>=0": summary(pos), "tum": summary(x), "GEX_alt%20(ikincil)": summary(low),
                   "H2_P_neg_gt_pos": boot_diff(neg.kazanc.to_numpy(), pos.kazanc.to_numpy()) if len(neg) > 5 else np.nan}
    return res


def main() -> None:
    out = {"30m": run("30m"), "1h": run("1h"), "hizalama_15m_30m": bars("30m").attrs.get("hizalama_uyum")}
    (OUT / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=float))
    for tf in ("30m", "1h"):
        for per in ("gelistirme", "dogrulama"):
            r = out[tf][per]
            print(f"\n=== {tf} {per}  (H2 P neg>pos = {r['H2_P_neg_gt_pos']}) ===")
            print(pd.DataFrame({k: v for k, v in r.items() if isinstance(v, dict)}).T.round(3).to_string())
    print("\n15m→30m hizalama uyumu:", out["hizalama_15m_30m"])


if __name__ == "__main__":
    main()
