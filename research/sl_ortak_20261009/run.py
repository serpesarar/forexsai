"""Ön-kayıt: PROTOCOL.md. python3 research/sl_ortak_20261009/run.py [hazirla|analiz]

hazirla: bot kararları + NDX bağımsız dönem sentetik girişleri için giriş-anı özellikleri → results/*.parquet
analiz : A (alt-grup) · B (benzerlik tekrarı) · C (SL kümeleme) · D (NDX bağımsız doğrulama) → results/rapor.txt
"""
from __future__ import annotations

import importlib.util
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "donus_vs_sl_20261009"))

from scripts.islem_otopsi import data  # noqa: E402
from scripts.islem_otopsi.features import (Ctx, geometry, pre_divergence, pre_momentum, pre_trend,  # noqa: E402
                                           pre_volume, time_features)
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402
from scripts.islem_otopsi.placebo import simulate  # noqa: E402
from scripts.islem_otopsi.stats import auc, boot_mean_ci  # noqa: E402

OUT = HERE / "results"
NDX_BARS = ROOT / "research" / "ndx_gate_forge" / "data" / "bars_1m_all.parquet"
VAL_END = pd.Timestamp("2026-06-15", tz="UTC")
SYN_HOURS = range(6, 21)
MIN_SUP, MIN_SUP_D, TOP, K_NN, N_CLUST = 12, 15, 10, 10, 4
RNG = np.random.default_rng(20261009)


def _mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


G = _mod("genis_mod", ROOT / "research" / "donus_vs_sl_20261009" / "genis.py")
LK = _mod("lk_run3", ROOT / "research" / "limit_kilit_20261007" / "run.py")


# ── giriş anı özellikleri (bot ve sentetik için AYNI fonksiyon) ─────────────

def entry_features(sb: SymbolBars, ext, s: int, entry: float, risk: float, rr: float, t0: pd.Timestamp,
                   spread: float) -> dict | None:
    i_pre = sb.last_closed(1, t0)
    if i_pre < 400:
        return None
    sl0, tp0 = entry - s * risk, entry + s * risk * rr
    c = Ctx(sb, s, entry, entry, t0, t0, sl0, tp0, risk, risk * rr, spread, i_pre, i_pre + 1, i_pre + 1)
    tr = pre_trend(c)
    f = {**tr, **pre_momentum(c, tr["_atr1"], tr["_atr5"]), **pre_volume(c), **pre_divergence(c),
         **geometry(c, tr["_atr5"], tr["_atr60"]), **time_features(t0), **G.ind_features(ext, i_pre, s)}
    return {k: v for k, v in f.items() if not k.startswith("_")}


def bot_table() -> pd.DataFrame:
    items = LK.load()
    sbs = {x["c"].sb.symbol: x["c"].sb for x in items}
    exts = {k: G.Ext(v) for k, v in sbs.items()}
    pan = G.panel_table()
    pt = {(sym, mdl): (g.ts.values.astype("datetime64[ns]"), g.ml_direction.values)
          for (sym, mdl), g in pan.sort_values("ts").groupby(["symbol", "model_type"])}
    vix = data.load_vix(pd.Timestamp("2026-06-01", tz="UTC"), data.utc_now())
    rows = []
    for x in items:
        r, c = x["r"], x["c"]
        if r["outcome"] not in ("TP", "SL"):
            continue
        f = entry_features(c.sb, exts[c.sb.symbol], c.s, c.entry, c.risk, c.reward / c.risk, c.t0, c.spread)
        if f is None:
            continue
        f.update(G.panel_feats(pt, c.sb.symbol, c.t0, c.s))
        day = pd.Timestamp(c.t0.tz_convert("America/New_York").date())
        prior = vix[vix.index < day]
        f.update({"vix_onceki": float(prior.iloc[-1]) if len(prior) else np.nan, "aile": r["family"],
                  "ctx_onceki_kazandi": r.get("ctx_prev_win"), "ctx_onceki_ayni_yon": r.get("ctx_prev_same_dir"),
                  "ctx_onceki_dk": r.get("ctx_min_since_prev"), "ctx_acik_poz": r.get("ctx_n_open"),
                  "sym": c.sb.symbol.split(".")[0], "yon": "BUY" if c.s > 0 else "SELL", "t0": c.t0,
                  "t1": r["exit_utc"], "B": int(r["outcome"] == "SL"), "R": r["r_exit"], "pid": r["pid"]})
        rows.append(f)
    return pd.DataFrame(rows).sort_values("t0").reset_index(drop=True)


