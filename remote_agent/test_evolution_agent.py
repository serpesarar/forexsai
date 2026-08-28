"""evolution_agent.py — MT5 trade senkronu + giriş/SL/TP zenginleştirme testleri.

Bu ajan Windows/MT5 kutusunda çalışır; Mac'te ne ``MetaTrader5`` ne de
``supabase`` paketi kurulu olmak zorunda değildir. Modül bu ikisini
``import``'ta yükler, o yüzden testler gerçek modülü sahte (fake)
``MetaTrader5``/``supabase`` ile ``sys.modules``'a koyup import zamanında
enjekte eder — ajan koduna TEK satır test-only dal eklenmeden.

Kapsam:
  1. push_trades: MT5 IPC koptuğunda (None dönüş) "yeni deal yok" (boş tuple)
     ile karıştırılmaz; yeniden bağlanma denenir, sağlık kalp atışına yazılır.
     (2026-08-26 vakası: bot_trades 9 gün sessizce donmuştu.)
  2. push_trades artık kapanan her deal için POZİSYONUN girişini (fiyat/zaman)
     ve PLANLANAN SL/TP'sini de yazıyor (2026-08-27) — panel artık decider'daki
     gibi giriş→çıkış / R / TP-SL dökümü gösterebilsin diye.
  3. backfill_trade_entries: var olan (open_price=null) satırları BİR KEZ
     doldurur; versiyon bayrağı olmadan her turda yeniden taramaz.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
AGENT_FILE = REPO / "remote_agent" / "evolution_agent.py"


class _Deal:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Order:
    def __init__(self, **kw):
        self.__dict__.update(kw)


@pytest.fixture
def agent(monkeypatch):
    """Sahte agent_config + MetaTrader5 + supabase ile ajanı taze yükler.

    Her test kendi ``fake_mt5`` nesnesini (fixture'ın döndürdüğü) özelleştirip
    davranışını değiştirebilir; modül HER testte sıfırdan import edilir ki
    testler arasında global durum (TRADE_SYNC vb.) sızmasın.
    """
    cfg = types.ModuleType("agent_config")
    cfg.SUPABASE_URL = "http://x"
    cfg.SUPABASE_SERVICE_KEY = "k"
    cfg.REPO_ROOT = str(REPO)
    cfg.HOST = "test_box"
    monkeypatch.setitem(sys.modules, "agent_config", cfg)

    fake_mt5 = types.ModuleType("MetaTrader5")
    fake_mt5.history_deals_get = lambda *a, **k: ()
    fake_mt5.history_orders_get = lambda *a, **k: ()
    fake_mt5.last_error = lambda: (0, "ok")
    fake_mt5.shutdown = lambda: None
    fake_mt5.initialize = lambda *a, **k: True
    fake_mt5.positions_get = lambda: ()
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake_mt5)

    sup = types.ModuleType("supabase")
    sup.create_client = lambda *a, **k: None
    sup.Client = object
    monkeypatch.setitem(sys.modules, "supabase", sup)

    spec = importlib.util.spec_from_file_location(
        f"evo_agent_{id(fake_mt5)}", AGENT_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.mt5 = fake_mt5  # modülün kendi `import MetaTrader5 as mt5` referansı
    return mod


class FakeUpsertQuery:
    def __init__(self, sink):
        self.sink = sink

    def upsert(self, rows):
        self.sink.extend(rows)
        return self

    def execute(self):
        return {"data": self.sink}


class FakeBotTradesClient:
    """`.table("bot_trades").upsert([...]).execute()` zincirini sahteler."""

    def __init__(self):
        self.written: list[dict] = []

    def table(self, name):
        assert name == "bot_trades"
        return FakeUpsertQuery(self.written)


# ── 1) okuma hatası vs "yeni deal yok" ──────────────────────────────────────

def test_none_result_is_read_error_not_no_new_deals(agent):
    calls = {"shutdown": 0, "initialize": 0}
    agent.mt5.history_deals_get = lambda *a, **k: None
    agent.mt5.last_error = lambda: (-10004, "no IPC connection")
    agent.mt5.shutdown = lambda: calls.__setitem__("shutdown", calls["shutdown"] + 1)
    agent.mt5.initialize = lambda *a, **k: calls.__setitem__("initialize", calls["initialize"] + 1) or True

    n = agent.push_trades(FakeBotTradesClient(), {"last_deal_ts": 500})

    assert n == 0
    assert agent.TRADE_SYNC["ok"] is False
    assert agent.TRADE_SYNC["fail_streak"] == 1
    assert calls["shutdown"] == 1 and calls["initialize"] == 1, "yeniden bağlanma denenmedi"


def test_empty_tuple_is_healthy_no_new_deals(agent):
    agent.mt5.history_deals_get = lambda *a, **k: ()
    n = agent.push_trades(FakeBotTradesClient(), {"last_deal_ts": 500})

    assert n == 0
    assert agent.TRADE_SYNC["ok"] is True
    assert agent.TRADE_SYNC["fail_streak"] == 0
    assert agent.TRADE_SYNC["last_push_at"] is not None


def test_fail_streak_accumulates(agent):
    agent.mt5.history_deals_get = lambda *a, **k: None
    agent.push_trades(FakeBotTradesClient(), {"last_deal_ts": 500})
    agent.push_trades(FakeBotTradesClient(), {"last_deal_ts": 500})
    assert agent.TRADE_SYNC["fail_streak"] == 2


# ── 2) giriş/SL/TP zenginleştirme ───────────────────────────────────────────

@pytest.fixture
def closed_position(agent):
    """Pozisyon 555: giriş 100.0@t1000, SL95/TP110; çıkış 110.0@t2000 (TP)."""
    entry = _Deal(entry=0, time=1000, price=100.0, ticket=1, position_id=555)
    exit_ = _Deal(entry=1, time=2000, price=110.0, ticket=2, position_id=555,
                  symbol="NAS100", volume=1.0, type=0, profit=500.0,
                  commission=0.0, swap=-1.5, comment="[tp 110.0]",
                  magic=42, order=99, reason=5)
    order = _Order(ticket=1, sl=95.0, tp=110.0)

    def _deals(*a, **k):
        if "position" in k:
            return (entry, exit_)
        return (exit_,)

    agent.mt5.history_deals_get = _deals
    agent.mt5.history_orders_get = lambda *a, **k: (order,)
    return {"entry": entry, "exit": exit_, "order": order}


def test_lookup_entry_extracts_open_and_planned_stop(agent, closed_position):
    open_price, open_time, sl, tp = agent._lookup_entry(555)
    assert (open_price, open_time, sl, tp) == (100.0, 1000, 95.0, 110.0)


def test_lookup_entry_missing_data_is_none_not_error(agent):
    agent.mt5.history_deals_get = lambda *a, **k: ()
    agent.mt5.history_orders_get = lambda *a, **k: ()
    assert agent._lookup_entry(999) == (None, None, None, None)


def test_push_trades_writes_enriched_row(agent, closed_position):
    client = FakeBotTradesClient()
    n = agent.push_trades(client, {"last_deal_ts": 500})

    assert n == 1
    row = client.written[0]
    assert row["open_price"] == 100.0
    assert row["sl"] == 95.0 and row["tp"] == 110.0
    assert row["close_price"] == 110.0
    assert row["open_time"] is not None
    assert row["raw"]["reason"] == 5, "TP çıkış sebebi (MT5 reason=5) korunmalı"


# ── 3) geriye dönük dolum (bir kerelik) ─────────────────────────────────────

class FakeSelectChain:
    def __init__(self, rows):
        self.data = rows

    def eq(self, *a):
        return self

    def is_(self, *a):
        return self

    def order(self, *a):
        return self

    def limit(self, *a):
        return self

    def execute(self):
        return self


class FakeUpdateChain:
    def __init__(self, sink, payload):
        self.sink = sink
        self.payload = payload

    def eq(self, *a):
        return self

    def execute(self):
        self.sink.append(self.payload)
        return self


class FakeBackfillClient:
    def __init__(self, null_rows):
        self.null_rows = null_rows
        self.updates: list[dict] = []
        self.table_calls = 0

    def table(self, name):
        self.table_calls += 1
        return self

    def select(self, *a):
        return FakeSelectChain(self.null_rows)

    def update(self, payload):
        return FakeUpdateChain(self.updates, payload)


def test_backfill_fills_null_rows_once(agent, closed_position):
    client = FakeBackfillClient([{"ticket": 2, "raw": {"position_id": 555}}])
    state: dict = {}

    filled = agent.backfill_trade_entries(client, state)

    assert filled == 1
    assert client.updates[0]["open_price"] == 100.0
    assert client.updates[0]["sl"] == 95.0 and client.updates[0]["tp"] == 110.0
    assert state["entry_backfill_version"] == agent.ENTRY_BACKFILL_VERSION


def test_backfill_skips_second_call(agent, closed_position):
    state = {"entry_backfill_version": agent.ENTRY_BACKFILL_VERSION}
    client = FakeBackfillClient([{"ticket": 2, "raw": {"position_id": 555}}])

    filled = agent.backfill_trade_entries(client, state)

    assert filled == 0
    assert client.table_calls == 0, "versiyon bayrağı ikinci taramayı engellemeli"


def test_backfill_skips_rows_without_position_id(agent):
    client = FakeBackfillClient([{"ticket": 3, "raw": {}}])
    filled = agent.backfill_trade_entries(client, {})
    assert filled == 0
    assert client.updates == []


def test_backfill_tolerates_lookup_miss(agent):
    """Pozisyon MT5 geçmişinde bulunamazsa satır atlanır, hata fırlatmaz."""
    client = FakeBackfillClient([{"ticket": 4, "raw": {"position_id": 777}}])
    filled = agent.backfill_trade_entries(client, {})
    assert filled == 0


def test_backfill_survives_warmup_query_failure(agent, closed_position):
    """Terminal-ısıtma sorgusu patlarsa dahi asıl dolum devam etmeli."""
    real_deals = agent.mt5.history_deals_get

    def _flaky(*a, **k):
        if "position" not in k:
            raise RuntimeError("ısıtma sorgusu koptu")
        return real_deals(*a, **k)

    agent.mt5.history_deals_get = _flaky
    client = FakeBackfillClient([{"ticket": 2, "close_time": "2026-08-01T00:00:00+00:00",
                                  "raw": {"position_id": 555}}])
    filled = agent.backfill_trade_entries(client, {})
    assert filled == 1, "ısıtma hatası asıl dolumu engellememeli"
