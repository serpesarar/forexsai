"""Gölge Modu paneli toplama mantığı — services/shadow_overview.py.

En kritik davranış: bir gölge kapının "açılmalı" sayılması, engelleyeceği
sinyallerin KAYBETMESİNE bağlıdır ve karar metriği **beklenti (R)**'dir,
çıplak WR değil. Bu testler o kuralı ve veri-kalitesi korumalarını kilitler.

DB gerektiren yollar ``_fetch_paged`` sahtelenerek test edilir — testler
Supabase olmadan da koşar.
"""
from __future__ import annotations

import pytest

from services import shadow_overview as so

# ⚠️ signal_analytics.canonical_stop_price satırın ml_stop_price'ını KULLANMAZ;
# stop'u sembol+timeframe'den yeniden hesaplar (NDX/15m → 50 pip). Test satırları
# bu kanona uymazsa R'ler makul bandın dışına düşüp beklentiden ELENİR ve test
# gerçekte olmayan bir davranışı ölçer. Geometri buna göre kurulur:
#   stop = 50 pip (kanonik), TP = 100 pip → RR 2.0 → başabaş %33,3
ENTRY, TP, SL = 29000.0, 29100.0, 28950.0


def _signal(gate: str, win: bool, i: int) -> dict:
    """prediction_logs satırı şeklinde, gölge etiketli sinyal."""
    return {
        "id": f"t{i}", "created_at": "2026-08-26T10:00:00+00:00",
        "symbol": "NDX.INDX", "model_type": "pulse1", "timeframe": "15m",
        "status": "completed" if win else "stopped",
        "ml_direction": "BUY", "ml_entry_price": ENTRY,
        "ml_target_price": TP, "ml_stop_price": SL,
        "targets": {"TP1": TP}, "targets_hit": ["TP1"] if win else [],
        "stop_loss_pips": 50.0, "exit_price": TP if win else SL,
        "resolution_reason": "tp1_hit" if win else "sl_hit",
        "close_reason": "tp1_hit" if win else "sl_hit",
        "factors": {"target_type": "atr_ladder_v1", "shadow_gates": [gate],
                    "shadow_gate_reasons": {gate: f"test gerekçesi {i}"}},
    }


@pytest.fixture(autouse=True)
def _clear_cache():
    so._cache.clear()
    yield
    so._cache.clear()


@pytest.fixture
def gate_report(monkeypatch):
    """Kapı A ağırlıklı kayıp, kapı B ağırlıklı kazanç, kapı C az örnek."""
    rows = [_signal("trend_align_gate", False, i) for i in range(32)]
    rows += [_signal("trend_align_gate", True, 100 + i) for i in range(8)]
    rows += [_signal("wave_position_gate", True, 200 + i) for i in range(32)]
    rows += [_signal("wave_position_gate", False, 300 + i) for i in range(8)]
    rows += [_signal("fakeout_gate", False, 400 + i) for i in range(10)]
    monkeypatch.setattr(so, "_fetch_paged", lambda *a, **k: rows)
    return so.get_shadow_gate_report(30)


def _gate(report: dict, gate_id: str) -> dict:
    return next(g for g in report["gates"] if g["id"] == gate_id)


def test_losing_set_says_open_the_gate(gate_report):
    """Bloklayacağı sinyaller kaybediyorsa kapı gerçek bir frendir."""
    g = _gate(gate_report, "trend_align_gate")
    assert g["would_block_total"] == 40
    assert g["metrics"]["expectancy_r"] < 0
    assert g["verdict"]["code"] == "ac"


def test_winning_set_says_do_not_open(gate_report):
    """Bloklayacağı sinyaller kazanıyorsa kapı kazancı keser — açılmamalı."""
    g = _gate(gate_report, "wave_position_gate")
    assert g["metrics"]["expectancy_r"] > 0
    assert g["verdict"]["code"] == "acma"


def test_small_sample_withholds_verdict(gate_report):
    """n < MIN_N_FOR_VERDICT iken karar verilmez — erken sonuç yasak."""
    g = _gate(gate_report, "fakeout_gate")
    assert g["metrics"]["n"] < so.MIN_N_FOR_VERDICT
    assert g["verdict"]["code"] == "veri_yok"


def test_untouched_gate_is_empty_not_missing(gate_report):
    """Hiç tetiklenmemiş kapı da listede durmalı (panelde künyesi görünsün)."""
    g = _gate(gate_report, "debate_bias_gate")
    assert g["would_block_total"] == 0
    assert g["verdict"]["code"] == "veri_yok"


def test_reasons_carried_per_row(gate_report):
    g = _gate(gate_report, "trend_align_gate")
    assert g["recent"]
    assert g["recent"][0]["reason"].startswith("test gerekçesi")


def test_measured_gate_count(gate_report):
    assert gate_report["measured_gates"] == 2


