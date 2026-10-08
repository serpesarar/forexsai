"""Ön-kayıt: PROTOCOL.md. python3 research/tpsl_opt_20261008/run.py"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from scripts.islem_otopsi import align, build, cli, data  # noqa: E402
from scripts.islem_otopsi.features import make_ctx  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402
from scripts.islem_otopsi.placebo import simulate  # noqa: E402
from scripts.islem_otopsi.stats import ranks  # noqa: E402

OUT = HERE / "results"
SLS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5)
TPS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0)
TRAIN_DAYS = 45
MIN_TRAIN = 20


def load() -> tuple[pd.DataFrame, dict]:
    a = cli.parse_args(["--base-days", "200", "--no-vix"])
    now = data.utc_now()
    al, bars, fps, vix, _ = cli.load_everything(a, now)
    sbs = {k: SymbolBars(k, v) for k, v in bars.items() if len(v)}
    t, _ = build.build_table(al.trades, sbs, fps, vix, now)
    t["decision_id"] = align.assign_decisions(t)
    t = t[t["family"] != "MANUEL"].sort_values("entry_utc").drop_duplicates("decision_id")
    t["donem"] = np.where(t["entry_utc"] >= now - pd.Timedelta(days=TRAIN_DAYS), "egitim", "test")
    return t.reset_index(drop=True), sbs


def replay_grid(t: pd.DataFrame, sbs: dict) -> pd.DataFrame:
    rows = []
    for _, r in t.iterrows():
        c = make_ctx(r, sbs[r["symbol"]])
        if c is None or not (np.isfinite(c.risk) and np.isfinite(c.reward)) or c.i_exit < c.i_in0:
            continue
        base = {"pid": r["pid"], "symbol": r["symbol"].split(".")[0], "side": r["side"], "family": r["family"],
                "donem": r["donem"], "gercek": r["outcome"], "gercek_R": r["r_exit"]}
        for slm in SLS:
            for tpm in TPS:
                R, j, _ = simulate(c.sb, c.s, c.entry, c.i_in0, c.risk * slm, c.reward * tpm, c.spread)
                rows.append({**base, "sl_x": slm, "tp_x": tpm, "R_risk": R, "R_lot": R * slm, "acik": j < 0})
    return pd.DataFrame(rows)


def calibration(g: pd.DataFrame) -> float:
    b = g[(g.sl_x == 1.0) & (g.tp_x == 1.0) & g.gercek.isin(["TP", "SL"])]
    return float(((b.R_risk > 0) == (b.gercek == "TP")).mean())


def cell_table(g: pd.DataFrame) -> pd.DataFrame:
    agg = g.groupby(["sl_x", "tp_x"]).agg(n=("pid", "nunique"), lot_R=("R_lot", "sum"), risk_R=("R_risk", "mean"),
                                          wr=("R_risk", lambda x: (x > 0).mean()))
    return agg.reset_index()


def neighbourhood(tab: pd.DataFrame, slm: float, tpm: float) -> float:
    i, j = SLS.index(slm), TPS.index(tpm)
    nb = tab[tab.sl_x.isin(SLS[max(0, i - 1):i + 2]) & tab.tp_x.isin(TPS[max(0, j - 1):j + 2])]
    return float(nb.lot_R.mean())


def evaluate(g: pd.DataFrame, scope: str) -> dict | None:
    tr, te = g[g.donem == "egitim"], g[g.donem == "test"]
    ntr, nte = tr.pid.nunique(), te.pid.nunique()
    if ntr < MIN_TRAIN or nte < MIN_TRAIN:
        return None
    a, b = cell_table(tr), cell_table(te)
    best = a.loc[a.lot_R.idxmax()]
    m = a.merge(b, on=["sl_x", "tp_x"], suffixes=("_egt", "_tst"))
    rho = float(np.corrcoef(ranks(m.lot_R_egt.to_numpy()), ranks(m.lot_R_tst.to_numpy()))[0, 1])
    tb = b.set_index(["sl_x", "tp_x"])
    cur_tr, cur_te = a.set_index(["sl_x", "tp_x"]).loc[(1.0, 1.0)], tb.loc[(1.0, 1.0)]
    sel_te = tb.loc[(best.sl_x, best.tp_x)]
    rank_te = int((b.lot_R > sel_te.lot_R).sum()) + 1
    return {"kapsam": scope, "egitim_n": ntr, "test_n": nte,
            "mevcut_egitim_R": cur_tr.lot_R, "mevcut_test_R": cur_te.lot_R,
            "en_iyi": f"SL×{best.sl_x:g} TP×{best.tp_x:g}", "en_iyi_egitim_R": best.lot_R,
            "en_iyi_komsu_ort": neighbourhood(a, best.sl_x, best.tp_x),
            "en_iyi_test_R": sel_te.lot_R, "test_farki": sel_te.lot_R - cur_te.lot_R,
            "en_iyi_test_wr": sel_te.wr, "mevcut_test_wr": cur_te.wr,
            "test_sirasi": f"{rank_te}/{len(b)}", "spearman": rho,
            "test_en_iyisi": f"SL×{b.loc[b.lot_R.idxmax()].sl_x:g} TP×{b.loc[b.lot_R.idxmax()].tp_x:g}"}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    t, sbs = load()
    print("karar:", len(t), t.groupby(["donem"]).size().to_dict())
    g = replay_grid(t, sbs)
    g.to_csv(OUT / "grid.csv", index=False)
    print("kalibrasyon (1,1) vs gerçek:", round(calibration(g), 3))
    rows = []
    for key, sub in list(g.groupby("side")) + list(g.groupby("symbol")):
        r = evaluate(sub, key)
        if r:
            rows.append(r)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "ozet.csv", index=False)
    pd.set_option("display.width", 250)
    print(res.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
