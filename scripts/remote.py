#!/usr/bin/env python3
"""remote.py — Panel (Mac) → MT5 kutusu kumandası.

Kutudaki evolution_agent'a komut kuyruğu üzerinden iş verir ve çıktıyı
canlı izler. Ajanın `claude_task` handler'ı sayesinde kutuda Claude Code'u
headless çalıştırıp sonucunu buraya getirebilir — iki Claude arasında
yapılandırılmış iş devri.

Kullanım:
  python3 scripts/remote.py ask "botun son 2 saatteki TREND KAPISI satırlarını say"
  python3 scripts/remote.py ask "..." --model opus --timeout 1800 --cwd "yeni deneme"
  python3 scripts/remote.py sh  "git log --oneline -5"        # kabuk komutu
  python3 scripts/remote.py pull                               # git pull
  python3 scripts/remote.py restart decider                    # süreç yenile
  python3 scripts/remote.py status                             # son komutlar
  python3 scripts/remote.py watch <id>                         # tekrar izle
  python3 scripts/remote.py health                             # ajan kalp atışı

Bayraklar: --no-wait (kuyruğa bırak, bekleme) · --host <ad> · --json

Ortam: SUPABASE_URL + SUPABASE_SERVICE_KEY (backend/.env'den okunur).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST = os.getenv("MT5_AGENT_HOST", "mt5_box")
POLL_SECONDS = 3
RESULT_BEGIN = "=== SONUÇ ==="
RESULT_END = "=== BITTI ==="


def _key_from_bot_config(url: str | None) -> tuple[str | None, str | None]:
    """Bot config'inden service-role anahtarını oku (import etmeden, regex)."""
    import re
    path = ROOT / "yeni deneme" / "config.py"
    if not path.exists():
        return None, url
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None, url
    m = re.search(r'SUPABASE_SERVICE_KEY\s*=\s*["\']([^"\']+)["\']', text)
    u = re.search(r'SUPABASE_URL\s*=\s*["\']([^"\']+)["\']', text)
    return (m.group(1) if m else None), (url or (u.group(1) if u else None))


def _client():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / "backend" / ".env")
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not key:
        # evolution_commands/agent_heartbeat RLS kilitli → service-role şart.
        # Bot config'i (gitignore'da, yerelde var) yedek kaynak.
        key, url = _key_from_bot_config(url)
    if not key:
        key = os.getenv("SUPABASE_KEY")     # son çare: anon (çoğu tablo görünmez)
    if not url or not key:
        sys.exit("HATA: SUPABASE_URL / SUPABASE_SERVICE_KEY bulunamadı "
                 "(backend/.env veya 'yeni deneme/config.py')")
    try:
        from supabase import create_client
    except ImportError:
        sys.exit("HATA: pip install supabase")
    return create_client(url, key)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def submit(client, host: str, kind: str, payload: dict, name: str) -> str:
    row = {"host": host, "kind": kind, "payload": payload, "status": "pending",
           "requested_by": "panel_claude", "analysis_id": kind,
           "analysis_name": name, "created_at": _now()}
    res = client.table("evolution_commands").insert(row).execute()
    return res.data[0]["id"]


def extract_result(output: str) -> str | None:
    """Ajan protokolündeki === SONUÇ === bloğunu ayıkla."""
    if not output or RESULT_BEGIN not in output:
        return None
    tail = output.split(RESULT_BEGIN, 1)[1]
    return tail.split(RESULT_END, 1)[0].strip() if RESULT_END in tail else tail.strip()


def watch(client, cmd_id: str, quiet: bool = False) -> dict:
    """Komutu bitene kadar izle; yeni çıktıyı akışkan yazdır."""
    seen = 0
    spinner = "|/-\\"
    tick = 0
    while True:
        res = (client.table("evolution_commands").select("*")
               .eq("id", cmd_id).limit(1).execute())
        if not res.data:
            sys.exit(f"komut bulunamadı: {cmd_id}")
        cmd = res.data[0]
        out = cmd.get("output") or ""
        if len(out) > seen and not quiet:
            sys.stdout.write(out[seen:])
            sys.stdout.flush()
        seen = max(seen, len(out))
        if cmd["status"] in ("done", "failed", "timeout"):
            if not quiet:
                print(f"\n── {cmd['status'].upper()} (rc={cmd.get('return_code')}) ──")
            return cmd
        if not quiet and cmd["status"] == "pending":
            tick += 1
            sys.stdout.write(f"\r[kuyrukta… {spinner[tick % 4]}] ")
            sys.stdout.flush()
        time.sleep(POLL_SECONDS)


