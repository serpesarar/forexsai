"""SL tipi yasağı (2026-11-28, defter SY-01) — saf kural testi."""
import types

import phase_rules as pr


def _cfg(**kw):
    return types.SimpleNamespace(**kw)


def test_default_bans_three_ndx_types():
    c = _cfg()
    assert pr.sl_type_banned(c, "NDX.INDX", "MOMSR", "BUY")
    assert pr.sl_type_banned(c, "NDX.INDX", "chrev", "buy")
    assert pr.sl_type_banned(c, "NDX.INDX", "VIXREG", "SELL")
    assert pr.flag(c, "SL_TYPE_BAN_BLOCK") is True


def test_profitable_and_other_types_untouched():
    c = _cfg()
    for fam, d in (("DAYCOMBO", "BUY"), ("REENTRY", "BUY"), ("REENTRY", "SELL"),
                   ("VIXREG", "BUY"), ("CHREV", "SELL"), ("MOMSR", "SELL"), ("DECIDER", "SELL")):
        assert not pr.sl_type_banned(c, "NDX.INDX", fam, d)
    assert not pr.sl_type_banned(c, "GDAXI.INDX", "MOMSR", "BUY")
    assert not pr.sl_type_banned(c, "USOIL.FOREX", "VIXREG", "SELL")


def test_kill_switch_and_override():
    assert not pr.sl_type_banned(_cfg(SL_TYPE_BAN_ENABLED=False), "NDX.INDX", "MOMSR", "BUY")
    c = _cfg(SL_TYPE_BAN=(("NDX.INDX", "VIXREG", "SELL"),))
    assert not pr.sl_type_banned(c, "NDX.INDX", "MOMSR", "BUY")
    assert pr.sl_type_banned(c, "NDX.INDX", "VIXREG", "SELL")
