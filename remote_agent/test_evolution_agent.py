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
from datetime import datetime
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
    fake_mt5.account_info = lambda: None
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
        match = ("forexsai_demo_bot.py" if "trade_bot" in bat
                 else "dbg_klon_runner.py" if "dbg_klon" in bat else "run_decider.py")
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
    assert "bot_last_restart" in meta and meta["agent_version"] == "1.5"


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


@pytest.fixture
def klon(agent, box, tmp_path, monkeypatch):
    """DBG klon koşucusu izlenen hedeflere eklenmiş kutu."""
    log_file, stop = tmp_path / "dbg_klon_log.jsonl", tmp_path / "DBG_KLON_DURDUR"
    log_file.write_text("x", encoding="utf-8")
    agent.WATCHDOG_SPECS["dbg_klon"] = {"file": log_file, "stale_after_s": 900, "off_file": stop}
    monkeypatch.setattr(agent, "WATCHDOG_WATCH", ("dbg_klon",))
    box.procs["dbg_klon_runner.py"] = [333]
    box.klon_log, box.klon_stop = log_file, stop
    return box


def test_dbg_klon_is_watched_by_default_and_bat_exists(agent):
    assert "dbg_klon" in agent.WATCHDOG_WATCH
    target = agent.DEFAULT_PROCESS_TARGETS["dbg_klon"]
    assert (REPO / target["bat"].replace("\\", "/")).exists()
    assert not target.get("safe_wait")      # gölge: açık pozisyon beklemez
    assert ("calistir/dbg_klon/", "dbg_klon") in agent.AUTO_RESTART_MAP


def test_dead_dbg_klon_restarted_and_reported(agent, klon):
    """11-02 vakası: koşucu sessizce durdu, kimse fark etmedi."""
    klon.procs["dbg_klon_runner.py"] = []
    client = FakeInsertClient()

    snap = agent.watchdog_tick(client)

    assert snap["dbg_klon"]["action"] == "restart"
    assert klon.calls["start"] == [r"calistir\19_dbg_klon_golge.bat"]
    assert [r["payload"]["target"] for r in client.inserted if r.get("requested_by") == "watchdog"] == ["dbg_klon"]
    assert snap["dbg_klon"]["alive"] is False
    agent.watchdog_tick(FakeInsertClient())     # sonraki tur: geri geldi, restart izi görünür
    client = FakeInsertClient()
    agent.push_heartbeat(client)
    meta = client.upserted[0]["meta"]
    assert meta["dbg_klon_alive"] is True and meta["dbg_klon_last_restart"]


def test_dbg_klon_heartbeat_gap_is_not_a_hang_but_15_min_silence_is(agent, klon):
    klon.age(klon.klon_log, 301)            # kutuda ölçülen en uzun nabız boşluğu
    assert agent.watchdog_tick(FakeInsertClient())["dbg_klon"]["action"] == "ok"
    assert klon.calls["start"] == []

    klon.age(klon.klon_log, 901)
    assert agent.watchdog_tick(FakeInsertClient())["dbg_klon"]["action"] == "restart"
    assert klon.calls["kill"] == ["dbg_klon_runner.py"]


def test_dbg_klon_stop_file_prevents_restart(agent, klon):
    """Toplam kesici ya da kullanıcı durdurduysa denetim geri kaldırmamalı."""
    klon.procs["dbg_klon_runner.py"] = []
    klon.klon_stop.write_text("toplam_kesici", encoding="utf-8")

    snap = agent.watchdog_tick(FakeInsertClient())

    assert snap["dbg_klon"]["action"] == "stopped" and snap["dbg_klon"]["alive"] is None
    assert klon.calls["kill"] == [] and klon.calls["start"] == []
    client = FakeInsertClient()
    agent.push_heartbeat(client)
    assert client.upserted[0]["meta"]["dbg_klon_stopped"] is True


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


# ── Sağlık denetimi (2026-11-02: hesap düştü + CLI logout, kalp atışı yeşildi) ──

@pytest.mark.parametrize("iso,expected", [
    ("2026-11-02T18:00", True),     # Pazartesi seans
    ("2026-11-02T21:00", False),    # günlük boşluk
    ("2026-11-02T23:45", True),     # boşluk bitti
    ("2026-11-06T20:00", True),     # Cuma kapanış öncesi
    ("2026-11-06T21:00", False),    # Cuma kapanış sonrası
    ("2026-11-07T12:00", False),    # Cumartesi
    ("2026-11-08T12:00", False),    # Pazar açılış öncesi
    ("2026-11-08T23:45", True),     # Pazar açılış sonrası
])
def test_market_expected_open(agent, iso, expected):
    assert agent.market_expected_open(datetime.fromisoformat(iso)) is expected


