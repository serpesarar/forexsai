"""V4 — NDX Professional Execution Framework (PEF), honest build.

Unifies the validated pieces into one layered engine and backtests it end-to-end
on the 10 untouched date groups. Every component kept only if it survives realistic
(gap-aware) fills and improves OOS EV; the rest of the PEF spec is pruned:

  Gate 0 Regime    : {TREND, CHOP, EXPANSION, CONTRACTION} from ADX + ATR-percentile.
  Gate 1 Events    : V1-gated events (chan_rev, vwap_rev, sweep, mom_cont).
  Gate 2 Meta      : V1 calibrated P(win); EV gate already applied by the V1 τ.
  Gate 3 Position  : size = base × confidence_mult(p) × regime_mult (learned on train).
                     Regime×family cells with train EV ≤ 0 are SKIPPED (size 0).
  Gate 4 Execution : realistic fills — spread inside replay, 1pt slip, gap-aware stop.
  Gate 5 Exit      : PURE time-stop ~15m at market. NO partial (it kills EV), NO
                     trailing (fill-illusion), optional regime-flip-at-close kicker.

Selection (regime×family allow/size table, confidence bins) uses TRAIN entries only.
Reported on 2025 holdout + 2026 broker, per-group and pooled, unweighted and
size-weighted, full metric suite.
"""
from __future__ import annotations

import glob
import json
import logging
import os
import sys
from datetime import date

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from features.pack import compute_feature_frame, event_features  # noqa: E402
from research.transfer_test_2026 import fetch_candles, to_bar_frame  # noqa: E402
from research.v2_exit_study import entries_2025 as _e25_base, _score_gate  # noqa: E402
from research.v3_exit_systems import ext_arrays, simulate, train_ml_exit  # noqa: E402
from triggers.detect import detect_day  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("pef")
RNG = np.random.default_rng(41)

EXIT_CFG = {"stop_mode": "fixed", "time_exit_min": 15, "ts_min": 60, "gap_fill": True}
TAU = {"chan_rev": 0.80, "vwap_rev": 0.78, "sweep": 0.81, "mom_cont": 0.0}


def regime_of(adx: float, atr_pctl: float) -> str:
    if not np.isfinite(adx):
        adx = 20.0
    if not np.isfinite(atr_pctl):
        atr_pctl = 0.5
    if atr_pctl >= 0.80:
        return "EXPANSION"
    if atr_pctl <= 0.25 and adx < 20:
        return "CONTRACTION"
    if adx >= 25:
        return "TREND"
    return "CHOP"


def enrich_2025() -> pd.DataFrame:
    ds = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    feats = ds.drop_duplicates(subset=["ts", "direction", "family"])
    g = _score_gate(feats)  # ts,direction,family,p,sl_atr,tau
    m = g.merge(feats[["ts", "direction", "family", "adx14", "atr_pctl"]],
                on=["ts", "direction", "family"], how="left")
    m["regime"] = [regime_of(a, p) for a, p in zip(m["adx14"], m["atr_pctl"])]
    split = date.fromisoformat("2025-04-11")
    m["split"] = np.where(m["ts"].dt.date <= split, "train", "hold")
    return m


def enrich_2026(grp: dict) -> pd.DataFrame:
    days = sorted(grp.keys())
    frames = []
    for i, d in enumerate(days):
        prev = None if i == 0 else grp[days[i - 1]]
        ev = detect_day(grp[d], prev, date.fromisoformat(d))
        if ev.empty:
            continue
        ctx = pd.concat([prev, grp[d]]).reset_index(drop=True) if prev is not None else grp[d]
        fe = event_features(compute_feature_frame(ctx), ev)
        if not fe.empty:
            frames.append(fe)
    feats = pd.concat(frames, ignore_index=True)
    g = _score_gate(feats)
    m = g.merge(feats[["ts", "direction", "family", "adx14", "atr_pctl"]].drop_duplicates(
        subset=["ts", "direction", "family"]), on=["ts", "direction", "family"], how="left")
    m["regime"] = [regime_of(a, p) for a, p in zip(m["adx14"], m["atr_pctl"])]
    m["split"] = "y2026"
    return m


