"""DBG izleyici testleri: sahte MT5 ile. Çalıştırma: pytest calistir/dbg_izleyici/test_dbg_izleyici.py -q"""
from __future__ import annotations

import gzip
import json
import types
from pathlib import Path

import numpy as np
import pytest

import dbg_izleyici as di

HERE = Path(__file__).resolve().parent
T0 = 1_793_000_160   # 3'e tam bölünür (bar başı, sn)


def poz(ticket, typ=0, lot=0.05, price=4000.0, tp=4005.0, msc=None, magic=6686):
    return types.SimpleNamespace(ticket=ticket, type=typ, volume=lot, price_open=price, tp=tp, sl=0.0, magic=magic,
                                 time_msc=msc or T0 * 1000, comment="", symbol=di.SYMBOL, reason=3)


class FakeMT5:
    TIMEFRAME_M3 = 3
    COPY_TICKS_ALL = 6

    def __init__(self):
        self.positions, self.bar_t, self.body = [], T0, 1.0
        self.acc = types.SimpleNamespace(login=303733, server="DBGMarkets-Live", trade_allowed=False, balance=1e6,
                                         equity=1e6, margin=0.0, margin_level=0.0)
        self.connected, self.init_calls, self.deals = True, [], []
        self.ticks = np.array([], dtype=[("time_msc", "i8"), ("bid", "f8"), ("ask", "f8"), ("flags", "i4")])
        self.bid = 4000.0
        self.orders, self.first_tick = [], None

    def account_info(self): return self.acc
    def symbol_info(self, s): return types.SimpleNamespace(trade_contract_size=100.0)
    def positions_get(self, **k): return list(self.positions)
    def terminal_info(self): return types.SimpleNamespace(connected=self.connected)
    def last_error(self): return (1, "ok")
    def initialize(self, *a, **k): self.init_calls.append(a); self.connected = True; return True
    def symbol_info_tick(self, s): return types.SimpleNamespace(bid=self.bid, ask=self.bid + 0.3, time=self.bar_t, time_msc=self.bar_t * 1000)
    def history_deals_get(self, *a, **k): return self.deals
    def copy_ticks_range(self, *a): return self.ticks
    def orders_get(self): return self.orders

    def copy_ticks_from(self, *a):
        if self.first_tick is None:
            return None
        return np.array([(self.bar_t * 1000 + 100, *self.first_tick)], dtype=[("time_msc", "i8"), ("bid", "f8"), ("ask", "f8")])

    def copy_rates_from_pos(self, *a):
        return np.array([(self.bar_t - 180, 4000.0, 4000.0 + self.body), (self.bar_t, 4000.0, 4000.0)],
                        dtype=[("time", "i8"), ("open", "f8"), ("close", "f8")])


