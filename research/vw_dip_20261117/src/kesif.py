"""kesif.py — PROTOCOL §5: 720 hücre KEŞİF taraması + ızgara plasebosu + aday dondurma. TEST'e BAKMAZ.

Çıktı: cache/girisler.parquet, cache/eval_gercek.parquet, results/kesif_izgara.csv, results/kesif_ozet.json, results/donmus_adaylar.json
"""
from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd

import vw  # noqa: I001  (sys.path: lib, veri)
import lib
import veri

CACHE = vw.HERE / "cache"
RES = vw.HERE / "results"
DROPS = {"hepsi": 0.0, "d1.5": 0.015, "d3": 0.03}
VIXS = {"hepsi": 0.0, "v18.4": 18.4}
N_MIN, P_MIN, N_PLACEBO, MAX_FROZEN, MAX_PER_TYPE = 40, 0.90, 20, 5, 2
KESIF_END = date(2021, 10, 31)


def build_entries() -> tuple[veri.PathBars, pd.DataFrame]:
    p = vw.duka_path_stable()
    q = veri.build_15m(p)
    b = veri.build_210m(q)
    excl = veri.check_vs_file(b)["supheli_t"]
    anc = pd.concat([vw.a210_anchors(q, b, excl), vw.ag_anchors(q)], ignore_index=True)
    e = vw.entries(q, anc)
    e["d"] = [pd.Timestamp(int(t), unit="s", tz="UTC").tz_convert(vw.NY).date() for t in e.t_sig]
    vix = lib.vix_prev_map(sorted(set(e.d)))
    e["vix"] = e.d.map(vix)
    e["era"] = np.where(e.d <= KESIF_END, "KESIF", "TEST")
    return p, e


def cluster_p(v: np.ndarray, cl: np.ndarray, n: int = 2000, seed: int = 3) -> float:
    if len(v) < 3:
        return np.nan
    u, inv = np.unique(cl, return_inverse=True)
    s, c = np.bincount(inv, v), np.bincount(inv)
    pick = np.random.default_rng(seed).integers(0, len(u), (n, len(u)))
    return float(((s[pick].sum(1) / c[pick].sum(1)) > 0).mean())


def grid(ev: pd.DataFrame, e: pd.DataFrame, n_boot: int = 2000, drops: dict | None = None, vixs: dict | None = None,
         types: tuple | None = None) -> pd.DataFrame:
    drops, vixs, types = drops or DROPS, vixs or VIXS, types or vw.ENTRY_TYPES
    x = ev.merge(e[["typ", "drop", "vix", "d", "era"]], left_on="e", right_index=True)
    rows = []
    for typ in types:
        xt = x[x.typ == typ]
        for dn, dv in drops.items():
            xd = xt[xt["drop"] >= dv]
            for vn, vv in vixs.items():
                xv = xd[xd.vix >= vv] if vv > 0 else xd
                for (tp, tm), g in xv.groupby(["tp", "time"]):
                    rows.append({"typ": typ, "drop": dn, "vix": vn, "tp": tp, "time": tm, "n": len(g),
                                 "mean": g.R.mean(), "mean15": g.R15.mean(), "hit": (g.R > 0).mean(),
                                 "t": g.R.mean() / (g.R.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 else np.nan,
                                 "P": cluster_p(g.R.values, g.d.astype(str).values, n_boot) if len(g) >= N_MIN else np.nan})
    return pd.DataFrame(rows)


def passing(gr: pd.DataFrame) -> pd.DataFrame:
    return gr[(gr.n >= N_MIN) & (gr["mean"] > 0) & (gr.P >= P_MIN) & (gr.mean15 > 0)]


def placebo_shifts(e: pd.DataFrame, rep: int) -> np.ndarray:
    """±1…7 takvim günü, hafta içine düşen, aynı NY saati."""
    rng = np.random.default_rng(100 + rep)
    out = np.zeros(len(e), np.int64)
    for n, d in enumerate(e.d):
        while True:
            k = int(rng.integers(1, 8)) * (1 if rng.random() < 0.5 else -1)
            if (pd.Timestamp(d) + pd.Timedelta(days=k)).weekday() < 5:
                out[n] = k * 86400
                break
    return out


def main() -> None:
    CACHE.mkdir(exist_ok=True)
    RES.mkdir(exist_ok=True)
    p, e = build_entries()
    e.to_parquet(CACHE / "girisler.parquet")
    print("girişler:", e.groupby(["typ", "era"]).size().unstack().to_dict(), flush=True)
    ek = e[e.era == "KESIF"].reset_index(drop=True)
    ev = vw.evaluate_all(p, ek)
    ev.to_parquet(CACHE / "eval_kesif.parquet")
    gr = grid(ev, ek)
    gr.to_csv(RES / "kesif_izgara.csv", index=False)
    real_pass = passing(gr)
    print(f"KEŞİF: {len(gr)} hücre, aday ölçütünü geçen {len(real_pass)}", flush=True)
    pl_counts = []
    for r in range(N_PLACEBO):
        evp = vw.evaluate_all(p, ek, shift=placebo_shifts(ek, r))
        gp = grid(evp, ek, n_boot=500)
        pl_counts.append(int(len(passing(gp))))
        print(f"  plasebo {r}: {pl_counts[-1]}", flush=True)
    pc = np.array(pl_counts)
    # dondurma: t'ye göre en iyi ≤5, aynı tipten ≤2
    frozen, per = [], {}
    for r in real_pass.sort_values("t", ascending=False).itertuples():
        if per.get(r.typ, 0) >= MAX_PER_TYPE:
            continue
        frozen.append({k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in r._asdict().items() if k != "Index"})
        per[r.typ] = per.get(r.typ, 0) + 1
        if len(frozen) == MAX_FROZEN:
            break
    ozet = {"hucre": len(gr), "gercek_aday": len(real_pass), "plasebo_aday": pl_counts,
            "plasebo_p95": float(np.percentile(pc, 95)), "gercek_plasebo_yuzdelik": float((pc < len(real_pass)).mean()),
            "izgara_sans_ustu": bool(len(real_pass) > np.percentile(pc, 95)), "donmus": frozen,
            "giris_sayilari": {f"{k[0]}|{k[1]}": int(v) for k, v in e.groupby(["typ", "era"]).size().items()}}
    (RES / "kesif_ozet.json").write_text(json.dumps(ozet, indent=1, ensure_ascii=False, default=str))
    (RES / "donmus_adaylar.json").write_text(json.dumps(frozen, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: v for k, v in ozet.items() if k not in ("giris_sayilari",)}, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