def ndx_synth() -> pd.DataFrame:
    raw = pd.read_parquet(NDX_BARS)
    raw = raw[raw.ts < VAL_END].set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float)
    sb = SymbolBars("NDX.INDX", raw)
    ext = G.Ext(sb)
    risk_frac, rr, spread = 0.00373, 0.73, 1.5
    idx = sb.m1.index
    starts = idx[(idx.minute == 0) & idx.hour.isin(list(SYN_HOURS)) & (idx.dayofweek < 5)]
    rows = []
    for ts in starts:
        j = sb.pos_at(ts)
        if j < 500 or j + 60 >= idx.size:
            continue
        for s in (1, -1):
            entry = float(sb.a["open"][j]) + (spread if s > 0 else 0.0)
            risk = entry * risk_frac
            R, k, _ = simulate(sb, s, entry, j, risk, risk * rr, spread)
            if k < 0:
                continue
            f = entry_features(sb, ext, s, entry, risk, rr, ts, spread)
            if f is None:
                continue
            f.update({"sym": "NDX", "yon": "BUY" if s > 0 else "SELL", "t0": ts, "t1": idx[k], "B": int(R < 0), "R": R})
            rows.append(f)
    return pd.DataFrame(rows).sort_values("t0").reset_index(drop=True)


def cmd_hazirla() -> None:
    OUT.mkdir(exist_ok=True)
    b = bot_table()
    b.to_parquet(OUT / "bot.parquet", index=False)
    print("bot:", len(b), b.groupby(["sym", "yon"]).B.agg(["size", "mean"]).round(2).to_dict("index"))
    s = ndx_synth()
    s.to_parquet(OUT / "ndx_sentetik.parquet", index=False)
    print("NDX sentetik (2025-01 → 2026-06):", len(s), s.groupby("yon").B.agg(["size", "mean"]).round(3).to_dict("index"))


# ── yardımcılar ──────────────────────────────────────────────────────────────

CAT = ("aile", "session", "yon")
SKIP = {"sym", "yon", "t0", "t1", "B", "R", "pid", "aile", "session"}
SYNTH_OK_PREFIX = ("pre_", "geo_", "g1_", "g5_", "g15_", "g60_", "vwap", "gun_", "hour_utc", "dow", "min_from")


def num_cols(d: pd.DataFrame, synth_only: bool = False) -> list[str]:
    cs = [c for c in d.columns if c not in SKIP and pd.api.types.is_numeric_dtype(d[c])
          and d[c].notna().mean() > 0.8 and d[c].nunique() > 2]
    if synth_only:
        cs = [c for c in cs if c.startswith(SYNTH_OK_PREFIX) and not c.startswith("geo_")]
    return cs


def conditions(ref: pd.DataFrame, cols: list[str], cats: tuple) -> list[tuple]:
    """(ad, sütun, alt, üst) tertil kutuları referans kümeden; kategoriler (ad, sütun, değer, None)."""
    out = []
    for c in cols:
        q1, q2 = ref[c].quantile([1 / 3, 2 / 3])
        if not (np.isfinite(q1) and np.isfinite(q2)) or q1 == q2:
            continue
        out += [(f"{c} düşük (≤{q1:.3g})", c, -np.inf, q1), (f"{c} orta", c, q1, q2), (f"{c} yüksek (>{q2:.3g})", c, q2, np.inf)]
    for c in cats:
        if c in ref:
            out += [(f"{c} = {v}", c, v, None) for v in ref[c].dropna().unique()]
    return out


def cmask(d: pd.DataFrame, cond: tuple) -> np.ndarray:
    _, c, lo, hi = cond
    if hi is None:
        return (d[c] == lo).to_numpy()
    x = d[c].to_numpy(float)
    return (x > lo) & (x <= hi)


