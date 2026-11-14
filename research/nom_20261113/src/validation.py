"""NOM Faz 3 — doğrulama şeması (modelden ÖNCE kuruldu; PROTOCOL.md §D).

* Kilitli final test: FINAL_START → veri sonu. `assert_not_final` her eğitim/seçim çağrısında kontrol eder.
* Walk-forward (genişleyen pencere) + arındırma (etiket penceresi blok başını geçen satırlar atılır) + 1 gün ambargo.
* Purged K-Fold (López de Prado) — hiperparametre araması yapılmadığı için yalnız tutarlılık kontrolünde kullanılır.
* İç kalibrasyon: eğitim penceresinin son %20'si (zaman), arada ufuk + ambargo boşluğu.
* Plasebo ve gün-blok bootstrap yardımcıları.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

FINAL_START = int(pd.Timestamp('2026-05-01', tz='UTC').timestamp())
EMBARGO_S = 86400
CALIB_FRAC = 0.20
WF_BLOCKS = [('2023H1', '2023-01-01', '2023-07-01'), ('2023H2', '2023-07-01', '2024-01-01'),
             ('2024H1', '2024-01-01', '2024-07-01'), ('2024H2', '2024-07-01', '2025-01-01'),
             ('2025H1', '2025-01-01', '2025-07-01'), ('2025H2', '2025-07-01', '2026-01-01'),
             ('2026Q1', '2026-01-01', '2026-05-01')]
SELECT_BLOCKS = ('2023H1', '2023H2', '2024H1', '2024H2')       # eşik seçimi
CONFIRM_BLOCKS = ('2025H1', '2025H2', '2026Q1')                # seçimi teyit
HORIZON_S = {'15m': 900, '1h': 3600, '4h': 4 * 3600, 'session': 7 * 3600}


def ts(s: str) -> int:
    return int(pd.Timestamp(s, tz='UTC').timestamp())


def assert_not_final(t: np.ndarray) -> None:
    if np.asarray(t).max() >= FINAL_START:
        raise RuntimeError('KİLİT: final test dönemine dokunan eğitim/seçim çağrısı')


@dataclass
class Fold:
    name: str
    fit: np.ndarray      # bool maske — ağaç eğitimi
    cal: np.ndarray      # bool maske — isotonic kalibrasyon
    test: np.ndarray     # bool maske — OOS


def walk_forward(t: np.ndarray, horizon: str, blocks=WF_BLOCKS, final: bool = False) -> list[Fold]:
    """final=True yalnız Faz 5'te: tek kat, eğitim = FINAL_START öncesi, test = final dönem."""
    hs = HORIZON_S[horizon]
    folds = []
    if final:
        blocks = [('FINAL', None, None)]
    for name, a, b in blocks:
        start = FINAL_START if final else ts(a)
        end = 2**62 if final else ts(b)
        train = t < start - hs - EMBARGO_S                       # arındırma + ambargo
        test = (t >= start) & (t < end)
        if not final:
            test &= t < FINAL_START
        tt = t[train]
        if len(tt) == 0:
            continue
        cut = np.quantile(tt, 1 - CALIB_FRAC)
        fit = train & (t < cut - hs - EMBARGO_S)
        cal = train & (t >= cut)
        if not final:
            assert_not_final(t[train | test])
        folds.append(Fold(name, fit, cal, test))
    return folds


def purged_kfold(t: np.ndarray, horizon: str, k: int = 6) -> list[tuple[np.ndarray, np.ndarray]]:
    """Geliştirme dönemi içinde ardışık k blok; test bloğunun iki yanında ufuk + ambargo arındırılır."""
    dev = t < FINAL_START
    edges = np.quantile(t[dev], np.linspace(0, 1, k + 1))
    hs = HORIZON_S[horizon]
    out = []
    for i in range(k):
        test = dev & (t >= edges[i]) & (t < edges[i + 1] if i < k - 1 else t <= edges[i + 1])
        train = dev & ~test & ~((t >= edges[i] - hs - EMBARGO_S) & (t < edges[i]))
        train &= ~((t >= edges[i + 1]) & (t < edges[i + 1] + hs + EMBARGO_S))
        out.append((train, test))
    return out


def day_block_bootstrap(r: np.ndarray, day: np.ndarray, n_boot: int = 2000, seed: int = 11) -> dict:
    """Gün-blok bootstrap: ortalama R'nin %95 GA'sı ve P(EV>0)."""
    r = np.asarray(r, float)
    if len(r) == 0:
        return {'n': 0, 'ev': np.nan, 'lo': np.nan, 'hi': np.nan, 'p_pos': np.nan}
    df = pd.DataFrame({'r': r, 'd': day})
    g = df.groupby('d').r.agg(['sum', 'size'])
    s, c = g['sum'].to_numpy(), g['size'].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), (n_boot, len(g)))
    means = s[idx].sum(1) / c[idx].sum(1)
    return {'n': int(len(r)), 'days': int(len(g)), 'ev': float(r.mean()), 'lo': float(np.quantile(means, .025)),
            'hi': float(np.quantile(means, .975)), 'p_pos': float((means > 0).mean())}


def independent_count(t: np.ndarray, gap_s: int = 3600) -> int:
    """Ardışık sinyalleri ≤ gap_s içinde tek epizoda indirger (E6/E9)."""
    t = np.sort(np.asarray(t))
    if len(t) == 0:
        return 0
    return int(1 + (np.diff(t) > gap_s).sum())


def hour_matched_placebo(sel_t: np.ndarray, pool_t: np.ndarray, pool_r: np.ndarray, n_rep: int = 1000,
                         seed: int = 5) -> dict:
    """P1: seçilen işlemlerle aynı sayıda ve aynı NY-saati dağılımında rastgele karar anı → EV dağılımı."""
    rng = np.random.default_rng(seed)
    hr = lambda x: pd.to_datetime(x, unit='s', utc=True).tz_convert('America/New_York').hour.to_numpy()
    sh, ph = hr(sel_t), hr(pool_t)
    by_h = {h: np.where(ph == h)[0] for h in np.unique(ph)}
    need = pd.Series(sh).value_counts()
    evs = np.empty(n_rep)
    for k in range(n_rep):
        picks = [rng.choice(by_h[h], n, replace=True) for h, n in need.items() if h in by_h and len(by_h[h])]
        idx = np.concatenate(picks) if picks else np.array([], int)
        evs[k] = np.nanmean(pool_r[idx]) if len(idx) else np.nan
    return {'p50': float(np.nanquantile(evs, .5)), 'p95': float(np.nanquantile(evs, .95)), 'evs': evs}
