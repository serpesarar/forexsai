"""Son kıyas (2026-10-02, ön-kayıt bu docstring):

Diğer ajanın (ndx_caprev_paths_20261002) en iyi adayı: CAPREV + "artan VIX" (önceki VIX ≥ ondan önceki gün)
+ tam +1R hedef / −1R stop (1R = 1×günlük vol). Bu iki seçim NDX sonuçlarından SONRA yapıldı.
Test: (A) bağımsız kodla NDX native 1h/30m/15m sayılarını yeniden üret (ajanlar arası uyum);
(B) aynı kuralları hiç değiştirmeden DAX'ta (bu filtreyle hiç bakılmamış piyasa) sına.
Tahmin: gerçek mekanizmaysa DAX'ta "artan VIX" alt kümesi tabandan iyi, +1R hedef en iyi-5-gün bağımlılığını azaltır.
Çıkışlar: d0 = aynı gün seans kapanışı, tp1 = +1R/−1R ilk geçiş (aynı barda ikisi → stop) yoksa d0, half = ½d0 + ½tp1.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, block_boot
from long_data import load_long, macro
from round4 import build, events as ev_ndx
import cross_market as cm

SPR = 0.00006


def vix_change(nyd: pd.Series) -> np.ndarray:
    v = macro().VIX_close.dropna()
    ch = v.diff()
    full = pd.date_range("2014-01-01", "2026-12-31")
    return ch.reindex(full).ffill().reindex(nyd - pd.Timedelta(days=1)).to_numpy()


def paths(d: pd.DataFrame, E: pd.DataFrame, close_end: int) -> pd.DataFrame:
    idx = pd.Series(d.index[d.end == close_end], index=d.nyd[d.end == close_end]).groupby(level=0).last()
    lo, hi, op, cl = (d[c].to_numpy() for c in ["low", "high", "open", "close"])
    rows = []
    for r in E.itertuples():
        if r.nyd not in idx.index:
            continue
        j0 = int(idx[r.nyd])
        if j0 < r.ei:
            continue
        e = op[r.ei]
        stop, tgt = e * (1 - r.dvol), e * (1 + r.dvol)
        sd = e * r.dvol
        R_d0 = R_tp = None
        for j in range(r.ei, j0 + 1):
            s_hit = lo[j] <= stop
            t_hit = hi[j] >= tgt
            if s_hit:
                px = min(op[j], stop) if j > r.ei else stop
                R_stop = (px - e) / sd - 2 * SPR / r.dvol
                R_d0 = R_stop if R_d0 is None else R_d0
                R_tp = R_stop if R_tp is None else R_tp
                break
            if t_hit and R_tp is None:
                px = max(op[j], tgt) if j > r.ei else tgt
                R_tp = (px - e) / sd - 2 * SPR / r.dvol
        if R_d0 is None:
            R_d0 = (cl[j0] - e) / sd - 2 * SPR / r.dvol
        if R_tp is None:
            R_tp = R_d0
        rows.append({"nyd": r.nyd, "year": r.nyd.year, "R_d0": R_d0, "R_tp1": R_tp, "R_half": .5 * R_d0 + .5 * R_tp})
    x = pd.DataFrame(rows)
    if len(x):
        x["vix_rising"] = vix_change(x.nyd) >= 0
    return x


def summ(x: pd.DataFrame, col: str) -> dict:
    if len(x) < 3:
        return {"n": int(len(x))}
    v = x.sort_values("nyd")[col].to_numpy()
    bs = block_boot(v, x.sort_values("nyd").nyd.astype(str).to_numpy(), 2000)
    h = len(v) // 2
    top5 = np.sort(v)[::-1][:5].sum()
    return {"n": int(len(v)), "toplam": round(float(v.sum()), 2), "ort": round(float(v.mean()), 3),
            "P(>0)": round(float(np.mean(bs > 0)), 3), "ilk/ikinci yarı": (round(float(v[:h].mean()), 3), round(float(v[h:].mean()), 3)),
            "en iyi 5 hariç toplam": round(float(v.sum() - top5), 2)}


def block(x: pd.DataFrame) -> dict:
    out = {}
    for lab, m in {"taban": np.ones(len(x), bool), "artan VIX": x.vix_rising.to_numpy(), "düşen VIX": ~x.vix_rising.to_numpy()}.items():
        for col in ["R_d0", "R_tp1", "R_half"]:
            out[f"{lab} | {col}"] = summ(x[m], col)
    return out


def main() -> dict:
    res = {}
    for tf, step in [("1h", 60), ("30m", 30), ("15m", 15)]:
        d = build(load_long(tf), step, 540 if step == 60 else 570)
        res[f"NDX {tf}"] = block(paths(d, ev_ndx(d, "stress", "hi"), 960))
    for tf in ["1h", "30m", "15m"]:
        d = cm.build_dax(tf)
        res[f"DAX {tf}"] = block(paths(d, cm.events(d, "stress", "hi"), int(d.close_end.iat[0])))
    return res


if __name__ == "__main__":
    res = main()
    (OUT / "final_check.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for k, r in res.items():
        print(f"\n===== {k} =====")
        for kk, v in r.items():
            print(f"  {kk}: {v}")
