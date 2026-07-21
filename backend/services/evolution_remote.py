"""
Evrim Ajanı köprüsü (panel tarafı) — MT5 kutusuyla Supabase üzerinden konuşur.

Tablolar: agent_heartbeat / bot_trades / decider_journal / evolution_commands
Karşı uç: remote_agent/evolution_agent.py (Windows MT5 kutusunda).

Tüm Supabase çağrıları sync httpx client'la yapılır — event loop'u kilitlememek
için router'lar bu modülün fonksiyonlarını asyncio.to_thread ile çağırır.
"""
from __future__ import annotations

import json
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
        "id,created_at,kind,status,requested_by,analysis_id,analysis_name,started_at,finished_at,return_code")
        .eq("host", host).order("created_at", desc=True).limit(12).execute())
    commands = cmd_res.get("data") or []
    # Güvenlik ağı: 3 saatten uzun 'running' = ajan o komutta öldü (kesinti).
    # Ajan yeniden başlarken bunları failed'a çeker; panel beklerken de doğru göstersin.
    for c in commands:
        if c.get("status") == "running":
            st = _parse_ts(c.get("started_at") or c.get("created_at"))
            if st and (_now() - st).total_seconds() > 3 * 3600:
                c["status"] = "interrupted"
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


def _parse_decider_action(decision: Any) -> tuple[str, Optional[str]]:
    """decider_journal.decision alanından (action, direction) çıkar.

    Gerçek format: decision bir JSON STRING —
    '{"action":"WAIT|OPEN","direction":"BUY|SELL|null",...}'. Eski kod bunu ham
    string olarak okuyup .upper() yapıyordu → her satır benzersiz anahtar,
    WAIT/OPEN sayımı 0, decider "aktif değil" görünüyordu. Artık parse ediyoruz.
    """
    if isinstance(decision, dict):
        obj = decision
    elif isinstance(decision, str) and decision.strip().startswith("{"):
        try:
            obj = json.loads(decision)
        except (ValueError, TypeError):
            return "?", None
    else:
        return (str(decision).upper() if decision else "?"), None
    action = str(obj.get("action") or "?").upper()
    direction = obj.get("direction")
    return action, (str(direction).upper() if direction else None)


def get_decider_stats(days: int = 30, host: str = DEFAULT_HOST) -> Dict[str, Any]:
    """decider_journal'dan karar dağılımı + sonuçlanmışlarda isabet.

    Karar formatı: her satır bir NASDAQ karar-anı. action=WAIT (bekle, işlem yok)
    veya action=OPEN (BUY/SELL işlem). OPEN kararlarının outcome'u WIN/LOSS/null.
    win_rate yalnız sonuçlanan OPEN'lardan hesaplanır (WAIT'in sonucu olmaz).
    """
    client = _client()
    since = (_now() - timedelta(days=days)).isoformat()
    res = (client.table("decider_journal").select("decision,outcome,ts,symbol")
           .eq("host", host).gte("inserted_at", since)
           .order("inserted_at", desc=True).limit(5000).execute())
    rows = res.get("data") or []

    decisions: Dict[str, int] = {}   # WAIT / BUY / SELL (kullanıcıya anlamlı)
    wait_count = 0
    open_count = 0
    resolved = 0
    correct = 0
    last_open_at: Optional[str] = None

    def _outcome_str(o: Any) -> Optional[str]:
        if isinstance(o, str):
            return o.strip().upper() or None
        if isinstance(o, dict):
            v = o.get("result") or o.get("outcome") or o.get("status")
            return str(v).strip().upper() if v else None
        return None

    for r in rows:
        action, direction = _parse_decider_action(r.get("decision"))
        if action == "WAIT":
            wait_count += 1
            decisions["WAIT"] = decisions.get("WAIT", 0) + 1
        elif action in ("OPEN", "BUY", "SELL"):
            open_count += 1
            key = direction or ("BUY" if action == "BUY" else "SELL" if action == "SELL" else "OPEN")
            decisions[key] = decisions.get(key, 0) + 1
            last_open_at = last_open_at or r.get("ts")
            oc = _outcome_str(r.get("outcome"))
            if oc in ("WIN", "LOSS", "TP", "SL"):
                resolved += 1
                if oc in ("WIN", "TP"):
                    correct += 1
        else:
            decisions[action] = decisions.get(action, 0) + 1

    return {
        "days": days,
        "total_decisions": len(rows),
        "wait_count": wait_count,
        "open_count": open_count,
        "decisions": decisions,
        "resolved": resolved,
        "win_rate": round(100 * correct / resolved, 1) if resolved else None,
        "last_decision_at": rows[0].get("ts") if rows else None,
        "last_trade_decision_at": last_open_at,
        # 48 saat içinde karar geldiyse decider canlı sayılır (panel rozeti)
        "active": bool(rows and _parse_ts(rows[0].get("ts"))
                       and (_now() - _parse_ts(rows[0].get("ts"))).total_seconds() < 48 * 3600),
    }


