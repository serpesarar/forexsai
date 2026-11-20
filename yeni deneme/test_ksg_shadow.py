"""KSG gölge modülü birim testleri (MT5 gerekmez, EMİR YOK). Çalıştır: cd 'yeni deneme' && python3 test_ksg_shadow.py"""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import ksg_shadow as gs

NY = ZoneInfo("America/New_York")


def bar(d: date, hh: int, mm: int, o: float) -> dict:
    t = int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY).astimezone(timezone.utc).timestamp())
    return {"t": t, "open": o, "high": o + 1, "low": o - 1, "close": o}


def session(d: date, o15: float, o16: float, base: float = 100.0) -> list[dict]:
    out, cur = [], datetime(d.year, d.month, d.day, 9, 30, tzinfo=NY)
    while (cur.hour, cur.minute) <= (16, 0):
        o = o15 if (cur.hour, cur.minute) == (15, 0) else o16 if (cur.hour, cur.minute) == (16, 0) else base
        out.append(bar(d, cur.hour, cur.minute, o))
        cur += timedelta(minutes=30)
    return out


def night(d: date, nd: date, o16: float, p1830: float | None, o930: float, o16n: float | None) -> list[dict]:
    b = session(d, o16 + 10, o16)
    if p1830 is not None:
        b.append(bar(d, 18, 30, p1830))
    b.append(bar(nd, 9, 30, o930))
    if o16n is not None:
        b.append(bar(nd, 16, 0, o16n))
    return sorted(b, key=lambda x: x["t"])


def test_no_signal_is_none():
    d = date(2026, 11, 10)
    assert gs.night_record(session(d, 100.0, 100.5), d) is None


def test_base_and_no_labels():
    d, nd = date(2026, 11, 10), date(2026, 11, 11)
    r = gs.night_record(night(d, nd, 10000.0, 10000.0, 10050.0, None), d)
    ask = 10000.0 + gs.SPREAD_MODEL
    assert r["tam"] and r["nd"] == "2026-11-11"
    assert abs(r["base_bp"] - ((10050 / ask - 1) * 1e4 - gs.FIN_BP_PER_DAY)) < 0.01
    assert r["kurtarma"] is False and r["ekleme"] is False and r["ek_birim_bp"] is None


def test_rescue_and_add():
    d, nd = date(2026, 11, 10), date(2026, 11, 11)
    r = gs.night_record(night(d, nd, 10000.0, 9950.0, 9920.0, 10010.0), d)    # 18:30 −51 bp, 09:30 −81 bp
    assert r["ekleme"] and r["kurtarma"] and r["tam"]
    assert abs(r["ek_birim_bp"] - ((9920 / (9950 + gs.SPREAD_MODEL) - 1) * 1e4 - gs.FIN_BP_PER_DAY)) < 0.01
    assert abs(r["kurtarma_fark_bp"] - (10010 - 9920) / (10000 + gs.SPREAD_MODEL) * 1e4) < 0.01


def test_rescue_waits_for_1600_bar():
    d, nd = date(2026, 11, 10), date(2026, 11, 11)
    r = gs.night_record(night(d, nd, 10000.0, 10000.0, 9900.0, None), d)
    assert r["kurtarma"] and not r["tam"]


def test_friday_no_1830_bar_and_monday_exit_and_opex():
    d, nd = date(2026, 11, 20), date(2026, 11, 23)                           # vade Cuması → OPEX vetolu, yine izlenir
    r = gs.night_record(night(d, nd, 10000.0, None, 10020.0, None), d)
    assert r["tam"] and r["ekleme"] is False and r["opex_veto"] and r["vadeye_gun"] == 0
    assert abs(r["base_bp"] - ((10020 / (10000 + gs.SPREAD_MODEL) - 1) * 1e4 - 3 * gs.FIN_BP_PER_DAY)) < 0.01


def test_fomc_tag():
    d, nd = date(2026, 12, 8), date(2026, 12, 9)                              # 9 Aralık FOMC
    assert gs.night_record(night(d, nd, 10000.0, 10000.0, 10000.0, None), d)["fomc_oncesi"]


def test_karne_empty(tmp=None):
    from pathlib import Path
    assert gs.karne(Path("/nonexistent/ksg.jsonl"))["gece"] == 0


if __name__ == "__main__":
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith("test_") and callable(f):
            f(); n += 1
    print(f"{n} test geçti")
