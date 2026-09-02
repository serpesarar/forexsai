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


# ── Cuma bloğu (2026-08-30) ────────────────────────────────────────────────
import datetime as _dt


def _utc(gun, saat):
    """2026-08-{gun} {saat}:00 UTC — 28 Ağu Cuma, 27 Ağu Perşembe."""
    return _dt.datetime(2026, 8, gun, saat, 0, tzinfo=_dt.timezone.utc)


def test_cuma_ogleden_sonra_bloklanir():
    assert _utc(28, 12).weekday() == 4          # gerçekten Cuma
    assert pr.friday_blocks(_utc(28, 12), 12) is True
    assert pr.friday_blocks(_utc(28, 15), 12) is True


def test_cuma_sabahi_gecer():
    assert pr.friday_blocks(_utc(28, 11), 12) is False
    assert pr.friday_blocks(_utc(28, 0), 12) is False


def test_diger_gunler_etkilenmez():
    assert _utc(27, 15).weekday() == 3          # Perşembe
    assert pr.friday_blocks(_utc(27, 15), 12) is False


def test_veri_yoksa_fail_open():
    assert pr.friday_blocks(None, 12) is False


def test_cuma_canli():
    """2026-08-30'da canlıya alındı (5 bağımsız test: permutasyon p=0,015,
    eşik platosu 10-15 UTC, hafta-çıkarma 9/9, aile 4/5, hacim n=258)."""
    assert pr.flag(None, "FRIDAY_BLOCK_LIVE") is True
    assert pr.flag(None, "FRIDAY_BLOCK_ENABLED") is True
    assert pr.flag(None, "FRIDAY_BLOCK_FROM_HOUR") == 12
