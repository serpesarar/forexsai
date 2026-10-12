"""xau_shadow.py birim testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 test_xau_shadow.py
Araştırma ile tam sadakat: research/pinbar_20261010/xau_shadow_fidelity.py"""
import xau_shadow as xs

H = 3600


def mk(n=40, start=1_700_000_000, base=2000.0, step=1.0):
    return [{"t": start + k * H, "open": base + k * step, "high": base + k * step + 2.0,
             "low": base + k * step - 2.0, "close": base + k * step + 1.0} for k in range(n)]


def test_signal_new_high_and_not():
    bars = mk()
    assert xs.is_signal(bars, 30)                              # yükselen seri → her bar yeni tepe
    flat = [{**b, "high": 2100.0} for b in bars]
    flat[30]["high"] = 2099.0
    assert not xs.is_signal(flat, 30)                          # önceki 20'nin en yükseğinin altında
    flat[30]["high"] = 2100.0
    assert xs.is_signal(flat, 30)                              # eşit → sinyal (≥)


def test_signal_blocked_by_gap():
    bars = mk()
    for b in bars[15:]:
        b["t"] += 5 * 86400                                    # pencerede 5 günlük boşluk
    assert not xs.is_signal(bars, 30)


def test_atr_excludes_signal_bar():
    bars = mk()
    a1 = xs.atr_before(bars, 30)
    bars[30]["high"] += 500                                    # sinyal barının kendisi ATR'ye girmemeli
    assert xs.atr_before(bars, 30) == a1
    assert a1 > 0 and xs.atr_before(bars, 10) is None


def _ev(bars, i, entry_ask=None):
    atr = xs.atr_before(bars, i)
    ask = entry_ask if entry_ask is not None else bars[i]["close"] + 0.3
    sd = xs.STOP_K * atr
    return {"sig_t": bars[i]["t"], "entry_ask": ask, "stop": ask - sd, "stop_dist": sd,
            "paper_close": bars[i]["close"], "spread_assumed": 0.25}


def test_resolve_time_exit_and_wait():
    bars = mk(60)
    ev = _ev(bars, 30)
    assert xs.resolve(ev, bars[:49]) is None                   # giriş barı + 19 bar yok (30+1..49 = 19)
    r = xs.resolve(ev, bars[:51])                              # 31..50 = 20 bar
    assert r["status"] == "done" and r["how"] == "time"
    assert abs(r["R"] - (bars[50]["close"] - ev["entry_ask"]) / ev["stop_dist"]) < 1e-3


def test_resolve_stop_gap_and_inbar():
    bars = mk(60)
    ev = _ev(bars, 30)
    b = [dict(x) for x in bars]
    b[34]["low"] = ev["stop"] - 1.0                            # bar-içi stop
    r = xs.resolve(ev, b[:51])
    assert r["how"] == "stop" and abs(r["R"] - (ev["stop"] - ev["entry_ask"]) / ev["stop_dist"]) < 1e-3
    b = [dict(x) for x in bars]
    b[34]["open"], b[34]["low"] = ev["stop"] - 3.0, ev["stop"] - 4.0   # boşluk → açılıştan dolum
    r = xs.resolve(ev, b[:51])
    assert abs(r["exit_px"] - (ev["stop"] - 3.0)) < 1e-9 and r["R"] < -1.0
    b = [dict(x) for x in bars]
    b[31]["low"] = ev["stop"] - 1.0                            # ilk (giriş) barda stop → stop fiyatından
    assert abs(xs.resolve(ev, b[:51])["exit_px"] - ev["stop"]) < 1e-9


def test_resolve_early_stop_frees_event():
    bars = mk(60)
    ev = _ev(bars, 30)
    b = [dict(x) for x in bars]
    b[33]["low"] = ev["stop"] - 1.0                            # 3. barda stop; 20 bar dolmadan sonuçlanmalı
    r = xs.resolve(ev, b[:36])
    assert r is not None and r["how"] == "stop" and r["bars_held"] == 3
    assert xs.resolve(ev, bars[:36]) is None                   # stop yok + 20 bar dolmadı → bekle


def test_resolve_void_on_gap():
    bars = mk(60)
    for b in bars[40:]:
        b["t"] += 6 * 86400
    r = xs.resolve(_ev(bars, 30), bars[:55])
    assert r["status"] == "void"


if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1
    print(f"{n} test geçti")
