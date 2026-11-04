"""Çıkış mekaniği (X1–X10) nötr + momentum girişlerde, C02 VIXREG nötr filtre,
swap ekonomisi, hafta sonu analizi (prereg §1 C02, §2, §2.1, §3)."""
import json
import os
import pickle
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

g = load_grid()
RNG = np.random.default_rng(13)
VARS = [Var("X1", tp=1.0), Var("X2", tp=0.73), Var("X3", tp=2.0), Var("X4", hmax=240), Var("X5"),
        Var("X6", tp=2.0, be=0.5), Var("X7", tp=2.0, be=1.0), Var("X8", tp=1.0, runner=True),
        Var("X9", tp=1.0, runner=True, be30=True), Var("X10", tp=0.73, be=0.5)]
H24 = 1440

# ── ATR14(1h), bar bitişine göre ──
h1 = pd.read_parquet(os.path.join(DATA, "btc_1h.parquet"), columns=["ts", "open", "high", "low", "close"])
h1["atr"] = atr_wilder(h1["high"].to_numpy(), h1["low"].to_numpy(), h1["close"].to_numpy())
h1["end"] = h1["ts"] + pd.Timedelta(hours=1)


def psar(h, l, af0=0.02, afmax=0.2):
    n = len(h); sar = np.full(n, np.nan); up = True; af = af0; ep = h[0]; sar[0] = l[0]
    for i in range(1, n):
        s = sar[i - 1] + af * (ep - sar[i - 1])
        if up:
            s = min(s, l[i - 1], l[i - 2] if i > 1 else l[i - 1])
            if l[i] < s:
                up = False; s = ep; ep = l[i]; af = af0
            elif h[i] > ep:
                ep = h[i]; af = min(af + af0, afmax)
        else:
            s = max(s, h[i - 1], h[i - 2] if i > 1 else h[i - 1])
            if h[i] > s:
                up = True; s = ep; ep = h[i]; af = af0
            elif l[i] < ep:
                ep = l[i]; af = min(af + af0, afmax)
        sar[i] = s
    return sar


h1["sar"] = psar(h1["high"].to_numpy(), h1["low"].to_numpy())


def asof_1h(dec_ts, col):
    left = pd.DataFrame({"t": dec_ts})
    r = pd.merge_asof(left, h1[["end", col]].rename(columns={"end": "t"}), on="t", direction="backward")
    return r[col].to_numpy()


def asof_close_1h(dec_ts):
    return asof_1h(dec_ts, "close")


# ── olay setleri ──
def neutral_events():
    ts = pd.date_range("2021-06-02 00:00", "2026-10-19 20:00", freq="h", tz="UTC")
    dec = m_of(ts).to_numpy()
    atr = asof_1h(ts, "atr")
    ok = ~np.isnan(atr) & (g.nv[dec] < dec + 30)
    return dec[ok], atr[ok]


def momentum_events():
    m15 = pd.read_parquet(os.path.join(DATA, "btc_15m.parquet"), columns=["ts", "high", "low", "close"])
    hi, lo, cl = m15["high"], m15["low"], m15["close"]
    raw = 100 * (cl - lo.rolling(14).min()) / (hi.rolling(14).max() - lo.rolling(14).min())
    k = raw.rolling(3).mean()
    ema = cl.ewm(span=20, adjust=False).mean()
    atr15 = atr_wilder(hi.to_numpy(), lo.to_numpy(), cl.to_numpy())
    dist = (cl - ema) / atr15
    end = m15["ts"] + pd.Timedelta(minutes=15)
    sar = asof_1h(end, "sar"); c1h = asof_close_1h(end)
    cond = (k > 70) & (dist > 0.8) & pd.Series(sar < c1h)
    cond = cond.fillna(False).to_numpy()
    first = cond & ~np.concatenate([[False], cond[:-1]])
    t = end[first]
    t = t[(t >= pd.Timestamp("2021-06-02", tz="UTC")) & (t <= pd.Timestamp("2026-10-19 20:00", tz="UTC"))]
    dec = m_of(t).to_numpy()
    atr = asof_1h(t, "atr")
    ok = ~np.isnan(atr) & (g.nv[dec] < dec + 30)
    return dec[ok], atr[ok]


