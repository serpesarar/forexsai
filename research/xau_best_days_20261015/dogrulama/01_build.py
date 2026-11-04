"""ADIM 1: ana küme (Duka 2008-01→2026-06-16) mutabakatı + S bayrakları + seçim ailesinin yeniden kurulumu.
Çıktı: results/allev.parquet (12.403 olay + S bayrakları), results/base.parquet (tek-poz 3.664 + aile bayrakları),
results/family.json (aile bayrak adları), results/allbars.parquet (P1-F havuzu: her geçerli bar için rastgele-BUY R + S)."""
from __future__ import annotations
import json, os
import numpy as np, pandas as pd
from common import (load_d, run_rule, add_flags, macro_inputs, one_position, path_sim, brk_density, gprev_for,
                    event_window, mak_feat, ANA, MAK, ERK, RES, SPREAD)

d = load_d(); M, cal = macro_inputs()
e = add_flags(run_rule(d), cal)
kb = one_position(e.ent.to_numpy(), e.xi.to_numpy())
e["base"] = kb
b = e[kb].reset_index(drop=True)
print(f"olay {len(e)}  tek-poz n={len(b)} toplam {b.R.sum():.1f} ortR {b.R.mean():+.4f}")
assert len(e) == 12403 and len(b) == 3664 and abs(b.R.sum() - 290.5) < 0.1

# ── aile: araştırmacıların bayrakları (salt-okunur dosyalardan, sig ile eşle) ──
A = pd.read_parquet(f"{ANA}/results/trades.parquet")
Mk = pd.read_csv(f"{MAK}/out/trades_feat.csv")
Ek = pd.read_parquet(f"{ERK}/results/events.parquet")
assert (A.sig.to_numpy() == b.sig.to_numpy()).all() and (Mk.sig.to_numpy() == b.sig.to_numpy()).all()
# kendi S1/S2'm araştırmacılarınkiyle birebir mi?
assert (b.dens24.to_numpy() == A.xa_brk_density24.to_numpy()).all(), "S1 tanımı uyuşmuyor"
assert (b.S2.to_numpy() == Mk.F_gprev_up1.to_numpy().astype(bool)).all(), "S2 tanımı uyuşmuyor"
assert np.allclose(b.R.to_numpy(), A.R.to_numpy())
fam: dict[str, np.ndarray] = {}
src: dict[str, str] = {}
# (a) anatomi: 33 xa_ özelliği → beşli Q1/Q5 (sürekli) veya =1 (ikili)
xa = [c for c in A.columns if c.startswith("xa_") and c != "xa_session"]
for f in xa:
    v = A[f].astype(float)
    if v.nunique() < 3:
        fam[f"{f}=1"] = (v == 1).to_numpy(); src[f"{f}=1"] = "anatomi"
    else:
        q = pd.qcut(v.rank(method="first"), 5, labels=False).to_numpy()
        fam[f"{f}_Q1"] = q == 0; fam[f"{f}_Q5"] = q == 4
        src[f"{f}_Q1"] = src[f"{f}_Q5"] = "anatomi"
for s in ("Asya", "Londra", "NY"):
    fam[f"seans_{s}"] = (A.xa_session == s).to_numpy(); src[f"seans_{s}"] = "anatomi"
fam["is_mon"] = (A.weekday == 0).to_numpy(); fam["is_fri"] = (A.weekday == 4).to_numpy()
src["is_mon"] = src["is_fri"] = "anatomi"
cands = {
    "dilim_asya23-06": (A.xa_hour_sig >= 23) | (A.xa_hour_sig <= 6),
    "dilim_atrH1pct≤0.2": A.xa_atrH1_pct500 <= 0.2,
    "S1_seri_kirilim(≥2)": A.xa_brk_density24 >= 2,
    "dilim_dens=0": A.xa_brk_density24 == 0,
    "dilim_ATH≤%2": A.xa_dist_ath_pct >= -0.02,
    "dilim_bbw120≤0.2": A.xa_bbw_pct120 <= 0.2,
    "dilim_seviye_yasi≥15": A.xa_level_age >= 15,
    "dilim_D1>EMA50": A.xa_d1_above_ema50 == 1,
    "dilim_tekil∧ATH≤%2": (A.xa_brk_density24 <= 1) & (A.xa_dist_ath_pct >= -0.02),
}
for k, v in cands.items():
    fam[k] = v.to_numpy(); src[k] = "anatomi"
