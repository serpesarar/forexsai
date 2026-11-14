"""NOM motor + API + model deposu testleri (geçici mini paketle; ağ/DB gerekmez)."""
from __future__ import annotations

import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.nom import engine as NOM  # noqa: E402
from services.nom import features as FE  # noqa: E402
from services.nom import labels as LB  # noqa: E402
from services.nom import model_store as MS  # noqa: E402
from tests.test_nom_features import synth_bars, synth_calendar, synth_macro  # noqa: E402


@pytest.fixture(scope='module')
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp('nom_models')
    MS.ROOT, MS.ACTIVE, MS.HISTORY = root, root / 'ACTIVE', root / 'HISTORY.jsonl'
    b, mac, cal = synth_bars(days=45), synth_macro(), synth_calendar()
    td = b.t.to_numpy() + 60
    td = td[(td % 900 == 0) & (td > b.t.iloc[0] + 20 * 86400)][:-50]
    F = FE.compute_features(b, td, mac, cal)
    cols = FE.feature_columns(F)
    rng = np.random.default_rng(0)
    models, cals, targets = {}, {}, {}
    for hz in LB.HORIZONS:
        for d in ('long', 'short'):
            for tp, sl in LB.GEOMETRIES:
                k = f'{hz}_{d}_{LB.geom_key(tp, sl)}'
                y = rng.integers(0, 3, len(F))
                models[k] = lgb.train({'objective': 'multiclass', 'num_class': 3, 'verbosity': -1, 'num_leaves': 4},
                                      lgb.Dataset(F[cols], y), 5)
                cals[k] = MS.Calibrator([[0, 1]] * 3, [[0, 1]] * 3)
                targets[k] = {'tp_r': tp / sl, 'r_sl': -1.1, 'r_to': -0.05, 'base_p_tp': 0.3, 'base_ev_r': -0.1,
                              'p_tp_bins': [{'lo': 0, 'hi': 1, 'n': 10, 'pred': .3, 'obs': .3, 'ci_lo': .2, 'ci_hi': .4}],
                              'exp_r_bins': [], 'threshold': None, 'proven': False}
    MS.save_bundle('test_v1', {'version': 'test_v1', 'feature_columns': cols, 'targets': targets,
                               'trained_until': '2025-04-01', 'data_version': 'synth'}, models, cals)
    MS.save_bundle('test_v2', {'version': 'test_v2', 'feature_columns': cols, 'targets': targets,
                               'trained_until': '2025-04-02', 'data_version': 'synth'}, models, cals)
    MS.promote('test_v1', 'test')
    NOM._cache.update({'bundle': None, 'bundle_ver': None, 'ctx_key': None})
    return b, mac, cal


def _weekday_now(b: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    ts = pd.to_datetime(b.t, unit='s', utc=True).dt.tz_convert('America/New_York')
    ok = (ts.dt.weekday < 4) & (ts.dt.hour == 11)
    last = b[ok].t.iloc[-1]
    bb = b[b.t <= last].reset_index(drop=True)
    return bb, float(last + 60 + 20)


def test_predict_structure(env):
    b, mac, cal = env
    bb, now = _weekday_now(b)
    r = NOM.predict('1h', '1.5x1.0', now=now, bars=bb, macro=mac, calendar=cal)
    assert r['durum'] == 'NÖTR / belirsiz'                 # kanıtsız hedef → yön önerisi yok
    for d in ('long', 'short'):
        s = r['tahmin'][d]
        tot = s['p_tp_once'] + s['p_sl_once'] + s['p_zaman_asimi']
        assert abs(tot - 1) < 1e-3
        assert len(s['neden']) == 5
        assert s['p_tp_bandi'] is not None
    c = r['baglam']
    assert set(c['rsi']) >= {'M5', 'M15', 'H1'}
    assert len(c['destekler']) <= 3 and len(c['direncler']) <= 3
    assert r['model']['surum'] == 'test_v1'


def test_stale_and_closed(env):
    b, mac, cal = env
    bb, now = _weekday_now(b)
    r = NOM.predict('1h', '1x1', now=now + 3600, bars=bb, macro=mac, calendar=cal)
    assert r['durum'] == 'VERI_BAYAT' and r['tahmin'] is None
    sat = pd.Timestamp('2025-03-15 12:00', tz='UTC').timestamp()
    r = NOM.predict('1h', '1x1', now=sat, bars=bb, macro=mac, calendar=cal)
    assert r['durum'] == 'PIYASA_KAPALI'


def test_bad_inputs(env):
    with pytest.raises(ValueError):
        NOM.predict('2h', '1x1')
    with pytest.raises(ValueError):
        NOM.predict('1h', '3x1')


def test_promote_rollback(env):
    MS.promote('test_v2', 'test')
    assert MS.active_version() == 'test_v2'
    assert MS.rollback() == 'test_v1'
    assert MS.active_version() == 'test_v1'


def test_router(env, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routers import nom_router
    b, mac, cal = env
    bb, now = _weekday_now(b)
    real = NOM.predict
    monkeypatch.setattr(NOM, 'predict', lambda h, g: real(h, g, now=now, bars=bb, macro=mac, calendar=cal))
    app = FastAPI()
    app.include_router(nom_router.router)
    cl = TestClient(app)
    r = cl.get('/api/probability/nasdaq?horizon=1h&geometry=1.5x1.0')
    assert r.status_code == 200 and r.json()['tahmin']['long']['p_tp_once'] >= 0
    assert cl.get('/probability/nasdaq?horizon=4h&geometry=1x1').status_code == 200
    assert cl.get('/api/probability/nasdaq?horizon=9h').status_code == 422
    assert cl.get('/api/probability/nasdaq/meta').json()['surum'] == 'test_v1'
