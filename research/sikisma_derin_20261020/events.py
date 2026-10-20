"""Olay tabloları (S1–S8) + karar anı sıkışma özellikleri → results/ev_<kaynak>.parquet. Bkz. PROTOCOL.md.

python3 research/sikisma_derin_20261020/events.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import core as C

OUT = C.HERE / "results"
TRADES = C.ROOT / "output" / "islem_otopsi" / "2026-10-20_1429_all" / "islemler.csv"
SNAP_START = "2026-05-20"
DEDUP_MIN = 30
BRK_LOOKBACK, BODY_MIN = 12, 0.5
SYMS = ("NDX.INDX", "GDAXI.INDX", "USOIL.FOREX", "XAUUSD")


def dedup(ev: pd.DataFrame, keys: list[str], minutes: int = DEDUP_MIN) -> pd.DataFrame:
    keep = []
    for _, g in ev.sort_values("t").groupby(keys):
        last = None
        for i, t in zip(g.index, g.t):
            if last is None or t - last >= pd.Timedelta(minutes=minutes):
                keep.append(i)
                last = t
    return ev.loc[keep].sort_values("t").reset_index(drop=True)


def bot_trades() -> pd.DataFrame:
    d = pd.read_csv(TRADES)
    d = d[d.outcome.isin(["TP", "SL", "BE", "DIGER_+", "DIGER_-"])].copy()
    return pd.DataFrame({"t": pd.to_datetime(d.entry_utc, utc=True), "sym": d.symbol, "s": np.where(d.direction == "BUY", 1, -1),
                         "fam": d.family, "R": d.r_exit.astype(float), "net": d.net,
                         "risk_frac": (d.open_price - d.sl0).abs() / d.open_price})


def breakout_events(df1m: pd.DataFrame) -> pd.DataFrame:
    """5m kapanış önceki 12 barın tepesini (dibini) gövdeli mumla kırar → M yönü; karar = 5m bar sonu."""
    g = df1m.resample("5min", label="left", closed="left")
    b = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()}).dropna()
    hh = b.high.shift(1).rolling(BRK_LOOKBACK).max()
    ll = b.low.shift(1).rolling(BRK_LOOKBACK).min()
    rng = (b.high - b.low).replace(0, np.nan)
    body = (b.close - b.open) / rng
    up = (b.close > hh) & (body > BODY_MIN)
    dn = (b.close < ll) & (body < -BODY_MIN)
    t = b.index + pd.Timedelta(minutes=5)
    ev = pd.concat([pd.DataFrame({"t": t[up.to_numpy()], "s": 1}), pd.DataFrame({"t": t[dn.to_numpy()], "s": -1})])
    return dedup(ev, ["s"])


def add(ev: pd.DataFrame, F: pd.DataFrame) -> pd.DataFrame:
    ev = ev.reset_index(drop=True)
    return pd.concat([ev, C.feats_at(F, ev.t).reset_index(drop=True)], axis=1)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    bot = bot_trades()
    rf = bot.groupby("sym").risk_frac.median().to_dict()
    rf["NDX.INDX"] = C.NDX_RISK_FRAC
    print("risk_frac:", {k: round(v, 5) for k, v in rf.items()})

    snap = {s: C.bars_snapshots(s, SNAP_START) for s in SYMS}
    Fs = {s: C.compute_feats(b) for s, b in snap.items()}
    sbs = {s: C.SymbolBars(s, b) for s, b in snap.items()}

    # S1 bot (tüm semboller, gerçek R)
    parts = [add(bot[bot.sym == s], Fs[s]) for s in SYMS if (bot.sym == s).any()]
    pd.concat(parts).sort_values("t").to_parquet(OUT / "ev_S1_bot.parquet")

    # S2 engellenen NDX SELL sinyalleri (kovalama_saglamlik G1 simülasyonu, aynı geometri)
    sk = pd.read_csv(C.ROOT / "research" / "kovalama_saglamlik_20261010" / "results" / "skipped_sim_G1.csv")
    sk = pd.DataFrame({"t": pd.to_datetime(sk.t, utc=True), "s": -1, "fam": sk.aile, "reason": sk.reason, "R": sk.R})
    add(sk, Fs["NDX.INDX"]).to_parquet(OUT / "ev_S2_skipped.parquet")

    nd = sbs["NDX.INDX"]
    # S3 panel modelleri NDX
    p = pd.read_parquet(C.ROOT / "research" / "donus_vs_sl_20261009" / "results" / "panel.parquet")
    p = p[p.symbol == "NDX.INDX"]
    p = pd.DataFrame({"t": p.ts, "s": np.where(p.ml_direction == "BUY", 1, -1), "fam": p.model_type})
    p = dedup(p, ["fam", "s"])
    p["R"] = C.sim_events(nd, p, rf["NDX.INDX"], C.SPREAD["NDX.INDX"])
    add(p, Fs["NDX.INDX"]).to_parquet(OUT / "ev_S3_panel.parquet")

    # S4 decider NDX
    dc = pd.read_parquet(C.ROOT / "research" / "decider_kural_20261008" / "data" / "decisions.parquet")
    dc = dc[dc.symbol.str.startswith("NDX") & dc.dir.isin(["BUY", "SELL"])]
    dc = pd.DataFrame({"t": pd.to_datetime(dc.ts, utc=True), "s": np.where(dc.dir == "BUY", 1, -1), "fam": dc.act})
    dc["R"] = C.sim_events(nd, dc, rf["NDX.INDX"], C.SPREAD["NDX.INDX"])
    add(dc, Fs["NDX.INDX"]).to_parquet(OUT / "ev_S4_decider.parquet")

    # S5/S6/S8 uzun NDX (2025-01 → 2026-09)
    long = C.bars_ndx_long()
    FL = C.compute_feats(long)
    sbl = C.SymbolBars("NDX.INDX", long)
    dcb = pd.read_parquet(C.ROOT / "research" / "canli_kart_20261009" / "results" / "daycombo_trades.parquet")
    dcb = pd.DataFrame({"t": dcb.entry, "s": 1, "fam": dcb.period, "R": dcb.R})
    add(dcb, FL).to_parquet(OUT / "ev_S5_daycombo.parquet")

    br = breakout_events(long)
    br["R"] = C.sim_events(sbl, br, rf["NDX.INDX"], C.SPREAD["NDX.INDX"])
    add(br.assign(fam="momentum"), FL).to_parquet(OUT / "ev_S6M_ndx.parquet")
    rv = br[["t", "s"]].assign(s=-br.s, fam="donus")
    rv["R"] = C.sim_events(sbl, rv, rf["NDX.INDX"], C.SPREAD["NDX.INDX"])
    add(rv, FL).to_parquet(OUT / "ev_S6R_ndx.parquet")

    idx = long.index
    hrs = idx[(idx.minute == 0) & (idx.hour >= 6) & (idx.hour <= 20) & (idx.dayofweek < 5)]
    pl = pd.DataFrame({"t": hrs + pd.Timedelta(minutes=1), "s": C.RNG.choice([-1, 1], hrs.size), "fam": "plasebo"})
    pl["R"] = C.sim_events(sbl, pl, rf["NDX.INDX"], C.SPREAD["NDX.INDX"])
    add(pl, FL).to_parquet(OUT / "ev_S8_placebo.parquet")

    # S7 diğer semboller: momentum + dönüş + plasebo (snapshot dönemi)
    for s in SYMS[1:]:
        b = breakout_events(snap[s])
        b["R"] = C.sim_events(sbs[s], b, rf.get(s, C.NDX_RISK_FRAC), C.SPREAD[s])
        r2 = b[["t", "s"]].assign(s=-b.s)
        r2["R"] = C.sim_events(sbs[s], r2, rf.get(s, C.NDX_RISK_FRAC), C.SPREAD[s])
        tag = s.split(".")[0]
        add(b.assign(fam="momentum", sym=s), Fs[s]).to_parquet(OUT / f"ev_S7M_{tag}.parquet")
        add(r2.assign(fam="donus", sym=s), Fs[s]).to_parquet(OUT / f"ev_S7R_{tag}.parquet")
        ix = snap[s].index
        h = ix[(ix.minute == 0) & (ix.dayofweek < 5)]
        pls = pd.DataFrame({"t": h + pd.Timedelta(minutes=1), "s": C.RNG.choice([-1, 1], h.size), "fam": "plasebo", "sym": s})
        pls["R"] = C.sim_events(sbs[s], pls, rf.get(s, C.NDX_RISK_FRAC), C.SPREAD[s])
        add(pls, Fs[s]).to_parquet(OUT / f"ev_S8_placebo_{tag}.parquet")

    for f in sorted(OUT.glob("ev_*.parquet")):
        d = pd.read_parquet(f)
        print(f"{f.stem:22s} n={len(d):6d} R ok={int(np.isfinite(d.R).sum()):6d} ortR {np.nanmean(d.R):+.3f} "
              f"sqz ok={int(d.atr_14_100.notna().sum())}")


if __name__ == "__main__":
    main()
