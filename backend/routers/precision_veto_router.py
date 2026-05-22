"""
Precision Veto Engine — gözlem & analiz endpoint'leri.

GET  /api/precision-veto/config         → motor durumu + config
GET  /api/precision-veto/vetoes         → son veto kayıtları
GET  /api/precision-veto/summary        → reason bazında özet
GET  /api/precision-veto/shadow-report  → shadow modda 'veto edilirdi' işaretli
                                          sinyallerin GERÇEK sonucu (SL'ye mi
                                          gitti, TP'ye mi) — dürüst backtest
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/precision-veto", tags=["Precision Veto"])


@router.get("/config")
async def veto_config():
    """Motor durumu + aktif config (sembol override'ları dahil)."""
    from services.precision_veto_service import (
        PRECISION_VETO_CONFIG, _SYMBOL_OVERRIDES, _env_enabled, _env_shadow,
    )
    return {
        "enabled": _env_enabled(),
        "shadow_mode": _env_shadow(),
        "note": ("shadow_mode=True → veto HESAPLANIR ve loglanır ama sinyal "
                  "bloklanmaz. Birkaç gün shadow verisi topla, /shadow-report "
                  "ile etkisini gör, sonra PRECISION_VETO_SHADOW=0 ile enforce'a geç."),
        "config": PRECISION_VETO_CONFIG,
        "symbol_overrides": _SYMBOL_OVERRIDES,
    }


@router.get("/vetoes")
async def list_vetoes(
    days: int = Query(7, ge=1, le=90),
    symbol: Optional[str] = None,
    stage: Optional[int] = Query(None, ge=1, le=4),
    limit: int = Query(200, ge=1, le=2000),
):
    """Son veto kayıtları (signal_vetoes tablosu)."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        raise HTTPException(503, "db_unavailable")
    client = get_supabase_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    q = (client.table("signal_vetoes")
         .select("created_at,symbol,model_type,signal_direction,signal_confidence,"
                 "veto_stage,veto_reason,outcome,liquidity_zone_position,"
                 "wick_rejection_score,price_at_veto")
         .gte("created_at", since)
         .order("created_at", desc=True)
         .limit(limit))
    if symbol:
        q = q.eq("symbol", symbol)
    if stage:
        q = q.eq("veto_stage", stage)
    res = q.execute() if hasattr(q, "execute") else q
    rows = res.data if hasattr(res, "data") else (
        res.get("data") if isinstance(res, dict) else []) or []
    return {"status": "ok", "count": len(rows), "vetoes": rows}


@router.get("/summary")
async def veto_summary(days: int = Query(30, ge=1, le=90)):
    """Reason / stage bazında veto özeti — hangi sebep ne sıklıkta tetikliyor."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        raise HTTPException(503, "db_unavailable")
    client = get_supabase_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    q = (client.table("signal_vetoes")
         .select("symbol,model_type,signal_direction,veto_stage,veto_reason,outcome")
         .gte("created_at", since).limit(20000))
    res = q.execute() if hasattr(q, "execute") else q
    rows = res.data if hasattr(res, "data") else (
        res.get("data") if isinstance(res, dict) else []) or []

    by_reason: dict = {}
    by_stage: dict = {}
    by_outcome: dict = {}
    for r in rows:
        rsn = r.get("veto_reason") or "?"
        by_reason[rsn] = by_reason.get(rsn, 0) + 1
        st = str(r.get("veto_stage"))
        by_stage[st] = by_stage.get(st, 0) + 1
        oc = r.get("outcome") or "?"
        by_outcome[oc] = by_outcome.get(oc, 0) + 1
    return {
        "status": "ok", "days": days, "total": len(rows),
        "by_reason": dict(sorted(by_reason.items(), key=lambda kv: -kv[1])),
        "by_stage": by_stage,
        "by_outcome": by_outcome,
    }


@router.get("/shadow-report")
async def shadow_report(days: int = Query(7, ge=1, le=60)):
    """DÜRÜST backtest: shadow modda 'veto edilirdi' işaretlenen sinyallerin
    GERÇEK sonucu. Shadow modda sinyal bloklanmaz, prediction_logs'a da yazılır
    — yani veto kararını gerçek outcome ile karşılaştırabiliriz.

    'good_catch'  = veto edilen sinyal SL'ye gitti (doğru engellerdik)
    'missed_win'  = veto edilen sinyal TP yaptı (yanlışlıkla kaçırırdık)
    Bu oran enforce moduna geçmeden önce motorun değerini gösterir."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        raise HTTPException(503, "db_unavailable")
    client = get_supabase_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Shadow / veto kayıtları
    vq = (client.table("signal_vetoes")
          .select("created_at,symbol,model_type,signal_direction,veto_stage,"
                  "veto_reason,outcome")
          .gte("created_at", since).in_("outcome", ["shadow", "veto"]).limit(20000))
    vres = vq.execute() if hasattr(vq, "execute") else vq
    vetoes = vres.data if hasattr(vres, "data") else (
        vres.get("data") if isinstance(vres, dict) else []) or []
    if not vetoes:
        return {"status": "ok", "days": days, "vetoed_signals": 0,
                "note": "Henüz shadow verisi yok — motor çalıştıkça birikir."}

    # prediction_logs'tan aynı pencereyi çek, eşleştirme için.
    pq = (client.table("prediction_logs")
          .select("symbol,model_type,ml_direction,status,created_at")
          .gte("created_at", since).limit(50000))
    pres = pq.execute() if hasattr(pq, "execute") else pq
    plogs = pres.data if hasattr(pres, "data") else (
        pres.get("data") if isinstance(pres, dict) else []) or []

    def _parse(t):
        try:
            return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        except Exception:
            return None

    # (symbol, model, direction) → [(created_at, status)]
    idx: dict = {}
    for p in plogs:
        key = (p.get("symbol"), p.get("model_type"),
               (p.get("ml_direction") or "").upper())
        idx.setdefault(key, []).append((_parse(p.get("created_at")), p.get("status")))

    good_catch = missed_win = neutral = unmatched = 0
    by_reason: dict = {}
    for v in vetoes:
        key = (v.get("symbol"), v.get("model_type"),
               (v.get("signal_direction") or "").upper())
        vt = _parse(v.get("created_at"))
        match_status = None
        best = None
        for (pt, status) in idx.get(key, []):
            if pt is None or vt is None:
                continue
            gap = abs((pt - vt).total_seconds())
            if gap <= 300 and (best is None or gap < best):   # ±5 dk
                best = gap
                match_status = status
        rsn = v.get("veto_reason") or "?"
        bucket = by_reason.setdefault(rsn, {"good": 0, "missed": 0, "other": 0})
        if match_status == "stopped":
            good_catch += 1; bucket["good"] += 1
        elif match_status == "completed":
            missed_win += 1; bucket["missed"] += 1
        elif match_status in ("expired", "market_closed_invalid"):
            neutral += 1; bucket["other"] += 1
        else:
            unmatched += 1

    resolved = good_catch + missed_win
    precision = round(100 * good_catch / resolved, 1) if resolved else None
    return {
        "status": "ok", "days": days,
        "vetoed_signals": len(vetoes),
        "matched_resolved": resolved,
        "good_catch_SL_avoided": good_catch,
        "missed_win_TP": missed_win,
        "neutral_expired": neutral,
        "unmatched": unmatched,
        "veto_precision_pct": precision,
        "verdict": (
            f"Veto edilen sinyallerin %{precision}'i gerçekten SL'ye gitti — "
            f"motor doğru engelliyor." if precision and precision >= 60 else
            f"Veto precision %{precision} — enforce'a geçmeden eşikleri gözden geçir."
            if precision is not None else
            "Yeterli eşleşmiş resolved sinyal yok."
        ),
        "by_reason": by_reason,
    }
