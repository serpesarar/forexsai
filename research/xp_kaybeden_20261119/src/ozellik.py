"""ozellik.py — K1 + XP işlemlerinin giriş anı (16:00 NY) yeni özellik aileleri. Yalnız 16:00'dan önce kapanmış 30 dk mumlar.

Aileler: G (30 dk/1 sa gösterge), U (uyumsuzluk), H (tik hacmi), F (formasyon), S (destek/direnç), T (trend kanalı),
D (düşüş yapısı), X (piyasalar arası). python ozellik.py test | kos
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/son_rapor_20261118/src"))
sys.path.insert(0, str(ROOT / "research/ndx_tf_yapilandirma_20261117/src"))
import rapor as R  # noqa: E402
import kaynak  # noqa: E402

G, NY = R.G, R.NY
HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "results"
TR = ROOT / "research/xp_gelistir_20261119/results/islemler.parquet"
MARKETS = ["NAS100", "US500", "US30", "US2000"]
LAST_MN = 930          # 15:30 mumu 16:00'da kapanır
SESS = (570, 960)


# ---------- göstergeler (nedensel, tüm seri) ----------
def rsi(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 * up / (up + dn).replace(0, np.nan)


def indicators(b: pd.DataFrame, pre: str) -> pd.DataFrame:
    c, h, l = b.c, b.h, b.l
    out = pd.DataFrame(index=b.index)
    out[pre + "rsi14"] = rsi(c, 14)
    out[pre + "rsi2"] = rsi(c, 2)
    lo14, hi14 = l.rolling(14).min(), h.rolling(14).max()
    out[pre + "stoch14"] = (c - lo14) / (hi14 - lo14) * 100
    tp = (h + l + c) / 3
    sma = tp.rolling(20).mean()
    mad = tp.rolling(20).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    out[pre + "cci20"] = (tp - sma) / (0.015 * mad)
    e12, e26 = c.ewm(span=12, adjust=False).mean(), c.ewm(span=26, adjust=False).mean()
    macd = e12 - e26
    hist = macd - macd.ewm(span=9, adjust=False).mean()
    out[pre + "macd_hist"] = hist / c * 1e4
    out[pre + "macd_hist_egim"] = hist.diff() / c * 1e4
    m20, s20 = c.rolling(20).mean(), c.rolling(20).std()
    out[pre + "bb_pctb"] = (c - (m20 - 2 * s20)) / (4 * s20)
    out[pre + "bb_gen"] = 4 * s20 / m20 * 1e4
    trng = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = trng.ewm(alpha=1 / 14, adjust=False).mean()
    out[pre + "atr_bp"] = atr / c * 1e4
    upm, dnm = h.diff(), -l.diff()
    pdm = np.where((upm > dnm) & (upm > 0), upm, 0.0)
    ndm = np.where((dnm > upm) & (dnm > 0), dnm, 0.0)
    pdi = 100 * pd.Series(pdm, index=b.index).ewm(alpha=1 / 14, adjust=False).mean() / atr
    ndi = 100 * pd.Series(ndm, index=b.index).ewm(alpha=1 / 14, adjust=False).mean() / atr
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi)
    out[pre + "adx14"] = dx.ewm(alpha=1 / 14, adjust=False).mean()
    out[pre + "di_fark"] = pdi - ndi
    emas = {n: c.ewm(span=n, adjust=False).mean() for n in (9, 21, 50, 200)}
    for n, e in emas.items():
        out[pre + f"ema{n}_uz"] = (c / e - 1) * 1e4
    out[pre + "ema_ayi_dizilim"] = ((c < emas[9]).astype(int) + (emas[9] < emas[21]).astype(int) + (emas[21] < emas[50]).astype(int)
                                    + (emas[50] < emas[200]).astype(int))
    out[pre + "ema9_egim"] = emas[9].pct_change(3) * 1e4
    if "v" in b.columns and b.v.notna().any():
        mf = tp * b.v
        pos = mf.where(tp > tp.shift(), 0.0).rolling(14).sum()
        neg = mf.where(tp < tp.shift(), 0.0).rolling(14).sum()
        out[pre + "mfi14"] = 100 - 100 / (1 + pos / neg.replace(0, np.nan))
    out[pre + "_rsi_raw"] = out[pre + "rsi14"]
    out[pre + "_macd_raw"] = hist
    return out


def divergence(l: np.ndarray, osc: np.ndarray, k: int, rec: int, back: int) -> tuple[float, float]:
    """Son `rec` mumun dibi vs önceki `back` mumun dibi: fiyat farkı (bp) ve osilatör farkı (dipteki değerler)."""
    a0, a1 = k - rec + 1, k + 1
    b0, b1 = k - rec - back + 1, k - rec + 1
    if b0 < 0:
        return np.nan, np.nan
    i1 = a0 + int(np.argmin(l[a0:a1]))
    i2 = b0 + int(np.argmin(l[b0:b1]))
    return (l[i1] / l[i2] - 1) * 1e4, osc[i1] - osc[i2]


def linreg(y: np.ndarray) -> tuple[float, float, float]:
    """Eğim (bp/adım, son değere göre), R², son noktanın kanal z'si."""
    y = np.asarray(y, float)
    if len(y) < 5 or not np.all(np.isfinite(y)):
        return np.nan, np.nan, np.nan
    x = np.arange(len(y))
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    fit = A @ coef
    res = y - fit
    sd = res.std(ddof=2) if len(y) > 2 else np.nan
    r2 = 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return coef[0] / y[-1] * 1e4, r2, res[-1] / sd if sd > 0 else np.nan


