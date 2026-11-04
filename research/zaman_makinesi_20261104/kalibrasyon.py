"""TM-01 — Zaman Makinesi olasılık kalibrasyonu. Ön-kayıt: PROTOCOL.md."""
import json, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from services import time_machine_service as tm

STEP, WARM, N_BARS, REPLAYS = 97, 65, 24, 1000


def load(sym):
    z = np.load(ROOT / f"backend/data/candle_history/{sym}_5m.npz")
    return tm.Bars(z["ts"].astype(np.int64), z["open"], z["high"], z["low"], z["close"])


def realized(b, idx, k, last, e, st, tg, long):
    for sl in range(k + 1, last + 1):
        j = idx.get(sl)
        if j is None:
            continue
        if (b.l[j] <= st) if long else (b.h[j] >= st):
            return "stop"
        if (b.h[j] >= tg) if long else (b.l[j] <= tg):
            return "target"
    return "close"


def run(sym):
    b = load(sym); days, slots = tm.day_and_slot(b.ts); atr = tm.atr_series(b)
    by_day = {}
    for i, (d, s) in enumerate(zip(days.tolist(), slots.tolist())):
        by_day.setdefault(d, {})[s] = i
    order = sorted(by_day); typical = float(np.median([len(by_day[d]) for d in order]))
    full = [d for d in order if len(by_day[d]) >= tm.MIN_DAY_FRACTION * typical]
    start = np.searchsorted(b.ts, 0) + 0
    first_ok = order[WARM]
    rows = []
    for q in range(len(b.ts) - 1, 0, -STEP):
        d, k = int(days[q]), int(slots[q])
        if d < first_ok or not np.isfinite(atr[q]) or atr[q] <= 0:
            continue
        last = min(tm.SLOTS - 1, k + N_BARS)
        if last - k < 6:
            continue
        prev = [x for x in full if x < d][-tm.POOL_SESSIONS:]
        sess = [{"day": x, "idx": by_day[x]} for x in prev]
        pool = tm.build_pool(b, sess)
        e = float(b.c[q]); r = float(atr[q])
        for side in ("buy", "sell"):
            long = side == "buy"
            st, tg = (e - r, e + r) if long else (e + r, e - r)
            mc = tm.simulate(pool, e, st, tg, k, last, replays=REPLAYS, seed=19, side=side)
            mc.pop("bands"); mc.pop("sample_paths")
            rows.append({"sym": sym, "side": side, "pt": mc["p_target"], "ps": mc["p_stop"],
                         "real": realized(b, by_day[d], k, last, e, st, tg, long)})
    return rows


def score(rows, key, outcome):
    p = np.array([r[key] for r in rows]); y = np.array([r["real"] == outcome for r in rows], float)
    clim = y.mean(); brier, brier_c = np.mean((p - y) ** 2), np.mean((clim - y) ** 2)
    edges = np.quantile(p, np.linspace(0, 1, 11)); b = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, 9)
    bins = [(float(p[b == i].mean()), float(y[b == i].mean()), int((b == i).sum())) for i in range(10) if (b == i).any()]
    gap = float(np.mean([abs(a - c) for a, c, _ in bins]))
    return {"n": len(rows), "brier": float(brier), "brier_iklim": float(brier_c), "gecti_brier": bool(brier <= brier_c),
            "kova_sapma_puan": 100 * gap, "gecti_kova": bool(100 * gap <= 5),
            "kovalar": [(round(100 * a, 1), round(100 * c, 1), n) for a, c, n in bins]}


def main():
    with Pool(3) as pl:
        allrows = sum(pl.map(run, ["NDX", "XAUUSD", "USOIL"]), [])
    out = {}
    for grp in ("NDX", "XAUUSD", "USOIL", "tum"):
        rs = [r for r in allrows if grp == "tum" or r["sym"] == grp]
        out[grp] = {"hedef_once": score(rs, "pt", "target"), "stop_once": score(rs, "ps", "stop")}
    json.dump(out, open(Path(__file__).parent / "sonuc.json", "w"), indent=1)
    for g, v in out.items():
        for ev, s in v.items():
            print(f"{g:7s} {ev:10s} n={s['n']:5d} Brier {s['brier']:.4f} vs iklim {s['brier_iklim']:.4f} "
                  f"({'✓' if s['gecti_brier'] else '✗'})  kova sapması {s['kova_sapma_puan']:.1f} puan ({'✓' if s['gecti_kova'] else '✗'})")
    print("tum hedef_once kovalar (tahmin%, gerçek%, n):", out["tum"]["hedef_once"]["kovalar"])


if __name__ == "__main__":
    main()
