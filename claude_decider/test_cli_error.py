"""call_claude hata gövdesinin okunur hale getirilmesi (2026-11-11: stdout[:200] asıl mesajı kesiyordu)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decide  # noqa: E402

CLI_JSON = {"type": "result", "is_error": True, "duration_api_ms": 0, "session_id": "s",
            "total_cost_usd": 0, "usage": {"input_tokens": 0, "output_tokens_details": {"thinking_tokens": 0}}}


def _json(result: str, **extra) -> str:
    return json.dumps({**CLI_JSON, "result": result, **extra})


def test_quota_message_survives_long_usage_block() -> None:
    kind, msg = decide._cli_error_detail(_json("You've hit your weekly limit · resets Nov 14"), "")
    assert kind == "kota"
    assert "weekly limit" in msg


def test_auth_and_model_kinds() -> None:
    assert decide._cli_error_detail(_json("Not logged in · Please run /login"), "")[0] == "oturum"
    assert decide._cli_error_detail(_json("model not found", api_error_status=404), "")[0] == "model"


def test_non_json_falls_back_to_raw_text() -> None:
    kind, msg = decide._cli_error_detail("plain failure", "trace")
    assert kind == "bilinmiyor"
    assert "plain failure" in msg and "trace" in msg


def test_call_claude_reason_keeps_agent_prefix(monkeypatch) -> None:
    """Ajanın arıza sayacı 'claude exit' önekine bakıyor; önek korunmalı."""
    done = subprocess.CompletedProcess(args=[], returncode=1, stdout=_json("Claude AI usage limit reached"), stderr="")
    monkeypatch.setattr(decide.subprocess, "run", lambda *a, **k: done)
    monkeypatch.setattr(decide, "_claude_bin", lambda: "claude")
    monkeypatch.setattr(decide, "_sandbox", lambda: ".")
    dec = decide.call_claude("p")
    assert dec["action"] == "WAIT" and dec["_error"] is True
    assert dec["reason"].startswith("claude exit 1 [kota]:")
    assert "usage limit reached" in dec["reason"]
    assert dec["_error_kind"] == "kota"