CACHEF = os.path.join(CACHE, "exits_sims.pkl")
if os.path.exists(CACHEF):
    S = pickle.load(open(CACHEF, "rb"))
else:
    S = {}
    dN, aN = neutral_events(); dM, aM = momentum_events()
    S["N_dec"], S["N_atr"], S["M_dec"], S["M_atr"] = dN, aN, dM, aM
    print("nötr olay", len(dN), "momentum olay", len(dM))
    for key, dec, atr, dirs in (("N", dN, aN, (("L", 1), ("S", -1))), ("M", dM, aM, (("L", 1),))):
        for dn, ds in dirs:
            t0 = time.time()
            r = simulate(g, dec, np.full(len(dec), ds), dec + H24, atr, VARS, spread="base")
            S[(key, dn, "base")] = {v.name: {kk: r[v.name][kk] for kk in ("R", "gain_bp", "hold", "nswap", "reason", "gapfill")} for v in VARS}
            S[(key, dn, "e")] = r["_e"]; S[(key, dn, "s")] = r["_s"]; S[(key, dn, "D")] = r["_D"]
            print(key, dn, "base", round(time.time() - t0, 1), "s")
            sub = [v for v in VARS if v.name in ("X1", "X3", "X4", "X5")] if key == "N" else VARS
            for mode in ("stress", "abs", "opt"):
                r = simulate(g, dec, np.full(len(dec), ds), dec + H24, atr, sub,
                             spread="base" if mode == "opt" else mode, optimistic=(mode == "opt"))
                S[(key, dn, mode)] = {v.name: {"R": r[v.name]["R"]} for v in sub}
            print(key, dn, "done", round(time.time() - t0, 1), "s")
    pickle.dump(S, open(CACHEF, "wb"))

OUT = {}
POSTP = ("OOS", "BLIND")


def pmask(per, p):
    if p == "POST":
        return (per == "OOS") | (per == "BLIND")
    if p == "ALL":
        return per != ""
    return per == p


# ── 1) varyant tablosu ──
tab = {}
for key, dn in (("N", "L"), ("N", "S"), ("M", "L")):
    dec = S[f"{key}_dec"]; per = period_of(dec); dk = day_key(dec)
    for v in VARS:
        o = S[(key, dn, "base")][v.name]
        for p in ("DISC", "OOS", "BLIND", "POST"):
            m = pmask(per, p)
            b = basic(o["R"][m], dk[m])
            b.update(hold_min=float(np.nanmean(o["hold"][m])), swap_share=float(np.nanmean(o["nswap"][m] > 0)),
                     gain_bp=float(np.nanmean(o["gain_bp"][m])), gapfill=float(np.mean(o["gapfill"][m])))
            tab[f"{key}-{dn}|{v.name}|{p}"] = b
OUT["varyantlar"] = tab

# ── 2) eşli karşılaştırmalar K1–K3 ──
COMP = [("K1", "X5", "X1"), ("K1", "X5", "X2"), ("K1", "X4", "X1"), ("K2", "X6", "X3"), ("K2", "X7", "X3"),
        ("K2", "X10", "X2"), ("K3", "X8", "X1"), ("K3", "X9", "X1")]
comp = {}
for key, dn in (("N", "L"), ("N", "S"), ("M", "L")):
    dec = S[f"{key}_dec"]; per = period_of(dec); dk = day_key(dec)
    for kname, a, b_ in COMP:
        d = S[(key, dn, "base")][a]["R"] - S[(key, dn, "base")][b_]["R"]
        row = {}
        for p in ("DISC", "OOS", "BLIND", "POST"):
            m = pmask(per, p) & ~np.isnan(d)
            P, lo, hi = boot_mean(d[m], dk[m])
            row[p] = dict(n=int(m.sum()), delta=float(d[m].mean()), P=P, lo=lo, hi=hi)
        m = pmask(per, "POST") & ~np.isnan(d)
        dd = d[m][np.argsort(dec[m])]; h = len(dd) // 2
        row["POST_h1"], row["POST_h2"] = float(dd[:h].mean()), float(dd[h:].mean())
        adopt = (row["DISC"]["delta"] > 0 and row["DISC"]["P"] >= 0.9 and row["OOS"]["delta"] > 0 and row["BLIND"]["delta"] > 0
                 and row["POST_h1"] >= 0 and row["POST_h2"] >= 0)
        reject = row["POST"]["delta"] < 0 and (1 - row["POST"]["P"]) >= 0.9
        row["verdict"] = "BENİMSE" if adopt else ("RED" if reject else "belirsiz")
        comp[f"{key}-{dn}|{kname}|{a}-{b_}"] = row
