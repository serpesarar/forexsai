"""Stage 3.6 — macro daily-bias layer inside the Precision Veto Engine.

Isolates the macro block by feeding mid-zone candles (Stage 1 liquidity/MTF
pass) and disabling Stages 2/1c/3/4, so the only thing that can move
adjusted_confidence is the NASDAQ macro bias.
"""
import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import services.data_fetcher as data_fetcher  # noqa: E402
import services.daily_bias_service as bias_svc  # noqa: E402
from services import precision_veto_service as pv  # noqa: E402


# Mid-zone candles: price 20000 sits ~0.5 in the last-50 high/low band, so
# neither BUY (premium) nor SELL (discount) liquidity vetoes fire.
def _candles(n=60, base=20000.0):
    out = []
    for i in range(n):
        wig = 40 if i % 2 == 0 else -40
        out.append({"open": base, "high": base + 50, "low": base - 50,
                    "close": base + wig})
    return out


@pytest.fixture
def isolated(monkeypatch):
    async def fake_fetch(symbol, timeframe, limit=120):
        return [] if timeframe in ("1h", "4h") else _candles()
    monkeypatch.setattr(data_fetcher, "fetch_ohlc_data", fake_fetch)

    # Keep Stage 1 (macro block lives inside it); silence the rest.
    for k in ("stage_2_enabled", "stage_1c_enabled", "stage_3_enabled", "stage_4_enabled"):
        monkeypatch.setitem(pv.PRECISION_VETO_CONFIG, k, False)
    monkeypatch.setitem(pv.PRECISION_VETO_CONFIG, "macro_bias_enabled", True)
    bias_svc._clear_cache()
    yield
    bias_svc._clear_cache()


def _set_bias(monkeypatch, bias):
    monkeypatch.setattr(bias_svc, "get_current_bias", lambda *a, **k: bias)


def _sig(direction="BUY", conf=70.0, symbol="NDX.INDX"):
    return {"symbol": symbol, "direction": direction, "confidence": conf,
            "timeframe": "15m", "price": 20000.0, "model_type": "ml"}


async def _run(sig):
    return await pv.check_signal(sig)


def _bias(b, conf, **extra):
    return {"nasdaq_daily_bias": b, "confidence": conf, "is_invalidated": False, **extra}


@pytest.mark.asyncio
async def test_bullish_buy_gets_bonus(isolated, monkeypatch):
    _set_bias(monkeypatch, _bias("bullish", 60))
    res = await _run(_sig("BUY", 70))
    assert res.features["macro_bias_state"] == "bullish"
    assert res.macro_bias_bonus == pytest.approx(12.0)        # min(15, 60*0.2)
    assert res.adjusted_confidence > 70.0                     # bonus applied
    assert not res.would_veto


@pytest.mark.asyncio
async def test_bearish_buy_gets_penalty(isolated, monkeypatch):
    _set_bias(monkeypatch, _bias("bearish", 60))
    res = await _run(_sig("BUY", 70))
    assert res.features["macro_bias_state"] == "bearish"
    assert res.total_penalty == pytest.approx(15.0)           # min(20, 60*0.25)
    assert res.adjusted_confidence == pytest.approx(55.0)


@pytest.mark.asyncio
async def test_bearish_buy_high_conf_soft_veto(isolated, monkeypatch):
    _set_bias(monkeypatch, _bias("bearish", 90))
    res = await _run(_sig("BUY", 70))
    assert res.would_veto is True
    assert res.reason == "macro_bias_opposition"
    assert res.stage == 1


@pytest.mark.asyncio
async def test_choppy_penalises(isolated, monkeypatch):
    _set_bias(monkeypatch, _bias("choppy", 50))
    res = await _run(_sig("BUY", 70))
    assert res.total_penalty == pytest.approx(10.0)
    assert res.adjusted_confidence == pytest.approx(60.0)


@pytest.mark.asyncio
async def test_invalidated_bias_no_effect(isolated, monkeypatch):
    b = _bias("bullish", 90); b["is_invalidated"] = True
    _set_bias(monkeypatch, b)
    res = await _run(_sig("BUY", 70))
    assert res.macro_bias_bonus == 0.0
    assert res.total_penalty == 0.0
    assert res.adjusted_confidence == pytest.approx(70.0)     # untouched


@pytest.mark.asyncio
async def test_no_bias_is_regression_safe(isolated, monkeypatch):
    _set_bias(monkeypatch, None)
    res = await _run(_sig("BUY", 70))
    assert res.macro_bias_bonus == 0.0
    assert res.total_penalty == 0.0
    assert res.adjusted_confidence == pytest.approx(70.0)


@pytest.mark.asyncio
async def test_non_nasdaq_untouched(isolated, monkeypatch):
    # Even with a stored bullish bias, XAUUSD must be a no-op.
    _set_bias(monkeypatch, _bias("bullish", 90))
    res = await _run(_sig("SELL", 70, symbol="XAUUSD"))
    assert res.macro_bias_bonus == 0.0
    assert res.total_penalty == 0.0
    assert "macro_bias_state" not in res.features             # scope-guarded out


@pytest.mark.asyncio
async def test_macro_disabled_flag(isolated, monkeypatch):
    monkeypatch.setitem(pv.PRECISION_VETO_CONFIG, "macro_bias_enabled", False)
    _set_bias(monkeypatch, _bias("bullish", 90))
    res = await _run(_sig("BUY", 70))
    assert res.macro_bias_bonus == 0.0
    assert res.adjusted_confidence == pytest.approx(70.0)


@pytest.mark.asyncio
async def test_log_dict_includes_macro_columns(isolated, monkeypatch):
    _set_bias(monkeypatch, _bias("bearish", 60))
    sig = _sig("BUY", 70)
    res = await _run(sig)
    row = res.to_log_dict(sig)
    assert row["macro_bias_state"] == "bearish"
    assert row["macro_bias_adjustment"] == pytest.approx(-15.0)
