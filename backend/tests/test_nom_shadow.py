"""NOM gölge modu testleri (sahte DB; ağ/Supabase gerekmez).

Sınananlar: (1) record_once her hedef için bir satır yazar, alanlar tam, emir/prediction_logs yok; (2) bayat/kapalı
piyasada tahmin yazılmaz; (3) fill_outcomes yalnız ufku dolmuş satırları çözer, sonucu EĞİTİMDEKİ label_batch ile birebir
üretir, güncellemede filtre update'ten ÖNCE gelir (E128); (4) karar barı yoksa −1; (5) DB yoksa fail-open 0.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.nom import labels as LB  # noqa: E402
from services.nom import shadow as SH  # noqa: E402
from tests.test_nom_features import synth_bars  # noqa: E402


class _Q:
    """Proje sarmalayıcısını taklit eder: select zinciri execute() ile, update() ANINDA çalışır."""

    def __init__(self, db: 'FakeDB'):
        self.db, self.filters, self.calls = db, [], []

    def upsert(self, row, on_conflict=None):
        self.db.upserts.append((row, on_conflict))
        return {'data': [row]}

    def select(self, cols):
        return self

    def is_(self, col, val):
        self.filters.append(('is_null', col))
        return self

    def lt(self, col, val):
        self.filters.append(('lt', col, val))
        return self

    def order(self, col):
        return self

    def limit(self, n):
        return self

    def execute(self):
        cut = next(f[2] for f in self.filters if f[0] == 'lt')
        rows = [r for r in self.db.rows if r.get('outcome_filled_at') is None and r['t_end'] < cut]
        return {'data': rows}

    def eq(self, col, val):
        self.filters.append(('eq', col, val))
        return self

    def update(self, upd):
        eqs = [f for f in self.filters if f[0] == 'eq']
        assert eqs, 'update() filtresiz çağrıldı — sarmalayıcıda tüm tabloyu günceller (E128)'
        self.db.updates.append((eqs[0][2], upd))
        return {'data': [upd]}


class FakeDB:
    def __init__(self, rows=None):
        self.rows, self.upserts, self.updates = rows or [], [], []

    def table(self, name):
        assert name == 'nom_predictions'
        return _Q(self)


def _fake_predict(hz, gk, now=None, asof=None):
    side = {'p_tp_once': 0.3, 'p_sl_once': 0.4, 'p_zaman_asimi': 0.3, 'beklenen_r': -0.05,
            'neden': [{'metin': f'f{i}'} for i in range(5)]}
    return {'tahmin': {'long': side, 'short': side}, 'geometri': gk, 'durum': 'NÖTR / belirsiz',
            'veri': {'son_bar_kapanis_utc': '2025-03-12T15:00:00+00:00'}, 'model': {'surum': 'test_v1'},
            'baglam': {'fiyat': 20000.0, 'rejim': 'trend', 'seans': 'ny_ogle', 'vix': {'deger': 19.0}},
            'atr_birimleri': {'M5': 20.0, 'M15': 40.0, 'H1': 80.0}}


def test_record_once_writes_each_target(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(SH, '_db', lambda: db)
    monkeypatch.setattr(SH.NOM, 'predict', _fake_predict)
    n = SH.record_once()
    assert n == len(SH.SHADOW_TARGETS) == len(db.upserts)
    need = {'t_dec', 't_end', 'horizon', 'geometry', 'model_version', 'price', 'atr', 'p_long_tp', 'p_long_sl', 'p_long_to',
            'exp_r_long', 'p_short_tp', 'p_short_sl', 'p_short_to', 'exp_r_short', 'status', 'feature_summary', 'source'}
    for row, conflict in db.upserts:
        assert need <= set(row)
        assert conflict == 't_dec,horizon,geometry,model_version'          # idempotent
        assert row['source'] == 'shadow'
        assert pd.Timestamp(row['t_end']) > pd.Timestamp(row['t_dec'])     # sonuç ufku karar anından sonra
        assert row['atr'] == _fake_predict('', '')['atr_birimleri'][LB.HORIZONS[row['horizon']]['atr_tf']]
        assert 'outcome_long_cls' not in row                                # sonuç tahminle birlikte YAZILMAZ


def test_record_skips_when_no_prediction(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(SH, '_db', lambda: db)
    monkeypatch.setattr(SH.NOM, 'predict', lambda *a, **k: {'durum': 'VERI_BAYAT', 'tahmin': None})
    assert SH.record_once() == 0 and not db.upserts


def test_fill_outcomes_matches_training_labels(monkeypatch):
    b = synth_bars(days=10)
    t = b.t.to_numpy()
    i0 = int(np.where(t % 3600 == 0)[0][100])      # bir saat başı karar barı
    t_dec = int(t[i0])
    t_end = t_dec + 3600
    atr = 30.0
    iso = lambda s: datetime.fromtimestamp(s, tz=timezone.utc).isoformat()
    rows = [{'id': 1, 't_dec': iso(t_dec), 't_end': iso(t_end), 'horizon': '1h', 'geometry': '1.5x1', 'atr': atr,
             'outcome_filled_at': None},
            {'id': 2, 't_dec': iso(t_dec + 7), 't_end': iso(t_end), 'horizon': '1h', 'geometry': '1x1', 'atr': atr,
             'outcome_filled_at': None},                                    # karar barı yok → −1
            {'id': 3, 't_dec': iso(t_dec), 't_end': iso(int(t[-1]) + 10 * 86400), 'horizon': '1h', 'geometry': '1x1',
             'atr': atr, 'outcome_filled_at': None}]                        # ufuk dolmamış → dokunulmaz
    db = FakeDB(rows)
    monkeypatch.setattr(SH, '_db', lambda: db)
    monkeypatch.setattr(SH.LD, 'load_bars', lambda: b)
    n = SH.fill_outcomes(now=float(t[-1]))
    assert n == 2 and {u[0] for u in db.updates} == {1, 2}
    upd = dict(db.updates)
    # beklenen: eğitimdeki aynı label_batch, aynı spread modeli
    h = pd.to_datetime(b.t, unit='s', utc=True).dt.tz_convert('America/New_York').dt.hour.to_numpy()
    spr = np.array([SH.SPREAD_NY_HOUR[x] for x in h])
    path = LB.Path1m(t=t, o=b.open.to_numpy(), h=b.high.to_numpy(), l=b.low.to_numpy(), c=b.close.to_numpy(), spr=spr)
    d = LB.label_batch(path, np.array([i0]), np.array([atr]), np.array([t_end]), geoms=((1.5, 1.0),),
                       expected_min=np.array([60.0]))
    gk = LB.geom_key(1.5, 1.0)
    for side in ('long', 'short'):
        assert upd[1][f'outcome_{side}_cls'] == int(d[(side, gk, 'cls')][0])
        exp_r = float(d[(side, gk, 'r')][0])
        got = upd[1][f'outcome_{side}_r']
        assert (got is None and np.isnan(exp_r)) or got == pytest.approx(exp_r)
    assert upd[2]['outcome_long_cls'] == -1 and upd[2]['outcome_short_cls'] == -1
    assert all('outcome_filled_at' in u for u in upd.values())


def test_db_missing_fail_open(monkeypatch):
    monkeypatch.setattr(SH, '_db', lambda: None)
    assert SH.record_once() == 0 and SH.fill_outcomes() == 0
