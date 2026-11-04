"""C01, C03–C07: çapraz varlık rejimi → BTC yön kuralları (prereg §1)."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

g = load_grid()
RNG = np.random.default_rng(11)
NPERM = 500

# ── günlük BTC (UTC) ve dvol20 ──
d1 = pd.read_parquet(os.path.join(DATA, "btc_1d.parquet"), columns=["ts", "close"])
d1["r"] = np.log(d1["close"]).diff()
d1["dvol20"] = d1["r"].rolling(20).std()          # gün D'nin kapanışına kadar
dvol_by_day = pd.Series(d1["dvol20"].to_numpy(), index=d1["ts"].dt.normalize())

macro = pd.read_parquet(os.path.join(DATA, "macro_daily.parquet")).sort_values("date").reset_index(drop=True)


def dvol_known(ts_dec: pd.DatetimeIndex) -> np.ndarray:
    """Karar anında tamamlanmış son UTC gününün dvol20'si (= karar günü − 1)."""
    prev = (ts_dec.normalize() - pd.Timedelta(days=1))
    return dvol_by_day.reindex(prev).to_numpy()


# ── sunucu günü pencereleri: her takvim günü 22:30 UTC ──
days = pd.date_range("2021-06-22", "2026-10-19", freq="D", tz="UTC")
dec_ts = days + pd.Timedelta(hours=22, minutes=30)
dec = m_of(dec_ts).to_numpy()
xdec = next_roll(g, dec) - 2
dv = dvol_known(dec_ts)
ok = ~np.isnan(dv) & g.trad[np.minimum(g.nv[dec], g.N - 1)]
# dışlanan aralığa değen pencere (2023-03-24) — pencere içinde kalırsa yol zaten NaN; olayı koru ama giriş geçerli olmalı
dec, xdec, dv, dec_ts = dec[ok], xdec[ok], dv[ok], dec_ts[ok]
n = len(dec)
print("sunucu günü pencere:", n)

# makro merge_asof
mac = macro.copy()
for c in ["vix_close", "dxy_close", "us10y_close", "qqq_close"]:
    mac[c + "_f"] = mac[c].ffill()
left = pd.DataFrame({"t": dec_ts})
mj = pd.merge_asof(left, mac[["avail_utc", "date", "vix_close_f", "dxy_close_f", "us10y_close_f", "qqq_close_f"]].rename(columns={"avail_utc": "t"}),
                   on="t", direction="backward")
VIX = mj["vix_close_f"].to_numpy()
mdate = mj["date"].to_numpy()
new_row = (pd.to_datetime(mdate).normalize() == dec_ts.tz_localize(None).normalize())  # o gün yeni ABD kapanışı

# ABD günlük değişimler (makro tablosu üzerinde, ham satırlar)
def daily_change(col, kind):
    s = macro[col].copy()
    valid = s.notna()
    sv = s[valid]
    ch = np.log(sv / sv.shift(1)) if kind == "log" else sv.diff()
    sig = ch.rolling(20).std()
    out = pd.DataFrame({"date": macro.loc[valid, "date"], "ch": ch, "sig": sig})
    return out

chg = {}
for col, kind in [("qqq_close", "log"), ("dxy_close", "log"), ("us10y_close", "diff")]:
    chg[col] = daily_change(col, kind).set_index("date")

dates_naive = dec_ts.tz_localize(None).normalize()

def sig_for(col):
    c = chg[col].reindex(dates_naive)
    return c["ch"].to_numpy(), (c["ch"] / c["sig"]).to_numpy()

# ── simülasyonlar: her pencere için long/short × k∈{1,2} × maliyet modları ──
res = {}
for k in (1, 2):
    for mode in ("base", "stress", "abs", "opt"):
        for dname, dsign in (("L", 1), ("S", -1)):
            r = simulate(g, dec, np.full(n, dsign), xdec, k * dv, [Var("t")],
                         spread="base" if mode == "opt" else mode, optimistic=(mode == "opt"), risk_is_frac=True)
            res[(k, mode, dname)] = r["t"]
            if mode == "base":
                res[(k, "e", dname)] = r["_e"]
per = period_of(dec)
yrs = dec_ts.year.to_numpy()
dkey = day_key(dec)
wkend = np.isin(dec_ts.weekday, [5, 6])   # karar günü Cmt/Paz (UTC)


