"""kr_motor.py — KORKU paketi (T30 + OPEX vetosu) olayları + 16:00 yolları; 5 turun ortak simülatörü.

python kr_motor.py → cache/olaylar.pkl
Olay: sinyal günü d, 16:00 bid/ask dizisi (d … d+6 işlem günü), takvim günleri, 16:00'lar arası en düşük fiyat, giriş özellikleri.
"""
from __future__ import annotations

import pickle
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/korku_evren_20261119/src"))
import esik as E  # noqa: E402

VR = E.VR
FIN = VR.FIN
CUT = E.CUT
T30 = E.CELLS["T30"]
NDAY = 7                       # d … d+6 (ikinci yarı + 5 gün)
MAXH = 5


def events(b: pd.DataFrame, step: int, name: str) -> list[dict]:
    dp, f, _ = VR.entry_features(b, step)
    sig = T30(f).fillna(False)
    t, o, l, sp = b.t.values, b.o.values, b.l.values, b.sp.values
    tol = 300 if step == 60 else step
    days = list(dp.index)
    out = []
    for i, d in enumerate(days):
        if not sig.iloc[i] or d > CUT or f.opex_k.iloc[i] in (0, 1, 2):
            continue
        bid, ask, idx, asknx = [], [], [], []
        for j in range(i, min(i + NDAY, len(days))):
            u = VR.ts(days[j], 16, 0)
            k = int(np.searchsorted(t, u))
            if k >= len(t) or t[k] - u > tol:
                break
            bid.append(float(o[k])); ask.append(float(o[k] + sp[k])); idx.append(k)
            asknx.append(float(o[k + 1] + sp[k + 1]) if k + 1 < len(t) else np.nan)
        if len(bid) < 2:
            continue
        cal = [(days[i + j] - d).days for j in range(len(bid))]
        lows = [float(l[idx[j - 1]:idx[j]].min()) if j else np.nan for j in range(len(bid))]
        dts = [days[i + j] for j in range(len(bid))]
        rlo = [float(dp.lo.iloc[i + j]) for j in range(len(bid))]
        rhi = [float(dp.hi.iloc[i + j]) for j in range(len(bid))]
        out.append({"feed": name, "d": d, "bid": bid, "ask": ask, "cal": cal, "low": lows, "dates": dts, "rlo": rlo, "rhi": rhi, "ask_nx": asknx,
                    "donem": "KESIF" if d <= pd.Timestamp("2021-10-31") else "TEST",
                    "f": {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v) for k, v in f.iloc[i].to_dict().items()}})
    return out


def part(ev: dict, j0: int, rule: str, h: float, w: float, maxh: int = MAXH, hold_if=None) -> tuple[float, int]:
    """Bir yarı/tam pozisyon: j0 günü 16:00 ask'ında al. Döner (ağırlıklı net bp, çıkış günü indeksi)."""
    bid, ask, cal = ev["bid"], ev["ask"], ev["cal"]
    if j0 >= len(bid) - 1:
        return np.nan, j0
    E0 = ask[j0]
    prev = bid[j0]
    locked, wt = 0.0, w
    last = min(j0 + maxh, len(bid) - 1)
    for j in range(j0 + 1, last + 1):
        r = (bid[j] / E0 - 1) * 1e4 - FIN * (cal[j] - cal[j0])
        ok = (bid[j] > prev) if rule == "XP" else (bid[j] >= E0)
        if ok or j == last:
            return locked + wt * r, j
        if j == j0 + 1:
            if hold_if is not None and not hold_if(ev, j, r):
                return locked + wt * r, j
            if h < 1.0 and bid[j] < E0:
                locked += wt * (1 - h) * r
                wt *= h
        prev = bid[j]
    return locked, last


def sim(ev: dict, entry: str, rule: str, h: float, **kw) -> tuple[float, int]:
    if entry == "E0":
        return part(ev, 0, rule, h, 1.0, **kw)
    if entry == "E2":
        a, ja = part(ev, 0, rule, h, 0.5, **kw)
        bb, jb = part(ev, 1, rule, h, 0.5, **kw)
        if not np.isfinite(bb):
            return np.nan, ja
        return a + bb, max(ja, jb)
    raise ValueError(entry)


def main() -> None:
    P = []
    sys.path.insert(0, str(ROOT / "research/ksg_tpsl_20261119/src"))
    import motor as KM  # noqa: E402
    feeds = dict(E.feeds())
    for nm in ("EET30", "NQ"):
        feeds[nm] = KM.load(nm)
    for name, (b, step) in feeds.items():
        ev = events(b, step, name)
        P += ev
        print(name, len(ev))
    pickle.dump(P, open(HERE / "cache/olaylar.pkl", "wb"))


if __name__ == "__main__":
    main()