def mine(d: pd.DataFrame, conds: list[tuple], min_sup: int, pairs: bool = True) -> list[tuple]:
    """[(SL farkı, ad, [koşullar], maske)] — SL oranı − taban."""
    base = d.B.mean()
    masks = [(c, cmask(d, c)) for c in conds]
    masks = [(c, m) for c, m in masks if m.sum() >= min_sup]
    res = [(d.B.to_numpy()[m].mean() - base, c[0], [c], m) for c, m in masks]
    if pairs:
        top = sorted(res, key=lambda x: -x[0])[:40]
        for (l1, n1, c1, m1), (l2, n2, c2, m2) in itertools.combinations(top, 2):
            if c1[0][1] == c2[0][1]:
                continue
            m = m1 & m2
            if m.sum() >= min_sup:
                res.append((d.B.to_numpy()[m].mean() - base, f"{n1} VE {n2}", c1 + c2, m))
    return sorted(res, key=lambda x: -x[0])


def apply_rule(d: pd.DataFrame, rule: list[tuple]) -> np.ndarray:
    m = np.ones(len(d), dtype=bool)
    for c in rule:
        m &= cmask(d, c)
    return m


# ── A: alt-grup madenciliği ──────────────────────────────────────────────────

def part_a(d: pd.DataFrame, label: str, lines: list) -> None:
    cut = int(len(d) * 0.6)
    lines.append(f"\n### A) {label}: n={len(d)} · SL oranı %{100 * d.B.mean():.0f} · ort R {d.R.mean():+.3f}")
    real = []
    for nm, tr, te in (("ileri", d.iloc[:cut], d.iloc[cut:]), ("geri", d.iloc[cut:], d.iloc[:cut])):
        conds = conditions(tr, num_cols(d), CAT)
        top = mine(tr, conds, MIN_SUP)[:TOP]
        te_base = te.B.mean()
        outs = []
        for lift, name, rule, _ in top:
            m = apply_rule(te, rule)
            outs.append((name, lift, m.sum(), (te.B[m].mean() - te_base) if m.sum() else np.nan, te.R[m].mean() if m.sum() else np.nan))
        lines.append(f"  [{nm}] keşifte en SL'li 10 tip → sınamada:")
        for name, lift, n, tl, tr_ in outs[:5]:
            lines.append(f"    {name[:95]:95s} keşif +{lift * 100:4.0f}pp | sınama n={n:3d} {tl * 100:+5.0f}pp ort R {tr_:+.2f}")
        mean_real = np.nanmean([o[3] for o in outs])
        null = []
        for _ in range(50):
            p = tr.copy()
            perm = RNG.permutation(len(p))
            p["B"], p["R"] = p.B.to_numpy()[perm], p.R.to_numpy()[perm]
            tops = mine(p, conds, MIN_SUP, pairs=False)[:TOP]
            vals = [te.B[apply_rule(te, r)].mean() - te_base for _, _, r, _ in tops if apply_rule(te, r).sum()]
            null.append(np.nanmean(vals))
        null = np.array(null)
        lines.append(f"    → en iyi 10'un sınama SL farkı ort {mean_real * 100:+.1f}pp · plasebo ort {np.nanmean(null) * 100:+.1f}pp, "
                     f"%90 üst {np.nanquantile(null, 0.9) * 100:+.1f}pp → {'GEÇTİ' if mean_real > np.nanquantile(null, 0.9) else 'tesadüften ayırt edilemiyor'}")
        real.append(mean_real)


# ── B: benzerlik tekrarı ─────────────────────────────────────────────────────

def knn_scores(d: pd.DataFrame, cols: list[str], k: int, labels: np.ndarray) -> np.ndarray:
    X = d[cols].astype(float)
    X = ((X - X.median()) / (X.quantile(0.75) - X.quantile(0.25)).replace(0, 1)).clip(-4, 4).fillna(0).to_numpy()
    t0, t1 = d.t0.to_numpy(), d.t1.to_numpy()
    sc = np.full(len(d), np.nan)
    for i in range(len(d)):
        past = np.flatnonzero(t1 < t0[i])
        if past.size < k:
            continue
        dist = np.sqrt(((X[past] - X[i]) ** 2).mean(axis=1))
        nn = past[np.argsort(dist)[:k]]
        sc[i] = labels[nn].mean()
    return sc


