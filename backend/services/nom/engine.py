"""NOM — canlı olasılık motoru (karar desteği; EMİR AÇMAZ).

`predict(horizon, geometry)` →
  long/short: P(TP önce), P(SL önce), P(zaman aşımı), beklenen R, %95 bant (WF OOS kovasından)
  context  : en yakın 3 destek + 3 direnç, RSI (her TF) ve 70/30'a uzaklık, trend/rejim, seans, VIX, yaklaşan olay
  explain  : TreeSHAP ile P(TP)'yi en çok etkileyen 5 faktör (Türkçe)
  status   : yalnız eğitimde kanıtlanmış hedef + eşik geçilirse yön; aksi hâlde 'NÖTR / belirsiz'
  model    : sürüm, eğitim sonu, veri tazeliği. Veri bayatsa tahmin VERİLMEZ.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
import pandas as pd

from . import features as FE
from . import labels as LB
from . import live_data as LD
from . import model_store as MS

logger = logging.getLogger(__name__)
STALE_S = 5 * 60
YON_UYARISI = ('LONG − SHORT farkı yön sinyali değildir (Yön Lab 2026-11-14: seviye aileleri hayaletten ayrılmıyor, ±1 ATR yarışında '
               'yön isabeti %50; tek iz 15 dk aşırı-uzama dönüşü maliyetin altında). research/yon_lab_20261114/FAZ_10_RAPOR.md')
NY = 'America/New_York'
_cache: dict[str, Any] = {'bundle': None, 'bundle_ver': None, 'ctx_key': None, 'ctx': None}

FEATURE_TR = {
    'ny_mod_sin': 'günün saati', 'ny_mod_cos': 'günün saati', 'session_phase': 'seans fazı',
    'min_to_cash_close': 'nakit kapanışa kalan süre', 'min_since_cash_open': 'nakit açılıştan geçen süre',
    'rv30_ratio': 'son 30 dk oynaklığı (normale göre)', 'rv120_ratio': 'son 2 saat oynaklığı (normale göre)',
    'M15_atr_ratio': 'M15 ATR rejimi', 'H1_atr_ratio': 'H1 ATR rejimi', 'atr_M5_H1': 'kısa/uzun ATR oranı',
    'atr_M15_H1': 'M15/H1 ATR oranı', 'atr_H1_pct': 'H1 ATR (% fiyat)', 'is_holiday': 'ABD tatil günü',
    'M5_rsi14': 'M5 RSI14', 'M15_rsi14': 'M15 RSI14', 'H1_rsi14': 'H1 RSI14', 'H4_rsi14': 'H4 RSI14', 'D1_rsi14': 'D1 RSI14',
    'ret15_atr': 'son 15 dk getiri', 'ret60_atr': 'son 60 dk getiri', 'twap_z': 'TWAP z-skoru',
    'sr_above_dist': 'en yakın dirence uzaklık', 'sr_below_dist': 'en yakın desteğe uzaklık',
    'sr_room_ratio': 'direnç/destek oda oranı', 'lvl_pdc_dist': 'önceki gün kapanışına uzaklık',
    'lvl_pdh_dist': 'önceki gün tepesine uzaklık', 'lvl_pdl_dist': 'önceki gün dibine uzaklık',
    'lvl_onh_dist': 'gece tepesine uzaklık', 'lvl_onl_dist': 'gece dibine uzaklık',
    'lvl_orbh_dist': 'açılış aralığı tepesine uzaklık', 'lvl_orbl_dist': 'açılış aralığı dibine uzaklık',
    'mac_vix': 'VIX düzeyi', 'mac_vix_chg1': 'VIX 1 günlük değişim', 'mac_vix_chg5': 'VIX 5 günlük değişim',
    'mac_vix9d_vix': 'VIX9D/VIX vade yapısı', 'mac_vix_vix3m': 'VIX/VIX3M vade yapısı', 'cash_gap_atr': 'açılış boşluğu',
    'min_to_EARN': 'mega-cap bilançoya kalan süre', 'min_to_CPI': "CPI'ya kalan süre", 'min_to_FOMC': "FOMC'a kalan süre",
    'min_to_NFP': "NFP'ye kalan süre", 'H1_ema200_slope': 'H1 EMA200 eğimi', 'H1_ema200_dist': 'H1 EMA200 uzaklığı',
    'sess_range_adr': 'bugünkü aralık / ortalama günlük aralık', 'dow': 'haftanın günü',
}


def _bundle() -> MS.Bundle:
    v = MS.active_version()
    if _cache['bundle'] is None or _cache['bundle_ver'] != v:
        _cache['bundle'] = MS.load_bundle(v)
        _cache['bundle_ver'] = v
    return _cache['bundle']


def norm_geometry(g: str) -> str:
    try:
        tp, sl = (float(x) for x in g.lower().replace(' ', '').split('x'))
    except Exception as e:  # noqa: BLE001
        raise ValueError(f'geometri biçimi TPxSL olmalı (ör. 1.5x1.0): {g}') from e
    return LB.geom_key(tp, sl)


def _band(table: list[dict], value: float, key: str) -> dict | None:
    """WF OOS kova tablosundan (sıralı 'lo','hi' sınırlı) değerin kovası."""
    for row in table:
        if row['lo'] <= value <= row['hi']:
            return {k: row[k] for k in row if k not in ('lo', 'hi')} | {'kova': [row['lo'], row['hi']], 'anahtar': key}
    return None


def _explain(booster, X: pd.DataFrame, top: int = 5) -> list[dict]:
    p = X.shape[1]
    contrib = booster.predict(X, pred_contrib=True).reshape(3, p + 1)[0, :p]       # TP sınıfı marjı
    order = np.argsort(-np.abs(contrib))[:top]
    out = []
    for j in order:
        c = X.columns[j]
        v = X.iloc[0, j]
        name = FEATURE_TR.get(c, c)
        yon = 'artırıyor' if contrib[j] > 0 else 'azaltıyor'
        val = 'yok' if pd.isna(v) else f'{float(v):.2f}'
        out.append({'ozellik': c, 'ad': name, 'deger': None if pd.isna(v) else float(v), 'katki': float(contrib[j]),
                    'metin': f'{name} ({val}) TP-önce olasılığını {yon}'})
    return out


def _context(ctx: dict, F: pd.DataFrame, t_dec: int, calendar: pd.DataFrame | None) -> dict:
    row = F.iloc[0]
    lv = FE.level_context(ctx, t_dec, n=3)
    rsi = {}
    for tf in ('M5', 'M15', 'H1', 'H4', 'D1'):
        v = row.get(f'{tf}_rsi14')
        if v is not None and not pd.isna(v):
            rsi[tf] = {'rsi14': round(float(v), 1), 'asiri_alima_uzaklik': round(70 - float(v), 1),
                       'asiri_satima_uzaklik': round(float(v) - 30, 1),
                       'bolge': 'aşırı alım' if v >= 70 else 'aşırı satım' if v <= 30 else 'nötr'}
    adx = row.get('H1_adx14')
    trend = {'h1_ema_dizilim': None if pd.isna(row.get('H1_ema_stack')) else float(row['H1_ema_stack']),
             'h1_psar_yon': None if pd.isna(row.get('H1_psar_dir')) else float(row['H1_psar_dir']),
             'h1_adx': None if pd.isna(adx) else round(float(adx), 1),
             'h1_yapi_hh_hl': None if pd.isna(row.get('h1_structure')) else float(row['h1_structure'])}
    rejim = 'trend' if adx is not None and not pd.isna(adx) and adx >= 25 else 'yatay'
    vix = row.get('mac_vix')
    phase = FE.SESSION_PHASES.get(int(row['session_phase']), '?')
    nxt = None
    if calendar is not None and len(calendar):
        ts = pd.to_datetime(calendar.ts_utc, utc=True)
        fut = calendar[(ts.astype('int64') // 10**9 > t_dec)].copy()
        if len(fut):
            r0 = fut.iloc[0]
            nxt = {'olay': str(r0.event), 'zaman_utc': str(r0.ts_utc),
                   'dakika': int((pd.Timestamp(r0.ts_utc).timestamp() - t_dec) // 60)}
    return {'fiyat': lv['price'], 'atr_h1': round(lv['atr_h1'], 2), 'destekler': lv['supports'],
            'direncler': lv['resistances'], 'rsi': rsi, 'trend': trend, 'rejim': rejim,
            'atr_rejim_h1': None if pd.isna(row.get('H1_atr_ratio')) else round(float(row['H1_atr_ratio']), 2),
            'seans': phase,
            'vix': None if vix is None or pd.isna(vix) else {'deger': round(float(vix), 2),
                                                              'rejim': 'yüksek (≥18,4)' if vix >= 18.4 else 'düşük (<18,4)'},
            'yaklasan_olay': nxt}


def predict(horizon: str = '1h', geometry: str = '1.5x1.0', now: float | None = None,
            bars: pd.DataFrame | None = None, macro: pd.DataFrame | None = None,
            calendar: pd.DataFrame | None = None, asof: float | None = None) -> dict:
    """asof (epoch sn): yeniden oynatma — yalnız asof'tan önce kapanmış barlar kullanılır, 'şimdi' = asof."""
    if asof is not None:
        b0 = LD.load_bars() if bars is None else bars
        bars = b0[b0.t + 60 <= asof].reset_index(drop=True)
        macro = LD.load_macro() if macro is None else macro
        calendar = LD.load_calendar() if calendar is None else calendar
        now = float(asof)
        r = _predict(horizon, geometry, now, bars, macro, calendar, live=False)
        r['yeniden_oynatma'] = pd.Timestamp(asof, unit='s', tz='UTC').isoformat()
        return r
    return _predict(horizon, geometry, now, bars, macro, calendar, live=bars is None)


