"""USOIL BUY RR-tabanlı hedef mesafesi (phase_rules.usoil_buy_tp_distance).

Kural 2026-08-20 derin sınamasından geldi (2.025 hipotetik giriş): RR 1,0
mevcut RR 0,70'i her kesitte geçiyor. VARSAYILAN KAPALI — bu testler hem
kapalıyken dokunmadığını hem de açıkken doğru mesafeyi ürettiğini kilitler.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "yeni deneme"))

import phase_rules as pr  # noqa: E402


class Cfg:
    """config nesnesi taklidi — yalnız verilen alanlar ezer."""

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def test_varsayilan_kapali():
    assert pr.DEFAULTS["USOIL_BUY_TP_RR"] == 0.0
    assert pr.usoil_buy_tp_distance("USOIL.FOREX:BUY", "USOIL.FOREX", "BUY",
                                    1.10, Cfg()) is None


def test_acikken_rr_carpani():
    cfg = Cfg(USOIL_BUY_TP_RR=1.0)
    assert pr.usoil_buy_tp_distance("USOIL.FOREX:BUY", "USOIL.FOREX", "BUY",
                                    1.10, cfg) == 1.10
    cfg = Cfg(USOIL_BUY_TP_RR=1.25)
    got = pr.usoil_buy_tp_distance("USOIL.FOREX:BUY", "USOIL.FOREX", "BUY",
                                   0.80, cfg)
    assert abs(got - 1.0) < 1e-9


def test_sell_ve_diger_semboller_etkilenmez():
    cfg = Cfg(USOIL_BUY_TP_RR=1.0)
    assert pr.usoil_buy_tp_distance("USOIL.FOREX:SELL", "USOIL.FOREX", "SELL",
                                    1.10, cfg) is None
    assert pr.usoil_buy_tp_distance("NDX.INDX:BUY", "NDX.INDX", "BUY",
                                    110.0, cfg) is None


def test_bozuk_girdide_fail_open():
    cfg = Cfg(USOIL_BUY_TP_RR=1.0)
    assert pr.usoil_buy_tp_distance("USOIL.FOREX:BUY", "USOIL.FOREX", "BUY",
                                    0.0, cfg) is None
    assert pr.usoil_buy_tp_distance("USOIL.FOREX:BUY", "USOIL.FOREX", "BUY",
                                    -1.0, cfg) is None
    assert pr.usoil_buy_tp_distance("USOIL.FOREX:BUY", "USOIL.FOREX", "BUY",
                                    1.10, Cfg(USOIL_BUY_TP_RR="bozuk")) is None


def test_daycombo_muaf():
    cfg = Cfg(USOIL_BUY_TP_RR=1.0)
    assert pr.usoil_buy_tp_distance("USOIL.FOREX:BUY:DAYCOMBO", "USOIL.FOREX",
                                    "BUY", 1.10, cfg) is None
