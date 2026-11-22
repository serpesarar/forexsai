"""caprev_live.py birim testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 test_caprev_live.py
Kartla tam sadakat (10 yıl, NDX 103/107 aynı tetik mumu, DAX 54/54): research/canli_kart_20261009/caprev_live_fidelity.py"""
from datetime import date, datetime, timedelta, timezone
import caprev_live as cl

NDX, DAX = cl.PROFILES["NDX.INDX"], cl.PROFILES["GDAXI.INDX"]


def bar(y, m, d, h, o, hi, lo, c):
    return {"t": datetime(y, m, d, h, tzinfo=timezone.utc).timestamp(), "open": o, "high": hi, "low": lo, "close": c}


def ndx_days(n=25, start=date(2026, 9, 1), drop_last=0.0):
    """n işlem günü, NY 09:00–16:00 (EDT → 13–19 UTC) yedi 1h bar; son gün kapanışı drop_last kadar düşer."""
    bars, d, px = [], start, 20000.0
    while len([b for b in bars if b["_h"] == 19]) < n:
        if d.weekday() < 5:
            last = len([b for b in bars if b["_h"] == 19]) == n - 1
            for h in range(13, 20):
                c = px * (1 + (drop_last if (last and h == 19) else 0.001 * (1 if h % 2 else -1)))
                bars.append({**bar(d.year, d.month, d.day, h, px, max(px, c) + 5, min(px, c) - 5, c), "_h": h})
                px = c
        d += timedelta(days=1)
    return bars, d


def test_stress_context_and_pdl():
    bars, nxt = ndx_days(25, drop_last=-0.02)
    ctx = cl.daily_context(cl.rth_days(bars, NDX), nxt)
    assert ctx is not None and ctx["stress"] and ctx["r1"] < -0.015
    last_day = max(cl.rth_days(bars, NDX))
    assert ctx["pdl"] == cl.rth_days(bars, NDX)[last_day]["low"]
    assert 0 < ctx["dvol"] < 0.05


def test_no_stress_on_normal_days():
    bars, nxt = ndx_days(25, drop_last=0.0)
    ctx = cl.daily_context(cl.rth_days(bars, NDX), nxt)
    assert ctx is not None and not ctx["stress"]


def test_trigger_window_ndx():
    today = date(2026, 10, 6)                       # Salı, EDT: NY 03:00 = 07:00Z, 15:00 = 19:00Z
    early = bar(2026, 10, 6, 6, 100, 101, 90, 95)   # NY 02:00 başlangıç → pencere dışı
    inwin = bar(2026, 10, 6, 8, 100, 101, 90, 95)   # NY 04:00
    late = bar(2026, 10, 6, 19, 100, 101, 90, 95)   # NY 15:00 başlangıç, bitiş 16:00 > 15:00 → dışı
    assert cl.trigger([early, inwin, late], NDX, today, 97) is inwin
    assert cl.trigger([early, late], NDX, today, 97) is None
    assert cl.trigger([inwin], NDX, today, 90) is None          # kapanış dibin altında değil


def test_trigger_window_dax_and_session_close():
    today = date(2026, 10, 6)                       # CEST: Berlin 08:00 = 06:00Z, 16:30 = 14:30Z
    b0 = bar(2026, 10, 6, 6, 100, 101, 90, 95)      # 08:00 → içinde
    b1 = bar(2026, 10, 6, 14, 100, 101, 90, 95)     # 16:00 başlangıç, bitiş 17:00 > 16:30 → dışı
    assert cl.trigger([b0, b1], DAX, today, 97) is b0
    assert cl.trigger([b1], DAX, today, 97) is None
    assert cl.session_close_utc(today, DAX) == datetime(2026, 10, 6, 16, 0, tzinfo=timezone.utc).timestamp()
    assert cl.session_close_utc(today, NDX) == datetime(2026, 10, 6, 20, 0, tzinfo=timezone.utc).timestamp()


def test_prev_day_vix_uses_strictly_earlier_day():
    h = {"2026-10-02": 19.0, "2026-10-05": 17.0, "2026-10-06": 25.0}
    assert cl.prev_day_vix(h, date(2026, 10, 6)) == 17.0
    assert cl.prev_day_vix(h, date(2026, 10, 5)) == 19.0
    assert cl.prev_day_vix({}, date(2026, 10, 5)) is None


