"""NOM — özellik paketi (eğitim ve canlı servis için TEK kod yolu).

`compute_features(b1, t_dec, macro, calendar)`:
  b1     : 1m barlar (t=açılış UTC epoch sn, open/high/low/close — BID), artan, kapalı saatler yok
  t_dec  : karar anları (epoch sn); her biri bir 1m bar KAPANIŞI. Yalnız açılışı < t_dec olan barlar kullanılır.
  macro  : günlük makro (data/macro/macro_daily.parquet şeması) veya None
  calendar: olay takvimi (ts_utc, event) veya None
Dönen: DataFrame (satır = karar anı), sütunlar FEATURE_COLUMNS + yardımcılar ('_price', '_atr_M5', ...).

Sızıntı kilitleri:
  * HTF göstergeleri HTF barı üzerinde hesaplanır, `end <= t_dec` ile eşlenir (bars.asof_map).
  * Fraktal pivot k bar sonra teyit edilir; teyit zamanı = (j+k). barın `end`'i.
  * Makro d günü değeri yalnız d 17:15 ET sonrasında görünür (E20/E99).
  * Gün-içi kümülatif (seans açılışı, gece yüksek/düşük, TWAP) yalnız kapanmış 1m barlarla.
Tüm uzaklıklar fiyat değil ATR(H1) birimi → Dukascopy ↔ Pepperstone seviye farkından bağımsız.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from . import bars as B
from . import nyse_calendar as CAL

NY = 'America/New_York'
MACRO_AVAILABLE_ET = (17, 15)
PIVOT_K = {'M15': 3, 'H1': 3, 'D1': 2}
PIVOT_LOOKBACK_S = {'M15': 5 * 86400, 'H1': 20 * 86400, 'D1': 60 * 86400}
PIVOT_LAST_N = 48
LEVEL_TOL_ATR = 0.3
VIX_REGIME = 18.4
EVENT_CAP_MIN = 3 * 1440
EVENT_CLASSES = ('FOMC', 'CPI', 'NFP', 'EARN')
SESSION_PHASES = {0: 'asya', 1: 'londra', 2: 'ny_acilis', 3: 'ny_ogle', 4: 'ny_kapanis', 5: 'kapanis_sonrasi'}
LIVE_HISTORY_DAYS = 240         # canlıda istenecek 1m geçmişi (takvim günü); 75 gün D1 özelliklerini %6-20 saptırdı (Faz 2)


# ───────────────────────────────── HTF gösterge tabloları ─────────────────────────────────

def _tf_table(b: pd.DataFrame, tf: str) -> pd.DataFrame:
    a = B.atr(b, 14)
    f = pd.DataFrame(index=b.index)
    f['atr'] = a
    f['atr_ratio'] = a / a.rolling({'M5': 288 * 5, 'M15': 96 * 5, 'H1': 23 * 20, 'H4': 6 * 20, 'D1': 20}[tf],
                                   min_periods=10).median()
    f['rsi14'] = B.rsi(b.c, 14)
    f['rsi14_slope3'] = f.rsi14 - f.rsi14.shift(3)
    if tf in ('M15', 'H1'):
        f['rsi7'] = B.rsi(b.c, 7)
        f['rsi21'] = B.rsi(b.c, 21)
        hh = b.c >= b.c.rolling(20, min_periods=20).max()
        ll = b.c <= b.c.rolling(20, min_periods=20).min()
        f['div_bear'] = (hh & (f.rsi14 < f.rsi14.rolling(20, min_periods=20).max() - 5)).astype(float)
        f['div_bull'] = (ll & (f.rsi14 > f.rsi14.rolling(20, min_periods=20).min() + 5)).astype(float)
        m = B.ema(b.c, 12) - B.ema(b.c, 26)
        f['macd_hist_atr'] = (m - B.ema(m, 9)) / a
        lo14, hi14 = b.l.rolling(14).min(), b.h.rolling(14).max()
        f['stoch_k'] = (100 * (b.c - lo14) / (hi14 - lo14).replace(0, np.nan)).rolling(3).mean()
        f['adx14'] = B.adx(b, 14)
        ch = (b.c - b.c.shift(20)).abs()
        f['er20'] = ch / b.c.diff().abs().rolling(20).sum().replace(0, np.nan)
        mid, sd = b.c.rolling(20).mean(), b.c.rolling(20).std()
        f['bb_width_atr'] = 4 * sd / a
        f['bb_pctb'] = (b.c - (mid - 2 * sd)) / (4 * sd).replace(0, np.nan)
        f['bb_squeeze'] = f.bb_width_atr / f.bb_width_atr.rolling(120, min_periods=20).median()
        for n in (20, 50, 200):
            e = B.ema(b.c, n)
            f[f'ema{n}_dist'] = (b.c - e) / a
            f[f'ema{n}_slope'] = (e - e.shift(10)) / a
        e20, e50, e200 = B.ema(b.c, 20), B.ema(b.c, 50), B.ema(b.c, 200)
        f['ema_stack'] = np.sign(e20 - e50) + np.sign(e50 - e200)
        f['roc4_atr'] = (b.c - b.c.shift(4)) / a
    if tf == 'M5':
        f['roc3_atr'] = (b.c - b.c.shift(3)) / a
        f['roc12_atr'] = (b.c - b.c.shift(12)) / a
    if tf == 'H1':
        ps = B.psar(b)
        f['psar_dir'] = ps[:, 0]
        f['psar_dist_atr'] = (b.c.to_numpy() - ps[:, 1]) / a
    if tf == 'D1':
        e20 = B.ema(b.c, 20)
        f['ema20_dist'] = (b.c - e20) / a
        f['adr20'] = (b.h - b.l).rolling(20, min_periods=5).mean()
        f['ret1'] = b.c.pct_change(fill_method=None)
        f['ret5'] = b.c.pct_change(5, fill_method=None)
        f['hi20'] = b.h.rolling(20, min_periods=5).max()
        f['lo20'] = b.l.rolling(20, min_periods=5).min()
        f['c'] = b.c
        f['h'] = b.h
        f['l'] = b.l
    return f


def _pivots(b: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Fraktal pivotlar: (teyit zamanı, pivot barı zamanı, seviye, tip +1 tepe / −1 dip)."""
    k = PIVOT_K[tf]
    w = 2 * k + 1
    ph = b.h == b.h.rolling(w, center=True, min_periods=w).max()
    pl = b.l == b.l.rolling(w, center=True, min_periods=w).min()
    conf_end = b.end.shift(-k)
    rows = []
    for mask, lvl, typ in ((ph, b.h, 1.0), (pl, b.l, -1.0)):
        sel = mask & conf_end.notna()
        rows.append(pd.DataFrame({'conf': conf_end[sel].astype('int64'), 'tbar': b.end[sel].astype('int64'),
                                  'lvl': lvl[sel].astype(float), 'typ': typ}))
    p = pd.concat(rows).sort_values(['conf', 'tbar']).reset_index(drop=True)
    return p


