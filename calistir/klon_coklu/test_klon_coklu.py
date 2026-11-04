"""Çok sembol gölge testleri (sahte veri). Çalıştırma: pytest calistir/klon_coklu/test_klon_coklu.py -q"""
from __future__ import annotations

import json
import types
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pytest

import klon_coklu as kc

HERE = Path(__file__).resolve().parent
PZT_09 = 1_793_610_000       # 2026-11-02 Pazartesi 09:00 UTC
SUNUCU = PZT_09 + 2 * 3600   # kışın sunucu = UTC+2
NAS = next(s for s in kc.SEMBOLLER if s.ad == "NAS100")
OIL = next(s for s in kc.SEMBOLLER if s.ad == "SpotCrude")
XAU = next(s for s in kc.SEMBOLLER if s.ad == "XAUUSD")


def test_kaynakta_emir_ve_oturum_yok():
    for f in ("klon_coklu.py", "klon_coklu_gecmis.py", "klon_coklu_ozet.py"):
        src = (HERE / f).read_text(encoding="utf-8")
        for yasak in ("order_send", "order_check", ".login(", "password"):
            assert yasak not in src, (f, yasak)


def test_olcek_altinla_ayni_para_ve_oran():
    a = XAU.ayar(False)
    assert a.tp_usd == 5.0 and dict(a.step_table)[5] == 0.5 and dict(a.step_table)[10] == 0.0
    n = NAS.ayar(False)
    assert n.tp_usd == pytest.approx(27.8) and dict(n.step_table)[5] == pytest.approx(2.8) and dict(n.step_table)[10] == 0.0
    o = OIL.ayar(False)
    assert o.tp_usd == pytest.approx(0.224) and dict(o.step_table)[5] == pytest.approx(0.022)
    # 1. seviye TP parası: altın 0,01 lot × 5 $ × 100 = 5 $, diğerleri aynı mertebede
    assert 0.2 * n.tp_usd * 1.0 == pytest.approx(5.56)
    assert 0.22 * o.tp_usd * 100.0 == pytest.approx(4.93, abs=0.01)


def test_utc_farki_abd_yaz_saatine_gore():
    assert kc.sunucu_farki(date(2026, 11, 2)) == 2
    assert kc.sunucu_farki(date(2026, 10, 30)) == 3
    assert kc.sunucu_farki(date(2026, 3, 7)) == 2 and kc.sunucu_farki(date(2026, 3, 8)) == 3
    assert kc.sunucu_utc(SUNUCU * 1000) == datetime.fromtimestamp(PZT_09, tz=timezone.utc)


def bar(sk, t, *fiyat, sp=1.0):
    out = []
    for n, p in enumerate(fiyat):
        out += sk.tick(t * 1000 + n * 1000, p, p + sp)
    return out


def test_taze_ekleme_tp_ve_karar_ilk_tickte():
    sk = kc.SembolKlon(NAS, 1.0)
    t = SUNUCU
    bar(sk, t, 28000.0, 28010.0)                    # yukarı bar
    e = bar(sk, t + 180, 28010.0, 28000.0)          # pencere içi, gövde yukarı: BUY taze, ilk tick ask'ıyla
    taze = [x for x in e if x["tur"] == "fresh" and x["side"] == "BUY" and x["v"] == "A"]
    assert taze and taze[0]["price"] == 28011.0 and taze[0]["lot"] == 0.2
    e = bar(sk, t + 360, 28000.0, 27990.0)          # gövde ters, ters mesafe 11 > 2,8: ekleme
    assert any(x["tur"] == "add" and x["side"] == "BUY" and x["level"] == 2 for x in e)
    e = sk.tick((t + 540) * 1000, 28100.0, 28101.0)
    tp = [x for x in e if x["tur"] == "tp" and x["side"] == "BUY" and x["v"] == "A"]
    assert tp and tp[0]["pnl"] > 0


def test_kesin_esik_petrolde_uc_basamak():
    """0,022 adımı tam eşitken ekleme yok, 0,023'te var (eski 2 hane yuvarlaması bunu bozardı)."""
    a = OIL.ayar(False)
    from klon_kurallar import BUY, decide_side
    assert decide_side(BUY, -0.1, 1, 88.000, 87.978, False, a) == "none"
    assert decide_side(BUY, -0.1, 1, 88.000, 87.977, False, a) == "add"


