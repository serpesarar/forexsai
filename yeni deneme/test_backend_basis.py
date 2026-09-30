"""Backend fiyat-tabanı korumasının SAF çekirdeğini sınar (MT5 gerekmez, Mac'te koşar).

Vaka: ticket 390567007 (2026-09-28 SpotCrude BUY) — broker 98.726, backend
(Yahoo CL=F) 95.662, sl_price == entry_price == 95.662 → eski kod SL = 3.064.
Kanıt: backend/data/evolution/analyst_reports/usoil_sl_fiyat_tabani_2026-09-29.md
"""
import phase_rules as pr

VAKA = {"entry_price": 95.662, "sl_price": 95.662, "current_market_price": 95.662}


def test_vaka_390567007_backend_sl_reddedilir():
    d, why = pr.backend_sl_distance(VAKA, 98.726)
    assert d is None
    assert why == "basis_gap"          # %3.1 fark > %0.25 tolerans


def test_taban_uyumlu_ama_sl_uretilmemis_dejenere():
    sig = {"entry_price": 98.70, "sl_price": 98.70, "current_market_price": 98.70}
    d, why = pr.backend_sl_distance(sig, 98.726)
    assert d is None and why == "degenerate"   # eskiden 0.026'lık mikro SL


def test_taban_uyumlu_gecerli_sl_eski_davranis():
    sig = {"entry_price": 98.70, "sl_price": 97.30, "current_market_price": 98.70}
    d, why = pr.backend_sl_distance(sig, 98.726)
    assert why == "ok"
    assert abs(d - (98.726 - 97.30)) < 1e-9


def test_ndx_normal_fark_sifir_degismez():
    sig = {"entry_price": 30432.5, "sl_price": 30542.5, "current_market_price": 30431.0}
    d, why = pr.backend_sl_distance(sig, 30432.5)
    assert why == "ok" and abs(d - 110.0) < 1e-9


def test_sl_yok():
    assert pr.backend_sl_distance({}, 100.0) == (None, "no_sl")
    assert pr.backend_sl_distance(None, 100.0) == (None, "no_sl")


def test_market_fiyati_yoksa_fark_kontrolu_atlanir():
    sig = {"entry_price": 99.0, "sl_price": 97.5}
    d, why = pr.backend_sl_distance(sig, 99.0)
    assert why == "ok" and abs(d - 1.5) < 1e-9
    assert pr.backend_basis_gap_pct(sig, 99.0) is None


def test_tolerans_configden_ezilir():
    class Cfg:
        BACKEND_BASIS_TOL_PCT = 5.0
    sig = {"entry_price": 95.0, "sl_price": 93.5, "current_market_price": 95.0}
    d, why = pr.backend_sl_distance(sig, 98.0, Cfg())      # %3.06 fark < %5
    assert why == "ok" and abs(d - 4.5) < 1e-9


def test_esik_kenari():
    sig = {"entry_price": 100.0, "sl_price": 98.5, "current_market_price": 100.0}
    assert pr.backend_sl_distance(sig, 100.25)[1] == "ok"        # %0.249 < %0.25
    assert pr.backend_sl_distance(sig, 100.30)[1] == "basis_gap"  # %0.299 > %0.25
