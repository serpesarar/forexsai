"""ME-12 — benzerlik motoru varyantları. Ön-kayıt: PROTOCOL.md."""
import json, sys, zlib
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from services import candle_similarity_service as cs

Q, TEST_FRAC = 200, 0.30


def close_dist(s, q):
    n = len(q); qz = (q - q.mean()) / q.std()
    c = s.c - np.median(s.c)
    m = pd.Series(c).rolling(n).mean().to_numpy()[n - 1:]
    sd = pd.Series(c).rolling(n).std(ddof=0).to_numpy()[n - 1:]
    r = np.correlate(c, qz, "valid") / (n * sd)
    d = np.sqrt(np.maximum(2 * n * (1 - r), 0))
    return np.where(np.isfinite(d) & (sd > 0), d, np.inf)


def vote(ret, w=None):
    w = np.ones(len(ret)) if w is None else w
    v = float((w * np.sign(ret)).sum())
    return 0 if v == 0 else (1 if v > 0 else -1)


def run_cell(arg):
    sym, tf, n = arg
    s = cs.load_history(sym, tf); hs = cs.HORIZONS[tf]; H = hs[1]; hmax = max(hs)
    rng = np.random.default_rng(zlib.crc32(f"v|{sym}|{tf}|{n}".encode()))
    first = int(len(s.ts) * (1 - TEST_FRAC)); end = len(s.ts) - hmax - 1
    step = (end - first) / Q
    ends = (first + step / 2 + np.arange(Q) * step).astype(int)          # karneden yarım adım kaydırılmış
    out = {k: [] for k in ("real", "V0", "V1", "V2", "V3", "V4", "RND", "MAJ")}
    for e in ends:
        q = cs._slice(s, e - n + 1, e + 1)
        if np.any(np.diff(q.ts) > cs.GAP_MAX_S):
            continue
        ok = cs.valid_starts(s, n, hmax, int(q.ts[0]))
        if ok.sum() < 200:
            continue
        qn = cs.normalize_window(q.o, q.h, q.l, q.c)
        d_ohlc = cs.window_rms(s, qn); d_cl = close_dist(s, q.c)
        fwd = lambda st: s.c[st + n - 1 + H] / s.c[st + n - 1] - 1  # noqa: E731
        p20 = cs.pick_matches(d_ohlc, ok, 20, max(1, n // 2)); p50 = cs.pick_matches(d_ohlc, ok, 50, max(1, n // 2))
        c20 = cs.pick_matches(d_cl, ok, 20, max(1, n // 2)); c50 = cs.pick_matches(d_cl, ok, 50, max(1, n // 2))
        med_o, med_c = np.median(d_ohlc[ok]), np.median(d_cl[ok])
        cand = np.flatnonzero(ok); rnd = rng.choice(cand, size=50, replace=False)
        lib_up = float((fwd(cand) > 0).mean())
        out["real"].append(np.sign(s.c[e + H] / s.c[e] - 1))
        out["V0"].append(vote(fwd(p20))); out["V1"].append(vote(fwd(p50)))
        out["V2"].append(vote(fwd(p50), np.exp(-d_ohlc[p50] / med_o)))
        out["V3"].append(vote(fwd(c20))); out["V4"].append(vote(fwd(c50), np.exp(-d_cl[c50] / med_c)))
        out["RND"].append(vote(fwd(rnd))); out["MAJ"].append(1 if lib_up >= 0.5 else -1)
    real = np.array(out.pop("real"))
    res = {}
    for k, v in out.items():
        v = np.array(v); m = (v != 0) & (real != 0)
        res[k] = (int((v[m] == real[m]).sum()), int(m.sum()))
    return f"{sym}|{tf}|{n}", res


def main():
    cells = [(sym, tf, n) for sym in ("NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX") for tf in cs.TIMEFRAMES for n in (50, 100)
             if (cs.HISTORY_DIR / f"{sym.split('.')[0]}_{tf}.npz").exists()]
    with Pool(6) as p:
        r = dict(p.map(run_cell, cells))
    json.dump(r, open("sonuc_hucreler.json", "w"), indent=1)
    rows = []
    for grp, keys in (("tum", list(r)), ("endeks", [k for k in r if k.startswith(("NDX", "GDAXI"))]), ("emtia", [k for k in r if k.startswith(("XAU", "USOIL"))])):
        agg = {v: (sum(r[k][v][0] for k in keys), sum(r[k][v][1] for k in keys)) for v in ("V0", "V1", "V2", "V3", "V4", "RND", "MAJ")}
        base = max(agg["RND"][0] / agg["RND"][1], agg["MAJ"][0] / agg["MAJ"][1])
        for v in ("V0", "V1", "V2", "V3", "V4"):
            h, nn = agg[v]; se = 0.5 / np.sqrt(nn)
            rows.append({"grup": grp, "varyant": v, "n": nn, "isabet_%": 100 * h / nn, "taban_%": 100 * base, "z": (h / nn - base) / se})
        rows.append({"grup": grp, "varyant": "RND", "n": agg["RND"][1], "isabet_%": 100 * agg["RND"][0] / agg["RND"][1]})
        rows.append({"grup": grp, "varyant": "MAJ", "n": agg["MAJ"][1], "isabet_%": 100 * agg["MAJ"][0] / agg["MAJ"][1]})
    df = pd.DataFrame(rows); df.to_csv("sonuc.csv", index=False)
    print(df.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
