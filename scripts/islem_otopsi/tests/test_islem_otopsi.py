"""islem_otopsi birim testleri — sentetik veri, ağ yok.

Çalıştır: python3 -m pytest scripts/islem_otopsi/tests -q
En kritik test ``test_pre_features_ignore_future``: karar-anı özellikleri gelecekteki
barlar değiştirildiğinde DEĞİŞMEMELİ (defter E1/E15/E16 sızıntı sınıfı).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.islem_otopsi import align, compare, stats
from scripts.islem_otopsi import settings as S
from scripts.islem_otopsi.build import trade_features
from scripts.islem_otopsi.features import make_ctx, pre_divergence, pre_momentum, pre_trend, pre_volume, vol_dir
from scripts.islem_otopsi.indicators import SymbolBars, seasonal_volume
from scripts.islem_otopsi.narrative import tr_num
from scripts.islem_otopsi.path import classify_outcome, sl_verdict
from scripts.islem_otopsi.placebo import simulate
from scripts.islem_otopsi.report import md_table

SYM = "NDX.INDX"
START = pd.Timestamp("2026-09-01T00:00:00Z")
DAYS = 16


def _bars(seed: int = 1, n_days: int = DAYS) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = n_days * 1440
    idx = pd.date_range(START, periods=n, freq="1min", tz="UTC")
    close = 30000 + np.cumsum(rng.normal(0, 3, n))
    open_ = np.r_[close[0], close[:-1]]
    spread = np.abs(rng.normal(0, 2, n)) + 0.5
    vol = rng.integers(80, 300, n).astype(float)
    return pd.DataFrame({"open": open_, "high": np.maximum(open_, close) + spread,
                         "low": np.minimum(open_, close) - spread, "close": close, "volume": vol}, index=idx)


def _row(sb: SymbolBars, entry_t: pd.Timestamp, exit_t: pd.Timestamp, direction: str = "BUY",
         risk: float = 40.0, reward: float = 30.0) -> pd.Series:
    i = sb.pos_at(entry_t)
    e = float(sb.m1["open"].iat[i])
    s = 1 if direction == "BUY" else -1
    return pd.Series({"direction": direction, "open_price": e, "sl0": e - s * risk, "tp0": e + s * reward,
                      "entry_utc": entry_t, "exit_utc": exit_t,
                      "close_price": float(sb.m1["close"].iat[sb.pos_at(exit_t)]),
                      "reason": 4, "net": -1.0, "pid": 1})


@pytest.fixture(scope="module")
def sb() -> SymbolBars:
    return SymbolBars(SYM, _bars())


def _pre(sb_: SymbolBars, row: pd.Series) -> dict:
    c = make_ctx(row, sb_)
    tr = pre_trend(c)
    out = {**tr, **pre_momentum(c, tr["_atr1"], tr["_atr5"]), **pre_volume(c), **pre_divergence(c)}
    return {k: v for k, v in out.items() if not k.startswith("_")}


def test_pre_features_ignore_future(sb):
    """Girişten SONRAKİ barları bozmak karar-anı özelliklerini değiştirmemeli."""
    entry = START + pd.Timedelta(days=12, hours=14, minutes=7, seconds=31)
    row = _row(sb, entry, entry + pd.Timedelta(minutes=50))
    before = _pre(sb, row)
    m1 = _bars()
    m1.loc[m1.index >= entry.floor("min"), ["open", "high", "low", "close"]] *= 1.07
    m1.loc[m1.index >= entry.floor("min"), "volume"] *= 9
    after = _pre(SymbolBars(SYM, m1), row)
    for k, v in before.items():
        assert after[k] == pytest.approx(v, nan_ok=True, rel=1e-9), k


def test_last_closed_respects_bar_end(sb):
    t_open = START + pd.Timedelta(days=13, hours=10, minutes=30)
    j_before = sb.last_closed(5, t_open + pd.Timedelta(minutes=4, seconds=59))
    j_after = sb.last_closed(5, t_open + pd.Timedelta(minutes=5))
    assert sb.tf[5].index[j_before] == t_open - pd.Timedelta(minutes=5)
    assert sb.tf[5].index[j_after] == t_open
    assert sb.m1.index[sb.last_closed(1, t_open + pd.Timedelta(seconds=30))] == t_open - pd.Timedelta(minutes=1)


def test_seasonal_volume_uses_only_prior_days():
    m1 = _bars(n_days=12)
    base = seasonal_volume(m1)
    last_day = m1.index.normalize() == m1.index.normalize()[-1]
    m2 = m1.copy()
    m2.loc[last_day, "volume"] *= 10
    changed = seasonal_volume(m2)
    ratio = (changed[last_day] / base[last_day]).dropna()
    assert np.allclose(ratio, 10.0)          # taban aynı kaldı → yalnız pay 10× arttı


def test_vol_dir_ignores_bar_count():
    v = np.full(30, 100.0)
    body = np.r_[np.full(25, -1.0), np.full(5, 1.0)]   # 25 aleyhte, 5 lehte bar, aynı hacim
    assert vol_dir(v, body) == pytest.approx(0.0)
    v2 = np.r_[np.full(25, 200.0), np.full(5, 100.0)]
    assert vol_dir(v2, body) < -0.9


@pytest.mark.parametrize("reason,r,net,expected", [
    (5, 0.7, 10, "TP"), (4, -1.0, -10, "SL"), (4, 0.05, 0.0, "BE"),
    (4, 0.6, 5, "IZ_SL"), (4, -0.5, -5, "KISMI_SL"), (3, 0.2, 3, "DIGER_+"), (4, np.nan, -5, "SL"),
])
def test_classify_outcome(reason, r, net, expected):
    assert classify_outcome(reason, r, net) == expected


def test_auc_and_permutation():
    a, b = np.arange(10, 20, dtype=float), np.arange(0, 10, dtype=float)
    assert stats.auc(a, b) == 1.0
    assert stats.auc(a, a.copy()) == 0.5
    obs, p = stats.auc_perm(a, b)
    assert obs == 1.0 and p < 0.01
    _, p_null = stats.auc_perm(np.random.default_rng(0).normal(size=40), np.random.default_rng(1).normal(size=40))
    assert p_null > 0.05


def test_bh_q_monotone_and_nan_safe():
    q = stats.bh_q(np.array([0.01, 0.04, np.nan, 0.03, 0.5]))
    assert np.isnan(q[2]) and q[0] <= q[3] <= q[1] <= q[4] <= 1.0


def test_simulate_same_bar_is_conservative_sl(sb):
    j = sb.pos_at(START + pd.Timedelta(days=12, hours=9))
    hi, lo = sb.a["high"][j], sb.a["low"][j]
    entry = (hi + lo) / 2
    risk, reward = entry - lo + 0.01 - 0.02, hi - entry - 0.01      # her iki bariyer aynı barda
    R, j_exit, _ = simulate(sb, 1, entry, j, risk, reward, 0.0)
    assert R == -1.0 and j_exit == j


def test_align_detects_broker_offset(sb):
    bars = {SYM: sb.m1[["open", "high", "low", "close", "volume"]]}
    rows = []
    for k in range(6):
        t0 = START + pd.Timedelta(days=11 + k, hours=9, minutes=13)
        if t0 >= sb.m1.index[-1]:
            break
        t1 = t0 + pd.Timedelta(minutes=37)
        rows.append({"pid": k, "symbol": SYM, "open_raw": t0 + pd.Timedelta(hours=3), "close_raw": t1 + pd.Timedelta(hours=3),
                     "open_price": float(sb.m1["close"].asof(t0)), "close_price": float(sb.m1["close"].asof(t1))})
    res = align.align_trades(pd.DataFrame(rows), bars)
    assert res.status == "ALIGNED"
    assert set(res.offset_counts) == {-3}


def test_sl_verdict_rules():
    assert sl_verdict("SL", -1.0, {"post240_max_adv_r": -1.2, "post240_hit_tp0": 1.0}) == "YON_DOGRU"
    assert sl_verdict("SL", -1.0, {"post240_max_adv_r": -2.5, "post240_hit_tp0": 0.0,
                                   "post240_back_entry": 0.0}) == "YON_YANLIS"
    assert sl_verdict("SL", -1.0, {"post240_max_adv_r": -1.4, "post240_hit_tp0": 0.0}) == "KARARSIZ"
    assert sl_verdict("TP", 0.7, {"post240_max_adv_r": -3}) == ""


def test_trade_features_end_to_end(sb):
    entry = START + pd.Timedelta(days=12, hours=15, minutes=2, seconds=10)
    row = _row(sb, entry, entry + pd.Timedelta(minutes=45))
    f = trade_features(row, sb, START + pd.Timedelta(days=DAYS))
    assert f is not None
    for k in ("pre_ret_15", "geo_sl_atr5", "path_mfe_r", "post240_max_fav_r", "e15_open"):
        assert k in f
    assert f["path_mfe_r"] >= 0 >= f["path_mae_r"]


def test_tag_frequency_and_decisions():
    t = pd.DataFrame({
        "entry_utc": pd.date_range(START, periods=6, freq="1h"), "symbol": SYM, "direction": "BUY",
        "outcome": ["SL", "SL", "TP", "TP", "TP", "SL"], "r_exit": [-1, -1, .7, .7, .7, -1],
        "etiket_giris": ["DAR_STOP", "DAR_STOP", "", "DAR_STOP", "", "DAR_STOP"] * 1, "etiket_yol": [""] * 6,
    })
    t.loc[1, "entry_utc"] = t.loc[0, "entry_utc"] + pd.Timedelta(minutes=1)   # bölünmüş bacak → tek karar
    t["decision_id"] = align.assign_decisions(t)
    assert t["decision_id"].nunique() == 5
    freq = compare.tag_frequency(t.assign(etiket_giris=t["etiket_giris"]))
    assert freq.empty or (freq["n"] >= 5).all()


def test_formatting_helpers():
    assert tr_num(-1234.567, 1) == "−1.234,6"
    assert tr_num(-0.0001, 2) == "0,00"
    df = pd.DataFrame({"n": [3, 4], "x": [0.5, 1.25]})
    out = md_table(df)
    assert "| 3 | 0,50 |" in out


def test_analogs_only_use_past_trades():
    from scripts.islem_otopsi import analogs
    rng = np.random.default_rng(3)
    n = 60
    t = pd.DataFrame({"pid": range(n), "side": "NDX BUY", "family": "X",
                      "entry_utc": pd.date_range(START, periods=n, freq="1h"),
                      "outcome": rng.choice(["SL", "TP"], n), "r_exit": rng.normal(size=n), "net": 0.0,
                      "ana_neden_kod": "", "decision_id": range(n)})
    t["exit_utc"] = t["entry_utc"] + pd.Timedelta(minutes=30)
    for c in analogs.ANALOG_FEATURES:
        t[c] = rng.normal(size=n)
    target = t.iloc[40]
    nb = analogs.nearest(t, target)
    assert len(nb) == analogs.K and (nb["entry_utc"] < target["entry_utc"]).all()
