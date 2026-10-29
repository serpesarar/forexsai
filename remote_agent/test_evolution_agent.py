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
import json
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


class FakeMultiTableClient:
    """Birden çok tabloya upsert yapan çağrıları sahteler (ör. push_fingerprints)."""

    def __init__(self):
        self.by_table: dict[str, list[dict]] = {}

    def table(self, name):
        sink = self.by_table.setdefault(name, [])
        return FakeUpsertQuery(sink)


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


# ── 4) giriş "parmak izi" senkronu (entry_fingerprints.jsonl → Supabase) ────

def test_push_fingerprints_missing_file_is_noop(agent, tmp_path):
    agent.FINGERPRINT_FILE = tmp_path / "yok.jsonl"
    n = agent.push_fingerprints(FakeMultiTableClient(), {})
    assert n == 0


def test_push_fingerprints_reads_new_lines_only(agent, tmp_path):
    """Byte-offset tail: ikinci çağrı yalnız YENİ satırları göndermeli."""
    f = tmp_path / "entry_fingerprints.jsonl"
    rec1 = {"ticket": 111, "ts": "2026-08-28T10:00:00+00:00", "scope": "NDX.INDX:momentum",
            "symbol": "NDX.INDX", "mt5_symbol": "NAS100", "direction": "BUY",
            "entry": 29000.0, "tp": 29100.0, "sl": 28950.0, "lot": 5.0, "rr": 2.0,
            "entry_type": "market", "tp_source": "backend", "voters": ["mom_cont"]}
    f.write_text(json.dumps(rec1) + "\n", encoding="utf-8")
    agent.FINGERPRINT_FILE = f

    client = FakeMultiTableClient()
    state: dict = {}
    n1 = agent.push_fingerprints(client, state)
    assert n1 == 1
    row = client.by_table["bot_entry_fingerprints"][0]
    assert row["ticket"] == 111 and row["direction"] == "BUY"
    assert row["voters"] == ["mom_cont"]
    assert row["raw"]["scope"] == "NDX.INDX:momentum"

    # Aynı offset'te ikinci çağrı: yeni satır yok → sıfır.
    n2 = agent.push_fingerprints(client, state)
    assert n2 == 0

    # Dosyaya YENİ bir satır eklenince yalnız o gelmeli (birincisi tekrar değil).
    rec2 = {**rec1, "ticket": 222, "direction": "SELL"}
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec2) + "\n")
    n3 = agent.push_fingerprints(client, state)
    assert n3 == 1
    assert len(client.by_table["bot_entry_fingerprints"]) == 2
    assert client.by_table["bot_entry_fingerprints"][1]["ticket"] == 222


def test_push_fingerprints_skips_malformed_and_ticketless_lines(agent, tmp_path):
    f = tmp_path / "entry_fingerprints.jsonl"
    f.write_text(
        '{"ticket": 1, "direction": "BUY"}\n'
        'not-json-garbage\n'
        '{"direction": "SELL"}\n'          # ticket yok
        '\n',                              # boş satır
        encoding="utf-8",
    )
    agent.FINGERPRINT_FILE = f
    client = FakeMultiTableClient()
    n = agent.push_fingerprints(client, {})
    assert n == 1
    assert client.by_table["bot_entry_fingerprints"][0]["ticket"] == 1


def test_push_fingerprints_handles_file_truncation(agent, tmp_path):
    """Dosya döndürülüp küçülürse offset sıfırlanır (journal ile aynı kural)."""
    f = tmp_path / "entry_fingerprints.jsonl"
    f.write_text('{"ticket": 1}\n{"ticket": 2}\n{"ticket": 3}\n', encoding="utf-8")
    agent.FINGERPRINT_FILE = f
    state = {"fingerprint_offset": f.stat().st_size}  # dosyanın sonuna işaretli

    f.write_text('{"ticket": 9}\n', encoding="utf-8")  # döndürüldü, küçüldü
    client = FakeMultiTableClient()
    n = agent.push_fingerprints(client, state)
    assert n == 1
    assert client.by_table["bot_entry_fingerprints"][0]["ticket"] == 9


