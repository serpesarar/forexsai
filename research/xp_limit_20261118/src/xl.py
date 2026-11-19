"""xl.py — K1 + XP için limit (geri çekilme) girişi haritası. python xl.py"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/son_rapor_20261118/src"))
import rapor as R  # noqa: E402

G, NY, FIN = R.G, R.NY, R.FIN
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
OFFS = (0, 10, 25, 50, 75, 100, 150, 200)
ESKI_END = pd.Timestamp("2021-10-31")


def ts(d, hh, mm) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())


def signals(b: pd.DataFrame, step: int) -> pd.DataFrame:
    """K1 günleri + XP çıkış günü (rapor.k1_table ile aynı tanım)."""
    dp = G.day_prices(b, NY, [570, 900, 960], step)
    x = G._local(b, NY)
    tw = x[(x.mn >= 570) & (x.mn < 960)].groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    rows = []
    for i in range(len(days) - 1):
        a = days[i]
        pc, p60 = dp.loc[a, "o960"], dp.loc[a, "o900"]
        if not ((pc / tw.get(a, np.nan) - 1) <= -0.005 and pc < p60):
            continue
        prev, ex = pc, None
        for j in range(i + 1, min(i + 6, len(days))):
            pj = dp.loc[days[j], "o960"]
            if not np.isfinite(pj):
                break
            if pj > prev or j == min(i + 5, len(days) - 1):
                ex = days[j]
                break
            prev = pj
        if ex is None:
            continue
        rows.append({"d": a, "ex": ex, "nxt": days[i + 1]})
    return pd.DataFrame(rows)


def simulate(b: pd.DataFrame, step: int, sg: pd.DataFrame) -> pd.DataFrame:
    t, o, l, sp = b.t.values, b.o.values, b.l.values, b.sp.values
    tol = 300 if step == 60 else step
    rows = []
    for r in sg.itertuples():
        u0, ux, un = ts(r.d, 16, 0), ts(r.ex, 16, 0), ts(r.nxt, 16, 0)
        i0, ix, inx = (int(np.searchsorted(t, u)) for u in (u0, ux, un))
        if i0 >= len(t) or t[i0] - u0 > tol or ix >= len(t) or t[ix] - ux > tol:
            continue
        ask0 = o[i0] + sp[i0]
        px_out = o[ix]
        cal = (pd.Timestamp(r.ex) - pd.Timestamp(r.d)).days
        base = (px_out / ask0 - 1) * 1e4 - FIN * cal
        rec = {"d": pd.Timestamp(r.d), "base": base}
        ask_low = l + sp
        ask_open = o + sp
        for x in OFFS[1:]:
            L = ask0 * (1 - x / 1e4)
            for wn, iend in (("W1", inx), ("W2", ix)):
                seg = np.flatnonzero(ask_low[i0:iend] <= L)
                if seg.size:
                    k = i0 + seg[0]
                    fill = min(L, ask_open[k])
                    rec[f"{wn}_{x}"] = (px_out / fill - 1) * 1e4 - FIN * cal
                else:
                    rec[f"{wn}_{x}"] = np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def stats(d: pd.Series, v: np.ndarray, base: np.ndarray) -> dict:
    filled = np.isfinite(v)
    per_signal = np.where(filled, v, 0.0)
    m = R.metrics(d[filled], v[filled], np.ones(filled.sum())) if filled.any() else {"islem": 0}
    eq = pd.Series(per_signal, index=d.values).sort_index().cumsum()
    q10 = np.quantile(base, 0.10)
    return {"dolum_%": round(float(filled.mean() * 100), 1), "dolan": m, "sinyal_basi_ort_bp": round(float(per_signal.mean()), 1),
            "toplam_bp": round(float(per_signal.sum()), 0), "maks_dusus_sinyal_bp": round(float((eq - eq.cummax()).min()), 0),
            "kacan_islemlerin_piyasa_ort_bp": round(float(base[~filled].mean()), 1) if (~filled).any() else None,
            "kacan_kazanan_%": round(float((base[~filled] > 0).mean() * 100), 1) if (~filled).any() else None,
            "dolan_islemlerin_piyasa_ort_bp": round(float(base[filled].mean()), 1) if filled.any() else None}


def run(name: str, b: pd.DataFrame, step: int) -> dict:
    sg = signals(b, step)
    s = simulate(b, step, sg)
    out = {}
    for e, msk in (("TUM", np.ones(len(s), bool)), ("ESKI", (s.d <= ESKI_END).values), ("YENI", (s.d > ESKI_END).values)):
        z = s[msk].reset_index(drop=True)
        rec = {"x0_piyasa": stats(z.d, z.base.values, z.base.values)}
        for x in OFFS[1:]:
            for wn in ("W1", "W2"):
                rec[f"{wn}_{x}bp"] = stats(z.d, z[f"{wn}_{x}"].values, z.base.values)
            half = 0.5 * z.base.values + 0.5 * np.where(np.isfinite(z[f"W2_{x}"].values), z[f"W2_{x}"].values, 0.0)
            rec[f"YARIM_{x}bp"] = {"sinyal_basi_ort_bp": round(float(half.mean()), 1), "toplam_bp": round(float(half.sum()), 0),
                                   "en_kotu_%10_ort_bp": round(float(np.mean(np.sort(half)[:max(1, len(half) // 10)])), 1),
                                   "en_kotu_bp": round(float(half.min()), 1)}
        out[e] = rec
    print(name, "sinyal", len(s), flush=True)
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_NAS100": (R.KD.mt5_m30("NAS100"), 1800), "MT5_US500": (R.KD.mt5_m30("US500", "2018-06-01"), 1800),
             "MT5_US30": (R.KD.mt5_m30("US30"), 1800), "MT5_US2000": (R.KD.mt5_m30("US2000"), 1800)}
    res = {nm: run(nm, b, st) for nm, (b, st) in feeds.items()}
    (RES / "xl.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for nm, r in res.items():
        print(f"\n===== {nm} (TÜM)")
        z = r["TUM"]
        for k, v in z.items():
            if k.startswith("YARIM"):
                print(f"  {k:12s} sinyal başı {v['sinyal_basi_ort_bp']:7.1f}  toplam {v['toplam_bp']:8.0f}  en kötü%10 {v['en_kotu_%10_ort_bp']}  en kötü {v['en_kotu_bp']}")
                continue
            dd = v["dolan"]
            print(f"  {k:12s} dolum %{v['dolum_%']:5.1f} | dolan: n {dd.get('islem')} isabet {dd.get('isabet_%')} ort {dd.get('ort_bp')} en kötü {dd.get('en_kotu_bp')} "
                  f"kötü%10 {dd.get('en_kotu_%10_ort_bp')} | sinyal başı {v['sinyal_basi_ort_bp']} toplam {v['toplam_bp']} DD {v['maks_dusus_sinyal_bp']} | "
                  f"kaçan piyasa ort {v['kacan_islemlerin_piyasa_ort_bp']} (kazanan %{v['kacan_kazanan_%']})")


if __name__ == "__main__":
    main()
