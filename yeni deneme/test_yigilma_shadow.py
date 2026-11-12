"""yigilma_shadow.py birim testleri (MT5 gerekmez).
Çalıştır:  cd 'yeni deneme' && python3 -m pytest test_yigilma_shadow.py"""
import ast
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

import yigilma_shadow as ys

LOG = logging.getLogger("test")
B = ys.MAGIC_BASE
MIN = 60_000


def deal(pid, t_min, entry, typ, price, magic, sym="GER40", vol=1.0, profit=0.0, order=None):
    return {"ticket": pid * 10 + entry, "order": order or pid, "time_msc": t_min * MIN, "type": typ, "entry": entry,
            "magic": magic, "position_id": pid, "volume": vol, "price": price, "profit": profit, "swap": 0.0,
            "commission": 0.0, "symbol": sym}


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr(ys, "EVENTS_JSONL", tmp_path / "ev.jsonl")
    monkeypatch.setattr(ys, "STATE_FILE", tmp_path / "st.json")
    return tmp_path


def recs(tmp):
    p = tmp / "ev.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


# 12 Kasım vakası: DECIDER 26886,8 açık (zararda) iken CHREV 26883,1 AL → Y2
NOV12 = [deal(1, 0, 0, 0, 26886.8, B + 20), deal(2, 39, 0, 0, 26883.1, B + 1, vol=10),
         deal(1, 68, 1, 1, 26852.0, B + 20, profit=-3.86), deal(2, 108, 1, 1, 26764.0, B + 1, vol=10, profit=-1319.77)]


def test_no_order_calls():
    src = Path(ys.__file__).read_text(encoding="utf-8")
    names = {n.attr for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Attribute)}
    assert not names & {"order_send", "order_check", "TRADE_ACTION_DEAL", "TRADE_ACTION_SLTP"}


def test_family_map():
    assert ys.family_of(B + 1) == "CHREV" and ys.family_of(B + 20) == "DECIDER" and ys.family_of(0) == "MANUEL"
    assert ys.family_of(123) == "MAGIC_123"


def test_build_positions_partial_close():
    pos = ys.build_positions([deal(5, 0, 0, 0, 100.0, B, vol=2), deal(5, 10, 1, 1, 101.0, B, vol=1, profit=5),
                              deal(5, 20, 1, 1, 102.0, B, vol=1, profit=10)])
    p = pos[5]
    assert p["t_close"] == 20 * MIN and p["X"] == 102.0 and p["net"] == 15.0
    pos2 = ys.build_positions([deal(6, 0, 0, 0, 100.0, B, vol=2), deal(6, 10, 1, 1, 101.0, B, vol=1)])
    assert pos2[6]["t_close"] is None


def test_crowd_nov12_case_is_y2():
    pos = ys.build_positions(NOV12)
    c = ys.crowd_at_open(pos[2], pos)
    assert c["y1"] and c["y2"] and c["n_under_other_fam"] == 1 and c["under"][0]["fam"] == "DECIDER"
    assert c["under"][0]["behind_pts"] == pytest.approx(3.7)
    assert not ys.crowd_at_open(pos[1], pos)["y1"]


def test_y1_without_y2_and_direction_symbol_filters():
    ds = [deal(1, 0, 0, 0, 100.0, B), deal(2, 5, 0, 0, 101.0, B + 1),       # önceki kârda → Y1, Y2 değil
          deal(3, 6, 0, 1, 99.0, B + 2),                                    # ters yön sayılmaz
          deal(4, 7, 0, 0, 90.0, B + 3, sym="NAS100")]                      # başka sembol sayılmaz
    pos = ys.build_positions(ds)
    c = ys.crowd_at_open(pos[2], pos)
    assert c["y1"] and not c["y2"]
    # SELL: önceki SELL daha düşükten açıldıysa ve fiyat yükseldiyse zararda
    pos = ys.build_positions([deal(7, 0, 0, 1, 100.0, B), deal(8, 3, 0, 1, 103.0, B + 1)])
    assert ys.crowd_at_open(pos[8], pos)["y2"]


