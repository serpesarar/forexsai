"""aysonu_live birim + sadakat testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 test_aysonu_live.py (pytest de olur).
Sadakat: research/qs03_akis_takvim_20261111 verisi varsa (kutuda research/ sparse-checkout dışı → atlanır) modülün sinyali araştırma
motorunun (qs04.monthly + side) sinyaliyle ay ay karşılaştırılır; tatil takvimi gerçek işlem günleriyle 2025-01 → 2026-10 doğrulanır."""
import sys
import types
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import aysonu_live as ay
import kural_katalogu as kk

NY = ZoneInfo("America/New_York")
RES = Path(__file__).resolve().parent.parent / "research/qs03_akis_takvim_20261111"


def ep(d: date, hh: int, mm: int) -> float:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY).astimezone(timezone.utc).timestamp()


# ───────── takvim ─────────
def test_calendar_month_ends():
    mi = ay.month_info(date(2026, 11, 3))
    assert mi["D"] == date(2026, 11, 30) and mi["Dm3"] == date(2026, 11, 24) and mi["p0"] == date(2026, 10, 30)
    assert mi["Dp3"] == date(2026, 12, 3)
    mi = ay.month_info(date(2026, 12, 10))                      # 25 Ara tatil; 1 Oca 2027 tatil
    assert mi["D"] == date(2026, 12, 31) and mi["Dm3"] == date(2026, 12, 28) and mi["Dp3"] == date(2027, 1, 6)
    mi = ay.month_info(date(2027, 3, 1))                        # Kutsal Cuma 26 Mar 2027
    assert mi["D"] == date(2027, 3, 31) and mi["Dm3"] == date(2027, 3, 25)
    assert ay.month_info(date(2029, 1, 15)) is None             # takvim kapsamı dışı → işlem yok
    assert ay.e2_exit_day(date(2026, 11, 30)) == date(2026, 12, 3) and ay.e2_exit_day(date(2026, 11, 27)) is None


def test_flow_side_thresholds():
    assert ay.flow_side(0.025) == -1 and ay.flow_side(0.02) == -1
    assert ay.flow_side(-0.02) == 1 and ay.flow_side(0.0199) == 0 and ay.flow_side(None) == 0


def test_delta_and_missing_dates():
    eq = {date(2026, 10, 30): 100.0, date(2026, 11, 24): 105.0}
    bd = {date(2026, 10, 30): 50.0, date(2026, 11, 24): 50.5}
    assert abs(ay.delta(eq, bd, date(2026, 10, 30), date(2026, 11, 24)) - 0.04) < 1e-12
    assert ay.delta(eq, bd, date(2026, 10, 29), date(2026, 11, 24)) is None


def test_parity_lot():
    # NAS100 25000 × 1, US500 6800 × 1 → 1 lot NAS ≈ 3.68 US500 → adım 0.1 ile 3.7
    assert ay.parity_lot(1.0, 25000, 1, 6800, 1, 0.1, 0.1, 100) == 3.7
    assert ay.parity_lot(0.75, 25000, 1, 6800, 1, 0.01, 0.01, 2.0) == 2.0      # tavan
    assert ay.parity_lot(1.0, 25000, 1, 0, 1, 0.1, 0.1, 100) == 0.0


def test_exit_rules():
    D = date(2026, 11, 30)
    assert not ay.son_exit_due(D, D, 959) and ay.son_exit_due(D, D, 960) and ay.son_exit_due(D, date(2026, 12, 1), 300)
    assert not ay.e2_exit_due(D, date(2026, 12, 3), 989) and ay.e2_exit_due(D, date(2026, 12, 3), 990)
    assert not ay.e2_exit_due(D, date(2026, 12, 2), 1200) and ay.e2_exit_due(D, date(2026, 12, 4), 0)


# ───────── kural_katalogu: iki yönlü kapanış ─────────
def _fake_mt5(positions=None):
    sent = []
    m = types.SimpleNamespace(
        TRADE_ACTION_DEAL=1, ORDER_TYPE_BUY=0, ORDER_TYPE_SELL=1, ORDER_TIME_GTC=0, TRADE_RETCODE_DONE=10009,
        POSITION_TYPE_BUY=0, POSITION_TYPE_SELL=1,
        symbol_info_tick=lambda s: types.SimpleNamespace(bid=100.0 if s == "NAS100" else 50.0, ask=100.5 if s == "NAS100" else 50.2),
        symbol_info=lambda s: types.SimpleNamespace(digits=1, trade_contract_size=1.0, volume_step=0.1, volume_min=0.1, volume_max=100.0),
        positions_get=lambda symbol=None: [p for p in (positions or []) if symbol is None or p.symbol == symbol])
    return m, sent