def get_decider_breakdown(days: int = 30, host: str = DEFAULT_HOST) -> Dict[str, Any]:
    """Decider yüzdesine tıkla → sembol × yön kırılımı + son kararlar.

    Kaynak decider_journal: her OPEN kararının yönü decision JSON'unda,
    sonucu outcome kolonunda (WIN/LOSS). WAIT'ler sembol başına ayrı sayılır.
    """
    client = _client()
    since = (_now() - timedelta(days=days)).isoformat()
    res = (client.table("decider_journal").select("decision,outcome,ts,symbol")
           .eq("host", host).gte("inserted_at", since)
           .order("ts", desc=True).limit(5000).execute())
    rows = res.get("data") or []

    def _oc(o: Any) -> Optional[str]:
        s = (o if isinstance(o, str) else "").strip().upper()
        return s if s in ("WIN", "LOSS") else None

    by_symbol: Dict[str, dict] = {}
    recent: List[dict] = []
    for r in rows:
        action, direction = _parse_decider_action(r.get("decision"))
        sym = r.get("symbol") or "?"
        s = by_symbol.setdefault(sym, {"waits": 0, "opens": 0, "wins": 0, "losses": 0,
                                       "open_pending": 0, "by_direction": {}})
        if action == "WAIT":
            s["waits"] += 1
            continue
        if action not in ("OPEN", "BUY", "SELL"):
            continue
        d = direction or "?"
        s["opens"] += 1
        dd = s["by_direction"].setdefault(d, {"n": 0, "wins": 0, "losses": 0})
        dd["n"] += 1
        oc = _oc(r.get("outcome"))
        if oc == "WIN":
            s["wins"] += 1; dd["wins"] += 1
        elif oc == "LOSS":
            s["losses"] += 1; dd["losses"] += 1
        else:
            s["open_pending"] += 1
        if len(recent) < 20:
            reason = ""
            dec = r.get("decision")
            if isinstance(dec, str) and dec.startswith("{"):
                try:
                    reason = str(json.loads(dec).get("reason") or "")[:160]
                except (ValueError, TypeError):
                    pass
            recent.append({"ts": r.get("ts"), "symbol": sym, "direction": d,
                           "outcome": oc, "reason": reason})

    def _wr(w: int, l: int) -> Optional[float]:
        return round(100 * w / (w + l), 1) if (w + l) else None

    for s in by_symbol.values():
        s["win_rate"] = _wr(s["wins"], s["losses"])
        for dd in s["by_direction"].values():
            dd["win_rate"] = _wr(dd["wins"], dd["losses"])

    return {"days": days, "by_symbol": by_symbol, "recent": recent}


# Bot (broker sembolü) ↔ Decider (panel sembolü) eşlemesi.
_BOT_SYMBOL_MAP = {
    "NAS100": "NDX.INDX",
    "GER40": "GDAXI.INDX",
    "SpotCrude": "USOIL.FOREX",
    "XAUUSD": "XAUUSD",
    "US100": "NDX.INDX",
    "USOIL": "USOIL.FOREX",
}
_PAIR_WINDOW_H = 3  # "yakın zaman dilimi" eşleme penceresi (saat)


