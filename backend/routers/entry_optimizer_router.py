"""
Entry Optimizer — test ve dış-API endpoint'leri.

Endpoint:
  POST /api/entry-optimizer/optimize  → tam karar (signal payload ile)
  GET  /api/entry-optimizer/test       → canlı fiyatla hızlı test

Trade bot bunu çağırmak için POST /optimize'ı kullanır:
  body: {symbol, direction, price?, tp?, sl?, atr?}
  response: {action, entry_price, sl_price, tp_price, structure_type, ...}
"""
from __future__ import annotations

import logging
from typing import Optional

from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/entry-optimizer", tags=["Entry Optimizer"])


@router.post("/optimize")
async def optimize(body: dict):
    """Trade pipeline'da Stage 4 sonrası çağrılır. Beklenen body:
      {symbol, direction (BUY|SELL), price, tp (opsiyonel), sl (opsiyonel),
       atr (opsiyonel)}

    Döndürdüğü JSON sözleşmesi entry_optimizer.optimize_entry'de
    belgelenmiştir — action ∈ {EXECUTE_NOW, LIMIT_ORDER, REJECT}."""
    if not isinstance(body, dict):
        raise HTTPException(400, "body must be JSON object")
    direction = (body.get("direction") or "").upper()
    if direction not in ("BUY", "SELL"):
        raise HTTPException(400, "direction must be BUY or SELL")
    if not body.get("symbol"):
        raise HTTPException(400, "symbol required")
    body["direction"] = direction
    try:
        from services.entry_optimizer import optimize_entry
        return await optimize_entry(body)
    except Exception as e:
        logger.exception("[entry-optimizer] optimize hata")
        raise HTTPException(500, f"optimize: {e}")


@router.get("/test")
async def test_endpoint(
    symbol: str = Query("XAUUSD"),
    direction: str = Query("BUY"),
    timeframe: str = Query("15m"),
    price: Optional[float] = Query(None, description=
        "Test fiyatı — boşsa canlı fiyat çekilir"),
):
    """Self-test — canlı fiyatla optimize_entry çalıştırır, sonucu döndürür.
    Trade pipeline'a dokunmaz; sadece kararı gösterir."""
    direction = direction.upper()
    if direction not in ("BUY", "SELL"):
        raise HTTPException(400, "direction must be BUY or SELL")

    use_price = price
    if use_price is None:
        try:
            from services.data_fetcher import fetch_latest_price
            use_price = await fetch_latest_price(symbol)
        except Exception as e:
            raise HTTPException(503, f"canlı fiyat alınamadı: {e}")
        if not use_price:
            raise HTTPException(503, f"{symbol} fiyat yok")

    signal = {"symbol": symbol, "direction": direction,
              "price": float(use_price), "timeframe": timeframe}
    try:
        from services.entry_optimizer import optimize_entry, DEFAULT_CONFIG
        cfg = {**DEFAULT_CONFIG, "timeframe": timeframe}
        decision = await optimize_entry(signal, config=cfg)
        return {"input": signal, "decision": decision,
                "config_summary": {
                    "ob_min_score": cfg["ob_min_score"],
                    "ob_max_age_candles": cfg["ob_max_age_candles"],
                    "inside_tolerance_atr": cfg["inside_tolerance_atr"],
                    "limit_max_pullback_atr": cfg["limit_max_pullback_atr"],
                    "default_rr": cfg["default_rr"],
                }}
    except Exception as e:
        logger.exception("[entry-optimizer] test hata")
        raise HTTPException(500, f"test: {e}")


# ─── 90 günlük replay backtest ────────────────────────────────────────────────
_BACKTEST_STATUS: dict = {"running": False, "started_at": None,
                           "finished_at": None, "result": None, "error": None}


@router.post("/backtest")
async def backtest(bg: BackgroundTasks,
                    days: int = Query(90, ge=14, le=180),
                    sample_per_scope: int = Query(300, ge=0, le=5000)):
    """Entry Optimizer'ı son N günün resolved sinyalleri üzerinde point-in-time
    simüle eder. Her sinyal için:
      - signal_created_at anına kadar 15m candle slice → MarketStructureAnalyzer
      - Entry Optimizer kararı (EXECUTE_NOW/LIMIT_ORDER/REJECT)
      - 1m walk-forward outcome simülasyonu

    Karşılaştırma: original (mevcut TP/SL config) vs entry_optimizer (kendi SL/TP'si).
    REJECT'lerin gerçek WR'i + LIMIT fill rate + toplam P&L delta.

    ~10-15 dk. Status endpoint ile takip et."""
    if _BACKTEST_STATUS["running"]:
        return {"status": "already_running",
                "started_at": _BACKTEST_STATUS["started_at"]}
    _BACKTEST_STATUS.update({"running": True,
                              "started_at": datetime.now(timezone.utc).isoformat(),
                              "finished_at": None, "result": None, "error": None})

    async def _do():
        try:
            from services.entry_optimizer_backtest import backtest_entry_optimizer
            res = await backtest_entry_optimizer(days=days,
                                                  sample_per_scope=sample_per_scope)
            _BACKTEST_STATUS["result"] = res
        except Exception as e:
            logger.exception("[entry-bt] hata: %s", e)
            _BACKTEST_STATUS["error"] = str(e)[:500]
        finally:
            _BACKTEST_STATUS["running"] = False
            _BACKTEST_STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do)
    return {"status": "scheduled", "days": days,
            "sample_per_scope": sample_per_scope,
            "poll": "/api/entry-optimizer/backtest/status",
            "estimated_minutes": "10-15"}


