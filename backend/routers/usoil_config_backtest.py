"""
USOIL config A/B backtest — eski vs yeni TP/SL ile aynı sinyalleri walk-forward
simüle eder. 1m bar replay, gerçekçi outcome ölçümü.

Eski: TP1=0.02% TP2=0.04% TP3=0.06% TP4=0.10% SL=0.05%
Yeni: TP1=0.10% TP2=0.20% TP3=0.35% TP4=0.50% SL=0.30%

Karşılaştırma:
  - Eski WR / Yeni WR
  - Eski expectancy / Yeni expectancy
  - Spread sonrası net / trade
  - Hangi TP daha çok hit
  - Toplam realized pips (gross + net spread)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/usoil-config-bt", tags=["USOIL Config Backtest"])

_STATUS: dict = {"running": False, "started_at": None, "finished_at": None,
                  "result": None, "error": None}


# Config'ler
OLD_CONFIG = {
    "TP1": 0.02, "TP2": 0.04, "TP3": 0.06, "TP4": 0.10,
    "SL": 0.05, "spread": 0.03,
}
NEW_CONFIG = {
    "TP1": 0.10, "TP2": 0.20, "TP3": 0.35, "TP4": 0.50,
    "SL": 0.30, "spread": 0.03,
}


def _simulate_walk(bars_after: list[dict], direction: str, entry: float,
                    cfg: dict) -> dict:
    """Tek sinyalin 1m bar'ları üzerinde walk → first-hit. Hangi TP veya SL?"""
    if not bars_after:
        return {"status": "no_bars"}
    tp_levels = {}
    sl_dist = entry * cfg["SL"] / 100
    if direction == "BUY":
        for tp_name in ("TP1", "TP2", "TP3", "TP4"):
            tp_levels[tp_name] = entry * (1 + cfg[tp_name] / 100)
        sl = entry - sl_dist
    else:
        for tp_name in ("TP1", "TP2", "TP3", "TP4"):
            tp_levels[tp_name] = entry * (1 - cfg[tp_name] / 100)
        sl = entry + sl_dist

    for i, b in enumerate(bars_after):
        h = float(b.get("high") or 0)
        l = float(b.get("low") or 0)
        o = float(b.get("open") or 0)
        c = float(b.get("close") or 0)
        bullish = c >= o

        # SL hit?
        if direction == "BUY":
            hit_sl = l <= sl
            # TP'lerden hangileri hit?
            tps_hit = [n for n, p in tp_levels.items() if h >= p]
        else:
            hit_sl = h >= sl
            tps_hit = [n for n, p in tp_levels.items() if l <= p]

        if hit_sl and tps_hit:
            # In-bar ambiguity — OHLC heuristic
            tp_first = (not bullish) if direction == "BUY" else bullish
            if tp_first:
                last_tp = max(tps_hit, key=lambda x: int(x[2:]))
                return {"status": "completed", "target_hit": last_tp,
                         "exit_price": tp_levels[last_tp], "bars_walked": i + 1,
                         "ambiguous": True}
            return {"status": "stopped", "target_hit": None,
                     "exit_price": sl, "bars_walked": i + 1, "ambiguous": True}
        if tps_hit:
            last_tp = max(tps_hit, key=lambda x: int(x[2:]))
            return {"status": "completed", "target_hit": last_tp,
                     "exit_price": tp_levels[last_tp], "bars_walked": i + 1}
        if hit_sl:
            return {"status": "stopped", "target_hit": None,
                     "exit_price": sl, "bars_walked": i + 1}
    return {"status": "expired", "exit_price": float(bars_after[-1].get("close") or entry),
             "bars_walked": len(bars_after)}


