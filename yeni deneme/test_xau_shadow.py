"""xau_shadow.py birim testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 test_xau_shadow.py
Mekanik tanımla (research/decider_xau_tpsl_20261015/mekanik) tam sadakat: research/xau_best_days_20261015/golge_parite/parity.py"""
from datetime import datetime, timezone

import xau_shadow as xs

H = 3600
T0 = int(datetime(2026, 10, 5, 0, tzinfo=timezone.utc).timestamp())      # Pazartesi 00:00 UTC


def mk(n=60, start=T0, base=2000.0, step=1.0):
    return [{"t": start + k * H, "open": base + k * step, "high": base + k * step + 2.0,
             "low": base + k * step - 2.0, "close": base + k * step + 1.0} for k in range(n)]


def flat(n=60, start=T0):
    return [{"t": start + k * H, "open": 2000.0, "high": 2002.0, "low": 1998.0, "close": 2000.0} for k in range(n)]


def test_signal_new_high_and_not():
    bars = flat()
    bars[30]["high"] = 2001.9
    assert not xs.is_signal(bars, 30)                          # önceki 20'nin en yükseğinin altında
    bars[30]["high"] = 2002.0
    assert xs.is_signal(bars, 30)                              # eşit → sinyal (≥)
    assert not xs.is_signal(bars, 19)                          # 20 bar geçmiş yok


def test_signal_not_blocked_by_gap():                          # mekanik rolling(20) boşluklardan kesilmez
    bars = mk()
    for b in bars[25:]:
        b["t"] += 2 * 86400
    assert xs.is_signal(bars, 30)


def test_atr_includes_signal_bar_and_seg_reset():
    bars = flat()
    a1 = xs.atr_at(bars, 30)
    bars[30]["high"] += 14.0                                   # sinyal barı ATR'ye GİRER
    assert abs(xs.atr_at(bars, 30) - (a1 + 1.0)) < 1e-9
    assert xs.atr_at(bars, 13) is None and xs.atr_at(bars, 14) is not None
    b = flat()
    b[25]["open"] = b[25]["high"] = b[25]["low"] = b[25]["close"] = 2100.0
    for x in b[25:]:
        x["t"] += 4 * H                                        # 25 segment başı → TR = h−l (önceki kapanış yok sayılır)
    assert xs.true_range(b, 25) == 0.0
    assert xs.true_range(flat(), 25) == 4.0


def _open(bars, i, cfg=None, ask=None):
    st = {"open": []}
    live = None if ask is None else {"now": bars[i]["t"] + H + 5, "ask": ask, "bid": ask - 0.2}
    recs = xs.step(st, bars, i, cfg, live)
    return st, recs


def test_time_exit_and_research_entry():
    bars = mk(60)
    st, recs = _open(bars, 30, ask=bars[30]["close"] + 0.3)
    ev = recs[-1]
    assert ev["kind"] == "event" and ev["in_base"] and ev["in_s2"]
    assert xs.advance(dict(st["open"][0]), bars[:50]) == "pending"   # giriş 31 + 19 bar = 49 → 20. bar yok
    e = dict(st["open"][0])
    assert xs.advance(e, bars[:51]) == "done"                  # 31..50 = 20 bar
    r = xs._result(e)
    entry_r = bars[31]["open"] + xs.SPREAD_RESEARCH
    assert r["how_research"] == "time" and r["exit_bar_t_research"] == bars[50]["t"]
    assert abs(r["R_research"] - (bars[50]["close"] - entry_r) / ev["stop_dist"]) < 1e-3
    assert abs(r["R"] - (bars[50]["close"] - ev["entry_ask"]) / ev["stop_dist"]) < 1e-3


def test_stop_gap_and_inbar():
    bars = mk(60)
    st, _ = _open(bars, 30)
    ev = st["open"][0]
    entry_r = bars[31]["open"] + xs.SPREAD_RESEARCH
    stop = entry_r - ev["stop_dist"]
    b = [dict(x) for x in bars]
    b[34]["low"] = stop - 1.0
    e = dict(ev); xs.advance(e, b[:40])
    assert e["rx"]["how"] == "stop" and abs(e["rx"]["exit_px"] - stop) < 1e-9 and e["rx"]["bars_held"] == 4
    b[34]["open"], b[34]["low"] = stop - 3.0, stop - 4.0       # boşluk → açılıştan dolum
    e = dict(ev); xs.advance(e, b[:40])
    assert abs(e["rx"]["exit_px"] - (stop - 3.0)) < 1e-9
    b = [dict(x) for x in bars]
    b[31]["low"] = stop - 50.0                                 # giriş barında stop → stop fiyatından
    e = dict(ev); xs.advance(e, b[:40])
    assert abs(e["rx"]["exit_px"] - stop) < 1e-9


