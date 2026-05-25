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

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

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


_TRAINING_STATUS: dict = {"running": False, "started_at": None,
                          "finished_at": None, "result": None, "error": None}


@router.post("/train-meta")
async def train_meta(bg: BackgroundTasks,
                      days: int = Query(90, ge=14, le=180)):
    """Stage 4 meta classifier'ı arka planda eğit (Railway'de). Local'de
    pip/python/env değişkeniyle uğraşmaya gerek yok — sadece bu endpoint'i
    çağır, /train-meta/status ile ilerlemeyi takip et."""
    if _TRAINING_STATUS["running"]:
        return {"status": "already_running",
                "started_at": _TRAINING_STATUS["started_at"]}
    _TRAINING_STATUS.update({"running": True, "started_at":
                              datetime.now(timezone.utc).isoformat(),
                              "finished_at": None, "result": None, "error": None})

    async def _do_train():
        try:
            from scripts.train_precision_meta_classifier import (
                collect_training_data, train, Path as _Path)
            X, y = await collect_training_data(days)
            if len(X) < 200:
                raise RuntimeError(f"yetersiz veri: {len(X)} örnek")
            base = _Path("backend") / "models"
            if not base.exists():
                base = _Path(__file__).parent.parent / "models"
            train(X, y, base / "precision_meta_classifier.joblib",
                  base / "precision_meta_features.json")
            _TRAINING_STATUS["result"] = {
                "n_samples": len(X),
                "model_path": str(base / "precision_meta_classifier.joblib"),
            }
        except Exception as e:
            logger.exception("[train-meta] hata: %s", e)
            _TRAINING_STATUS["error"] = str(e)[:300]
        finally:
            _TRAINING_STATUS["running"] = False
            _TRAINING_STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do_train)
    return {"status": "scheduled", "days": days,
            "poll": "/api/precision-veto/train-meta/status"}


@router.get("/train-meta/status")
async def train_meta_status():
    return {**_TRAINING_STATUS}


@router.post("/reload-meta-model")
async def reload_meta_model_endpoint():
    """Yeni eğitim sonrası model cache'ini tazele (yeniden başlatmadan)."""
    from services.precision_veto_service import reload_meta_model
    return reload_meta_model()


@router.post("/backtest-stage1c")
async def backtest_stage1c(
    days: int = Query(90, ge=14, le=180),
    sample_per_scope: int = Query(300, ge=0, le=5000,
                                    description="(sembol,yön) başına örneklem — 0 = tümü"),
):
    """Stage 1c (Day Structure) point-in-time backtest. Leak-siz: her sinyal
    için sadece o anın 1m verisinden DS yeniden hesaplanır, Stage 1c uygulanır,
    sonra signal'in gerçek corrected_status'uyla karşılaştırılır.

    Haftasonu beklemeden Stage 1c'nin gerçek etkisini ölçer."""
    from services.precision_veto_backtest import backtest_stage1c
    res = await backtest_stage1c(days=days, sample_per_scope=sample_per_scope)
    if res.get("status") == "error":
        raise HTTPException(500, res.get("error", "backtest hatası"))
    return res


