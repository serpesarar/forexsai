"""NOM özellik paketi — sızıntı ve eğitim/servis eşdeğerliği testleri.

1) Kesme eşdeğerliği: T anındaki özellikler, tam veriyle ve yalnız açılışı < T olan barlarla AYNI.
   (Canlı servis yalnız geçmişi görür → bu test aynı zamanda train/serve eşdeğerliğidir.)
2) Gelecek bozma: T'den sonraki barlar rastgele değiştirilince T'deki özellikler değişmez.
3) Etiket: aynı barda TP ve SL → SL; giriş spread + kayma içerir; ufuk dışı barlar etiketi etkilemez.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.nom import features as FE  # noqa: E402
from services.nom import labels as LB  # noqa: E402

NY = 'America/New_York'


def synth_bars(days: int = 45, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(pd.Timestamp('2025-03-03', tz='UTC').timestamp(),
                  pd.Timestamp('2025-03-03', tz='UTC').timestamp() + days * 86400, 60, dtype='int64')
    ts = pd.to_datetime(t, unit='s', utc=True).tz_convert(NY)
    closed = (ts.hour == 17) | (ts.weekday == 5) | ((ts.weekday == 6) & (ts.hour < 18)) | ((ts.weekday == 4) & (ts.hour >= 17))
    t = t[~np.asarray(closed)]
    r = rng.standard_t(4, len(t)) * 3.0
    c = 20000 + np.cumsum(r)
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.exponential(2.0, len(t))
    lo = np.minimum(o, c) - rng.exponential(2.0, len(t))
    return pd.DataFrame({'t': t, 'open': o, 'high': h, 'low': lo, 'close': c})


def synth_macro() -> pd.DataFrame:
    d = pd.bdate_range('2024-01-01', '2025-05-01')
    rng = np.random.default_rng(3)
    n = len(d)
    return pd.DataFrame({'date': d, 'VIX_close': 15 + np.cumsum(rng.normal(0, .5, n)).clip(-5, 20),
                         'VIX9D_close': 15 + rng.normal(0, 1, n), 'VIX3M_close': 17 + rng.normal(0, 1, n),
                         'NDX_close': 18000 * np.exp(np.cumsum(rng.normal(0, .01, n))),
                         'SPX_close': 5000 * np.exp(np.cumsum(rng.normal(0, .008, n))),
                         'DXY_close': 100 + np.cumsum(rng.normal(0, .2, n)),
                         'TNX_close': 4 + np.cumsum(rng.normal(0, .03, n)),
                         'QQQ_volume': rng.integers(2e7, 6e7, n).astype(float)})


def synth_calendar() -> pd.DataFrame:
    ts = pd.to_datetime(['2025-03-12 12:30', '2025-03-19 18:00', '2025-04-04 12:30', '2025-03-27 20:05'], utc=True)
    return pd.DataFrame({'ts_utc': ts, 'event': ['CPI', 'FOMC', 'NFP', 'EARN_NVDA']})


def _eq(a: pd.DataFrame, b: pd.DataFrame) -> list[str]:
    bad = []
    for c in a.columns:
        x, y = a[c].to_numpy(dtype=float), b[c].to_numpy(dtype=float)
        same = (np.isnan(x) & np.isnan(y)) | np.isclose(x, y, rtol=1e-9, atol=1e-9)
        if not same.all():
            bad.append(c)
    return bad


@pytest.fixture(scope='module')
def data():
    b = synth_bars()
    return b, synth_macro(), synth_calendar()


def _decisions(b: pd.DataFrame, n: int = 12, seed: int = 1) -> np.ndarray:
    td = b.t.to_numpy() + 60
    td = td[(td % 300 == 0) & (td > b.t.iloc[0] + 25 * 86400)]
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(td, n, replace=False))


def test_truncation_equivalence(data):
    b, mac, cal = data
    T = _decisions(b)
    full = FE.compute_features(b, T, mac, cal)
    cols = FE.feature_columns(full)
    for k, t in enumerate(T):
        cut = b[b.t < t].reset_index(drop=True)
        one = FE.compute_features(cut, np.array([t]), mac, cal)
        bad = _eq(full.iloc[[k]][cols].reset_index(drop=True), one[cols])
        assert not bad, f'kesme eşdeğerliği bozuk @ {t}: {bad[:10]}'


def test_future_perturbation(data):
    b, mac, cal = data
    T = _decisions(b, n=6, seed=2)
    base = FE.compute_features(b, T, mac, cal)
    cols = FE.feature_columns(base)
    rng = np.random.default_rng(9)
    for k, t in enumerate(T):
        pb = b.copy()
        fut = pb.t >= t
        shock = rng.normal(0, 50, fut.sum())
        for c in ('open', 'high', 'low', 'close'):
            pb.loc[fut, c] = pb.loc[fut, c] + shock
        pb.loc[fut, 'high'] = pb.loc[fut, ['open', 'high', 'low', 'close']].max(axis=1) + 5
        pb.loc[fut, 'low'] = pb.loc[fut, ['open', 'high', 'low', 'close']].min(axis=1) - 5
        one = FE.compute_features(pb, np.array([t]), mac, cal)
        bad = _eq(base.iloc[[k]][cols].reset_index(drop=True), one[cols])
        assert not bad, f'gelecek bozma özelliği değiştirdi @ {t}: {bad[:10]}'


def test_macro_not_visible_before_1715_et(data):
    b, mac, cal = data
    d = pd.Timestamp('2025-03-14')
    before = int(pd.Timestamp('2025-03-14 17:10', tz=NY).tz_convert('UTC').timestamp())
    after = int(pd.Timestamp('2025-03-14 18:05', tz=NY).tz_convert('UTC').timestamp())
    F = FE.compute_features(b, np.array([before, after]), mac, cal)
    vix_d = float(mac.loc[mac.date == d, 'VIX_close'].iloc[0])
    vix_prev = float(mac.loc[mac.date == d - pd.offsets.BDay(1), 'VIX_close'].iloc[0])
    assert F.mac_vix.iloc[0] == pytest.approx(vix_prev)
    assert F.mac_vix.iloc[1] == pytest.approx(vix_d)


def _path(o, h, l, c, spr=1.0):
    n = len(o)
    return LB.Path1m(t=np.arange(n, dtype='int64') * 60, o=np.array(o, float), h=np.array(h, float),
                     l=np.array(l, float), c=np.array(c, float), spr=np.full(n, spr))


def test_same_bar_is_sl():
    p = _path([100, 100, 100], [100, 130, 100], [100, 70, 100], [100, 100, 100])
    d = LB.label_batch(p, np.array([0]), np.array([10.0]), np.array([180]), geoms=((1.0, 1.0),),
                       expected_min=np.array([3.0]))
    assert d[('long', '1x1', 'cls')][0] == LB.CLASS_SL
    assert d[('short', '1x1', 'cls')][0] == LB.CLASS_SL


def test_entry_includes_friction_and_tp():
    # LONG giriş = 100 + spr 1 + kayma 1 = 102; TP = 112 → yalnız high ≥ 112 TP sayılır
    p = _path([100, 101, 103], [101, 111.9, 112.0], [99.5, 100, 103], [101, 103, 111])
    d = LB.label_batch(p, np.array([0]), np.array([10.0]), np.array([180]), geoms=((1.0, 1.0),),
                       expected_min=np.array([3.0]))
    assert d[('long', '1x1', 'cls')][0] == LB.CLASS_TP
    assert d[('long', '1x1', 'tbar')][0] == 2
    assert d[('long', '1x1', 'r')][0] == pytest.approx(1.0)


def test_horizon_excludes_later_bars():
    p = _path([100, 100, 100, 100], [100.5, 100.5, 100.5, 200], [99.5, 99.5, 99.5, 99.5], [100, 100, 100, 100])
    d = LB.label_batch(p, np.array([0]), np.array([10.0]), np.array([180]), geoms=((1.0, 1.0),),
                       expected_min=np.array([3.0]))
    assert d[('long', '1x1', 'cls')][0] == LB.CLASS_TO
