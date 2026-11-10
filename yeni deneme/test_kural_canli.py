"""C3b / ORB×VIX / FR-15 çekiç canlı modüllerinin birim testleri (MT5 gerekmez).
Çalıştır: cd 'yeni deneme' && python3 test_kural_canli.py   (pytest de olur)
Çekiç dedektörü araştırma motoruyla kontrol edildi: NDX 715/715 çekiç, DAX 1925/1925 (teyitli: araştırma ⊂ canlı)."""
import types
from datetime import date

import c3b_live as c3
import cekic_live as ck
import kural_katalogu as kk
import orb_vix_live as ov


def bar(t, o, h, l, c):
    return {"t": t, "open": o, "high": h, "low": l, "close": c}


def flat_bars(n=20, start=1000.0, step=3600):
    """Her biri aralığı 10 olan sakin barlar (ATR14 = 10)."""
    return [bar(i * step, start, start + 5, start - 5, start) for i in range(n)]


# ───────── çekiç ─────────
def test_atr_needs_history():
    b = flat_bars(20)
    assert ck.atr14(b, 5) is None
    assert abs(ck.atr14(b, 19) - 10.0) < 1e-9


def test_hammer_and_confirmation():
    b = flat_bars(20)
    b.append(bar(20 * 3600, 1000, 1002, 960, 1001))        # alt fitil 39/42 ≥ %70, 39 ≥ 0,2×ATR, üst fitil ~1
    assert ck.is_hammer(b, 20)
    conf = bar(21 * 3600, 1001, 1010, 965, 1004)            # dibi kırmadı (965 > 960), kapanış 1004 > tepe 1002
    assert ck.confirmed(b[20], conf)
    b.append(conf)
    sig = ck.find_signal(b)
    assert sig and sig["hammer"]["low"] == 960


def test_confirmation_rejects_broken_low_or_weak_close():
    h = bar(0, 1000, 1002, 960, 1001)
    assert not ck.confirmed(h, bar(3600, 1001, 1010, 960, 1004))      # dip eşit/kırıldı
    assert not ck.confirmed(h, bar(3600, 1001, 1010, 970, 1002))      # kapanış tepenin üstünde değil
    assert not ck.confirmed(h, bar(3 * 3600, 1001, 1010, 970, 1004))  # ardışık değil


def test_hammer_rejects_small_wick_or_dominance():
    b = flat_bars(20)
    b.append(bar(20 * 3600, 1000, 1030, 990, 1020))        # alt fitil 10/40 = %25
    assert not ck.is_hammer(b, 20)
    b2 = flat_bars(20)
    b2.append(bar(20 * 3600, 1000, 1004, 999.5, 1000.2))   # fitil oranı yüksek ama < 0,2×ATR
    assert not ck.is_hammer(b2, 20)


def test_order_geometry_and_min_risk():
    h = bar(0, 1000, 1002, 960, 1001)
    pl, why = ck.build_order(h, ask=1005.0, bid=1004.0)
    assert why is None and pl["sl"] == 960 and abs(pl["tp"] - (1005 + 5 * 45)) < 1e-9
    pl, why = ck.build_order(h, ask=962.0, bid=958.0)       # risk 2 < 2×spread 8
    assert pl is None and why


def test_friday_close_window():
    # 2026-11-06 Cuma, EST: 16:45 NY = 21:45 UTC
    from datetime import datetime, timezone
    ts = lambda h, m: datetime(2026, 11, 6, h, m, tzinfo=timezone.utc).timestamp()
    assert not ck.friday_close_due(ts(21, 30))
    assert ck.friday_close_due(ts(21, 50))
    assert not ck.friday_close_due(datetime(2026, 11, 5, 21, 50, tzinfo=timezone.utc).timestamp())


# ───────── ORB × VIX ─────────
def test_orb_plan_rules():
    trig = {"stop": 9950.0}
    pl, why = ov.plan(trig, 10000.0, 20.0)
    assert why is None and pl["sl"] == 9950.0 and abs(pl["tp"] - 10100.0) < 1e-9   # TP = giriş + 2×risk
    assert ov.plan(trig, 10000.0, 17.0)[0] is None            # alt VIX kolu
    assert ov.plan(trig, 10000.0, None)[0] is None            # VIX geçmişi yok
    assert ov.plan(trig, 9950.5, 20.0)[0] is None             # risk çok dar (< %0,05)
    assert ov.plan(trig, 10300.0, 20.0)[0] is None            # risk > %2 (ek güvenlik)


# ───────── C3b ─────────
def _series(vals):
    return [{"d": date(2026, 1, 1 + k), "S": v, "E": v, "t": k} for k, v in enumerate(vals)]


def test_c3b_exit_rules():
    s = _series([100, 99, 98, 97, 96, 95, 94])            # sürekli düşüş
    assert c3.should_exit(s, 2, 3) is None
    assert c3.should_exit(s, 0, 5) == "sure"              # 5 gün doldu
    s2 = _series([100, 99, 98, 99.5, 97])
    assert c3.should_exit(s2, 1, 3) == "yukselis"         # 3. gün S yükseldi
    assert c3.should_exit(s2, 1, 4) == "yukselis"         # kaçırılan yükseliş de sayılır


# ───────── katalog ─────────
def test_lots_distinct_and_overridable():
    cfg = types.SimpleNamespace(MAGIC_NUMBER=1000, LIVE_TRADING=True)
    lots = {k: kk.lot_of(cfg, k) for k in kk.RULES}
    assert lots == {"C3B": 2.0, "CAPREV": 1.0, "ORBVIX": 0.75, "CEKIC": 0.5, "KSG": 0.5}
    cfg.C3B_LIVE_LOT = 3.0
    assert kk.lot_of(cfg, "C3B") == 3.0
    assert len({kk.magic(cfg, k) for k in kk.RULES}) == 5 and kk.magic(cfg, "CAPREV") == 1007


def test_enabled_needs_both_flags():
    cfg = types.SimpleNamespace(LIVE_TRADING=True)
    assert kk.is_enabled(cfg, "C3B")
    cfg.C3B_LIVE = False
    assert not kk.is_enabled(cfg, "C3B")
    assert not kk.is_enabled(types.SimpleNamespace(LIVE_TRADING=False), "ORBVIX")


def test_banner_names_rule_and_success_rate():
    txt = "\n".join(kk.banner("C3B", "NAS100 BUY 2.0 lot"))
    assert "C3b" in txt and "%78,1" in txt and "n 155" in txt and "NAS100 BUY 2.0 lot" in txt


def test_concentration_cap():
    cfg = types.SimpleNamespace(MAGIC_NUMBER=1000)
    pos = lambda m, v: types.SimpleNamespace(magic=m, volume=v)
    mt5 = types.SimpleNamespace(positions_get=lambda symbol=None: [pos(1008, 2.0), pos(1007, 1.0), pos(999, 5.0)])
    ok, open_lot, cap = kk.concentration_ok(mt5, cfg, "NAS100", 0.75)
    assert ok and open_lot == 3.0 and cap == 4.5               # 999 numaralı başka magic sayılmaz
    ok, _, _ = kk.concentration_ok(mt5, cfg, "NAS100", 2.0)
    assert not ok


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for f in fns:
        f()
        print("ok", f.__name__)
    print(len(fns), "test geçti")