if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1
    print(f"{n} test geçti")


# ── kâr çıkışı (2026-11-21, CD-04) ──
class _Cfg:
    MAGIC_NUMBER = 1000
    DEVIATION_POINTS = 10
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_kar_enabled_only_ndx_by_default():
    c = _Cfg()
    assert cl.kar_enabled(c, "NDX.INDX") and not cl.kar_enabled(c, "GDAXI.INDX")
    assert not cl.kar_enabled(_Cfg(CAPREV_KAR_EXIT=False), "NDX.INDX")


def test_kar_decision_matches_research_exit_index():
    assert cl.kar_decision(101.0, 100.0, 0) == "kar"
    assert cl.kar_decision(100.0, 100.0, 3) == "kar"          # ≥ giriş (exit_index cl[s] >= E)
    assert cl.kar_decision(99.0, 100.0, 4) is None
    assert cl.kar_decision(99.0, 100.0, cl.KAR_MAX_DAYS) == "sure"


def test_next_weekday_skips_weekend():
    assert cl.next_weekday(date(2026, 11, 20)) == date(2026, 11, 23)   # Cuma → Pazartesi
    assert cl.next_weekday(date(2026, 11, 17)) == date(2026, 11, 18)


class _Tick:
    def __init__(self, bid, t): self.bid, self.ask, self.time = bid, bid, t


class _Pos:
    ticket, symbol, volume = 7, "NAS100", 1.0


class _MT5:
    TRADE_ACTION_DEAL = ORDER_TYPE_SELL = ORDER_FILLING_IOC = 0
    TRADE_RETCODE_DONE = 10009
    def __init__(self, bid, t): self.tick, self.sent = _Tick(bid, t), []
    def symbol_info_tick(self, s): return self.tick
    def order_send(self, r):
        self.sent.append(r)
        class R: retcode = 10009
        return R()


class _Log:
    def info(self, *a): pass
    error = warning = info


def test_kar_check_holds_then_exits(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "LOG_JSONL", tmp_path / "l.jsonl")
    d0 = date(2026, 11, 19)                                     # Perşembe
    due = cl.session_close_utc(d0, cl.PROFILES["NDX.INDX"])
    meta = {"market": "NDX.INDX", "mode": "kar", "entry": 100.0, "step": 0, "entry_t": due - 3600, "exit_t": due}
    m = _MT5(99.0, due + 5)
    cl._kar_check(m, _Cfg(), _Log(), due + 5, _Pos(), meta)
    assert not m.sent and meta["step"] == 1
    assert meta["exit_t"] == cl.session_close_utc(date(2026, 11, 20), cl.PROFILES["NDX.INDX"])
    m2 = _MT5(100.5, meta["exit_t"] + 5)
    cl._kar_check(m2, _Cfg(), _Log(), meta["exit_t"] + 5, _Pos(), meta)
    assert len(m2.sent) == 1


def test_kar_check_stale_tick_does_not_count_day(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "LOG_JSONL", tmp_path / "l.jsonl")
    due = cl.session_close_utc(date(2026, 11, 26), cl.PROFILES["NDX.INDX"])   # Şükran günü
    meta = {"market": "NDX.INDX", "mode": "kar", "entry": 100.0, "step": 2, "entry_t": due - 86400, "exit_t": due}
    m = _MT5(99.0, due - 20 * 3600)
    cl._kar_check(m, _Cfg(), _Log(), due + 5, _Pos(), meta)
    assert not m.sent and meta["step"] == 2


# ── KQ-03 tutuş koruması ──
def test_kar_decision_guard_rules():
    g = {"dvol": 0.02, "clv": 0.4, "vixchg": None}
    assert cl.kar_decision(99.2, 100.0, 0, g) is None                 # z = −0,4 → tut
    assert cl.kar_decision(98.9, 100.0, 0, g) == "tutma_yok"          # z = −0,55 → çık
    assert cl.kar_decision(99.5, 100.0, 0, {**g, "clv": 0.0}) == "tutma_yok"
    assert cl.kar_decision(99.0, 100.0, 2, {**g, "vixchg": 0.12}) == "vix"
    assert cl.kar_decision(99.0, 100.0, 2, {**g, "vixchg": 0.05}) is None
    assert cl.kar_decision(98.0, 100.0, 0, None) is None              # korumasız


