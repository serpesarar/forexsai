"""KORKU canlı modülü birim testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 test_korku_live.py (pytest de olur).
Araştırma motoruyla sadakat: research/korku_evren_20261119/src/canli_parite.py."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import korku_live as kl
import kural_katalogu as kk

NY = ZoneInfo("America/New_York")


def day_bars(d: date, closes: list[float], o15: float, p16: float) -> list[dict]:
    """09:30…15:30 (13 bar) kapanışları `closes`, 15:00 barı açılışı o15, 16:00 barı açılışı p16."""
    bars, cur = [], datetime(d.year, d.month, d.day, 9, 30, tzinfo=NY)
    for i in range(14):
        t = int(cur.astimezone(timezone.utc).timestamp())
        hm = (cur.hour, cur.minute)
        o = o15 if hm == (15, 0) else p16 if hm == (16, 0) else 100.0
        c = closes[i] if i < 13 else p16
        bars.append({"t": t, "open": o, "high": max(o, c) + 1, "low": min(o, c) - 1, "close": c})
        cur += timedelta(minutes=30)
    return bars


def test_signal_t30():
    d = date(2026, 11, 10)                                        # Salı, vadeye uzak değil ama sinyal ayrı test
    tab = kl.day_table(day_bars(d, [100.0] * 13, 99.9, 99.6))      # TWAP 100, P16 99,6 → −40 bp; son saat aşağı
    s = kl.find_signal(tab, d)
    assert s and abs(s["twap_bp"] + 40) < 1e-6 and s["son_saat_bp"] < 0


def test_no_signal_threshold_or_last_hour_up():
    d = date(2026, 11, 10)
    assert kl.find_signal(kl.day_table(day_bars(d, [100.0] * 13, 99.7, 99.75)), d) is None    # −25 bp > −30
    assert kl.find_signal(kl.day_table(day_bars(d, [100.0] * 13, 99.5, 99.6)), d) is None     # son saat yukarı
    assert kl.find_signal(kl.day_table(day_bars(d, [100.0] * 13, 99.6, 99.6)), d) is None     # son saat düz (strict <)


def test_holiday_and_weekend_no_signal():
    hol = date(2026, 11, 26)                                       # Şükran günü
    assert kl.find_signal(kl.day_table(day_bars(hol, [100.0] * 13, 99.9, 99.0)), hol) is None
    sat = date(2026, 11, 14)
    assert kl.find_signal(kl.day_table(day_bars(sat, [100.0] * 13, 99.9, 99.0)), sat) is None


def test_opex_calendar():
    assert kl.opex_day(2026, 11) == date(2026, 11, 20)
    assert kl.opex_day(2027, 3) == date(2027, 3, 19)
    assert kl.opex_day(2025, 4) == date(2025, 4, 17)               # 3. Cuma (18 Nisan) İyi Cuma tatili → Perşembe
    assert kl.days_to_opex(date(2026, 11, 20)) == 0
    assert kl.days_to_opex(date(2026, 11, 18)) == 2 and kl.opex_veto(date(2026, 11, 18))
    assert kl.days_to_opex(date(2026, 11, 17)) == 3 and not kl.opex_veto(date(2026, 11, 17))
    assert kl.days_to_opex(date(2026, 11, 23)) > 2                 # vade sonrası → sonraki ay


def _tab(seq: list[tuple[date, float]]) -> dict:
    return {d: {"p16": p, "o15": p, "twap": p, "n": 13, "t16": 0, "c": []} for d, p in seq}


def test_xp_exit_first_up_close():
    mon, tue, wed, thu = date(2026, 11, 2), date(2026, 11, 3), date(2026, 11, 4), date(2026, 11, 5)
    tab = _tab([(mon, 100.0), (tue, 99.0), (wed, 99.5), (thu, 101.0)])
    assert kl.xp_exit(tab, mon, tue, 15 * 60) is None              # 16:00'dan önce bugünkü fiyat kullanılmaz
    assert kl.xp_exit(tab, mon, tue, 16 * 60) is None              # 99 < 100 → tut, referans 99
    assert kl.xp_exit(tab, mon, wed, 16 * 60) == ("yukselis", wed)  # 99,5 > 99 → çık
    assert kl.xp_exit(tab, mon, thu, 9 * 60) == ("yukselis", wed)   # kaçırılmış çıkış → geç kapat


def test_xp_exit_max_hold_5():
    days = [date(2026, 11, 2) + timedelta(days=i) for i in range(10) if (date(2026, 11, 2) + timedelta(days=i)).weekday() < 5]
    tab = _tab([(d, 100.0 - i) for i, d in enumerate(days)])      # her gün düşüyor
    assert kl.xp_exit(tab, days[0], days[4], 16 * 60) is None
    assert kl.xp_exit(tab, days[0], days[5], 16 * 60) == ("sure", days[5])


def test_emergency_sl_and_catalog():
    assert kl.stop_price(20000.0, 1) == 17400.0
    r = kk.RULES["KORKU"]
    assert r["magic_offset"] == 16 and r["lot"] == 0.75 and r["live_key"] == "KORKU_LIVE"
    assert r["magic_offset"] not in {v["magic_offset"] for k, v in kk.RULES.items() if k != "KORKU"}
    assert any("GİRİŞ SONRASI DÜŞÜŞ" in ln for ln in kk.banner("KORKU", "test"))


if __name__ == "__main__":
    for nm, fn in list(globals().items()):
        if nm.startswith("test_"):
            fn()
    print("test_korku_live: hepsi geçti")
