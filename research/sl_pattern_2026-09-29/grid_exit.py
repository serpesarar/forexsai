"""Çıkış kuralı taraması — mevcut girişler sabit, yalnız çıkış değişir.

Birim: R (1R = girişteki orijinal SL mesafesi) + $ (gerçek lot).
Doğrulama: kronolojik TRAIN (< SPLIT) / TEST (≥ SPLIT) + aylık dilimler + bootstrap.
"""
from __future__ import annotations
import itertools
import numpy as np
import pandas as pd
from sim import simulate

SPLIT = pd.Timestamp("2026-08-01", tz="UTC")
df = pd.read_pickle("paths_stats.pkl")
df = df[df.exit.isin(["tp", "sl"])].copy()
df["usd_R"] = df["risk"] * df["volume"] * np.where(df.sym == "USOIL.FOREX", 100.0, 1.0)
df["test"] = df.open_utc >= SPLIT
df["grp"] = df.sym.str[:4] + "_" + df.dir


def run(rule: dict) -> np.ndarray:
    out = np.empty(len(df))
    for k, (p, rr) in enumerate(zip(df.path.values, df.rr.values)):
        r = dict(rule)
        tpm = r.pop("tp_mult", 1.0)
        # TP yolunun kesri cinsinden verilen tetikleri R'ye çevir
        for key in ("be_trig", "trail_trig", "partial_at"):
            fk = key + "_f"
            if fk in r:
                v = r.pop(fk); r[key] = None if v is None else v * rr
        if "be_lock_f" in r:
            r["be_lock"] = r.pop("be_lock_f") * rr
        if "trail_dist_f" in r:
            r["trail_dist"] = r.pop("trail_dist_f") * rr
        tp = rr * tpm if tpm is not None else None
        out[k], _, _ = simulate(p, tp, **r)
    return out


def summarize(name: str, R: np.ndarray, base: np.ndarray) -> dict:
    d = R - base
    tr, te = ~df.test.values, df.test.values
    usd = (R * df.usd_R.values)
    rng = np.random.default_rng(7)
    bs = [d[rng.integers(0, len(d), len(d))].sum() for _ in range(1000)]
    m = df.open_utc.dt.strftime("%m").values
    months = {mm: round(d[m == mm].sum(), 1) for mm in sorted(set(m))}
    return dict(rule=name, sumR=R.sum().round(1), dR=d.sum().round(1),
                dR_train=d[tr].sum().round(1), dR_test=d[te].sum().round(1),
                wr=(R > 0).mean().round(3), usd=usd.sum().round(0),
                d_usd=(d * df.usd_R.values).sum().round(0),
                p_pos=np.mean(np.array(bs) > 0).round(3), months=months)


if __name__ == "__main__":
    base = run({})
    print("BASELINE ΣR", base.sum().round(1), "WR", (base > 0).mean().round(3),
          "Σ$", (base * df.usd_R).sum().round(0), "n", len(df), "test n", df.test.sum())
    rules = {}
    for f in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        for lock in (0.0, 0.1, 0.25, 0.5):
            if lock < f:
                rules[f"BE@%{int(f*100)}TP lock%{int(lock*100)}TP"] = dict(be_trig_f=f, be_lock_f=lock)
    for k in (0.1, 0.2, 0.3, 0.5):
        rules[f"BE@{k}R"] = dict(be_trig=k, be_lock=0.0)
    for f in (0.3, 0.5, 0.7):
        for dist in (0.3, 0.5, 0.7):
            rules[f"TRAIL@%{int(f*100)}TP dist%{int(dist*100)}TP"] = dict(trail_trig_f=f, trail_dist_f=dist)
    for f in (0.3, 0.5, 0.7):
        rules[f"PARTIAL50@%{int(f*100)}TP +BE"] = dict(partial_at_f=f, partial_frac=0.5, be_trig_f=f, be_lock_f=0.0)
        rules[f"PARTIAL50@%{int(f*100)}TP"] = dict(partial_at_f=f, partial_frac=0.5)
    for tm in (0.5, 0.6, 0.75, 0.9, 1.25, 1.5):
        rules[f"TPx{tm}"] = dict(tp_mult=tm)
    for s in (0.5, 0.6, 0.75):
        rules[f"SLx{s}"] = dict(sl_r=s)
    for ts in (60, 120, 240):
        rules[f"TIME{ts}m"] = dict(time_stop=ts)
    rows = [summarize(n, run(r), base) for n, r in rules.items()]
    out = pd.DataFrame(rows).sort_values("dR", ascending=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
    print(out.to_string(index=False))
    out.to_pickle("grid_exit.pkl")
