"""Re-entry icra çekirdeği testleri (MT5 gerekmez).

Kritik davranışlar:
  · gecikme TP/SL'ye göre farklı (5 dk / 1 dk)
  · bayat niyet iptal edilir
  · zincirleme yok (re-entry magic'inden yeni re-entry doğmaz)
  · guard reddederse emir gönderilmez
  · gölge modda opener HİÇ çağrılmaz
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

BOT = Path(__file__).resolve().parents[1] / "yeni deneme"
sys.path.insert(0, str(BOT))
if "config" not in sys.modules:
    cfg = types.ModuleType("config")
    cfg.MAGIC_NUMBER = 52890969
    sys.modules["config"] = cfg

import reentry_exec as re_  # noqa: E402
import config as fake        # noqa: E402


class Cfg:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def _log():
    return types.SimpleNamespace(info=lambda *a, **k: None,
                                 warning=lambda *a, **k: None,
                                 exception=lambda *a, **k: None)


# ── saf çekirdek ───────────────────────────────────────────────────────────

def test_gecikme_tp_ve_sl_farkli():
    assert re_.gecikme_dk(True, None) == 5      # TP sonrası
    assert re_.gecikme_dk(False, None) == 1     # SL sonrası


def test_gecikme_config_ile_degisir():
    c = Cfg(REENTRY_DELAY_TP_MIN=30, REENTRY_DELAY_SL_MIN=3)
    assert re_.gecikme_dk(True, c) == 30
    assert re_.gecikme_dk(False, c) == 3


def test_hazir_bekler_sonra_gider():
    assert re_.hazir_mi(60, True, None)[0] == "wait"       # 1dk < 5dk
    assert re_.hazir_mi(5 * 60, True, None)[0] == "go"
    assert re_.hazir_mi(60, False, None)[0] == "go"        # SL'de 1dk yeter


def test_bayat_niyet_iptal():
    v, why = re_.hazir_mi(25 * 60, True, None)
    assert v == "cancel" and "bayat" in why


def test_zincir_engeli():
    """Re-entry magic'inden (+6) yeni re-entry doğmamalı."""
    assert re_.zincir_engeli(52890969 + 6)
    assert not re_.zincir_engeli(52890969)          # normal momentum
    assert not re_.zincir_engeli(52890969 + 2)      # vixreg


def test_magic_ayri():
    """Slot çakışmasını önleyen ayrı magic."""
    assert re_.magic() == 52890969 + 6


# ── mod kontrolü ───────────────────────────────────────────────────────────

def test_varsayilan_golge():
    for attr in ("REENTRY_MODE", "REENTRY_SYMBOLS"):
        if hasattr(fake, attr):
            delattr(fake, attr)
    assert re_.mode() == "shadow"
    assert re_.is_enabled("NDX.INDX")
    assert not re_.is_enabled("USOIL.FOREX")     # kanıt yalnız NASDAQ'ta


def test_off_modu_kapatir():
    fake.REENTRY_MODE = "off"
    assert not re_.is_enabled("NDX.INDX")
    del fake.REENTRY_MODE


# ── kuyruk işleme ──────────────────────────────────────────────────────────

def _fake_mt5():
    class Tick:
        bid = ask = 100.0

    class M:
        @staticmethod
        def symbol_info_tick(s):
            return Tick()
    return M


def _kuyruga(kazandi=True, yas_sn=600):
    import time
    re_._pending.clear()
    re_._pending.append({"ana_ticket": 1, "fx": "NDX.INDX", "sym": "NAS100",
                         "dir": "BUY", "kapanis_px": 100.0, "kazandi": kazandi,
                         "t0": time.time() - yas_sn})


def test_golge_modda_emir_gonderilmez():
    fake.REENTRY_MODE = "shadow"
    _kuyruga()
    acilan, kayit = [], []
    re_.isle(_fake_mt5(), _log(), lambda *a: acilan.append(a),
             shadow_record=lambda *a, **k: kayit.append(a))
    assert acilan == []           # canlı emir YOK
    assert len(kayit) == 1        # gölge kaydı VAR
    assert re_._pending == []
    del fake.REENTRY_MODE


def test_canli_modda_emir_gonderilir():
    fake.REENTRY_MODE = "live"
    _kuyruga()
    acilan = []
    re_.isle(_fake_mt5(), _log(), lambda *a: acilan.append(a),
             guard=lambda p: (True, ""))
    assert len(acilan) == 1
    assert acilan[0][2] == "BUY" and acilan[0][3] == re_.magic()
    del fake.REENTRY_MODE


def test_guard_reddederse_emir_yok():
    """Faz-1 penceresi kapalıysa / tavan doluysa re-entry açılmaz."""
    fake.REENTRY_MODE = "live"
    _kuyruga()
    acilan = []
    re_.isle(_fake_mt5(), _log(), lambda *a: acilan.append(a),
             guard=lambda p: (False, "global tavan dolu"))
    assert acilan == [] and re_._pending == []
    del fake.REENTRY_MODE


def test_bekleyen_niyet_kuyrukta_kalir():
    fake.REENTRY_MODE = "live"
    _kuyruga(kazandi=True, yas_sn=60)      # 1dk < 5dk (TP gecikmesi)
    acilan = []
    re_.isle(_fake_mt5(), _log(), lambda *a: acilan.append(a),
             guard=lambda p: (True, ""))
    assert acilan == [] and len(re_._pending) == 1
    re_._pending.clear()
    del fake.REENTRY_MODE