def R_of(k, mode, dirv):
    return np.where(dirv > 0, res[(k, mode, "L")]["R"], np.where(dirv < 0, res[(k, mode, "S")]["R"], np.nan))


def stats_cell(k, dirv, mask_extra=None):
    """dirv: +1/-1/0 (0 = işlem yok). Dönem bazında temel + OOS∪BLIND kartı."""
    act = dirv != 0
    if mask_extra is not None:
        act &= mask_extra
    dv_ = np.where(act, dirv, 0)
    R = R_of(k, "base", dv_)
    out = {}
    for p in ("DISC", "OOS", "BLIND", "POST", "ALL"):
        msk = (per == p) if p in ("DISC", "OOS", "BLIND") else ((per == "OOS") | (per == "BLIND")) if p == "POST" else (per != "")
        m = msk & act
        b = basic(R[m], dkey[m])
        b["base_long"] = float(np.nanmean(res[(k, "base", "L")]["R"][m])) if m.any() else np.nan
        b["base_rand"] = float(np.nanmean((res[(k, "base", "L")]["R"][m] + res[(k, "base", "S")]["R"][m]) / 2)) if m.any() else np.nan
        b["nBUY"] = int((dv_[m] > 0).sum())
        b["gain_bp"] = float(np.nanmean(np.where(dv_ > 0, res[(k, "base", "L")]["gain_bp"], res[(k, "base", "S")]["gain_bp"])[m])) if m.any() else np.nan
        out[p] = b
    m = ((per == "OOS") | (per == "BLIND")) & act
    c = card(R[m], R_of(k, "stress", dv_)[m], R_of(k, "opt", dv_)[m], dkey[m], dec[m], np.ones(m.sum(), bool))
    c["abs15"] = float(np.nanmean(R_of(k, "abs", dv_)[m]))
    out["card_POST"] = c
    for p in ("OOS", "BLIND"):
        mm = (per == p) & act
        out["card_" + p] = card(R[mm], R_of(k, "stress", dv_)[mm], R_of(k, "opt", dv_)[mm], dkey[mm], dec[mm], np.ones(mm.sum(), bool))
    return out


def perm_pct(k, make_dir, signal, elig, sel_mask_period, nperm=NPERM):
    """Yıl-içi permütasyon: sinyal değerleri elig günler arasında yıl içinde karıştırılır."""
    real = np.nanmean(R_of(k, "base", make_dir(signal))[sel_mask_period & (make_dir(signal) != 0)])
    vals = []
    idx = np.where(elig)[0]
    for _ in range(nperm):
        sp = signal.copy()
        sp[idx] = within_year_perm(signal[idx], yrs[idx], RNG)
        dv_ = make_dir(sp)
        m = sel_mask_period & (dv_ != 0)
        vals.append(np.nanmean(R_of(k, "base", dv_)[m]))
    vals = np.array(vals)
    return float((vals < real).mean()), float(np.median(vals))


def maxz(cells, signal, elig, nperm=300):
    """DISC ızgarasında max-t; cells: list of (k, make_dir)."""
    disc = per == "DISC"
    def tmax(sig):
        ts = []
        for k, f in cells:
            dv_ = f(sig); m = disc & (dv_ != 0)
            ts.append(cluster_t(R_of(k, "base", dv_)[m], dkey[m]))
        return np.nanmax(ts)
    real = tmax(signal)
    idx = np.where(elig)[0]; cnt = 0
    for _ in range(nperm):
        sp = signal.copy(); sp[idx] = within_year_perm(signal[idx], yrs[idx], RNG)
        cnt += tmax(sp) >= real
    return float(real), float((cnt + 1) / (nperm + 1))


OUT = {}
POST = (per == "OOS") | (per == "BLIND")

