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


# ── Sayfalı çekim ─────────────────────────────────────────────────────────
# ⚠️ PostgREST'in sunucu tarafı `db-max-rows` ayarı 1000'dir; `.limit(5000)`
# yazmak bunu AŞMAZ, istek sessizce 1000 satırda kesilir. 2026-08-26 denetimi:
# `get_decider_stats` 30 gün istediği hâlde `total_decisions` tam 1000
# dönüyordu (yani ~son 12 gün) ve `get_bot_vs_decider` ARTAN sıralamayla
# çektiği için elindeki 1000 satır en ESKİ günlerdi → panel "14 gün öncesi"
# gösteriyordu. Tüm çok-satırlı okumalar artık bu yardımcıdan geçer.
PAGE_SIZE = 1000


def _fetch_paged(table: str, select: str, *, order: str, desc: bool = True,
                 cap: int = 8000, **eq_gte) -> List[dict]:
    """Bir tabloyu sayfa sayfa çek — PostgREST 1000-satır tavanını aşar.

    Args:
        table: tablo adı.
        select: PostgREST select ifadesi.
        order: sıralama kolonu (sayfalama determinizmi için ZORUNLU).
        desc: True → en yeni önce (panel her zaman en tazeyi ister).
        cap: en fazla kaç satır (koruma).
        **eq_gte: `eq__<kolon>` ve `gte__<kolon>` biçiminde filtreler.

    Returns:
        Satır listesi (sıralama korunur).
    """
    client = _client()
    rows: List[dict] = []
    for start in range(0, cap, PAGE_SIZE):
        q = client.table(table).select(select)
        for key, value in eq_gte.items():
            if value is None:
                continue
            if key.startswith("eq__"):
                q = q.eq(key[4:], value)
            elif key.startswith("gte__"):
                q = q.gte(key[5:], value)
        chunk = (q.order(order, desc=desc)
                 .range(start, start + PAGE_SIZE - 1).execute()).get("data") or []
        rows.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            break
    return rows


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

    meta = (heartbeat or {}).get("meta") or {}
    # Ajan "çevrimiçi" olması işlem senkronunun çalıştığı anlamına GELMEZ:
    # 2026-08-18→26 arasında kalp atışı düzgün akarken bot_trades donmuştu
    # (MT5 bağlantısı düşmüş, push_trades sessizce 0 dönüyordu). Ajan 1.1'den
    # itibaren senkron sağlığını kalp atışına yazıyor; panel bunu ayrı gösterir.
    trade_sync = {
        "ok": meta.get("trade_sync_ok"),
        "last_push": meta.get("trade_sync_last_push"),
        "error": meta.get("trade_sync_error"),
        "fail_streak": meta.get("trade_sync_fail_streak") or 0,
        # Eski ajan sürümü bu alanları hiç yazmaz → "bilinmiyor" (uyarı basma).
        "reported": meta.get("trade_sync_ok") is not None,
    }

    return {
        "host": host,
        "online": online,
        "last_seen": heartbeat.get("last_seen") if heartbeat else None,
        "last_seen_ago_s": last_seen_ago_s,
        "meta": meta,
        "trade_sync": trade_sync,
        "pending_commands": pending,
        "running_commands": running,
        "recent_commands": commands,
    }


# ── Bot & Decider performansı ─────────────────────────────────────────────

def get_bot_performance(days: int = 30, host: str = DEFAULT_HOST) -> Dict[str, Any]:
    """bot_trades'ten sembol kırılımlı WR + toplam kâr (gerçek MT5 sonuçları)."""
    since = (_now() - timedelta(days=days)).isoformat()
    trades = _fetch_paged(
        "bot_trades", "symbol,profit,commission,swap,close_time,comment",
        order="close_time", desc=True, eq__host=host, gte__close_time=since)

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
        # Tazelik denetimi (2026-08-26): ajan canlı görünürken bot_trades
        # senkronu sessizce durabiliyor (vaka: 2026-08-18'den 26'sına kadar
        # tek satır yazılmadı, panel hiçbir uyarı vermedi). Panel artık
        # verinin YAŞINI gösterir — "sessiz bayat veri" bir daha olmasın.
        "data_age_hours": _data_age_hours(trades[0].get("close_time") if trades else None),
    }