def _codes(issues):
    return [i["code"] for i in issues]


def test_health_issues_reports_each_failure(agent):
    assert _codes(agent.health_issues(False, 9999, True, False, 71)) == [
        "mt5_disconnected", "claude_logged_out", "decider_llm_failing"]
    assert _codes(agent.health_issues(True, 1300, True, True, 0)) == ["mt5_ticks_stale"]


def test_health_issues_quiet_when_healthy_closed_or_unmeasured(agent):
    assert agent.health_issues(True, 5, True, True, 0) == []
    assert agent.health_issues(True, 99999, False, True, 0) == []       # hafta sonu
    assert agent.health_issues(None, None, True, None, 0) == []         # ölçülemedi
    assert agent.health_issues(True, 5, True, True, 4) == []            # tekil hatalar


def test_health_issues_bot_log_and_recorder(agent):
    stale = agent.WATCHDOG_SPECS["bot"]["stale_after_s"]
    assert _codes(agent.health_issues(True, 5, True, True, 0, stale + 1, False)) == [
        "bot_log_silent", "recorder_down"]
    assert agent.health_issues(True, 5, True, True, 0, stale, True) == []
    assert agent.health_issues(True, 5, True, True, 0, None, None) == []  # ölçülemedi


def test_process_health_measures_log_age_and_recorder(agent, tmp_path, monkeypatch):
    log_file = tmp_path / "demo_bot.log"
    log_file.write_text("x", encoding="utf-8")
    monkeypatch.setitem(agent.WATCHDOG_SPECS["bot"], "file", log_file)
    monkeypatch.setattr(agent, "_pids_by_cmdline", lambda m: [])
    measured = agent.process_health()
    assert measured["recorder_alive"] is False and measured["bot_log_age_s"] < 60

    log_file.unlink()
    monkeypatch.setattr(agent, "_pids_by_cmdline", lambda m: None)
    assert agent.process_health() == {"bot_log_age_s": None, "recorder_alive": None}


def test_tick_age_ignores_broker_clock_and_grows_when_frozen(agent, monkeypatch):
    term = types.SimpleNamespace(connected=True)
    tick = types.SimpleNamespace(time=1_000_000_000, time_msc=1)    # saat anlamsız olabilir
    agent.mt5.terminal_info = lambda: term
    agent.mt5.account_info = lambda: types.SimpleNamespace(login=7, server="S")
    agent.mt5.symbol_info_tick = lambda sym: tick
    clock = {"now": 1000.0}
    monkeypatch.setattr(agent.time, "time", lambda: clock["now"])
    assert agent.mt5_health()["mt5_tick_age_s"] == 0
    clock["now"] = 1500.0
    measured = agent.mt5_health()
    assert measured["mt5_tick_age_s"] == 500 and measured["mt5_connected"] is True
    tick = types.SimpleNamespace(time=1_000_000_000, time_msc=2)
    assert agent.mt5_health()["mt5_tick_age_s"] == 0


def test_lost_ipc_counts_as_disconnected(agent):
    agent.mt5.terminal_info = lambda: None
    agent.mt5.account_info = lambda: None
    agent.mt5.symbol_info_tick = lambda sym: None
    measured = agent.mt5_health()
    assert measured["mt5_connected"] is False and measured["mt5_error"]


def test_claude_auth_parses_and_caches(agent, monkeypatch):
    calls = []

    def run(*a, **k):
        calls.append(a)
        return types.SimpleNamespace(stdout=json.dumps({"loggedIn": False}))
    monkeypatch.setattr(agent.subprocess, "run", run)
    assert agent.claude_logged_in() is False
    assert agent.claude_logged_in() is False
    assert len(calls) == 1


def test_claude_auth_unreadable_is_unknown_not_failure(agent, monkeypatch):
    monkeypatch.setattr(agent.subprocess, "run",
                        lambda *a, **k: types.SimpleNamespace(stdout="not json"))
    assert agent.claude_logged_in() is None


def test_llm_error_streak_counts_only_latest_run(agent, tmp_path):
    bad = {"decision": {"action": "WAIT", "reason": "claude exit 1 | stderr: "}}
    good = {"decision": {"action": "OPEN", "reason": "kanıt"}}
    journal = tmp_path / "journal.jsonl"
    lines = [bad, good, bad, {"outcome": 1}, bad, bad]
    journal.write_text("\n".join(json.dumps(x) for x in lines) + "\nbozuk{\n", encoding="utf-8")
    assert agent.decider_llm_error_streak(journal) == 3
    assert agent.decider_llm_error_streak(tmp_path / "yok.jsonl") == 0
    assert agent.decider_llm_error_streak(None) == 0


