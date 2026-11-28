"""SY — canlı NDX kitabında SL tipleri: aile/yön yasağı (A) + donmuş işlem-tipi bayrakları (B). Ön kayıt: ../PROTOCOL.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/canli_kart_20261009"))
from scripts.islem_otopsi import align, data  # noqa: E402
import live_card as LC  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
OUT.mkdir(exist_ok=True)
SINCE = pd.Timestamp("2026-06-01", tz="UTC")
FWD = pd.Timestamp("2026-10-10", tz="UTC")
FWD2 = pd.Timestamp("2026-10-30", tz="UTC")
SL_R = -0.7
RNG = np.random.default_rng(20261128)
NB = 2000


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    tr = data.load_trades(data.get_client(), SINCE)
    tr = tr[tr.symbol == "NDX.INDX"].reset_index(drop=True)
    pad = pd.Timedelta(hours=8)
    need = {"NDX.INDX": (tr.open_raw.min() - pad, tr.close_raw.max() + pad)}
    bars = data.load_bars(["NDX.INDX"], need)
    al = align.align_trades(tr, bars)
    print(f"hizalama {al.status} kesin={al.aligned_frac:.2f} dışlanan={len(al.excluded)}")
    t = LC.per_trade(al.trades, bars, LC.point_values(al.trades))
    return t, bars["NDX.INDX"]


def decisions(t: pd.DataFrame) -> pd.DataFrame:
    out = []
    for fam, g in t.groupby("family"):
        g = g.sort_values("entry_utc").copy()
        g["dec"] = align.assign_decisions(g).values
        a = g.groupby("dec")
        d = pd.DataFrame({"entry": a.entry_utc.min(), "exit": a.exit_utc.max(), "side": a.direction.first(),
                          "net": a.net.sum(), "risk": a.risk_usd.sum(), "legs": a.size(),
                          "risk_pts": a.risk_pts.first(), "entry_px": a.open_price.first()})
        d["R"] = d.net / d.risk
        d["family"] = fam
        out.append(d)
    d = pd.concat(out).sort_values("entry").reset_index(drop=True)
    d["fs"] = d.family + " " + d.side
    d["day"] = d.entry.dt.strftime("%Y-%m-%d")
    return d


def bar_feats(d: pd.DataFrame, m1: pd.DataFrame) -> pd.DataFrame:
    m1 = m1.sort_index()
    tr1 = pd.concat([m1.high - m1.low, (m1.high - m1.close.shift()).abs(), (m1.low - m1.close.shift()).abs()], axis=1).max(1)
    atr1 = tr1.rolling(14).mean()
    m5 = m1.resample("5min", label="left", closed="left").agg({"high": "max", "low": "min", "close": "last"}).dropna()
    tr5 = pd.concat([m5.high - m5.low, (m5.high - m5.close.shift()).abs(), (m5.low - m5.close.shift()).abs()], axis=1).max(1)
    atr5 = tr5.rolling(14).mean()
    end5 = m5.index + pd.Timedelta(minutes=5)
    idx1 = m1.index + pd.Timedelta(minutes=1)          # bar bitişi
    nr, mom = [], []
    for r in d.itertuples():
        i = idx1.searchsorted(r.entry, side="right") - 1          # bitişi ≤ giriş
        j = end5.searchsorted(r.entry, side="right") - 1
        if i < 60 or j < 14:
            nr.append(np.nan); mom.append(np.nan); continue
        a1 = atr1.iat[i]
        nr.append(r.risk_pts / (a1 * np.sqrt(30)) if a1 > 0 else np.nan)
        s = 1 if r.side.upper() == "BUY" else -1
        mom.append(s * (m1.close.iat[i] - m1.close.iat[i - 60]) / atr5.iat[j])
    d["NR"], d["mom60_atr5"] = nr, mom
    return d


def stack_feats(d: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    legs = t[["entry_utc", "exit_utc", "direction", "open_price", "family"]].copy()
    y1, y2 = [], []
    for r in d.itertuples():
        o = legs[(legs.entry_utc < r.entry - pd.Timedelta(minutes=2)) & (legs.exit_utc > r.entry)
                 & (legs.direction == r.side)]
        y1.append(len(o) > 0)
        s = 1 if r.side.upper() == "BUY" else -1
        y2.append(bool(len(o) and ((s * (r.entry_px - o.open_price)) < 0).any()))
    d["B3_Y1"], d["B2_Y2"] = y1, y2
    sl = d[d.R <= SL_R]
    d["B4_kotu_gun"] = [int(((sl.day == r.day) & (sl.exit < r.entry)).sum()) >= 2 for r in d.itertuples()]
    return d


def strat_delta(d: pd.DataFrame, flag: str) -> float:
    num = w = 0.0
    for _, g in d.groupby("fs"):
        f = g[flag].astype(bool)
        if f.sum() and (~f).sum():
            num += f.sum() * (g.R[f].mean() - g.R[~f].mean()); w += f.sum()
    return num / w if w else np.nan


def boot_delta(d: pd.DataFrame, flag: str) -> float:
    days = d.day.unique(); grp = {k: g for k, g in d.groupby("day")}
    vals = []
    for _ in range(NB):
        pick = RNG.choice(days, len(days))
        vals.append(strat_delta(pd.concat([grp[k] for k in pick]), flag))
    v = np.array(vals); v = v[np.isfinite(v)]
    return float((v < 0).mean())


def placebo(d: pd.DataFrame, flag: str, obs: float, n: int = 1000) -> float:
    vals = []
    for _ in range(n):
        x = d.copy()
        for k, g in x.groupby("fs"):
            arr = g[flag].to_numpy()
            x.loc[g.index, flag] = np.roll(arr, RNG.integers(1, max(2, len(arr))))
        vals.append(strat_delta(x, flag))
    v = np.array(vals)
    return float((v <= obs).mean())


def family_table(d: pd.DataFrame) -> list[dict]:
    rows = []
    for k, g in d.groupby("fs"):
        if len(g) < 30:
            continue
        pre, fwd = g[g.entry < FWD], g[g.entry >= FWD]
        p_pos, _ = LC.boot_p(g.R.to_numpy(), g.day.to_numpy())
        m = g.R.mean()
        ban = m < 0 and (1 - p_pos) >= 0.80 and pre.R.mean() <= 0 and fwd.R.mean() <= 0 and g.net.sum() < 0
        dead = (not ban) and abs(m) < 0.03 and (pre.R.mean() <= 0.03) and (fwd.R.mean() <= 0.03)
        rows.append({"aile_yon": k, "n": len(g), "WR": round(100 * (g.R > 0).mean(), 1), "SL%": round(100 * (g.R <= SL_R).mean(), 1),
                     "ortR": round(m, 3), "P(EV<0)": round(1 - p_pos, 3), "ON_n": len(pre), "ON_R": round(pre.R.mean(), 3) if len(pre) else None,
                     "ILERI_n": len(fwd), "ILERI_R": round(fwd.R.mean(), 3) if len(fwd) else None,
                     "net$": round(g.net.sum()), "risk$_toplam": round(g.risk.sum()),
                     "hukum": "YASAK" if ban else ("OLU_RISK" if dead else "-")})
    return rows


def flag_table(d: pd.DataFrame) -> list[dict]:
    d = d.copy()
    d["B1_NR_lt_0.5"] = d.NR < 0.5
    d["B5_kovalama"] = d.mom60_atr5 >= 1.5
    flags = ["B1_NR_lt_0.5", "B2_Y2", "B3_Y1", "B4_kotu_gun", "B5_kovalama"]
    rows = []
    for f in flags:
        x = d[d[f].notna()].copy(); x[f] = x[f].astype(bool)
        obs = strat_delta(x, f)
        sl, win = x.R <= SL_R, x.R > 0
        r = {"bayrak": f, "n_bayrakli": int(x[f].sum()), "R_bayrakli": round(x.R[x[f]].mean(), 3), "R_diger": round(x.R[~x[f]].mean(), 3),
             "delta_tabakali": round(obs, 3) if np.isfinite(obs) else None,
             "ON_delta": round(strat_delta(x[x.entry < FWD], f), 3), "ILERI_delta": round(strat_delta(x[x.entry >= FWD], f), 3),
             "ILERI2_delta": round(strat_delta(x[x.entry >= FWD2], f), 3),
             "SL_engel%": round(100 * x[f][sl].mean(), 1), "TP_kayip%": round(100 * x[f][win].mean(), 1),
             "P(delta<0)": round(boot_delta(x, f), 3) if np.isfinite(obs) else None,
             "plasebo_yuzdelik": round(placebo(x, f, obs), 3) if np.isfinite(obs) else None,
             "engellenen_net$": round(x.net[x[f]].sum())}
        rows.append(r)
    ps = sorted([(1 - (r["P(delta<0)"] or 0), i) for i, r in enumerate(rows)])
    m = len(ps)
    for rank, (p, i) in enumerate(ps):
        rows[i]["holm_p"] = round(min(1.0, p * (m - rank)), 3)
    for r in rows:
        r["gecti"] = bool(r["n_bayrakli"] >= 20 and (r["delta_tabakali"] or 0) < 0 and (r["P(delta<0)"] or 0) >= 0.9
                          and (r["ON_delta"] or 0) < 0 and (r["ILERI_delta"] or 0) < 0
                          and r["SL_engel%"] - r["TP_kayip%"] >= 10 and r["holm_p"] <= 0.10)
    return rows


def main() -> None:
    t, m1 = load()
    d = decisions(t)
    d = bar_feats(d, m1)
    d = stack_feats(d, t)
    d.to_parquet(OUT / "kararlar.parquet")
    fam, flg = family_table(d), flag_table(d)
    pts = [(r["SL_engel%"], r["TP_kayip%"]) for r in flg]
    corr = float(np.corrcoef(np.array(pts).T)[0, 1]) if len(pts) > 2 else None
    res = {"karar": len(d), "aralik": [str(d.entry.min()), str(d.entry.max())], "aile": fam, "bayrak": flg,
           "engel_kayip_korelasyon": corr}
    (OUT / "sonuc.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    print(pd.DataFrame(fam).to_string(index=False))
    print(pd.DataFrame(flg).to_string(index=False))
    print("SL-engel/TP-kayıp korelasyonu:", corr)


if __name__ == "__main__":
    main()