# ---------- piyasa başına özellik tablosu ----------
def load_market(s: str) -> pd.DataFrame:
    since = "2018-06-01" if s == "US500" else None
    x = pd.read_csv(ROOT / f"research/c1_turev_20261105/data/mt5/{s}_M30.csv.gz")
    b = R.KD.mt5_m30(s, since)
    tv = pd.Series(x.v.values, index=kaynak.server_to_utc(x["t"].to_numpy()).astype(np.int64))
    tv = tv[~tv.index.duplicated()]
    b["v"] = tv.reindex(b.t.values).values
    return b.reset_index(drop=True)


def duka_30m() -> pd.DataFrame:
    b = G.ndx_bars()
    g = b.assign(k=(b.t // 1800) * 1800).groupby("k")
    return pd.DataFrame({"t": g.t.first().index.values, "o": g.o.first().values, "h": g.h.max().values,
                         "l": g.l.min().values, "c": g.c.last().values})


def market_features(b: pd.DataFrame, dates: list[pd.Timestamp]) -> pd.DataFrame:
    b = b.copy()
    b["t"] = (b.t // 1800) * 1800
    x = G._local(b, NY)
    b["day"] = pd.to_datetime(x.day.values)
    b["mn"] = x.mn.values
    ind30 = indicators(b, "m30_")
    hb = b.assign(hk=(b.t // 3600) * 3600).groupby("hk").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"),
                                                              v=("v", "sum") if "v" in b.columns else ("c", "size"))
    if "v" not in b.columns:
        hb = hb.drop(columns="v")
    ind1h = indicators(hb.reset_index(drop=True), "h1_")
    ind1h.index = hb.index
    has_v = "v" in b.columns and b.v.notna().mean() > 0.5
    sess = b[(b.mn >= SESS[0]) & (b.mn < SESS[1])]
    gs = sess.groupby("day")
    daily = pd.DataFrame({"p": b[b.mn == LAST_MN].set_index("day").c, "o930": gs.o.first(), "s_hi": gs.h.max(), "s_lo": gs.l.min()})
    allday = b.groupby("day").agg(lo=("l", "min"), hi=("h", "max"))
    daily = daily.join(allday)
    if has_v:
        daily["svol"] = gs.v.sum()
        daily["lhvol"] = sess[sess.mn >= 900].groupby("day").v.sum()
    daily = daily.dropna(subset=["p"])
    days = list(daily.index)
    pos = {d: i for i, d in enumerate(days)}
    l_arr, c_arr, o_arr, h_arr = b.l.values, b.c.values, b.o.values, b.h.values
    rsi30, macd30 = ind30["m30__rsi_raw"].values, ind30["m30__macd_raw"].values
    hl, hr, hm = hb.l.values, ind1h["h1__rsi_raw"].values, ind1h["h1__macd_raw"].values
    hc = hb.c.values
    key = pd.Series(np.arange(len(b)), index=list(zip(b.day, b.mn)))
    key = key[~key.index.duplicated()]
    hpos = pd.Series(np.arange(len(hb)), index=hb.index)
    rows = []
    for d in dates:
        d = pd.Timestamp(d)
        if d not in pos or (d, LAST_MN) not in key.index:
            continue
        k, i = int(key[(d, LAST_MN)]), pos[d]
        p = daily.p.iloc[i]
        r = {"d": d}
        for col in ind30.columns:
            if not col.startswith("m30__"):
                r[col] = ind30[col].iloc[k]
        hk = (int(b.t.iloc[k]) // 3600) * 3600          # 15:00 saatlik mum (16:00'da kapanır)
        if hk in hpos.index:
            j = int(hpos[hk])
            for col in ind1h.columns:
                if not col.startswith("h1__") and col in ("h1_rsi14", "h1_macd_hist", "h1_stoch14", "h1_adx14", "h1_ema50_uz", "h1_ema200_uz", "h1_bb_pctb", "h1_ema_ayi_dizilim"):
                    r[col] = ind1h[col].iloc[j]
            r["U_h1_fiyat_dd"], r["U_h1_rsi_fark"] = divergence(hl, hr, j, 5, 25)
            _, r["U_h1_macd_fark"] = divergence(hl, hm / hc * 1e4, j, 5, 25)
            r["T_1sa_egim"], r["T_1sa_r2"], r["T_1sa_z"] = linreg(hc[max(0, j - 79):j + 1])
        # uyumsuzluk 30 dk
        r["U_m30_fiyat_dd"], r["U_m30_rsi_fark"] = divergence(l_arr, rsi30, k, 6, 20)
        _, r["U_m30_macd_fark"] = divergence(l_arr, macd30 / c_arr * 1e4, k, 6, 20)
        r["U_m30_boga_uyumsuz"] = float(r["U_m30_fiyat_dd"] < 0 and r["U_m30_rsi_fark"] > 0) if np.isfinite(r["U_m30_fiyat_dd"]) else np.nan
        # seans mumları
        sk = np.flatnonzero((b.day.values == np.datetime64(d)) & (b.mn.values >= SESS[0]) & (b.mn.values < SESS[1]))
        so, sh, sl, sc = o_arr[sk], h_arr[sk], l_arr[sk], c_arr[sk]
        red = sc < so
        # formasyon
        rng = h_arr[k] - l_arr[k]
        if rng > 0:
            r["F_son30_govde"] = (c_arr[k] - o_arr[k]) / rng
            r["F_son30_altfitil"] = (min(o_arr[k], c_arr[k]) - l_arr[k]) / rng
            r["F_son30_ustfitil"] = (h_arr[k] - max(o_arr[k], c_arr[k])) / rng
            r["F_son30_konum"] = (c_arr[k] - l_arr[k]) / rng
        r["F_son30_aralik_atr"] = rng / c_arr[k] * 1e4 / r["m30_atr_bp"] if r.get("m30_atr_bp") else np.nan
        streak = 0
        for q in range(k, max(-1, k - 30), -1):
            if c_arr[q] < o_arr[q]:
                streak += 1
            else:
                break
        r["F_kirmizi_seri"] = streak
        r["F_cekic"] = float(r.get("F_son30_altfitil", 0) >= 0.5 and r.get("F_son30_konum", 0) >= 0.6)
        r["F_yutan_boga"] = float(c_arr[k] > o_arr[k] and c_arr[k - 1] < o_arr[k - 1] and c_arr[k] >= o_arr[k - 1] and o_arr[k] <= c_arr[k - 1])
        r["F_ic_mum"] = float(h_arr[k] <= h_arr[k - 1] and l_arr[k] >= l_arr[k - 1])
        # düşüş yapısı
        if len(sk) >= 6:
            ihi, ilo = int(np.argmax(sh)), int(np.argmin(sl))
            r["D_tepeden_dusus"] = (p / sh.max() - 1) * 1e4
            r["D_tepe_dip_mum"] = ilo - ihi
            body_drop = np.where(red, so - sc, 0.0)
            tot = max(so[0] - p, 1e-9)
            r["D_en_buyuk_mum_payi"] = body_drop.max() / tot if so[0] > p else np.nan
            r["D_kirmizi_pay"] = red.mean()
            r["D_dipten_sekme"] = (p / sl.min() - 1) * 1e4
            noon = np.flatnonzero(b.mn.values[sk] <= 720)
            r["D_sabah_payi"] = (so[0] - sc[noon[-1]]) / tot if (len(noon) and so[0] > p) else np.nan
            i14 = np.flatnonzero(b.mn.values[sk] == 840)
            r["D_son2saat"] = (p / so[i14[0]] - 1) * 1e4 if len(i14) else np.nan
            T = linreg(sc)
            r["T_seans_egim"], r["T_seans_r2"], r["T_seans_z"] = T
        # önceki günler: destek/direnç + kanal + seri
        prev = daily.iloc[max(0, i - 250):i]
        if len(prev) >= 20:
            for n in (5, 20, 60, 250):
                if len(prev) >= n:
                    r[f"S_d{n}dip_uz"] = (p / prev.lo.iloc[-n:].min() - 1) * 1e4
            r["S_d20tepe_uz"] = (p / prev.hi.iloc[-20:].max() - 1) * 1e4
            r["S_dunku_dip_uz"] = (p / prev.lo.iloc[-1] - 1) * 1e4
            lows20 = prev.lo.iloc[-20:].values
            above = lows20[lows20 > p]
            below = lows20[lows20 < p]
            r["S_ustte_kirik_destek_uz"] = (above.min() / p - 1) * 1e4 if len(above) else 0.0
            r["S_kirik_destek_say"] = float(len(above))
            r["S_alttaki_destek_uz"] = (p / below.max() - 1) * 1e4 if len(below) else np.nan
            r["S_yakin_dip_kumesi"] = float(np.sum(np.abs(lows20 / p - 1) * 1e4 <= 50))
            pc = prev.p.values
            for n in (20, 60):
                if len(pc) >= n:
                    y = np.append(pc[-n:], p)
                    r[f"T_g{n}_egim"], r[f"T_g{n}_r2"], r[f"T_g{n}_z"] = linreg(y)
            dd = 0
            for q in range(len(pc) - 1, 0, -1):
                if pc[q] < pc[q - 1]:
                    dd += 1
                else:
                    break
            r["D_dusen_gun_seri"] = dd + (1 if p < pc[-1] else 0)
            r["D_ret3"] = (p / pc[-3] - 1) * 1e4
        # hacim
        if has_v and np.isfinite(daily.svol.iloc[i]):
            sv, lhv = daily.svol.values, daily.lhvol.values
            a20 = np.nanmean(sv[max(0, i - 20):i]) if i >= 5 else np.nan
            l20 = np.nanmean(lhv[max(0, i - 20):i]) if i >= 5 else np.nan
            sv_ = b.v.values[sk]
            r["H_gun_oran"] = sv[i] / a20
            r["H_dun_oran"] = sv[i - 1] / a20 if i >= 1 else np.nan
            r["H_son_saat_payi"] = lhv[i] / sv[i] if sv[i] > 0 else np.nan
            r["H_son_saat_oran"] = lhv[i] / l20
            gv, rv = sv_[~red].sum(), sv_[red].sum()
            r["H_kirmizi_yesil_log"] = np.log((rv + 1) / (gv + 1))
            mbar = sv_.mean()
            r["H_maks_mum_oran"] = sv_.max() / mbar if mbar > 0 else np.nan
            r["H_dip_mum_oran"] = sv_[int(np.argmin(sl))] / mbar if mbar > 0 else np.nan
            r["H_son_mum_oran"] = sv_[-1] / mbar if mbar > 0 else np.nan
            r["H_trend"] = pd.Series(sv_).corr(pd.Series(np.arange(len(sv_))), method="spearman") if len(sv_) > 4 else np.nan
            ihi, ilo = int(np.argmax(sh)), int(np.argmin(sl))
            if ilo > ihi:
                r["H_dusus_bacagi_oran"] = sv_[ihi:ilo + 1].mean() / mbar
            tpv = (sh + sl + sc) / 3
            r["H_vwap_uz"] = (p / ((tpv * sv_).sum() / sv_.sum()) - 1) * 1e4 if sv_.sum() > 0 else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def cross_market(all_days: dict[str, pd.Series]) -> pd.DataFrame:
    """Aynı gün piyasaların seans getirisi (09:30→16:00): göreli zayıflık ve yayılım."""
    S = pd.DataFrame(all_days)
    out = {}
    for m in S.columns:
        others = S.drop(columns=m)
        out[m] = pd.DataFrame({"X_goreli_zayiflik": S[m] - others.mean(axis=1), "X_yayilim": S.std(axis=1),
                               "X_ndx_eksi_rut": S.get("NAS100") - S.get("US2000")})
    return out


def session_ret(b: pd.DataFrame) -> pd.Series:
    x = G._local(b.assign(t=(b.t // 1800) * 1800), NY)
    z = b.assign(day=pd.to_datetime(x.day.values), mn=x.mn.values)
    o = z[z.mn == SESS[0]].set_index("day").o
    c = z[z.mn == LAST_MN].set_index("day").c
    o, c = o[~o.index.duplicated()], c[~c.index.duplicated()]
    return (c / o - 1) * 1e4


def unit_tests() -> None:
    s, r2, z = linreg(np.array([1.0, 2, 3, 4, 5, 6]))
    assert abs(r2 - 1) < 1e-9 and abs(s - 1 / 6 * 1e4) < 1e-6
    l = np.array([10, 9, 8, 9, 10, 11, 10, 9, 8.5, 9.0])
    osc = np.array([50, 40, 20, 40, 60, 70, 50, 40, 35, 45.0])
    pdd, od = divergence(l, osc, 9, 3, 6)                     # son dip 8.5 (osc 35) vs önceki 8 (osc 20)
    assert pdd > 0 and od == 15
    c = pd.Series(np.r_[np.linspace(100, 110, 30), np.linspace(110, 100, 30)])
    rr = rsi(c, 14)
    assert rr.iloc[29] > 90 and rr.iloc[-1] < 15
    print("birim testleri geçti")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    D = pd.read_parquet(TR)
    bars = {s: load_market(s) for s in MARKETS}
    sret = {s: session_ret(b) for s, b in bars.items()}
    X = cross_market(sret)
    k1 = D.assign(m=D.besleme.str.replace("MT5_", "").str.replace("DUKA_NDX", "NAS100")).groupby("d").m.nunique()
    parts = []
    for s in MARKETS + ["DUKA_NDX"]:
        feed = f"MT5_{s}" if s != "DUKA_NDX" else s
        dates = D[D.besleme == feed].d.tolist()
        b = bars[s] if s != "DUKA_NDX" else duka_30m()
        f = market_features(b, dates)
        xm = X["NAS100" if s == "DUKA_NDX" else s]
        f = f.join(xm, on="d")
        f["X_k1_genislik"] = f.d.map(k1).values
        if s == "DUKA_NDX":                                 # hacim: aynı günün NAS100 değerleri
            nas = market_features(bars["NAS100"], dates)
            hcols = [c for c in nas.columns if c.startswith("H_") or c == "m30_mfi14"]
            f = f.drop(columns=[c for c in hcols if c in f.columns]).merge(nas[["d"] + hcols], on="d", how="left")
        f["besleme"] = feed
        parts.append(f)
        print(feed, len(f), "/", len(dates), flush=True)
    F = pd.concat(parts, ignore_index=True)
    M = D.merge(F, on=["besleme", "d"], how="inner")
    M.to_parquet(OUT / "ozellikler.parquet")
    print("tablo", M.shape)


if __name__ == "__main__":
    unit_tests() if sys.argv[1] == "test" else (unit_tests(), main())
