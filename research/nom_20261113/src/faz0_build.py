"""NOM Faz 0 — envanter + kaynak karşılaştırma + temiz katman yazımı.

python src/faz0_build.py  →  data/ndx_1m_v1.parquet, results/faz0_*.json|csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(H / 'src'))
sys.path.insert(0, str(REPO / 'backend'))
import data_layer as DL  # noqa: E402
from services.nom import nyse_calendar as CAL  # noqa: E402

RES = H / 'results'
DATA_VERSION = 'ndx_1m_v1'
TOL_PTS = 3.0            # uyum toleransı (seviye farkı çıkarıldıktan sonra kapanış farkı)
LAGS = range(-90, 91)    # dakika: saat ekseni kayması taraması


def inventory(m: pd.DataFrame, name: str) -> dict:
    ts = pd.to_datetime(m.t, unit='s', utc=True)
    step = np.diff(m.t.to_numpy())
    ny = ts.dt.tz_convert(DL.NY)
    days = ny.dt.date
    per_day = m.groupby(days).size()
    weekdays = [d for d in pd.date_range(days.min(), days.max()).date if d.weekday() < 5]
    trading = [d for d in weekdays if not CAL.is_holiday(d)]
    missing = sorted(set(trading) - set(per_day.index))
    thin = per_day[per_day < 600]
    return {
        'source': name, 'start_utc': str(ts.min()), 'end_utc': str(ts.max()), 'bars': int(len(m)),
        'dup_t': int(m.t.duplicated().sum()),
        'gaps_gt5m_open_market': int(((step > 300) & (step < 3600)).sum()),
        'trading_days_expected': len(trading), 'days_missing': len(missing),
        'days_missing_sample': [str(x) for x in missing[:15]],
        'days_thin_lt600bars': int(len(thin)),
        'median_bars_per_day': float(per_day.median()),
        'spread_obs_median': float(np.nanmedian(m.spr_obs)) if 'spr_obs' in m and m.spr_obs.notna().any() else None,
        'has_volume': bool('vol' in m and m.vol.notna().any()),
        'timezone': 'UTC (epoch sn, bar açılışı)',
    }


def compare(a: pd.DataFrame, b: pd.DataFrame, an: str, bn: str) -> dict:
    """a, b: t, close (+high, low). Saat kayması taraması + seviye farkı + uyum oranı."""
    x = a[['t', 'close', 'high', 'low']].merge(b[['t', 'close', 'high', 'low']], on='t', suffixes=('_a', '_b'))
    if len(x) < 500:
        return {'pair': f'{an} vs {bn}', 'overlap_bars': int(len(x))}
    ra = np.diff(np.log(x.close_a.to_numpy()))
    # gecikme taraması: b'yi k dakika kaydır, getiri korelasyonu
    sa = a.set_index('t').close
    sb = b.set_index('t').close
    lag_corr = {}
    for k in LAGS:
        y = pd.concat([sa, sb.rename(lambda t: t + 60 * k)], axis=1, join='inner').dropna()
        if len(y) < 500:
            continue
        r = np.log(y).diff().dropna()
        lag_corr[k] = float(r.iloc[:, 0].corr(r.iloc[:, 1]))
    best = max(lag_corr, key=lag_corr.get) if lag_corr else None
    diff = x.close_a - x.close_b
    off = diff.rolling(1440, min_periods=60, center=True).median()
    resid = (diff - off).abs()
    day = pd.to_datetime(x.t, unit='s', utc=True).dt.date
    per_day_agree = (resid <= TOL_PTS).groupby(day).mean()
    return {
        'pair': f'{an} vs {bn}', 'overlap_bars': int(len(x)),
        'overlap_start': str(pd.to_datetime(x.t.min(), unit='s', utc=True)),
        'overlap_end': str(pd.to_datetime(x.t.max(), unit='s', utc=True)),
        'level_offset_median_pts': float(diff.median()), 'level_offset_iqr_pts': float(diff.quantile(.75) - diff.quantile(.25)),
        'ret_corr_lag0': lag_corr.get(0), 'best_lag_min': best, 'best_lag_corr': lag_corr.get(best),
        'agree_within_tol_frac': float((resid <= TOL_PTS).mean()), 'tol_pts': TOL_PTS,
        'resid_p95_pts': float(resid.quantile(.95)), 'resid_max_pts': float(resid.max()),
        'days_agree_lt80pct': int((per_day_agree < 0.8).sum()), 'days_total': int(len(per_day_agree)),
        'range_ratio_median': float(((x.high_a - x.low_a) / (x.high_b - x.low_b).replace(0, np.nan)).median()),
    }


def weekly_lag_scan(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """Haftalık en iyi gecikme (E4 tipi dönemsel kaymaları yakalamak için)."""
    out = []
    sa = a.set_index('t').close
    wk = (b.t // (7 * 86400))
    for w, g in b.groupby(wk):
        if len(g) < 1500:
            continue
        sb = g.set_index('t').close
        best, bc = None, -1.0
        for k in range(-180, 181, 15):
            y = pd.concat([sa, sb.rename(lambda t: t + 60 * k)], axis=1, join='inner').dropna()
            if len(y) < 500:
                continue
            r = np.log(y).diff().dropna()
            c = r.iloc[:, 0].corr(r.iloc[:, 1])
            if c > bc:
                best, bc = k, c
        out.append({'week_start': str(pd.to_datetime(g.t.min(), unit='s', utc=True).date()), 'best_lag_min': best,
                    'corr': round(bc, 3), 'bars': len(g)})
    return pd.DataFrame(out)


def roll_gaps(m: pd.DataFrame) -> dict:
    """Günlük aradan (17-18 NY) sonraki açılış sıçraması; çeyrek vade (Mar/Haz/Eyl/Ara 3. Cuma'dan önceki
    hafta) günlerinde sistematik sıçrama var mı?"""
    ts = pd.to_datetime(m.t, unit='s', utc=True)
    step = np.r_[0, np.diff(m.t.to_numpy())]
    reopen = (step >= 3600) & (step < 4 * 86400)
    prev_close = m.close.shift(1)
    gap = (m.open - prev_close)[reopen]
    d = ts[reopen].dt.tz_convert(DL.NY).dt.date
    def is_roll(x) -> bool:
        if x.month not in (3, 6, 9, 12):
            return False
        first = pd.Timestamp(x.year, x.month, 1)
        third_fri = first + pd.Timedelta(days=(4 - first.weekday()) % 7 + 14)
        return 0 <= (third_fri.date() - x).days <= 8
    roll = np.array([is_roll(x) for x in d])
    g = gap.to_numpy()
    return {'reopen_events': int(len(g)), 'abs_gap_median_pts': float(np.median(np.abs(g))),
            'roll_window_events': int(roll.sum()),
            'roll_window_abs_gap_median': float(np.median(np.abs(g[roll]))) if roll.any() else None,
            'roll_window_mean_gap': float(np.mean(g[roll])) if roll.any() else None,
            'other_mean_gap': float(np.mean(g[~roll])),
            'largest_gaps': [{'date': str(dd), 'gap_pts': round(float(v), 1)} for dd, v in
                             sorted(zip(d, g), key=lambda z: -abs(z[1]))[:8]]}


def load_candle_cache() -> pd.DataFrame:
    c = pd.read_csv(REPO / 'nasdaq_1m_candle_cache_2026-02-10_2026-08-29/nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv')
    c['t'] = (pd.to_datetime(c.time_utc, utc=True).astype('int64') // 10**9).astype('int64')
    return c[['t', 'open', 'high', 'low', 'close']]


def load_recover_json() -> pd.DataFrame:
    j = json.load(open(REPO / 'RECOVER/mt5_ustec_1m_bars.json'))
    bars = j.get('bars') or j.get('data') or []
    if not bars:
        return pd.DataFrame(columns=['t', 'open', 'high', 'low', 'close'])
    r = pd.DataFrame(bars)
    r = r.rename(columns={'time': 't', 'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close'})
    return r[['t', 'open', 'high', 'low', 'close']]


def quality_score(inv: dict, cmp_gold: dict | None) -> float:
    """0-100: kapsam (eksik gün), boşluk, duplike, altın standarda uyum."""
    s = 100.0
    s -= 40 * inv['days_missing'] / max(1, inv['trading_days_expected'])
    s -= 20 * min(1.0, inv['days_thin_lt600bars'] / max(1, inv['trading_days_expected']))
    s -= 10 * min(1.0, inv['dup_t'] / max(1, inv['bars']) * 100)
    if cmp_gold and 'agree_within_tol_frac' in cmp_gold:
        s -= 30 * (1 - cmp_gold['agree_within_tol_frac'])
        if cmp_gold.get('best_lag_min') not in (0, None):
            s -= 20
    return round(max(0.0, s), 1)


def main() -> None:
    RES.mkdir(exist_ok=True)
    m, stats, sm = DL.build_master()
    gold = DL.load_mt5_gold()
    cc = load_candle_cache()
    rec = load_recover_json()
    inv = {'master': inventory(m, 'NOM master (birleşik)')}
    for src in m.src.unique():
        inv[src] = inventory(m[m.src == src], src)
    gi = gold.assign(spr_obs=gold.spr)
    inv['mt5_gold'] = inventory(gi, 'MT5 NAS100 1m (Pepperstone, altın standart)')
    inv['candle_cache'] = inventory(cc, 'Supabase candle_cache 1m CSV')
    cmp = {
        'duka_vs_mt5gold': compare(m, gold, 'duka', 'mt5gold'),
        'candlecache_vs_mt5gold': compare(cc, gold, 'candle_cache', 'mt5gold'),
        'duka_vs_candlecache': compare(m, cc, 'duka', 'candle_cache'),
    }
    if len(rec):
        cmp['recover_json_vs_mt5gold'] = compare(rec, gold, 'recover_json(broker saati?)', 'mt5gold')
        inv['recover_json'] = inventory(rec.assign(spr_obs=np.nan), 'RECOVER/mt5_ustec_1m_bars.json')
    wk = weekly_lag_scan(m, cc)
    wk.to_csv(RES / 'faz0_candle_cache_weekly_lag.csv', index=False)
    rg = roll_gaps(m)
    q = {k: quality_score(v, cmp.get('duka_vs_mt5gold') if k in ('master',) or k.startswith('duka') or k.startswith('haber')
                          else cmp.get('candlecache_vs_mt5gold') if k == 'candle_cache' else None)
         for k, v in inv.items()}
    yearly = m.groupby(pd.to_datetime(m.t, unit='s', utc=True).dt.year).agg(
        bars=('t', 'size'), spr_obs_frac=('spr_obs', lambda s: float(s.notna().mean())),
        close_min=('close', 'min'), close_max=('close', 'max')).reset_index()
    out = {'data_version': DATA_VERSION, 'clean_stats': stats, 'inventory': inv, 'compare': cmp,
           'roll_gaps': rg, 'quality_score': q, 'spread_model_ny_hour': sm.round(3).to_dict(),
           'yearly': yearly.to_dict('records'),
           'candle_cache_weeks_lag_nonzero': wk[wk.best_lag_min != 0].to_dict('records')}
    (RES / 'faz0_inventory.json').write_text(json.dumps(out, indent=1, default=str))
    keep = m[['t', 'open', 'high', 'low', 'close', 'spr', 'spr_obs', 'src']].copy()
    keep['src'] = keep.src.astype('category')
    for c in ('open', 'high', 'low', 'close', 'spr', 'spr_obs'):
        keep[c] = keep[c].astype('float64')
    keep.to_parquet(H / 'data' / f'{DATA_VERSION}.parquet', index=False)
    print(json.dumps({'master': inv['master'], 'cmp': cmp, 'q': q, 'roll': rg}, indent=1, default=str)[:6000])


if __name__ == '__main__':
    main()
