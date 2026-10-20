"""2026-10-19 NDX SL zinciri — karşı-olgu kuralları K1–K6 (bkz. PROTOCOL.md).

python3 research/ndx_sl_zinciri_20261020/run.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import data  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402

TRADES = ROOT / "output" / "islem_otopsi" / "2026-10-20_1409_ndx" / "islemler.csv"
OUT = HERE / "results"
DAY = pd.Timestamp("2026-10-19", tz="UTC")
DAILY_MAX_LOSS = 3000.0
COOL_MIN, SQZ_MIN = 60, 1.00
REENTRY_LINK_MIN = (0.5, 22.0)          # ebeveyn kapanışından REENTRY girişine dk aralığı
N_PLAC = 2000
RNG = np.random.default_rng(20261020)
CHAIN = ("DAYCOMBO", "REENTRY")


def load() -> pd.DataFrame:
    d = pd.read_csv(TRADES)
    d["t0"] = pd.to_datetime(d.entry_utc, utc=True)
    d["t1"] = pd.to_datetime(d.exit_utc, utc=True)
    d = d[d.family != "DECIDER"].sort_values("t0").reset_index(drop=True)
    d["R"] = d.r_exit.astype(float)
    d["day"] = d.t0.dt.normalize()
    return d


def parents(d: pd.DataFrame) -> np.ndarray:
    """REENTRY satırı için ebeveyn indeksi (aynı yön, kapanışı girişten 0,5–22 dk önce)."""
    par = np.full(len(d), -1)
    for i in np.flatnonzero(d.family.to_numpy() == "REENTRY"):
        dt = (d.t0[i] - d.t1).dt.total_seconds() / 60
        ok = (dt >= REENTRY_LINK_MIN[0]) & (dt <= REENTRY_LINK_MIN[1]) & (d.direction == d.direction[i]) \
            & (d.family != "REENTRY")
        if ok.any():
            par[i] = int(dt[ok].idxmin())
    return par


def squeeze(d: pd.DataFrame) -> np.ndarray:
    raw = data.load_bars_raw("NDX.INDX", d.t0.min() - pd.Timedelta(days=1), d.t1.max())
    sb = SymbolBars("NDX.INDX", data.normalize_snapshot_clock(raw))
    h, l, c = sb.a["high"], sb.a["low"], sb.a["close"]
    tr = np.maximum.reduce([h[1:] - l[1:], np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])])
    out = np.full(len(d), np.nan)
    for k, r in d.iterrows():
        # DAYCOMBO probasyonla 5 dk sonra girer; SQZ sinyal anında ölçülür
        t = r.t0 - pd.Timedelta(minutes=5) if r.family == "DAYCOMBO" and r.t0 >= pd.Timestamp("2026-08-15", tz="UTC") else r.t0
        i = sb.last_closed(1, t)                    # i = son kapanmış bar; tr[i-1] = o barın TR'si
        if i < 102 or (t - sb.m1.index[i]) > pd.Timedelta(minutes=10):
            continue
        out[k] = tr[i - 14:i].mean() / tr[i - 100:i].mean()
    return out


# ── kurallar: True = bu işlem engellenirdi ───────────────────────────────────

def k1_daily(d: pd.DataFrame) -> np.ndarray:
    blk = np.zeros(len(d), bool)
    for _, g in d.groupby("day"):
        for i in g.index:
            done = g[(g.t1 <= d.t0[i]) & ~blk[g.index]]
            if done.net.sum() <= -DAILY_MAX_LOSS:
                blk[i] = True
    return blk


def k2_stack(d: pd.DataFrame) -> np.ndarray:
    blk = np.zeros(len(d), bool)
    for i in range(len(d)):
        prev = d.iloc[:i]
        live = prev[(prev.direction == d.direction[i]) & (prev.t1 > d.t0[i]) & ~blk[:i]]
        blk[i] = len(live) > 0
    return blk


def k3_cool(d: pd.DataFrame) -> np.ndarray:
    blk = np.zeros(len(d), bool)
    for i in range(len(d)):
        prev = d.iloc[:i]
        m = (prev.direction == d.direction[i]) & (prev.outcome == "SL") & ~blk[:i] \
            & (prev.t1 <= d.t0[i]) & (prev.t1 > d.t0[i] - pd.Timedelta(minutes=COOL_MIN))
        blk[i] = bool(m.any())
    return blk


def k4_daycombo(d: pd.DataFrame) -> np.ndarray:
    blk = np.zeros(len(d), bool)
    dc = d[d.family == "DAYCOMBO"]
    for _, g in dc.groupby("day"):
        blk[g.index[1:]] = True
    return blk


def k5_sqz(d: pd.DataFrame, chain_only: bool) -> np.ndarray:
    m = np.isfinite(d.sqz) & (d.sqz < SQZ_MIN)
    return (m & d.family.isin(CHAIN)).to_numpy() if chain_only else m.to_numpy()


def k6_reentry_tp(d: pd.DataFrame) -> np.ndarray:
    blk = np.zeros(len(d), bool)
    for i in np.flatnonzero(d.par.to_numpy() >= 0):
        blk[i] = d.outcome[d.par[i]] == "SL"
    return blk


def with_children(d: pd.DataFrame, blk: np.ndarray) -> np.ndarray:
    b = blk.copy()
    for i in np.flatnonzero(d.par.to_numpy() >= 0):
        if b[d.par[i]]:
            b[i] = True
    return b


# ── değerlendirme ────────────────────────────────────────────────────────────

def plac_pct(d: pd.DataFrame, blk: np.ndarray, elig: np.ndarray) -> float:
    k, pool = int(blk.sum()), np.flatnonzero(elig)
    if k == 0 or k > pool.size:
        return np.nan
    saved = -d.R.to_numpy()[blk].sum()
    sims = np.array([-d.R.to_numpy()[RNG.choice(pool, k, replace=False)].sum() for _ in range(N_PLAC)])
    return float((sims < saved).mean())


def row(d: pd.DataFrame, blk: np.ndarray, elig: np.ndarray, name: str) -> dict:
    hist = (d.t0 < DAY).to_numpy()
    yday = ((d.t0 >= DAY) & (d.t0 < DAY + pd.Timedelta(days=1))).to_numpy()
    h = np.flatnonzero(hist)
    half = np.zeros(len(d), bool)
    half[h[: h.size // 2]] = True
    out = {"kural": name}
    for lab, m in (("geçmiş", hist), ("10-19", yday)):
        b = blk & m
        out[f"{lab} engel"] = int(b.sum())
        out[f"{lab} kurt.R"] = round(float(-d.R[b].sum()), 2)
        out[f"{lab} kurt.$"] = round(float(-d.net[b].sum()))
    out["geçmiş SL/TP engel"] = f"{int(((d.outcome == 'SL') & blk & hist).sum())}/{int(((d.outcome == 'TP') & blk & hist).sum())}"
    out["yarılar R"] = f"{-d.R[blk & half].sum():+.2f}/{-d.R[blk & hist & ~half].sum():+.2f}"
    dh = d[hist].reset_index(drop=True)
    out["plasebo %"] = round(100 * plac_pct(dh, blk[hist], elig[hist]), 1)
    ok = out["geçmiş kurt.R"] > 0 and out["plasebo %"] >= 90 and all(float(x) >= 0 for x in out["yarılar R"].split("/"))
    out["hüküm"] = "GÖLGE ADAYI" if ok else "geçmedi"
    return out


def chain_stats(d: pd.DataFrame, L: list) -> None:
    hist = d[d.t0 < DAY]
    L.append("\n## Geçmişte zincir/üst üste binme ne kadar sık ve sonucu?")
    for nm, g in (("tüm bot NDX (DECIDER hariç)", hist), ("DAYCOMBO+REENTRY", hist[hist.family.isin(CHAIN)])):
        L.append(f"- {nm}: n={len(g)} ortR {g.R.mean():+.3f} · SL %{100 * (g.outcome == 'SL').mean():.0f}")
    for nm, m in (("aynı yönde açık pozisyon varken açılan", d.k2), ("SL'den sonraki 60 dk içinde açılan", d.k3),
                  ("günün 2.+ DAYCOMBO'su", d.k4), ("SL sonrası REENTRY", d.k6)):
        g = hist[m[hist.index]]
        L.append(f"- {nm}: n={len(g)} ortR {g.R.mean() if len(g) else float('nan'):+.3f} "
                 f"SL %{100 * (g.outcome == 'SL').mean() if len(g) else float('nan'):.0f} · "
                 f"diğerleri ortR {hist[~m[hist.index]].R.mean():+.3f}")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    d = load()
    d["par"] = parents(d)
    d["sqz"] = squeeze(d)
    d["k2"], d["k3"], d["k4"], d["k6"] = k2_stack(d), k3_cool(d), k4_daycombo(d), k6_reentry_tp(d)
    allb = np.ones(len(d), bool)
    chain = d.family.isin(CHAIN).to_numpy()
    rules = [("K1 günlük fren (tüm magic, −3.000$)", with_children(d, k1_daily(d)), allb),
             ("K2 aynı yönde üst üste binme yok", with_children(d, d.k2.to_numpy()), allb),
             (f"K3 SL sonrası {COOL_MIN} dk soğuma", with_children(d, d.k3.to_numpy()), allb),
             ("K4 DAYCOMBO günde 1", with_children(d, d.k4.to_numpy()), chain),
             ("K5a SQZ<1,00 engel (DAYCOMBO+REENTRY)", with_children(d, k5_sqz(d, True)), chain),
             ("K5b SQZ<1,00 engel (tüm bot aileleri)", with_children(d, k5_sqz(d, False)), allb),
             ("K6 REENTRY yalnız TP sonrası", d.k6.to_numpy(), chain)]
    L = ["# 2026-10-19 NDX SL zinciri — karşı-olgu kuralları (ön-kayıt PROTOCOL.md)",
         f"\nİşlem: {len(d)} bot NDX (DECIDER hariç), geçmiş {int((d.t0 < DAY).sum())}, 10-19 "
         f"{int(((d.t0 >= DAY) & (d.t0 < DAY + pd.Timedelta(days=1))).sum())}. Birim R; $ ikincil (lot 1→30 değişti)."]
    tab = pd.DataFrame([row(d, b, e, n) for n, b, e in rules])
    L.append("\n" + tab.to_markdown(index=False))
    chain_stats(d, L)
    y = d[(d.t0 >= DAY) & (d.t0 < DAY + pd.Timedelta(days=1))]
    L.append("\n## 10-19 işlemleri ve her kuralın hükmü")
    flags = {n.split(" ")[0]: b for n, b, _ in rules}
    cols = ["pid", "family", "t0", "outcome", "R", "net", "sqz"]
    yy = y[cols].copy()
    for k, b in flags.items():
        yy[k] = np.where(b[y.index], "ENGEL", "")
    L.append(yy.to_markdown(index=False, floatfmt=".3f"))
    d.to_csv(OUT / "islemler_kurallar.csv", index=False)
    txt = "\n".join(L)
    (OUT / "rapor.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
