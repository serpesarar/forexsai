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
    """Eğitim durumu + son eğitimin metrikleri (RMSE/MAE/Spearman/feature_count).

    Metrikler `precision_meta_features.json`'dan okunur (eğitim sonu yazılır)."""
    import json, os
    from pathlib import Path as _P
    # train-meta task aynı yolu kullanıyor (backend/models veya scripts'in tahminine göre)
    candidates = [
        _P("backend") / "models" / "precision_meta_features.json",
        _P(__file__).parent.parent / "models" / "precision_meta_features.json",
        _P("/app/models/precision_meta_features.json"),
    ]
    meta_info = None
    meta_path = None
    for p in candidates:
        try:
            if p.exists():
                with open(p, "r") as f:
                    meta_info = json.load(f)
                meta_path = str(p)
                # mtime de bilgi olsun (son güncelleme)
                try:
                    meta_info["_file_mtime"] = datetime.fromtimestamp(
                        os.path.getmtime(p), tz=timezone.utc).isoformat()
                except Exception:
                    pass
                break
        except Exception as e:
            logger.debug("[train-status] %s okunamadı: %s", p, e)
    out = {**_TRAINING_STATUS}
    if meta_info is not None:
        # features.json içeriği genelde: {"features": [...], "rmse": .., "mae": .., "spearman": ..,
        #  "n_train": .., "n_test": .., "is_regressor": true, ...}
        features = meta_info.get("features") or []
        out["last_model"] = {
            "path": meta_path,
            "feature_count": len(features),
            "metrics": {k: meta_info.get(k) for k in
                         ("rmse", "mae", "spearman", "r2", "n_train", "n_val",
                          "n_test", "is_regressor", "target",
                          "test_rmse", "test_mae", "test_spearman",
                          "val_rmse", "val_mae")
                         if meta_info.get(k) is not None},
            "trained_at": meta_info.get("trained_at") or meta_info.get("_file_mtime"),
            "first_features": features[:8],
        }
    else:
        out["last_model"] = None
    return out


@router.post("/reload-meta-model")
async def reload_meta_model_endpoint():
    """Yeni eğitim sonrası model cache'ini tazele (yeniden başlatmadan)."""
    from services.precision_veto_service import reload_meta_model
    return reload_meta_model()


# ─── Stage 4 percentile-based sizing — state & seeding ───────────────────────
@router.get("/stage4-sizing/state")
async def stage4_sizing_state(verbose: bool = Query(False)):
    """Percentile-based sizing modülünün anlık durumu — sembol başına history
    sayısı, predicted_r dağılım kuantilleri (p10/p30/p50/p70/p90), realized R
    ortalaması, win rate, pending kuyruk uzunluğu. Filtreleme aktif mi göster."""
    from services.stage4_sizing import get_state
    return get_state(verbose=verbose)


_SEED_STATUS: dict = {"running": False, "started_at": None,
                       "finished_at": None, "result": None, "error": None}


