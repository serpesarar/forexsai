"""Kanonik sinyal metrikleri — regresyon testleri.

Bu testler 2026-08-21 çekirdek (Core) denetiminde bulunan şişirme kusurlarının
GERİ GELMEMESİNİ garanti eder. Her test bir kusura karşılık gelir; biri
kırılırsa panel istatistikleri yeniden yalan söylemeye başlamış demektir.
"""

import pytest

from services.signal_metrics import (
    AMBIGUOUS_LOSS,
    LOSS,
    NEUTRAL,
    PARTIAL,
    WIN,
    aggregate_outcomes,
    signal_outcome,
)


def _sig(**kw):
    """XAU BUY, giriş 4486.79, TP1 +8, SL −15 (RR 0,533) — gerçek static_pips."""
    base = dict(
        symbol="XAUUSD",
        ml_direction="BUY",
        ml_entry_price=4486.79,
        ml_stop_price=4471.79,
        ml_target_price=4494.79,
        stop_loss_pips=15.0,
        targets={"TP1": 4494.79, "TP2": 4501.79, "TP3": 4511.79, "TP4": 4526.79},
        targets_hit={},
        status="completed",
        exit_price=4494.79,
        resolution_reason="tp4_hit",
        factors={"target_type": "static_pips"},
    )
    base.update(kw)
    return base


# ── KUSUR #2: aynı barda TP+SL iyimser çözülüyordu ──────────────────────────

def test_same_bar_tp_sl_konservatif_kayip_sayilir():
    """Mum içi sıra bilinmiyorsa KAYIP sayılmalı (shadow tracker ile aynı yön).

    Eskiden lifecycle TP döngüsünü önce koştuğu için bu sessizce WIN'di.
    """
    out = signal_outcome(
        _sig(
            resolution_reason="tp1_3_hit_then_sl",
            targets_hit={"TP1": True},
            factors={"target_type": "static_pips", "same_bar_tp_sl": True},
        )
    )
    assert out.klass == AMBIGUOUS_LOSS
    assert out.r_multiple == -1.0
    assert not out.is_win


# ── KUSUR #3: tp1_3_hit_then_sl tam WIN sayılıyordu ─────────────────────────

def test_tp1_sonra_sl_kismi_sayilir_tam_kazanc_degil():
    out = signal_outcome(
        _sig(resolution_reason="tp1_3_hit_then_sl", targets_hit={"TP1": True})
    )
    assert out.klass == PARTIAL, "TP1 görüp SL yiyen işlem TP4 ile aynı ağırlıkta olamaz"
    # R, ilan edilen TP1 geometrisini yansıtmalı (8/15 ≈ 0,533)
    assert out.r_multiple == pytest.approx(0.533, abs=0.01)


def test_tam_tp4_kazanc_ve_r_dogru():
    out = signal_outcome(_sig(exit_price=4526.79, targets_hit={"TP4": True}))
    assert out.klass == WIN
    assert out.r_multiple == pytest.approx(2.667, abs=0.01)  # 40/15


def test_sl_kaybi():
    out = signal_outcome(
        _sig(status="stopped", resolution_reason="sl_hit",
             exit_price=4471.79, targets_hit={})
    )
    assert out.klass == LOSS
    assert out.r_multiple == pytest.approx(-1.0, abs=0.01)


def test_expired_notr_wr_disinda():
    out = signal_outcome(
        _sig(status="expired", resolution_reason="window_resolve_inconclusive")
    )
    assert out.klass == NEUTRAL
    assert not out.counts_in_wr, "expired WR paydasına girmemeli"


# ── KUSUR #1: çıplak WR yanıltıcı — beklenti/başabaş zorunlu ────────────────

def test_wr_yaninda_beklenti_ve_basabas_hep_gelir():
    rows = [_sig(exit_price=4526.79, targets_hit={"TP4": True}) for _ in range(8)]
    rows += [_sig(status="stopped", resolution_reason="sl_hit",
                  exit_price=4471.79) for _ in range(2)]
    m = aggregate_outcomes(rows, default_symbol="XAUUSD")
    assert m.win_rate is not None
    assert m.expectancy_r is not None, "beklenti asla eksik olamaz"
    assert m.breakeven_wr is not None, "başabaş WR asla eksik olamaz"
    assert m.edge_pp is not None


