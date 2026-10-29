"""decider_early_cut birim testleri (MT5 gerekmez). cd 'yeni deneme' && python3 -m pytest -q test_decider_early_cut.py"""
import types

import decider_early_cut as dec


def test_pure_decision():
    # giriş 100, SL 98.5 (risk 1.5): R=-0.5 → kapanış 99.25
    assert dec.early_cut_decision("BUY", 100, 98.5, 99.25, 5.5) == ("kes", -0.5)
    assert dec.early_cut_decision("BUY", 100, 98.5, 99.5, 5.5)[0] == "tut"
    assert dec.early_cut_decision("BUY", 100, 98.5, 99.0, 4.9)[0] == "bekle"
    assert dec.early_cut_decision("BUY", 100, 98.5, 99.0, 11.0)[0] == "gec"
    assert dec.early_cut_decision("SELL", 100, 101.5, 101.0, 6.0)[0] == "gecersiz"
    assert dec.early_cut_decision("BUY", 100, 0.0, 99.0, 6.0)[0] == "gecersiz"


class FakeMT5:
    ORDER_TYPE_BUY, ORDER_TYPE_SELL, TRADE_ACTION_DEAL, ORDER_TIME_GTC = 0, 1, 1, 0
    ORDER_FILLING_IOC, ORDER_FILLING_FOK, ORDER_FILLING_RETURN, TRADE_RETCODE_DONE, TIMEFRAME_M1 = 1, 0, 2, 10009, 1

    def __init__(self, positions, close_px, now):
        self.positions, self.close_px, self.now, self.sent = positions, close_px, now, []

    def positions_get(self):
        return self.positions

    def symbol_info_tick(self, sym):
        return types.SimpleNamespace(time=self.now, bid=99.0, ask=99.1)

    def copy_rates_from_pos(self, sym, tf, pos, n):
        return [{"close": self.close_px}]

    def order_send(self, req):
        self.sent.append(req)
        return types.SimpleNamespace(retcode=self.TRADE_RETCODE_DONE)


class Log:
    def info(self, *a): pass
    def warning(self, *a): pass
    def debug(self, *a): pass


def _pos(ticket, magic=52890989, sym="XAUUSD", t=0, typ=0):
    return types.SimpleNamespace(ticket=ticket, magic=magic, symbol=sym, time=t, type=typ, price_open=100.0,
                                 sl=98.5, volume=0.02, profit=-1.0)


def test_manage_cuts_only_decider_xau_buy_once(monkeypatch):
    monkeypatch.setitem(dec.pr.DEFAULTS, "DECIDER_EARLY_CUT_LIVE", True)
    dec._karar_verildi.clear()
    ps = [_pos(1), _pos(2, magic=52890969), _pos(3, sym="NAS100"), _pos(4, typ=1)]
    m = FakeMT5(ps, close_px=99.0, now=6 * 60)
    dec.manage(m, Log(), lambda s: s)
    assert [r["position"] for r in m.sent] == [1]
    dec.manage(m, Log(), lambda s: s)                 # ikinci tur: tek karar → tekrar gönderme yok
    assert len(m.sent) == 1


def test_manage_keeps_when_above_threshold():
    dec._karar_verildi.clear()
    m = FakeMT5([_pos(7)], close_px=99.6, now=6 * 60)
    dec.manage(m, Log(), lambda s: s)
    assert m.sent == [] and 7 in dec._karar_verildi


def test_manage_shadow_default_never_sends():
    dec._karar_verildi.clear()
    m = FakeMT5([_pos(9)], close_px=99.0, now=6 * 60)    # R=-0,67 → canlıda kesilirdi
    dec.manage(m, Log(), lambda s: s)
    assert m.sent == [] and 9 in dec._karar_verildi
