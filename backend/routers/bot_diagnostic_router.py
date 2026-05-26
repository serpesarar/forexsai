"""
Bot vs Sistem diagnostic — "backend %80 WR diyor, MT5 zarar ediyor"
boşluğunu kapamak için tek-shot rapor.

Sorduğu sorular:
1. XAUUSD ve USOIL için en yüksek WR'li model_type hangisi?
2. Bot config'i hangi modelleri / scope'ları kullanıyor?
3. Bot config'i ile backend WR arasında uçurum var mı?
4. Eğer bot bir model'i kullanmıyorsa, neden? (sembol eksik mi, scope yanlış mı?)

POST/GET /api/bot-diagnostic/report?days=30 → tek paket rapor.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bot-diagnostic", tags=["Bot Diagnostic"])


@router.get("/report")
async def report(days: int = Query(30, ge=7, le=180),
                  symbols: str = Query("XAUUSD,USOIL.FOREX,NDX.INDX,GDAXI.INDX")):
    """Bot vs Sistem performans karşılaştırması.

    Her sembol-model çifti için son N gün:
      - resolved (completed + stopped) sayısı
      - WR
      - TP1/2/3/4 hit oranları
      - Spread maliyeti tahmini (sembol bazlı)
      - Bot bu kombinasyonu KULLANIYOR MU
    """
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "db_unavailable"}
    client = get_supabase_client()

    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # ── prediction_logs üzerinden sembol-model breakdown ────────────────────
    rows: list[dict] = []
    offset = 0
    PAGE = 1000
    while True:
        q = (client.table("prediction_logs").select(
            "symbol,model_type,strategy,status,ml_direction,"
            "ml_entry_price,exit_price,highest_profit_pips,"
            "lowest_drawdown_pips,resolution_reason")
             .gte("created_at", since)
             .in_("symbol", sym_list)
             .in_("status", ["completed", "stopped", "expired"])
             .range(offset, offset + PAGE - 1))
        res = q.execute() if hasattr(q, "execute") else q
        page = (res.data if hasattr(res, "data")
                  else (res.get("data") if isinstance(res, dict) else [])) or []
        if not page: break
        rows.extend(page)
        if len(page) < PAGE: break
        offset += PAGE
        if offset > 50000: break  # safeguard

    # market_closed_invalid'i ele
    rows = [r for r in rows
             if r.get("resolution_reason") != "market_closed_invalid"]

    # Aggregate per (symbol, model_type)
    from collections import defaultdict
    agg: dict = defaultdict(lambda: {
        "n_total": 0, "completed": 0, "stopped": 0, "expired": 0,
        "total_profit_pips": 0.0, "total_drawdown_pips": 0.0,
    })
    for r in rows:
        sym = r.get("symbol")
        m = r.get("model_type") or "unknown"
        st = r.get("status")
        key = (sym, m)
        agg[key]["n_total"] += 1
        if st == "completed":
            agg[key]["completed"] += 1
        elif st == "stopped":
            agg[key]["stopped"] += 1
        else:
            agg[key]["expired"] += 1
        try:
            agg[key]["total_profit_pips"] += float(r.get("highest_profit_pips") or 0)
            agg[key]["total_drawdown_pips"] += float(r.get("lowest_drawdown_pips") or 0)
        except (ValueError, TypeError):
            pass

    # Compute WR ve sırala
    breakdown: list[dict] = []
    for (sym, m), s in agg.items():
        resolved = s["completed"] + s["stopped"]
        if resolved < 5:  # düşük sample skip
            continue
        wr = round(100 * s["completed"] / resolved, 1) if resolved else 0
        avg_mfe = round(s["total_profit_pips"] / s["n_total"], 2) if s["n_total"] else 0
        avg_mae = round(s["total_drawdown_pips"] / s["n_total"], 2) if s["n_total"] else 0
        breakdown.append({
            "symbol": sym, "model_type": m,
            "n_total": s["n_total"], "resolved": resolved,
            "completed": s["completed"], "stopped": s["stopped"],
            "expired": s["expired"],
            "win_rate_pct": wr,
            "avg_mfe_pips": avg_mfe,    # max favorable excursion
            "avg_mae_pips": avg_mae,    # max adverse excursion
        })

    # Sembol başına en iyi 5 model
    by_sym: dict = defaultdict(list)
    for row in breakdown:
        by_sym[row["symbol"]].append(row)
    top_per_sym: dict = {}
    for sym, lst in by_sym.items():
        lst.sort(key=lambda x: (-x["win_rate_pct"], -x["resolved"]))
        top_per_sym[sym] = lst[:8]

    # ── Bot config karşılaştırması ──────────────────────────────────────────
    # yeni deneme/config.py local — repo'da yok. Hard-coded olarak
    # biliyoruz (kullanıcı paylaştı):
    BOT_CONFIG = {
        "NDX.INDX:BUY":     {"models": ["pulse1", "pulse2", "pulse3"],
                              "tp": 80, "sl": 110, "is_pct": False},
        "GDAXI.INDX:SELL":  {"models": ["pulse1", "pulse2", "pulse3"],
                              "tp": 67, "sl": 119, "is_pct": False},
        "USOIL.FOREX:SELL": {"models": ["pulse1", "pulse2", "pulse3"],
                              "tp": 1.04, "sl": 1.49, "is_pct": True},
    }

    # Gap analysis: her sembol için "bot kullanıyor mu" kontrolü
    gap_analysis: dict = {}
    for sym in sym_list:
        sym_data = top_per_sym.get(sym, [])
        # Bot bu sembolü ne için açıyor (yön)?
        bot_scopes = {k: v for k, v in BOT_CONFIG.items() if k.startswith(sym + ":")}
        bot_directions = [k.split(":")[1] for k in bot_scopes.keys()]
        bot_models = []
        for v in bot_scopes.values():
            bot_models.extend(v["models"])
        bot_models = sorted(set(bot_models))

        # En iyi modeller bot tarafından kullanılıyor mu?
        best_models = [r["model_type"] for r in sym_data[:5]]
        unused_best = [m for m in best_models if m not in bot_models]
        # Yön — bot yön mü açıyor sembolde?

        gap_analysis[sym] = {
            "in_bot": bool(bot_scopes),
            "bot_directions": bot_directions or ["NONE"],
            "bot_models": bot_models or ["NONE"],
            "bot_tp_sl": ({k: {"tp": v["tp"], "sl": v["sl"], "is_pct": v["is_pct"]}
                            for k, v in bot_scopes.items()}
                           if bot_scopes else None),
            "system_top_models": best_models,
            "best_models_NOT_in_bot": unused_best,
            "note": (
                "❌ SEMBOL BOT'TA YOK — backend WR'i ne olursa olsun MT5'te işlem açılmaz."
                if not bot_scopes
                else f"⚠ Bot {bot_models} kullanıyor, sistemin en iyi modelleri {best_models[:3]} — "
                f"bot {len(unused_best)} adet daha iyi modeli kullanmıyor."
                if unused_best
                else "✓ Bot sistemin en iyi modellerini kullanıyor."
            ),
        }

    # ── Spread / TP-SL maliyet analizi (USOIL/XAU için kritik) ──────────────
    spread_table = {
        "XAUUSD": {"spread_pips": 3.5, "pip_value_usd": 1.0,
                    "note": "spread = 3.5$ / trade"},
        "USOIL.FOREX": {"spread_pct": 0.03,
                         "note": "spread = 0.03% (entry'ye orantılı)"},
        "NDX.INDX": {"spread_pips": 1.5,
                      "note": "spread = 1.5 puan"},
        "GDAXI.INDX": {"spread_pips": 1.5,
                        "note": "spread = 1.5 puan"},
    }

    # USOIL SELL özelinde expectancy analizi (kullanıcı asıl bunu sordu)
    usoil_sell_analysis = None
    for r in by_sym.get("USOIL.FOREX", []):
        if r["model_type"] in ("pulse1", "pulse2", "pulse3"):
            # Beklenti hesabı: 0.03% spread + TP=1.04% / SL=1.49%
            wr_pct = r["win_rate_pct"]
            wr_frac = wr_pct / 100
            tp = 1.04
            sl = 1.49
            spread = 0.03
            gross_ev = wr_frac * tp - (1 - wr_frac) * sl
            net_ev = gross_ev - spread
            if usoil_sell_analysis is None:
                usoil_sell_analysis = {"per_model": []}
            usoil_sell_analysis["per_model"].append({
                "model": r["model_type"],
                "wr_pct": wr_pct,
                "resolved": r["resolved"],
                "gross_ev_per_trade_pct": round(gross_ev, 3),
                "net_ev_after_spread_pct": round(net_ev, 3),
                "verdict": ("KAR" if net_ev > 0 else "ZARAR" if net_ev < -0.05 else "BREAK-EVEN"),
            })

    return {
        "status": "ok",
        "period_days": days,
        "scanned_rows": len(rows),
        "top_models_per_symbol": top_per_sym,
        "bot_gap_analysis": gap_analysis,
        "spread_costs": spread_table,
        "usoil_sell_expectancy": usoil_sell_analysis,
        "interpretation": {
            "neden_backend_basari_MT5_zarar_olabilir": [
                "1. Bot sembolde IŞLEM AÇMIYOR (XAUUSD bot config'inde YOK)",
                "2. Bot YANLIŞ MODELI okuyor (pulse vs en iyi olabilecek emel/ml/ai_panel)",
                "3. Bot'un TP/SL CONFIG'i backend'den farklı (R:R'i bozar)",
                "4. Spread + slippage backend WR'inden yenir (USOIL %0.03)",
                "5. Bot'un emir açma TIMING'i farklı (signal +1-15dk gecikme)",
                "6. Bot ENTRY'i market tick'i, backend ml_entry_price'ı kullanır",
            ],
            "ne_yapmali": [
                "Bot config'ine XAUUSD scope ekle (kullanıcı asıl bunu istiyor)",
                "Her scope için 'system_top_models' listesindeki en iyi modeli ekle",
                "TP/SL'i backend'in target_config'iyle hizala (veya bot endpoint'inden al)",
            ],
        },
    }