def run_hyp(name, cells, signal, elig, extra_info=None):
    """cells: dict cell_name -> (k, make_dir). Seçim DISC ortR."""
    tab = {}
    for cn, (k, f) in cells.items():
        tab[cn] = stats_cell(k, f(signal))
    sel = max(cells, key=lambda c: (tab[c]["DISC"].get("meanR", -9) if tab[c]["DISC"].get("n", 0) >= 30 else -9))
    k, f = cells[sel]
    pct, med = perm_pct(k, f, signal, elig, POST)
    tz, psel = maxz(list(cells.values()), signal, elig)
    OUT[name] = dict(cells=tab, selected=sel, placebo_pct=pct, placebo_median=med, maxz_disc_t=tz, maxz_disc_psel=psel,
                     p_post=p_one(tab[sel]["card_POST"].get("t", np.nan)), info=extra_info or {})
    c = tab[sel]["card_POST"]
    print(f"{name} sel={sel} DISC={tab[sel]['DISC'].get('meanR'):.4f} POST n={c.get('n')} R={c.get('meanR'):.4f} P={c.get('P'):.3f} "
          f"pass={c.get('passed')} plc={pct:.2f} BLIND={tab[sel]['BLIND'].get('meanR'):.4f} long={tab[sel]['POST']['base_long']:.4f}")


# C01 VIXREG
vix_dir = lambda v: np.where(np.isnan(v), 0, np.where(v >= 18.4, 1, -1))
run_hyp("C01_VIXREG_gunluk", {"k1": (1, vix_dir), "k2": (2, vix_dir)}, VIX.copy(), np.ones(n, bool))
# kollar + hafta içi/sonu (bilgi)
arms = {}
for k in (1, 2):
    for arm, f in (("BUYkolu", lambda v: np.where(v >= 18.4, 1, 0)), ("SELLkolu", lambda v: np.where(v < 18.4, -1, 0))):
        arms[f"k{k}_{arm}"] = stats_cell(k, f(VIX))
    arms[f"k{k}_haftaici"] = stats_cell(k, vix_dir(VIX), ~wkend)
    arms[f"k{k}_haftasonu"] = stats_cell(k, vix_dir(VIX), wkend)
    arms[f"k{k}_heplong"] = stats_cell(k, np.ones(n, int))
OUT["C01_kollar"] = arms
# yıllık işaret
yr_tab = {}
dv_ = vix_dir(VIX)
for y in np.unique(yrs):
    m = (yrs == y)
    yr_tab[int(y)] = dict(rule=float(np.nanmean(R_of(2, "base", dv_)[m])), long=float(np.nanmean(res[(2, "base", "L")]["R"][m])),
                         share_highvix=float((VIX[m] >= 18.4).mean()), btc_ret=float(np.nanmean(res[(2, "base", "L")]["gain_bp"][m])))
OUT["C01_yillik"] = yr_tab

# C03 QQQ günü
qr, qz = sig_for("qqq_close")
qz = np.where(new_row, qz, np.nan)
elig_q = ~np.isnan(qz)
def mk(theta, mode, sgn=1):
    def f(z):
        d = np.where(np.isnan(z) | (np.abs(z) <= theta), 0, np.sign(z) * sgn)
        if theta == 0:
            d = np.where(np.isnan(z) | (z == 0), 0, np.sign(z) * sgn)
        return (d * (1 if mode == "takip" else -1)).astype(int)
    return f
c03 = {f"th{th}_{md}": (2, mk(th, md)) for th in (0, 0.5, 1.0) for md in ("takip", "ters")}
run_hyp("C03_QQQ_gun", c03, qz.copy(), elig_q)

# C05 korelasyon koşullayıcı (C03 seçimi üzerine)
sel03 = OUT["C03_QQQ_gun"]["selected"]
# BTC NY 16:00 fiyatı her ABD işlem günü
tdays = macro.loc[macro["qqq_close"].notna(), "date"].reset_index(drop=True)
ny16 = pd.DatetimeIndex([pd.Timestamp(d.year, d.month, d.day, 16, 0, tzinfo=NY).tz_convert("UTC") for d in tdays])
mm16 = m_of(ny16).to_numpy()
okm = (mm16 >= 0) & (mm16 < g.N)
btc16 = np.full(len(mm16), np.nan)
btc16[okm] = g.O[g.nv[mm16[okm]]]
al = pd.DataFrame({"date": tdays, "btc": btc16, "qqq": macro.loc[macro["qqq_close"].notna(), "qqq_close"].to_numpy()})
al["rb"] = np.log(al["btc"]).diff(); al["rq"] = np.log(al["qqq"]).diff()
al["rho60"] = al["rb"].rolling(60).corr(al["rq"])
rho = al.set_index("date")["rho60"].reindex(dates_naive).to_numpy()
rho = np.where(new_row, rho, np.nan)
k03, f03 = c03[sel03]
c05 = {}
for cth in (0.2, 0.4):
    c05[f"rho>{cth}"] = (2, (lambda cth: (lambda z: np.where(rho > cth, f03(z), 0)))(cth))
