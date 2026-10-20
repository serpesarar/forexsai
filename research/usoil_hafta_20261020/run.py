"""USOIL düzeltme adayları C1–C5 × kaynaklar K1–K3 — bkz. PROTOCOL.md.

python3 research/usoil_hafta_20261020/pull.py   # bir kez
python3 research/usoil_hafta_20261020/run.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "results"
sys.path.insert(0, str(ROOT / "research" / "sikisma_derin_20261020"))
import core as C  # noqa: E402

SYM = "USOIL.FOREX"
TRADES = ROOT / "output" / "islem_otopsi" / "2026-10-20_2222_usoil" / "islemler.csv"
CLEAN = ROOT / "research" / "wti_transfer_20261002" / "data" / "clean_1m.csv"
SEAM = pd.Timestamp("2026-05-20", tz="UTC")
KESIF_END, FWD, WEEK = (pd.Timestamp(x, tz="UTC") for x in ("2026-09-30", "2026-09-30", "2026-10-13"))
TP_PCT, SL_PCT, SPREAD = 0.0104, 0.0149, 0.03
SESSION_START = 13
SKIP_REASONS = ("position_gate", "trend_gate")
N_RAND = 3000
RNG = np.random.default_rng(1020)


def bars() -> pd.DataFrame:
    c = pd.read_csv(CLEAN, usecols=["ts", "open", "high", "low", "close", "volume"])
    c["ts"] = pd.to_datetime(c.ts, utc=True)
    c = c[c.ts < SEAM].set_index("ts").astype(float)
    s = C.bars_snapshots(SYM, "2026-05-20")
    s = s[s.index >= SEAM][["open", "high", "low", "close", "volume"]].astype(float)
    return pd.concat([c, s]).sort_index()


def h1_feats(df: pd.DataFrame) -> pd.DataFrame:
    """1h EMA50 / ATR14 (Wilder), 5m ATR14 — bilinme anı bar sonu."""
    g = df.resample("1h", label="left", closed="left")
    h = pd.DataFrame({"high": g.high.max(), "low": g.low.min(), "close": g.close.last()}).dropna()
    pc = h.close.shift()
    tr = pd.concat([h.high - h.low, (h.high - pc).abs(), (h.low - pc).abs()], axis=1).max(axis=1)
    h1 = pd.DataFrame({"ema50": h.close.ewm(span=50, adjust=False).mean(),
                       "atr1h": tr.ewm(alpha=1 / 14, adjust=False).mean()}, index=h.index + pd.Timedelta(hours=1))
    g5 = df.resample("5min", label="left", closed="left")
    b5 = pd.DataFrame({"high": g5.high.max(), "low": g5.low.min(), "close": g5.close.last()}).dropna()
    pc5 = b5.close.shift()
    tr5 = pd.concat([b5.high - b5.low, (b5.high - pc5).abs(), (b5.low - pc5).abs()], axis=1).max(axis=1)
    a5 = pd.DataFrame({"atr5": tr5.ewm(alpha=1 / 14, adjust=False).mean()}, index=b5.index + pd.Timedelta(minutes=5))
    c1 = pd.DataFrame({"px": df.close}, index=df.index + pd.Timedelta(minutes=1))
    out = pd.merge_asof(c1, h1, left_index=True, right_index=True)
    out = pd.merge_asof(out, a5, left_index=True, right_index=True)
    out["_k"] = out.index
    return out


def feats(H: pd.DataFrame, ev: pd.DataFrame, sl_dist: np.ndarray) -> pd.DataFrame:
    q = pd.DataFrame({"t": pd.to_datetime(ev.t, utc=True).values}).reset_index()
    q["t"] = pd.to_datetime(q.t, utc=True)
    j = pd.merge_asof(q.sort_values("t"), H.reset_index(drop=True).sort_values("_k"), left_on="t", right_on="_k")
    j = j.sort_values("index").reset_index(drop=True)
    stale = (j.t - j._k) > pd.Timedelta(minutes=10)
    ev = ev.reset_index(drop=True).copy()
    ev["dist_ema50"] = np.where(stale, np.nan, (j.px - j.ema50) / j.atr1h)
    ev["sl_atr5"] = np.where(stale, np.nan, sl_dist / j.atr5.to_numpy())
    ev["hour"] = pd.to_datetime(ev.t, utc=True).dt.hour
    return ev


def sim(sb, ev: pd.DataFrame) -> np.ndarray:
    idx = sb.m1.index
    out = np.full(len(ev), np.nan)
    for k, t in enumerate(pd.to_datetime(ev.t, utc=True)):
        j = idx.searchsorted(t, side="left")
        if j >= idx.size - 30 or (idx[j] - t) > pd.Timedelta(minutes=5):
            continue
        e = float(sb.a["open"][j]) + SPREAD
        R, kk, _ = C.simulate(sb, 1, e, j, e * SL_PCT, e * TP_PCT, SPREAD)
        out[k] = R
    return out


def candidates(th: dict) -> dict:
    c1 = lambda d: (d.hour < SESSION_START).to_numpy()  # noqa: E731
    c2 = lambda d: (d.dist_ema50 >= th["dist_hi"]).to_numpy()  # noqa: E731
    c3 = lambda d: (d.sl_atr5 <= th["sl_lo"]).to_numpy()  # noqa: E731
    return {"C1 seans <13 UTC": c1, f"C2 uzama ≥{th['dist_hi']:.2f} ATR": c2, f"C3 dar stop ≤{th['sl_lo']:.2f}×ATR5": c3,
            "C4 C1∨C2": lambda d: c1(d) | c2(d), "C5 C1∧C2": lambda d: c1(d) & c2(d)}


def evaluate(d: pd.DataFrame, m: np.ndarray, src: str, cand: str) -> dict:
    d = d.reset_index(drop=True)
    ok = np.isfinite(d.R.to_numpy(float))
    d, m = d[ok].reset_index(drop=True), m[ok]
    R = d.R.to_numpy(float)
    nb = int(m.sum())
    row = {"kaynak": src, "aday": cand, "n": len(d), "engel": nb}
    if nb < 3 or nb > len(d) - 3:
        return row
    real = -R[m].sum()
    rnd = np.array([-R[RNG.choice(R.size, nb, replace=False)].sum() for _ in range(N_RAND)])
    qs = C.quarters(R, m)
    row.update({"ortR engel": R[m].mean(), "ortR kalan": R[~m].mean(), "kurt_R": real,
                "P(kurt>0)": C.boot_saved(R, m, C.day_ids(d.t)), "rastgele %": float((rnd < real).mean()),
                "saat-eşli %": (C.hour_placebo(R, m, d.hour.to_numpy()) if not cand.startswith(("C1", "C4", "C5")) else np.nan),
                "Ç+": sum(x >= 0 for x in qs), "çeyrekler": "/".join(f"{x:+.1f}" for x in qs)})
    return row


def main() -> None:
    df = bars()
    sb = C.SymbolBars(SYM, df)
    H = h1_feats(df)
    # K1 bot
    tr = pd.read_csv(TRADES)
    tr = tr[(tr.family == "MOMSR") & (tr.direction == "BUY") & tr.outcome.isin(["TP", "SL", "BE", "DIGER_+", "DIGER_-"])]
    k1 = pd.DataFrame({"t": pd.to_datetime(tr.entry_utc, utc=True), "R": tr.r_exit.astype(float).to_numpy(),
                       "net": tr.net.to_numpy()})
    k1 = feats(H, k1, (tr.open_price - tr.sl0).abs().to_numpy())
    pre = k1[k1.t < WEEK]
    th = {"dist_hi": float(pre.dist_ema50.quantile(2 / 3)), "sl_lo": float(pre.sl_atr5.quantile(1 / 3))}
    cands = candidates(th)
    # K2 engellenen
    s = pd.read_parquet(OUT / "skipped_usoil.parquet")
    s = s[s.reason.isin(SKIP_REASONS)].rename(columns={"ts": "t"}).sort_values("t").reset_index(drop=True)
    s["R"] = sim(sb, s)
    k2 = feats(H, s, (s.price * SL_PCT).to_numpy(float))
    # K3 panel BUY
    p = pd.read_parquet(OUT / "panel_usoil.parquet")
    p = p[p.ml_direction == "BUY"].sort_values("ts")
    keep, last = [], {}
    for i, (t, mdl) in enumerate(zip(p.ts, p.model_type)):
        if mdl not in last or t - last[mdl] >= pd.Timedelta(minutes=30):
            keep.append(i)
            last[mdl] = t
    p = p.iloc[keep].rename(columns={"ts": "t", "model_type": "fam"}).reset_index(drop=True)
    p["R"] = sim(sb, p)
    j = sb.m1.index.searchsorted(pd.to_datetime(p.t, utc=True))
    px = sb.a["open"][np.minimum(j, sb.m1.index.size - 1)]
    k3 = feats(H, p, px * SL_PCT)
    for nm, x in (("k1", k1), ("k2", k2), ("k3", k3)):
        x.to_parquet(OUT / f"{nm}.parquet")
    srcs = [("K1 bot keşif (<09-30)", k1[k1.t < KESIF_END]), ("K1 bot İLERİ (09-30→)", k1[k1.t >= FWD]),
            ("K1 bot son hafta (10-13→)", k1[k1.t >= WEEK]), ("K1 bot tümü", k1),
            ("K2 engellenen BUY (konum/trend kapısı)", k2), ("K3 panel BUY 02→10", k3),
            ("K3 panel BUY 06→10 (bot dönemi)", k3[k3.t >= pd.Timestamp("2026-06-01", tz="UTC")])]
    rows = [evaluate(d, f(d), lab, nm) for lab, d in srcs for nm, f in cands.items()]
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "adaylar.csv", index=False)
    L = ["# USOIL düzeltme adayları — sonuçlar (ön-kayıt PROTOCOL.md)",
         f"\nEşikler (bot MOMSR BUY, 10-13 öncesi tertil): uzama ≥ {th['dist_hi']:.2f} ATR · dar stop ≤ {th['sl_lo']:.2f}×ATR5. "
         f"Kaynaklar: K1 {len(k1)} · K2 {len(k2)} · K3 {len(k3)} (ortR K2 {np.nanmean(k2.R):+.3f}, K3 {np.nanmean(k3.R):+.3f})"]
    for cand in cands:
        L.append(f"\n## {cand}")
        L.append(C.md(t[t.aday == cand].drop(columns=["aday"])))
    txt = "\n".join(L)
    (OUT / "rapor.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