class _MT5G(_MT5):
    TIMEFRAME_H1, TRADE_ACTION_SLTP = 1, 6
    def __init__(self, bid, t, bars=None):
        super().__init__(bid, t)
        self.bars = bars
    def copy_rates_from_pos(self, *a): return self.bars
    def symbol_info(self, s):
        class I: digits = 2
        return I()


def test_guarded_hold_moves_stop_and_vix_exit(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "LOG_JSONL", tmp_path / "l.jsonl")
    d0 = date(2026, 11, 19)
    prof = cl.PROFILES["NDX.INDX"]
    due = cl.session_close_utc(d0, prof)
    bars = [{"time": int(cl.cs.local_to_utc(d0, m, "US")), "open": 100, "high": 101, "low": 98.5, "close": 99.5}
            for m in range(540, 960, 60)]
    meta = {"market": "NDX.INDX", "mode": "kar", "entry": 100.0, "step": 0, "entry_t": due - 3600, "exit_t": due,
            "dvol": 0.02, "vix0": 20.0}
    m = _MT5G(99.5, due + 5, bars)                                    # z = −0,25, clv > 0 → tut + stop 97,00
    cl._kar_check(m, _Cfg(), _Log(), due + 5, _Pos(), meta, 0, lambda: 21.0)
    assert meta["step"] == 1 and len(m.sent) == 1 and m.sent[0]["action"] == 6 and m.sent[0]["sl"] == 97.0
    m2 = _MT5G(99.6, meta["exit_t"] + 5)
    cl._kar_check(m2, _Cfg(), _Log(), meta["exit_t"] + 5, _Pos(), meta, 0, lambda: 22.5)   # VIX +%12,5 → çık
    assert len(m2.sent) == 1 and m2.sent[0]["type"] == 0


def test_guarded_d0_deep_loss_exits(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "LOG_JSONL", tmp_path / "l.jsonl")
    due = cl.session_close_utc(date(2026, 11, 19), cl.PROFILES["NDX.INDX"])
    meta = {"market": "NDX.INDX", "mode": "kar", "entry": 100.0, "step": 0, "entry_t": due - 3600, "exit_t": due,
            "dvol": 0.02, "vix0": 20.0}
    m = _MT5G(98.8, due + 5, None)                                    # z = −0,6
    cl._kar_check(m, _Cfg(), _Log(), due + 5, _Pos(), meta, 0, None)
    assert len(m.sent) == 1 and "position" in m.sent[0]


# ── KQ-06 bölünmüş giriş + yarım tutuş ──
def test_split_decision_rules():
    assert cl.split_decision(100.0, 100.0, 0, False) == "kar"
    assert cl.split_decision(99.0, 100.0, 0, False) == "yarim"
    assert cl.split_decision(99.0, 100.0, 1, True) is None
    assert cl.split_decision(99.0, 100.0, cl.KAR_MAX_DAYS, True) == "sure"


def test_round_volume():
    class I: volume_step, volume_min = 0.1, 0.1
    assert cl.round_volume(0.5, I()) == 0.5
    assert cl.round_volume(0.25, I()) == 0.2
    assert cl.round_volume(0.05, I()) == 0.0


class _Info:
    digits, volume_step, volume_min = 2, 0.01, 0.01


class _MT5S(_MT5G):
    ORDER_TYPE_BUY, ORDER_TIME_GTC = 0, 0
    def symbol_info(self, s): return _Info()
    def terminal_info(self):
        class T: trade_allowed = True
        return T()


class _PosV:
    ticket, symbol = 9, "NAS100"
    def __init__(self, v): self.volume = v


