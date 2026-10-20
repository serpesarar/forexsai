"""Günlük zarar freni birim testleri (MT5 gerekmez — sahte modül). 2026-10-19 vakası:
DAYCOMBO/REENTRY magic'leri sayılmıyordu + pencere broker saatine çevrilmiyordu.
Çalıştır: cd 'yeni deneme' && python3 -m pytest -q test_daily_brake.py"""
import sys
import time
import types
from datetime import datetime, timezone

fake = types.ModuleType("MetaTrader5")
for k, v in {"ORDER_TYPE_BUY": 0, "ORDER_TYPE_SELL": 1, "ORDER_TYPE_BUY_LIMIT": 2, "ORDER_TYPE_SELL_LIMIT": 3,
             "DEAL_ENTRY_OUT": 1, "DEAL_ENTRY_OUT_BY": 3, "TIMEFRAME_M1": 1, "TIMEFRAME_M5": 5,
             "TIMEFRAME_M15": 15, "TIMEFRAME_M30": 30, "TIMEFRAME_H1": 16385, "TIMEFRAME_H4": 16388,
             "TIMEFRAME_D1": 16408}.items():
    setattr(fake, k, v)
sys.modules.setdefault("MetaTrader5", fake)

import forexsai_demo_bot as bot  # noqa: E402

OFF = 3 * 3600


class Deal:
    def __init__(self, magic, profit, t_utc):
        self.magic, self.profit, self.swap, self.commission = magic, profit, 0.0, 0.0
        self.time = int(t_utc.timestamp()) + OFF           # MT5: broker etiketli


def _install(deals, monkeypatch, now_utc):
    calls = {}

    def hist(a, b):
        calls["win"] = (a, b)
        lo, hi = a.timestamp(), b.timestamp()
        return [d for d in deals if lo <= d.time <= hi]

    monkeypatch.setattr(bot.mt5, "history_deals_get", hist, raising=False)
    monkeypatch.setattr(bot, "_broker_offset_sec", lambda: OFF)

    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return now_utc
    monkeypatch.setattr(bot, "datetime", FakeDT)
    return calls


def test_daycombo_and_reentry_magics_counted():
    m = bot._bot_magics()
    base = bot.config.MAGIC_NUMBER
    assert {base, base + 4, base + 6} <= m


def test_brake_sees_last_three_hours_in_broker_time(monkeypatch):
    base = bot.config.MAGIC_NUMBER
    d = lambda h, mi: datetime(2026, 10, 19, h, mi, tzinfo=timezone.utc)  # noqa: E731
    deals = [Deal(base, -1486, d(7, 0)), Deal(base + 4, 2400, d(15, 23)),
             Deal(base + 6, -3330, d(16, 30)), Deal(base + 4, -3300, d(16, 30)),
             Deal(base, 1032, d(16, 31)),
             Deal(base + 4, -999, datetime(2026, 10, 18, 22, 0, tzinfo=timezone.utc))]  # dün → sayılmaz
    _install(deals, monkeypatch, d(16, 32))
    pnl = bot.today_realized_pnl()
    assert round(pnl) == -4684
    assert pnl <= -bot.config.DAILY_MAX_LOSS or bot.config.DAILY_MAX_LOSS > 4684


def test_offset_falls_back_when_tick_stale(monkeypatch):
    bot._BROKER_OFF.update({"sec": None, "t": 0.0})
    stale = types.SimpleNamespace(time=int(time.time()) - 2 * 86400)
    monkeypatch.setattr(bot, "resolve_symbol", lambda fx: "X")
    monkeypatch.setattr(bot.mt5, "symbol_info_tick", lambda s: stale, raising=False)
    assert bot._broker_offset_sec() == bot.BROKER_OFFSET_DEFAULT_SEC
