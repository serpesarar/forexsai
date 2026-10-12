"""IO-18 sağlamlık turu — bkz. PROTOCOL.md (ön-kayıt). 2026-10-10.

python3 research/kovalama_saglamlik_20261010/pull_skipped.py   # bir kez (kutu)
python3 research/kovalama_saglamlik_20261010/run.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import data  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402
from scripts.islem_otopsi.placebo import simulate  # noqa: E402

OUT = HERE / "results"
SPREAD, RISK_FRAC, RR, SL_ATR1H = 1.5, 0.00373, 0.73, 0.84
C1_T, C2_T = 2.0, 65.0                       # SELL-işaretli: g60_ema50 ≥ 2 · 100−RSI ≥ 65 (RSI ≤ 35)
DEDUP_MIN, BOT_EXCL_MIN = 30, 15
N_BOOT, N_SHIFT, MIN_SUP = 2000, 1000, 25
RNG = np.random.default_rng(20261010)
PANEL_MODELS = ("pulse1", "pulse2", "pulse3", "ml:main", "meta", "smc")
P_START, P_END = pd.Timestamp("2026-06-15", tz="UTC"), pd.Timestamp("2026-10-09 21:00", tz="UTC")


def _mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


G = _mod("genis_ks", ROOT / "research" / "donus_vs_sl_20261009" / "genis.py")


# ── yardımcılar ──────────────────────────────────────────────────────────────

def dedup(ts: pd.Series, minutes: int) -> list[pd.Timestamp]:
    keep, last = [], None
    for t in sorted(ts):
        if last is None or t - last >= pd.Timedelta(minutes=minutes):
            keep.append(t)
            last = t
    return keep


def day_block(df: pd.DataFrame, stat, n: int = N_BOOT) -> tuple[float, float]:
    """Gün-blok bootstrap %95 — stat(df) → float."""
    days = df.t.dt.tz_convert("America/New_York").dt.date.to_numpy()
    groups = [df.index[days == d].to_numpy() for d in np.unique(days)]
    vals = []
    for _ in range(n):
        pick = RNG.integers(0, len(groups), len(groups))
        v = stat(df.loc[np.concatenate([groups[i] for i in pick])])
        if np.isfinite(v):
            vals.append(v)
    return (float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))) if vals else (np.nan, np.nan)


def sl_diff(d: pd.DataFrame, c: str) -> float:
    m = d[c].to_numpy(bool)
    return d.B[m].mean() - d.B[~m].mean() if 3 <= m.sum() < len(m) - 3 else np.nan


def r_diff(d: pd.DataFrame, c: str) -> float:
    m = d[c].to_numpy(bool)
    return d.R[m].mean() - d.R[~m].mean() if 3 <= m.sum() < len(m) - 3 else np.nan


def line(d: pd.DataFrame, c: str, label: str) -> str:
    m = d[c].to_numpy(bool)
    if m.sum() < 5 or (~m).sum() < 5:
        return f"  {label:34s} {c}: n={m.sum()} yetersiz"
    lo, hi = day_block(d, lambda x: sl_diff(x, c))
    rlo, rhi = day_block(d, lambda x: r_diff(x, c))
    ok = " ✓" if lo > 0 else ""
    return (f"  {label:34s} {c}: n={m.sum():4d}/{len(d):5d}  SL %{100 * d.B[m].mean():3.0f} vs %{100 * d.B[~m].mean():3.0f}"
            f"  fark {100 * sl_diff(d, c):+5.1f}pp [{100 * lo:+.1f}…{100 * hi:+.1f}]{ok}"
            f"  ortR {d.R[m].mean():+.3f} vs {d.R[~m].mean():+.3f} [{rlo:+.2f}…{rhi:+.2f}]")


# ── olay simülasyonu (B–E ortak) ─────────────────────────────────────────────

class Market:
    def __init__(self) -> None:
        raw = data.load_bars_raw("NDX.INDX", pd.Timestamp("2026-05-20", tz="UTC"), data.utc_now())
        self.sb = SymbolBars("NDX.INDX", data.normalize_snapshot_clock(raw))
        self.ext = G.Ext(self.sb)

    def event(self, t: pd.Timestamp, geo: str) -> dict | None:
        sb = self.sb
        t = t.tz_localize("UTC") if t.tzinfo is None else t
        i_pre = sb.last_closed(1, t)
        j = i_pre + 1
        if i_pre < 400 or j >= sb.m1.index.size - 30:
            return None
        if (sb.m1.index[j] - t) > pd.Timedelta(minutes=5):      # piyasa kapalı / boşluk
            return None
        f = G.ind_features(self.ext, i_pre, -1)
        if "g60_ema50" not in f or not np.isfinite(f["g60_ema50"]):
            return None
        entry = float(sb.a["open"][j])
        if geo == "G1":
            risk = entry * RISK_FRAC
        else:
            atr1h = float(self.ext.f[60]["atr"][sb.last_closed(60, t)])
            risk = SL_ATR1H * atr1h
        R, k, _ = simulate(sb, -1, entry, j, risk, risk * RR, SPREAD)
        if k < 0:
            return None
        return {"t": t, "B": int(R < 0), "R": R, "C1": f["g60_ema50"] >= C1_T, "C2": f["g60_rsi"] >= C2_T,
                "g60_ema50": f["g60_ema50"], "g60_rsi": f["g60_rsi"]}

    def table(self, ts: list, geo: str, extra: list[dict] | None = None) -> pd.DataFrame:
        rows = []
        for i, t in enumerate(ts):
            e = self.event(pd.Timestamp(t), geo)
            if e is not None:
                rows.append({**e, **(extra[i] if extra else {})})
        return pd.DataFrame(rows).reset_index(drop=True) if rows else pd.DataFrame()


# ── kaynaklar ────────────────────────────────────────────────────────────────

def bot_df() -> pd.DataFrame:
    b = pd.read_parquet(ROOT / "research" / "sl_ortak_20261009" / "results" / "bot.parquet")
    b = b[(b.sym == "NDX") & (b.yon == "SELL")].copy().sort_values("t0").reset_index(drop=True)
    b["t"] = pd.to_datetime(b.t0, utc=True)
    b["C1"], b["C2"] = b.g60_ema50 >= C1_T, b.g60_rsi >= C2_T
    return b


def skipped_events(bot: pd.DataFrame) -> tuple[list, list]:
    s = pd.read_parquet(OUT / "skipped.parquet")
    s = s[~s.reason.str.contains("shadow", na=False)].sort_values("ts")
    bt = bot.t.to_numpy(dtype="datetime64[ns]")
    keep, extra, last = [], [], None
    for _, r in s.iterrows():
        t = r.ts
        if last is not None and t - last < pd.Timedelta(minutes=DEDUP_MIN):
            continue
        dt = np.abs((bt - np.datetime64(t.tz_convert(None))).astype("timedelta64[m]").astype(float))
        if dt.size and dt.min() <= BOT_EXCL_MIN:
            continue
        keep.append(t)
        extra.append({"aile": r.aile, "reason": r.reason})
        last = t
    return keep, extra


def panel_events() -> tuple[list, list]:
    p = pd.read_parquet(ROOT / "research" / "donus_vs_sl_20261009" / "results" / "panel.parquet")
    p = p[(p.symbol == "NDX.INDX") & p.model_type.isin(PANEL_MODELS) & (p.ml_direction == "SELL")]
    ts, ex = [], []
    for mdl, g in p.groupby("model_type"):
        for t in dedup(g.ts, DEDUP_MIN):
            ts.append(t)
            ex.append({"model": mdl})
    return ts, ex


def decider_events() -> tuple[list, list]:
    d = pd.read_parquet(ROOT / "research" / "decider_kural_20261008" / "data" / "decisions.parquet")
    d = d[d.symbol.str.startswith("NDX") & (d.dir == "SELL")].sort_values("ts")
    return list(pd.to_datetime(d.ts, utc=True)), [{"act": a} for a in d.act]


def generic_events(mk: Market) -> list:
    idx = mk.sb.m1.index
    st = idx[(idx.minute == 0) & (idx.hour >= 6) & (idx.hour <= 20) & (idx.dayofweek < 5)]
    return list(st[(st >= P_START) & (st <= P_END)])


# ── A: bot içi ──────────────────────────────────────────────────────────────

def saved_r(d: pd.DataFrame, c: str) -> float:
    return float(-d.R[d[c].to_numpy(bool)].sum())


def part_a(b: pd.DataFrame, L: list) -> None:
    L.append(f"\n## A) Bot içi — NDX SELL n={len(b)}, SL %{100 * b.B.mean():.0f}, ort R {b.R.mean():+.3f}")
    for c in ("C1", "C2"):
        lo, hi = day_block(b, lambda x: saved_r(x, c))
        L.append(line(b, c, "A1 tümü"))
        L.append(f"     kurtarılan R {saved_r(b, c):+.1f}  gün-blok %95 [{lo:+.1f}…{hi:+.1f}]")
    L.append("  A2 ay ay (C1 / C2): SL% koşullu vs diğer, kurtarılan R")
    for mo, g in b.groupby(b.t.dt.strftime("%Y-%m")):
        parts = []
        for c in ("C1", "C2"):
            m = g[c].to_numpy(bool)
            parts.append(f"{c} n={m.sum():2d} SL %{100 * g.B[m].mean() if m.any() else float('nan'):3.0f} vs "
                         f"%{100 * g.B[~m].mean() if (~m).any() else float('nan'):3.0f} kurt {saved_r(g, c):+5.1f}R")
        L.append(f"     {mo} (n={len(g):3d}): " + " · ".join(parts))
    L.append("     ay-dışarıda (o ay çıkarılınca C1 kurtarılan R / SL farkı):")
    for mo in sorted(b.t.dt.strftime("%Y-%m").unique()):
        g = b[b.t.dt.strftime("%Y-%m") != mo]
        L.append(f"       −{mo}: C1 {saved_r(g, 'C1'):+5.1f}R  {100 * sl_diff(g, 'C1'):+5.1f}pp · "
                 f"C2 {saved_r(g, 'C2'):+5.1f}R  {100 * sl_diff(g, 'C2'):+5.1f}pp")
    L.append("  A3 aile:")
    for nm, g in (("VIXREG", b[b.aile == "VIXREG"]), ("diğer", b[b.aile != "VIXREG"])):
        for c in ("C1", "C2"):
            L.append(line(g.reset_index(drop=True), c, f"     {nm}"))
    part_a4(b, L)
    part_a5(b, L)


def part_a4(b: pd.DataFrame, L: list) -> None:
    L.append("  A4 eşik platosu (kurtarılan R · SL farkı pp · n):")
    for col, ths, lab in (("g60_ema50", (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0), "1h EMA50 altı ≥ ATR"),
                          ("g15_ema50", (1.0, 1.5, 2.0, 2.5, 3.0, 4.0), "15m EMA50 altı ≥ ATR"),
                          ("g5_ema50", (1.0, 1.5, 2.0, 3.0, 4.0), "5m EMA50 altı ≥ ATR"),
                          ("g60_ema20", (1.0, 1.5, 2.0, 2.5), "1h EMA20 altı ≥ ATR"),
                          ("g60_ema200", (1.0, 2.0, 3.0, 4.0), "1h EMA200 altı ≥ ATR")):
        cells = []
        for th in ths:
            d = b.assign(K=b[col] >= th)
            cells.append(f"{th:g}: {saved_r(d, 'K'):+5.1f}R {100 * sl_diff(d, 'K'):+4.0f}pp n{int(d.K.sum())}")
        L.append(f"     {lab:22s} " + " | ".join(cells))
    for col, lab in (("g60_rsi", "1h RSI ≤"), ("g15_rsi", "15m RSI ≤"), ("g5_rsi", "5m RSI ≤")):
        cells = []
        for rsi in (30, 33, 35, 38, 40, 45):
            d = b.assign(K=b[col] >= 100 - rsi)
            cells.append(f"{rsi}: {saved_r(d, 'K'):+5.1f}R {100 * sl_diff(d, 'K'):+4.0f}pp n{int(d.K.sum())}")
        L.append(f"     {lab:22s} " + " | ".join(cells))


def _max_saved(F: np.ndarray, R: np.ndarray) -> float:
    """Her sütun × iki kuyruk × desil eşiği (destek ≥ MIN_SUP) içinde en büyük −ΣR."""
    best = -np.inf
    for k in range(F.shape[1]):
        x = F[:, k]
        ok = np.isfinite(x)
        if ok.sum() < 2 * MIN_SUP:
            continue
        for q in np.nanquantile(x[ok], np.linspace(0.1, 0.9, 9)):
            for m in (ok & (x >= q), ok & (x <= q)):
                if m.sum() >= MIN_SUP:
                    best = max(best, -R[m].sum())
    return best


def part_a5(b: pd.DataFrame, L: list) -> None:
    skip = {"t0", "t1", "B", "R", "pid", "sym", "yon", "aile", "session", "t", "C1", "C2"}
    cols = [c for c in b.columns if c not in skip and pd.api.types.is_numeric_dtype(b[c]) and b[c].nunique() > 3]
    F, R = b[cols].to_numpy(float), b.R.to_numpy(float)
    obs = _max_saved(F, R)
    n = len(R)
    shifts = RNG.integers(10, n - 10, N_SHIFT)
    null = np.array([_max_saved(F, np.roll(R, int(s))) for s in shifts])
    c1 = saved_r(b, "C1")
    L.append(f"  A5 seçim düzeltmeli maks. istatistik ({len(cols)} özellik × 2 kuyruk × 9 eşik, destek ≥{MIN_SUP}):")
    L.append(f"     gözlenen en iyi kural {obs:+.1f}R · boş dağılım (dairesel kaydırma ×{N_SHIFT}) medyan {np.median(null):+.1f}R, "
             f"%95 {np.quantile(null, 0.95):+.1f}R → p(maks) = {(null >= obs).mean():.3f}")
    L.append(f"     C1'in kendi değeri {c1:+.1f}R → p(C1 düzeyinde bir kural tesadüfen bulunur) = {(null >= c1).mean():.3f}")


# ── B–F ─────────────────────────────────────────────────────────────────────

def block(d: pd.DataFrame, title: str, L: list, by: str | None = None) -> None:
    if d.empty:
        L.append(f"\n## {title}: veri yok")
        return
    L.append(f"\n## {title}: n={len(d)}, SL %{100 * d.B.mean():.0f}, ort R {d.R.mean():+.3f}")
    for c in ("C1", "C2"):
        L.append(line(d, c, "tümü"))
    if by:
        for k, g in d.groupby(by):
            if len(g) >= 20:
                for c in ("C1", "C2"):
                    L.append(line(g.reset_index(drop=True), c, f"{by}={k}"))
    half = d.sort_values("t").reset_index(drop=True)
    h = len(half) // 2
    for nm, g in (("1. yarı", half.iloc[:h]), ("2. yarı", half.iloc[h:])):
        L.append(line(g.reset_index(drop=True), "C1", nm))


def did(bot: pd.DataFrame, gen: pd.DataFrame, c: str, L: list) -> None:
    both = pd.concat([bot[["t", "B", "R", c]].assign(src=1), gen[["t", "B", "R", c]].assign(src=0)], ignore_index=True)

    def stat(x: pd.DataFrame) -> float:
        return sl_diff(x[x.src == 1].reset_index(drop=True), c) - sl_diff(x[x.src == 0].reset_index(drop=True), c)
    lo, hi = day_block(both, stat)
    L.append(f"  F) {c}: bot etkisi {100 * sl_diff(bot, c):+.1f}pp − piyasa etkisi {100 * sl_diff(gen, c):+.1f}pp = "
             f"{100 * stat(both):+.1f}pp  gün-blok %95 [{100 * lo:+.1f}…{100 * hi:+.1f}]{' ✓' if lo > 0 else ''}")


def main() -> None:
    L: list[str] = ["# IO-18 sağlamlık turu — sonuçlar (ön-kayıt: PROTOCOL.md)"]
    bot = bot_df()
    part_a(bot, L)
    mk = Market()
    sk_ts, sk_ex = skipped_events(bot)
    pn_ts, pn_ex = panel_events()
    dc_ts, dc_ex = decider_events()
    gn_ts = generic_events(mk)
    gens = {}
    for geo in ("G1", "G2"):
        L.append(f"\n# ── Geometri {geo} {'(birincil: fiyat×%0,373, RR 0,73)' if geo == 'G1' else '(yan: 0,84×ATR1h, RR 0,73)'}")
        sk = mk.table(sk_ts, geo, sk_ex)
        block(sk, f"B) Botun ENGELLENEN NDX SELL sinyalleri ({geo})", L, by="aile")
        if geo == "G1":
            block(sk, "B') engelleme nedenine göre", L, by="reason")
        block(mk.table(pn_ts, geo, pn_ex), f"C) Panel modelleri NDX SELL ({geo})", L, by="model")
        block(mk.table(dc_ts, geo, dc_ex), f"D) Decider NDX SELL kararları ({geo})", L, by="act")
        gens[geo] = mk.table(gn_ts, geo)
        block(gens[geo], f"E) Aynı dönem sinyalsiz piyasa 06-15→10-09 ({geo})", L)
        sk.to_csv(OUT / f"skipped_sim_{geo}.csv", index=False)
        gens[geo].to_csv(OUT / f"generic_{geo}.csv", index=False)
    L.append("\n## F) Fark-içinde-fark (bot gerçek işlemleri vs aynı dönem piyasa G1)")
    for c in ("C1", "C2"):
        did(bot, gens["G1"], c, L)
    txt = "\n".join(L)
    (OUT / "rapor.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