def test_split_enter_schedules_b_and_b_opens_at_close(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "LOG_JSONL", tmp_path / "l.jsonl")
    d0 = date(2026, 11, 19)
    prof = cl.PROFILES["NDX.INDX"]
    close = cl.session_close_utc(d0, prof)
    m = _MT5S(100.0, close - 3600)
    st = {"fired": {}}
    sent = []
    class R:
        retcode, order = 10009, 111
    def send(req, sym):
        sent.append(req); return R()
    ctx = {"dvol": 0.02}
    base = {"vix": 25.0, "latency_s": 5.0}
    cl._enter(m, _Cfg(LIVE_TRADING=True, CAPREV_LIVE_LOT=1.0, CAPREV_NDX_LOT=1.0), _Log(), "NDX.INDX", "NAS100", prof, d0, ctx, base, close - 3600,
              st, True, send, lambda a, b: a + b, lambda: True, lambda *a: None)
    assert sent[0]["volume"] == 0.5 and sent[0]["sl"] == 94.0
    assert st["pos"]["111"]["mode"] == "split" and st["pos"]["111"]["part"] == "A"
    pb = st["pending_b"]["NDX.INDX|2026-11-19"]
    assert pb["lot"] == 0.5 and pb["due"] == close
    m2 = _MT5S(98.0, close + 10)
    cl._open_split_b(m2, _Cfg(), _Log(), close + 10, st)
    assert not st["pending_b"] and m2.sent[0]["volume"] == 0.5 and m2.sent[0]["sl"] == round(98.0 * 0.94, 2)
    b = [v for k, v in st["pos"].items() if v.get("part") == "B"][0]
    assert b["exit_t"] == cl.session_close_utc(date(2026, 11, 20), prof) and b["step"] == 0


def test_split_check_partial_then_profit(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "LOG_JSONL", tmp_path / "l.jsonl")
    prof = cl.PROFILES["NDX.INDX"]
    due = cl.session_close_utc(date(2026, 11, 19), prof)
    meta = {"market": "NDX.INDX", "mode": "split", "part": "A", "entry": 100.0, "step": 0, "entry_t": due - 3600, "exit_t": due}
    m = _MT5S(99.0, due + 5)
    cl._split_check(m, _Cfg(), _Log(), due + 5, _PosV(0.5), meta)
    assert len(m.sent) == 1 and m.sent[0]["volume"] == 0.25 and meta["partial_done"] and meta["step"] == 1
    m2 = _MT5S(99.5, meta["exit_t"] + 5)
    cl._split_check(m2, _Cfg(), _Log(), meta["exit_t"] + 5, _PosV(0.25), meta)
    assert not m2.sent and meta["step"] == 2                      # hâlâ zarar → tut, ikinci yarım kapanış YOK
    m3 = _MT5S(100.2, meta["exit_t"] + 5)
    cl._split_check(m3, _Cfg(), _Log(), meta["exit_t"] + 5, _PosV(0.25), meta)
    assert len(m3.sent) == 1 and m3.sent[0]["volume"] == 0.25


def test_split_b_late_is_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "LOG_JSONL", tmp_path / "l.jsonl")
    st = {"pending_b": {"k": {"market": "NDX.INDX", "sym": "NAS100", "due": 1000.0, "lot": 0.5, "dvol": 0.02}}}
    m = _MT5S(100.0, 5000)
    cl._open_split_b(m, _Cfg(), _Log(), 1000.0 + cl.MAX_LATE_S + 5, st)
    assert not m.sent and not st["pending_b"]


def test_ndx_default_lot_is_0_4(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "LOG_JSONL", tmp_path / "l.jsonl")
    d0 = date(2026, 11, 19)
    prof = cl.PROFILES["NDX.INDX"]
    close = cl.session_close_utc(d0, prof)
    sent, st = [], {"fired": {}}
    class R:
        retcode, order = 10009, 7
    cl._enter(_MT5S(100.0, close - 3600), _Cfg(LIVE_TRADING=True, CAPREV_LIVE_LOT=1.0), _Log(), "NDX.INDX", "NAS100", prof, d0,
              {"dvol": 0.02}, {"vix": 25.0, "latency_s": 1.0}, close - 3600, st, True, lambda r, s_: (sent.append(r), R())[1],
              lambda a, b: a + b, lambda: True, lambda *a: None)
    assert sent[0]["volume"] == 0.2 and st["pending_b"]["NDX.INDX|2026-11-19"]["lot"] == 0.2
