"""ATR sıkışma filtresinin SAF çekirdeğini sınar (MT5 gerekmez, Mac'te koşar).

Kanıt bağlamı: analyst_reports/sikisma_filtresi_denetimi_2026-08-28.md
"""
import phase_rules as pr


def _bars(trs, base=100.0):
    """Verilen true-range dizisinden sentetik bar üret (TR = high-low)."""
    out = [{"high": base, "low": base, "close": base}]
    for tr in trs:
        out.append({"high": base + tr, "low": base, "close": base})
    return out


def test_yetersiz_veri_fail_open():
    assert pr.squeeze_ratio(_bars([1.0] * 50)) is None
    assert pr.squeeze_blocks(None, 1.0) is False       # veri yok → engelleme


def test_sabit_volatilitede_oran_bir():
    r = pr.squeeze_ratio(_bars([2.0] * 130))
    assert r is not None and abs(r - 1.0) < 1e-9


def test_sikisma_orani_birin_altinda():
    # son 14 bar sakin (0.5), oncesi hareketli (3.0) → oran < 1
    r = pr.squeeze_ratio(_bars([3.0] * 110 + [0.5] * 14))
    assert r is not None and r < 1.0
    assert pr.squeeze_blocks(r, 1.00) is True


def test_genisleme_oraninda_gecer():
    r = pr.squeeze_ratio(_bars([0.5] * 110 + [3.0] * 14))
    assert r is not None and r > 1.0
    assert pr.squeeze_blocks(r, 1.00) is False


def test_esik_kenar_durumu():
    assert pr.squeeze_blocks(1.00, 1.00) is False      # esitlik gecer
    assert pr.squeeze_blocks(0.999, 1.00) is True


def test_varsayilan_golge():
    """Kural CANLI davranisi degistirmemeli: blok varsayilani KAPALI."""
    assert pr.flag(None, "SQZ_FILTER_BLOCK") is False
    assert pr.flag(None, "SQZ_FILTER_ENABLED") is True
    assert pr.flag(None, "SQZ_FILTER_MIN") == 1.00
    assert "NDX.INDX" in pr.flag(None, "SQZ_FILTER_SYMBOLS")


# ── Cuma bloğu: KANONİK mekanizma NDX_FRIDAY_BLOCK (2026-08-30) ───────────
# Ayrı bir FRIDAY_BLOCK_* kapısı eklenmiş ve sonra KALDIRILMIŞTIR: kutuda
# NDX_FRIDAY_BLOCK zaten ~2026-08-07'den beri TÜM Cuma NDX girişlerini
# bloklıyordu (kanıt: son Cuma işlemi 08-07, veri 08-26'ya kadar sürüyor ve
# aradaki 3 Cuma'da tek işlem yok). Paralel ikinci mekanizma yerine kanıt
# mevcut bayrağa bağlandı ve repo varsayılanı True yapıldı.


def test_cuma_kanonik_bayrak_acik():
    assert pr.flag(None, "NDX_FRIDAY_BLOCK") is True


def test_yinelenen_cuma_kapisi_kaldirildi():
    assert not hasattr(pr, "friday_blocks"), "yinelenen mekanizma geri gelmis"
    assert "FRIDAY_BLOCK_LIVE" not in pr.DEFAULTS


# ── Sıkı konum kapısı sembol kapsamı (2026-09-02) ─────────────────────────
def test_pos_tight_canli_ama_sembol_sinirli():
    """Gölge ölçümü: GDAXI %28,6 (başabaş %64) → blokla; NDX %62,0 → bloklama."""
    assert pr.flag(None, "POS_TIGHT_BLOCK") is True
    syms = pr.flag(None, "POS_TIGHT_SYMBOLS")
    assert "GDAXI.INDX" in syms
    assert "NDX.INDX" not in syms, "NDX'te bloklamak gölge kanıtına aykiri"
    assert "USOIL.FOREX" not in syms, "USOIL'de bloklananlar %99 kazaniyor"


def test_pos_tight_esikleri_degismedi():
    assert pr.flag(None, "POS_TIGHT_SELL_MIN") == 0.60
    assert pr.flag(None, "POS_TIGHT_BUY_MAX") == 0.40