def test_closed_before_open_not_counted():
    pos = ys.build_positions([deal(1, 0, 0, 0, 100.0, B), deal(1, 5, 1, 1, 98.0, B), deal(2, 9, 0, 0, 97.0, B + 1)])
    assert not ys.crowd_at_open(pos[2], pos)["y1"]


def test_step_tags_once_and_resolves(files):
    st = ys._load_state(now_ms=0)
    pos = ys.build_positions(NOV12)
    sl = {1: 26852.0, 2: 26764.0}
    assert ys.step(st, pos, lambda p: sl[p["pid"]], LOG, 200 * MIN)
    r = recs(files)
    entries = [x for x in r if x["kind"] == "entry"]
    results = {x["pid"]: x for x in r if x["kind"] == "result"}
    assert [e["pid"] for e in entries] == [1, 2] and entries[1]["y2"] and not entries[0]["y1"]
    assert results[2]["r"] == -1.0 and results[2]["y2"] and results[2]["net"] == -1319.77
    assert not ys.step(st, pos, lambda p: None, LOG, 200 * MIN)          # tekrar yazmaz
    assert len(recs(files)) == 4


def test_open_position_then_close_later(files):
    st = ys._load_state(now_ms=0)
    ys.step(st, ys.build_positions(NOV12[:2]), lambda p: None, LOG, 50 * MIN)
    assert [x["kind"] for x in recs(files)] == ["entry", "entry"]
    ys.step(st, ys.build_positions(NOV12), lambda p: None, LOG, 200 * MIN)
    res = [x for x in recs(files) if x["kind"] == "result"]
    assert len(res) == 2 and res[0]["r"] is None                         # SL bilinmiyor → R yok, $ var


def test_retro_flag_and_summary(files):
    st = ys._load_state(now_ms=100 * MIN)                                # modül 100. dk'da başladı
    ys.step(st, ys.build_positions(NOV12), lambda p: {1: 26852.0, 2: 26764.0}[p["pid"]], LOG, 200 * MIN)
    e = {x["pid"]: x for x in recs(files) if x["kind"] == "entry"}
    assert e[1]["retro"] and e[2]["retro"]
    s = ys.summarize([{"kind": "result", "y1": True, "y2": True, "r": -1.0, "net": -10},
                      {"kind": "result", "y1": False, "y2": False, "r": 0.5, "net": 5},
                      {"kind": "result", "y1": True, "y2": False, "r": None, "net": 1}])
    assert s["Y2"] == {"n": 1, "ort_r": -1.0, "n_r": 1, "net_usd": -10}
    assert s["yalniz"]["ort_r"] == 0.5 and s["Y1_degil_Y2"]["n_r"] == 0


def test_poll_with_fake_mt5(files):
    class O:  # opening order
        def __init__(self, sl): self.sl = sl
    mt5 = SimpleNamespace(
        history_deals_get=lambda a, b: [SimpleNamespace(**d) for d in NOV12],
        history_orders_get=lambda ticket: [O({1: 26852.0, 2: 26764.0}[ticket])],
        positions_get=lambda ticket: [])
    ys.poll(mt5, LOG, now=1e9, force=True)
    res = {x["pid"]: x for x in recs(files) if x["kind"] == "result"}
    assert res[2]["r"] == -1.0 and res[1]["r"] == -1.0


def test_research_parity():
    """Araştırma tanımıyla parite: 400 g tabanında Y2 = 44 işlem (yigilma.json)."""
    p = Path(__file__).resolve().parent.parent / "research/dax_gun_otopsi_20261112/results/yigilma.json"
    if not p.exists():
        pytest.skip("araştırma çıktısı yok (kutuda research/ sparse-checkout dışı)")
    assert json.loads(p.read_text(encoding="utf-8"))["Y2_tumu"]["n_flag"] == 44
