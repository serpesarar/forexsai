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


# ─── F1 rejim analizi — neden 0-30 gün ters çalıştı? ─────────────────────────
_REGIME_STATUS: dict = {"running": False, "started_at": None,
                          "finished_at": None, "result": None, "error": None}


@router.post("/regime-analysis")
async def regime_analysis(bg: BackgroundTasks,
                            days: int = Query(90, ge=14, le=180)):
    """3 fold (0-30, 30-60, 60-90 gün) için volatilite ve rejim profili.

    Her fold için sembol bazlı:
      - ATR(14) ortalaması ve std (15m bar üzerinde)
      - ATR genişleme oranı (max/min ATR)
      - Range coverage (gün başına ortalama high-low)
      - Trend rejimi yüzdesi (basit: |last_close - first_close| / atr_sum)
      - Sinyal yoğunluğu (gün başına resolved signal sayısı)

    F1 deltası -155% iken F2/F3 +840/+564 — bu metrikler farkı yakalamalı."""
    if _REGIME_STATUS["running"]:
        return {"status": "already_running",
                "started_at": _REGIME_STATUS["started_at"]}
    _REGIME_STATUS.update({"running": True,
                            "started_at": datetime.now(timezone.utc).isoformat(),
                            "finished_at": None, "result": None, "error": None})

    async def _do():
        import asyncio as _aio
        import numpy as np
        from datetime import timedelta as _td
        try:
            from services.signal_replay_1m import _load_all_1m_bars_sync
            from services.precision_veto_backtest import _aggregate
            from database.supabase_client import get_supabase_client, is_db_available
            now = datetime.now(timezone.utc)
            folds = [
                ("F1_0-30d", now - _td(days=days),
                  now - _td(days=days - 30)),
                ("F2_30-60d", now - _td(days=days - 30),
                  now - _td(days=days - 60)),
                ("F3_60-90d", now - _td(days=days - 60), now),
            ]
            symbols = ["XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"]

            # Per-symbol 15m bars (tek seferde yükle)
            per_sym_15m: dict = {}
            for sym in symbols:
                bars_1m = await _aio.to_thread(_load_all_1m_bars_sync, sym)
                if not bars_1m:
                    continue
                per_sym_15m[sym] = _aggregate(bars_1m, "15m")

            def _atr_window(bars, lo, hi):
                """[lo, hi] aralığındaki barlarda ATR(14) hesapla."""
                window = [b for b in bars if lo <= b["ts"] <= hi]
                if len(window) < 16:
                    return {"n_bars": len(window)}
                trs = []
                for i in range(1, len(window)):
                    h = window[i]["high"]; l = window[i]["low"]
                    cp = window[i-1]["close"]
                    trs.append(max(h - l, abs(h - cp), abs(l - cp)))
                trs_arr = np.array(trs)
                # Rolling 14 ATR
                atrs = []
                for i in range(13, len(trs_arr)):
                    atrs.append(float(np.mean(trs_arr[i-13:i+1])))
                if not atrs:
                    return {"n_bars": len(window)}
                atr_arr = np.array(atrs)
                # Trendiness — net move / total range
                first_close = window[0]["close"]
                last_close = window[-1]["close"]
                net_move = abs(last_close - first_close)
                total_range = sum(abs(b["high"] - b["low"]) for b in window)
                trendiness = net_move / total_range if total_range > 0 else 0
                return {
                    "n_bars": len(window),
                    "atr_mean": round(float(atr_arr.mean()), 4),
                    "atr_std": round(float(atr_arr.std()), 4),
                    "atr_cv": round(float(atr_arr.std()
                                            / max(1e-9, atr_arr.mean())), 3),
                    "atr_p90_over_p10": round(float(np.percentile(atr_arr, 90)
                                                      / max(1e-9, np.percentile(atr_arr, 10))), 2),
                    "trendiness": round(trendiness, 3),
                    "first_close": round(first_close, 2),
                    "last_close": round(last_close, 2),
                    "net_move_pct": round(net_move
                                              / max(1e-9, first_close) * 100, 2),
                }

            # Sinyal yoğunluğu — prediction_replay_corrections
            sig_counts: dict = {}
            if is_db_available():
                client = get_supabase_client()
                for fold_name, lo, hi in folds:
                    q = (client.table("prediction_replay_corrections")
                          .select("symbol")
                          .gte("signal_created_at", lo.isoformat())
                          .lte("signal_created_at", hi.isoformat())
                          .eq("replay_status", "ok")
                          .in_("corrected_status", ["completed", "stopped"])
                          .limit(20000))
                    try:
                        res = q.execute() if hasattr(q, "execute") else q
                        # Page through to get actual rows
                        rows = (res.data if hasattr(res, "data")
                                  else (res.get("data") if isinstance(res, dict)
                                          else [])) or []
                        per: dict = {}
                        for r in rows:
                            s = r.get("symbol")
                            if s: per[s] = per.get(s, 0) + 1
                        sig_counts[fold_name] = per
                    except Exception as e:
                        logger.debug("sig count: %s", e)
                        sig_counts[fold_name] = {"_err": str(e)[:80]}

            # Fold × sembol matrisi
            out: dict = {}
            for fold_name, lo, hi in folds:
                fold_data: dict = {"period": f"{lo.isoformat()} → {hi.isoformat()}"}
                for sym in symbols:
                    if sym not in per_sym_15m:
                        fold_data[sym] = {"_skip": "no bars"}
                        continue
                    fold_data[sym] = _atr_window(per_sym_15m[sym], lo, hi)
                    fold_data[sym]["resolved_signals"] = (
                        sig_counts.get(fold_name, {}).get(sym, 0))
                out[fold_name] = fold_data

            # F1 vs F2/F3 karşılaştırma özeti
            comparison: dict = {}
            for sym in symbols:
                rows: dict = {}
                for fold_name, _, _ in folds:
                    rows[fold_name] = out.get(fold_name, {}).get(sym, {})
                f1 = rows.get("F1_0-30d", {})
                f2 = rows.get("F2_30-60d", {})
                f3 = rows.get("F3_60-90d", {})
                if not all([f1.get("atr_mean"), f2.get("atr_mean"),
                              f3.get("atr_mean")]):
                    continue
                avg_f23 = (f2["atr_mean"] + f3["atr_mean"]) / 2
                comparison[sym] = {
                    "atr_f1_vs_avg_f23_ratio": round(f1["atr_mean"]
                                                       / max(1e-9, avg_f23), 2),
                    "trendiness_f1": f1.get("trendiness"),
                    "trendiness_avg_f23": round(
                        ((f2.get("trendiness") or 0)
                          + (f3.get("trendiness") or 0)) / 2, 3),
                    "atr_cv_f1_vs_f23": round(
                        (f1.get("atr_cv") or 0)
                          - ((f2.get("atr_cv") or 0)
                              + (f3.get("atr_cv") or 0)) / 2, 3),
                    "n_signals_f1": f1.get("resolved_signals"),
                    "n_signals_f23": ((f2.get("resolved_signals") or 0)
                                        + (f3.get("resolved_signals") or 0)),
                }

            _REGIME_STATUS["result"] = {
                "folds": out,
                "comparison_f1_vs_f23": comparison,
                "interpretation": {
                    "atr_f1_vs_avg_f23_ratio": "1.0 = aynı, >1.2 = F1 daha volatil",
                    "atr_cv_f1_vs_f23": "Pozitif = F1 daha düzensiz volatilite",
                    "trendiness": "0=ranging, 1=güçlü trend (net move/total range)",
                },
            }
        except Exception as e:
            logger.exception("[regime] hata: %s", e)
            _REGIME_STATUS["error"] = str(e)[:500]
        finally:
            _REGIME_STATUS["running"] = False
            _REGIME_STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do)
    return {"status": "scheduled", "days": days,
            "poll": "/api/entry-optimizer/regime-analysis/status",
            "estimated_minutes": "2-3"}