def test_segment_end_exit_and_void():
    bars = mk(60)
    for x in bars[36:]:
        x["t"] += 2 * 86400                                    # 35 → 36 arası hafta sonu
    st, _ = _open(bars, 30)
    e = dict(st["open"][0])
    assert xs.advance(e, bars[:36]) == "pending"               # boşluk henüz görülmedi
    assert xs.advance(e, bars[:37]) == "done"
    assert e["rx"]["how"] == "seg" and e["rx"]["exit_bar_t"] == bars[35]["t"]
    st, _ = _open(bars, 35)                                    # Cuma son barı sinyali → giriş barı yok
    assert xs.advance(dict(st["open"][0]), bars[:37]) == "void"


def test_signal_on_exit_bar_opens():
    """mech.one_position: çıkış barında gelen sinyalin girişi (sonraki bar) > çıkış barı → açılır."""
    bars = mk(80)
    # 25'te açıldı (giriş 26), 20. bar = 45 → 45'te çıkış + aynı barda yeni olay
    evs = []
    st = {"open": []}
    for k in range(25, 51):
        evs += [r for r in xs.step(st, bars, k) if r["kind"] in ("event", "result")]
    kinds = [(r["kind"], r["sig_t"]) for r in evs]
    assert ("result", bars[25]["t"]) in kinds and ("event", bars[45]["t"]) in kinds
    assert kinds.index(("result", bars[25]["t"])) < kinds.index(("event", bars[45]["t"]))
    assert all(r["kind"] != "event" or r["sig_t"] in (bars[25]["t"], bars[45]["t"]) for r in evs)


def test_s2_skip_does_not_lock():
    """Önceki gün >%1 → filtreli varyant atlar ve KİLİTLENMEZ; ertesi gün filtreli varyant açar, filtresiz dolu."""
    lv = [2000.0] * 24 + [2030.0] * 72                         # A=2000, B=2030 (+%1,5), C=D=2030
    bars = [{"t": T0 + k * H, "open": L, "high": L + 2 - 0.01 * k, "low": L - 2, "close": L} for k, L in enumerate(lv)]
    bars[62]["high"] = 2040.0                                  # C 14:00 sinyali: önceki gün B/A = +%1,5
    bars[74]["high"] = 2045.0                                  # D 02:00 sinyali: önceki gün C/B = 0
    assert abs(xs.prevday_ret(bars, 62) - 0.015) < 1e-12 and xs.prevday_ret(bars, 74) == 0.0
    st = {"open": []}
    recs = []
    for k in range(40, 76):
        recs += xs.step(st, bars, k)
    e1 = next(r for r in recs if r["kind"] == "event" and r["sig_t"] == bars[62]["t"])
    assert e1["in_base"] and not e1["in_s2"] and e1["skip_s2"] and e1["s2_decision"] == "skip_s2"
    e2 = next(r for r in recs if r["kind"] == "event" and r["sig_t"] == bars[74]["t"])
    assert e2["base_decision"] == "overlap" and not e2["in_base"] and e2["in_s2"]
    st2 = {"open": []}
    for k in range(40, 76):
        xs.step(st2, bars, k, {"s2_thr": 0.02})                # eşik %2 → ilk olay her iki varyantta → ikinci overlap
    assert len(st2["open"]) == 1


def test_prevday_sunday_is_separate_day():
    thu = int(datetime(2026, 10, 1, 20, tzinfo=timezone.utc).timestamp())
    fri = int(datetime(2026, 10, 2, 19, tzinfo=timezone.utc).timestamp())
    sun = int(datetime(2026, 10, 4, 21, tzinfo=timezone.utc).timestamp())   # Pazar 21:00 UTC açılış
    px = [(thu, 99.0), (fri, 100.0), (fri + H, 101.0), (sun, 102.0), (sun + H, 103.0), (sun + 2 * H, 104.0)]
    bars = [{"t": t, "open": 1, "high": 1, "low": 1, "close": c} for t, c in px]
    assert abs(xs.prevday_ret(bars, 4) - (101.0 / 99.0 - 1)) < 1e-12    # Pazar 22:00 sinyali → giriş Pazar: Cuma/Per
    assert abs(xs.prevday_ret(bars, 5) - (104.0 / 101.0 - 1)) < 1e-12    # Pazar 23:00 → giriş Pzt: Pazar/Cuma


def test_dens24():
    bars = mk(80)                                              # her bar yeni tepe → her olay barı
    assert xs.dens24(bars, 43) is None and xs.dens24(bars, 44) == 24
    for x in bars[60:]:
        x["t"] += 4 * H                                        # 59 segment sonu → olay sayılmaz
    assert xs.dens24(bars, 70) == 23


def test_fomc_window():
    t = datetime(2026, 10, 28, 0, tzinfo=timezone.utc).timestamp()
    assert xs.fomc_in_window(t) is True                        # 18:00 UTC ∈ [00:00, 20:00)
    assert xs.fomc_in_window(t - 3 * H) is False               # 21:00 önceki gün + 20s = 17:00 → dışarıda
    assert xs.fomc_in_window(datetime(2026, 12, 9, 0, tzinfo=timezone.utc).timestamp()) is True
    assert xs.fomc_in_window(datetime(2027, 1, 5, tzinfo=timezone.utc).timestamp()) is None