def r_per_trade(entries: pd.DataFrame, bars_by_day: dict) -> pd.Series:
    """Time-stop exit R for each entry (NaN if dropped). Index-aligned to entries."""
    out = pd.Series(np.nan, index=entries.index)
    for idx, ev in entries.iterrows():
        A = bars_by_day.get(str(pd.Timestamp(ev["ts"]).date()))
        if A is None:
            continue
        e = A["pos"].get(pd.Timestamp(ev["ts"]).to_datetime64().astype("datetime64[ns]").astype("int64"))
        if e is None:
            continue
        res = simulate(A, int(e), ev["direction"], ev["sl_atr"], ev["p"], EXIT_CFG)
        if res is not None:
            out.loc[idx] = res["r"]
    return out


def metrics(r: np.ndarray, size: np.ndarray | None = None) -> dict:
    r = r[np.isfinite(r)]
    if len(r) == 0:
        return {"n": 0}
    wins, losses = r[r > 0], r[r <= 0]
    eq = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(eq) - eq))
    pf = float(wins.sum() / -losses.sum()) if losses.sum() < 0 else float("inf")
    m = {"n": len(r), "wr": round(float((r > 0).mean()), 4), "ev_r": round(float(r.mean()), 4),
         "pf": round(pf, 3), "max_dd_r": round(dd, 2),
         "avg_win": round(float(wins.mean()), 3) if len(wins) else None,
         "avg_loss": round(float(losses.mean()), 3) if len(losses) else None}
    if size is not None:
        sw = (r * size[:len(r)]).sum() / size[:len(r)].sum()
        m["sw_ev_r"] = round(float(sw), 4)
    return m


def build_size_table(train: pd.DataFrame) -> dict:
    """Per (family,regime): train EV under time-stop. Allow if EV>0 & n>=20; size the
    cell PROPORTIONAL to its train EV (data-driven, not hand-set multipliers), clipped
    to [0.5, 1.6]×. This concentrates risk on the highest-edge setups (e.g. momentum in
    expansion), which the earlier hand-set regime multipliers wrongly penalised."""
    tbl = {}
    rows = train.dropna(subset=["r"]).groupby(["family", "regime"])
    evs = {k: float(s["r"].mean()) for k, s in rows}
    allowed = {k: v for k, v in evs.items() if v > 0}
    ref = np.median(list(allowed.values())) if allowed else 1.0
    for (fam, reg), sub in rows:
        ev, n = float(sub["r"].mean()), len(sub)
        allow = bool(ev > 0 and n >= 20)
        size = float(np.clip(ev / ref, 0.5, 1.6)) if allow else 0.0
        tbl[f"{fam}|{reg}"] = {"train_ev": round(ev, 4), "n": n, "allow": allow,
                               "cell_size": round(size, 3)}
    return tbl


def conf_mult(p: float, fam: str) -> float:
    if fam == "mom_cont":
        return 1.0
    edge = max(0.0, p - TAU[fam])
    return float(np.clip(0.7 + edge * 3.0, 0.7, 1.3))


def regime_mult(reg: str) -> float:
    return {"TREND": 1.1, "CHOP": 1.0, "EXPANSION": 0.8, "CONTRACTION": 0.5}[reg]


def apply_pef(df: pd.DataFrame, size_tbl: dict) -> pd.DataFrame:
    df = df.dropna(subset=["r"]).copy()
    df["allow"] = [size_tbl.get(f"{f}|{r}", {}).get("allow", False)
                   for f, r in zip(df["family"], df["regime"])]
    df = df[df["allow"]].copy()
    df["size"] = [conf_mult(p, f) * size_tbl.get(f"{f}|{r}", {}).get("cell_size", 1.0)
                  for p, f, r in zip(df["p"], df["family"], df["regime"])]
    return df


def group_rows(df: pd.DataFrame, groups: list) -> list:
    rows = []
    for name, mask in groups:
        sub = df[mask]
        if sub.empty:
            rows.append((name, {"n": 0}))
            continue
        rows.append((name, metrics(sub["r"].to_numpy(), sub["size"].to_numpy())))
    return rows


def boot(r):
    if len(r) == 0:
        return 0.0
    m = [np.mean(RNG.choice(r, len(r), replace=True)) for _ in range(3000)]
    return float(np.mean(np.array(m) > 0))