def _predict(horizon: str, geometry: str, now: float | None, bars: pd.DataFrame | None,
             macro: pd.DataFrame | None, calendar: pd.DataFrame | None, live: bool) -> dict:
    if horizon not in LB.HORIZONS:
        raise ValueError(f'ufuk: {list(LB.HORIZONS)}')
    gk = norm_geometry(geometry)
    if gk not in {LB.geom_key(*g) for g in LB.GEOMETRIES}:
        raise ValueError(f'geometri: {[LB.geom_key(*g) for g in LB.GEOMETRIES]}')
    now = now or time.time()
    bundle = _bundle()
    b = LD.load_bars() if bars is None else bars
    macro = LD.load_macro() if macro is None and live else macro
    calendar = LD.load_calendar() if calendar is None and live else calendar
    base = {'model': {'surum': bundle.version, 'egitim_sonu': bundle.meta.get('trained_until'),
                      'veri_surumu': bundle.meta.get('data_version')},
            'ufuk': horizon, 'geometri': gk, 'not': 'Karar destek aracıdır; otomatik işlem açmaz.',
            'yon_uyarisi': YON_UYARISI}
    if b is None or b.empty:
        return base | {'durum': 'VERI_YOK', 'tahmin': None}
    last_t = int(b.t.iloc[-1])
    t_dec = last_t + 60
    lag = now - t_dec
    base['veri'] = {'kaynak': 'candle_cache NDX.INDX 1m (MT5 kaydedici)',
                    'son_bar_kapanis_utc': pd.Timestamp(t_dec, unit='s', tz='UTC').isoformat(), 'gecikme_sn': round(lag)}
    if not LD.market_open(now):
        return base | {'durum': 'PIYASA_KAPALI', 'tahmin': None}
    if lag > STALE_S:
        return base | {'durum': 'VERI_BAYAT', 'tahmin': None,
                       'aciklama': f'son bar {int(lag // 60)} dk önce kapandı (> {STALE_S // 60} dk) — tahmin verilmez'}
    if horizon == 'session':
        ny = pd.Timestamp(t_dec, unit='s', tz='UTC').tz_convert(NY)
        mod = ny.hour * 60 + ny.minute
        from . import nyse_calendar as CAL
        close = CAL.cash_close_minutes(ny.date())
        if not (570 <= mod <= close - 30) or CAL.is_holiday(ny.date()):
            return base | {'durum': 'UFUK_TANIMSIZ', 'tahmin': None,
                           'aciklama': 'seans sonu ufku yalnız NY nakit seansında (kapanıştan ≥30 dk önce) tanımlı'}
    key = (bundle.version, last_t, len(b))
    if _cache['ctx_key'] != key:
        _cache['ctx'] = FE.build_context(b)
        _cache['ctx_key'] = key
    ctx = _cache['ctx']
    F = FE.compute_features(b, np.array([t_dec]), macro, calendar, ctx=ctx)
    cols = bundle.meta['feature_columns']
    X = F[cols]
    out = {}
    for d in ('long', 'short'):
        booster, cal, tm = bundle.target(horizon, d, gk)
        p = cal.apply(booster.predict(X))[0]
        exp_r = float(p[0] * tm['tp_r'] + p[1] * tm['r_sl'] + p[2] * tm['r_to'])
        out[d] = {'p_tp_once': round(float(p[0]), 4), 'p_sl_once': round(float(p[1]), 4),
                  'p_zaman_asimi': round(float(p[2]), 4), 'beklenen_r': round(exp_r, 4),
                  'p_tp_bandi': _band(tm.get('p_tp_bins', []), float(p[0]), 'p_tp'),
                  'beklenen_r_bandi': _band(tm.get('exp_r_bins', []), exp_r, 'beklenen_r'),
                  'taban': {'p_tp': tm.get('base_p_tp'), 'beklenen_r': tm.get('base_ev_r')},
                  'esik': tm.get('threshold'), 'kanitli': bool(tm.get('proven', False)),
                  'neden': _explain(booster, X)}
    status, why = 'NÖTR / belirsiz', 'hiçbir taraf eğitimde kanıtlanmış eşiği geçmiyor'
    cands = [(d, out[d]['beklenen_r']) for d in out
             if out[d]['kanitli'] and out[d]['esik'] is not None and out[d]['beklenen_r'] >= out[d]['esik']]
    if cands:
        d, e = max(cands, key=lambda x: x[1])
        status, why = ('LONG' if d == 'long' else 'SHORT'), f'{d} beklenen R {e:+.3f} ≥ kanıtlı eşik'
    atr_units = {tf: round(float(F[f'_atr_{tf}'].iloc[0]), 3) for tf in ('M5', 'M15', 'H1')}
    return base | {'durum': status, 'durum_nedeni': why, 'tahmin': out, 'atr_birimleri': atr_units,
                   'atr_ufuk': {'tf': LB.HORIZONS[horizon]['atr_tf'], 'deger': atr_units[LB.HORIZONS[horizon]['atr_tf']]},
                   'baglam': _context(ctx, F, t_dec, calendar)}
