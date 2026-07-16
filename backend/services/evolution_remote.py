"""
Evrim Ajanı köprüsü (panel tarafı) — MT5 kutusuyla Supabase üzerinden konuşur.

Tablolar: agent_heartbeat / bot_trades / decider_journal / evolution_commands
Karşı uç: remote_agent/evolution_agent.py (Windows MT5 kutusunda).

Tüm Supabase çağrıları sync httpx client'la yapılır — event loop'u kilitlememek
için router'lar bu modülün fonksiyonlarını asyncio.to_thread ile çağırır.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from database.supabase_client import get_supabase_client, is_db_available

logger = logging.getLogger(__name__)

DEFAULT_HOST = "mt5_box"
ONLINE_WINDOW_SECONDS = 420  # heartbeat 5 dk'da bir → 7 dk görülmediyse çevrimdışı
_CMD_ID_RE = re.compile(r"^cmd_([0-9a-f-]{36})$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _client():
    if not is_db_available():
        raise RuntimeError("Supabase erişilemiyor — köprü çalışamaz")
    return get_supabase_client()


# ── Durum ─────────────────────────────────────────────────────────────────

def get_remote_status(host: str = DEFAULT_HOST) -> Dict[str, Any]:
    """Kutu canlı mı + kuyruk durumu + son komutlar (panelin Canlı Bot kartı)."""
    client = _client()
    hb_res = client.table("agent_heartbeat").select("*").eq("host", host).execute()
    hb_rows = hb_res.get("data") or []
    heartbeat = hb_rows[0] if hb_rows else None

    online = False
    last_seen_ago_s: Optional[int] = None
    if heartbeat:
        seen = _parse_ts(heartbeat.get("last_seen"))
        if seen:
            last_seen_ago_s = int((_now() - seen).total_seconds())
            online = last_seen_ago_s < ONLINE_WINDOW_SECONDS

    cmd_res = (client.table("evolution_commands").select(
        "id,created_at,kind,status,requested_by,analysis_id,analysis_name,finished_at,return_code")
        .eq("host", host).order("created_at", desc=True).limit(12).execute())
    commands = cmd_res.get("data") or []
    pending = sum(1 for c in commands if c.get("status") == "pending")
    running = sum(1 for c in commands if c.get("status") == "running")

    return {
        "host": host,
        "online": online,
        "last_seen": heartbeat.get("last_seen") if heartbeat else None,
        "last_seen_ago_s": last_seen_ago_s,
        "meta": (heartbeat or {}).get("meta") or {},
        "pending_commands": pending,
        "running_commands": running,
        "recent_commands": commands,
    }


# ── Bot & Decider performansı ─────────────────────────────────────────────

def get_bot_performance(days: int = 30, host: str = DEFAULT_HOST) -> Dict[str, Any]:
    """bot_trades'ten sembol kırılımlı WR + toplam kâr (gerçek MT5 sonuçları)."""
    client = _client()
    since = (_now() - timedelta(days=days)).isoformat()
    res = (client.table("bot_trades")
           .select("symbol,profit,commission,swap,close_time,comment")
           .eq("host", host).gte("close_time", since)
           .order("close_time", desc=True).limit(5000).execute())
    trades = res.get("data") or []

    by_symbol: Dict[str, Dict[str, Any]] = {}
    total_net = 0.0
    wins = 0
    for t in trades:
        net = (t.get("profit") or 0) + (t.get("commission") or 0) + (t.get("swap") or 0)
        total_net += net
        if net > 0:
            wins += 1
        s = by_symbol.setdefault(t.get("symbol") or "?", {"n": 0, "wins": 0, "net": 0.0})
        s["n"] += 1
        s["wins"] += 1 if net > 0 else 0
        s["net"] += net

    for s in by_symbol.values():
        s["win_rate"] = round(100 * s["wins"] / s["n"], 1) if s["n"] else None
        s["net"] = round(s["net"], 2)

    return {
        "days": days,
        "total_trades": len(trades),
        "win_rate": round(100 * wins / len(trades), 1) if trades else None,
        "net_profit": round(total_net, 2),
        "by_symbol": by_symbol,
        "last_trade_at": trades[0].get("close_time") if trades else None,
    }