def test_llm_error_streak_drops_truncated_first_line(agent, tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "DECIDER_JOURNAL_TAIL_BYTES", 120)
    journal = tmp_path / "journal.jsonl"
    row = json.dumps({"decision": {"reason": "claude exit 1"}, "pad": "x" * 30})
    journal.write_text("\n".join([row] * 10) + "\n", encoding="utf-8")
    assert 0 < agent.decider_llm_error_streak(journal) <= 2


@pytest.fixture
def health_box(agent, tmp_path, monkeypatch):
    state = types.SimpleNamespace(connected=False)
    monkeypatch.setattr(agent, "WATCHDOG_STATE_FILE", tmp_path / "wd.json")
    monkeypatch.setattr(agent, "mt5_health", lambda: {"mt5_connected": state.connected,
                                                      "mt5_tick_age_s": 1})
    monkeypatch.setattr(agent, "process_health", lambda: {"bot_log_age_s": 1, "recorder_alive": True})
    monkeypatch.setattr(agent, "claude_logged_in", lambda: True)
    monkeypatch.setattr(agent, "decider_llm_error_streak", lambda p: 0)
    return state


def _alerts(client):
    return [r for r in client.inserted if r.get("requested_by") == "health"]


def test_health_tick_alerts_once_after_two_rounds_then_on_recovery(agent, health_box):
    client = FakeInsertClient()
    first = agent.health_tick(client)               # tek tur: kısa kopuş olabilir
    assert first["health_ok"] is True and _alerts(client) == []

    second = agent.health_tick(client)
    assert second["health_ok"] is False
    assert [i["code"] for i in second["health_issues"]] == ["mt5_disconnected"]
    assert [a["status"] for a in _alerts(client)] == ["failed"]

    agent.health_tick(client)                       # aynı sorun: yeni uyarı yok
    assert len(_alerts(client)) == 1

    health_box.connected = True
    assert agent.health_tick(client)["health_ok"] is True
    assert [a["status"] for a in _alerts(client)] == ["failed", "done"]


def test_health_alert_not_repeated_after_agent_restart(agent, health_box):
    client = FakeInsertClient()
    agent.health_tick(client)
    agent.health_tick(client)
    agent.HEALTH = {}                               # ajan yeniden başladı
    agent.health_tick(client)
    agent.health_tick(client)
    assert len(_alerts(client)) == 1


def test_heartbeat_mt5_field_is_real_connection_not_import(agent, health_box):
    agent.health_tick(None)
    client = FakeInsertClient()
    agent.push_heartbeat(client)
    meta = client.upserted[0]["meta"]
    assert meta["mt5"] is False and "health_ok" in meta and "raw_codes" not in meta


def test_health_tick_never_restarts_anything(agent, health_box, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("sağlık denetimi restart atmamalı")
    monkeypatch.setattr(agent, "restart_target", boom)
    agent.health_tick(FakeInsertClient())
    agent.health_tick(FakeInsertClient())


def test_dbg_izleyici_is_watched_by_default_and_bat_exists(agent):
    assert "dbg_izleyici" in agent.WATCHDOG_WATCH
    target = agent.DEFAULT_PROCESS_TARGETS["dbg_izleyici"]
    assert (REPO / target["bat"].replace("\\", "/")).exists()
    assert not target.get("safe_wait")
    assert ("calistir/dbg_izleyici/", "dbg_izleyici") in agent.AUTO_RESTART_MAP


@pytest.mark.parametrize("server,expected", [("Pepperstone-Demo", True), ("DBGMarkets-Live", False)])
def test_mt5_connect_refuses_dbg_terminal(agent, monkeypatch, server, expected):
    """İkinci terminale takılırsa başkasının işlemleri bot_trades'e yazılırdı."""
    calls = []
    fake = types.SimpleNamespace(initialize=lambda *a, **k: True, last_error=lambda: (1, "ok"),
                                 account_info=lambda: types.SimpleNamespace(server=server),
                                 shutdown=lambda: calls.append("shutdown"))
    monkeypatch.setattr(agent, "mt5", fake, raising=False)
    monkeypatch.setattr(agent, "HAS_MT5", True)
    assert agent.mt5_connect() is expected
    assert calls == ([] if expected else ["shutdown"])


@pytest.mark.parametrize("target,pids,skip", [
    ("backend", [], True),        # kapalı backend güncellemede açılmaz
    ("backend", None, True),      # süreç sorgusu başarısız: emin olmadan açma
    ("backend", [123], False),    # çalışıyorsa yeni kodla yenilenir
    ("bot", [], False),           # diğer hedefler eskisi gibi
    ("recorder", [], False),
])
def test_oto_guncelleme_kapali_backendi_acmaz(agent, target, pids, skip):
    assert agent.should_skip_auto_restart(target, agent.DEFAULT_PROCESS_TARGETS, lambda _m: pids) is skip