def part_b(d: pd.DataFrame, label: str, lines: list, n_plac: int = 100) -> None:
    fams = {"bar": [c for c in num_cols(d) if c.startswith(("pre_", "geo_"))],
            "gösterge": [c for c in num_cols(d) if c.startswith(("g1_", "g5_", "g15_", "g60_", "vwap", "gun_"))],
            "hepsi": num_cols(d)}
    y = d.B.to_numpy()
    parts = []
    for fam, cols in fams.items():
        for k in (5, K_NN, 20):
            sc = knn_scores(d, cols, k, y)
            ok = np.isfinite(sc)
            if ok.sum() < 30:
                continue
            a = auc(sc[ok & (y == 1)], sc[ok & (y == 0)])
            if k == K_NN:
                null = []
                for _ in range(n_plac):
                    yp = RNG.permutation(y)
                    sp = knn_scores(d, cols, k, yp)
                    okp = np.isfinite(sp)
                    null.append(auc(sp[okp & (y == 1)], sp[okp & (y == 0)]))
                parts.append(f"{fam} k={k}: AUC {a:.3f} (plasebo %95 üst {np.quantile(null, 0.95):.3f})")
            else:
                parts.append(f"{fam} k={k}: {a:.3f}")
    lines.append(f"\n### B) {label}: benzer geçmiş işlemlerin SL oranı bu işlemin SL'sini öngörüyor mu? (0,5 = hayır)")
    lines += ["    " + p for p in parts]


# ── C: SL kümeleme ───────────────────────────────────────────────────────────

def kmeans(X: np.ndarray, k: int, it: int = 100) -> np.ndarray:
    C = X[RNG.choice(len(X), k, replace=False)]
    for _ in range(it):
        lab = np.argmin(((X[:, None, :] - C[None]) ** 2).sum(-1), axis=1)
        C = np.vstack([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
    return C


def part_c(d: pd.DataFrame, label: str, lines: list) -> None:
    cols = num_cols(d)
    cut = int(len(d) * 0.6)
    tr, te = d.iloc[:cut], d.iloc[cut:]
    med, iqr = tr[cols].median(), (tr[cols].quantile(0.75) - tr[cols].quantile(0.25)).replace(0, 1)
    z = lambda x: ((x[cols] - med) / iqr).clip(-4, 4).fillna(0).to_numpy()  # noqa: E731
    sl = tr[tr.B == 1]
    if len(sl) < 4 * N_CLUST:
        return
    C = kmeans(z(sl), N_CLUST)
    lines.append(f"\n### C) {label}: keşif SL'lerinden {N_CLUST} küme → sınamada kümeye düşen işlemlerin SL oranı (taban %{100 * te.B.mean():.0f})")
    for nm, part in (("keşif", tr), ("sınama", te)):
        lab = np.argmin(((z(part)[:, None, :] - C[None]) ** 2).sum(-1), axis=1)
        stats = [f"k{j}: n={int((lab == j).sum())} SL %{100 * part.B[lab == j].mean():.0f}" for j in range(N_CLUST) if (lab == j).any()]
        lines.append(f"    {nm}: " + " · ".join(stats))
    for j in range(N_CLUST):
        top = np.argsort(-np.abs(C[j]))[:4]
        lines.append(f"    k{j} merkezi: " + ", ".join(f"{cols[t]} {'yüksek' if C[j][t] > 0 else 'düşük'}" for t in top))


# ── D: NASDAQ bağımsız doğrulama ─────────────────────────────────────────────

def day_block_ci(x: np.ndarray, days: np.ndarray, base: float, n: int = 1000) -> tuple[float, float]:
    ud = np.unique(days)
    by = {u: x[days == u] for u in ud}
    vals = []
    for _ in range(n):
        pick = RNG.choice(ud, len(ud))
        v = np.concatenate([by[u] for u in pick])
        vals.append(v.mean() - base)
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))