OUT["karsilastirma"] = comp

# ── 3) C02 VIXREG nötr filtre ──
macro = pd.read_parquet(os.path.join(DATA, "macro_daily.parquet")).sort_values("date")
macro["vix_f"] = macro["vix_close"].ffill()
dec = S["N_dec"]; dts = ts_of(dec)
vix = pd.merge_asof(pd.DataFrame({"t": dts}), macro[["avail_utc", "vix_f"]].rename(columns={"avail_utc": "t"}), on="t")["vix_f"].to_numpy()
per = period_of(dec); dk = day_key(dec); yrs = dts.year.to_numpy()
day_u, day_inv = np.unique(dk, return_inverse=True)
vix_day = np.full(len(day_u), np.nan)
vix_day[day_inv] = vix          # aynı gün içinde VIX değişebilir (22:30); gün etiketi = son değer → olay düzeyinde gerçek değer kullanılır
day_year = (day_u * 1440 // 1440)
c02 = {}
for vn in ("X4", "X5"):
    RL = S[("N", "L", "base")][vn]["R"]; RS = S[("N", "S", "base")][vn]["R"]
    def Rdir(lbl, mode="base"):
        if mode == "base":
            return np.where(lbl > 0, RL, RS)
        return np.where(lbl > 0, S[("N", "L", mode)][vn]["R"], S[("N", "S", mode)][vn]["R"])
    lbl = np.where(vix >= 18.4, 1, -1)
    R = Rdir(lbl)
    row = {}
    for p in ("DISC", "OOS", "BLIND", "POST"):
        m = pmask(per, p)
        b = basic(R[m], dk[m]); b["heplong"] = float(np.nanmean(RL[m])); b["karsit"] = float(np.nanmean(Rdir(-lbl)[m]))
        row[p] = b
    m = pmask(per, "POST")
    e = S[("N", "L", "e")]; hold = np.where(lbl > 0, S[("N", "L", "base")][vn]["hold"], S[("N", "S", "base")][vn]["hold"])
    keep = as_traded(e[m], e[m] + np.nan_to_num(hold[m]).astype(int))
    row["card_POST"] = card(R[m], Rdir(lbl, "stress")[m], Rdir(lbl, "opt")[m], dk[m], dec[m], keep)
    row["card_POST"]["abs15"] = float(np.nanmean(Rdir(lbl, "abs")[m]))
    # plasebo: yıl içinde günlük VIX değerleri karıştırılır (olaylar gün etiketini taşır)
    dvals = pd.Series(vix).groupby(dk).last()
    dyear = ts_of(dvals.index.to_numpy() * 1440).year.to_numpy()
    real = np.nanmean(R[m]); vals = []; tvals = []
    for _ in range(500):
        pv = within_year_perm(dvals.to_numpy(), dyear, RNG)
        vmap = pd.Series(pv, index=dvals.index).reindex(dk).to_numpy()
        lp = np.where(vmap >= 18.4, 1, -1)
        Rp = Rdir(lp)
        vals.append(np.nanmean(Rp[m]))
    row["placebo_pct"] = float((np.array(vals) < real).mean()); row["placebo_med"] = float(np.median(vals))
    row["p_post"] = p_one(row["card_POST"].get("t", np.nan))
    c02[vn] = row
# DISC seçim + max-z (2 hücre)
sel = max(c02, key=lambda k: c02[k]["DISC"]["meanR"])
dvals = pd.Series(vix).groupby(dk).last(); dyear = ts_of(dvals.index.to_numpy() * 1440).year.to_numpy()
disc = per == "DISC"
def tmax(lbl):
    return max(cluster_t(np.where(lbl > 0, S[("N", "L", "base")][vn]["R"], S[("N", "S", "base")][vn]["R"])[disc], dk[disc]) for vn in ("X4", "X5"))
real_t = tmax(np.where(vix >= 18.4, 1, -1)); cnt = 0
for _ in range(300):
    pv = within_year_perm(dvals.to_numpy(), dyear, RNG)
    vmap = pd.Series(pv, index=dvals.index).reindex(dk).to_numpy()
    cnt += tmax(np.where(vmap >= 18.4, 1, -1)) >= real_t
OUT["C02_VIXREG_notr"] = dict(cells=c02, selected=sel, maxz_disc_t=float(real_t), maxz_disc_psel=(cnt + 1) / 301)
print("C02 sel", sel, {p: round(c02[sel][p]["meanR"], 4) for p in ("DISC", "OOS", "BLIND", "POST")}, "card", c02[sel]["card_POST"]["passed"],
      "plc", c02[sel]["placebo_pct"])

# ── 4) swap ekonomisi ──
sw = {}
dec = S["N_dec"]; per = period_of(dec)
e = g.nv[dec]; ent = g.O[e]; s = SPREAD_BASE * ent
for Hh in (1, 4, 8, 24, 48, 72, 120, 240):
    x = g.nv[np.minimum(e + Hh * 60, g.N - 1)]
    okx = x < g.N - 1
    x = np.minimum(x, g.N - 1)
    ns = swaps_crossed(g, e, x)
    gl = ((g.O[x] - s / 2) - (ent + s / 2)) / ent * 1e4
    gs = ((ent - s / 2) - (g.O[x] + s / 2)) / ent * 1e4
    row = {}
    for p in ("DISC", "OOS", "BLIND", "ALL"):
        m = pmask(per, p) & okx & ~np.isnan(gl)
        swl = SWAP_LONG * ns[m] * 1e4; sws = SWAP_SHORT * ns[m] * 1e4
        row[p] = dict(long_gross_bp=float(gl[m].mean()), long_net_bp=float((gl[m] + swl).mean()), long_swap_bp=float(swl.mean()),
                      short_net_bp=float((gs[m] + sws).mean()), nights=float(ns[m].mean()),
                      sd_bp=float(gl[m].std()))
    sw[f"{Hh}h"] = row
OUT["swap"] = sw

# ── 5) hafta sonu ──
def weekend_mask(dec):
    t = ts_of(dec); wd = t.weekday.to_numpy()
    dstart = (dec // 1440) * 1440
    rday = g.roll[np.searchsorted(g.roll, dstart, side="left")]
    return (wd == 5) | (wd == 6) | ((wd == 4) & (dec >= rday))

wk = {}
for key, dn in (("N", "L"), ("N", "S"), ("M", "L")):
    dec = S[f"{key}_dec"]; per = period_of(dec); dk = day_key(dec); we = weekend_mask(dec)
    D = S[(key, dn, "D")]; s = S[(key, dn, "s")]; px = SPREAD_BASE and s / SPREAD_BASE
    row = {"n_weekend_share": float(we.mean()),
           "atr_pct_weekday": float(np.median(D[~we] / px[~we])) * 100, "atr_pct_weekend": float(np.median(D[we] / px[we])) * 100,
           "spread_over_SL_pct_weekday": float(np.median(s[~we] / D[~we])), "spread_over_SL_pct_weekend": float(np.median(s[we] / D[we])),
           "abs15_over_SL_weekday": float(np.median(15 / D[~we])), "abs15_over_SL_weekend": float(np.median(15 / D[we]))}
    for vn in ("X1", "X3", "X5"):
        R = S[(key, dn, "base")][vn]["R"]; gb = S[(key, dn, "base")][vn]["gain_bp"]
        for p in ("DISC", "OOS", "BLIND", "POST"):
            m = pmask(per, p) & ~np.isnan(R)
            a_ = basic(R[m & we], dk[m & we]); b_ = basic(R[m & ~we], dk[m & ~we])
            # Δ = hafta sonu − hafta içi; gün-blok bootstrap (iki grup ayrı günler)
            rng = np.random.default_rng(5)
            def bm(Rv, dv):
                u, inv = np.unique(dv, return_inverse=True); su = np.bincount(inv, weights=Rv); cn = np.bincount(inv).astype(float)
                pk = rng.integers(0, len(u), size=(2000, len(u))); return su[pk].sum(1) / cn[pk].sum(1)
            dlt = bm(R[m & we], dk[m & we]) - bm(R[m & ~we], dk[m & ~we])
            row[f"{vn}|{p}"] = dict(weekend=a_.get("meanR"), weekday=b_.get("meanR"), n_we=a_.get("n"), n_wd=b_.get("n"),
                                    delta=float(a_.get("meanR", np.nan) - b_.get("meanR", np.nan)), P_delta_neg=float((dlt < 0).mean()),
                                    we_bp=float(np.nanmean(gb[m & we])), wd_bp=float(np.nanmean(gb[m & ~we])),
                                    we_WR=a_.get("WR"), wd_WR=b_.get("WR"))
        gf = S[(key, dn, "base")][vn]["gapfill"]
        row[f"{vn}|gapfill_share"] = float(gf.mean())
    wk[f"{key}-{dn}"] = row

# kapalı pencere boşluk hareketi (Binance yolu)
cl = g.closed
starts = np.where(cl & ~np.concatenate([[False], cl[:-1]]))[0]
ends = np.where(cl & ~np.concatenate([cl[1:], [False]]))[0]
okse = (starts > 100) & (ends < g.N - 100)
starts, ends = starts[okse], ends[okse]
L_ = ends - starts + 1
Craw = pd.read_parquet(os.path.join(DATA, "btc_1m.parquet"), columns=["ts", "open", "close"])
mi = m_of(Craw["ts"]).to_numpy(); Cfull = np.full(g.N, np.nan); Ofull = np.full(g.N, np.nan)
Cfull[mi] = Craw["close"].to_numpy(); Ofull[mi] = Craw["open"].to_numpy()
bef = Cfull[starts - 1]; aft = Ofull[ends + 1]
mv = np.abs(np.log(aft / bef)) * 1e4
cb = Cfull[starts - 61]; ca = Ofull[ends + 1 - 60]
mv_ctrl = np.abs(np.log(ca / cb)) * 1e4
atr_at = asof_1h(ts_of(starts), "atr"); pxs = bef
mv_atr = mv / 1e4 * pxs / atr_at
gaps = {}
for lab, sel_ in (("gunluk_2dk", L_ == 2), ("cuma_6dk", L_ == 6)):
    ok = sel_ & ~np.isnan(mv)
    gaps[lab] = dict(n=int(ok.sum()), p50_bp=float(np.nanpercentile(mv[ok], 50)), p90_bp=float(np.nanpercentile(mv[ok], 90)),
                     p99_bp=float(np.nanpercentile(mv[ok], 99)), max_bp=float(np.nanmax(mv[ok])),
                     p99_atr=float(np.nanpercentile(mv_atr[ok], 99)), max_atr=float(np.nanmax(mv_atr[ok])),
                     ctrl_p50_bp=float(np.nanpercentile(mv_ctrl[ok], 50)), ctrl_p99_bp=float(np.nanpercentile(mv_ctrl[ok], 99)))
wk["kapali_pencere_hareket"] = gaps
# boşluk dolum maliyeti (SL'ler)
for key, dn in (("N", "L"), ("M", "L")):
    o = S[(key, dn, "base")]["X1"]; slm = o["reason"] == "SL"
    wk[f"{key}-{dn}|X1_SL_gapfill_share"] = float(o["gapfill"][slm].mean())
    wk[f"{key}-{dn}|X1_gap_extra_R_per_trade"] = float(np.nansum(np.where(o["gapfill"], -1 - o["R"], 0)) / len(o["R"]))
OUT["haftasonu"] = wk

# ── 6) lot / risk ölçeği (BLIND) ──
dec = S["N_dec"]; per = period_of(dec); D = S[("N", "L", "D")]; px = S[("N", "L", "s")] / SPREAD_BASE
m = per == "BLIND"
OUT["olcek"] = dict(atr1h_usd_median_BLIND=float(np.median(D[m])), atr1h_usd_p90_BLIND=float(np.percentile(D[m], 90)),
                    price_median_BLIND=float(np.median(px[m])), spread_usd_median=float(np.median(S[("N", "L", "s")][m])))

with open(os.path.join(RES, "exits.json"), "w") as fh:
    json.dump(OUT, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("yazıldı exits.json")