@router.get("/day-structure")
async def day_structure(symbol: str = Query("XAUUSD"),
                         timeframe: str = Query("15m")):
    """Bir sembol için tam Day Structure paketi — PDH/PDL/PWH/PWL, pivotlar,
    multi-scale swings, memory zones (freshness + rejection sayısı), ATR.
    Stage 1c bu veriyi kullanır; Stage 4 ML feature seti de buradan beslenir."""
    from services.day_structure_service import compute_day_structure
    ds = await compute_day_structure(symbol, timeframe)
    if ds is None:
        raise HTTPException(503, f"{symbol} için day structure hesaplanamadı (mum verisi yok)")
    return {
        "status": "ok",
        "symbol": ds.symbol, "timeframe": ds.timeframe,
        "computed_at": ds.computed_at.isoformat(),
        "current_price": ds.current_price,
        "atr": ds.atr, "today_atr_ratio": ds.today_atr_ratio,
        "day_high": ds.day_high, "day_low": ds.day_low,
        "pdh": ds.pdh, "pdl": ds.pdl, "pdc": ds.pdc,
        "pwh": ds.pwh, "pwl": ds.pwl,
        "pdh_tests_today": {"touches": ds.pdh_touches_today,
                              "rejections": ds.pdh_rejections_today},
        "pdl_tests_today": {"touches": ds.pdl_touches_today,
                              "rejections": ds.pdl_rejections_today},
        "pivots": ds.pivots,
        "swing_counts": {
            "small_highs": len(ds.swings_small_highs),
            "small_lows": len(ds.swings_small_lows),
            "large_highs": len(ds.swings_large_highs),
            "large_lows": len(ds.swings_large_lows),
        },
        "memory_zones": [
            {"center": z.center, "lower": z.lower, "upper": z.upper,
             "touches": z.touches, "rejections": z.rejections, "breaks": z.breaks,
             "freshness": z.freshness, "last_touch_min_ago": z.last_touch_minutes_ago,
             "strength": z.strength}
            for z in ds.memory_zones[:10]
        ],
    }


