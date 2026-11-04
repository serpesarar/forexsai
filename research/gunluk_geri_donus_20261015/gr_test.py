"""GR-01 — günlük endeks geri dönüşü. Ön-kayıt: PROTOCOL.md. Çalıştır: python3 research/gunluk_geri_donus_20261015/gr_test.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/mum_eslestirme_20261012"))
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
DEV_END, HO_START = pd.Timestamp("2025-11-30"), pd.Timestamp("2025-12-01")
SPLIT = pd.Timestamp("2021-01-01")
B = 10_000; BLOCK = 5
SPREAD, SWAP = 1.5, 5.0
W = np.array([5, 4, 3, 2, 1]) / 15
rng = np.random.default_rng(1501)


def series(name: str) -> pd.Series:
    if name == "DAX":
        from kaldirma_testi import load_tf
        d = load_tf("DAX", "1d")
        return pd.Series(d.close.to_numpy(), index=pd.DatetimeIndex(d.ts).tz_convert("America/New_York").tz_localize(None).normalize() + pd.Timedelta(days=1))
    m = pd.read_csv(ROOT / "research/ndx_gate_forge/data/macro_daily_patched.csv", usecols=["date", f"{name}_close"]).dropna()
    return pd.Series(m[f"{name}_close"].to_numpy(), index=pd.to_datetime(m.date))


def build(c: pd.Series) -> pd.DataFrame:
    c = c[~c.index.duplicated()].sort_index()
    d = pd.DataFrame({"c": c}); d["r"] = np.log(d.c).diff()
    d["r_next"] = d.r.shift(-1)
    s = sum(W[k] * d.r.shift(k) for k in range(5))
    d["s1"] = -np.sign(d.r); d["s2"] = -np.sign(s)
    rho = sum(W[k - 1] * d.r.rolling(250, min_periods=200).apply(lambda x, k=k: pd.Series(x).autocorr(k), raw=True) for k in range(1, 6))
    d["rho"] = rho
    d["s3"] = np.where(rho < 0, d.s2, 0.0)
    d["wd_next"] = d.index.to_series().shift(-1).dt.weekday
    for sname in ("s1", "s2", "s3"):
        pos = d[sname].fillna(0.0)
        flip = (pos != pos.shift(1).fillna(0)).astype(float)
        nights = np.where(d.wd_next == 4, 3.0, 1.0)            # pozisyon Cuma→Pazartesi tutulursa ×3 (temkinli)
        cost_pts = flip * SPREAD + np.abs(pos) * SWAP * nights
        d[f"g_{sname}"] = pos * d.r_next
        d[f"n_{sname}"] = d[f"g_{sname}"] - cost_pts / d.c
    d["long"] = d.r_next
    return d.dropna(subset=["r_next", "r"])


def bboot(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]; n = len(x)
    if n < 20:
        return np.nan
    nb = int(np.ceil(n / BLOCK)); st = rng.integers(0, n - BLOCK + 1, size=(B, nb))
    idx = (st[:, :, None] + np.arange(BLOCK)).reshape(B, -1)[:, :n]
    return float((x[idx].mean(1) > 0).mean())


def stats(x: pd.Series) -> dict:
    x = x.dropna()
    if len(x) < 20:
        return {"gun": len(x)}
    return {"gun": int(len(x)), "ort_bp": 1e4 * x.mean(), "yillik_sharpe": float(x.mean() / x.std() * np.sqrt(252)),
            "isabet_%": 100 * float((x > 0).mean()), "P": bboot(x.to_numpy())}


def beta_p(d: pd.DataFrame) -> tuple:
    b = np.polyfit(d.r, d.r_next, 1)[0]
    n = len(d); nb = int(np.ceil(n / BLOCK)); x, y = d.r.to_numpy(), d.r_next.to_numpy(); bs = []
    for _ in range(2000):
        st = rng.integers(0, n - BLOCK + 1, size=nb); i = (st[:, None] + np.arange(BLOCK)).ravel()[:n]
        bs.append(np.polyfit(x[i], y[i], 1)[0])
    return float(b), float((np.array(bs) < 0).mean())


def report(d: pd.DataFrame, label: str) -> dict:
    out = {"beta": beta_p(d), "hep_uzun": stats(d.long)}
    for s in ("s1", "s2", "s3"):
        out[f"{s}_brut"] = stats(d[f"g_{s}"]); out[f"{s}_net"] = stats(d[f"n_{s}"])
    dn, up = d[d.r < 0], d[d.r > 0]
    out["dusus_sonrasi_al"] = stats(dn.r_next); out["dusus_sonrasi_hep_uzun_ayni_gun"] = "aynı seri (taban = tüm günler hep uzun)"
    out["yukselis_sonrasi_sat"] = stats(-up.r_next)
    out["ortalama_ertesi_gun_bp"] = {"dusus_sonrasi": 1e4 * dn.r_next.mean(), "yukselis_sonrasi": 1e4 * up.r_next.mean(), "tum": 1e4 * d.r_next.mean()}
    for nm, part in (("yari1", d[d.index < SPLIT]), ("yari2", d[d.index >= SPLIT])):
        out[f"s1_brut_{nm}"] = stats(part.g_s1)
    print(f"\n=== {label}: {d.index.min().date()} → {d.index.max().date()}  β={out['beta'][0]:.4f} P(β<0)={out['beta'][1]:.3f} ===")
    rows = {k: v for k, v in out.items() if isinstance(v, dict) and "gun" in v}
    print(pd.DataFrame(rows).T.round(3).to_string())
    print("ertesi gün ort (bp):", {k: round(v, 2) for k, v in out["ortalama_ertesi_gun_bp"].items()})
    return out


def main() -> None:
    res = {}
    ndx, spx, dax = build(series("NDXCASH")), build(series("SPX")), build(series("DAX"))
    res["NDX_gelistirme"] = report(ndx[ndx.index <= DEV_END], "NDX geliştirme")
    res["SPX_gelistirme"] = report(spx[spx.index <= DEV_END], "SPX geliştirme (ikincil)")
    res["NDX_dogrulama"] = report(ndx[ndx.index >= HO_START], "NDX doğrulama")
    res["DAX_bagimsiz"] = report(dax, "DAX bağımsız")
    ho = ndx[ndx.index >= HO_START].g_s1.dropna()
    res["NDX_dogrulama_MDE_bp"] = float(1e4 * 2.8 * ho.std() / np.sqrt(len(ho)))
    print("\nDoğrulama en küçük saptanabilir etki (≈2,8σ/√n):", round(res["NDX_dogrulama_MDE_bp"], 1), "bp/gün")
    (OUT / "sonuc.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=float))


if __name__ == "__main__":
    main()