def test_yuksek_wr_negatif_beklenti_uyari_verir():
    """RR 0,53 geometrisinde WR yüksek ama beklenti negatifse panel uyarmalı."""
    # 6 kazanç TP1'de (+0,533R), 4 kayıp (−1R) → EV = (6*0.533 - 4)/10 < 0
    rows = [_sig(exit_price=4494.79, targets_hit={"TP1": True},
                 resolution_reason="window_resolve_positive") for _ in range(6)]
    rows += [_sig(status="stopped", resolution_reason="sl_hit",
                  exit_price=4471.79) for _ in range(4)]
    m = aggregate_outcomes(rows, default_symbol="XAUUSD")
    assert m.win_rate == 60.0
    assert m.expectancy_r < 0
    assert any("beklenti NEGAT" in w.upper() or "NEGATİF" in w for w in m.warnings), \
        f"negatif beklenti uyarısı yok: {m.warnings}"


def test_basabas_wr_geometriden_hesaplanir_sonuctan_degil():
    """Başabaş, ULAŞILAN hedeften değil İLAN EDİLEN TP1'den gelmeli.

    İlk sürümde ``target_hit_profit_floor`` kullanılıyordu; o yalnız
    kazananlarda tanımlı olduğu için başabaş %49,7'ye düşüp WR %80 ile
    çelişmişti. Kazanan-ağırlıklı bir küme bile RR 0,533 vermeli.
    """
    rows = [_sig(exit_price=4526.79, targets_hit={"TP4": True}) for _ in range(9)]
    rows += [_sig(status="stopped", resolution_reason="sl_hit",
                  exit_price=4471.79)]
    m = aggregate_outcomes(rows, default_symbol="XAUUSD")
    assert m.avg_rr_geometry == pytest.approx(0.533, abs=0.01)
    assert m.breakeven_wr == pytest.approx(65.2, abs=0.5)


# ── KUSUR #4: epoch karışımı ────────────────────────────────────────────────

def test_epochlar_ayri_raporlanir_ve_karisim_uyarilir():
    eski = [_sig(exit_price=4526.79, targets_hit={"TP4": True},
                 factors={"target_type": "static_pips"}) for _ in range(9)]
    yeni = [_sig(status="stopped", resolution_reason="sl_hit", exit_price=4471.79,
                 factors={"target_type": "atr_ladder_v1"}) for _ in range(5)]
    m = aggregate_outcomes(eski + yeni, default_symbol="XAUUSD")
    assert m.mixed_epochs is True
    assert set(m.by_epoch) >= {"static_pips", "atr_ladder_v1"}
    assert m.by_epoch["static_pips"].win_rate == 100.0
    assert m.by_epoch["atr_ladder_v1"].win_rate == 0.0
    assert any("epoch" in w.lower() for w in m.warnings)


# ── KUSUR #5: bozuk satır ortalamayı deviriyordu ────────────────────────────

def test_bozuk_exit_price_beklentiyi_devirmez():
    """exit_price=0 olan satır R=−300 üretip ortalamayı deviriyordu."""
    saglam = [_sig(exit_price=4526.79, targets_hit={"TP4": True}) for _ in range(9)]
    bozuk = _sig(exit_price=0, resolution_reason="mt5_manual_sync")
    m = aggregate_outcomes(saglam + [bozuk], default_symbol="XAUUSD")
    assert m.excluded_r == 1, "bozuk satır dışlanmalı"
    assert m.expectancy_r > 2.0, f"beklenti bozuk satırdan etkilenmiş: {m.expectancy_r}"
    assert any("makul band" in w for w in m.warnings)


def test_bozuk_satir_wr_sayiminda_kalir():
    """Dışlanan R, satırı WR'dan SİLMEZ — yoksa kayıplar gizlenebilirdi."""
    saglam = [_sig(exit_price=4526.79, targets_hit={"TP4": True}) for _ in range(3)]
    bozuk = _sig(exit_price=0, resolution_reason="mt5_manual_sync")
    m = aggregate_outcomes(saglam + [bozuk], default_symbol="XAUUSD")
    assert m.n == 4, "bozuk satır WR paydasından düşmemeli"


def test_bos_kume_cokmez():
    m = aggregate_outcomes([], default_symbol="XAUUSD")
    assert m.n == 0
    assert m.win_rate is None