class Clock:
    t = T0 + 0.2                 # Pazartesi/pencere bağımsız; pencere testlerinde ayrıca ayarlanır

    def __call__(self):
        return self.t


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    monkeypatch.setattr(di, "LOG_FILE", tmp_path / "log.jsonl")
    monkeypatch.setattr(di, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(di, "TICK_DIR", tmp_path / "ticks")
    mt, ck = FakeMT5(), Clock()
    iz = di.Izleyici(mt, simdi=ck)
    iz.baslat()
    return mt, ck, iz, tmp_path


def olaylar(tmp: Path) -> list[dict]:
    return [json.loads(x) for x in (tmp / "log.jsonl").read_text().splitlines()]


def test_kaynakta_emir_ve_sifre_yok():
    src = (HERE / "dbg_izleyici.py").read_text(encoding="utf-8")
    for yasak in ("order_send", "order_check", "mt5.login", ".login(", "password"):
        assert yasak not in src, yasak


@pytest.mark.parametrize("deg", [dict(login=1), dict(server="Pepperstone-Demo"), dict(trade_allowed=True)])
def test_yanlis_hesap_reddedilir(deg):
    a = types.SimpleNamespace(login=303733, server="DBGMarkets-Live", trade_allowed=False)
    for k, v in deg.items():
        setattr(a, k, v)
    with pytest.raises(di.GuvenlikHatasi):
        di.hesap_dogrula(a)


def test_calisirken_hesap_degisirse_durur(ortam):
    mt, ck, iz, _ = ortam
    mt.acc.login = 61628380
    ck.t += 100
    with pytest.raises(di.GuvenlikHatasi):
        iz.adim()


def test_giris_tp_kapanis_kaydi(ortam):
    mt, ck, iz, tmp = ortam
    mt.positions = [poz(1)]
    iz.adim()
    mt.positions = [poz(1, tp=4003.0)]
    iz.adim()
    mt.deals = [types.SimpleNamespace(entry=0, type=0), types.SimpleNamespace(entry=1, type=0, time_msc=5, price=4003.0, reason=5, profit=1.0, swap=0.0, comment="[tp]")]
    mt.positions = []
    iz.adim()
    ev = {r["olay"]: r for r in olaylar(tmp)}
    assert ev["giris"]["ticket"] == 1 and ev["giris"]["n_acik_once"] == 0
    assert (ev["tp_degisti"]["eski"], ev["tp_degisti"]["yeni"]) == (4005.0, 4003.0)
    assert ev["kapanis"]["reason"] == 5 and ev["kapanis"]["cikis_px"] == 4003.0


def test_acilista_yarim_barda_karar_yok(ortam):
    mt, ck, iz, tmp = ortam
    iz.adim()
    assert not any(r["olay"] == "bar" for r in olaylar(tmp))


def test_sessizlik_baslar_ve_biter(ortam):
    """Beklenen eylem varken 3 bar gerçek eylem yoksa sessizlik; gerçek giriş gelince biter."""
    mt, ck, iz, tmp = ortam
    # pencere içi: 2026-11-02 Pazartesi 09:00 UTC, iki yön boş, gövde yukarı -> BUY taze beklenir
    baz = 1_793_610_000
    assert baz % 180 == 0
    for k in range(3):
        mt.bar_t = baz + 180 * k
        ck.t = mt.bar_t + 0.2
        iz.adim()
        ck.t += di.BAR_WAIT_S + 1
        iz.adim()
    ev = [r["olay"] for r in olaylar(tmp)]
    assert ev.count("bar_uyumsuz") == 3 and "sessizlik_basladi" in ev
    mt.bar_t = baz + 540
    ck.t = mt.bar_t + 0.2
    iz.adim()
    mt.positions = [poz(9, msc=mt.bar_t * 1000 + 200)]
    ck.t += 1
    iz.adim()
    ck.t += di.BAR_WAIT_S
    iz.adim()
    assert "sessizlik_bitti" in [r["olay"] for r in olaylar(tmp)]


def test_kopukken_yeniden_baglanir_sifresiz(ortam):
    mt, ck, iz, tmp = ortam
    mt.connected = False
    ck.t += di.RECONNECT_S + 1
    iz.adim()
    assert mt.init_calls == [(di.TERMINAL,)]
    iz.adim()
    ev = [r["olay"] for r in olaylar(tmp)]
    assert "baglanti_yok" in ev and "baglanti_geldi" in ev


def test_tick_arsivi_filigrani_ilerler_cift_yazmaz(ortam):
    mt, ck, iz, tmp = ortam
    m0 = iz.tick_wm
    mt.ticks = np.array([(m0 - 5, 1.0, 1.1, 2), (m0 + 5, 2.0, 2.1, 2), (m0 + 9, 3.0, 3.1, 2)], dtype=mt.ticks.dtype)
    iz._tick_arsivle(m0 + 10)
    assert iz.tick_wm == m0 + 9
    iz._tick_arsivle(m0 + 10)
    f = next((tmp / "ticks").glob("*.gz"))
    assert len(gzip.open(f, "rt").read().splitlines()) == 2


BAZ = 1_793_610_000      # 2026-11-02 Pazartesi 09:00 UTC, pencere içi


def _bar_adim(mt, ck, t, wait=True):
    mt.bar_t = t
    ck.t = t + 0.4
    return t


def test_ayni_yoklamada_gorulen_giris_bar_durumunu_bozmaz(ortam):
    """Giriş barın ilk yoklamasında görülür: durum girişten ÖNCEKİ olmalı, kural doğru sayılmalı (11-03 hatası)."""
    mt, ck, iz, tmp = ortam
    mt.body = 1.0
    _bar_adim(mt, ck, BAZ)
    mt.positions = [poz(5, typ=0, msc=BAZ * 1000 + 230)]
    iz.adim()
    b = [r for r in olaylar(tmp) if r["olay"] == "bar"][-1]
    assert b["BUY"]["n"] == 0 and b["BUY"]["beklenen"] == "fresh"
    ck.t += di.BAR_WAIT_S + 1
    iz.adim()
    assert not any(r["olay"] == "bar_uyumsuz" for r in olaylar(tmp))


def test_bar_sinirindan_sonra_kapanan_bacak_karar_aninda_aciktir(ortam):
    """Karar önce, TP sonra (RAPOR §4): kapanış bar açılışından sonraysa bacak o karar anında açıktır."""
    mt, ck, iz, tmp = ortam
    mt.positions = [poz(7, msc=(BAZ - 300) * 1000)]
    iz.adim()
    mt.deals = [types.SimpleNamespace(entry=1, type=0, time_msc=BAZ * 1000 + 100, price=4005.0, reason=5, profit=1.0, swap=0.0, comment="")]
    mt.positions = []
    mt.body = -1.0
    _bar_adim(mt, ck, BAZ)
    iz.adim()
    b = [r for r in olaylar(tmp) if r["olay"] == "bar"][-1]
    assert b["BUY"]["n"] == 1


def test_karar_fiyati_ilk_tick(ortam):
    mt, ck, iz, tmp = ortam
    mt.first_tick = (3999.0, 3999.3)
    _bar_adim(mt, ck, BAZ)
    iz.adim()
    b = [r for r in olaylar(tmp) if r["olay"] == "bar"][-1]
    assert (b["bid"], b["ask"], b["fiyat"]) == (3999.0, 3999.3, "ilk_tick")


def test_elle_emir_bakiye_ve_yeni_magic_kaydi(ortam):
    mt, ck, iz, tmp = ortam
    mt.positions = [poz(11, magic=0)]
    mt.orders = [types.SimpleNamespace(ticket=1, symbol=di.SYMBOL, type=2, volume_current=1.0, price_open=3900.0, tp=0.0, sl=0.0, magic=6686)]
    mt.deals = [types.SimpleNamespace(type=2, ticket=9, profit=2_000_000.0, comment="deposit", time=T0 + 5, entry=0)]
    ck.t += di.HESAP_S + 1
    iz.adim()
    ev = [r["olay"] for r in olaylar(tmp)]
    assert {"yeni_magic", "bekleyen_emir", "bakiye_islem"} <= set(ev)