def test_d1_features():
    d1 = [{"high": 100.0 + k, "low": 90.0 + k, "close": 95.0 + k} for k in range(250)]
    d1[-1] = {"high": d1[-2]["high"] - 1, "low": d1[-2]["low"] + 1, "close": 300.0}   # inside + NR4
    f = xs.d1_features(d1, high_i=400.0, close_i=340.0)
    assert f["d1_inside"] and f["d1_nr4"] and f["d1_nr4_inside"] and f["d1_brk20"] and f["at_52wh"]
    assert f["d1_hh250"] == 348.0 and abs(f["dist_52wh_pct"] - (340.0 / 348.0 - 1)) < 1e-4
    assert xs.d1_features(d1[:3], 1, 1)["d1_hh20"] is None


def test_live_leg_late_and_absent():
    bars = mk(60)
    st = {"open": []}
    ev = xs.step(st, bars, 30, live={"now": bars[30]["t"] + H + 999, "ask": 1.0, "bid": 0.9})[-1]
    assert ev["live_reason"] == "geç tespit" and ev["entry_ask"] is None and ev["in_base"]
    e = dict(st["open"][0])
    assert xs.advance(e, bars[:51]) == "done" and "R" not in xs._result(e)   # yalnız araştırma bacağı


def test_poll_smoke_fake_mt5():
    """poll(): v1 durum göçü, ısınma, D1/VIX bağlamı, sonraki barda canlı bacak — sahte MT5, geçici dosyalar."""
    import json, logging, tempfile, types
    from pathlib import Path
    tmp = Path(tempfile.mkdtemp())
    xs.EVENTS_JSONL, xs.STATE_FILE = tmp / "e.jsonl", tmp / "s.json"
    xs.STATE_FILE.write_text(json.dumps({"last_bar": 1, "open": [{"sig_t": 1}]}))         # eski (v1) durum
    OFF = 3 * H
    h1 = [{"time": b["t"] + OFF, "open": b["open"], "high": b["high"], "low": b["low"], "close": b["close"]}
          for b in mk(230)]
    d1 = [{"time": T0 - (300 - k) * 86400 + OFF, "open": 1.0, "high": 1500.0 + k, "low": 1.0, "close": 2.0}
          for k in range(300)]
    feed = {"n": 201}

    class MT5:
        TIMEFRAME_H1, TIMEFRAME_D1 = 1, 2

        def copy_rates_from_pos(self, sym, tf, pos, cnt):
            if tf == self.TIMEFRAME_D1:
                return d1[-cnt:]
            return h1[:feed["n"]][-cnt:]

        def symbol_info_tick(self, sym):
            return types.SimpleNamespace(ask=2300.0, bid=2299.8)

    cfg = types.SimpleNamespace(XAU_SHADOW_S2_THR=0.5)
    now = h1[200]["time"] - OFF + H + 5
    xs.poll(MT5(), logging.getLogger("t"), lambda s: "XAUUSD", lambda s: OFF, now=now, force=True,
            get_vix=lambda: 21.5, config=cfg)
    recs = [json.loads(x) for x in xs.EVENTS_JSONL.read_text().splitlines()]
    assert recs[0]["status"] == "void" and "v2" in recs[0]["reason"]
    evs = [r for r in recs if r["kind"] == "event"]
    assert evs and all(r.get("warmup") for r in evs)
    assert evs[-1]["d1_hh20"] is not None and "vix_prev" in evs[-1]
    st = json.loads(xs.STATE_FILE.read_text())
    assert st["ver"] == 2 and st["last_bar"] == h1[200]["time"] - OFF
    feed["n"] = 222                                            # 21 yeni bar: 201 olayı (yakalama, canlı yok) 221'de
    xs.poll(MT5(), logging.getLogger("t"), lambda s: "XAUUSD", lambda s: OFF, now=h1[221]["time"] - OFF + H + 5,
            force=True, get_vix=lambda: 22.0, config=cfg)
    recs = [json.loads(x) for x in xs.EVENTS_JSONL.read_text().splitlines()]
    ev = [r for r in recs if r["kind"] == "event"]
    assert ev[-2]["sig_t"] == h1[201]["time"] - OFF and ev[-2]["entry_ask"] is None      # yakalanan bar: canlı yok
    assert any(r["kind"] == "result" and r["sig_t"] == ev[-2]["sig_t"] for r in recs)   # 221'de çıktı ...
    assert ev[-1]["sig_t"] == h1[221]["time"] - OFF and ev[-1]["entry_ask"] == 2300.0   # ... ve aynı barda açıldı
    assert not ev[-1].get("warmup") and ev[-1]["d1_nr4"] is not None


if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1
    print(f"{n} test geçti")