@router.post("/stage4-sizing/seed-from-backtest")
async def stage4_sizing_seed(bg: BackgroundTasks,
                              days: int = Query(90, ge=14, le=180),
                              test_only: bool = Query(False, description=
                                  "True: sadece OOS slice (dar dağılım). "
                                  "False (default): tüm slice'tan stratified sample"),
                              stratified_per_symbol: int = Query(500, ge=50, le=5000,
                                  description="Sembol başına evenly-spaced "
                                  "kaç örnek (sadece test_only=False'da)"),
                              per_symbol: bool = Query(True, description=
                                  "Her sembolün kendi modeli varsa onunla "
                                  "tahmin et — yoksa legacy combined")):
    """Cold start'ı atlamak için bootstrap. ARKA PLAN — collect_training_data
    5+ dk sürer; /stage4-sizing/seed-from-backtest/status ile takip et.

    test_only=False (default 2026-05-25): tüm slice'tan her sembol için
    `stratified_per_symbol` evenly-spaced örnek alınır → percentile dağılımı
    geniş ve gerçekçi (sahte 99+ percentile sorununu önler)."""
    if _SEED_STATUS["running"]:
        return {"status": "already_running",
                "started_at": _SEED_STATUS["started_at"]}
    _SEED_STATUS.update({"running": True,
                          "started_at": datetime.now(timezone.utc).isoformat(),
                          "finished_at": None, "result": None, "error": None})

    async def _do():
        try:
            from scripts.train_precision_meta_classifier import collect_training_data
            from services.stage4_sizing import seed_from_backtest, get_state
            from services.inference_stage4 import predict_r as per_sym_predict
            X, y, M = await collect_training_data(days=days, return_meta=True)
            if not X:
                _SEED_STATUS["error"] = "veri yok"
                return
            n = len(X)
            # Stratified sampling per symbol — geniş percentile dağılımı için
            if test_only:
                indices = list(range(int(n * 0.85), n))
            else:
                from collections import defaultdict
                by_sym: dict = defaultdict(list)
                for i, m in enumerate(M):
                    by_sym[m["symbol"]].append(i)
                indices = []
                for sym, idxs in by_sym.items():
                    if len(idxs) <= stratified_per_symbol:
                        indices.extend(idxs)
                    else:
                        step = len(idxs) / float(stratified_per_symbol)
                        sel = [idxs[int(k * step)] for k in range(stratified_per_symbol)]
                        indices.extend(sel)
                indices.sort()
            rows = []
            used_per_sym = 0
            used_legacy = 0
            for i in indices:
                sym = M[i]["symbol"]
                pred = None
                if per_symbol:
                    pred, info = per_sym_predict(sym, X[i])
                    if pred is not None:
                        if info.get("used_per_symbol"):
                            used_per_sym += 1
                        else:
                            used_legacy += 1
                if pred is None:
                    continue
                rows.append({"symbol": sym, "predicted_r": float(pred),
                              "realized_r": float(y[i])})
            added = seed_from_backtest(rows)
            _SEED_STATUS["result"] = {
                "seeded_rows": added,
                "predicted_per_symbol": used_per_sym,
                "predicted_legacy_fallback": used_legacy,
                "indices_used": len(indices),
                "total_samples": n,
                "test_only": test_only,
                "stratified_per_symbol": (stratified_per_symbol
                                            if not test_only else None),
                "state_after": get_state(verbose=False),
            }
        except Exception as e:
            logger.exception("[seed] hata: %s", e)
            _SEED_STATUS["error"] = str(e)[:500]
        finally:
            _SEED_STATUS["running"] = False
            _SEED_STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do)
    return {"status": "scheduled", "days": days,
            "poll": "/api/precision-veto/stage4-sizing/seed-from-backtest/status",
            "estimated_minutes": "5-7"}


@router.get("/stage4-sizing/seed-from-backtest/status")
async def stage4_sizing_seed_status():
    return {**_SEED_STATUS}


# ─── Per-symbol training & inspection ────────────────────────────────────────
_TRAIN_STAGE4_STATUS: dict = {"running": False, "started_at": None,
                                "finished_at": None, "result": None, "error": None}


@router.post("/train-stage4")
async def train_stage4_endpoint(bg: BackgroundTasks,
                                 days: int = Query(90, ge=14, le=180)):
    """Sembol bazlı LightGBM eğitimi (z-score normalize). USOIL Spearman=null
    sorununu çözmek için: her sembol kendi verisi+ölçeğiyle ayrı model.

    Eğitim sonunda backend/models/stage4_per_symbol/{slug}/ altına yazar
    (model.joblib + features.json + normalizer.json). model_loader otomatik
    cache'i temizler — sonraki check_signal yeni modeli kullanır.

    ~12 dk (collect_training_data 5dk + sembol başına 1-2 dk eğitim)."""
    if _TRAIN_STAGE4_STATUS["running"]:
        return {"status": "already_running",
                "started_at": _TRAIN_STAGE4_STATUS["started_at"]}
    _TRAIN_STAGE4_STATUS.update({"running": True,
                                  "started_at": datetime.now(timezone.utc).isoformat(),
                                  "finished_at": None, "result": None, "error": None})

    async def _do():
        try:
            from scripts.train_stage4 import train_all
            res = await train_all(days=days)
            _TRAIN_STAGE4_STATUS["result"] = res
        except Exception as e:
            logger.exception("[train-stage4] hata: %s", e)
            _TRAIN_STAGE4_STATUS["error"] = str(e)[:500]
        finally:
            _TRAIN_STAGE4_STATUS["running"] = False
            _TRAIN_STAGE4_STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do)
    return {"status": "scheduled", "days": days,
            "poll": "/api/precision-veto/train-stage4/status",
            "estimated_minutes": "10-15"}