def part_d(bot: pd.DataFrame, syn: pd.DataFrame, lines: list) -> None:
    lines.append("\n### D) NASDAQ: botun SL'ye yatkın tipleri, botun ÇALIŞMADIĞI 2025-01 → 2026-06'da (sentetik giriş) da SL'ye yatkın mı?")
    cols = num_cols(bot[bot.sym == "NDX"], synth_only=True)
    for yon in ("BUY", "SELL"):
        b = bot[(bot.sym == "NDX") & (bot.yon == yon)].reset_index(drop=True)
        s = syn[syn.yon == yon].reset_index(drop=True)
        conds = conditions(b, cols, ())
        half = np.arange(len(b)) < len(b) // 2
        cands = []
        for lift, name, rule, m in mine(b, conds, MIN_SUP_D):
            l1 = b.B[m & half].mean() - b.B[half].mean() if (m & half).sum() >= 4 else -1
            l2 = b.B[m & ~half].mean() - b.B[~half].mean() if (m & ~half).sum() >= 4 else -1
            if lift > 0 and l1 > 0 and l2 > 0:
                cands.append((lift, name, rule))
            if len(cands) >= TOP:
                break
        sbase, days = s.B.mean(), s.t0.dt.normalize().to_numpy()
        lines.append(f"\n  NDX {yon}: bot n={len(b)} SL %{100 * b.B.mean():.0f} · sentetik n={len(s)} SL %{100 * sbase:.1f} ort R {s.R.mean():+.3f}")
        lifts = []
        for lift, name, rule in cands:
            m = apply_rule(s, rule)
            if m.sum() < 30:
                lines.append(f"    {name[:90]:90s} bot +{lift * 100:.0f}pp | 2025-26: yetersiz ({m.sum()})")
                continue
            sl = s.B[m].mean() - sbase
            lo, hi = day_block_ci(s.B.to_numpy()[m].astype(float), days[m], sbase)
            lifts.append(sl)
            lines.append(f"    {name[:90]:90s} bot +{lift * 100:3.0f}pp | 2025-26 n={m.sum():5d} {sl * 100:+5.1f}pp "
                         f"[{lo * 100:+.1f}…{hi * 100:+.1f}] ort R {s.R[m].mean():+.3f} {'✓' if lo > 0 else ''}")
        null = []
        for _ in range(200):
            c1, c2 = RNG.choice(len(conds), 2, replace=False)
            if conds[c1][1] == conds[c2][1]:
                continue
            m = apply_rule(s, [conds[c1], conds[c2]])
            if m.sum() >= 30:
                null.append(s.B[m].mean() - sbase)
        if lifts:
            lines.append(f"    → gerçek koşulların 2025-26 SL farkı ort {np.mean(lifts) * 100:+.1f}pp · rastgele 2'li koşullar ort "
                         f"{np.mean(null) * 100:+.1f}pp, %90 üst {np.quantile(null, 0.9) * 100:+.1f}pp · %95'i sıfırın üstünde: "
                         f"{sum(1 for _ in lifts)} içinden {sum(1 for l in lines[-len(lifts) - 1:] if l.endswith('✓'))}")


def cmd_analiz() -> None:
    bot = pd.read_parquet(OUT / "bot.parquet")
    syn = pd.read_parquet(OUT / "ndx_sentetik.parquet")
    lines = []
    for sym, g in bot.groupby("sym"):
        g = g.reset_index(drop=True)
        part_a(g, f"{sym} (iki yön)", lines)
        for yon, h in g.groupby("yon"):
            if len(h) >= 60:
                part_a(h.reset_index(drop=True), f"{sym} {yon}", lines)
        for yon, h in g.groupby("yon"):
            if len(h) >= 40:
                part_b(h.reset_index(drop=True), f"{sym} {yon}", lines)
        if len(g) >= 60:
            part_c(g, sym, lines)
    part_d(bot, syn, lines)
    b2 = syn.sample(n=min(3000, len(syn)), random_state=1).sort_values("t0").reset_index(drop=True)
    for yon, h in b2.groupby("yon"):
        part_b(h.reset_index(drop=True), f"NDX sentetik 2025-26 {yon} (örneklem)", lines, n_plac=30)
    txt = "\n".join(lines)
    (OUT / "rapor.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    {"hazirla": cmd_hazirla, "analiz": cmd_analiz}[sys.argv[1]]()