def get_decider_stats(days: int = 30, host: str = DEFAULT_HOST) -> Dict[str, Any]:
    """decider_journal'dan karar dağılımı + sonuçlanmışlarda isabet."""
    client = _client()
    since = (_now() - timedelta(days=days)).isoformat()
    res = (client.table("decider_journal").select("decision,outcome,ts,symbol")
           .eq("host", host).gte("inserted_at", since)
           .order("inserted_at", desc=True).limit(3000).execute())
    rows = res.get("data") or []

    decisions: Dict[str, int] = {}
    resolved = 0
    correct = 0
    for r in rows:
        d = (r.get("decision") or "?").upper()
        decisions[d] = decisions.get(d, 0) + 1
        outcome = r.get("outcome") or {}
        if isinstance(outcome, dict) and outcome.get("result") in ("win", "loss"):
            resolved += 1
            if outcome["result"] == "win":
                correct += 1

    return {
        "days": days,
        "total_decisions": len(rows),
        "decisions": decisions,
        "resolved": resolved,
        "win_rate": round(100 * correct / resolved, 1) if resolved else None,
        "last_decision_at": rows[0].get("ts") if rows else None,
    }


# ── Komut kuyruğu ─────────────────────────────────────────────────────────

ALLOWED_KINDS = {"run_analysis", "sync_lessons", "git_pull", "restart_bot"}


def enqueue_command(
    kind: str,
    payload: Optional[dict] = None,
    host: str = DEFAULT_HOST,
    requested_by: str = "panel",
    analysis_id: Optional[str] = None,
    analysis_name: Optional[str] = None,
) -> dict:
    """Kuyruğa komut yaz; ajan 30 sn içinde alır."""
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"bilinmeyen komut türü: {kind}")
    client = _client()
    res = client.table("evolution_commands").insert({
        "host": host,
        "kind": kind,
        "payload": payload or {},
        "requested_by": requested_by,
        "analysis_id": analysis_id,
        "analysis_name": analysis_name,
        "status": "pending",
    })
    rows = res.get("data") or []
    if not rows:
        raise RuntimeError(f"komut kuyruğa yazılamadı: {res.get('error')}")
    return rows[0]


def get_command(cmd_id: str) -> Optional[dict]:
    client = _client()
    res = client.table("evolution_commands").select("*").eq("id", cmd_id).execute()
    rows = res.get("data") or []
    return rows[0] if rows else None


def command_to_run_meta(cmd: dict) -> dict:
    """Komut satırını panelin RunMeta şekline çevir — RunDrawer değişmeden çalışır."""
    status_map = {"pending": "running", "running": "running", "done": "done",
                  "failed": "failed", "timeout": "timeout"}
    output = cmd.get("output") or ""
    if cmd.get("status") == "pending":
        output = "[uzak] Komut kuyruğa alındı — MT5 kutusundaki ajan 30 sn içinde başlatacak…"
    return {
        "run_id": f"cmd_{cmd['id']}",
        "analysis_id": cmd.get("analysis_id") or cmd.get("kind"),
        "analysis_name": cmd.get("analysis_name") or f"[uzak] {cmd.get('kind')}",
        "command": (cmd.get("payload") or {}).get("command", cmd.get("kind", "")),
        "status": status_map.get(cmd.get("status", "pending"), "failed"),
        "started_at": cmd.get("started_at") or cmd.get("created_at"),
        "finished_at": cmd.get("finished_at"),
        "return_code": cmd.get("return_code"),
        "output": output,
        "output_truncated": False,
        "remote": True,
    }


def parse_cmd_run_id(run_id: str) -> Optional[str]:
    """'cmd_<uuid>' → uuid; değilse None."""
    m = _CMD_ID_RE.match(run_id or "")
    return m.group(1) if m else None


def start_remote_analysis(analysis: dict, extra_args: str = "") -> dict:
    """Panel kataloğundaki runnable_here=false analizi kutuda başlat."""
    command = (analysis.get("command") or "").strip()
    if not command:
        raise ValueError("bu analizin komutu tanımlı değil — uzakta çalıştırılamaz")
    if extra_args.strip():
        command = f"{command} {extra_args.strip()}"
    status = get_remote_status()
    if not status["online"]:
        raise RuntimeError(
            "MT5 kutusundaki Evrim Ajanı çevrimdışı — kutuda start_agent.bat çalışıyor mu?")
    cmd = enqueue_command(
        kind="run_analysis",
        payload={"command": command, "cwd": analysis.get("cwd", ""), "timeout": 1800},
        analysis_id=analysis.get("id"),
        analysis_name=analysis.get("name"),
    )
    return command_to_run_meta(cmd)
