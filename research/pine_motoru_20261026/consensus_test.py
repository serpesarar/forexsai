"""EK-P7: tüm-script konsensüs çizgisinin yön sınaması (PROTOCOL EK-P7).

Çıktı: results/konsensus.csv + konsol özeti.
"""
from __future__ import annotations

import gzip
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gosterge_cakisma_20261025"))
sys.path.insert(0, str(HERE))
import config as GC  # noqa: E402
import data  # noqa: E402
import engine as E  # noqa: E402
import eval_scripts as EV  # noqa: E402
from pine_inceleme import _sign  # noqa: E402

SYMS = ("NDX", "DAX", "XAU", "USOIL")
HS = (1, 2, 4, 8, 16, 32)
Q_LO, Q_HI = 0.10, 0.90
N_PLACEBO = 20


def consensus(sym: str, n: int, exclude: set) -> np.ndarray:
    return consensus_dir(sym, n, exclude, HERE / "data/runs/recent")


def consensus_dir(sym: str, n: int, exclude: set, run_dir: Path) -> np.ndarray:
    bull = np.zeros(n, np.int32)
    bear = np.zeros(n, np.int32)
    scripts = set()
    for p in sorted(run_dir.glob("part_*.pkl.gz")):
        with gzip.open(p, "rb") as f:
            for r in pickle.load(f):
                if r["sid"] in exclude:
                    continue
                v = r["per_sym"].get(sym)
                if not v or v["status"] != "ok" or not v["states"]:
                    continue
                scripts.add(r["sid"])
                for k, b in v["states"].items():
                    sg = _sign(k)
                    if sg:
                        a = np.unpackbits(np.frombuffer(b, np.uint8))[:n].astype(bool)
                        (bull if sg > 0 else bear)[:] += a
    return (bull - bear) / max(len(scripts), 1)


def triggers(c: np.ndarray, disc: np.ndarray) -> dict:
    lo, hi = np.quantile(c[disc], [Q_LO, Q_HI])
    prev = np.r_[c[0], c[:-1]]
    return {"BUY": (c > hi) & (prev <= hi), "SELL": (c < lo) & (prev >= lo)}


def cell(T, h, L, W, dsg):
    T = E.thin(T[:, None], h)[:, 0]
    vec = W[np.flatnonzero(T)].sum(axis=0)
    out = {}
    for s, nm in enumerate(("KESIF", "DOGRULAMA", "KASA")):
        o = E.directional(E.split_stats(vec, s), np.array(dsg), L["cost"][s])
        out.update({f"{nm}_{k}": float(np.asarray(o[k]).ravel()[0]) for k in ("n", "z", "hit", "base", "lift", "ret_bp", "cost_bp")})
    out["kanitli"] = (out["DOGRULAMA_z"] >= GC.Z_PASS and out["KASA_z"] >= GC.Z_PASS and out["KASA_lift"] >= 0.02
                      and out["KASA_ret_bp"] > out["KASA_cost_bp"])
    return out


def main():
    excl = EV.lookahead_sids()
    rows, null = [], np.zeros(N_PLACEBO, int)
    rng = np.random.default_rng(7)
    for sym in SYMS:
        d = EV.window_frame(sym, "recent")
        n = len(d)
        c = consensus(sym, n, excl)
        disc = np.flatnonzero(d.split.values == 0)
        shifts = rng.integers(n // 10, n - n // 10, N_PLACEBO)
        for h in HS:
            L = E.labels(d, data.bucket(d, "1h"), h, GC.SPREAD[sym])
            W = E.weights(L)
            for dr, T in triggers(c, disc).items():
                rows.append(dict(sym=sym, h=h, dir=dr, **cell(T, h, L, W, 1.0 if dr == "BUY" else -1.0)))
            for k, sh in enumerate(shifts):
                cp = np.roll(c, sh)
                for dr, T in triggers(cp, disc).items():
                    null[k] += cell(T, h, L, W, 1.0 if dr == "BUY" else -1.0)["kanitli"]
        print(sym, "bitti", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "results/konsensus.csv", index=False)
    cols = ["sym", "h", "dir", "KESIF_n", "KESIF_z", "DOGRULAMA_z", "KASA_z", "KASA_hit", "KASA_base", "KASA_ret_bp", "KASA_cost_bp", "kanitli"]
    print(out[cols].round(3).to_string())
    print(f"kanıtlı {int(out.kanitli.sum())}/48; plasebo ort {null.mean():.2f}, max {null.max()}, "
          f"p {(null >= out.kanitli.sum()).mean():.2f}; doğrulama z≥1,645: {(out.DOGRULAMA_z >= GC.Z_PASS).sum()} "
          f"ters {(out.DOGRULAMA_z <= -GC.Z_PASS).sum()}; kasa {(out.KASA_z >= GC.Z_PASS).sum()}/{(out.KASA_z <= -GC.Z_PASS).sum()}")


if __name__ == "__main__":
    main()