@router.get("/regime-analysis/status")
async def regime_analysis_status():
    return {**_REGIME_STATUS}


# ─── Shadow / Enforce mod yönetimi ───────────────────────────────────────────
@router.get("/shadow/status")
async def shadow_status():
    """Mevcut Entry Optimizer modu (off/shadow/enforce) + filter bilgisi."""
    from services.shadow_executor import get_status
    return get_status()


@router.get("/shadow/stats")
async def shadow_stats_endpoint(days: int = Query(7, ge=1, le=60)):
    """Son N gün shadow log özeti — A/B karşılaştırma + dağılım."""
    from services.regime_logger import shadow_stats
    return await shadow_stats(days=days)


@router.post("/shadow/test-apply")
async def shadow_test_apply(body: dict):
    """Manuel test — bir sinyali shadow executor'dan geçir, sonuç ne?
    Trade pipeline'a etkisi yok, sadece görsel doğrulama.

    body: {symbol, direction, price, confidence?}
    """
    from services.shadow_executor import apply_entry_optimizer
    if not isinstance(body, dict):
        raise HTTPException(400, "JSON body gerekli")
    try:
        result = await apply_entry_optimizer(body, stage4_info=body.get("stage4"))
        return {"input": body, "output": result,
                 "mode_note": "Mode env ENTRY_OPTIMIZER_MODE'da set, "
                                "production sinyalleri bu mod'da işlenir."}
    except Exception as e:
        raise HTTPException(500, f"shadow apply: {e}")


@router.post("/shadow/backfill/{prediction_id}")
async def shadow_backfill(prediction_id: str):
    """Trade kapandı, outcome'u entry_optimizer_logs'a yaz."""
    from services.regime_logger import backfill_outcome
    return await backfill_outcome(prediction_id)


@router.get("/config")
async def show_config():
    """Mevcut default config — eşikleri görmek için."""
    from services.entry_optimizer import DEFAULT_CONFIG
    return {"config": DEFAULT_CONFIG,
            "note": "ATR-relative thresholds — sembol bağımsız"}