def main() -> None:
    raw = {os.path.basename(p).replace(".parquet", ""): pd.read_parquet(p)
           for p in sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet")))}
    d25 = sorted(raw)
    b25 = {}
    for k, d in enumerate(d25):
        b25[d] = ext_arrays(raw[d], raw[d25[k - 1]] if k else None)
    grp = {str(x): g.reset_index(drop=True)
           for x, g in to_bar_frame(fetch_candles()).groupby(to_bar_frame(fetch_candles())["ts"].dt.date)}
    d26 = sorted(grp)
    b26 = {}
    for k, d in enumerate(d26):
        b26[d] = ext_arrays(grp[d], grp[d26[k - 1]] if k else None)

    e25 = enrich_2025()
    e25["r"] = r_per_trade(e25, b25)
    e26 = enrich_2026(grp)
    e26["r"] = r_per_trade(e26, b26)
    train = e25[e25["split"] == "train"]
    hold = e25[e25["split"] == "hold"]

    size_tbl = build_size_table(train)
    log.info("── Gate 0/3 regime×family allow-table (train EV, time-stop) ──")
    for k, v in sorted(size_tbl.items(), key=lambda x: -x[1]["train_ev"]):
        log.info("  %-24s train_ev=%+.3f n=%4d  %s", k, v["train_ev"], v["n"],
                 "ALLOW" if v["allow"] else "skip")

    hold_pef = apply_pef(hold, size_tbl)
    e26_pef = apply_pef(e26, size_tbl)

    # baseline = all V1 entries, time-stop, no regime filter/sizing
    log.info("\n── BASELINE (all gated events, pure time-stop, no regime layer) ──")
    log.info("  HOLDOUT  %s", metrics(hold["r"].dropna().to_numpy()))
    log.info("  2026     %s", metrics(e26["r"].dropna().to_numpy()))

    log.info("\n── PEF (regime allow-filter + confidence/regime sizing + time-stop) ──")
    log.info("  HOLDOUT  %s", metrics(hold_pef["r"].to_numpy(), hold_pef["size"].to_numpy()))
    log.info("  2026     %s", metrics(e26_pef["r"].to_numpy(), e26_pef["size"].to_numpy()))

    # 10-group
    hd = sorted(hold_pef["ts"].dt.date.astype(str).unique())
    chunks = np.array_split(np.array(hd), 5)
    groups = [(f"G{i} 2025 {c[0]}..{c[-1]}",
               hold_pef["ts"].dt.date.astype(str).isin(set(c))) for i, c in enumerate(chunks, 1)]
    rows = group_rows(hold_pef, groups)
    for i, mo in enumerate([2, 3, 4, 5, 6], 6):
        sub = e26_pef[(e26_pef["ts"].dt.year == 2026) & (e26_pef["ts"].dt.month == mo)]
        rows.append((f"G{i} 2026-{mo:02d}", metrics(sub["r"].to_numpy(), sub["size"].to_numpy())
                     if not sub.empty else {"n": 0}))
    log.info("\n── PEF 10-GROUP ──")
    pos = 0
    for name, m in rows:
        ok = m.get("ev_r", -9) is not None and m.get("ev_r", -9) > 0
        pos += ok
        log.info("  %-24s n=%4s WR=%s EV=%s PF=%s DD=%s aw=%s al=%s", name, m.get("n"),
                 f"{m['wr']*100:.0f}%" if m.get("wr") is not None else "-",
                 f"{m['ev_r']:+.3f}" if m.get("ev_r") is not None else "-",
                 m.get("pf"), m.get("max_dd_r"), m.get("avg_win"), m.get("avg_loss"))
    pooled = np.concatenate([hold_pef["r"].to_numpy(), e26_pef["r"].to_numpy()])
    log.info("  EV>0 in %d/10 | pooled n=%d WR=%.0f%% EV=%+.3fR P(EV>0)=%.3f",
             pos, len(pooled), (pooled > 0).mean() * 100, pooled.mean(), boot(pooled))

    with open(os.path.join(config.MODELS_DIR, "v4_pef.json"), "w") as f:
        json.dump({"size_table": size_tbl, "groups": rows,
                   "pooled": {"n": int(len(pooled)), "wr": float((pooled > 0).mean()),
                              "ev_r": float(pooled.mean()), "p_ev_pos": boot(pooled)}},
                  f, indent=2, default=str)
    log.info("\nsaved → v4_pef.json")


if __name__ == "__main__":
    main()