run_hyp("C05_QQQ_korelasyon", c05, qz.copy(), elig_q, {"base_cell": sel03})
OUT["C05_tamamlayici"] = {f"rho<={cth}": stats_cell(2, np.where(rho <= cth, f03(qz), 0)) for cth in (0.2, 0.4)}
OUT["C05_rho_dagilim"] = {p: dict(median=float(np.nanmedian(rho[per == p])), share_gt04=float(np.nanmean(rho[per == p] > 0.4)))
                          for p in ("DISC", "OOS", "BLIND")}

# C06 DXY, C07 US10Y (a priori ters yön)
for name, col in (("C06_DXY", "dxy_close"), ("C07_US10Y", "us10y_close")):
    ch, z = sig_for(col)
    z = np.where(new_row, z, np.nan)
    cells = {f"th{th}_ters": (2, mk(th, "ters")) for th in (0, 0.5)}
    run_hyp(name, cells, z.copy(), ~np.isnan(z))
    OUT[name]["bilgi_takip_mod"] = {f"th{th}_takip": stats_cell(2, mk(th, "takip")(z)) for th in (0, 0.5)}

# ── C04: QQQ açılış boşluğu, 10:00 ET → aynı gün rollover−2 ──
mq = macro.loc[macro["qqq_close"].notna() & macro["qqq_open"].notna()].reset_index(drop=True)
prev_close = macro["qqq_close"].ffill().shift(1)
mq_prev = prev_close.loc[macro["qqq_close"].notna() & macro["qqq_open"].notna()].to_numpy()
gap = np.log(mq["qqq_open"].to_numpy() / mq_prev)
rq = np.log(macro["qqq_close"].ffill()).diff()
sig_prev = rq.rolling(20).std().shift(1).loc[macro["qqq_close"].notna() & macro["qqq_open"].notna()].to_numpy()  # D−1'e kadar
gz = gap / sig_prev
t10 = pd.DatetimeIndex([pd.Timestamp(d.year, d.month, d.day, 10, 0, tzinfo=NY).tz_convert("UTC") for d in mq["date"]])
dec4 = m_of(t10).to_numpy()
keep4 = (dec4 > 30 * 1440) & (dec4 < m_of(pd.Timestamp("2026-10-20 12:00", tz="UTC")))
dec4, gz, t10 = dec4[keep4], gz[keep4], t10[keep4]
x4 = next_roll(g, dec4) - 2
dv4 = dvol_known(t10)
ok4 = ~np.isnan(dv4) & ~np.isnan(gz)
dec4, gz, t10, x4, dv4 = dec4[ok4], gz[ok4], t10[ok4], x4[ok4], dv4[ok4]
n4 = len(dec4)
res4 = {}
for mode in ("base", "stress", "abs", "opt"):
    for dname, dsign in (("L", 1), ("S", -1)):
        res4[(1, mode, dname)] = simulate(g, dec4, np.full(n4, dsign), x4, dv4, [Var("t")],
                                          spread="base" if mode == "opt" else mode, optimistic=(mode == "opt"), risk_is_frac=True)["t"]
# geçici olarak global'leri C04'e çevir
_saved = (res, per, yrs, dkey, dec, POST, n)
res, per, yrs, dkey, dec = res4, period_of(dec4), t10.year.to_numpy(), day_key(dec4), dec4
POST = (per == "OOS") | (per == "BLIND"); n = n4
c04 = {f"th{th}_{md}": (1, mk(th, md)) for th in (0, 0.5) for md in ("takip", "ters")}
run_hyp("C04_QQQ_bosluk", c04, gz.copy(), np.ones(n4, bool), {"pencere": "10:00 ET → 16:58 ET", "n_gun": int(n4)})
res, per, yrs, dkey, dec, POST, n = _saved

# Holm (7 hipotezden 6'sı burada; C02 20_exits'te) → özet betiğinde
with open(os.path.join(RES, "regime.json"), "w") as fh:
    json.dump(OUT, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("yazıldı", os.path.join(RES, "regime.json"))