def _pivot_matrix(p: pd.DataFrame, t_dec: np.ndarray, lookback_s: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Her karar için teyitli son PIVOT_LAST_N pivot: seviye, tip, pivot zamanı [N, P] (NaN = yok)."""
    e = np.searchsorted(p.conf.to_numpy(), t_dec, side='right')
    P = PIVOT_LAST_N
    idx = e[:, None] - P + np.arange(P)[None, :]
    ok = idx >= 0
    idc = np.clip(idx, 0, max(len(p) - 1, 0))
    if len(p) == 0:
        nan = np.full(idx.shape, np.nan)
        return nan, nan, nan
    lv = np.where(ok, p.lvl.to_numpy()[idc], np.nan)
    ty = np.where(ok, p.typ.to_numpy()[idc], np.nan)
    tb = np.where(ok, p.tbar.to_numpy()[idc].astype(float), np.nan)
    old = tb < (t_dec[:, None] - lookback_s)
    lv[old] = np.nan
    ty[old] = np.nan
    tb[old] = np.nan
    return lv, ty, tb


# ───────────────────────────────── gün-içi (1m) yardımcılar ─────────────────────────────────

def _intraday_table(b1: pd.DataFrame) -> pd.DataFrame:
    """1m barda (o barın KAPANIŞI itibarıyla) seans kümülatifleri ve kısa pencere istatistikleri."""
    ts = pd.to_datetime(b1.t, unit='s', utc=True).dt.tz_convert(NY)
    naive = ts.dt.tz_localize(None)
    sess = (naive - pd.Timedelta(hours=18)).dt.floor('D')                 # CFD seansı (18:00 ET başlar)
    mod = (naive - naive.dt.floor('D')).dt.total_seconds() // 60          # NY dakikası
    cash_day = naive.dt.floor('D')
    in_cash = (mod >= 570) & (mod < 960)
    f = pd.DataFrame(index=b1.index)
    g = b1.groupby(sess.values)
    f['sess_open'] = g.open.transform('first')
    f['sess_hi'] = g.high.cummax()
    f['sess_lo'] = g.low.cummin()
    # gece (globex 18:00 → 09:30 ET): nakit öncesi kümülatif; nakit açıldıktan sonra donmuş değer
    pre = ~in_cash & (mod < 570) | (mod >= 1080)
    hi_pre = b1.high.where(pre)
    lo_pre = b1.low.where(pre)
    f['on_hi'] = hi_pre.groupby(sess.values).cummax().groupby(sess.values).ffill()
    f['on_lo'] = lo_pre.groupby(sess.values).cummin().groupby(sess.values).ffill()
    # nakit seans: açılış, ORB15, TWAP
    cash_key = np.where(in_cash, cash_day.astype('int64'), -1)
    gc = b1.where(in_cash).groupby(cash_key)
    f['cash_open'] = gc.open.transform('first').where(in_cash)
    orb = in_cash & (mod < 585)
    f['orb_hi'] = b1.high.where(orb).groupby(cash_key).cummax().groupby(cash_key).ffill().where(in_cash & (mod >= 584))
    f['orb_lo'] = b1.low.where(orb).groupby(cash_key).cummin().groupby(cash_key).ffill().where(in_cash & (mod >= 584))
    tp = (b1.high + b1.low + b1.close) / 3
    anchor = np.where(in_cash, cash_day.astype('int64'), sess.astype('int64').to_numpy() + 1)
    cs = tp.groupby(anchor).cumsum()
    cn = tp.groupby(anchor).cumcount() + 1
    cs2 = (tp ** 2).groupby(anchor).cumsum()
    f['twap'] = cs / cn
    f['twap_sd'] = np.sqrt(np.maximum(cs2 / cn - f.twap ** 2, 0))
    f['twap_n'] = cn
    lr = np.log(b1.close).diff()
    f['rv30'] = lr.rolling(30, min_periods=20).std()
    f['rv120'] = lr.rolling(120, min_periods=60).std()
    f['rv_day_med'] = f.rv30.rolling(1380 * 10, min_periods=1380).median()
    f['skew60'] = lr.rolling(60, min_periods=40).skew()
    f['maxabs60'] = lr.abs().rolling(60, min_periods=40).max()
    up = (b1.close > b1.open).astype(int)
    grp = (up != up.shift()).cumsum()
    f['run_len'] = up.groupby(grp).cumcount() + 1
    f['run_dir'] = np.where(up == 1, 1.0, -1.0)
    f['ret15'] = np.log(b1.close / b1.close.shift(15))
    f['ret60'] = np.log(b1.close / b1.close.shift(60))
    f['mod'] = mod
    f['sess_key'] = sess.astype('int64').to_numpy() // 10**9
    f['close'] = b1.close
    return f


# ───────────────────────────────── makro + takvim ─────────────────────────────────

def _macro_table(macro: pd.DataFrame) -> pd.DataFrame:
    """Her seri kendi geçerli günlerinde hesaplanır (tatil/eksik satırlar NaN üretmesin), sonra ileri doldurulur."""
    m = macro.copy()
    m['date'] = pd.to_datetime(m['date'])
    m = m.sort_values('date').drop_duplicates('date').set_index('date')

    def s(col: str) -> pd.Series | None:
        return m[col].dropna() if col in m else None

    cols: dict[str, pd.Series] = {}
    v = s('VIX_close')
    if v is not None:
        cols['vix'] = v
        cols['vix_chg1'] = v.diff()
        cols['vix_chg5'] = v.diff(5)
        cols['vix_rank252'] = v.rolling(252, min_periods=60).rank(pct=True)
        cols['vix_ge_184'] = (v >= VIX_REGIME).astype(float)
        v9, v3 = s('VIX9D_close'), s('VIX3M_close')
        if v9 is not None:
            cols['vix9d_vix'] = (v9 / v).dropna()
        if v3 is not None:
            cols['vix_vix3m'] = (v / v3).dropna()
    ndx, spx = s('NDX_close'), s('SPX_close')
    if ndx is not None:
        cols['ndx_ret1d'] = ndx.pct_change(fill_method=None)
        cols['ndx_ret5d'] = ndx.pct_change(5, fill_method=None)
        if spx is not None:
            j = pd.concat([ndx, spx], axis=1, join='inner')
            cols['ndx_spx_rs5'] = j.iloc[:, 0].pct_change(5, fill_method=None) - j.iloc[:, 1].pct_change(5, fill_method=None)
    dxy = s('DXY_close')
    if dxy is not None:
        cols['dxy_chg1'] = dxy.pct_change(fill_method=None)
        cols['dxy_chg5'] = dxy.pct_change(5, fill_method=None)
    tnx = s('TNX_close')
    if tnx is not None:
        cols['tnx'] = tnx
        cols['tnx_chg5'] = tnx.diff(5)
        if ndx is not None:
            j = pd.concat([ndx, tnx], axis=1, join='inner')
            cols['corr20_ndx_tnx'] = j.iloc[:, 0].pct_change(fill_method=None).rolling(20).corr(j.iloc[:, 1].diff())
    q = s('QQQ_volume')
    if q is not None:
        cols['qqq_vol_z20'] = (q - q.rolling(20).mean()) / q.rolling(20).std()
    f = pd.DataFrame(cols).sort_index().ffill()
    avail = (f.index + pd.Timedelta(hours=MACRO_AVAILABLE_ET[0], minutes=MACRO_AVAILABLE_ET[1]))
    avail = avail.tz_localize(NY).tz_convert('UTC')
    f.insert(0, 'avail', np.asarray(avail.asi8 // 10**9, dtype='int64'))
    return f.reset_index(drop=True)


def _event_features(t_dec: np.ndarray, calendar: pd.DataFrame | None) -> pd.DataFrame:
    out = pd.DataFrame(index=range(len(t_dec)))
    for cls in EVENT_CLASSES:
        if calendar is None or calendar.empty:
            out[f'min_to_{cls}'] = float(EVENT_CAP_MIN)
            out[f'min_since_{cls}'] = float(EVENT_CAP_MIN)
            continue
        ev = calendar[calendar.event.str.startswith(cls)]
        et = np.sort((pd.to_datetime(ev.ts_utc, utc=True).astype('int64') // 10**9).to_numpy())
        j = np.searchsorted(et, t_dec, side='left')
        nxt = np.where(j < len(et), et[np.clip(j, 0, len(et) - 1)], np.nan) if len(et) else np.full(len(t_dec), np.nan)
        prv = np.where(j > 0, et[np.clip(j - 1, 0, len(et) - 1)], np.nan) if len(et) else np.full(len(t_dec), np.nan)
        # bilinen olay yoksa (takvim kapsamı dışı) NaN değil tavan: "≥3 gün uzak" (eğitimde görülmeyen NaN canlıda oluşmasın)
        out[f'min_to_{cls}'] = np.nan_to_num(np.minimum((nxt - t_dec) / 60.0, EVENT_CAP_MIN), nan=EVENT_CAP_MIN)
        out[f'min_since_{cls}'] = np.nan_to_num(np.minimum((t_dec - prv) / 60.0, EVENT_CAP_MIN), nan=EVENT_CAP_MIN)
    return out


# ───────────────────────────────── ana fonksiyon ─────────────────────────────────

def build_context(b1: pd.DataFrame) -> dict:
    """HTF barları + gösterge tabloları + pivotlar + gün-içi tablo (bir kez hesaplanır, çok karar için)."""
    b1 = b1.reset_index(drop=True)
    ctx: dict = {'b1': b1, 'tf': {}, 'piv': {}}
    for tf in B.TF_MIN:
        b = B.resample(b1, tf)
        ctx['tf'][tf] = (b, _tf_table(b, tf))
        if tf in PIVOT_K:
            ctx['piv'][tf] = _pivots(b, tf)
    ctx['intra'] = _intraday_table(b1)
    return ctx


def _levels(ctx: dict, t_dec: np.ndarray, price: np.ndarray, atr_h1: np.ndarray, it: pd.DataFrame,
            d1: pd.DataFrame) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
    """Tüm seviye adayları [N, M] + pivot-test istatistikleri."""
    mats, kinds, times = [], [], []
    for tf, p in ctx['piv'].items():
        lv, ty, tb = _pivot_matrix(p, t_dec, PIVOT_LOOKBACK_S[tf])
        mats.append(lv)
        kinds.append(np.full(lv.shape, {'M15': 1, 'H1': 2, 'D1': 3}[tf], dtype=float))
        times.append(tb)
    piv_lv = np.concatenate(mats, axis=1)
    piv_tb = np.concatenate(times, axis=1)
    fixed = {
        'pdh': d1['h'].to_numpy(), 'pdl': d1['l'].to_numpy(), 'pdc': d1['c'].to_numpy(),
        'onh': it['on_hi'].to_numpy(), 'onl': it['on_lo'].to_numpy(),
        'orbh': it['orb_hi'].to_numpy(), 'orbl': it['orb_lo'].to_numpy(),
        'hi20d': d1['hi20'].to_numpy(), 'lo20d': d1['lo20'].to_numpy(),
    }
    for step in (100, 500, 1000):
        fixed[f'r{step}_up'] = np.ceil(price / step) * step
        fixed[f'r{step}_dn'] = np.floor(price / step) * step
    fx = np.column_stack(list(fixed.values()))
    allv = np.concatenate([piv_lv, fx], axis=1)
    return fixed, allv, piv_lv, piv_tb


def compute_features(b1: pd.DataFrame, t_dec: np.ndarray, macro: pd.DataFrame | None = None,
                     calendar: pd.DataFrame | None = None, ctx: dict | None = None) -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', pd.errors.PerformanceWarning)
        return _compute_features(b1, t_dec, macro, calendar, ctx).copy()


def _compute_features(b1: pd.DataFrame, t_dec: np.ndarray, macro: pd.DataFrame | None,
                      calendar: pd.DataFrame | None, ctx: dict | None) -> pd.DataFrame:
    t_dec = np.asarray(t_dec, dtype='int64')
    if ctx is None:
        ctx = build_context(b1)
    b1 = ctx['b1']
    F = pd.DataFrame(index=range(len(t_dec)))
    # HTF tabloları
    maps = {}
    for tf, (b, tab) in ctx['tf'].items():
        mp = B.asof_map(t_dec, b.end.to_numpy(), tab)
        maps[tf] = mp
        keep = [c for c in tab.columns if c not in ('c', 'h', 'l', 'hi20', 'lo20', 'adr20', 'atr')]
        for c in keep:
            F[f'{tf}_{c}'] = mp[c].to_numpy()
    atr = {tf: maps[tf]['atr'].to_numpy() for tf in maps}
    a1 = atr['H1']
    F['atr_M5_H1'] = atr['M5'] / a1
    F['atr_M15_H1'] = atr['M15'] / a1
    F['atr_H1_pct'] = a1 / np.nan_to_num(maps['D1']['c'].to_numpy(), nan=np.nan)
    # 1m gün-içi
    i1 = B.last_closed_1m(b1.t.to_numpy(), t_dec)
    it = ctx['intra'].iloc[np.clip(i1, 0, None)].reset_index(drop=True)
    it.loc[i1 < 0, :] = np.nan
    price = it['close'].to_numpy()
    d1 = maps['D1']
    F['rv30_ratio'] = (it.rv30 / it.rv_day_med).to_numpy()
    F['rv120_ratio'] = (it.rv120 / it.rv_day_med).to_numpy()
    F['skew60'] = it.skew60.to_numpy()
    F['maxabs60_atr'] = (it.maxabs60 * price / atr['M5']).to_numpy()
    F['run_len_signed'] = (it.run_len * it.run_dir).to_numpy()
    F['ret15_atr'] = (it.ret15 * price / atr['M15']).to_numpy()
    F['ret60_atr'] = (it.ret60 * price / a1).to_numpy()
    F['sess_range_adr'] = ((it.sess_hi - it.sess_lo) / d1['adr20']).to_numpy()
    rng = (it.sess_hi - it.sess_lo).replace(0, np.nan)
    F['sess_pos'] = ((it.close - it.sess_lo) / rng).to_numpy()
    F['sess_ret_atr'] = ((it.close - it.sess_open) / a1).to_numpy()
    F['cash_gap_atr'] = ((it.cash_open - d1['c']) / a1).to_numpy()
    F['twap_z'] = ((it.close - it.twap) / it.twap_sd.replace(0, np.nan)).where(it.twap_n >= 15).to_numpy()
    F['twap_dist_atr'] = ((it.close - it.twap) / a1).to_numpy()
    # seviyeler
    fixed, allv, piv_lv, piv_tb = _levels(ctx, t_dec, price, a1, it, d1)
    for k, v in fixed.items():
        if not k.startswith('r'):
            F[f'lvl_{k}_dist'] = (v - price) / a1
    for step in (100, 500, 1000):
        up = fixed[f'r{step}_up'] - price
        dn = price - fixed[f'r{step}_dn']
        F[f'round{step}_near'] = np.minimum(up, dn) / a1
    d = (allv - price[:, None]) / a1[:, None]
    above = np.where(d > 0.02, d, np.inf)
    below = np.where(d < -0.02, -d, np.inf)
    na = np.min(above, axis=1)
    nb = np.min(below, axis=1)
    F['sr_above_dist'] = np.where(np.isfinite(na), na, np.nan)
    F['sr_below_dist'] = np.where(np.isfinite(nb), nb, np.nan)
    F['sr_room_ratio'] = F.sr_above_dist / F.sr_below_dist
    F['sr_n_within_05_above'] = ((d > 0) & (d <= 0.5)).sum(axis=1)
    F['sr_n_within_05_below'] = ((d < 0) & (d >= -0.5)).sum(axis=1)
    # test sayısı: en yakın üst/alt seviyenin ±tol içindeki pivot sayısı + son testten geçen süre
    lvl_above = price + np.nan_to_num(F.sr_above_dist.to_numpy(), nan=1e9) * a1
    lvl_below = price - np.nan_to_num(F.sr_below_dist.to_numpy(), nan=1e9) * a1
    tol = (LEVEL_TOL_ATR * a1)[:, None]
    for name, lv in (('above', lvl_above), ('below', lvl_below)):
        near = np.abs(piv_lv - lv[:, None]) <= tol
        F[f'sr_{name}_tests'] = near.sum(axis=1)
        last_t = np.where(near, piv_tb, -np.inf).max(axis=1)
        F[f'sr_{name}_hrs_since_test'] = np.where(np.isfinite(last_t), (t_dec - last_t) / 3600.0, np.nan)
    # HH/HL yapısı (H1 pivotları)
    hh_struct = _structure(ctx['piv']['H1'], t_dec)
    F['h1_structure'] = hh_struct
    # zaman
    ts = pd.to_datetime(t_dec, unit='s', utc=True).tz_convert(NY)
    mod = (ts.hour * 60 + ts.minute).to_numpy()
    F['ny_mod_sin'] = np.sin(2 * np.pi * mod / 1440)
    F['ny_mod_cos'] = np.cos(2 * np.pi * mod / 1440)
    F['session_phase'] = session_phase(mod)
    F['dow'] = ts.dayofweek.to_numpy()
    dates = ts.tz_localize(None).normalize()
    dlist = [x.date() for x in dates]
    F['is_early_close'] = np.array([CAL.is_early_close(x) for x in dlist], dtype=float)
    F['is_holiday'] = np.array([CAL.is_holiday(x) for x in dlist], dtype=float)
    F['month_end'] = _month_edge(dates, end=True)
    F['month_start'] = _month_edge(dates, end=False)
    close_m = np.array([CAL.cash_close_minutes(x) for x in dlist])
    F['min_to_cash_close'] = np.where((mod >= 570) & (mod < close_m), close_m - mod, np.nan)
    F['min_since_cash_open'] = np.where((mod >= 570) & (mod < close_m), mod - 570, np.nan)
    ev = _event_features(t_dec, calendar)
    for c in ev.columns:
        F[c] = ev[c].to_numpy()
    # makro
    if macro is not None and len(macro):
        mt = _macro_table(macro)
        mp = B.asof_map(t_dec, mt.avail.to_numpy(), mt.drop(columns=['avail']))
        for c in mp.columns:
            F[f'mac_{c}'] = mp[c].to_numpy()
    # yardımcılar (özellik değil)
    F['_t'] = t_dec
    F['_price'] = price
    for tf in ('M5', 'M15', 'H1'):
        F[f'_atr_{tf}'] = atr[tf]
    F['_i1'] = i1
    return F


def _structure(p: pd.DataFrame, t_dec: np.ndarray) -> np.ndarray:
    """Son iki teyitli H1 tepesi ve dibi: +2 HH&HL, −2 LH&LL, diğer kombinasyonlar ±1/0."""
    out = np.full(len(t_dec), np.nan)
    for typ, sgn in ((1.0, 'h'), (-1.0, 'l')):
        q = p[p.typ == typ]
        e = np.searchsorted(q.conf.to_numpy(), t_dec, side='right')
        lv = q.lvl.to_numpy()
        last = np.where(e >= 1, lv[np.clip(e - 1, 0, None)], np.nan) if len(q) else np.full(len(t_dec), np.nan)
        prev = np.where(e >= 2, lv[np.clip(e - 2, 0, None)], np.nan) if len(q) else np.full(len(t_dec), np.nan)
        s = np.sign(last - prev)
        if sgn == 'h':
            sh = s
        else:
            sl = s
    out = sh + sl
    return out


def session_phase(mod: np.ndarray) -> np.ndarray:
    """0 asya (18:00-03:00), 1 londra (03:00-09:30), 2 NY açılış (09:30-10:30), 3 öğle (10:30-14:00),
    4 kapanış (14:00-16:00), 5 kapanış sonrası (16:00-18:00) — NY saatiyle."""
    ph = np.full(len(mod), 0)
    ph[(mod >= 180) & (mod < 570)] = 1
    ph[(mod >= 570) & (mod < 630)] = 2
    ph[(mod >= 630) & (mod < 840)] = 3
    ph[(mod >= 840) & (mod < 960)] = 4
    ph[(mod >= 960) & (mod < 1080)] = 5
    return ph


def _month_edge(dates: pd.DatetimeIndex, end: bool) -> np.ndarray:
    """Ayın son/ilk 2 iş günü (hafta içi + NYSE tatili hariç) bayrağı."""
    out = np.zeros(len(dates))
    uniq = pd.DatetimeIndex(sorted(set(dates)))
    flag = {}
    for d in uniq:
        mstart = d.replace(day=1)
        mend = (mstart + pd.offsets.MonthEnd(0))
        days = [x for x in pd.date_range(mstart, mend) if x.weekday() < 5 and not CAL.is_holiday(x.date())]
        edge = days[-2:] if end else days[:2]
        flag[d] = float(d in edge)
    return np.array([flag[d] for d in dates])


def feature_columns(F: pd.DataFrame) -> list[str]:
    return [c for c in F.columns if not c.startswith('_')]


def level_context(ctx: dict, t_dec: int, n: int = 3) -> dict:
    """Canlı açıklama: en yakın n destek + n direnç (fiyat, ATR(H1) uzaklığı, test sayısı, tür)."""
    t = np.array([t_dec], dtype='int64')
    F = compute_features(ctx['b1'], t, ctx=ctx)
    price = float(F._price.iloc[0])
    a1 = float(F._atr_H1.iloc[0])
    b, tab = ctx['tf']['D1']
    d1 = B.asof_map(t, b.end.to_numpy(), tab)
    i1 = int(F._i1.iloc[0])
    it = ctx['intra'].iloc[[max(i1, 0)]].reset_index(drop=True)
    fixed, allv, piv_lv, piv_tb = _levels(ctx, t, np.array([price]), np.array([a1]), it, d1)
    names = []
    for tf, p in ctx['piv'].items():
        names += [f'pivot_{tf}'] * PIVOT_LAST_N
    names += list(fixed.keys())
    lv = allv[0]
    rows = []
    for nm, v in zip(names, lv):
        if not np.isfinite(v):
            continue
        tests = int((np.abs(piv_lv[0] - v) <= LEVEL_TOL_ATR * a1).sum())
        rows.append({'price': round(float(v), 1), 'dist_atr': round(float((v - price) / a1), 2), 'kind': nm,
                     'tests': tests})
    df = pd.DataFrame(rows)
    if df.empty:
        return {'supports': [], 'resistances': [], 'price': price, 'atr_h1': a1}
    df = df.sort_values('tests', ascending=False).drop_duplicates('price')
    # aynı bölgedeki (±tol) seviyeleri birleştir: en çok test edileni tut
    def pick(side: pd.DataFrame, asc: bool) -> list[dict]:
        side = side.sort_values('dist_atr', ascending=asc)
        keep: list[dict] = []
        for r in side.to_dict('records'):
            if all(abs(r['dist_atr'] - k['dist_atr']) > LEVEL_TOL_ATR for k in keep):
                keep.append(r)
            if len(keep) >= n:
                break
        return keep
    return {'price': price, 'atr_h1': a1,
            'resistances': pick(df[df.dist_atr > 0.02], True),
            'supports': pick(df[df.dist_atr < -0.02], False)}
