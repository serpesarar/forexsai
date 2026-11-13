"""fx_fiks_shadow.py birim testleri (MT5 gerekmez).
Çalıştır:  cd 'yeni deneme' && python3 -m pytest test_fx_fiks_shadow.py"""
import logging
import math
from datetime import date

import pytest

import fx_fiks_shadow as fx

LOG = logging.getLogger("t")
HOL = fx.jp_holidays()


@pytest.fixture(autouse=True)
def _tmp_files(tmp_path, monkeypatch):
    monkeypatch.setattr(fx, "EVENTS_JSONL", tmp_path / "ev.jsonl")
    monkeypatch.setattr(fx, "STATE_FILE", tmp_path / "st.json")


def _recs():
    import json
    return [json.loads(x) for x in fx.EVENTS_JSONL.read_text().splitlines()] if fx.EVENTS_JSONL.exists() else []


def test_gotobi_takvimi_arastirmayla_ayni():
    # research/fx_secim_20261113/hyp.py::gotobi_days çıktısı (2026-11 / 2026-12)
    assert sorted(fx.gotobi_days(2026, 11, HOL)) == [date(2026, 11, d) for d in (5, 10, 13, 20, 25, 30)]
    assert sorted(fx.gotobi_days(2026, 12, HOL)) == [date(2026, 12, d) for d in (4, 10, 15, 18, 25, 30, 31)]


def test_londra_saat_dilimi():
    # 2026-07-31 BST: 16:00 Londra = 15:00 UTC; 2026-11-30 GMT: 16:00 Londra = 16:00 UTC
    assert fx.london_to_utc(date(2026, 7, 31), 16) == fx.utc_at(date(2026, 7, 31), 15)
    assert fx.london_to_utc(date(2026, 11, 30), 16) == fx.utc_at(date(2026, 11, 30), 16)


def test_ay_son_hafta_ici():
    assert fx.last_weekday_of_month(date(2026, 10, 3)) == date(2026, 10, 30)   # 31 Ekim Cumartesi
    assert fx.last_weekday_of_month(date(2026, 11, 3)) == date(2026, 11, 30)


def test_gotobi_sabah_yukseldiyse_sat_ve_kapat():
    d = date(2026, 11, 20)
    pre, t_in, t_out = fx.utc_at(date(2026, 11, 19), 23), fx.utc_at(d, 1), fx.utc_at(d, 6)
    bars = {"USDJPY": {pre: 155.00, t_in: 155.20}}
    st = {"pos": [], "done": []}
    assert fx.step(st, bars, {"USDJPY": (155.21, 155.20)}, t_in + 30, HOL, LOG)
    assert len(st["pos"]) == 1 and st["pos"][0]["side"] == -1 and st["pos"][0]["fill"] == 155.20
    assert not fx.step(st, bars, {}, t_in + 600, HOL, LOG)          # aynı gün ikinci kez açılmaz
    bars["USDJPY"][t_out] = 155.00
    assert fx.step(st, bars, {"USDJPY": (155.01, 155.00)}, t_out + 20, HOL, LOG)
    res = [r for r in _recs() if r["kind"] == "result"][0]
    assert res["bp_model"] == pytest.approx(-math.log(155.0 / 155.2) * 1e4 - fx.COST_BP["GOTOBI"], abs=0.01)
    assert res["bp_fill"] == pytest.approx(-math.log(155.01 / 155.20) * 1e4, abs=0.01)
    assert st["pos"] == []


def test_gotobi_sabah_dustuyse_islem_yok():
    d = date(2026, 11, 20)
    bars = {"USDJPY": {fx.utc_at(date(2026, 11, 19), 23): 155.30, fx.utc_at(d, 1): 155.20}}
    st = {"pos": [], "done": []}
    fx.step(st, bars, {}, fx.utc_at(d, 1) + 30, HOL, LOG)
    assert st["pos"] == [] and _recs()[0]["kind"] == "skip"


def test_gotobi_olmayan_gun_dokunmaz():
    d = date(2026, 11, 19)
    bars = {"USDJPY": {fx.utc_at(date(2026, 11, 18), 23): 155.0, fx.utc_at(d, 1): 156.0}}
    st = {"pos": [], "done": []}
    assert not fx.step(st, bars, {}, fx.utc_at(d, 2), HOL, LOG)


def test_ay_sonu_ters_yon():
    d = date(2026, 11, 30)
    t_pre, t_in, t_out = fx.london_to_utc(d, 10), fx.london_to_utc(d, 16), fx.london_to_utc(d, 20)
    bars = {s: {t_pre: 1.1000, t_in: 1.1000} for s in fx.AYSONU_SYMBOLS}
    bars["EURUSD"] = {t_pre: 1.1000, t_in: 1.1050}          # yükseldi → SAT
    bars["USDJPY"] = {t_pre: 155.0, t_in: 154.0}            # düştü → AL
    st = {"pos": [], "done": []}
    fx.step(st, bars, {}, t_in + 10, HOL, LOG)
    sides = {p["sym"]: p["side"] for p in st["pos"]}
    assert sides == {"EURUSD": -1, "USDJPY": 1}             # hareketsiz dördü 'missed'
    bars["EURUSD"][t_out] = 1.1000
    bars["USDJPY"][t_out] = 154.5
    fx.step(st, bars, {}, t_out + 10, HOL, LOG)
    res = {r["sym"]: r["bp_model"] for r in _recs() if r["kind"] == "result"}
    assert res["EURUSD"] > 0 and res["USDJPY"] > 0 and st["pos"] == []


def test_karne_ozet():
    recs = [{"kind": "result", "leg": "GOTOBI", "bp_model": 2.0, "bp_fill": None},
            {"kind": "result", "leg": "GOTOBI", "bp_model": -1.0, "bp_fill": 0.5},
            {"kind": "skip", "leg": "GOTOBI"}]
    s = fx.summarize(recs)["GOTOBI"]
    assert s["n"] == 2 and s["bp_model"] == 0.5 and s["atlanan"] == 1 and s["n_fill"] == 1