def test_breakeven_comes_from_geometry(gate_report):
    """RR 2.0 → başabaş %33,3. Bu çıta olmadan WR tek başına anlamsızdır."""
    m = _gate(gate_report, "trend_align_gate")["metrics"]
    assert m["breakeven_wr"] == pytest.approx(33.3, abs=0.2)


# ── gölge kâğıt-işlemler ────────────────────────────────────────────────────

def _trade(source: str, status: str, i: int, tp_d: float = 20.0, sl_d: float = 10.0,
           r: float | None = None) -> dict:
    return {
        "id": f"s{i}", "created_at": "2026-08-26T10:00:00+00:00", "exit_time": None,
        "source": source, "symbol": "NDX.INDX", "timeframe": "5m", "direction": "BUY",
        "pattern_type": "x", "pattern_name": "y", "confidence": 70,
        "entry_price": 100.0, "tp_price": 100.0 + tp_d, "sl_price": 100.0 - sl_d,
        "status": status, "exit_price": None,
        "r_multiple": r if r is not None else (tp_d / sl_d if status == "win" else -1.0),
        "ambiguous": False,
    }


def test_degenerate_geometry_flagged(monkeypatch):
    """Stop'u girişe yapışık işlemler ORTALAMA RR'ı şişirip başabaşı düşürüyordu.

    2026-08-26 bulgusu: formasyon kayıplarında ortalama RR 21,95 çıkıyor,
    başabaş %6'ya iniyor ve kaybeden bir dedektör "kenarlı" görünüyordu.
    Medyan RR + bozuk-geometri sayacı bunu görünür kılar.
    """
    # Gerçek dağılıma benzet: azınlık bozuk (canlıda %30), çoğunluk sağlıklı.
    # ORTALAMA RR bu 12 satır yüzünden ~50'ye fırlar; MEDYAN 2.0'da kalmalı.
    rows = [_trade("pattern", "loss", i, tp_d=200.0, sl_d=1.0) for i in range(12)]
    rows += [_trade("pattern", "loss", 50 + i, tp_d=20.0, sl_d=10.0) for i in range(18)]
    rows += [_trade("pattern", "win", 100 + i, tp_d=20.0, sl_d=10.0) for i in range(10)]
    monkeypatch.setattr(so, "_fetch_paged", lambda *a, **k: rows)

    rep = so.get_shadow_trade_report(30)
    src = rep["sources"][0]

    assert src["degenerate"] == 12, "bozuk geometri sayılmadı"
    # Ortalama RR ~50 olurdu (12×200 + 28×2)/40; medyan sağlıklı çoğunluğu verir.
    assert src["median_rr"] == pytest.approx(2.0, abs=0.01)
    assert any("stop mesafesi" in w for w in src["warnings"])
    assert src["expectancy_r"] < 0


def test_high_wr_negative_expectancy_warned(monkeypatch):
    """WR başabaşın üstünde ama beklenti negatifse panel susmamalı."""
    # Canlı meta vakasının kurgusu (2026-08-26): geometri RR 0,67 → başabaş %59,9,
    # WR %70 (üstünde) AMA kazananlar ilan edilen 0,67R'yi realize etmiyor
    # (gerçekte ort. 0,40R) → beklenti negatife düşüyor. Çıplak WR tam burada yalan söyler.
    rows = [_trade("meta", "win", i, tp_d=6.7, sl_d=10.0, r=0.40) for i in range(14)]
    rows += [_trade("meta", "loss", 100 + i, tp_d=6.7, sl_d=10.0, r=-1.0) for i in range(6)]
    monkeypatch.setattr(so, "_fetch_paged", lambda *a, **k: rows)

    src = so.get_shadow_trade_report(30)["sources"][0]
    assert src["win_rate"] == 70.0
    assert src["breakeven_wr"] is not None and src["win_rate"] > src["breakeven_wr"]
    assert src["expectancy_r"] < 0
    assert any("beklenti NEGATİF" in w for w in src["warnings"])


def test_cache_returns_same_object(monkeypatch):
    """Panel 60 sn'de bir yoklar; her yoklamada 6000 satır çekilmemeli."""
    calls = {"n": 0}

    def _fake(*a, **k):
        calls["n"] += 1
        return [_trade("meta", "win", 0)]

    monkeypatch.setattr(so, "_fetch_paged", _fake)
    a = so.get_shadow_trade_report(30)
    b = so.get_shadow_trade_report(30)
    assert a is b and calls["n"] == 1


def test_overview_is_fail_soft(monkeypatch):
    """Bir blok patlasa bile panel açılmalı; hata listelenir."""
    def _boom(*a, **k):
        raise RuntimeError("supabase yok")

    monkeypatch.setattr(so, "_fetch_paged", _boom)
    out = so.get_shadow_overview(30)

    assert out["gates"] is None and out["models"] is None and out["trades"] is None
    assert {e["block"] for e in out["errors"]} == {"gates", "models", "trades"}
    assert out["flags"] is not None, "bayraklar DB'siz de dönmeli"