# ── 2026-10-20: restart borcu ana döngünün eski state kopyasıyla silinmemeli ──
def test_pending_restart_survives_main_loop_save(agent, tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "STATE_FILE", tmp_path / "agent_state.json")
    state = agent.load_state()                       # ana döngü: açılışta yüklenen kopya (borç yok)
    state["last_deal_ts"] = 1
    agent.save_state(state)
    agent._queue_pending_restart("bot", "test")      # borç dosyaya yazılır
    state["last_deal_ts"] = 2
    agent.save_state(state)                          # ana döngü turu — borcu SİLMEMELİ
    disk = json.loads((tmp_path / "agent_state.json").read_text())
    assert disk["last_deal_ts"] == 2
    assert "bot" in disk[agent.PENDING_RESTART_KEY]


def test_paid_restart_not_resurrected(agent, tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "STATE_FILE", tmp_path / "agent_state.json")
    agent._queue_pending_restart("bot", "test")
    state = agent.load_state()                       # bellekte borçlu kopya
    st = agent.load_state(); st[agent.PENDING_RESTART_KEY] = {}
    agent.save_state(st, own_pending=True)           # borç ödendi
    agent.save_state(state)                          # eski kopya borcu geri getirmemeli
    disk = json.loads((tmp_path / "agent_state.json").read_text())
    assert disk[agent.PENDING_RESTART_KEY] == {}


# ── 2026-10-29: canlılık denetimi (bot 10-21→29 sessizce 8 gün ölüydü, E83) ──

MIN = 60.0


@pytest.mark.parametrize("proc, age, since, expected", [
    (False, 30.0, None, "restart"),            # süreç yok → ölü
    (True, 30.0, None, "ok"),                  # süreç var + log taze
    (True, 11 * MIN, None, "restart"),         # süreç var ama 11 dk sessiz → asılı
    (True, 600.0, None, "ok"),                 # eşiğin TAM kendisi henüz sessizlik değil
    (None, 11 * MIN, None, "restart"),         # süreç sorgusu patladı ama log ölü
    (None, 30.0, None, "ok"),                  # sorgu patladı, log taze → canlı
    (True, None, None, "ok"),                  # kalp atışı yazmayan eski sürüm → karar yok
    (False, None, None, "restart"),            # süreç yok, dosya da yok
    (None, None, None, "unknown"),             # hiçbir şey okunamadı → dokunma
    (False, 30.0, 5 * MIN, "cooldown"),        # 5 dk önce restart edildi → açılış payı
    (True, 20 * MIN, 5 * MIN, "cooldown"),
    (False, 30.0, 16 * MIN, "restart"),        # bekleme doldu → tekrar dene
])
def test_liveness_verdict(agent, proc, age, since, expected):
    action, reason = agent.liveness_verdict(proc, age, 600, since, 15 * MIN)
    assert action == expected
    assert (reason == "") == (expected == "ok")


def test_liveness_verdict_reason_names_hang(agent):
    _, reason = agent.liveness_verdict(True, 12 * MIN, 600, None, 900)
    assert "asılı" in reason
    _, reason = agent.liveness_verdict(False, 30.0, 600, None, 900)
    assert reason == "süreç yok"


@pytest.mark.parametrize("streak, expected_min", [(0, 15), (1, 15), (2, 30), (3, 60), (4, 120), (9, 120)])
def test_watchdog_cooldown_backs_off_and_caps(agent, streak, expected_min):
    assert agent.watchdog_cooldown_s(streak, 900, 7200) == expected_min * MIN


class FakeInsertClient:
    """`.table(x).insert(row).execute()` (panel izi) + heartbeat upsert'ünü sahteler."""

    def __init__(self):
        self.inserted: list[dict] = []
        self.upserted: list[dict] = []

    def table(self, name):
        self._t = name
        return self

    def insert(self, row):
        self.inserted.append(row)
        return self

    def upsert(self, row):
        self.upserted.append(row)
        return self

    def execute(self):
        return self