#: bot_trades bu saatten eski ise panel "bayat" uyarısı basar. Bot hafta sonu
#: işlem yapmaz; 3 gün eşiği normal hafta sonunu (Cuma 22:00 → Pazartesi 00:00)
#: yanlış alarma çevirmez ama gerçek bir senkron kesintisini yakalar.
TRADE_STALE_HOURS = 72


def _data_age_hours(last_iso: Optional[str]) -> Optional[float]:
    """Son işlemin üstünden kaç saat geçti (None = hiç işlem yok)."""
    ts = _parse_ts(last_iso)
    if ts is None:
        return None
    return round((_now() - ts).total_seconds() / 3600, 1)


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
    since = (_now() - timedelta(days=days)).isoformat()
    rows = _fetch_paged("decider_journal", "decision,outcome,ts,symbol",
                        order="ts", desc=True, eq__host=host, gte__ts=since)

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
    since = (_now() - timedelta(days=days)).isoformat()
    rows = _fetch_paged("decider_journal", "decision,outcome,ts,symbol",
                        order="ts", desc=True, eq__host=host, gte__ts=since)

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


# ── Sembol derinlemesine geçmiş (gün × yön) ───────────────────────────────

# Seans etiketleri iki motorda farklı yazılıyor (klasik decider Türkçe,
# gold_brain İngilizce) — panelde tek dil görünsün diye normalize edilir.
_SESSION_TR = {
    "ASIA": "Asya", "ASYA": "Asya",
    "LONDON": "Londra", "LONDRA": "Londra",
    "NY": "NY", "NEWYORK": "NY", "NEW_YORK": "NY",
    "CLOSE": "kapanış", "KAPANIŞ": "kapanış", "KAPANIS": "kapanış",
}


def _session_label(raw_session: Optional[str], ts: Optional[datetime]) -> str:
    """Seans etiketi; kayıtta yoksa UTC saatinden türetilir (eski satırlar)."""
    if raw_session:
        return _SESSION_TR.get(str(raw_session).strip().upper(), str(raw_session))
    if not ts:
        return "?"
    h = ts.astimezone(timezone.utc).hour
    if h < 7:
        return "Asya"
    if h < 13:
        return "Londra"
    if h < 21:
        return "NY"
    return "kapanış"


# Karar listesi kotalari - panel "gun gun her islem" gezinmesi icin OPEN'lar
# genis tutulur; WAIT'ler yalnizca baglam icin ornekleme alinir.
OPEN_DECISION_QUOTA = 500
WAIT_DECISION_QUOTA = 150


def _round(v: Optional[float], digits: int) -> Optional[float]:
    """None-guvenli yuvarlama - jsonb alanlari sik sik bos gelir."""
    return round(v, digits) if v is not None else None