def test_close_direction():
    mt5, sent = _fake_mt5()
    cfg = types.SimpleNamespace(MAGIC_NUMBER=1000, DEVIATION_POINTS=20)
    send = lambda req, sym: (sent.append(req), types.SimpleNamespace(retcode=10009, order=7))[1]
    log = types.SimpleNamespace(info=lambda *a: None, error=lambda *a: None)
    short = types.SimpleNamespace(symbol="NAS100", ticket=1, volume=1.0, type=1, price_open=101.0)
    long_ = types.SimpleNamespace(symbol="NAS100", ticket=2, volume=1.0, type=0, price_open=99.0)
    legacy = types.SimpleNamespace(symbol="NAS100", ticket=3, volume=1.0, price_open=99.0)       # tip alanı yok → BUY
    for p in (short, long_, legacy):
        kk.close(mt5, cfg, log, send, "AYSONU_SON", p, "test")
    assert [r["type"] for r in sent] == [0, 1, 1] and sent[0]["price"] == 100.5 and sent[1]["price"] == 100.0


# ───────── uçtan uca: sahte MT5 ile poll + manage_exits ─────────
def test_poll_enters_both_symbols_on_D_only():
    ay._last_poll = 0.0
    ay.STATE_FILE = Path("/tmp/aysonu_test_state.json")
    ay.STATE_FILE.unlink(missing_ok=True)
    mt5, _ = _fake_mt5()
    cfg = types.SimpleNamespace(MAGIC_NUMBER=1000, DEVIATION_POINTS=20, LIVE_TRADING=True)
    orders = []
    send = lambda req, sym: (orders.append((sym, req)), types.SimpleNamespace(retcode=10009, order=len(orders)))[1]
    log = types.SimpleNamespace(info=lambda *a: None, error=lambda *a: None, warning=lambda *a: None)
    resolve = {"NDX.INDX": "NAS100", "US500": "US500"}.get
    ay._data.update(t=1e18, eq={date(2026, 10, 30): 100.0, date(2026, 11, 24): 103.0},
                    bd={date(2026, 10, 30): 50.0, date(2026, 11, 24): 50.0})                     # Δ = +3% → SAT
    args = (mt5, cfg, log, resolve, None, lambda s: 0, send, lambda p, t: (p + t)[:28], lambda: True,
            lambda *a: None)
    ay.poll(*args, now=ep(date(2026, 11, 27), 9, 31))                                            # D değil → emir yok
    assert orders == []
    ay._last_poll = 0.0
    ay.poll(*args, now=ep(date(2026, 11, 30), 9, 31))
    assert [(s, r["type"]) for s, r in orders] == [("NAS100", 1), ("US500", 1)]
    assert orders[0][1]["volume"] == 1.0 and orders[1][1]["volume"] == 2.0                      # 100/50 → aynı nominal 2×
    assert orders[0][1]["sl"] > orders[0][1]["price"] and orders[0][1]["magic"] == 1012
    ay._last_poll = 0.0
    ay.poll(*args, now=ep(date(2026, 11, 30), 9, 35))                                            # aynı gün ikinci karar yok
    assert len(orders) == 2
    ay._data.update(t=0.0, eq=None, bd=None)