# (b) makro: 18 F_ + olay pencereleri + post-hoc tatil + post-hoc düşük gvol
for f in [c for c in Mk.columns if c.startswith("F_")]:
    nm = "S2_onceki_gun>%1" if f == "F_gprev_up1" else f
    fam[nm] = Mk[f].to_numpy().astype(bool); src[nm] = "makro"
for ev_ in ("FOMC", "CPI", "NFP", "JH"):
    nm = "S3_FOMC_penceresi" if ev_ == "FOMC" else f"win_{ev_}"
    fam[nm] = event_window(Mk.ent_ts, cal, ev_); src[nm] = "makro"
spx_days = set(M.index[M.spx.notna()])
hol = [x for x in pd.bdate_range("2007-06-01", "2026-10-15") if x not in spx_days]
post = set()
for h in hol:
    nx = h + pd.offsets.BDay(1)
    while nx not in spx_days and nx < pd.Timestamp("2026-10-15"):
        nx += pd.offsets.BDay(1)
    post.add(nx); post.add(h)
fam["posthoc_tatil"] = pd.to_datetime(Mk.ent_day).isin(post).to_numpy(); src["posthoc_tatil"] = "makro"
fam["posthoc_gvol≤0.73"] = (Mk.gvol <= 0.73).to_numpy(); src["posthoc_gvol≤0.73"] = "makro"
# (c) erken_sinyal F1..F10
Ek = Ek.set_index("sig")
for f in [f"F{i}" for i in range(1, 11)]:
    fam[f"erken_{f}"] = Ek.loc[b.sig.to_numpy(), f].to_numpy().astype(bool); src[f"erken_{f}"] = "erken_sinyal"
# eşdeğer/boş bayrakları ayıkla
keep, seen = {}, set()
for k, v in fam.items():
    v = np.asarray(v, bool)
    if v.sum() < 20 or (~v).sum() < 20:
        continue
    key = v.tobytes(); keyc = (~v).tobytes()
    if key in seen or keyc in seen:
        continue
    seen.add(key); keep[k] = v
print(f"aile: {len(fam)} aday → {len(keep)} benzersiz bayrak (n≥20 iki tarafta)")
F = pd.DataFrame(keep)
F.columns = [f"fam::{c}" for c in F.columns]
b = pd.concat([b, F], axis=1)
b.to_parquet(os.path.join(RES, "base.parquet"))
e.to_parquet(os.path.join(RES, "allev.parquet"))
json.dump({"family": list(keep), "source": {k: src[k] for k in keep}}, open(os.path.join(RES, "family.json"), "w"),
          ensure_ascii=False, indent=1)

# ── P1-F havuzu: her geçerli bar için rastgele BUY (aynı geometri) R + S bayrakları ──
O, H, L, C = (d[k].to_numpy() for k in "ohlc"); seg = d.seg.to_numpy(); atr = d.atr.to_numpy(); n = len(d)
valid = np.zeros(n, bool); valid[:-1] = seg[1:] == seg[:-1]; valid &= np.isfinite(atr) & (atr > 0)
vi = np.where(valid)[0]
Rv, _, _ = path_sim(O, H, L, C, seg, vi, vi + 1, atr[vi], np.full(len(vi), 20), None, 1.5, +1, SPREAD)
P = pd.DataFrame({"sig": vi, "R": Rv})
P = P[np.isfinite(P.R)].reset_index(drop=True)
P["year"] = d.year.to_numpy()[P.sig]; P["utc_h"] = d.utc_h.to_numpy()[P.sig]
P["ent_ts"] = d.ts.to_numpy()[P.sig + 1]
P["dens24"] = brk_density(d)[P.sig]
P["gprev"] = gprev_for(d, P.sig.to_numpy() + 1)
P = add_flags(P, cal)
P.drop(columns=["ent_ts"]).to_parquet(os.path.join(RES, "allbars.parquet"))
print("P1-F havuzu", len(P), "rastgele BUY ortR", round(P.R.mean(), 4))
for s in ("S1", "S2", "S3_fomcwin"):
    print(f"  {s}: kural tek-poz oranı {b[s].mean():.3f}, ortR in {b.R[b[s]].mean():+.3f} out {b.R[~b[s]].mean():+.3f}")
