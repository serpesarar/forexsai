"""execute_mt5 saf yardımcıları + send_order koruma zinciri (sahte mt5 ile)."""
import types
import execute_mt5 as ex


def test_normalize_lot_cap_and_step():
    assert ex.normalize_lot(1.0, 0.01, 50, 0.01) == 0.03          # cap 0.3 × 0.10
    assert ex.normalize_lot(0.1, 0.01, 50, 0.01) == 0.01
    assert ex.normalize_lot(0.0, 0.01, 50, 0.01) == 0.01          # min lot'a yükselir
    assert ex.normalize_lot(1.0, 0.1, 50, 0.1) == 0.1             # step 0.1 → aşağı yuvarla sonra min


def test_levels_and_stops():
    tp, sl = ex.build_levels("BUY", 100.0, 2.0, 1.0, 1.5)
    assert (tp, sl) == (102.0, 97.0)
    tp, sl = ex.build_levels("SELL", 100.0, 2.0, 1.0, 1.5)
    assert (tp, sl) == (98.0, 103.0)
    assert ex.stops_ok(100.0, 102.0, 97.0, 10, 0.01)
    assert not ex.stops_ok(100.0, 100.05, 97.0, 10, 0.01)


def test_comment_ascii_28():
    c = ex.mk_comment("USOIL.FOREX", "SELL")
    assert len(c) <= 28 and c.isascii()


def _fake_mt5(trade_mode=0, positions=(), sent=None):
    m = types.SimpleNamespace(
        ACCOUNT_TRADE_MODE_DEMO=0, TRADE_ACTION_DEAL=1, ORDER_TYPE_BUY=0, ORDER_TYPE_SELL=1,
        ORDER_TIME_GTC=0, ORDER_FILLING_IOC=1, ORDER_FILLING_FOK=0, ORDER_FILLING_RETURN=2,
        TRADE_RETCODE_DONE=10009, TIMEFRAME_M5=5)
    m.account_info = lambda: types.SimpleNamespace(trade_mode=trade_mode)
    m.terminal_info = lambda: types.SimpleNamespace(trade_allowed=True)
    m.positions_get = lambda: list(positions)
    m.symbol_info = lambda s: types.SimpleNamespace(digits=2, point=0.01, trade_stops_level=10,
                                                   volume_min=0.01, volume_max=50, volume_step=0.01,
                                                   filling_mode=2)
    m.symbol_info_tick = lambda s: types.SimpleNamespace(ask=100.02, bid=100.0)
    m.order_check = lambda r: types.SimpleNamespace(retcode=0, comment="ok")

    def order_send(r):
        if sent is not None:
            sent.append(dict(r))
        return types.SimpleNamespace(retcode=10009, order=777, price=r["price"], comment="")
    m.order_send = order_send
    m.last_error = lambda: (0, "")
    return m


def _run(m, tmp_path, monkeypatch, **dec):
    monkeypatch.setattr(ex, "LIVE_ORDERS_JSONL", tmp_path / "o.jsonl")
    monkeypatch.setattr(ex, "KILL_FILE", tmp_path / "OFF")
    d = {"direction": "BUY", "size_factor": 0.7, "reason": "t"}
    d.update(dec)
    return ex.send_order(m, "NDX.INDX", "NAS100", d, 5.0, 1.0, 1.5)


def test_sends_on_demo_with_small_lot(tmp_path, monkeypatch):
    sent = []
    r = _run(_fake_mt5(sent=sent), tmp_path, monkeypatch)
    assert r["status"] == "sent" and sent[0]["volume"] == 0.03
    assert sent[0]["magic"] == ex.DECIDER_MAGIC and sent[0]["tp"] > sent[0]["price"] > sent[0]["sl"]


def test_refuses_real_account(tmp_path, monkeypatch):
    sent = []
    r = _run(_fake_mt5(trade_mode=2, sent=sent), tmp_path, monkeypatch)
    assert r["status"] == "skipped" and not sent


def test_one_position_per_symbol_and_kill_switch(tmp_path, monkeypatch):
    pos = [types.SimpleNamespace(magic=ex.DECIDER_MAGIC, symbol="NAS100")]
    assert _run(_fake_mt5(positions=pos), tmp_path, monkeypatch)["status"] == "skipped"
    (tmp_path / "OFF").write_text("x")
    monkeypatch.setattr(ex, "KILL_FILE", tmp_path / "OFF")
    assert ex.killed()