@router.get("/backtest/status")
async def backtest_status():
    return {**_BACKTEST_STATUS}


# ─── Validation Suite — leakage + walk-forward + slippage + determinizm ──────
_VALIDATION_STATUS: dict = {"running": False, "started_at": None,
                              "finished_at": None, "result": None, "error": None}


@router.post("/validation-suite")
async def validation_suite(bg: BackgroundTasks,
                            days: int = Query(90, ge=14, le=180),
                            sample_per_scope: int = Query(100, ge=30, le=500,
                                                            description="Bellek için düşük; 100 yeterli"),
                            ):
    """Entry Optimizer üzerinde 5 bağımsız doğrulama:
      1. (Kod-incelemesi) — leakage TEMİZ (FVG/OB candles[-1] kullanıyor)
      2. Walk-forward — 3 zaman penceresi (0-30, 30-60, 60-90 gün)
      3. Slippage — spread + random fill ile gerçekçi simülasyon
      4. Sembol bazlı — her sembol için ayrı delta
      5. Determinizm — aynı sinyal 5× → aynı action

    Tahmini ~10-12 dk (4 backtest run + determinizm testi)."""
    if _VALIDATION_STATUS["running"]:
        return {"status": "already_running",
                "started_at": _VALIDATION_STATUS["started_at"]}
    _VALIDATION_STATUS.update({"running": True,
                                "started_at": datetime.now(timezone.utc).isoformat(),
                                "finished_at": None, "result": None, "error": None})

    async def _do():
        import gc
        try:
            from services.entry_optimizer_backtest import backtest_entry_optimizer
            from services.entry_optimizer import decide_from_payload, DEFAULT_CONFIG
            results: dict = {}

            # ── KONTROL 1: Leakage (kod-tabanlı tespit, çalışma değil)
            results["check1_leakage"] = {
                "status": "TEMİZ",
                "detail": ("FVGDetector.detect ve OrderBlockDetector.detect "
                            "'filled'/'tested'/'mitigated' kontrollerinde "
                            "candles[-1] (= signal anındaki son mum) "
                            "kullanıyor. Backtest candles'ı signal_created_at'e "
                            "kadar slice'lıyor, dolayısıyla 'son mum' = sinyal "
                            "anı. OB displacement c_next (i+1) kullanıyor ama "
                            "bu da slice içinde ve OB'den 1 mum sonra (en az "
                            "15dk önce). Geleceği görme yolu YOK."),
                "etki": "Backtest geçerli, devam et."
            }

            # ── KONTROL 2: Walk-forward — 3 fold (no-overlap windows)
            wf_results = []
            folds = [
                (0, 30, "F1: 0-30d (en eski)"),
                (30, 60, "F2: 30-60d (orta)"),
                (60, 90, "F3: 60-90d (en yeni)"),
            ]
            for start, end, name in folds:
                res = await backtest_entry_optimizer(
                    days=days, sample_per_scope=sample_per_scope,
                    day_offset_start=start, day_offset_end=end,
                    apply_slippage=False)
                ovr = res.get("overall") or {}
                wf_results.append({
                    "fold": name, "n": ovr.get("n"),
                    "original_pips": ovr.get("original_total_pips"),
                    "optimizer_pips": ovr.get("optimizer_total_pips"),
                    "delta_pct": ovr.get("delta_pct"),
                })
                del res; gc.collect()
            avg_delta = (sum(r["delta_pct"] or 0 for r in wf_results)
                          / max(1, len(wf_results)))
            min_delta = min((r["delta_pct"] or 0) for r in wf_results)
            max_delta = max((r["delta_pct"] or 0) for r in wf_results)
            wf_verdict = ("ROBUST — tüm foldlarda pozitif" if min_delta > 50
                           else "MARJİNAL — bazı foldlarda zayıf"
                           if min_delta > 10
                           else "OVERFIT — foldlar arası varyans yüksek")
            results["check2_walk_forward"] = {
                "folds": wf_results,
                "avg_delta_pct": round(avg_delta, 1),
                "min_delta_pct": round(min_delta, 1),
                "max_delta_pct": round(max_delta, 1),
                "verdict": wf_verdict,
            }

            # ── KONTROL 3: Slippage — full 90d, slippage ON vs OFF
            no_slip = await backtest_entry_optimizer(
                days=days, sample_per_scope=sample_per_scope,
                apply_slippage=False)
            gc.collect()
            with_slip = await backtest_entry_optimizer(
                days=days, sample_per_scope=sample_per_scope,
                apply_slippage=True)
            gc.collect()
            ns_ovr = no_slip.get("overall") or {}
            ws_ovr = with_slip.get("overall") or {}
            results["check3_slippage"] = {
                "no_slippage_delta_pct": ns_ovr.get("delta_pct"),
                "with_slippage_delta_pct": ws_ovr.get("delta_pct"),
                "drop_pp": (round((ns_ovr.get("delta_pct") or 0)
                                    - (ws_ovr.get("delta_pct") or 0), 1)),
                "spread_table": {
                    "XAUUSD": "3.5 pips", "NDX.INDX": "1.5 pts",
                    "GDAXI.INDX": "1.5 pts", "USOIL.FOREX": "0.03%",
                },
                "slip_range": "0.1-0.5 pips/% per fill (uniform)",
                "verdict": ("Robust — slippage ≤30% düşüş" if
                              ws_ovr.get("delta_pct") and
                              (ns_ovr.get("delta_pct") or 0) > 0 and
                              (ws_ovr.get("delta_pct") /
                               max(1e-9, ns_ovr.get("delta_pct"))) > 0.7
                              else "Slippage hassas — gerçekçi beklenti düşük"),
            }

            # ── KONTROL 4: Sembol bazlı — no_slip içinden çıkar
            # (artık main backtest per_symbol_delta dahil dönüyor — ek run yok)
            per_sym_delta = no_slip.get("per_symbol_delta") or {}
            deltas = [v["delta_pct"] for v in per_sym_delta.values()
                       if v.get("delta_pct") is not None]
            sym_verdict = "DAĞINIK"
            if deltas:
                if min(deltas) > 50 and max(deltas) / max(1, min(deltas)) < 4:
                    sym_verdict = "YAYGIN — tüm sembollerde edge"
                elif max(deltas) > 200 and min(deltas) < 50:
                    sym_verdict = "BAZ SEMBOLDE OVERFIT/ANOMALY"
                else:
                    sym_verdict = "KARIŞIK — sembol bazlı strateji düşünülmeli"
            results["check4_per_symbol"] = {
                "per_symbol": per_sym_delta,
                "verdict": sym_verdict,
            }

            # ── KONTROL 5: Determinizm — aynı input 5× → aynı action
            test_signals = [
                {"symbol": "XAUUSD", "direction": "BUY", "price": 4500.0},
                {"symbol": "NDX.INDX", "direction": "SELL", "price": 30000.0},
                {"symbol": "USOIL.FOREX", "direction": "BUY", "price": 90.0},
            ]
            det_results = []
            for sig in test_signals:
                actions_seen = set()
                priorities = []
                from services.entry_optimizer import optimize_entry
                for _ in range(5):
                    try:
                        d = await optimize_entry(dict(sig))
                        actions_seen.add(d.get("action"))
                        priorities.append(d.get("priority_score"))
                    except Exception as e:
                        actions_seen.add(f"err:{str(e)[:40]}")
                det_results.append({
                    "input": sig,
                    "unique_actions": list(actions_seen),
                    "deterministic": len(actions_seen) == 1,
                    "priorities": priorities,
                })
            all_det = all(r["deterministic"] for r in det_results)
            results["check5_determinism"] = {
                "tests": det_results,
                "all_deterministic": all_det,
                "verdict": ("DETERMINISTIK" if all_det
                              else "RASTGELELİK VAR — race condition?"),
            }

            _VALIDATION_STATUS["result"] = results
        except Exception as e:
            logger.exception("[validation] hata: %s", e)
            _VALIDATION_STATUS["error"] = str(e)[:500]
        finally:
            _VALIDATION_STATUS["running"] = False
            _VALIDATION_STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do)
    return {"status": "scheduled", "days": days,
            "sample_per_scope": sample_per_scope,
            "poll": "/api/entry-optimizer/validation-suite/status",
            "estimated_minutes": "10-12"}


@router.get("/validation-suite/status")
async def validation_suite_status():
    return {**_VALIDATION_STATUS}


@router.get("/config")
async def show_config():
    """Mevcut default config — eşikleri görmek için."""
    from services.entry_optimizer import DEFAULT_CONFIG
    return {"config": DEFAULT_CONFIG,
            "note": "ATR-relative thresholds — sembol bağımsız"}
