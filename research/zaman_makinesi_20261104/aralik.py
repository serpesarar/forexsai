"""TM-01b — ufuk-sonu fiyat aralığı kapsaması (aracın %90 iddiası) + saat-koşulsuz kıyas."""
import json, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kalibrasyon as K
tm = K.tm


def run(sym):
    b = K.load(sym); days, slots = tm.day_and_slot(b.ts); atr = tm.atr_series(b)
    by_day = {}
    for i, (d, s) in enumerate(zip(days.tolist(), slots.tolist())):
        by_day.setdefault(d, {})[s] = i
    order = sorted(by_day); typical = float(np.median([len(by_day[d]) for d in order]))
    full = [d for d in order if len(by_day[d]) >= tm.MIN_DAY_FRACTION * typical]
    rows = []
    for q in range(len(b.ts) - 1, 0, -K.STEP):
        d, k = int(days[q]), int(slots[q])
        if d < order[K.WARM] or not np.isfinite(atr[q]):
            continue
        last = min(tm.SLOTS - 1, k + K.N_BARS)
        idx = by_day[d]; js = [idx[s] for s in range(k + 1, last + 1) if s in idx]
        if last - k < 6 or not js:
            continue
        prev = [x for x in full if x < d][-tm.POOL_SESSIONS:]
        pool = tm.build_pool(b, [{"day": x, "idx": by_day[x]} for x in prev])
        e = float(b.c[q]); n = last - k
        mc = tm.simulate(pool, e, e - 1e9, e + 1e9, k, last, replays=K.REPLAYS, seed=19, side="buy")
        b5, b25, _m, b75, b95 = mc["bands"][-1]
        flat = [x for s in pool for x in s]                       # saat koşulsuz havuz
        rng = np.random.default_rng(19); pick = rng.integers(0, len(flat), size=(K.REPLAYS, n))
        rets = np.prod(np.array([x[3] for x in flat])[pick], axis=1) * e
        u5, u25, u75, u95 = np.quantile(rets, [0.05, 0.25, 0.75, 0.95])
        real = float(b.c[js[-1]])
        rows.append({"sym": sym, "in90": b5 <= real <= b95, "in50": b25 <= real <= b75,
                     "u90": u5 <= real <= u95, "u50": u25 <= real <= u75,
                     "w90": (b95 - b5) / e, "uw90": (u95 - u5) / e})
    return rows


def main():
    with Pool(3) as pl:
        rows = sum(pl.map(run, ["NDX", "XAUUSD", "USOIL"]), [])
    out = {}
    for g in ("NDX", "XAUUSD", "USOIL", "tum"):
        r = [x for x in rows if g == "tum" or x["sym"] == g]
        out[g] = {"n": len(r), "kapsama90_%": 100 * np.mean([x["in90"] for x in r]), "kapsama50_%": 100 * np.mean([x["in50"] for x in r]),
                  "saatsiz_kapsama90_%": 100 * np.mean([x["u90"] for x in r]), "saatsiz_kapsama50_%": 100 * np.mean([x["u50"] for x in r]),
                  "genislik90_medyan_%": 100 * float(np.median([x["w90"] for x in r])),
                  "saatsiz_genislik90_medyan_%": 100 * float(np.median([x["uw90"] for x in r]))}
        print(g, {k: round(v, 2) for k, v in out[g].items()})
    json.dump(out, open(Path(__file__).parent / "sonuc_aralik.json", "w"), indent=1)


if __name__ == "__main__":
    main()
