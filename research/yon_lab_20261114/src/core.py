"""Yön Lab çekirdeği: ızgara, ATR, eşleme kovaları, etiketler, ilk-geçiş tabloları, martingal piyasa üretici.

İlk-geçiş tabloları (FU/FD): her ızgara noktasında p_t'den u_k = k·0,05·ATR(H1) (k = 1…60) yukarı/aşağı seviyeye ilk değme
dakikası (8 saat pencere, hafta sonu boşluğu kesilir; değmezse NOHIT). Gerçek referans yarışı, hayalet yarışı ve simetrik
yarış aynı tablodan okunur → gerçek ile hayalet aynı ölçüm yoluyla, yalnız seviyenin "gerçek" olup olmamasıyla ayrışır.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(REPO / 'backend'))
from services.nom import features as FE  # noqa: E402

NY = 'America/New_York'
GRID_S = 900
STEP_ATR = 0.05
NK = 60                      # 0,05 … 3,00 ATR
WIN_MIN = 480
GAP_S = 6 * 3600
NOHIT = np.int16(32000)
KESIF = ('2021-11-01', '2024-07-01')
DOGRU = ('2024-07-01', '2026-01-01')
KOR = ('2026-01-01', '2027-01-01')
WARM_DAYS = 30
HORIZONS = {'15m': 15, '1h': 60, '4h': 240}


def ts(s: str) -> int:
    return int(pd.Timestamp(s, tz='UTC').timestamp())


def load_ndx() -> pd.DataFrame:
    return pd.read_parquet(H / 'data/ndx_1m_v2.parquet')[['t', 'open', 'high', 'low', 'close']]


def load_macro():
    m = pd.read_parquet(REPO / 'research/nom_20261113/data/macro/macro_daily.parquet')
    c = pd.read_parquet(REPO / 'research/nom_20261113/data/macro/calendar.parquet')
    return m, c


def grid(b: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """t_dec (karar anı) ve i1 (son kapanmış 1m bar indeksi). Isınma: verinin ilk 30 günü yok."""
    t = b.t.to_numpy()
    cand = t + 60
    ok = (cand % GRID_S == 0) & (cand >= t[0] + WARM_DAYS * 86400)
    i1 = np.where(ok)[0]
    nxt = np.r_[t[1:], t[-1] + 10**9]
    i1 = i1[(nxt[i1] - (t[i1] + 60)) < 6 * 3600]          # sonrası var (hafta sonu öncesi son nokta da dahil)
    return t[i1] + 60, i1


def period(td: np.ndarray) -> np.ndarray:
    out = np.full(len(td), 'X', dtype=object)
    for name, (a, b) in (('K', KESIF), ('D', DOGRU), ('T', KOR)):
        out[(td >= ts(a)) & (td < ts(b))] = name
    # etiket penceresi dönem sınırını geçmesin: her dönemin son 1 günü dışarı (göstergeler geçmişi kullanabilir)
    for a, b in (KESIF, DOGRU, KOR):
        out[(td >= ts(b) - 86400) & (td < ts(b))] = 'X'
    return out


def half_year(td: np.ndarray) -> np.ndarray:
    d = pd.to_datetime(td, unit='s', utc=True)
    return (d.year * 2 + (d.month > 6)).to_numpy()


def ny_hour(td: np.ndarray) -> np.ndarray:
    return pd.to_datetime(td, unit='s', utc=True).tz_convert(NY).hour.to_numpy()


def strata(td: np.ndarray, volr: np.ndarray, edges: np.ndarray) -> np.ndarray:
    vd = np.searchsorted(edges, np.nan_to_num(volr, nan=np.nanmedian(volr)))
    return (half_year(td) * 1000 + ny_hour(td) * 10 + vd).astype(np.int64)


def first_hit_tables(b: pd.DataFrame, td: np.ndarray, i1: np.ndarray, atr: np.ndarray, chunk: int = 3000):
    """FU, FD: [N, NK] int16 dakika (1 = sonraki ilk bar). Pencere 8 s, >6 s boşlukta kesilir."""
    t, hi, lo = b.t.to_numpy(), b.high.to_numpy(), b.low.to_numpy()
    p = b.close.to_numpy()[i1]
    n = len(t)
    N = len(i1)
    FU = np.full((N, NK), NOHIT, dtype=np.int16)
    FD = np.full((N, NK), NOHIT, dtype=np.int16)
    lev = (np.arange(1, NK + 1) * STEP_ATR)[None, :]
    for s in range(0, N, chunk):
        I = i1[s:s + chunk]
        J = I[:, None] + 1 + np.arange(WIN_MIN)[None, :]
        inb = J < n
        Jc = np.where(inb, J, n - 1)
        tt = t[Jc]
        ok = inb & (tt < (td[s:s + chunk, None] + WIN_MIN * 60))
        gap = np.zeros_like(ok)
        gap[:, 1:] = np.diff(tt, axis=1) > GAP_S
        ok &= ~np.maximum.accumulate(gap, axis=1)
        mins = ((tt - td[s:s + chunk, None]) // 60 + 1).astype(np.int32)
        A = atr[s:s + chunk, None]
        up = np.maximum.accumulate(np.where(ok, hi[Jc], -np.inf), axis=1) - p[s:s + chunk, None]
        dn = p[s:s + chunk, None] - np.minimum.accumulate(np.where(ok, lo[Jc], np.inf), axis=1)
        for M, X in ((up, FU), (dn, FD)):
            hit = M[:, :, None] >= (lev * A)[:, None, :]           # [c, W, NK], W ekseninde monoton
            anyh = hit[:, -1, :]
            first = hit.argmax(axis=1)
            mm = np.take_along_axis(mins, first, axis=1)
            X[s:s + chunk] = np.where(anyh, np.minimum(mm, 32000), NOHIT).astype(np.int16)
    return FU, FD


def dir_labels(b: pd.DataFrame, td: np.ndarray, i1: np.ndarray) -> dict:
    t, c = b.t.to_numpy(), b.close.to_numpy()
    p = c[i1]
    out = {}
    for name, m in HORIZONS.items():
        j = np.searchsorted(t, td + m * 60 - 60, side='right') - 1     # ufuk sonundan önce kapanan son bar
        ok = (j > i1) & (t[np.clip(j, 0, None)] >= td + m * 60 - 60 - 300) & ((t[np.clip(j, 0, None)] - t[i1]) < m * 60 + GAP_S)
        out[f'dir_{name}'] = np.where(ok, np.sign(c[j] - p), np.nan)
        out[f'mag_{name}'] = np.where(ok, c[j] - p, np.nan)
    ny = pd.to_datetime(td, unit='s', utc=True).tz_convert(NY)
    mod = (ny.hour * 60 + ny.minute).to_numpy()
    day0 = (ny.tz_localize(None).normalize().tz_localize(NY).tz_convert('UTC').asi8 // 10**9)
    te = day0 + 960 * 60
    sess = (mod >= 570) & (mod <= 930) & (ny.dayofweek.to_numpy() < 5)
    j = np.searchsorted(t, te - 60, side='right') - 1
    ok = sess & (j > i1) & (t[np.clip(j, 0, None)] >= te - 60 - 900) & (t[np.clip(j, 0, None)] < te)
    out['dir_sess'] = np.where(ok, np.sign(c[j] - p), np.nan)
    out['mag_sess'] = np.where(ok, c[j] - p, np.nan)
    return out


def sym_race(b: pd.DataFrame, td: np.ndarray, i1: np.ndarray, atr: np.ndarray, minutes: int = 60, k: float = 1.0):
    """±k·ATR (verilen ATR) yarışı, `minutes` pencere: +1 yukarı önce, −1 aşağı önce, 0 çözülmedi, nan belirsiz (aynı bar)."""
    t, hi, lo = b.t.to_numpy(), b.high.to_numpy(), b.low.to_numpy()
    p = b.close.to_numpy()[i1]
    n = len(t)
    J = i1[:, None] + 1 + np.arange(minutes)[None, :]
    inb = J < n
    Jc = np.where(inb, J, n - 1)
    ok = inb & (t[Jc] < td[:, None] + minutes * 60)
    A = (k * atr)[:, None]
    hu = ok & (hi[Jc] >= p[:, None] + A)
    hd = ok & (lo[Jc] <= p[:, None] - A)
    big = 10**6
    fu = np.where(hu.any(1), hu.argmax(1), big)
    fd = np.where(hd.any(1), hd.argmax(1), big)
    out = np.where(fu < fd, 1.0, np.where(fd < fu, -1.0, 0.0))
    out[(fu == fd) & (fu < big)] = np.nan
    return out


def race_from_tables(FU, FD, ub: np.ndarray, db: np.ndarray, rows: np.ndarray | None = None) -> np.ndarray:
    """Satır başına (ub, db) kova indeksleriyle yarış: +1 üst önce, −1 alt önce, 0 çözülmedi, nan eşit."""
    r = np.arange(len(ub)) if rows is None else rows
    fu = FU[r, ub].astype(np.int32)
    fd = FD[r, db].astype(np.int32)
    out = np.where(fu < fd, 1.0, np.where(fd < fu, -1.0, 0.0))
    out[(fu == fd) & (fu < NOHIT)] = np.nan
    return out


def ghost_table(FU, FD, strat: np.ndarray, mask: np.ndarray, pairs: np.ndarray) -> dict:
    """Hayalet: kova (strat) içinde tüm noktaların (ub, db) yarışı ortalaması. pairs: benzersiz (ub, db) [P, 2].
    Dönen: {(ub, db): Series(strat → (yukarı_oranı_çözülende, çözülme_oranı, n))}."""
    out = {}
    sidx = strat[mask]
    for ub, db in pairs:
        r = race_from_tables(FU[mask], FD[mask], np.full(mask.sum(), ub), np.full(mask.sum(), db))
        df = pd.DataFrame({'s': sidx, 'up': (r == 1).astype(float), 'res': np.isin(r, (1, -1)).astype(float)})
        g = df.groupby('s').agg(up=('up', 'sum'), res=('res', 'sum'), n=('up', 'size'))
        out[(int(ub), int(db))] = g
    return out


def martingale_path(b: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Sıfır 4: 30 dk blokları, aynı NY yarım-saat dilimi × takvim yarıyılı içinde günler arası karıştırılır.
    Bar şekli (o/h/l'nin c'ye göre farkı) korunur; fiyat log getirilerin kümülatifinden yeniden kurulur."""
    rng = np.random.default_rng(seed)
    t = b.t.to_numpy()
    c = b.close.to_numpy()
    lr = np.diff(np.log(c), prepend=np.log(c[0]))
    lr[0] = 0.0
    oc = np.log(b.open.to_numpy() / c)
    hc = np.log(b.high.to_numpy() / c)
    lc = np.log(b.low.to_numpy() / c)
    ny = pd.to_datetime(t, unit='s', utc=True).tz_convert(NY)
    day = ny.tz_localize(None).normalize().asi8 // 10**9
    slot = (ny.hour * 2 + (ny.minute >= 30)).to_numpy()
    hy = (ny.year * 2 + (ny.month > 6)).to_numpy()
    key = pd.DataFrame({'d': day, 's': slot, 'h': hy})
    blk = key.groupby(['d', 's'], sort=False).ngroup().to_numpy()
    # blokları aynı (slot, yarıyıl) grubunda karıştır
    bk = key.assign(b=blk).drop_duplicates('b')
    perm = np.empty(blk.max() + 1, dtype=np.int64)
    for _, g in bk.groupby(['s', 'h']):
        ids = g.b.to_numpy()
        perm[ids] = rng.permutation(ids)
    order = np.argsort(blk, kind='stable')
    starts = np.r_[0, np.flatnonzero(np.diff(blk[order])) + 1]
    seg = {int(blk[order[s]]): order[s:e] for s, e in zip(starts, np.r_[starts[1:], len(order)])}
    new_lr, new_oc, new_hc, new_lc = lr.copy(), oc.copy(), hc.copy(), lc.copy()
    for tgt, src in enumerate(perm):
        a, s_ = seg.get(tgt), seg.get(int(src))
        if a is None or s_ is None:
            continue
        k = min(len(a), len(s_))
        new_lr[a[:k]] = lr[s_[:k]]
        new_oc[a[:k]] = oc[s_[:k]]
        new_hc[a[:k]] = hc[s_[:k]]
        new_lc[a[:k]] = lc[s_[:k]]
    lc_path = np.log(c[0]) + np.cumsum(new_lr)
    cc = np.exp(lc_path)
    o, h, l = cc * np.exp(new_oc), cc * np.exp(new_hc), cc * np.exp(new_lc)
    h = np.maximum.reduce([h, o, cc])
    l = np.minimum.reduce([l, o, cc])
    return pd.DataFrame({'t': t, 'open': o, 'high': h, 'low': l, 'close': cc})


def nom_features(b: pd.DataFrame, td: np.ndarray, mac, cal) -> pd.DataFrame:
    return FE.compute_features(b, td, mac, cal)
