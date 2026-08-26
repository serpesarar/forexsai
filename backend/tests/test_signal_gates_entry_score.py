"""entry_score_gate + yeni seans saatleri testleri (2026-07-10 MT5 otopsi kapıları)."""
from datetime import datetime, timezone

import pytest

from services.signal_gates import (
    SESSION_BLOCK_HOURS_UTC,
    compute_entry_score,
    session_gate,
)


def _mk_candles(n: int, start: float = 100.0, step: float = 0.1, vol: float = 100.0):
    """Yavaş yükselen sentetik mumlar (BUY lehine trend)."""
    out = []
    px = start
    for i in range(n):
        o = px
        px += step
        out.append({
            "open": o, "high": max(o, px) + 0.05, "low": min(o, px) - 0.05,
            "close": px, "volume": vol,
        })
    return out


NOON = datetime(2026, 7, 10, 16, 0, tzinfo=timezone.utc)  # NDX/USOIL için serbest saat


class TestSessionHours:
    def test_ndx_blocked_hours(self):
        for h in (3, 4, 18, 22):
            ok, reason = session_gate("NDX.INDX", now=datetime(2026, 7, 10, h, 30, tzinfo=timezone.utc))
            assert not ok and "Seans kapısı" in reason

    def test_ndx_open_hours(self):
        ok, _ = session_gate("NDX.INDX", now=NOON)
        assert ok

    def test_usoil_blocked_before_ny(self):
        ok, _ = session_gate("USOIL.FOREX", now=datetime(2026, 7, 10, 8, 0, tzinfo=timezone.utc))
        assert not ok

    def test_usoil_open_after_12(self):
        ok, _ = session_gate("USOIL.FOREX", now=NOON)
        assert ok

    def test_existing_symbols_untouched(self):
        assert SESSION_BLOCK_HOURS_UTC["XAUUSD"] == (20, 1, 2)
        assert SESSION_BLOCK_HOURS_UTC["GDAXI.INDX"] == (7,)


class TestComputeEntryScore:
    def test_aligned_buy_full_score(self):
        c5 = _mk_candles(260)
        c30 = _mk_candles(60)
        score, fails = compute_entry_score("NDX.INDX", "BUY", c5, c30, now=NOON)
        assert score == 8, fails

    def test_counter_trend_sell_fails_trend_conditions(self):
        c5 = _mk_candles(260)  # yükselen seri → SELL karşı-trend
        c30 = _mk_candles(60)
        score, fails = compute_entry_score("NDX.INDX", "SELL", c5, c30, now=NOON)
        assert "5m_trend" in fails and "30m_trend" in fails and "ema200_tarafi" in fails
        assert score <= 5

    def test_blocked_hour_costs_a_point(self):
        c5 = _mk_candles(260)
        c30 = _mk_candles(60)
        night = datetime(2026, 7, 10, 3, 0, tzinfo=timezone.utc)
        score, fails = compute_entry_score("NDX.INDX", "BUY", c5, c30, now=night)
        assert "saat_penceresi" in fails and score == 7

    def test_volume_spike_fails(self):
        c5 = _mk_candles(260)
        c5[-1]["volume"] = 1000.0  # 10× ortalama
        score, fails = compute_entry_score("NDX.INDX", "BUY", c5, _mk_candles(60), now=NOON)
        assert "hacim_patlamasi" in fails

    def test_knife_catch_buy_fails(self):
        # 30dk'da sert düşüş → BUY bıçak yakalama + karşı momentum
        c5 = _mk_candles(250) + _mk_candles(10, start=125.0, step=-2.0)
        score, fails = compute_entry_score("NDX.INDX", "BUY", c5, _mk_candles(60), now=NOON)
        assert "bicak_yakalama" in fails and "1h_karsi_momentum" in fails

    def test_missing_data_fail_open(self):
        score, fails = compute_entry_score("NDX.INDX", "BUY", None, None, now=NOON)
        assert score == 8 and fails == []


class TestEntryScoreGate:
    @pytest.mark.asyncio
    async def test_gate_disabled_by_env(self, monkeypatch):
        from services import signal_gates
        monkeypatch.setenv("ENTRY_SCORE_GATE_ENABLED", "0")
        ok, _ = await signal_gates.entry_score_gate("NDX.INDX", "BUY")
        assert ok

    @pytest.mark.asyncio
    async def test_gate_skips_uncovered_symbol(self):
        from services import signal_gates
        ok, _ = await signal_gates.entry_score_gate("XAUUSD", "BUY")
        assert ok

    @staticmethod
    def _patch_candles(monkeypatch):
        async def fake_ohlcv(symbol, timeframe="1H", limit=250):
            if timeframe == "5m":
                return _mk_candles(260)
            return _mk_candles(60)

        import services.market_data_service as mds
        monkeypatch.setattr(mds, "get_ohlcv_data", fake_ohlcv)

    @pytest.mark.asyncio
    async def test_gate_blocks_low_score(self, monkeypatch):
        """ENTRY_SCORE_GATE_BLOCK=1 iken düşük skor GERÇEKTEN bloklanır.

        ⚠️ Bu kapı 2026-08-11'den beri VARSAYILAN GÖLGE (sızıntısız canlı ölçüm
        aleyhine çıktı). Blok davranışı ancak bayrak açıkken beklenebilir —
        bayrağı kurmayan bir test gölge davranışını "hata" sanır.
        """
        from services import signal_gates
        monkeypatch.setenv("ENTRY_SCORE_GATE_BLOCK", "1")
        self._patch_candles(monkeypatch)
        # Yükselen seride SELL → çok koşul ihlali → blok
        ok, reason = await signal_gates.entry_score_gate(
            "NDX.INDX", "SELL", now=NOON
        )
        assert not ok and "Giriş skoru kapısı" in reason

    @pytest.mark.asyncio
    async def test_gate_shadow_mode_passes_but_records_verdict(self, monkeypatch):
        """Varsayılan (GÖLGE): sinyal GEÇER ama "bloklardım" verdikti kaydedilir.

        Verdikt olmadan kapının açılmasının doğru karar olup olmadığı
        ölçülemez — Gölge Modu paneli tam bu kaydı okur.
        """
        from services import signal_gates
        monkeypatch.setenv("ENTRY_SCORE_GATE_BLOCK", "0")
        self._patch_candles(monkeypatch)

        sink: list = []
        token = signal_gates._shadow_sink.set(sink)
        try:
            ok, reason = await signal_gates.entry_score_gate(
                "NDX.INDX", "SELL", now=NOON
            )
        finally:
            signal_gates._shadow_sink.reset(token)

        assert ok and reason is None, "gölge modda bloklamamalı"
        assert [v["gate"] for v in sink] == ["entry_score_gate"]
        assert "giriş skoru" in sink[0]["reason"].lower()

    @pytest.mark.asyncio
    async def test_gate_fail_open_on_error(self, monkeypatch):
        from services import signal_gates
        import services.market_data_service as mds

        async def boom(*a, **k):
            raise RuntimeError("veri yok")

        monkeypatch.setattr(mds, "get_ohlcv_data", boom)
        ok, _ = await signal_gates.entry_score_gate("NDX.INDX", "BUY", now=NOON)
        assert ok
