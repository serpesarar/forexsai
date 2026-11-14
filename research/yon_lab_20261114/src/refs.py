"""Referans katalogu (PROTOCOL §5): her ızgara noktasında, yalnız KAPANMIŞ barlardan seviyeler.

`build_refs(b, td, i1)` → dict: üye_adı → seviye dizisi [N] ve aile → üye listesi. HTF değerleri `bars.asof_map`
(end ≤ t_dec) ile; gün-içi kümülatifler son kapanmış 1m barda; pivotlar k bar sonra teyit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import core as C
from services.nom import bars as B

NY = C.NY
PIV_K = (2, 3, 5, 8)
PIV_LAST = 48
PIV_LOOKBACK_S = {'M15': 5 * 86400, 'H1': 20 * 86400, 'H4': 60 * 86400}


def _sma(c: pd.Series, n: int) -> pd.Series:
    return c.rolling(n, min_periods=n).mean()


def _supertrend(b: pd.DataFrame, n: int = 10, mult: float = 3.0) -> np.ndarray:
    a = B.atr(b, n).to_numpy()
    hl2 = ((b.h + b.l) / 2).to_numpy()
    c = b.c.to_numpy()
    up, dn = hl2 - mult * a, hl2 + mult * a
    st = np.full(len(c), np.nan)
    trend = 1
    fu, fd = up[0], dn[0]
    for i in range(1, len(c)):
        fu = max(up[i], fu) if c[i - 1] > fu else up[i]
        fd = min(dn[i], fd) if c[i - 1] < fd else dn[i]
        if c[i] > fd:
            trend = 1
        elif c[i] < fu:
            trend = -1
        st[i] = fu if trend == 1 else fd
    return st


def _tf_levels(b: pd.DataFrame, tf: str) -> pd.DataFrame:
    c = b.c
    a = B.atr(b, 14)
    f = pd.DataFrame(index=b.index)
    emas = {'M5': (9, 21, 50, 100, 200), 'M15': (9, 21, 50, 100, 200), 'H1': (9, 21, 50, 100, 200),
            'H4': (9, 21, 50, 100, 200), 'D1': (20, 50, 200)}[tf]
    for n in emas:
        f[f'EMA{n}_{tf}'] = B.ema(c, n)
    if tf in ('M15', 'H1', 'D1'):
        for n in (20, 50, 200):
            f[f'SMA{n}_{tf}'] = _sma(c, n)
    if tf in ('M15', 'H1', 'H4'):
        m, sd = _sma(c, 20), c.rolling(20, min_periods=20).std()
        f[f'BBU_{tf}'], f[f'BBL_{tf}'] = m + 2 * sd, m - 2 * sd
    if tf in ('M15', 'H1'):
        e = B.ema(c, 20)
        f[f'KCU_{tf}'], f[f'KCL_{tf}'] = e + 2 * a, e - 2 * a
        f[f'ST_{tf}'] = _supertrend(b)
    if tf in ('M15', 'H1', 'H4', 'D1'):
        f[f'DONU_{tf}'] = b.h.rolling(20, min_periods=20).max()
        f[f'DONL_{tf}'] = b.l.rolling(20, min_periods=20).min()
    if tf in ('H1', 'H4'):
        ten = (b.h.rolling(9).max() + b.l.rolling(9).min()) / 2
        kij = (b.h.rolling(26).max() + b.l.rolling(26).min()) / 2
        sa = ((ten + kij) / 2).shift(26)
        sb = ((b.h.rolling(52).max() + b.l.rolling(52).min()) / 2).shift(26)
        f[f'TENKAN_{tf}'], f[f'KIJUN_{tf}'], f[f'SENA_{tf}'], f[f'SENB_{tf}'] = ten, kij, sa, sb
    if tf == 'H1':
        f['SAR_H1'] = B.psar(b)[:, 1]
    return f


FAMILY_OF = [('EMA', 'EMA'), ('SMA', 'SMA'), ('BB', 'BB'), ('KC', 'KC'), ('DON', 'DON'), ('TENKAN', 'ICHI'),
             ('KIJUN', 'ICHI'), ('SENA', 'ICHI'), ('SENB', 'ICHI'), ('SAR', 'TRD'), ('ST', 'TRD'), ('TWAP', 'TWAP'),
             ('PIV', 'PIV'), ('CAL', 'CAL'), ('RND', 'RND'), ('FIB', 'FIB')]


def family(name: str) -> str:
    for pre, fam in FAMILY_OF:
        if name.startswith(pre):
            return fam
    raise KeyError(name)


def _pivots(b: pd.DataFrame, k: int) -> pd.DataFrame:
    w = 2 * k + 1
    ph = b.h == b.h.rolling(w, center=True, min_periods=w).max()
    pl = b.l == b.l.rolling(w, center=True, min_periods=w).min()
    conf = b.end.shift(-k)
    rows = []
    for m, lv, ty in ((ph, b.h, 1.0), (pl, b.l, -1.0)):
        s = m & conf.notna()
        rows.append(pd.DataFrame({'conf': conf[s].astype('int64'), 'tb': b.end[s].astype('int64'),
                                  'lvl': lv[s].astype(float), 'typ': ty}))
    return pd.concat(rows).sort_values(['conf', 'tb']).reset_index(drop=True)


def _pivot_matrix(p: pd.DataFrame, td: np.ndarray, lookback: int) -> np.ndarray:
    e = np.searchsorted(p.conf.to_numpy(), td, side='right')
    idx = e[:, None] - PIV_LAST + np.arange(PIV_LAST)[None, :]
    ok = idx >= 0
    idc = np.clip(idx, 0, max(len(p) - 1, 0))
    lv = np.where(ok, p.lvl.to_numpy()[idc], np.nan)
    tb = np.where(ok, p.tb.to_numpy()[idc], 0)
    lv[tb < td[:, None] - lookback] = np.nan
    return lv


def _fib(p: pd.DataFrame, td: np.ndarray) -> dict:
    """Son teyitli H1 (k=5) tepe ve dip: son pivot tepeyse salınım yukarı (dip→tepe)."""
    hi = p[p.typ == 1]
    lo = p[p.typ == -1]
    eh = np.searchsorted(hi.conf.to_numpy(), td, side='right') - 1
    el = np.searchsorted(lo.conf.to_numpy(), td, side='right') - 1
    H_ = np.where(eh >= 0, hi.lvl.to_numpy()[np.clip(eh, 0, None)], np.nan)
    L_ = np.where(el >= 0, lo.lvl.to_numpy()[np.clip(el, 0, None)], np.nan)
    th = np.where(eh >= 0, hi.tb.to_numpy()[np.clip(eh, 0, None)], 0)
    tl = np.where(el >= 0, lo.tb.to_numpy()[np.clip(el, 0, None)], 0)
    upmove = th > tl
    rng = H_ - L_
    out = {}
    for r in (0.382, 0.5, 0.618):
        out[f'FIB_R{int(r * 1000)}'] = np.where(upmove, H_ - r * rng, L_ + r * rng)
    for e in (1.272, 1.618):
        out[f'FIB_X{int(e * 1000)}'] = np.where(upmove, L_ + e * rng, H_ - e * rng)
    return out


def _intraday(b1: pd.DataFrame, i1: np.ndarray, td: np.ndarray) -> dict:
    t = b1.t.to_numpy()
    ny = pd.to_datetime(t, unit='s', utc=True).tz_convert(NY).tz_localize(None)
    mod = (ny.hour * 60 + ny.minute).to_numpy()
    cash_day = ny.normalize().asi8
    sess = (ny - pd.Timedelta(hours=18)).normalize().asi8
    sh = (ny - pd.Timedelta(hours=18)).normalize()
    wk = (sh - pd.to_timedelta((sh.dayofweek + 1) % 7, 'D')).asi8        # hafta = Pazar 18:00 ET başlangıçlı CFD haftası
    tp = ((b1.high + b1.low + b1.close) / 3).to_numpy()
    in_cash = (mod >= 570) & (mod < 960)
    out = {}
    for name, key, valid in (('TWAP_CASH', np.where(in_cash, cash_day, -1), in_cash),
                             ('TWAP_SESS', sess, np.ones(len(t), bool)), ('TWAP_WEEK', wk, np.ones(len(t), bool))):
        s = pd.Series(tp).groupby(key)
        cs, cn, cs2 = s.cumsum().to_numpy(), (s.cumcount() + 1).to_numpy(), pd.Series(tp ** 2).groupby(key).cumsum().to_numpy()
        m = cs / cn
        sd = np.sqrt(np.maximum(cs2 / cn - m ** 2, 0))
        ok = valid[i1] & (cn[i1] >= 15)
        mm, ss = np.where(ok, m[i1], np.nan), np.where(ok, sd[i1], np.nan)
        out[name] = mm
        for k in (1, 2):
            out[f'{name}_P{k}'] = mm + k * ss
            out[f'{name}_M{k}'] = mm - k * ss
    # ORB 15/30/60, nakit açılış
    g = pd.DataFrame({'k': np.where(in_cash, cash_day, -1), 'h': b1.high.to_numpy(), 'l': b1.low.to_numpy(),
                      'o': b1.open.to_numpy(), 'mod': mod})
    for m_ in (15, 30, 60):
        w = in_cash & (mod < 570 + m_)
        hh = pd.Series(np.where(w, g.h, np.nan)).groupby(g.k).cummax().groupby(g.k).ffill().to_numpy()
        ll = pd.Series(np.where(w, g.l, np.nan)).groupby(g.k).cummin().groupby(g.k).ffill().to_numpy()
        done = in_cash[i1] & (mod[i1] >= 570 + m_ - 1)
        out[f'CAL_ORB{m_}H'] = np.where(done, hh[i1], np.nan)
        out[f'CAL_ORB{m_}L'] = np.where(done, ll[i1], np.nan)
    co = pd.Series(np.where(in_cash, g.o, np.nan)).groupby(g.k).transform('first').to_numpy()
    out['CAL_CASHOPEN'] = np.where(in_cash[i1], co[i1], np.nan)
    pre = (~in_cash & (mod < 570)) | (mod >= 1080)
    onh = pd.Series(np.where(pre, b1.high, np.nan)).groupby(sess).cummax().groupby(sess).ffill().to_numpy()
    onl = pd.Series(np.where(pre, b1.low, np.nan)).groupby(sess).cummin().groupby(sess).ffill().to_numpy()
    out['CAL_ONH'], out['CAL_ONL'] = onh[i1], onl[i1]
    wo = pd.Series(b1.open.to_numpy()).groupby(wk).transform('first').to_numpy()
    out['CAL_WEEKOPEN'] = wo[i1]
    return out


def build_refs(b1: pd.DataFrame, td: np.ndarray, i1: np.ndarray) -> pd.DataFrame:
    cols: dict[str, np.ndarray] = {}
    tfb = {}
    for tf in ('M5', 'M15', 'H1', 'H4', 'D1'):
        bb = B.resample(b1, tf)
        tfb[tf] = bb
        lv = _tf_levels(bb, tf)
        mp = B.asof_map(td, bb.end.to_numpy(), lv)
        for c in mp.columns:
            cols[c] = mp[c].to_numpy()
    d1 = tfb['D1']
    mp = B.asof_map(td, d1.end.to_numpy(), d1[['o', 'h', 'l', 'c']])
    cols['CAL_PDO'], cols['CAL_PDH'], cols['CAL_PDL'], cols['CAL_PDC'] = (mp[x].to_numpy() for x in 'ohlc')
    # önceki hafta / ay (D1 seanslarından; tamamlanmış dönem)
    dts = (pd.to_datetime(d1.key, unit='s', utc=True).dt.tz_convert(NY).dt.tz_localize(None) + pd.Timedelta(hours=6)).dt   # işlem günü tarihi
    for name, per in (('W', dts.to_period('W-FRI')), ('MO', dts.to_period('M'))):
        g = d1.assign(per=per.astype(str)).groupby('per', sort=False).agg(h=('h', 'max'), l=('l', 'min'))
        # dönem sonu takvimden (kesme eşdeğerliği için veriden DEĞİL): hafta → Cuma 17:00 ET, ay → ayın son günü 17:00 ET
        pe = pd.PeriodIndex(g.index, freq='W-FRI' if name == 'W' else 'M').end_time.normalize() + pd.Timedelta(hours=17)
        g['end'] = pe.tz_localize(NY).tz_convert('UTC').asi8 // 10**9
        g = g.sort_values('end')
        mp = B.asof_map(td, g.end.to_numpy(), g[['h', 'l']].reset_index(drop=True))
        # son tamamlanmış dönem: end ≤ t; içinde bulunulan dönemin end'i ilerde olduğundan otomatik dışarıda
        cols[f'CAL_P{name}H'], cols[f'CAL_P{name}L'] = mp.h.to_numpy(), mp.l.to_numpy()
    cols.update(_intraday(b1, i1, td))
    for tf in ('M15', 'H1', 'H4'):
        for k in PIV_K:
            pv = _pivots(tfb[tf], k)
            M = _pivot_matrix(pv, td, PIV_LOOKBACK_S[tf])
            for j in range(PIV_LAST):
                cols[f'PIV_{tf}_k{k}_{j}'] = M[:, j]
            if tf == 'H1' and k == 5:
                cols.update(_fib(pv, td))
    price = b1.close.to_numpy()[i1]
    for step in (50, 100, 250, 500, 1000):
        cols[f'RND{step}_U'] = np.ceil(price / step) * step
        cols[f'RND{step}_D'] = np.floor(price / step) * step
    return pd.DataFrame(cols)


def member_groups(cols: list[str]) -> dict[str, list[str]]:
    fam: dict[str, list[str]] = {}
    for c in cols:
        fam.setdefault(family(c), []).append(c)
    return fam


def single_members(cols: list[str]) -> list[str]:
    """Atlas alt-üyeleri: tek seviyeli seriler (pivot matris sütunları hariç; pivotlar aile düzeyinde)."""
    return [c for c in cols if not c.startswith('PIV_')]


def nearest(R: pd.DataFrame, cols: list[str], price: np.ndarray, atr: np.ndarray, lo: float = 0.05, hi: float = 3.0):
    """Aile içinde en yakın üst/alt seviye uzaklığı (ATR) ve seviye adı indeksi."""
    M = R[cols].to_numpy(dtype=float)
    d = (M - price[:, None]) / atr[:, None]
    up = np.where((d >= lo) & (d <= hi), d, np.inf)
    dn = np.where((-d >= lo) & (-d <= hi), -d, np.inf)
    U, D = up.min(1), dn.min(1)
    return np.where(np.isfinite(U), U, np.nan), np.where(np.isfinite(D), D, np.nan), up.argmin(1), dn.argmin(1)