@pytest.fixture
def box(agent, tmp_path, monkeypatch):
    """Sahte kutu: bot/decider süreç tablosu + tazelik dosyaları + kill/start kaydı."""
    import os
    import time as _time

    bot_log = tmp_path / "demo_bot.log"
    dec_hb = tmp_path / "decider_heartbeat.json"
    bot_log.write_text("x", encoding="utf-8")
    dec_hb.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(agent, "WATCHDOG_SPECS", {
        "bot": {"file": bot_log, "stale_after_s": 600},
        "decider": {"file": dec_hb, "stale_after_s": 10800},
    })
    monkeypatch.setattr(agent, "WATCHDOG_STATE_FILE", tmp_path / "watchdog_state.json")
    monkeypatch.setattr(agent, "WATCHDOG_OFF_FILE", tmp_path / "WATCHDOG_OFF")
    monkeypatch.setattr(agent, "STATE_FILE", tmp_path / "agent_state.json")
    monkeypatch.setattr(agent.time, "sleep", lambda s: None)

    procs = {"forexsai_demo_bot.py": [111], "run_decider.py": [222]}
    calls = {"kill": [], "start": []}

    def _kill(match):
        calls["kill"].append(match)
        if not getattr(box_state, "unkillable", False):
            procs[match] = []
        return "ok"

    def _start(bat):
        calls["start"].append(bat)
        match = "forexsai_demo_bot.py" if "trade_bot" in bat else "run_decider.py"
        procs[match] = [999]
        return f"başlatıldı: {bat}"

    box_state = types.SimpleNamespace(procs=procs, calls=calls, bot_log=bot_log, dec_hb=dec_hb)
    monkeypatch.setattr(agent, "_pids_by_cmdline", lambda m: list(procs[m]) if procs[m] is not None else None)
    monkeypatch.setattr(agent, "_kill_by_cmdline", _kill)
    monkeypatch.setattr(agent, "_start_bat", _start)

    def age(path, seconds):
        t = _time.time() - seconds
        os.utime(path, (t, t))
    box_state.age = age
    return box_state


def test_healthy_bot_not_touched_and_heartbeat_reports_alive(agent, box):
    box.age(box.bot_log, 40)
    snap = agent.watchdog_tick(FakeInsertClient())
    assert snap["bot"]["action"] == "ok" and snap["bot"]["alive"] is True
    assert box.calls["kill"] == [] and box.calls["start"] == []

    client = FakeInsertClient()
    agent.push_heartbeat(client)
    meta = client.upserted[0]["meta"]
    assert meta["bot_alive"] is True
    assert meta["bot_log_age_s"] is not None and meta["bot_log_age_s"] < 120
    assert "bot_last_restart" in meta and meta["agent_version"] == "1.2"


def test_dead_bot_restarted_without_deferral_even_with_open_positions(agent, box):
    """10-21 vakası: süreç yok. Açık pozisyon ERTELEME sebebi olmamalı."""
    agent.mt5.positions_get = lambda: ("pos1", "pos2")
    box.procs["forexsai_demo_bot.py"] = []
    box.age(box.bot_log, 3 * 86400)
    client = FakeInsertClient()

    snap = agent.watchdog_tick(client)

    assert snap["bot"]["action"] == "restart" and snap["bot"]["alive"] is False
    assert box.calls["start"] == [r"calistir\2_oto_trade_bot.bat"]
    assert box.procs["forexsai_demo_bot.py"] == [999]
    trace = [r for r in client.inserted if r.get("requested_by") == "watchdog"]
    assert trace and trace[0]["payload"]["target"] == "bot" and trace[0]["return_code"] == 0
    wd = agent._load_wd()
    assert wd["restarts"]["bot"]["why"].startswith("watchdog: süreç yok")
    assert wd["streak"]["bot"] == 1


def test_hung_bot_with_silent_log_is_restarted(agent, box):
    """Süreç var ama log 15 dk sessiz (ör. konsol QuickEdit donması) → asılı → restart."""
    box.age(box.bot_log, 15 * MIN)
    snap = agent.watchdog_tick(FakeInsertClient())
    assert snap["bot"]["action"] == "restart"
    assert box.calls["kill"] == ["forexsai_demo_bot.py"]
    assert len(box.calls["start"]) == 1


def test_no_restart_storm_within_cooldown(agent, box):
    box.procs["forexsai_demo_bot.py"] = []
    agent.watchdog_tick(FakeInsertClient())
    box.procs["forexsai_demo_bot.py"] = []          # yeni bot da hemen çöktü
    snap = agent.watchdog_tick(FakeInsertClient())
    assert snap["bot"]["action"] == "cooldown"
    assert len(box.calls["start"]) == 1, "15 dk dolmadan ikinci restart atılmamalı"


def test_streak_resets_once_healthy(agent, box):
    box.procs["forexsai_demo_bot.py"] = []
    agent.watchdog_tick(FakeInsertClient())
    box.age(box.bot_log, 10)
    agent.watchdog_tick(FakeInsertClient())
    assert agent._load_wd()["streak"]["bot"] == 0


