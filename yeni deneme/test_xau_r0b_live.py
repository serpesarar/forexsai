"""xau_r0b_live.py birim testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 test_xau_r0b_live.py
Uçtan uca araştırma paritesi (Duka 2008-26): research/xau_best_days_20261015/golge_parite/live_parity.py
→ n 3.296 / ort +0,1093R / isabet %36,4 (araştırma 3.259 / +0,1095R / %36,3)."""
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

import kural_katalogu as kk
import xau_r0b_live as xl

H = 3600
T0 = int(datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc).timestamp())      # Salı 00:00 UTC


def bar(t, o, h, l, c):
    return {"t": t, "open": o, "high": h, "low": l, "close": c}


def flat(n=40, px=4000.0, start=T0):
    return [bar(start + i * H, px, px + 5, px - 5, px) for i in range(n)]


def test_signal_and_no_signal():
    b = flat()
    assert xl.evaluate(b)[0] is not None                       # eşit tepe de sinyal (araştırma: high ≥ önceki 20 max)
    b = flat()
    b[-1] = bar(b[-1]["t"], 4000, 4004, 3995, 4000)            # tepe altında
    assert xl.evaluate(b) == (None, None)
    b[-1] = bar(b[-1]["t"], 4000, 4020, 3998, 4018)            # yeni tepe
    sig, why = xl.evaluate(b)
    assert why is None and sig["sig_high"] == 4020 and abs(sig["stop_dist"] - 1.5 * sig["atr"]) < 1e-9


def test_s2_skip_after_big_up_day():
    # dün (UTC) kapanış önceki güne göre +%2 → atla
    b = [bar(T0 - 48 * H + i * H, 3900, 3905, 3895, 3900) for i in range(24)]
    b += [bar(T0 - 24 * H + i * H, 3978, 3983, 3973, 3978) for i in range(24)]
    b += [bar(T0 + i * H, 3978, 3983, 3973, 3978) for i in range(5)]
    b[-1] = bar(b[-1]["t"], 3978, 4050, 3975, 4040)
    sig, why = xl.evaluate(b)
    assert sig is None and why.startswith("S2")
    sig, why = xl.evaluate(b, thr=0.05)                        # eşik ezilirse açılır
    assert sig is not None


def test_exit_reasons():
    entry = T0 + 10 * H
    b = flat(60)
    assert xl.exit_reason([x for x in b if x["t"] < entry + 19 * H], entry, entry + 19 * H) is None
    assert xl.exit_reason([x for x in b if x["t"] < entry + 20 * H], entry, entry + 20 * H).startswith("20 bar")
    gap = [x for x in b if x["t"] < entry + 3 * H] + [bar(entry + 8 * H, 4000, 4005, 3995, 4000)]
    assert "segment" in xl.exit_reason(gap, entry, entry + 9 * H)
    fri = datetime(2026, 11, 13, 21, 55, tzinfo=timezone.utc).timestamp()      # Cuma 16:55 NY (EST)
    assert "Cuma" in xl.exit_reason(flat(3, start=int(fri) - 3 * H), int(fri) - 3 * H, fri)


# ───────── sahte MT5 ile akış ─────────
class FakeMT5:
    TIMEFRAME_H1 = 16385; TRADE_ACTION_DEAL = 1; ORDER_TYPE_BUY = 0; ORDER_TYPE_SELL = 1; ORDER_TIME_GTC = 0
    TRADE_RETCODE_DONE = 10009; POSITION_TYPE_SELL = 1

    def __init__(self, bars, now):
        self.bars, self.now, self.positions, self.sent = bars, now, [], []

    def copy_rates_from_pos(self, sym, tf, start, n):
        rows = self.bars[-n:]
        return [{"time": x["t"], "open": x["open"], "high": x["high"], "low": x["low"], "close": x["close"]} for x in rows]

    def symbol_info_tick(self, sym):
        return types.SimpleNamespace(ask=4020.5, bid=4020.2, time=self.now)

    def symbol_info(self, sym):
        return types.SimpleNamespace(digits=2)

    def positions_get(self, symbol=None):
        return list(self.positions)