@router.get("/train-stage4/status")
async def train_stage4_status():
    return {**_TRAIN_STAGE4_STATUS}


@router.post("/reload-models")
async def reload_models():
    """model_loader cache'ini temizle ve disk'i yeniden tara. Yeni eğitim
    sonrası çağır (train-stage4 sonunda otomatik çağrılıyor ama manuel
    kontrol için de açık)."""
    from services.model_loader import reload_all
    return reload_all()


@router.get("/models-state")
async def models_state():
    """Hangi sembollere model yüklü, normalizer var mı, legacy fallback aktif mi."""
    from services.model_loader import state_snapshot
    return state_snapshot()


# ─── Feature dağılım debug — USOIL Spearman=null kök neden tespiti ───────────
_FEATURE_DEBUG_STATUS: dict = {"running": False, "started_at": None,
                                "finished_at": None, "result": None, "error": None}


@router.post("/debug-feature-distribution")
async def debug_feature_distribution(bg: BackgroundTasks,
                                       days: int = Query(90, ge=14, le=180)):
    """Per-symbol feature dağılım istatistikleri — USOIL Spearman=null
    sorununu debug etmek için. Her continuous feature için sembol bazlı
    p10/p50/p90/std/zero_rate verir, scale uyumsuzluğu görünür."""
    if _FEATURE_DEBUG_STATUS["running"]:
        return {"status": "already_running",
                "started_at": _FEATURE_DEBUG_STATUS["started_at"]}
    _FEATURE_DEBUG_STATUS.update({"running": True,
                                   "started_at": datetime.now(timezone.utc).isoformat(),
                                   "finished_at": None, "result": None, "error": None})

    async def _do():
        try:
            from scripts.train_precision_meta_classifier import collect_training_data
            X, y, M = await collect_training_data(days=days, return_meta=True)
            if not X:
                _FEATURE_DEBUG_STATUS["error"] = "veri yok"
                return
            # Sembol bazında gruplama
            per_sym: dict = {}
            for i, m in enumerate(M):
                per_sym.setdefault(m["symbol"], []).append(X[i])
            # Tüm feature isimleri (union)
            feat_names = sorted({k for row in X for k in row.keys()})
            import numpy as np
            out: dict = {"per_symbol_counts": {s: len(v) for s, v in per_sym.items()},
                          "features": {}}
            for name in feat_names:
                row: dict = {}
                for sym, rows in per_sym.items():
                    vals = []
                    zeros = 0
                    nones = 0
                    for r in rows:
                        v = r.get(name)
                        if v is None:
                            nones += 1
                            continue
                        try:
                            x = float(v)
                        except (TypeError, ValueError):
                            continue
                        if x == 0.0:
                            zeros += 1
                        vals.append(x)
                    if not vals:
                        row[sym] = {"n": 0, "all_none_or_skip": True}
                        continue
                    arr = np.array(vals, dtype=float)
                    n = len(arr)
                    row[sym] = {
                        "n": n,
                        "mean": round(float(arr.mean()), 4),
                        "std": round(float(arr.std()), 4),
                        "min": round(float(arr.min()), 4),
                        "p10": round(float(np.percentile(arr, 10)), 4),
                        "p50": round(float(np.percentile(arr, 50)), 4),
                        "p90": round(float(np.percentile(arr, 90)), 4),
                        "max": round(float(arr.max()), 4),
                        "zero_rate": round(zeros / n, 3),
                        "none_rate": round(nones / (n + nones), 3) if (n + nones) else 0,
                    }
                # Cross-symbol scale lift (max std / min std)
                stds = [r.get("std") for r in row.values()
                         if isinstance(r, dict) and r.get("std") is not None]
                if stds and min(stds) > 1e-9:
                    row["_scale_lift_max_over_min_std"] = round(max(stds) / min(stds), 2)
                out["features"][name] = row
            # En problematik feature'ları öne çıkar (max scale lift)
            ranked = sorted(
                ((n, f.get("_scale_lift_max_over_min_std") or 0)
                 for n, f in out["features"].items()),
                key=lambda kv: -kv[1])
            out["top_scale_mismatch"] = [{"feature": n, "scale_lift": s}
                                          for n, s in ranked[:15] if s > 2]
            _FEATURE_DEBUG_STATUS["result"] = out
        except Exception as e:
            logger.exception("[debug-feature] hata: %s", e)
            _FEATURE_DEBUG_STATUS["error"] = str(e)[:500]
        finally:
            _FEATURE_DEBUG_STATUS["running"] = False
            _FEATURE_DEBUG_STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do)
    return {"status": "scheduled", "days": days,
            "poll": "/api/precision-veto/debug-feature-distribution/status",
            "estimated_minutes": "4-6"}


