"""Ön-kayıt: PROTOCOL.md. python3 research/sl_onleme_kural_20261007/search.py"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from scripts.islem_otopsi import align, build, cli, data  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402

OUT = HERE / "results"
TRAIN_FRAC = 0.6
QS = (0.10, 0.20, 0.33, 0.50, 0.67, 0.80, 0.90)
MIN_BLOCK, MAX_BLOCK_FRAC = 10, 0.5
MIN_SCOPE = 40
TOP_SINGLE, TOP_REPORT = 30, 10
EXCLUDE = {"pre_stale_min", "geo_be_wr"}
CATS = ("session", "family", "dow")
RNG = np.random.default_rng(20261007)


def load() -> pd.DataFrame:
    a = cli.parse_args(["--base-days", "200", "--no-vix"])
    now = data.utc_now()
    al, bars, fps, vix, _ = cli.load_everything(a, now)
    sbs = {k: SymbolBars(k, v) for k, v in bars.items() if len(v)}
    t, _ = build.build_table(al.trades, sbs, fps, data.load_vix(now - pd.Timedelta(days=200), now), now)
    t["decision_id"] = align.assign_decisions(t)
    t = t.sort_values("entry_utc").drop_duplicates("decision_id")
    return t[t["r_exit"].notna()].reset_index(drop=True)


def numeric_cols(t: pd.DataFrame) -> list[str]:
    cols = [c for c in t.columns if c.startswith(("pre_", "geo_", "ctx_")) and c not in EXCLUDE
            and pd.api.types.is_numeric_dtype(t[c]) and t[c].notna().mean() > 0.5]
    return cols + ["hour_utc", "min_from_us_open"]


def singles(tr: pd.DataFrame, cols: list[str]) -> list[tuple]:
    """(ad, maske-fonksiyonu girdisi) — eşikler EĞİTİM verisinden."""
    rules = []
    for c in cols:
        x = tr[c].dropna()
        vals = sorted(set(x.unique())) if x.nunique() <= 2 else sorted({float(x.quantile(q)) for q in QS})
        for v in vals:
            if x.nunique() <= 2:
                rules.append((f"{c} = {v:g}", c, "==", v))
            else:
                rules.append((f"{c} ≥ {v:.4g}", c, ">=", v))
                rules.append((f"{c} ≤ {v:.4g}", c, "<=", v))
    for c in CATS:
        for v in tr[c].dropna().unique():
            rules.append((f"{c} = {v}", c, "==", v))
    return rules


def mask(df: pd.DataFrame, rule: tuple) -> np.ndarray:
    _, c, op, v = rule
    x = df[c]
    m = (x >= v) if op == ">=" else (x <= v) if op == "<=" else (x == v)
    return m.fillna(False).to_numpy()


def score(df: pd.DataFrame, m: np.ndarray) -> dict:
    b = df[m]
    return {"engel": int(m.sum()), "engel_sl": int((b["outcome"] == "SL").sum()),
            "engel_tp": int((b["outcome"] == "TP").sum()), "kurtarilan_R": float(-b["r_exit"].sum())}


def ok_size(m: np.ndarray) -> bool:
    return MIN_BLOCK <= m.sum() <= MAX_BLOCK_FRAC * m.size


def search_scope(tr: pd.DataFrame, te: pd.DataFrame, cols: list[str], scope: str) -> pd.DataFrame:
    rules = singles(tr, cols)
    rows = []
    for r in rules:
        m = mask(tr, r)
        if ok_size(m):
            rows.append((r, m, score(tr, m)["kurtarilan_R"]))
    rows.sort(key=lambda x: -x[2])
    top = rows[:TOP_SINGLE]
    combos = [((f"{a[0][0]} VE {b[0][0]}",), a[0], b[0], a[1] & b[1]) for a, b in itertools.combinations(top, 2)]
    out = []
    for r, m, _ in rows:
        out.append(_record(scope, r[0], [r], tr, te, m, "tekli"))
    for (name,), ra, rb, m in combos:
        if ok_size(m):
            out.append(_record(scope, name, [ra, rb], tr, te, m, "ikili"))
    return pd.DataFrame(out)


def _record(scope: str, name: str, rules: list, tr: pd.DataFrame, te: pd.DataFrame, m_tr: np.ndarray, kind: str) -> dict:
    m_te = np.ones(len(te), dtype=bool)
    for r in rules:
        m_te &= mask(te, r)
    s_tr, s_te = score(tr, m_tr), score(te, m_te)
    rand = -m_te.sum() * te["r_exit"].mean()
    return {"kapsam": scope, "kural": name, "tur": kind, **{f"egitim_{k}": v for k, v in s_tr.items()},
            **{f"sinama_{k}": v for k, v in s_te.items()}, "sinama_rastgele_R": rand}


def run_split(t: pd.DataFrame, train_first: bool) -> pd.DataFrame:
    cut = int(len(t) * TRAIN_FRAC) if train_first else int(len(t) * (1 - TRAIN_FRAC))
    a, b = t.iloc[:cut], t.iloc[cut:]
    tr, te = (a, b) if train_first else (b, a)
    cols = numeric_cols(t)
    scopes = [("TÜMÜ", tr, te)]
    for side, g in tr.groupby("side"):
        if len(g) >= MIN_SCOPE:
            scopes.append((side, g, te[te["side"] == side]))
    res = pd.concat([search_scope(x, y, cols, s) for s, x, y in scopes], ignore_index=True)
    res["yon"] = "ileri" if train_first else "geri"
    return res


def placebo_corr(res: pd.DataFrame) -> dict:
    from scripts.islem_otopsi.stats import ranks
    x, y = res["egitim_kurtarilan_R"].to_numpy(), res["sinama_kurtarilan_R"].to_numpy()
    rho = float(np.corrcoef(ranks(x), ranks(y))[0, 1])
    top = res[res["egitim_kurtarilan_R"] >= res["egitim_kurtarilan_R"].quantile(0.95)]
    return {"kural_sayisi": len(res), "spearman_egitim_sinama": rho,
            "en_iyi_%5_sinamada_pozitif": float((top["sinama_kurtarilan_R"] > 0).mean()),
            "en_iyi_%5_rastgeleden_iyi": float((top["sinama_kurtarilan_R"] > top["sinama_rastgele_R"]).mean()),
            "tum_kurallar_sinamada_pozitif": float((res["sinama_kurtarilan_R"] > 0).mean())}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    t = load()
    print("karar:", len(t), t["entry_utc"].min(), "→", t["entry_utc"].max())
    fwd, bwd = run_split(t, True), run_split(t, False)
    fwd.to_csv(OUT / "ileri.csv", index=False)
    bwd.to_csv(OUT / "geri.csv", index=False)
    for name, res in (("ileri", fwd), ("geri", bwd)):
        print(name, placebo_corr(res))


if __name__ == "__main__":
    main()