def _setup(tmp):
    xl.STATE_FILE = Path(tmp) / "st.json"
    kk.EVENTS_JSONL = Path(tmp) / "ev.jsonl"
    xl._last_poll = 0.0
    cfg = types.SimpleNamespace(MAGIC_NUMBER=1000, LIVE_TRADING=True, DEVIATION_POINTS=30)
    b = flat()
    b[-1] = bar(b[-1]["t"], 4000, 4020, 3998, 4018)
    now = b[-1]["t"] + H + 30
    mt5 = FakeMT5(b, now)

    def send(req, sym):
        mt5.sent.append(req)
        if req["type"] == mt5.ORDER_TYPE_BUY and "position" not in req:
            mt5.positions.append(types.SimpleNamespace(ticket=77, magic=req["magic"], volume=req["volume"], symbol=sym,
                                                       time=now, type=0, price_open=req["price"]))
        else:
            mt5.positions = [p for p in mt5.positions if p.ticket != req.get("position")]
        return types.SimpleNamespace(retcode=10009, order=77)
    log = types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
    args = lambda: (mt5, cfg, log, lambda s: "XAUUSD", lambda: None, lambda s: 0, send, lambda p, t: (p + t)[:28],
                    lambda: True, lambda *a: None)
    return mt5, cfg, log, send, args, now


def test_poll_opens_once_with_sl_and_no_tp():
    with tempfile.TemporaryDirectory() as tmp:
        mt5, cfg, log, send, args, now = _setup(tmp)
        xl.poll(*args(), now=now)
        assert len(mt5.sent) == 1
        r = mt5.sent[0]
        assert r["type"] == 0 and r["tp"] == 0.0 and r["volume"] == 0.05 and r["magic"] == 1014
        sig, _ = xl.evaluate(mt5.bars)
        assert abs(r["sl"] - round(4020.5 - sig["stop_dist"], 2)) < 1e-9
        xl._last_poll = 0.0
        xl.poll(*args(), now=now + 60)                             # aynı bar → ikinci emir yok
        assert len(mt5.sent) == 1


def test_poll_ignores_late_signal():
    with tempfile.TemporaryDirectory() as tmp:
        mt5, cfg, log, send, args, now = _setup(tmp)
        xl.poll(*args(), now=now + xl.MAX_LATE_S + 5)
        assert mt5.sent == []


def test_disabled_flag_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        mt5, cfg, log, send, args, now = _setup(tmp)
        cfg.XAU_R0B_LIVE = False
        xl.poll(*args(), now=now)
        assert mt5.sent == []


def test_manage_exits_after_20_bars():
    with tempfile.TemporaryDirectory() as tmp:
        mt5, cfg, log, send, args, now = _setup(tmp)
        xl.poll(*args(), now=now)
        assert len(mt5.positions) == 1
        entry_bar = mt5.bars[-1]["t"] + H
        mt5.bars += [bar(entry_bar + j * H, 4020, 4025, 4015, 4020) for j in range(19)]
        xl.manage_exits(mt5, cfg, log, send, lambda s: 0, lambda s: "XAUUSD", now=entry_bar + 19 * H + 30)
        assert len(mt5.positions) == 1                             # 19 bar → sürüyor
        mt5.bars.append(bar(entry_bar + 19 * H, 4020, 4025, 4015, 4020))
        xl.manage_exits(mt5, cfg, log, send, lambda s: 0, lambda s: "XAUUSD", now=entry_bar + 20 * H + 30)
        assert mt5.positions == [] and mt5.sent[-1]["type"] == 1  # BUY pozisyonu SELL ile kapandı


if __name__ == "__main__":
    import sys
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try:
                f(); print("✓", k)
            except Exception as e:                                  # noqa: BLE001
                fails += 1; print("✗", k, repr(e))
    sys.exit(1 if fails else 0)
