"""Tek-yazar politikası (PREDICTION_LOGS_WRITER) + yazar kimliği etiketi."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import writer_identity as wi  # noqa: E402


def test_writes_enabled_by_default(monkeypatch):
    monkeypatch.delenv(wi.PREDICTION_LOGS_WRITER_ENV, raising=False)
    assert wi.prediction_log_writes_enabled() is True


def test_writes_disabled_with_zero(monkeypatch):
    monkeypatch.setenv(wi.PREDICTION_LOGS_WRITER_ENV, "0")
    assert wi.prediction_log_writes_enabled() is False


def test_railway_host_label(monkeypatch):
    monkeypatch.setenv("RAILWAY_SERVICE_NAME", "upbeat-flow")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_NAME", "production")
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "50afb451deadbeef")
    assert wi._host_label() == "railway:upbeat-flow/production"
    assert wi._git_sha() == "50afb451"


def test_log_paths_noop_when_writer_off(monkeypatch):
    monkeypatch.setenv(wi.PREDICTION_LOGS_WRITER_ENV, "0")
    from services import prediction_logger as pl
    from services import meta_signal_logger as msl

    async def run():
        assert await pl.log_prediction("NDX.INDX", {}, {}, "5m", model_type="pulse1") is None
        assert await pl.log_smc_prediction("NDX.INDX", "5m", "BUY", 80, 29500.0) is None
        assert await pl.mark_prediction_checked("00000000-0000-0000-0000-000000000000") is False
        assert await msl.log_meta_prediction({"symbol": "NDX.INDX", "direction": "BUY"}) is None

    asyncio.run(run())
