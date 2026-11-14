"""Ek ikili durumlar (PROTOCOL §7) — NOM'un 132 özelliğine ek. Hepsi KAPANMIŞ HTF barlarından (asof end ≤ t)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import core as C
from services.nom import bars as B
from services.nom import nyse_calendar as CAL

NY = C.NY
DIX_FILE = C.H / 'data/DIX.csv'


def _ind(b: pd.DataFrame, tf: str) -> pd.DataFrame:
    c, h, l, o = b.c, b.h, b.l, b.o
    f = pd.DataFrame(index=b.index)
    e9, e21, e50, e200 = (B.ema(c, n) for n in (9, 21, 50, 200))
    x921 = np.sign(e9 - e21)
    f[f'{tf}_x921_up3'] = ((x921 > 0) & (x921.shift(3) < 0)).astype(float)
    f[f'{tf}_x921_dn3'] = ((x921 < 0) & (x921.shift(3) > 0)).astype(float)
    x50 = np.sign(e50 - e200)
    f[f'{tf}_golden10'] = ((x50 > 0) & (x50.shift(10) < 0)).astype(float)
    f[f'{tf}_death10'] = ((x50 < 0) & (x50.shift(10) > 0)).astype(float)
    f[f'{tf}_stack_bull'] = ((B.ema(c, 8) > e21) & (e21 > e50) & (e50 > e200)).astype(float)
    f[f'{tf}_stack_bear'] = ((B.ema(c, 8) < e21) & (e21 < e50) & (e50 < e200)).astype(float)
    for n, e in ((21, e21), (50, e50), (200, e200)):
        f[f'{tf}_above_ema{n}'] = (c > e).astype(float)
    body = (c - o).abs()
    rng = (h - l).replace(0, np.nan)
    up_w = h - np.maximum(c, o)
    lo_w = np.minimum(c, o) - l
    f[f'{tf}_hammer'] = ((lo_w >= 2 * body) & (up_w <= 0.3 * rng)).astype(float)
    f[f'{tf}_invhammer'] = ((up_w >= 2 * body) & (lo_w <= 0.3 * rng)).astype(float)
    f[f'{tf}_engulf_up'] = ((c > o) & (c.shift() < o.shift()) & (c >= o.shift()) & (o <= c.shift())).astype(float)
    f[f'{tf}_engulf_dn'] = ((c < o) & (c.shift() > o.shift()) & (c <= o.shift()) & (o >= c.shift())).astype(float)
    f[f'{tf}_doji'] = (body <= 0.1 * rng).astype(float)
    f[f'{tf}_inside'] = ((h <= h.shift()) & (l >= l.shift())).astype(float)
    f[f'{tf}_outside'] = ((h > h.shift()) & (l < l.shift())).astype(float)
    up3 = (c > o) & (c.shift() > o.shift()) & (c.shift(2) > o.shift(2)) & (c > c.shift()) & (c.shift() > c.shift(2))
    dn3 = (c < o) & (c.shift() < o.shift()) & (c.shift(2) < o.shift(2)) & (c < c.shift()) & (c.shift() < c.shift(2))
    f[f'{tf}_3soldiers'], f[f'{tf}_3crows'] = up3.astype(float), dn3.astype(float)
    small = (c.shift() - o.shift()).abs() <= 0.3 * (h.shift() - l.shift())
    f[f'{tf}_morningstar'] = ((c.shift(2) < o.shift(2)) & small & (c > o) & (c > (o.shift(2) + c.shift(2)) / 2)).astype(float)
    f[f'{tf}_eveningstar'] = ((c.shift(2) > o.shift(2)) & small & (c < o) & (c < (o.shift(2) + c.shift(2)) / 2)).astype(float)
    r = h - l
    f[f'{tf}_nr4'] = (r <= r.rolling(4).min()).astype(float)
    f[f'{tf}_nr7'] = (r <= r.rolling(7).min()).astype(float)
    hh_i = h.rolling(26).apply(np.argmax, raw=True)
    ll_i = l.rolling(26).apply(np.argmin, raw=True)
    f[f'{tf}_aroon_up70'] = ((100 * hh_i / 25) > 70).astype(float)
    f[f'{tf}_aroon_dn70'] = ((100 * ll_i / 25) > 70).astype(float)
    tp = (h + l + c) / 3
    md = tp.rolling(20).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    cci = (tp - tp.rolling(20).mean()) / (0.015 * md)
    f[f'{tf}_cci_hi'], f[f'{tf}_cci_lo'] = (cci > 100).astype(float), (cci < -100).astype(float)
    wr = -100 * (h.rolling(14).max() - c) / (h.rolling(14).max() - l.rolling(14).min()).replace(0, np.nan)
    f[f'{tf}_wr_hi'], f[f'{tf}_wr_lo'] = (wr > -20).astype(float), (wr < -80).astype(float)
    rsi = B.rsi(c, 14)
    srsi = (rsi - rsi.rolling(14).min()) / (rsi.rolling(14).max() - rsi.rolling(14).min()).replace(0, np.nan)
    f[f'{tf}_stochrsi_hi'], f[f'{tf}_stochrsi_lo'] = (srsi > 0.8).astype(float), (srsi < 0.2).astype(float)
    tr = np.maximum(h - l, np.maximum((h - c.shift()).abs(), (l - c.shift()).abs()))
    vp = (h - l.shift()).abs().rolling(14).sum() / tr.rolling(14).sum()
    vm = (l - h.shift()).abs().rolling(14).sum() / tr.rolling(14).sum()
    f[f'{tf}_vortex_bull'] = (vp > vm).astype(float)
    trix = B.ema(B.ema(B.ema(c, 15), 15), 15).pct_change(fill_method=None)
    f[f'{tf}_trix_pos'] = (trix > 0).astype(float)
    bp = c - np.minimum(l, c.shift())
    trr = np.maximum(h, c.shift()) - np.minimum(l, c.shift())
    a7, a14, a28 = (bp.rolling(n).sum() / trr.rolling(n).sum() for n in (7, 14, 28))
    uo = 100 * (4 * a7 + 2 * a14 + a28) / 7
    f[f'{tf}_uo_hi'], f[f'{tf}_uo_lo'] = (uo > 70).astype(float), (uo < 30).astype(float)
    m, sd = c.rolling(20).mean(), c.rolling(20).std()
    atr = B.atr(b, 20)
    f[f'{tf}_squeeze'] = (((m + 2 * sd) < (B.ema(c, 20) + 1.5 * atr)) & ((m - 2 * sd) > (B.ema(c, 20) - 1.5 * atr))).astype(float)
    return f


def load_dix() -> pd.DataFrame | None:
    if not DIX_FILE.exists():
        return None
    d = pd.read_csv(DIX_FILE, parse_dates=['date'])
    # yayın: kapanıştan sonra → d günü değeri d+1 günü 09:30 ET'den itibaren kullanılabilir (korumacı)
    avail = (d.date + pd.Timedelta(days=1, hours=9, minutes=30)).dt.tz_localize(NY).dt.tz_convert('UTC')
    d['avail'] = avail.astype('int64') // 10**9
    d['gex_neg'] = (d.gex < 0).astype(float)
    d['dix_z'] = (d.dix - d.dix.rolling(60).mean()) / d.dix.rolling(60).std()
    d['gex_z'] = (d.gex - d.gex.rolling(60).mean()) / d.gex.rolling(60).std()
    return d.sort_values('avail').reset_index(drop=True)


def calendar_flags(td: np.ndarray) -> pd.DataFrame:
    ny = pd.to_datetime(td, unit='s', utc=True).tz_convert(NY).tz_localize(None)
    dates = ny.normalize()
    out = pd.DataFrame(index=range(len(td)))
    # opsiyon vade haftası: ayın 3. Cuma'sını içeren Pzt–Cum
    third_fri = dates.to_period('M').to_timestamp() + pd.to_timedelta(((4 - dates.to_period('M').to_timestamp().dayofweek) % 7) + 14, 'D')
    out['opex_week'] = ((dates >= third_fri - pd.Timedelta(days=4)) & (dates <= third_fri)).astype(float)
    qend = dates.month.isin([3, 6, 9, 12]) & (dates.day >= (dates.days_in_month - 6))
    out['quarter_end_week'] = qend.astype(float)
    nxt = dates + pd.Timedelta(days=1)
    nxt = nxt + pd.to_timedelta(np.where(nxt.dayofweek == 5, 2, 0), 'D')
    out['pre_holiday'] = np.array([CAL.is_holiday(x.date()) or CAL.is_early_close(x.date()) for x in nxt], float)
    return out


def build_extras(b1: pd.DataFrame, td: np.ndarray) -> pd.DataFrame:
    parts = []
    for tf in ('M15', 'H1', 'D1'):
        bb = B.resample(b1, tf)
        f = _ind(bb, tf)
        parts.append(B.asof_map(td, bb.end.to_numpy(), f))
    out = pd.concat(parts, axis=1)
    out = pd.concat([out, calendar_flags(td)], axis=1)
    dx = load_dix()
    if dx is not None:
        mp = B.asof_map(td, dx.avail.to_numpy(), dx[['gex_neg', 'dix_z', 'gex_z', 'dix', 'gex']])
        out['gex_neg'] = mp.gex_neg.to_numpy()
        out['dix_z_hi'] = (mp.dix_z.to_numpy() > 1).astype(float)
        out['dix_z_lo'] = (mp.dix_z.to_numpy() < -1).astype(float)
        out['gex_z_lo'] = (mp.gex_z.to_numpy() < -1).astype(float)
        out['_dix'] = mp.dix.to_numpy()
        out['_gex'] = mp.gex.to_numpy()
    return out