def test_e2_entry_and_exits():
    ay._last_poll = 0.0; ay._last_exit_poll = 0.0
    ay.STATE_FILE = Path("/tmp/aysonu_test_state2.json"); ay.STATE_FILE.unlink(missing_ok=True)
    D = date(2026, 11, 30)
    pos_list = []
    mt5, _ = _fake_mt5(pos_list)
    cfg = types.SimpleNamespace(MAGIC_NUMBER=1000, DEVIATION_POINTS=20, LIVE_TRADING=True, AYSONU_SON_LIVE=False)
    orders = []
    send = lambda req, sym: (orders.append((sym, req)), types.SimpleNamespace(retcode=10009, order=len(orders)))[1]
    log = types.SimpleNamespace(info=lambda *a: None, error=lambda *a: None, warning=lambda *a: None)
    resolve = {"NDX.INDX": "NAS100", "US500": "US500"}.get
    eq = {date(2026, 10, 30): 100.0, D: 101.0}; bd = {date(2026, 10, 30): 50.0, D: 49.0}            # Δ_D = +1% − (−2%) = +3%
    args = (mt5, cfg, log, resolve, None, lambda s: 0, send, lambda p, t: (p + t)[:28], lambda: True, lambda *a: None)
    ay._data.update(t=1e18, eq={k: v for k, v in eq.items() if k != D}, bd={k: v for k, v in bd.items() if k != D})
    ay.poll(*args, now=ep(D, 16, 25))                                     # bugünün kapanışı yok → bekle
    assert orders == []
    ay._data.update(t=1e18, eq=eq, bd=bd); ay._last_poll = 0.0
    ay.poll(*args, now=ep(D, 16, 26))
    assert [(s, r["type"], r["magic"]) for s, r in orders] == [("NAS100", 0, 1013), ("US500", 0, 1013)]
    assert orders[0][1]["volume"] == 0.75 and orders[0][1]["sl"] < orders[0][1]["price"]
    # çıkışlar: E2 pozisyonu D+3 (3 Ara) 16:30'da, son seans pozisyonu 16:00'da kapanır
    orders.clear()
    pos_list += [types.SimpleNamespace(symbol="NAS100", ticket=11, volume=0.75, type=0, price_open=100.5, magic=1013, time=ep(D, 16, 26)),
                 types.SimpleNamespace(symbol="NAS100", ticket=12, volume=1.0, type=1, price_open=100.0, magic=1012, time=ep(D, 9, 31))]
    ay.manage_exits(mt5, cfg, log, send, lambda s: 0, resolve, now=ep(D, 16, 1))
    assert [r["position"] for _, r in orders] == [12] and orders[0][1]["type"] == 0      # SELL pozisyonu BUY ile kapanır
    orders.clear(); ay._last_exit_poll = 0.0
    ay.manage_exits(mt5, cfg, log, send, lambda s: 0, resolve, now=ep(date(2026, 12, 3), 16, 29))
    assert [r["position"] for _, r in orders] == [12]                                     # E2 henüz değil (16:29)
    orders.clear(); ay._last_exit_poll = 0.0
    ay.manage_exits(mt5, cfg, log, send, lambda s: 0, resolve, now=ep(date(2026, 12, 3), 16, 31))
    assert sorted(r["position"] for _, r in orders) == [11, 12]
    ay._data.update(t=0.0, eq=None, bd=None)


# ───────── sadakat: araştırma motoruyla ay ay aynı sinyal ─────────
def test_research_fidelity():
    if not (RES / "data/SPY.parquet").exists():
        print("  (araştırma verisi yok — sadakat testi atlandı)")
        return
    sys.path.insert(0, str(RES)); sys.path.insert(0, str(RES.parent / "kazanan_turev_20261111"))
    import pandas as pd
    from r1_dengeleme import px
    from qs04 import monthly, side
    spy, tlt = px("SPY"), px("TLT")
    cal = spy.dropna().index.intersection(tlt.dropna().index)
    M = monthly(spy, tlt, {"_": spy}); M = M[M.d_s >= "2018-06-01"].reset_index(drop=True)
    eq = {t.date(): float(v) for t, v in spy.reindex(cal).items()}; bd = {t.date(): float(v) for t, v in tlt.reindex(cal).items()}
    s_res = side(M.dm.to_numpy()); mism = 0; cal_checked = 0
    last = pd.Series(range(len(cal)), index=cal).groupby(cal.to_period("M")).max()
    for k, r in M.iterrows():
        per = r.m; p0 = cal[last[per - 1]].date(); dm3 = r.d_s.date()
        if ay.flow_side(ay.delta(eq, bd, p0, dm3)) != s_res[k]:
            mism += 1
        if 2025 <= r.d_D.year <= 2026:                                        # tatil takvimi = gerçek işlem günleri mi?
            mi = ay.month_info(r.d_D.date())
            assert mi["D"] == r.d_D.date() and mi["Dm3"] == dm3 and mi["p0"] == p0, (per, mi)
            cal_checked += 1
    assert mism == 0 and cal_checked >= 20, (mism, cal_checked)
    print(f"  sadakat: {len(M)} ay, uyuşmazlık {mism}; takvim {cal_checked} ay doğrulandı")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for f in fns:
        f()
        print("ok", f.__name__)
