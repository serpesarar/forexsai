"""USOIL gölge kurallarının SAF çekirdeği (MT5 gerekmez, Mac'te koşar).

Kanıt: backend/data/evolution/analyst_reports/usoil_sl_fiyat_tabani_2026-09-29.md §6, §8
"""
from datetime import datetime, timezone

import phase_rules as pr


def _t(h):
    return datetime(2026, 9, 28, h, 10, tzinfo=timezone.utc)


# ── seans filtresi ──────────────────────────────────────────────────────────

def test_seans_sabah_engellerdi():
    would, why = pr.session_gate(_t(8), "USOIL.FOREX:BUY", None)
    assert would and "08 UTC" in why


def test_seans_ogleden_sonra_serbest():
    assert pr.session_gate(_t(13), "USOIL.FOREX:BUY", None) == (False, "")
    assert pr.session_gate(_t(23), "USOIL.FOREX:BUY", None) == (False, "")


def test_seans_kenar_12_engeller():
    assert pr.session_gate(_t(12), "USOIL.FOREX:BUY", None)[0] is True


def test_seans_baska_scope_etkilenmez():
    assert pr.session_gate(_t(8), "NDX.INDX:BUY", None)[0] is False
    assert pr.session_gate(_t(8), "USOIL.FOREX:SELL", None)[0] is False


def test_seans_alt_scope_eki_kapsanir():
    # CHREV gibi ekli scope anahtarı tabana indirgenir
    assert pr.session_gate(_t(8), "USOIL.FOREX:BUY:CHREV", None)[0] is True


def test_seans_varsayilan_golge():
    assert pr.flag(None, "USOIL_SESSION_GATE_BLOCK") is False


def test_seans_kapatilabilir():
    class C:
        USOIL_SESSION_GATE_ENABLED = False
    assert pr.session_gate(_t(8), "USOIL.FOREX:BUY", C()) == (False, "")


# ── zikzak kâr kilidi — ticket 390567007'nin gerçek yolu ───────────────────
E, SL, TP = 98.648, 95.584, 99.675


def _run(prices):
    st, evs = {}, []
    for p in prices:
        ev = pr.zz_lock_step(st, p, E, E - SL, TP - E, None)
        if ev:
            evs.append(ev)
    return st, evs


def test_vaka_390567007_kilit_tetiklenir_ve_vurulur():
    # 97.31 (−0.44R dip) → 99.306 (TP yolunun %64'ü) → 98.6 (kilit 99.16 altı)
    st, evs = _run([98.5, 97.31, 98.2, 99.306, 99.2, 98.6, 95.6])
    assert evs == ["loss_seen", "fired", "lock_hit"]
    assert abs(st["lock"] - (E + 0.5 * (TP - E))) < 1e-9


def test_once_zarar_yoksa_tetiklenmez():
    # doğrudan TP yoluna gidip dönen işlem: kural kapsamı DIŞI
    st, evs = _run([98.9, 99.3, 99.5, 98.0])
    assert evs == []


def test_zarar_esigi_altinda_kalan_dip_sayilmaz():
    # 0.3R = 0.919 → 97.729 altı gerekir; 97.9 yetmez
    st, evs = _run([97.9, 99.4])
    assert evs == []


def test_kilit_vurulmadan_tp():
    st, evs = _run([97.5, 99.3, 99.5, 99.68])
    assert evs == ["loss_seen", "fired"] and not st.get("lock_hit")


def test_gecersiz_geometri():
    assert pr.zz_lock_step({}, 98.0, E, 0.0, 1.0, None) is None