@router.get("/test")
async def veto_self_test(
    symbol: str = Query("XAUUSD"),
    direction: str = Query("BUY"),
    confidence: float = Query(75.0),
    timeframe: str = Query("15m"),
):
    """Self-test — canlı fiyat/mum verisiyle check_signal()'i çalıştırır,
    4 aşamanın da hatasız çalıştığını anında gösterir. Beklemeden doğrulama."""
    from services.precision_veto_service import check_signal
    try:
        from services.data_fetcher import fetch_latest_price
        price = await fetch_latest_price(symbol) or 0.0
    except Exception as e:
        raise HTTPException(500, f"fiyat alınamadı: {e}")
    if not price:
        raise HTTPException(503, f"{symbol} için canlı fiyat yok")

    signal = {"symbol": symbol, "direction": direction.upper(),
              "confidence": confidence, "model_type": "self_test",
              "timeframe": timeframe, "price": price}
    try:
        vr = await check_signal(signal)
    except Exception as e:
        logger.exception("veto self-test hata: %s", e)
        raise HTTPException(500, f"check_signal hata: {e}")

    return {
        "status": "ok",
        "input": signal,
        "engine_ran": True,
        "result": {
            "would_veto": vr.would_veto,
            "vetoed": vr.vetoed,
            "shadow_mode": vr.shadow_mode,
            "stage": vr.stage,
            "reason": vr.reason,
            "direction_out": vr.direction,
            "original_confidence": vr.original_confidence,
            "adjusted_confidence": round(vr.adjusted_confidence, 2),
            "total_penalty": vr.total_penalty,
            "converted_to_hold": vr.converted_to_hold,
        },
        "features": vr.features,
        "stage_details": vr.details,
        "note": ("4 aşama da hatasız çalıştıysa 'features' alanında "
                  "liquidity_zone_position / mtf_agreement_score / "
                  "wick_rejection_score / bb_position / z_score dolu olmalı."),
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
    """DÜRÜST backtest — PIP TEMELLİ. Shadow modda veto edilen sinyal
    bloklanmaz, prediction_logs'a yazılır ve lifecycle onu normal çözer —
    yani gerçek exit_price'ı bilinir. Her veto için:

      good_catch (status=stopped)  → veto X pip ZARARDAN kurtardı
      missed_win (status=completed)→ veto Y pip KAZANCI kaçırdı

    net_pips_saved = Σ(kurtarılan zarar) − Σ(kaçırılan kazanç), sembol bazlı
    (NDX puanı / XAUUSD pip / USOIL % aynı kovaya konmaz — per-symbol).

    NOT: enforce moduna geçince vetolanan sinyal prediction_logs'a YAZILMAZ;
    o zaman bu yöntem çalışmaz — veto anından itibaren 1m mum ileri-yürüyüşü
    gerekir (replay motoru bunun için hazır). Şimdilik shadow fazında bu
    yöntem doğru ve yeterli."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        raise HTTPException(503, "db_unavailable")
    client = get_supabase_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

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

    # prediction_logs — eşleştirme + realized pip hesabı için tüm gerekli alanlar.
    pq = (client.table("prediction_logs")
          .select("symbol,model_type,ml_direction,status,created_at,"
                  "ml_entry_price,exit_price,stop_loss_pips")
          .gte("created_at", since).limit(50000))
    pres = pq.execute() if hasattr(pq, "execute") else pq
    plogs = pres.data if hasattr(pres, "data") else (
        pres.get("data") if isinstance(pres, dict) else []) or []

    def _parse(t):
        try:
            return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        except Exception:
            return None

    try:
        from services.target_config import pips_from_price_change
    except Exception:
        pips_from_price_change = None

    def _realized_pips(symbol, direction, entry, exit_p) -> float:
        """Sinyal yönünde gerçekleşen pip (kazanç +, zarar −)."""
        if not entry or not exit_p:
            return 0.0
        diff = (exit_p - entry) if direction == "BUY" else (entry - exit_p)
        if pips_from_price_change:
            try:
                mag = abs(pips_from_price_change(abs(diff), symbol))
                return mag if diff >= 0 else -mag
            except Exception:
                pass
        return diff   # ham fiyat farkı (fallback)

    # (symbol, model, direction) → [(created_at, row)]
    idx: dict = {}
    for p in plogs:
        key = (p.get("symbol"), p.get("model_type"),
               (p.get("ml_direction") or "").upper())
        idx.setdefault(key, []).append((_parse(p.get("created_at")), p))

    good_catch = missed_win = neutral = unmatched = 0
    by_reason: dict = {}
    # sembol bazlı pip kovaları (birimler karışmasın)
    per_symbol: dict = {}

    for v in vetoes:
        sym = v.get("symbol")
        direction = (v.get("signal_direction") or "").upper()
        key = (sym, v.get("model_type"), direction)
        vt = _parse(v.get("created_at"))
        match = None
        best = None
        for (pt, prow) in idx.get(key, []):
            if pt is None or vt is None:
                continue
            gap = abs((pt - vt).total_seconds())
            if gap <= 300 and (best is None or gap < best):   # ±5 dk
                best = gap
                match = prow
        rsn = v.get("veto_reason") or "?"
        bucket = by_reason.setdefault(rsn, {"good": 0, "missed": 0, "other": 0})
        ps = per_symbol.setdefault(sym, {"good_catch": 0, "missed_win": 0,
                                          "pips_saved": 0.0, "pips_missed": 0.0})

        if match is None:
            unmatched += 1
            continue
        status = match.get("status")
        realized = _realized_pips(sym, direction,
                                  float(match.get("ml_entry_price") or 0),
                                  float(match.get("exit_price") or 0))
        if status == "stopped":
            good_catch += 1; bucket["good"] += 1
            ps["good_catch"] += 1
            ps["pips_saved"] += abs(realized)        # bu zarardan kurtulurduk
        elif status == "completed":
            missed_win += 1; bucket["missed"] += 1
            ps["missed_win"] += 1
            ps["pips_missed"] += max(0.0, realized)  # bu kazancı kaçırırdık
        else:
            neutral += 1; bucket["other"] += 1

    for sym, ps in per_symbol.items():
        ps["pips_saved"] = round(ps["pips_saved"], 2)
        ps["pips_missed"] = round(ps["pips_missed"], 2)
        ps["net_pips_saved"] = round(ps["pips_saved"] - ps["pips_missed"], 2)

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
        "per_symbol_pips": per_symbol,
        "verdict": (
            f"Veto edilen sinyallerin %{precision}'i SL'ye gitti — motor "
            f"doğru engelliyor. Pip etkisi per_symbol_pips'te." if precision
            and precision >= 60 else
            f"Veto precision %{precision} — enforce'a geçmeden eşikleri gözden geçir."
            if precision is not None else
            "Yeterli eşleşmiş resolved sinyal yok — birkaç saat/gün daha bekle."
        ),
        "by_reason": by_reason,
    }