@router.get("/debug-feature-distribution/status")
async def debug_feature_distribution_status():
    return {**_FEATURE_DEBUG_STATUS}


@router.post("/stage4-sizing/prune")
async def stage4_sizing_prune():
    """7+ gün bekleyen pending tahminleri at (lifecycle kaçırırsa bellek
    sızıntısı olmasın)."""
    from services.stage4_sizing import prune_stale_pending
    return {"removed": prune_stale_pending()}


_STAGE4_BACKTEST_STATUS: dict = {"running": False, "started_at": None,
                                   "finished_at": None, "result": None, "error": None}


@router.post("/backtest-stage4")
async def backtest_stage4(bg: BackgroundTasks,
                           days: int = Query(90, ge=14, le=180),
                           test_frac: float = Query(0.15, ge=0.05, le=0.4)):
    """Stage 4 ML modelinin GERÇEK kazandırıp kazandırmadığını dürüstçe ölç.

    Aynı 90 günlük replay verisi üzerinde:
    - Train slice (ilk %85) ile Test slice (son %15) ayrı metrikler
    - Decile analizi (predicted_r kovaları gerçekten R'yi sıralıyor mu?)
    - Threshold sweep (skip-if-low filtresi ne kadar kazandırır?)
    - Per-symbol Spearman (XAUUSD'de mi en iyi?)

    Decision: READY / TUNE / REJECT — Spearman + lift'e göre."""
    if _STAGE4_BACKTEST_STATUS["running"]:
        return {"status": "already_running",
                "started_at": _STAGE4_BACKTEST_STATUS["started_at"]}
    _STAGE4_BACKTEST_STATUS.update({"running": True,
                                    "started_at": datetime.now(timezone.utc).isoformat(),
                                    "finished_at": None, "result": None, "error": None})

    async def _do():
        try:
            from services.precision_veto_backtest import backtest_stage4_meta
            res = await backtest_stage4_meta(days=days, test_frac=test_frac)
            _STAGE4_BACKTEST_STATUS["result"] = res
        except Exception as e:
            logger.exception("[backtest-stage4] hata: %s", e)
            _STAGE4_BACKTEST_STATUS["error"] = str(e)[:500]
        finally:
            _STAGE4_BACKTEST_STATUS["running"] = False
            _STAGE4_BACKTEST_STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do)
    return {"status": "scheduled", "days": days, "test_frac": test_frac,
            "poll": "/api/precision-veto/backtest-stage4/status",
            "estimated_minutes": "5-8"}


@router.get("/backtest-stage4/status")
async def backtest_stage4_status():
    return {**_STAGE4_BACKTEST_STATUS}


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
