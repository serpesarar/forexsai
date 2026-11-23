"""Kaydedici MT5 bağlantı doğrulaması + kendini onarma birim testleri (MT5 gerekmez — sahte modül).

2026-11-19 vakası: Pepperstone terminali 05:05 UTC'de yeniden başladı, kaydedici eski IPC'de
kaldı; 4,5 gün her dakika "kayıt @" yazdı ama tek bar yazmadı.
Çalıştır: cd 'yeni deneme' && python3 -m pytest -q test_data_recorder_link.py"""
import importlib
import logging
import sys
import types

import pytest

fake = types.ModuleType("MetaTrader5")
for k, v in {"TIMEFRAME_M1": 1, "TIMEFRAME_M5": 5, "TIMEFRAME_M15": 15,
             "TIMEFRAME_M30": 30, "TIMEFRAME_H1": 16385}.items():
    setattr(fake, k, v)

GOOD_LOGIN = 61628380


@pytest.fixture
def rec(tmp_path, monkeypatch):
    """data_recorder'ı sahte MT5 + sahte config ile, log dosyası tmp'ye düşecek şekilde yükle."""
    monkeypatch.chdir(tmp_path)
    cfg = types.ModuleType("config")
    cfg.MT5_ACCOUNT = 0
    cfg.MT5_PASSWORD = ""
    cfg.MT5_SERVER = "Pepperstone-Demo"
    cfg.MT5_TERMINAL_PATH = r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"
    cfg.RECORDER_EXPECTED_LOGIN = GOOD_LOGIN
    cfg.RECORDER_SYMBOLS = {"NDX.INDX": "NAS100", "XAUUSD": "XAUUSD"}
    monkeypatch.setitem(sys.modules, "config", cfg)
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
    monkeypatch.setitem(sys.modules, "supabase", types.SimpleNamespace(create_client=lambda *a: None))
    sys.modules.pop("data_recorder", None)
    module = importlib.import_module("data_recorder")
    yield module
    for h in list(logging.getLogger().handlers):       # tmp'deki log dosyasını bırak
        if isinstance(h, logging.FileHandler):
            logging.getLogger().removeHandler(h)
            h.close()
    sys.modules.pop("data_recorder", None)


def _acc(login=GOOD_LOGIN, server="Pepperstone-Demo"):
    return types.SimpleNamespace(login=login, server=server, company="Pepperstone")


def test_account_problem_rejects_dbg_and_wrong_login(rec):
    assert rec.account_problem(_acc(), GOOD_LOGIN) is None
    assert "DBG" in rec.account_problem(_acc(303733, "DBGMarkets-Server"), GOOD_LOGIN)
    assert "yanlış hesap" in rec.account_problem(_acc(61587064), GOOD_LOGIN)
    assert rec.account_problem(None, GOOD_LOGIN) is not None
    assert rec.account_problem(_acc(61587064), None) is None       # beklenen yoksa yalnız DBG reddi


def _mt5(monkeypatch, rec, *, account, link_ok, init_ok=True):
    calls = []
    mt = types.SimpleNamespace(
        TIMEFRAME_M1=1,
        initialize=lambda *a, **k: calls.append(("init", a)) or init_ok,
        last_error=lambda: (1, "ok"),
        account_info=lambda: account,
        shutdown=lambda: calls.append(("shutdown",)),
        terminal_info=lambda: types.SimpleNamespace(connected=True) if link_ok["v"] else None,
        copy_rates_from_pos=lambda *a: [1] if link_ok["v"] else None,
        symbol_info=lambda s: object(),
        symbol_select=lambda s, on: True,
    )
    monkeypatch.setattr(rec, "mt5", mt)
    return calls


def test_connect_uses_terminal_path_and_rejects_foreign_account(rec, monkeypatch):
    calls = _mt5(monkeypatch, rec, account=_acc(303733, "DBGMarkets-Server"), link_ok={"v": True})
    assert rec.connect_mt5() is False
    assert calls[0] == ("init", (rec.config.MT5_TERMINAL_PATH,)) and ("shutdown",) in calls

    calls = _mt5(monkeypatch, rec, account=_acc(), link_ok={"v": True})
    assert rec.connect_mt5() is True and ("shutdown",) not in calls


def test_ensure_link_reconnects_after_terminal_restart(rec, monkeypatch):
    link = {"v": False}
    calls = _mt5(monkeypatch, rec, account=_acc(), link_ok=link)
    state, resolved = {"fails": 0}, {"NDX.INDX": "NAS100", "XAUUSD": "XAUUSD"}
    assert rec.ensure_link(state, resolved) is False and state["fails"] == 1   # tek kopuş: bekle
    assert not [c for c in calls if c[0] == "init"]

    def _init(*a, **k):                      # yeni terminale bağlanınca IPC yeniden canlı
        link["v"] = True
        return True
    rec.mt5.initialize = _init
    assert rec.ensure_link(state, resolved) is True and state["fails"] == 0
    assert rec.ensure_link(state, resolved) is True


def test_ensure_link_exits_when_reconnect_keeps_failing(rec, monkeypatch):
    _mt5(monkeypatch, rec, account=_acc(), link_ok={"v": False}, init_ok=False)
    state, resolved = {"fails": 0}, {"NDX.INDX": "NAS100"}
    with pytest.raises(SystemExit) as exc:
        for _ in range(rec.RECONNECT_AFTER_FAILS + rec.RECONNECT_MAX_FAILS + 1):
            rec.ensure_link(state, resolved)
    assert exc.value.code == 3