def test_b_kesicisi_tetiklenir_a_devam_eder():
    sk = kc.SembolKlon(NAS, 1.0)
    t = SUNUCU
    bar(sk, t, 28000.0, 28010.0)
    bar(sk, t + 180, 28010.0, 28005.0)
    for k in range(40):
        bar(sk, t + 360 + 180 * k, 28000.0 - 60 * k, 28000.0 - 60 * k - 50)
    oz = sk.ozet()
    assert oz["B"]["kesici"] >= 1 and oz["B"]["max_seviye"] <= kc.SEVIYE_TAVANI
    assert oz["A"]["kesici"] == 0 and oz["A"]["seviye"]["BUY"] > 20 and oz["A"]["en_kotu_yuzen"] < -1000


def test_swap_tahmini_gun_devrinde():
    sw = {"mod": kc.SWAP_INTEREST, "long": -6.48, "short": 1.48, "point": 0.1, "uc_kat": 5}
    sk = kc.SembolKlon(NAS, 1.0, sw)
    t = SUNUCU
    bar(sk, t, 28000.0, 28010.0)
    bar(sk, t + 180, 28010.0, 28005.0)
    sk.tick((t + 86_400) * 1000, 28005.0, 28006.0)
    assert sk.ist["A"]["swap"] == pytest.approx(0.2 * 28005.0 * -6.48 / 100 / 360, rel=1e-6)


class FakeMT5:
    COPY_TICKS_ALL = 6

    def __init__(self):
        self.ticks = {s.ad: [] for s in kc.SEMBOLLER}

    def account_info(self):
        return types.SimpleNamespace(server="Pepperstone-Demo", login=1)

    def symbol_select(self, *a):
        return True

    def symbol_info(self, s):
        return types.SimpleNamespace(trade_tick_size=0.1, trade_tick_value=0.1, swap_mode=0, swap_long=0.0, swap_short=0.0,
                                     point=0.1, swap_rollover3days=3)

    def symbol_info_tick(self, s):
        return types.SimpleNamespace(time_msc=SUNUCU * 1000)

    def copy_ticks_range(self, ad, bas, bit, fl):
        a, b = bas.timestamp() * 1000, bit.timestamp() * 1000
        return np.array([t for t in self.ticks[ad] if a <= t[0] <= b], dtype=[("time_msc", "i8"), ("bid", "f8"), ("ask", "f8")])


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    for ad, f in (("LOG_FILE", "log.jsonl"), ("STATE_FILE", "state.json"), ("OZET_FILE", "ozet.json")):
        monkeypatch.setattr(kc, ad, tmp_path / f)
    monkeypatch.setattr(kc, "VERI", tmp_path)
    return FakeMT5(), tmp_path


def test_yeniden_baslatmada_kacan_tickler_islenir_cift_islenmez(ortam):
    mt, tmp = ortam
    clk = [SUNUCU + 10.0]
    k = kc.Kosucu(mt, simdi=lambda: clk[0])
    k.baslat()
    mt.ticks["NAS100"] = [((SUNUCU + 1) * 1000, 28000.0, 28001.0), ((SUNUCU + 170) * 1000, 28010.0, 28011.0),
                          ((SUNUCU + 181) * 1000, 28010.0, 28011.0)]
    k.adim()
    assert k.k["NAS100"].wm == (SUNUCU + 181) * 1000
    taze = k.k["NAS100"].ist["A"]["taze"]
    assert taze == 1
    k._yaz()
    # süreç ölür; bu arada tick gelir; yeni süreç durumdan devam edip kaçanı işler
    mt.ticks["NAS100"].append(((SUNUCU + 400) * 1000, 28009.0, 28010.0))
    k2 = kc.Kosucu(mt, simdi=lambda: clk[0] + 500)
    k2.baslat()
    assert k2.k["NAS100"].ist["A"]["taze"] == 1
    k2.adim()
    k2.adim()
    assert k2.k["NAS100"].wm == (SUNUCU + 400) * 1000 and k2.k["NAS100"].ist["A"]["taze"] == 1
    assert (tmp / "ozet.json").exists() and json.loads((tmp / "ozet.json").read_text())["kural"] == kc.KURAL


def test_hafta_sonu_boslugunda_sorgu_ilerler(ortam):
    mt, _ = ortam
    clk = [SUNUCU + 3 * 86_400.0]
    k = kc.Kosucu(mt, simdi=lambda: clk[0])
    k.baslat()
    bas = k.sorgu["NAS100"]
    k.adim()
    assert k.sorgu["NAS100"] > bas


def test_yanlis_terminal_reddedilir(ortam):
    mt, _ = ortam
    mt.account_info = lambda: types.SimpleNamespace(server="DBGMarkets-Live", login=303733)
    with pytest.raises(RuntimeError):
        kc.Kosucu(mt).baslat()
