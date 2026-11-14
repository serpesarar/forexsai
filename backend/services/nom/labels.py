"""NOM — Triple-Barrier etiketleri (bid/ask yolu, sürtünme dahil, aynı-bar → SL).

Hem araştırma (Faz 1) hem canlı sonuç notlaması (Faz 8) bu fonksiyonu kullanır.
Birim: R = SL mesafesi (SL·A). Giriş fiyatı sürtünme dahil gerçek dolum; bariyerler dolumdan ölçülür.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SLIP_PTS = 1.0
CLASS_TP, CLASS_SL, CLASS_TO = 0, 1, 2
WEEKEND_GAP_S = 6 * 3600          # pencere içinde > 6 saat boşluk → hafta sonu/tatil: etiket yok
MIN_COVER = 0.5                   # pencerede beklenen açık dakikaların en az yarısı
GEOMETRIES: tuple[tuple[float, float], ...] = ((1.0, 1.0), (1.5, 1.0), (2.0, 1.0), (1.0, 1.5), (1.5, 1.5))
HORIZONS: dict[str, dict] = {
    '15m': {'minutes': 15, 'atr_tf': 'M5', 'grid_s': 300},
    '1h': {'minutes': 60, 'atr_tf': 'M15', 'grid_s': 300},
    '4h': {'minutes': 240, 'atr_tf': 'H1', 'grid_s': 900},
    'session': {'minutes': None, 'atr_tf': 'H1', 'grid_s': 900},
}


def geom_key(tp: float, sl: float) -> str:
    return f'{tp:g}x{sl:g}'


@dataclass
class Path1m:
    t: np.ndarray        # açılış epoch sn (artan)
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    spr: np.ndarray      # bar başı ask−bid (puan)


def _window(p: Path1m, i0: np.ndarray, t_end: np.ndarray, wmax: int):
    """i0: giriş barı indeksleri; t_end: ufuk sonu (hariç). Dönen [N, W] indeks matrisi + maske + geçerlilik."""
    n = len(p.t)
    J = i0[:, None] + np.arange(wmax)[None, :]
    inb = J < n
    Jc = np.where(inb, J, n - 1)
    tt = p.t[Jc]
    m = inb & (tt < t_end[:, None])
    # hafta sonu boşluğu: pencere içinde ardışık barlar arası > 6 s
    dt = np.diff(tt, axis=1)
    gap = np.zeros_like(m)
    gap[:, 1:] = (dt > WEEKEND_GAP_S) & m[:, 1:]
    bad_gap = gap.any(axis=1)
    return Jc, m, bad_gap


def label_batch(p: Path1m, i0: np.ndarray, atr_val: np.ndarray, t_end: np.ndarray, geoms=GEOMETRIES,
                expected_min: np.ndarray | None = None, wmax: int | None = None) -> dict:
    """Bir karar kümesi için tüm geometrilerde LONG ve SHORT etiketleri.

    Dönen sözlük: valid [N] bool ve her (yön, geom) için cls [N] int8, r [N] float32, tbar [N] int16
    (çözüm barı sırası; TO = −1).
    """
    i0 = np.asarray(i0, dtype='int64')
    N = len(i0)
    if wmax is None:
        wmax = int(max(1, np.ceil((t_end - p.t[i0]).max() / 60))) + 1
    Jc, m, bad_gap = _window(p, i0, t_end, wmax)
    nbars = m.sum(axis=1)
    exp = expected_min if expected_min is not None else (t_end - p.t[i0]) / 60.0
    valid = (~bad_gap) & (nbars >= MIN_COVER * exp) & np.isfinite(atr_val) & (atr_val > 0) & (nbars > 0)
    O, Hh, L, C, S = p.o[Jc], p.h[Jc], p.l[Jc], p.c[Jc], p.spr[Jc]
    last = np.maximum(nbars - 1, 0)
    rows = np.arange(N)
    c_last_bid = C[rows, last]
    s_last = S[rows, last]
    entry_long = O[:, 0] + S[:, 0] + SLIP_PTS
    entry_short = O[:, 0] - SLIP_PTS
    out: dict = {'valid': valid, 'nbars': nbars.astype('int16')}
    big = np.int64(10**6)
    for tp, sl in geoms:
        A = atr_val
        sd = sl * A
        gk = geom_key(tp, sl)
        # LONG — bid yolu
        tpl = entry_long + tp * A
        sll = entry_long - sd
        hit_tp = (Hh >= tpl[:, None]) & m
        hit_sl = (L <= sll[:, None]) & m
        ftp = np.where(hit_tp.any(1), hit_tp.argmax(1), big)
        fsl = np.where(hit_sl.any(1), hit_sl.argmax(1), big)
        cls = np.full(N, CLASS_TO, dtype='int8')
        cls[(fsl <= ftp) & (fsl < big)] = CLASS_SL         # aynı bar → SL
        cls[(ftp < fsl)] = CLASS_TP
        k_sl = np.minimum(fsl, wmax - 1)
        o_sl = O[rows, k_sl]
        sl_fill = np.minimum(sll, o_sl) - SLIP_PTS          # boşluk dolumu + kayma
        r = np.where(cls == CLASS_TP, tp / sl,
                     np.where(cls == CLASS_SL, (sl_fill - entry_long) / sd,
                              (c_last_bid - SLIP_PTS - entry_long) / sd))
        out[('long', gk, 'cls')] = np.where(valid, cls, -1).astype('int8')
        out[('long', gk, 'r')] = np.where(valid, r, np.nan).astype('float32')
        out[('long', gk, 'tbar')] = np.where(cls == CLASS_TP, ftp, np.where(cls == CLASS_SL, fsl, -1)).astype('int32')
        out[('long', gk, 'amb')] = ((ftp == fsl) & (fsl < big) & valid).astype('int8')
        # SHORT — ask yolu (bid + spr)
        tps = entry_short - tp * A
        sls = entry_short + sd
        hit_tp = ((L + S) <= tps[:, None]) & m
        hit_sl = ((Hh + S) >= sls[:, None]) & m
        ftp = np.where(hit_tp.any(1), hit_tp.argmax(1), big)
        fsl = np.where(hit_sl.any(1), hit_sl.argmax(1), big)
        cls = np.full(N, CLASS_TO, dtype='int8')
        cls[(fsl <= ftp) & (fsl < big)] = CLASS_SL
        cls[(ftp < fsl)] = CLASS_TP
        k_sl = np.minimum(fsl, wmax - 1)
        o_sl_ask = O[rows, k_sl] + S[rows, k_sl]
        sl_fill = np.maximum(sls, o_sl_ask) + SLIP_PTS
        r = np.where(cls == CLASS_TP, tp / sl,
                     np.where(cls == CLASS_SL, (entry_short - sl_fill) / sd,
                              (entry_short - (c_last_bid + s_last + SLIP_PTS)) / sd))
        out[('short', gk, 'cls')] = np.where(valid, cls, -1).astype('int8')
        out[('short', gk, 'r')] = np.where(valid, r, np.nan).astype('float32')
        out[('short', gk, 'tbar')] = np.where(cls == CLASS_TP, ftp, np.where(cls == CLASS_SL, fsl, -1)).astype('int32')
        out[('short', gk, 'amb')] = ((ftp == fsl) & (fsl < big) & valid).astype('int8')
    return out


def label_frame(p: Path1m, i0: np.ndarray, atr_val: np.ndarray, t_end: np.ndarray, chunk: int = 20000, **kw):
    """Büyük kümeler için parça parça label_batch; pandas DataFrame döner (sütun: <yön>_<geom>_<alan>)."""
    import pandas as pd
    parts = []
    for s in range(0, len(i0), chunk):
        sl_ = slice(s, s + chunk)
        exp = kw.get('expected_min')
        d = label_batch(p, i0[sl_], atr_val[sl_], t_end[sl_],
                        expected_min=None if exp is None else exp[sl_],
                        geoms=kw.get('geoms', GEOMETRIES))
        cols = {}
        for k, v in d.items():
            cols[k if isinstance(k, str) else f'{k[0]}_{k[1]}_{k[2]}'] = v
        parts.append(pd.DataFrame(cols))
    return pd.concat(parts, ignore_index=True)