@router.post("/run")
async def run_backtest(bg: BackgroundTasks,
                        days: int = Query(90, ge=14, le=180),
                        direction: str = Query("BUY"),
                        max_signals: int = Query(500, ge=50, le=5000)):
    """USOIL eski vs yeni config — 1m walk-forward A/B."""
    if _STATUS["running"]:
        return {"status": "already_running",
                "started_at": _STATUS["started_at"]}
    _STATUS.update({"running": True,
                     "started_at": datetime.now(timezone.utc).isoformat(),
                     "finished_at": None, "result": None, "error": None})

    async def _do():
        import asyncio, bisect
        try:
            from database.supabase_client import get_supabase_client, is_db_available
            from services.signal_replay_1m import _load_all_1m_bars_sync
            if not is_db_available():
                _STATUS["error"] = "db_unavailable"; return

            client = get_supabase_client()
            since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            # USOIL sinyallerini çek (resolved + replay verisi varsa)
            rows: list[dict] = []
            offset = 0
            while True:
                q = (client.table("prediction_replay_corrections").select(
                      "prediction_id,symbol,direction,entry_price,signal_created_at,"
                      "corrected_status,corrected_exit_price,replay_status")
                      .eq("symbol", "USOIL.FOREX")
                      .eq("direction", direction.upper())
                      .gte("signal_created_at", since)
                      .eq("replay_status", "ok")
                      .order("signal_created_at", desc=False)
                      .range(offset, offset + 999))
                res = q.execute() if hasattr(q, "execute") else q
                page = (res.data if hasattr(res, "data")
                          else (res.get("data") if isinstance(res, dict) else [])) or []
                if not page: break
                rows.extend(page)
                if len(page) < 1000: break
                offset += 1000
                if len(rows) >= max_signals * 2: break

            rows = [r for r in rows if r.get("entry_price")]
            if len(rows) > max_signals:
                # Stratified across time
                step = len(rows) / max_signals
                rows = [rows[int(i * step)] for i in range(max_signals)]

            if not rows:
                _STATUS["error"] = f"USOIL {direction} sinyal yok (son {days}d)"
                return

            # 1m bars yükle
            bars_1m = await asyncio.to_thread(_load_all_1m_bars_sync, "USOIL.FOREX")
            if not bars_1m:
                _STATUS["error"] = "1m bars yok"; return
            ts_keys = [b["ts"] for b in bars_1m]

            old_results = []
            new_results = []
            for r in rows:
                entry = float(r["entry_price"])
                try:
                    cutoff = datetime.fromisoformat(
                        r["signal_created_at"].replace("Z", "+00:00"))
                except: continue
                # Walk window — 6 saat
                window_end = cutoff + timedelta(minutes=360)
                idx_start = bisect.bisect_right(ts_keys, cutoff)
                idx_end = bisect.bisect_right(ts_keys, window_end)
                bars_after = bars_1m[idx_start:idx_end]
                if not bars_after: continue

                old_results.append(_simulate_walk(bars_after, direction, entry, OLD_CONFIG))
                new_results.append(_simulate_walk(bars_after, direction, entry, NEW_CONFIG))

            def summarize(results, cfg, label):
                from collections import Counter
                if not results: return {}
                statuses = Counter(r["status"] for r in results)
                completed = [r for r in results if r["status"] == "completed"]
                stopped = [r for r in results if r["status"] == "stopped"]
                resolved = len(completed) + len(stopped)
                wr = round(100 * len(completed) / resolved, 1) if resolved else 0
                # TP dağılımı
                tp_dist = Counter(r.get("target_hit") for r in completed)
                # Brüt expectancy (yüzde olarak)
                gross_per = []
                for r in results:
                    if r["status"] == "completed":
                        name = r["target_hit"]
                        gross_per.append(cfg[name])
                    elif r["status"] == "stopped":
                        gross_per.append(-cfg["SL"])
                    else:
                        gross_per.append(0)
                gross_total = round(sum(gross_per), 3)
                gross_avg = round(sum(gross_per) / len(gross_per), 4) if gross_per else 0
                # Net (spread çıkarılmış)
                net_per = [g - cfg["spread"] if abs(g) > 0.001 else 0 for g in gross_per]
                net_total = round(sum(net_per), 3)
                net_avg = round(sum(net_per) / len(net_per), 4) if net_per else 0
                return {
                    "label": label, "n_total": len(results),
                    "statuses": dict(statuses),
                    "resolved": resolved, "win_rate_pct": wr,
                    "tp_distribution": dict(tp_dist),
                    "gross_pct_total": gross_total,
                    "gross_pct_avg_per_signal": gross_avg,
                    "net_pct_total_after_spread": net_total,
                    "net_pct_avg_per_signal": net_avg,
                    "spread_assumed_pct": cfg["spread"],
                }

            old_s = summarize(old_results, OLD_CONFIG, "OLD config")
            new_s = summarize(new_results, NEW_CONFIG, "NEW config")
            improvement = None
            if old_s.get("net_pct_total_after_spread") is not None:
                old_net = old_s["net_pct_total_after_spread"]
                new_net = new_s["net_pct_total_after_spread"]
                improvement = {
                    "old_net_total": old_net,
                    "new_net_total": new_net,
                    "delta_pct_points": round(new_net - old_net, 3),
                    "delta_pct_rel": (round(100 * (new_net - old_net) / abs(old_net), 1)
                                       if abs(old_net) > 0.001 else None),
                }

            _STATUS["result"] = {
                "status": "ok",
                "days": days,
                "direction": direction.upper(),
                "signals_simulated": len(old_results),
                "old_config": OLD_CONFIG,
                "new_config": NEW_CONFIG,
                "old_summary": old_s,
                "new_summary": new_s,
                "improvement": improvement,
                "verdict": (
                    "🟢 YENİ CONFIG ÇOK DAHA İYİ" if improvement and improvement.get("delta_pct_points") and improvement["delta_pct_points"] > 0.5
                    else "🟡 YENİ CONFIG MARJİNAL İYİLEŞME" if improvement and improvement.get("delta_pct_points") and improvement["delta_pct_points"] > 0
                    else "🔴 YENİ CONFIG DAHA KÖTÜ — DEPLOY ETME"
                    if improvement else "yetersiz veri"),
            }
        except Exception as e:
            logger.exception("[usoil-bt] hata: %s", e)
            _STATUS["error"] = str(e)[:500]
        finally:
            _STATUS["running"] = False
            _STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do)
    return {"status": "scheduled", "days": days, "direction": direction,
            "max_signals": max_signals,
            "poll": "/api/usoil-config-bt/status",
            "estimated_minutes": "3-6"}


@router.get("/status")
async def bt_status():
    return {**_STATUS}