def test_watchdog_off_file_only_reports(agent, box):
    agent.WATCHDOG_OFF_FILE.write_text("", encoding="utf-8")
    box.procs["forexsai_demo_bot.py"] = []
    snap = agent.watchdog_tick(FakeInsertClient())
    assert snap["off"] is True and snap["bot"]["alive"] is False
    assert box.calls["start"] == []


def test_unknown_process_state_never_kills(agent, box):
    box.procs["forexsai_demo_bot.py"] = None        # PowerShell sorgusu patladı
    box.procs["run_decider.py"] = None
    box.bot_log.unlink()
    box.dec_hb.unlink()
    snap = agent.watchdog_tick(FakeInsertClient())
    assert snap["bot"]["action"] == "unknown" and snap["bot"]["alive"] is None
    assert box.calls["kill"] == []


def test_dead_decider_restarted(agent, box):
    box.procs["run_decider.py"] = []
    box.age(box.bot_log, 30)
    agent.watchdog_tick(FakeInsertClient())
    assert box.calls["start"] == [r"calistir\3_claude_decider.bat"]


def test_unkillable_process_blocks_second_instance(agent, box, monkeypatch):
    """Öldürülemeyen asılı bot varken ikinci kopya başlatılmaz (iki bot = çift emir)."""
    monkeypatch.setattr(agent, "_kill_by_cmdline", lambda m: "erişim reddedildi")
    out, rc = agent.restart_target("bot", force=True, why="test")
    assert rc == 4 and box.calls["start"] == []
    assert "restarts" not in agent._load_wd()


def test_watchdog_restart_pays_pending_debt_without_second_kill(agent, box, monkeypatch):
    """Borç yazılmışken denetim ölü botu kaldırdıysa borç kapanır; sağlıklı bot ikinci kez öldürülmez."""
    agent.mt5.positions_get = lambda: ("pos1",)
    st = {agent.PENDING_RESTART_KEY: {"bot": {"since": "2026-10-21T00:00:00+00:00", "commits": "3"}}}
    agent.save_state(st, own_pending=True)
    box.procs["forexsai_demo_bot.py"] = []
    agent.watchdog_tick(FakeInsertClient())          # ölü bot → restart (borçtan SONRA)
    n_start = len(box.calls["start"])

    agent.flush_pending_restarts(None)

    assert agent.load_state()[agent.PENDING_RESTART_KEY] == {}
    assert len(box.calls["start"]) == n_start, "borç ödemesi ikinci restart atmamalı"


def test_older_restart_does_not_pay_newer_debt(agent, box):
    agent._record_restart("bot", "eski")
    st = {agent.PENDING_RESTART_KEY: {"bot": {"since": "2099-01-01T00:00:00+00:00", "commits": "1"}}}
    agent.save_state(st, own_pending=True)
    agent.mt5.positions_get = lambda: ("pos1",)     # pozisyon açık → borç beklemeli
    agent.flush_pending_restarts(None)
    assert "bot" in agent.load_state()[agent.PENDING_RESTART_KEY]


def test_pids_by_cmdline_distinguishes_none_from_empty(agent, monkeypatch):
    res = types.SimpleNamespace(returncode=1, stdout="")
    monkeypatch.setattr(agent.subprocess, "run", lambda *a, **k: res)
    monkeypatch.setattr(agent.sys, "platform", "darwin")
    assert agent._pids_by_cmdline("forexsai_demo_bot.py") == []          # pgrep: eşleşme yok
    res.returncode, res.stdout = 0, "123\n456\n"
    assert agent._pids_by_cmdline("forexsai_demo_bot.py") == [123, 456]
    res.returncode = 2
    assert agent._pids_by_cmdline("forexsai_demo_bot.py") is None        # sorgu hatası

    def _boom(*a, **k):
        raise OSError("powershell yok")
    monkeypatch.setattr(agent.subprocess, "run", _boom)
    assert agent._pids_by_cmdline("x") is None


def test_pids_by_cmdline_windows_counts_only_python(agent, monkeypatch):
    seen = {}

    def _run(argv, **k):
        seen["ps"] = argv[-1]
        return types.SimpleNamespace(returncode=0, stdout="15680\r\n")
    monkeypatch.setattr(agent.subprocess, "run", _run)
    monkeypatch.setattr(agent.sys, "platform", "win32")
    assert agent._pids_by_cmdline("forexsai_demo_bot.py") == [15680]
    assert "$_.Name -like 'python*'" in seen["ps"]
    assert agent._ps_cmdline_filter("forexsai_demo_bot.py") in seen["ps"]