def cmd_ask(client, a) -> None:
    payload = {"prompt": a.text, "timeout": a.timeout, "model": a.model}
    if a.cwd:
        payload["cwd"] = a.cwd
    if a.raw:
        payload["raw"] = True
    cid = submit(client, a.host, "claude_task", payload,
                 f"Claude görevi: {a.text[:60]}")
    print(f"[panel] görev gönderildi → {cid}")
    if a.no_wait:
        return
    cmd = watch(client, cid, quiet=a.json_out)
    result = extract_result(cmd.get("output") or "")
    if a.json_out:
        print(json.dumps({"id": cid, "status": cmd["status"],
                          "return_code": cmd.get("return_code"),
                          "result": result, "output": cmd.get("output")},
                         ensure_ascii=False, indent=1))
    elif result:
        print("\n╭─ KUTUNUN SONUCU ─────────────────────────")
        for line in result.splitlines():
            print(f"│ {line}")
        print("╰──────────────────────────────────────────")


def cmd_sh(client, a) -> None:
    payload = {"command": a.text, "timeout": a.timeout}
    if a.cwd:
        payload["cwd"] = a.cwd
    cid = submit(client, a.host, "run_analysis", payload, f"Kabuk: {a.text[:60]}")
    print(f"[panel] komut gönderildi → {cid}")
    if not a.no_wait:
        watch(client, cid)


def cmd_pull(client, a) -> None:
    cid = submit(client, a.host, "git_pull", {}, "git pull")
    print(f"[panel] git pull → {cid}")
    watch(client, cid)


def cmd_restart(client, a) -> None:
    payload = {"target": a.target}
    if a.force:
        payload["force"] = True
    cid = submit(client, a.host, "restart_process", payload, f"restart {a.target}")
    print(f"[panel] restart {a.target} → {cid}")
    watch(client, cid)


def cmd_status(client, a) -> None:
    res = (client.table("evolution_commands")
           .select("id,kind,status,analysis_name,created_at,finished_at,return_code")
           .eq("host", a.host).order("created_at", desc=True).limit(a.limit).execute())
    rows = res.data or []
    if not rows:
        print("kayıt yok")
        return
    print(f"{'zaman':<17}{'tür':<14}{'durum':<9}{'rc':>4}  ad")
    for r in rows:
        t = (r["created_at"] or "")[5:16].replace("T", " ")
        print(f"{t:<17}{r['kind']:<14}{r['status']:<9}"
              f"{str(r.get('return_code') or ''):>4}  {(r.get('analysis_name') or '')[:52]}")
        if a.ids:
            print(f"{'':<17}id={r['id']}")


def cmd_watch(client, a) -> None:
    watch(client, a.id)


def cmd_health(client, a) -> None:
    res = (client.table("agent_heartbeat").select("*")
           .order("last_seen", desc=True).limit(5).execute())
    rows = res.data or []
    if not rows:
        print("kalp atışı kaydı yok")
        return
    for r in rows:
        ts = r.get("last_seen") or ""
        mins = None
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            mins = (datetime.now(timezone.utc) - dt).total_seconds() / 60
        except Exception:
            pass
        mark = "🟢" if mins is not None and mins < 10 else "🔴"
        age = f"{mins:.0f} dk önce" if mins is not None else "?"
        meta = r.get("meta") or {}
        extra = " ".join(f"{k}={v}" for k, v in meta.items()) if isinstance(meta, dict) else ""
        print(f"{mark} {r.get('host'):<10} {ts[:19]}  ({age})  {extra}")


def main() -> None:
    ap = argparse.ArgumentParser(description="MT5 kutusu kumandası")
    ap.add_argument("--host", default=DEFAULT_HOST)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ask", help="kutudaki Claude Code'a görev ver")
    p.add_argument("text")
    p.add_argument("--model", default="sonnet")
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--cwd", default=None)
    p.add_argument("--raw", action="store_true", help="protokol başlığı ekleme")
    p.add_argument("--no-wait", action="store_true")
    p.add_argument("--json", dest="json_out", action="store_true")
    p.set_defaults(fn=cmd_ask)

    p = sub.add_parser("sh", help="kabuk komutu çalıştır")
    p.add_argument("text")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--cwd", default=None)
    p.add_argument("--no-wait", action="store_true")
    p.set_defaults(fn=cmd_sh)

    p = sub.add_parser("pull"); p.set_defaults(fn=cmd_pull)

    p = sub.add_parser("restart", help="süreç yenile")
    p.add_argument("target", choices=["decider", "bot", "backend", "agent"])
    p.add_argument("--force", action="store_true", help="bot: açık pozisyon beklemeden")
    p.set_defaults(fn=cmd_restart)

    p = sub.add_parser("status")
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--ids", action="store_true")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("watch"); p.add_argument("id"); p.set_defaults(fn=cmd_watch)
    p = sub.add_parser("health"); p.set_defaults(fn=cmd_health)

    a = ap.parse_args()
    a.fn(_client(), a)


if __name__ == "__main__":
    main()
