"""DTS-03 — Zaman Makinesi aralık kalibrasyonu farklı TF ve ufuklarda (5m/15m/1h). Ön-kayıt: PROTOCOL.md."""
import json, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from services import time_machine_service as tm
from common import load

GRID = {"5m": (("NDX", "XAUUSD", "USOIL"), (12, 48, 96)), "15m": (("NDX", "GDAXI", "XAUUSD", "USOIL"), (4, 16, 32)),
        "1h": (("NDX", "GDAXI", "XAUUSD", "USOIL"), (4, 8, 24))}
WARM, REPLAYS, STEP_MIN = 65, 600, 480


def bars(sym, tf):
    d = load(sym, tf)
    return tm.Bars((d.ts.astype("int64") // 10**9).to_numpy(), d.open.to_numpy(), d.high.to_numpy(), d.low.to_numpy(), d.close.to_numpy())


def run(arg):
    sym, tf = arg
    bm = int(tf[:-1]) if tf.endswith("m") else 60
    b = bars(sym, tf); days, slots = tm.day_and_slot(b.ts, bm); atr = tm.atr_series(b)
    by_day = {}
    for i, (d, s) in enumerate(zip(days.tolist(), slots.tolist())):
        by_day.setdefault(d, {})[s] = i
    order = sorted(by_day); typical = float(np.median([len(by_day[x]) for x in order]))
    full = [x for x in order if len(by_day[x]) >= tm.MIN_DAY_FRACTION * typical]
    hs = GRID[tf][1]; hmax = max(hs); step = max(1, STEP_MIN // bm)
    rows = []
    start_day = order[min(WARM, len(order) - 1)]
    for q in range(len(b.ts) - 1 - hmax, 0, -step):
        d = int(days[q])
        if d < start_day or not np.isfinite(atr[q]):
            continue
        prev = [x for x in full if x < d][-tm.POOL_SESSIONS:]
        if len(prev) < tm.MIN_SESSIONS:
            continue
        pool = tm.build_pool(b, [{"day": x, "idx": by_day[x]} for x in prev], bm)
        k = int(slots[q]); e = float(b.c[q]); r = float(atr[q])
        for h in hs:
            if b.ts[q + h] - b.ts[q] > (h * bm * 60) * 3:          # ufuk hafta sonu/boşluğa taşıyor → atla
                continue
            mc = tm.simulate(pool, e, e - r, e + r, k, k + h, replays=REPLAYS, seed=19, side="buy")
            b5, b25, _m, b75, b95 = mc["bands"][-1]
            real = float(b.c[q + h])
            hit = "close"
            for j in range(q + 1, q + h + 1):
                if b.l[j] <= e - r:
                    hit = "stop"; break
                if b.h[j] >= e + r:
                    hit = "target"; break
            flat = [x for s in pool for x in s]
            pick = np.random.default_rng(19).integers(0, len(flat), size=(REPLAYS, h))
            sims = np.prod(np.array([x[3] for x in flat])[pick], axis=1) * e
            u5, u25, u75, u95 = np.quantile(sims, [0.05, 0.25, 0.75, 0.95])
            rows.append({"sym": sym, "tf": tf, "h": h, "in90": b5 <= real <= b95, "in50": b25 <= real <= b75,
                         "u90": u5 <= real <= u95, "w": (b95 - b5) / e, "uw": (u95 - u5) / e, "pt": mc["p_target"], "hit": hit})
    return rows


def main():
    jobs = [(s, tf) for tf, (syms, _) in GRID.items() for s in syms]
    with Pool(6) as p:
        rows = sum(p.map(run, jobs), [])
    import pandas as pd
    df = pd.DataFrame(rows)
    g = df.groupby(["tf", "sym", "h"])
    out = g.apply(lambda x: pd.Series({"n": len(x), "kapsama90": 100 * x.in90.mean(), "kapsama50": 100 * x.in50.mean(),
                                         "saatsiz90": 100 * x.u90.mean(), "genislik_%": 100 * x.w.median(), "saatsiz_genislik_%": 100 * x.uw.median(),
                                         "brier": ((x.pt - (x.hit == "target")) ** 2).mean(),
                                         "brier_taban": (((x.hit == "target").mean() - (x.hit == "target")) ** 2).mean()}), include_groups=False).reset_index()
    out["aralik_gecti"] = (out.kapsama90.between(85, 95)) & (out["genislik_%"] <= 1.05 * out["saatsiz_genislik_%"])
    out["brier_gecti"] = out.brier <= out.brier_taban
    out.to_csv("dts03_hucreler.csv", index=False)
    pd.set_option("display.width", 220); pd.set_option("display.max_rows", 100)
    print(out.round(3).to_string(index=False))
    print(f"\naralık geçen: {int(out.aralik_gecti.sum())}/{len(out)} · kapsama90 aralığı {out.kapsama90.min():.1f}–{out.kapsama90.max():.1f} · Brier geçen: {int(out.brier_gecti.sum())}/{len(out)}")
    json.dump(out.to_dict("records"), open("dts03_ozet.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
