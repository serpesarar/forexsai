"""DAYCOMBO aile-içi SL ayırıcı / SQZ kombo araması — bkz. PROTOCOL.md.

python3 research/daycombo_kombo_20261020/run.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "results"
sys.path.insert(0, str(ROOT))


def _mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


SO = _mod("sl_ortak_run", ROOT / "research" / "sl_ortak_20261009" / "run.py")
sys.path.insert(0, str(ROOT / "research" / "sikisma_derin_20261020"))
import core as C  # noqa: E402

TP, SL, SPREAD = 80.0, 110.0, 1.5
MIN_SUP, TOPK, N_PLAC = 15, 10, 300
RNG = np.random.default_rng(1019)
SQZ = "atr_14_100"
SKIP = {"t", "R", "B", "period", "split", "exit"}


def build() -> pd.DataFrame:
    tr = pd.read_parquet(ROOT / "research" / "canli_kart_20261009" / "results" / "daycombo_trades.parquet")
    long = C.bars_ndx_long()
    sb = C.SymbolBars("NDX.INDX", long)
    ext = SO.G.Ext(sb)
    F = C.compute_feats(long)
    vix = C.data.load_vix(pd.Timestamp("2024-11-01", tz="UTC"), C.data.utc_now()).sort_index()
    rows = []
    for _, r in tr.iterrows():
        t = pd.Timestamp(r.entry)
        j = sb.pos_at(t)
        if j < 500:
            continue
        e = float(sb.a["open"][j]) + SPREAD
        f = SO.entry_features(sb, ext, 1, e, SL, TP / SL, t, SPREAD)
        if f is None:
            continue
        day0 = t.normalize()
        k0 = sb.m1.index.searchsorted(day0)
        k1 = sb.m1.index.searchsorted(day0 + pd.Timedelta(hours=13, minutes=25))
        gece = float(sb.a["close"][k1 - 1] / sb.a["open"][k0] - 1) if k1 > k0 else np.nan
        nyd = pd.Timestamp(t.tz_convert("America/New_York").date())
        pv = vix[vix.index < nyd]
        rows.append({**f, "t": t, "exit": r.exit, "R": float(r.R), "period": r.period, "gece_getiri": gece,
                     "vix_onceki": float(pv.iloc[-1]) if len(pv) else np.nan})
    d = pd.DataFrame(rows).sort_values("t").reset_index(drop=True)
    sq = C.feats_at(F, d.t).reset_index(drop=True)
    d = pd.concat([d, sq], axis=1)
    d["gun_sira"] = d.groupby(d.t.dt.normalize()).cumcount() + 1
    prev = []
    for i in range(len(d)):
        g = d[(d.t.dt.normalize() == d.t[i].normalize()) & (pd.to_datetime(d.exit, utc=True) <= d.t[i])]
        prev.append(float(g.R.iloc[-1] > 0) if len(g) else np.nan)
    d["onceki_dc_kazandi"] = prev
    d["B"] = (d.R < 0).astype(int)
    d["split"] = np.where(d.t < pd.Timestamp("2026-01-01", tz="UTC"), "keşif", "sınama")
    return d


def conditions(ref: pd.DataFrame, cols: list[str]) -> list[tuple[str, np.ndarray]]:
    """(ad, maske fonksiyonu yerine eşikler) — keşif tertilleri."""
    out = []
    for c in cols:
        x = ref[c].to_numpy(float)
        ok = np.isfinite(x)
        if ok.sum() < 3 * MIN_SUP or np.unique(x[ok]).size < 3:
            if np.unique(x[ok]).size == 2:
                v = np.unique(x[ok])[1]
                out.append((f"{c}={v:g}", (c, "eq", v)))
            continue
        q1, q2 = np.quantile(x[ok], [1 / 3, 2 / 3])
        out += [(f"{c}≤{q1:.3g}", (c, "le", q1)), (f"{q1:.3g}<{c}≤{q2:.3g}", (c, "mid", (q1, q2))),
                (f"{c}>{q2:.3g}", (c, "gt", q2))]
    return out


def mask(d: pd.DataFrame, spec: tuple) -> np.ndarray:
    c, op, v = spec
    x = d[c].to_numpy(float)
    if op == "eq":
        return x == v
    if op == "le":
        return x <= v
    if op == "gt":
        return x > v
    return (x > v[0]) & (x <= v[1])


def search(k: pd.DataFrame, conds: list, R: np.ndarray) -> dict[str, list]:
    M = {n: mask(k, s) for n, s in conds}
    names = list(M)
    sq_lo, sq_hi = k[SQZ].to_numpy(float) < 1, k[SQZ].to_numpy(float) >= 1
    fam = {"tek": [], "SQZ∧X": [], "çift": []}
    for n in names:
        m = M[n]
        if m.sum() >= MIN_SUP:
            fam["tek"].append((R[m].mean(), n, [n]))
        for sn, sm in (("SQZ<1", sq_lo), ("SQZ≥1", sq_hi)):
            mm = m & sm
            if mm.sum() >= MIN_SUP and not n.startswith(SQZ):
                fam["SQZ∧X"].append((R[mm].mean(), f"{sn} ∧ {n}", [sn, n]))
    arr = np.array([M[n] for n in names])
    cnt = arr.astype(int) @ arr.T.astype(int)
    sums = (arr * R) .astype(float) @ arr.T.astype(float)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if names[i].split("≤")[0].split(">")[0].split("<")[-1] == names[j].split("≤")[0].split(">")[0].split("<")[-1]:
                continue
            if cnt[i, j] >= MIN_SUP:
                fam["çift"].append((sums[i, j] / cnt[i, j], f"{names[i]} ∧ {names[j]}", [names[i], names[j]]))
    return {f: sorted(v)[:TOPK] for f, v in fam.items()}


def apply(d: pd.DataFrame, rule: list[str], conds: dict) -> np.ndarray:
    m = np.ones(len(d), bool)
    for n in rule:
        if n == "SQZ<1":
            m &= d[SQZ].to_numpy(float) < 1
        elif n == "SQZ≥1":
            m &= d[SQZ].to_numpy(float) >= 1
        else:
            m &= mask(d, conds[n])
    return m


def main() -> None:
    OUT.mkdir(exist_ok=True)
    p = OUT / "daycombo_feats.parquet"
    d = pd.read_parquet(p) if p.exists() else build()
    d.to_parquet(p)
    k, s = d[d.split == "keşif"].reset_index(drop=True), d[d.split == "sınama"].reset_index(drop=True)
    cols = [c for c in d.columns if c not in SKIP and pd.api.types.is_numeric_dtype(d[c]) and c != "B"]
    conds = conditions(k, cols)
    cd = dict(conds)
    L = ["# DAYCOMBO aile-içi SL ayırıcı / SQZ kombo araması (ön-kayıt PROTOCOL.md)",
         f"\nkeşif 2025: n={len(k)} ortR {k.R.mean():+.3f} SL %{100 * k.B.mean():.0f} · sınama 2026: n={len(s)} "
         f"ortR {s.R.mean():+.3f} SL %{100 * s.B.mean():.0f} · {len(cols)} özellik, {len(conds)} koşul"]
    real = search(k, conds, k.R.to_numpy(float))
    Rk = k.R.to_numpy(float)
    plac = {f: [] for f in real}
    for _ in range(N_PLAC):
        sel = search(k, conds, RNG.permutation(Rk))
        for f, top in sel.items():
            vals = [-s.R[apply(s, r, cd)].sum() for _, _, r in top]
            plac[f].append(np.mean(vals) if vals else np.nan)
    for f, top in real.items():
        L.append(f"\n## Aile: {f}")
        L.append("| kural (keşifte en kötü 10) | keşif n | keşif ortR | sınama n | sınama ortR engel | sınama ortR kalan | sınama kurt_R |")
        L.append("|---|---|---|---|---|---|---|")
        sv = []
        for mr, name, rule in top:
            mk, ms = apply(k, rule, cd), apply(s, rule, cd)
            kr = -s.R[ms].sum()
            sv.append(kr)
            L.append(f"| {name} | {mk.sum()} | {mr:+.3f} | {ms.sum()} | {s.R[ms].mean() if ms.any() else np.nan:+.3f} | "
                     f"{s.R[~ms].mean():+.3f} | {kr:+.2f} |")
        pl = np.array(plac[f], float)
        pl = pl[np.isfinite(pl)]
        npos = sum(x > 0 for x in sv)
        pct = float((pl < np.mean(sv)).mean()) if pl.size else np.nan
        ok = npos >= 6 and pct >= 0.90
        L.append(f"\n**{f}: sınamada + olan {npos}/10 · ortalama kurt_R {np.mean(sv):+.2f} · plasebo yüzdeliği %{100 * pct:.0f} "
                 f"(plasebo medyan {np.median(pl):+.2f}) → {'GEÇTİ (gölge adayı)' if ok else 'GEÇMEDİ'}**")
    txt = "\n".join(L)
    (OUT / "rapor.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
