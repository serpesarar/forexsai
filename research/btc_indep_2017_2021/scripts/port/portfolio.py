"""Kol ve portföy kartları + vetolar + plasebo (prereg §5–§8). Çıktı: results/cards.json, cards_table.csv, vetoes.csv,
corr_post.csv, placebo.pkl, portfolio_trades.pkl"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import lib_st as L
import sleeves as SV

t0 = time.time()
E = SV.engine()
TR = pd.read_pickle(L.RES / "trades.pkl")
NAMES = [k for k in SV.SLEEVES]
NPL = 200
rng = np.random.default_rng(20261022)
DAYM = 1440

# ───────────────────────── vetolar (karar anı = ent) ─────────────────────────
b5 = pd.read_parquet(SV.R5 / "data" / "btc_5m.parquet", columns=["ts", "close"])
S5 = L.lt.tmin(b5["ts"]) + 5          # 5m bar KAPANIŞ anı (epoch dk)
C5 = b5["close"].to_numpy()
j = np.searchsorted(S5, S5 - 60)
okj = (j < len(S5)) & (S5[np.minimum(j, len(S5) - 1)] == S5 - 60)
RET60 = np.where(okj, C5 / C5[np.minimum(j, len(S5) - 1)] - 1, np.nan)
SIG60 = pd.Series(RET60).rolling(8640, min_periods=4000).std().shift(1).to_numpy()
with np.errstate(invalid="ignore"):
    UPSHOCK = RET60 >= 3.5 * SIG60
cs_up = np.concatenate([[0], np.cumsum(UPSHOCK.astype(int))])


def v1_flag(t):
    """(t−60, t] içinde kapanan herhangi bir 5m barda r60 ≥ +3,5σ60."""
    a = np.searchsorted(S5, t - 60, "right")
    b = np.searchsorted(S5, t, "right")
    return (cs_up[b] - cs_up[a]) > 0


m1 = pd.read_parquet(SV.R5 / "data" / "btc_1m.parquet", columns=["ts", "high", "low", "close", "volume"])
MT = L.lt.tmin(m1["ts"])
tp_ = ((m1["high"] + m1["low"] + m1["close"]) / 3).to_numpy()
vv = m1["volume"].to_numpy()
day = MT // DAYM
cv = pd.Series(vv).groupby(day).cumsum().to_numpy()
cpv = pd.Series(vv * tp_).groupby(day).cumsum().to_numpy()
cp2v = pd.Series(vv * tp_ * tp_).groupby(day).cumsum().to_numpy()
MH = m1["high"].to_numpy()
MC = m1["close"].to_numpy()
DF = SV.daily_flags()


def v3_flag(t):
    i = np.searchsorted(MT, t, "left") - 1          # karar barı (t'den önce kapanan son 1m)
    i = np.maximum(i, 0)
    same = (MT[i] // DAYM) == (t // DAYM)
    vw = cpv[i] / np.maximum(cv[i], 1e-12)
    sd = np.sqrt(np.maximum(cp2v[i] / np.maximum(cv[i], 1e-12) - vw * vw, 0))
    c = MC[i]
    a = np.searchsorted(MT, t - 15, "left")
    hi15 = np.array([MH[x:y + 1].max() if y >= x else np.nan for x, y in zip(a, i)])
    pdh = DF.pdh.reindex(t // DAYM).to_numpy()
    return (same & (c >= vw + 2 * sd)) | (hi15 > pdh)


def v2_flag(t):
    dd_ = t // DAYM
    st = DF.stress1.reindex(dd_).to_numpy().astype(bool)
    rvlo = (DF.rvhi.reindex(dd_).to_numpy() == 0.0)
    pdl = DF.pdl.reindex(dd_).to_numpy()
    c = SV.sig_close(t)
    return st & rvlo & (c < pdl)


for k in NAMES:
    df = TR[k]
    t = df.ent.to_numpy(np.int64)
    sell = df.dir.to_numpy() == -1
    buy = ~sell
    df["V1"] = sell & v1_flag(t)
    df["V2"] = buy & v2_flag(t)
    df["V3"] = sell & v3_flag(t) if sell.any() else False
    df["VANY"] = df.V1 | df.V2 | df.V3
print(f"vetolar {time.time()-t0:.0f}s", flush=True)


def chain(df):
    keep = L.single_position(df.ent_t.to_numpy().astype(float), df.ext_t.to_numpy())
    return df.iloc[np.sort(keep)].copy()


def sleeve_set(k, veto=False):
    df = TR[k]
    if veto:
        df = df[~df.VANY]
    return chain(df)


# ───────────────────────── kart ─────────────────────────
WIN = {"IND": ["A", "PERP"], "PERP": ["PERP"], "A": ["A"]}


def card(df, win="POST", glob_single=False):
    d = df[df.split.isin(WIN[win])].sort_values("ent_t")
    n = len(d)
    r = {"n": n}
    if n == 0:
        return r
    R = d.R.to_numpy()
    dayk = (d.ent_t.to_numpy() // DAYM)
    r["n_gün"] = int(len(np.unique(dayk)))
    r["WR"] = float(np.mean(R > 0))
    r["ortR"] = float(R.mean())
    r["bp"] = float(d.bp.mean())
    P, lo, hi = L.day_boot(R, dayk)
    r["P"], r["GA"] = P, [lo, hi]
    h = n // 2
    r["yarı1"], r["yarı2"] = float(R[:h].mean()) if h else np.nan, float(R[h:].mean())
    r["stres"] = float(d.R_st.mean())
    r["abs15"] = float(d.R_abs.mean())
    r["iyimser"] = float(d.R_opt.mean())
    r["icra_farkı"] = abs(r["iyimser"] - r["ortR"])
    gs = chain(d)
    r["küresel_tekpoz_n"], r["küresel_tekpoz_R"] = len(gs), float(gs.R.mean())
    ds = pd.Series(R).groupby(dayk).sum().sort_values(ascending=False)
    for kk in (5, 20):
        drop = set(ds.index[:kk])
        rest = R[~np.isin(dayk, list(drop))]
        r[f"enİyi{kk}gün_hariç"] = float(rest.mean()) if len(rest) else np.nan
    o = np.argsort(d.ext_t.to_numpy())
    r["maxDD_R"] = L.max_dd_R(R[o])
    r["ΣR"] = float(R.sum())
    yrs = pd.to_datetime(d.ent_t.to_numpy() * 60, unit="s").year
    r["yıl"] = {int(y): [int((yrs == y).sum()), round(float(R[yrs == y].mean()), 3)] for y in np.unique(yrs)}
    b = d[d.split == "BLIND"]
    r["BLIND_n"], r["BLIND_R"] = len(b), float(b.R.mean()) if len(b) else np.nan
    r["aynı_bar_%"] = float(100 * d.samebar.mean())
    c = [n >= 150, (r["ortR"] > 0) and (P >= 0.90), (r["yarı1"] >= 0) and (r["yarı2"] >= 0), r["stres"] > 0,
         r["icra_farkı"] <= r["ortR"] / 2 if r["ortR"] > 0 else False, r["küresel_tekpoz_R"] > 0 if glob_single else r["ortR"] > 0]
    r["ölçütler"] = [bool(x) for x in c]
    r["kart"] = int(sum(c))
    return r


# ───────────────────────── plasebo ─────────────────────────
def placebo_sleeve(k, df):
    """df: kolun (tek-poz) işlemleri. Dönüş: (NPL × n) R matrisi (NaN = geçersiz)."""
    fev, fgeom = SV.SLEEVES[k]
    n = len(df)
    ent = df.ent.to_numpy(np.int64)
    dirn = df.dir.to_numpy(np.int64)
    out = np.full((NPL, n), np.nan)
    need = np.ones((NPL, n), bool)
    yrs = pd.to_datetime(ent * 60, unit="s").year.to_numpy()
    mod = ent % DAYM
    for it in range(6):
        if not need.any():
            break
        if k == "S3_QB":
            dur = (df.end - df.ent).to_numpy()
            hh = rng.integers(0, 24, size=(NPL, n))
            tp = (ent // DAYM * DAYM)[None, :] + hh * 60 + (ent % 60)[None, :]
        else:
            tp = np.empty((NPL, n), np.int64)
            for y in np.unique(yrs):
                d0 = max(L.em(f"{y}-01-01"), L.em("2017-08-17")) // DAYM
                d1 = min(L.em(f"{y + 1}-01-01"), L.em("2021-05-31")) // DAYM
                mk = yrs == y
                tp[:, mk] = rng.integers(d0, d1, size=(NPL, int(mk.sum()))) * DAYM + mod[mk][None, :]
        sel = need
        tt = tp[sel]
        dd = np.broadcast_to(dirn[None, :], (NPL, n))[sel]
        if k == "S3_QB":
            g = fgeom(tt, dd, np.broadcast_to(dur[None, :], (NPL, n))[sel])
        else:
            g = fgeom(tt, dd)
        s = E.simulate(g.ent, g.dir, g.sl_d, g.tp_d, g.end, g.sig, mode="base")
        R = s.R.to_numpy() * (g.sl_d.to_numpy() / g.R_den.to_numpy())
        vals = out[sel]
        good = np.isfinite(R)
        vals[good] = R[good]
        out[sel] = vals
        nd = need.copy()
        nd[sel] = ~good
        need = nd
    return out


cards, PL = {}, {}
SETS = {}
for k in NAMES:
    SETS[k] = sleeve_set(k)
    SETS[k + "+V"] = sleeve_set(k, veto=True)
for k in NAMES:
    df = SETS[k]
    PL[k] = placebo_sleeve(k, df)
    print(f"plasebo {k} n={len(df)} geçersiz %{100*np.mean(~np.isfinite(PL[k])):.1f} ({time.time()-t0:.0f}s)", flush=True)
pd.to_pickle({"PL": PL, "SETS": SETS}, L.RES / "placebo.pkl")


def plac_pct(names, win):
    acts, pms = [], np.zeros(NPL)
    num, den = np.zeros(NPL), np.zeros(NPL)
    tot, cnt = 0.0, 0
    for k in names:
        df = SETS[k]
        m = df.split.isin(WIN[win]).to_numpy()
        P = PL[k][:, m]
        num += np.nansum(P, axis=1)
        den += np.sum(np.isfinite(P), axis=1)
        tot += df.R.to_numpy()[m].sum()
        cnt += m.sum()
    pm = num / np.maximum(den, 1)
    act = tot / max(cnt, 1)
    return float(np.mean(pm < act) * 100), float(np.mean(pm)), pm


PORT = {"P-CORE": ["S1_CORE"], "P-PRE": ["S1_CORE", "S2_MAX10", "S3_QB", "S4_X04"],
        "P-ALL": NAMES, "P-ALL-DV": NAMES[:6]}
rows = []
for unit, names, glob in [(k, [k], False) for k in NAMES] + [(p, v, True) for p, v in PORT.items()]:
    for veto in (False, True):
        df = pd.concat([SETS[k + ("+V" if veto else "")] for k in names], ignore_index=True)
        for win in ("IND", "PERP", "A"):
            c = card(df, win, glob_single=glob)
            if not veto:
                pp, pmean, _ = plac_pct(names, win)
                c["plasebo_%"], c["plasebo_ort"] = pp, pmean
            key = f"{unit}{'+V' if veto else ''}|{win}"
            cards[key] = c
            rows.append({"birim": unit, "veto": veto, "dönem": win, **{kk: (round(v, 4) if isinstance(v, float) else v)
                                                                        for kk, v in c.items() if kk not in ("yıl", "GA", "ölçütler")},
                         "GA": [round(x, 3) for x in c.get("GA", [np.nan, np.nan])], "ölçütler": c.get("ölçütler")})
tab = pd.DataFrame(rows)
tab.to_csv(L.RES / "cards_table.csv", index=False)
json.dump(cards, open(L.RES / "cards.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250)
cols = ["birim", "veto", "dönem", "n", "n_gün", "ortR", "bp", "P", "yarı1", "yarı2", "stres", "abs15", "icra_farkı",
        "küresel_tekpoz_R", "enİyi20gün_hariç", "maxDD_R", "BLIND_R", "plasebo_%", "kart"]
print(tab[cols].to_string())

# ───────────────────────── korelasyon + katkı (POST) ─────────────────────────
a, b = L.SPLITS["A"][0] // DAYM, L.SPLITS["PERP"][1] // DAYM
days = np.arange(a, b)
M = pd.DataFrame(index=days)
for k in NAMES:
    d = SETS[k][SETS[k].split.isin(["A", "PERP"])]
    M[k] = pd.Series(d.R.to_numpy()).groupby(d.ent_t.to_numpy() // DAYM).sum().reindex(days).fillna(0).to_numpy()
corr = M.corr().round(3)
corr.to_csv(L.RES / "corr_post.csv")
print("\nPOST günlük ΣR korelasyonu:\n", corr.to_string())
act = (M != 0)
ov = pd.DataFrame({k: [round(float((act[k] & act[j]).sum() / max(act[k].sum(), 1)), 3) for j in NAMES] for k in NAMES}, index=NAMES)
ov.to_csv(L.RES / "overlap_post.csv")
print("\naynı gün örtüşme (satır kolun işlem günlerinin, sütun kolunun da işlem yaptığı payı):\n", ov.T.to_string())
contrib = {p: {k: round(float(M[k].sum()), 2) for k in v} for p, v in PORT.items()}
json.dump({"contrib_POST_sumR": contrib}, open(L.RES / "contrib.json", "w"), indent=1)
print("\nPOST ΣR katkı:", contrib)

# ───────────────────────── veto marjinal etkisi ─────────────────────────
vrows = []
for k in NAMES:
    df = TR[k]
    for v in ("V1", "V2", "V3"):
        for win in ("IND",):
            m = df[v].to_numpy() & df.split.isin(WIN[win]).to_numpy()
            vrows.append({"kol": k, "veto": v, "dönem": win, "silinen_n(tüm olay)": int(m.sum()),
                          "silinenlerin_ortR": round(float(df.R[m].mean()), 3) if m.any() else np.nan})
vt = pd.DataFrame(vrows)
vt = vt[vt["silinen_n(tüm olay)"] > 0]
vt.to_csv(L.RES / "vetoes.csv", index=False)
print("\nveto silmeleri:\n", vt.to_string())
pd.to_pickle(SETS, L.RES / "portfolio_trades.pkl")
print(f"bitti {time.time()-t0:.0f}s")