def _fnum(v: Any) -> Optional[float]:
    """jsonb->>text alanları string döner; sayıya çevir, çöpse None."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _new_bucket() -> Dict[str, Any]:
    return {"opens": 0, "wins": 0, "losses": 0, "pending": 0, "net_r": 0.0}


def _close_bucket(b: Dict[str, Any]) -> Dict[str, Any]:
    resolved = b["wins"] + b["losses"]
    b["resolved"] = resolved
    b["win_rate"] = round(100 * b["wins"] / resolved, 1) if resolved else None
    b["net_r"] = round(b["net_r"], 2)
    b["avg_r"] = round(b["net_r"] / resolved, 3) if resolved else None
    return b


def get_decider_symbol_history(symbol: str, days: int = 30,
                               host: str = DEFAULT_HOST) -> Dict[str, Any]:
    """Bir sembolün decider geçmişi — GÜN bazlı ve YÖN bazlı kırılım.

    Neden ayrı bir uç: karne kartındaki tek WR sayısı yanıltıcı. Kararların
    RR'ı ~0.67 olduğundan başabaş WR ≈ %60 — yani %57 WR bile NET KAYIP'tır.
    Bu yüzden her kırılımda WR'ın yanına **net R** ve başabaş çıtası konur.

    Ek olarak WAIT kararlarının karşı-olgusu (cf_pnl_r) "kaçırılan/elenen"
    olarak yön bazında toplanır: aşırı temkin de ölçülebilir bir maliyettir.
    """
    since = (_now() - timedelta(days=days)).isoformat()
    # TP/SL detay takibi (2026-08-26): seviyelerin yanina gerceklesen yol da
    # cekilir - mfe_r/mae_r (en iyi/en kotu nokta), tp_progress (hedefin yuzde
    # kacina gidildi), maliyet-sonrasi net R ve cozulme ani. "Hangi gun hangi
    # islemde ne kadar TP/SL yapmis" ancak bu alanlarla cevaplanabilir.
    sel = ("ts,outcome,"
           "pnl_r:raw->>pnl_r,pnl_r_net:raw->>pnl_r_net,cost_usd:raw->>cost_usd,"
           "cf_pnl_r:raw->>cf_pnl_r,cf_outcome:raw->>cf_outcome,"
           "action:raw->decision->>action,direction:raw->decision->>direction,"
           "reason:raw->decision->>reason,size_factor:raw->decision->>size_factor,"
           "management:raw->decision->>management,"
           "cf_dir:raw->counterfactual->>dir,"
           "session:raw->context->>session,gb_session:raw->gb_context->>session,"
           "entry:raw->trade->>entry_price,sl:raw->trade->>sl,tp:raw->trade->>tp,"
           "rr:raw->trade->>rr,atr:raw->trade->>atr,spread:raw->trade->>spread,"
           "mfe_r:raw->path->>mfe_r,mae_r:raw->path->>mae_r,"
           "tp_progress:raw->path->>tp_progress,bars:raw->path->>bars_to_outcome,"
           "outcome_at:raw->>outcome_at,shadow_model:raw->>shadow_model,"
           "cf_rr:raw->counterfactual->>rr,mode:raw->>mode")
    rows = _fetch_paged("decider_journal", sel, order="ts", desc=True, cap=6000,
                        eq__host=host, eq__symbol=symbol, gte__ts=since)

    summary = _new_bucket()
    summary.update({"waits": 0, "foregone_r": 0.0, "missed_wins": 0})
    by_day: Dict[str, Dict[str, Any]] = {}
    by_dir: Dict[str, Dict[str, Any]] = {}
    decisions: List[dict] = []
    rr_seen: List[float] = []

    for r in rows:
        ts = _parse_ts(r.get("ts"))
        action = str(r.get("action") or "").upper()
        direction = (str(r.get("direction")).upper() if r.get("direction") else None)
        outcome = (str(r.get("outcome")).upper() if isinstance(r.get("outcome"), str) else None)
        pnl_r = _fnum(r.get("pnl_r"))
        cf_r = _fnum(r.get("cf_pnl_r"))
        cf_dir = (str(r.get("cf_dir")).upper() if r.get("cf_dir") else None)
        rr = _fnum(r.get("rr")) or _fnum(r.get("cf_rr"))
        if rr:
            rr_seen.append(rr)
        day = ts.astimezone(timezone.utc).strftime("%Y-%m-%d") if ts else "?"
        session = _session_label(r.get("session") or r.get("gb_session"), ts)

        d = by_day.setdefault(day, {"day": day, "waits": 0, "foregone_r": 0.0,
                                    **_new_bucket(),
                                    "BUY": _new_bucket(), "SELL": _new_bucket()})

        if action == "OPEN" and direction in ("BUY", "SELL"):
            dd = by_dir.setdefault(direction, {
                **_new_bucket(), "missed": {"n": 0, "wins": 0, "r": 0.0},
                "by_session": {}, "by_hour": {}, "size_sum": 0.0, "size_n": 0,
            })
            sess = dd["by_session"].setdefault(session, _new_bucket())
            hour = ts.astimezone(timezone.utc).hour if ts else -1
            hr = dd["by_hour"].setdefault(hour, _new_bucket())
            size = _fnum(r.get("size_factor"))
            if size is not None:
                dd["size_sum"] += size
                dd["size_n"] += 1
            for b in (summary, d, d[direction], dd, sess, hr):
                b["opens"] += 1
                if outcome == "WIN":
                    b["wins"] += 1
                elif outcome == "LOSS":
                    b["losses"] += 1
                else:
                    b["pending"] += 1
                if pnl_r is not None and outcome in ("WIN", "LOSS"):
                    b["net_r"] += pnl_r
        elif action == "WAIT":
            summary["waits"] += 1
            d["waits"] += 1
            if cf_r is not None and str(r.get("cf_outcome") or "").upper() in ("WIN", "LOSS"):
                summary["foregone_r"] += cf_r
                d["foregone_r"] += cf_r
                if cf_r > 0:
                    summary["missed_wins"] += 1
                if cf_dir in ("BUY", "SELL"):
                    dd = by_dir.setdefault(cf_dir, {
                        **_new_bucket(), "missed": {"n": 0, "wins": 0, "r": 0.0},
                        "by_session": {}, "by_hour": {}, "size_sum": 0.0, "size_n": 0,
                    })
                    dd["missed"]["n"] += 1
                    dd["missed"]["r"] += cf_r
                    if cf_r > 0:
                        dd["missed"]["wins"] += 1

        # Liste kotasi tur bazinda: XAU gibi cok bekleyen sembollerde tek havuz
        # kullanilsaydi son satirlarin hepsi WAIT olur, "islemler" sekmesi bos
        # kalirdi. OPEN'lara ayri (ve genis) kota verilir - kullanici gun gun
        # her islemi gezebilmeli.
        quota = OPEN_DECISION_QUOTA if action == "OPEN" else WAIT_DECISION_QUOTA
        if sum(1 for x in decisions if (x["action"] == "OPEN") == (action == "OPEN")) < quota:
            entry_p, sl_p, tp_p = _fnum(r.get("entry")), _fnum(r.get("sl")), _fnum(r.get("tp"))
            decisions.append({
                "ts": r.get("ts"), "day": day, "session": session,
                "action": action or "?", "direction": direction,
                "outcome": outcome if outcome in ("WIN", "LOSS") else None,
                "r": round(pnl_r, 3) if pnl_r is not None and outcome in ("WIN", "LOSS") else None,
                "r_net": _round(_fnum(r.get("pnl_r_net")), 3),
                "cost_usd": _round(_fnum(r.get("cost_usd")), 2),
                "cf_direction": cf_dir,
                "cf_outcome": str(r.get("cf_outcome")).upper() if r.get("cf_outcome") else None,
                "cf_r": round(cf_r, 3) if cf_r is not None else None,
                "size_factor": _fnum(r.get("size_factor")),
                "entry": entry_p, "sl": sl_p, "tp": tp_p,
                # Seviyelerin fiyat cinsinden UZAKLIGI: "ne kadar TP / ne kadar
                # SL" sorusunun dogrudan cevabi (R degil, puan olarak).
                "tp_distance": _round(abs(tp_p - entry_p), 2) if (tp_p and entry_p) else None,
                "sl_distance": _round(abs(entry_p - sl_p), 2) if (sl_p and entry_p) else None,
                # Gerceklesen cikis fiyati: WIN -> TP, LOSS -> SL (decider
                # geometrisi sabit hedeflidir; ara cikis exit_policy ile gelir).
                "exit_price": (tp_p if outcome == "WIN" else sl_p if outcome == "LOSS" else None),
                "mfe_r": _round(_fnum(r.get("mfe_r")), 2),
                "mae_r": _round(_fnum(r.get("mae_r")), 2),
                "tp_progress": _round(_fnum(r.get("tp_progress")), 2),
                "bars_to_outcome": _fnum(r.get("bars")),
                "outcome_at": r.get("outcome_at"),
                "atr": _round(_fnum(r.get("atr")), 2),
                "spread": _round(_fnum(r.get("spread")), 2),
                "rr": rr, "mode": r.get("mode"),
                "shadow_model": r.get("shadow_model"),
                "management": str(r.get("management") or "")[:300],
                "reason": str(r.get("reason") or "")[:600],
            })

    # Başabaş WR = 1/(1+RR) — kararların tipik RR'ından. WR bunun altındaysa
    # "yüksek isabet" bile net kayıptır; panelin en kritik çizgisi budur.
    rr_typ = round(sorted(rr_seen)[len(rr_seen) // 2], 3) if rr_seen else None
    breakeven_wr = round(100 / (1 + rr_typ), 1) if rr_typ else None

    for dd in by_dir.values():
        dd["avg_size"] = round(dd["size_sum"] / dd["size_n"], 2) if dd["size_n"] else None
        dd.pop("size_sum", None)
        dd.pop("size_n", None)
        dd["missed"]["r"] = round(dd["missed"]["r"], 2)
        dd["by_session"] = {k: _close_bucket(v) for k, v in
                            sorted(dd["by_session"].items(), key=lambda kv: -kv[1]["opens"])}
        dd["by_hour"] = [{"hour": h, **_close_bucket(v)}
                         for h, v in sorted(dd["by_hour"].items()) if h >= 0]
        _close_bucket(dd)

    days_list = []
    for day in sorted(by_day, reverse=True):
        d = by_day[day]
        d["foregone_r"] = round(d["foregone_r"], 2)
        d["BUY"] = _close_bucket(d["BUY"])
        d["SELL"] = _close_bucket(d["SELL"])
        days_list.append(_close_bucket(d))

    graded = [d for d in days_list if d["resolved"] > 0]
    best = max(graded, key=lambda d: d["net_r"], default=None)
    worst = min(graded, key=lambda d: d["net_r"], default=None)
    summary["foregone_r"] = round(summary["foregone_r"], 2)
    _close_bucket(summary)
    summary.update({
        "rr_typical": rr_typ,
        "breakeven_wr": breakeven_wr,
        # WR başabaşın üstünde mi? Panelin "kâr ediyor mu" cevabı.
        "above_breakeven": (summary["win_rate"] is not None and breakeven_wr is not None
                            and summary["win_rate"] >= breakeven_wr),
        "active_days": len(graded),
        "best_day": {"day": best["day"], "net_r": best["net_r"]} if best else None,
        "worst_day": {"day": worst["day"], "net_r": worst["net_r"]} if worst else None,
        "first_ts": rows[-1].get("ts") if rows else None,
        "last_ts": rows[0].get("ts") if rows else None,
    })

    return {
        "symbol": symbol, "days": days, "total_rows": len(rows),
        "summary": summary,
        "by_day": days_list,
        "by_direction": by_dir,
        "decisions": decisions,
    }


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
    since = (_now() - timedelta(days=days)).isoformat()

    # ⚠️ Eskiden `.order("close_time").limit(3000)` idi: PostgREST 1000'de
    # kestiği için elde kalan EN ESKİ 1000 satırdı ve eşleştirme hep geçmişe
    # bakıyordu (panelde "14 gün öncesi"). Artık en yeniden başlayıp sayfalanır.
    trades = _fetch_paged(
        "bot_trades", "ticket,symbol,direction,close_time,profit,commission,swap",
        order="close_time", desc=True, eq__host=host, gte__close_time=since)
    trades.reverse()   # eşleştirme kronolojik ilerler
    for t in trades:
        t["net"] = (t.get("profit") or 0) + (t.get("commission") or 0) + (t.get("swap") or 0)
        t["nsym"] = _BOT_SYMBOL_MAP.get(t.get("symbol") or "", t.get("symbol"))
        t["t"] = _parse_ts(t.get("close_time"))

    jrows = _fetch_paged("decider_journal", "decision,outcome,ts,symbol",
                         order="ts", desc=True, eq__host=host, gte__ts=since)
    jrows.reverse()
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
    since = (_now() - timedelta(days=days)).isoformat()
    trades = _fetch_paged(
        "bot_trades",
        "ticket,symbol,direction,volume,close_time,close_price,profit,commission,swap,comment",
        order="close_time", desc=True, cap=max(limit, PAGE_SIZE),
        eq__host=host, eq__symbol=symbol, gte__close_time=since)[:limit]
    for t in trades:
        t["net"] = round((t.get("profit") or 0) + (t.get("commission") or 0) + (t.get("swap") or 0), 2)
    return {"symbol": symbol, "days": days, "trades": trades}


# ── Sembol derinlemesine geçmiş — BOT (MT5 gerçek işlemler) ─────────────────
# Decider'daki "gün & yön geçmişi" panelinin bot işlemleri için karşılığı.
# 2026-08-27'den ÖNCE bot_trades yalnız ÇIKIŞ bilgisini taşıyordu (giriş
# fiyatı/SL/TP hiç yazılmıyordu) — bu satırlar için giriş/R/TP-SL alanları
# None döner (frontend eksik veriyi zaten zarifçe gösterir). O tarihten
# sonraki her satırda evolution_agent._lookup_entry ile dolduruluyor.

#: MT5 DEAL_REASON sabitleri (yalnız ilgilendiğimiz ikisi + haritalama).
_MT5_REASON_TP = 5
_MT5_REASON_SL = 4


def _new_bot_bucket() -> Dict[str, Any]:
    return {"n": 0, "wins": 0, "losses": 0, "tp_hits": 0, "sl_hits": 0,
            "net": 0.0, "r_sum": 0.0, "r_n": 0}


def _close_bot_bucket(b: Dict[str, Any]) -> Dict[str, Any]:
    b["win_rate"] = round(100 * b["wins"] / b["n"], 1) if b["n"] else None
    b["net"] = round(b["net"], 2)
    b["avg_net"] = round(b["net"] / b["n"], 2) if b["n"] else None
    b["avg_r"] = round(b["r_sum"] / b["r_n"], 3) if b["r_n"] else None
    b.pop("r_sum", None)
    b.pop("r_n", None)
    return b


def _bot_trade_r(direction: str, open_price: Optional[float], close_price: Optional[float],
                 sl: Optional[float]) -> Optional[float]:
    """Gerçekleşen fiyat hareketi / PLANLANAN stop mesafesi.

    Sembol-agnostik: pip dönüşümü gerekmez, hepsi aynı fiyat biriminde.
    Stop mesafesi yoksa (eski satır ya da SL'siz işlem) None — beklentiye
    KATILMAZ, satır yine de listede görünür.
    """
    if open_price is None or close_price is None or sl is None:
        return None
    if direction == "BUY":
        risk = open_price - sl
        move = close_price - open_price
    elif direction == "SELL":
        risk = sl - open_price
        move = open_price - close_price
    else:
        return None
    if not risk or risk <= 0:
        return None
    return round(move / risk, 4)


def get_bot_symbol_history(symbol: str, days: int = 30,
                           host: str = DEFAULT_HOST) -> Dict[str, Any]:
    """Bir sembolün BOT geçmişi — decider'ınkiyle aynı gün/yön/işlem-defteri şekli.

    WR tek başına yanıltıcıdır (bkz. services/signal_metrics.py doktrini) —
    bu yüzden RR planlı SL/TP'den hesaplanır ve başabaş çıta + net R her
    zaman WR'ın yanında döner.
    """
    since = (_now() - timedelta(days=days)).isoformat()
    rows = _fetch_paged(
        "bot_trades",
        "ticket,direction,volume,open_time,open_price,close_time,close_price,"
        "sl,tp,profit,commission,swap,comment,raw",
        order="close_time", desc=True, cap=4000,
        eq__host=host, eq__symbol=symbol, gte__close_time=since)

    summary = _new_bot_bucket()
    by_day: Dict[str, Dict[str, Any]] = {}
    by_dir: Dict[str, Dict[str, Any]] = {}
    decisions: List[dict] = []
    rr_seen: List[float] = []

    for r in rows:
        ts = _parse_ts(r.get("close_time"))
        direction = (r.get("direction") or "").upper()
        open_price = _fnum(r.get("open_price"))
        close_price = _fnum(r.get("close_price"))
        sl = _fnum(r.get("sl"))
        tp = _fnum(r.get("tp"))
        net = round((r.get("profit") or 0) + (r.get("commission") or 0) + (r.get("swap") or 0), 2)
        win = net > 0
        reason = ((r.get("raw") or {}).get("reason")
                  if isinstance(r.get("raw"), dict) else None)
        exit_label = ("TP" if reason == _MT5_REASON_TP
                      else "SL" if reason == _MT5_REASON_SL else "manuel")
        r_mult = _bot_trade_r(direction, open_price, close_price, sl)

        # Planlanan RR (geometriden — sonuçtan bağımsız): TP/SL ikisi de
        # varsa aynı mantık, sinyal tarafındaki _geometry_rr ile simetrik.
        if open_price is not None and sl is not None and tp is not None:
            risk = abs(open_price - sl)
            reward = abs(tp - open_price)
            if risk > 0:
                rr_seen.append(reward / risk)

        day = ts.astimezone(timezone.utc).strftime("%Y-%m-%d") if ts else "?"
        session = _session_label(None, ts)

        d = by_day.setdefault(day, {"day": day, **_new_bot_bucket(),
                                    "BUY": _new_bot_bucket(), "SELL": _new_bot_bucket()})
        dd = by_dir.setdefault(direction or "?", {
            **_new_bot_bucket(), "by_session": {}, "by_hour": {},
        })
        sess = dd["by_session"].setdefault(session, _new_bot_bucket())
        hour = ts.astimezone(timezone.utc).hour if ts else -1
        hr = dd["by_hour"].setdefault(hour, _new_bot_bucket())

        targets = [summary, d]
        if direction in ("BUY", "SELL"):
            targets.append(d[direction])
        targets += [dd, sess, hr]
        for b in targets:
            b["n"] += 1
            b["net"] += net
            if win:
                b["wins"] += 1
            else:
                b["losses"] += 1
            if exit_label == "TP":
                b["tp_hits"] += 1
            elif exit_label == "SL":
                b["sl_hits"] += 1
            if r_mult is not None:
                b["r_sum"] += r_mult
                b["r_n"] += 1

        if len(decisions) < 300:
            decisions.append({
                "ts": r.get("close_time"), "day": day, "session": session,
                "direction": direction or None,
                "entry": open_price, "exit": close_price, "sl": sl, "tp": tp,
                "r": r_mult, "net": net, "win": win, "exit_reason": exit_label,
                "volume": _fnum(r.get("volume")),
                "commission": _fnum(r.get("commission")),
                "swap": _fnum(r.get("swap")),
                "comment": r.get("comment"),
            })

    rr_typ = round(sorted(rr_seen)[len(rr_seen) // 2], 3) if rr_seen else None
    breakeven_wr = round(100 / (1 + rr_typ), 1) if rr_typ else None

    for dd in by_dir.values():
        dd["by_session"] = {k: _close_bot_bucket(v) for k, v in
                            sorted(dd["by_session"].items(), key=lambda kv: -kv[1]["n"])}
        dd["by_hour"] = [{"hour": h, **_close_bot_bucket(v)}
                         for h, v in sorted(dd["by_hour"].items()) if h >= 0]
        _close_bot_bucket(dd)

    days_list = []
    for day in sorted(by_day, reverse=True):
        d = by_day[day]
        d["BUY"] = _close_bot_bucket(d["BUY"])
        d["SELL"] = _close_bot_bucket(d["SELL"])
        days_list.append(_close_bot_bucket(d))

    graded = [d for d in days_list if d["n"] > 0]
    best = max(graded, key=lambda d: d["net"], default=None)
    worst = min(graded, key=lambda d: d["net"], default=None)
    _close_bot_bucket(summary)
    summary.update({
        "rr_typical": rr_typ,
        "breakeven_wr": breakeven_wr,
        "above_breakeven": (summary["win_rate"] is not None and breakeven_wr is not None
                            and summary["win_rate"] >= breakeven_wr),
        "active_days": len(graded),
        "best_day": {"day": best["day"], "net": best["net"]} if best else None,
        "worst_day": {"day": worst["day"], "net": worst["net"]} if worst else None,
        "first_ts": rows[-1].get("close_time") if rows else None,
        "last_ts": rows[0].get("close_time") if rows else None,
        "with_geometry": sum(1 for x in decisions if x["r"] is not None),
    })

    return {
        "symbol": symbol, "days": days, "total_rows": len(rows),
        "summary": summary,
        "by_day": days_list,
        "by_direction": by_dir,
        "decisions": decisions,
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
