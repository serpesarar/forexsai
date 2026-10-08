"""Ön-kayıt: PROTOCOL.md. python3 research/decider_kural_20261008/analyze.py  (önce pull.py)"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi.stats import boot_mean_ci, ranks  # noqa: E402

OUT = HERE / "results"
TRAIN_FRAC, QS = 0.6, (0.10, 0.20, 0.33, 0.50, 0.67, 0.80, 0.90)
MIN_BLOCK, MAX_BLOCK_FRAC, MIN_SCOPE, TOP_SINGLE = 10, 0.5, 40, 30
LOSS_R = -0.8
FALLBACK_HOLD = pd.Timedelta(minutes=60)
NON_FEATURES = {"id", "ts", "symbol", "act", "dir", "pnl_r", "outcome", "outcome_at", "model", "mae_r", "mfe_r",
                "tp_progress", "sl_recovered_entry", "bars_to_outcome", "session"}
CATS = ("session", "model", "dir")


def independent(d: pd.DataFrame) -> pd.DataFrame:
    """Sembol başına tek pozisyon: önceki sayılan kararın sonucu gelmeden gelen karar atılır (E6)."""
    keep, busy_until = [], {}
    for i, r in d.sort_values("ts").iterrows():
        if r["ts"] < busy_until.get(r["symbol"], pd.Timestamp.min.tz_localize("UTC")):
            continue
        keep.append(i)
        end = r["outcome_at"] if pd.notna(r["outcome_at"]) else r["ts"] + FALLBACK_HOLD
        busy_until[r["symbol"]] = max(end, r["ts"])
    return d.loc[keep].sort_values("ts").reset_index(drop=True)


def base_table(o: pd.DataFrame, w: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sym, dr), g in pd.concat([o, w]).groupby(["symbol", "dir"]):
        for act, h in g.groupby("act"):
            lo, hi, p = boot_mean_ci(h["pnl_r"].to_numpy(float))
            rows.append({"sembol": sym, "yön": dr, "tür": "OPEN (açtı)" if act == "OPEN" else "WAIT-cf (açmadı)",
                         "n": len(h), "wr": (h["pnl_r"] > 0).mean(), "ort_R": h["pnl_r"].mean(),
                         "ci": f"[{lo:+.2f}…{hi:+.2f}]", "P(>0)": p})
    return pd.DataFrame(rows)


def anatomy(o: pd.DataFrame, w: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sym in sorted(o["symbol"].unique()):
        for act, g in (("OPEN", o[o.symbol == sym]), ("WAIT-cf", w[w.symbol == sym])):
            sl = g[g["pnl_r"] <= LOSS_R]
            if len(sl) < 5:
                continue
            rows.append({"sembol": sym, "tür": act, "SL n": len(sl), "SL payı": len(sl) / len(g),
                         "hiç çalışmadı": (sl["mfe_r"] < 0.15).mean(), "önce kâr ≥0,3R": (sl["mfe_r"] >= 0.3).mean(),
                         "TP'nin ≥%70'i": (sl["tp_progress"] >= 0.7).mean(),
                         "SL sonrası girişe döndü": (sl["sl_recovered_entry"] == 1).mean(),
                         "medyan süre (bar)": sl["bars_to_outcome"].median()})
    return pd.DataFrame(rows)


# ── kural araması (sl_onleme_kural_20261007 ile aynı uzay) ──

def feats(d: pd.DataFrame) -> list[str]:
    return [c for c in d.columns if c not in NON_FEATURES and pd.api.types.is_numeric_dtype(d[c])
            and d[c].notna().mean() > 0.5 and d[c].nunique() > 1]


def singles(tr: pd.DataFrame, cols: list[str]) -> list[tuple]:
    rules = []
    for c in cols:
        x = tr[c].dropna()
        if x.nunique() <= 2:
            rules += [(f"{c} = {v:g}", c, "==", v) for v in sorted(x.unique())]
            continue
        for v in sorted({float(x.quantile(q)) for q in QS}):
            rules += [(f"{c} ≥ {v:.4g}", c, ">=", v), (f"{c} ≤ {v:.4g}", c, "<=", v)]
    for c in CATS:
        rules += [(f"{c} = {v}", c, "==", v) for v in tr[c].dropna().unique()]
    return rules


def mask(df: pd.DataFrame, rule: tuple) -> np.ndarray:
    _, c, op, v = rule
    x = df[c]
    return ((x >= v) if op == ">=" else (x <= v) if op == "<=" else (x == v)).fillna(False).to_numpy()


def saved(df: pd.DataFrame, m: np.ndarray) -> float:
    return float(-df.loc[m, "pnl_r"].sum())


def search(tr: pd.DataFrame, te: pd.DataFrame, scope: str) -> list[dict]:
    cols = feats(tr)
    sc = []
    for r in singles(tr, cols):
        m = mask(tr, r)
        if MIN_BLOCK <= m.sum() <= MAX_BLOCK_FRAC * len(tr):
            sc.append(([r], m, saved(tr, m)))
    sc.sort(key=lambda x: -x[2])
    cands = list(sc)
    for a, b in itertools.combinations(sc[:TOP_SINGLE], 2):
        m = a[1] & b[1]
        if MIN_BLOCK <= m.sum() <= MAX_BLOCK_FRAC * len(tr):
            cands.append((a[0] + b[0], m, saved(tr, m)))
    out = []
    for rules, m_tr, s_tr in cands:
        m_te = np.ones(len(te), dtype=bool)
        for r in rules:
            m_te &= mask(te, r)
        out.append({"kapsam": scope, "kural": " VE ".join(r[0] for r in rules), "egitim_engel": int(m_tr.sum()),
                    "egitim_R": s_tr, "sinama_engel": int(m_te.sum()), "sinama_R": saved(te, m_te),
                    "sinama_rastgele_R": -m_te.sum() * te["pnl_r"].mean(),
                    "sinama_engel_sl": int((te.loc[m_te, "pnl_r"] <= LOSS_R).sum()),
                    "sinama_engel_tp": int((te.loc[m_te, "pnl_r"] > 0).sum())})
    return out


def run(o: pd.DataFrame, forward: bool) -> pd.DataFrame:
    rows = []
    for sym, g in o.groupby("symbol"):
        g = g.sort_values("ts").reset_index(drop=True)
        cut = int(len(g) * (TRAIN_FRAC if forward else 1 - TRAIN_FRAC))
        tr, te = (g.iloc[:cut], g.iloc[cut:]) if forward else (g.iloc[cut:], g.iloc[:cut])
        scopes = [(sym, tr, te)] + [(f"{sym} {d}", tr[tr.dir == d], te[te.dir == d])
                                     for d in ("BUY", "SELL") if (tr.dir == d).sum() >= MIN_SCOPE]
        for name, a, b in scopes:
            if len(a) >= MIN_SCOPE and len(b) >= 10:
                rows += search(a.reset_index(drop=True), b.reset_index(drop=True), name)
    res = pd.DataFrame(rows)
    res["yön"] = "ileri" if forward else "geri"
    return res


def generalization(res: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sym, g in res.groupby(res["kapsam"].str.split().str[0]):
        rho = float(np.corrcoef(ranks(g["egitim_R"].to_numpy()), ranks(g["sinama_R"].to_numpy()))[0, 1])
        top = g[g["egitim_R"] >= g["egitim_R"].quantile(0.95)]
        rows.append({"sembol": sym, "kural": len(g), "spearman": rho,
                     "en_iyi_%5_sınamada_+": (top["sinama_R"] > 0).mean(),
                     "en_iyi_%5_rastgeleden_iyi": (top["sinama_R"] > top["sinama_rastgele_R"]).mean()})
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    d = pd.read_parquet(HERE / "data" / "decisions.parquet")
    o = independent(d[d.act == "OPEN"])
    w = independent(d[d.act == "WAIT"])
    print("bağımsız OPEN:", o.groupby("symbol").size().to_dict(), "| WAIT-cf:", w.groupby("symbol").size().to_dict())
    base_table(o, w).to_csv(OUT / "taban.csv", index=False)
    anatomy(o, w).to_csv(OUT / "sl_anatomi.csv", index=False)
    fwd, bwd = run(o, True), run(o, False)
    fwd.to_csv(OUT / "kural_ileri.csv", index=False)
    bwd.to_csv(OUT / "kural_geri.csv", index=False)
    pd.concat([generalization(fwd).assign(yön="ileri"), generalization(bwd).assign(yön="geri")]).to_csv(
        OUT / "genelleme.csv", index=False)
    pd.set_option("display.width", 220)
    for f in ("taban", "sl_anatomi", "genelleme"):
        print(f"\n== {f}\n", pd.read_csv(OUT / f"{f}.csv").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