def get_bot_vs_decider(days: int = 30, host: str = DEFAULT_HOST) -> Dict[str, Any]:
    """Forex botu ↔ Claude Decider yakın-zaman karşılaştırması + karşılıklı dersler.

    Aynı sembolde ±3 saat penceresinde eşleştirir:
      - agree_*: ikisi de aynı yönde açtı
      - conflict_*: zıt yönde açtılar
      - decider_korudu / decider_kacirdi: bot açtı, decider en yakın kararında WAIT dedi
      - bot_kacirdi / bot_korundu: decider açtı, bot o pencerede hiç işlem yapmadı
    'Dersler' bu istatistiklerden kural-bazlı üretilir (LLM yok — dürüst sayım).
    """
    client = _client()
    since = (_now() - timedelta(days=days)).isoformat()

    trades = (client.table("bot_trades")
              .select("ticket,symbol,direction,close_time,profit,commission,swap")
              .eq("host", host).gte("close_time", since)
              .order("close_time").limit(3000).execute()).get("data") or []
    for t in trades:
        t["net"] = (t.get("profit") or 0) + (t.get("commission") or 0) + (t.get("swap") or 0)
        t["nsym"] = _BOT_SYMBOL_MAP.get(t.get("symbol") or "", t.get("symbol"))
        t["t"] = _parse_ts(t.get("close_time"))

    jrows = (client.table("decider_journal").select("decision,outcome,ts,symbol")
             .eq("host", host).gte("inserted_at", since)
             .order("ts").limit(5000).execute()).get("data") or []
    devents = []
    for r in jrows:
        action, direction = _parse_decider_action(r.get("decision"))
        ts = _parse_ts(r.get("ts"))
        if ts is None or action not in ("WAIT", "OPEN", "BUY", "SELL"):
            continue
        oc = (r.get("outcome") if isinstance(r.get("outcome"), str) else "") or ""
        devents.append({"ts": ts, "sym": r.get("symbol"),
                        "action": "WAIT" if action == "WAIT" else "OPEN",
                        "direction": direction, "outcome": oc.strip().upper()})

    window = timedelta(hours=_PAIR_WINDOW_H)
    stats = {
        "agree_n": 0, "agree_bot_win": 0, "agree_decider_win": 0,
        "conflict_n": 0, "conflict_bot_win": 0, "conflict_decider_win": 0,
        "decider_korudu": 0, "decider_kacirdi": 0,
        "bot_korundu": 0, "bot_kacirdi": 0,
    }
    pairs: List[dict] = []
    matched_open_ids: set = set()

    for t in trades:
        if t["t"] is None:
            continue
        near = [e for e in devents if e["sym"] == t["nsym"] and abs(e["ts"] - t["t"]) <= window]
        if not near:
            continue
        opens = [e for e in near if e["action"] == "OPEN"]
        ev = min(opens or near, key=lambda e: abs(e["ts"] - t["t"]))
        bot_win = t["net"] > 0
        cat = ""
        if ev["action"] == "OPEN":
            matched_open_ids.add(id(ev))
            if (ev["direction"] or "?") == (t.get("direction") or "!"):
                cat = "agree"
                stats["agree_n"] += 1
                stats["agree_bot_win"] += 1 if bot_win else 0
                stats["agree_decider_win"] += 1 if ev["outcome"] == "WIN" else 0
            else:
                cat = "conflict"
                stats["conflict_n"] += 1
                stats["conflict_bot_win"] += 1 if bot_win else 0
                stats["conflict_decider_win"] += 1 if ev["outcome"] == "WIN" else 0
        else:  # en yakın karar WAIT
            cat = "decider_kacirdi" if bot_win else "decider_korudu"
            stats[cat] += 1
        if len(pairs) < 40:
            pairs.append({
                "time": t["close_time"], "symbol": t["nsym"], "category": cat,
                "bot_direction": t.get("direction"), "bot_net": round(t["net"], 2),
                "decider_action": ev["action"], "decider_direction": ev["direction"],
                "decider_outcome": ev["outcome"] or None,
            })

    # Decider'ın açıp botun hiç dokunmadığı pencereler
    bot_by_sym: Dict[str, list] = {}
    for t in trades:
        if t["t"] is not None:
            bot_by_sym.setdefault(t["nsym"], []).append(t["t"])
    for e in devents:
        if e["action"] != "OPEN" or id(e) in matched_open_ids or e["outcome"] not in ("WIN", "LOSS"):
            continue
        if any(abs(bt - e["ts"]) <= window for bt in bot_by_sym.get(e["sym"], [])):
            continue
        if e["outcome"] == "WIN":
            stats["bot_kacirdi"] += 1
        else:
            stats["bot_korundu"] += 1

    # ── Karşılıklı dersler (kural-bazlı, sayımlardan) ──
    lessons: List[dict] = []

    def _pct(a: int, b: int) -> Optional[int]:
        return round(100 * a / b) if b else None

    agree_wr = _pct(stats["agree_bot_win"], stats["agree_n"])
    if stats["agree_n"] >= 3 and agree_wr is not None:
        lessons.append({"to": "both", "text":
            f"İkisi aynı yönde açtığında bot {stats['agree_n']} işlemde %{agree_wr} kazandı — "
            "mutabakat en güçlü sinyal" + (", bu kesişim öncelikli değerlendirilmeli." if agree_wr >= 55 else
            " değil; mutabakat bile yetmiyor, rejim filtresi gerekli.")})
    if stats["conflict_n"] >= 3:
        bw, dw = stats["conflict_bot_win"], stats["conflict_decider_win"]
        winner = "bot" if bw > dw else ("decider" if dw > bw else "berabere")
        lessons.append({"to": "both", "text":
            f"Zıt yönde açtıkları {stats['conflict_n']} çatışmada bot {bw}, decider {dw} kez haklı çıktı — "
            + ("bot'un momentum kuralları bu dönemde daha isabetli, decider zıt sinyalde temkin artırmalı."
               if winner == "bot" else
               "decider'ın bağlam okuması daha isabetli, bot zıt-decider anlarında boyut küçültmeli."
               if winner == "decider" else "net bir üstün yok.")})
    guard_total = stats["decider_korudu"] + stats["decider_kacirdi"]
    if guard_total >= 5:
        guard_rate = _pct(stats["decider_korudu"], guard_total)
        lessons.append({"to": "bot", "text":
            f"Decider'ın WAIT dediği anlarda bot {guard_total} işlem açtı; bunların {stats['decider_korudu']}'i "
            f"(%{guard_rate}) kayıptı — " + ("decider'ın beklemesi değerli bir fren: bot, WAIT anlarında boyutu "
            "kısmayı denemeli." if (guard_rate or 0) >= 55 else
            f"ama {stats['decider_kacirdi']} kazancı da kaçırırdı; WAIT'i körü körüne fren yapma.")})
    solo_total = stats["bot_kacirdi"] + stats["bot_korundu"]
    if solo_total >= 3:
        miss_rate = _pct(stats["bot_kacirdi"], solo_total)
        lessons.append({"to": "decider", "text":
            f"Decider'ın tek başına açtığı {solo_total} pencerede {stats['bot_kacirdi']} kazanç vardı (%{miss_rate}) — "
            + ("bot bu kurulumları görmüyor; decider'ın kazandığı desenler bot scope'una aday."
               if (miss_rate or 0) >= 55 else
               "çoğu kayıptı; decider bot'un işlem açmadığı sularda daha seçici olmalı.")})
    if not lessons:
        lessons.append({"to": "both", "text":
            "Henüz yeterli örtüşen işlem yok — veri biriktikçe karşılıklı dersler burada belirecek."})

    return {"days": days, "window_hours": _PAIR_WINDOW_H, "stats": stats,
            "lessons": lessons, "recent_pairs": list(reversed(pairs))[:15]}


def get_bot_trades(symbol: str, days: int = 30, host: str = DEFAULT_HOST,
                   limit: int = 40) -> Dict[str, Any]:
    """Tek sembolün son MT5 işlemleri (panelde sembole tıkla → detay)."""
    client = _client()
    since = (_now() - timedelta(days=days)).isoformat()
    res = (client.table("bot_trades")
           .select("ticket,symbol,direction,volume,close_time,close_price,profit,commission,swap,comment")
           .eq("host", host).eq("symbol", symbol).gte("close_time", since)
           .order("close_time", desc=True).limit(limit).execute())
    trades = res.get("data") or []
    for t in trades:
        t["net"] = round((t.get("profit") or 0) + (t.get("commission") or 0) + (t.get("swap") or 0), 2)
    return {"symbol": symbol, "days": days, "trades": trades}


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
