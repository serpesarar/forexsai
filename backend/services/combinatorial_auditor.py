"""
Combinatorial Signal Auditor & Confluence Optimizer
────────────────────────────────────────────────────
Mines prediction logs to discover high-performing model combinations
under specific market regimes, symbols, and session hours.
Updates the `meta_combination_stats` table to dynamically guide the Meta-Engine.
"""
from __future__ import annotations

import logging
import json
import time
from datetime import datetime, timedelta, timezone
from itertools import combinations
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

from database.supabase_client import get_supabase_client, is_db_available
from utils.safe_supabase import safe_get_data, safe_get_error

logger = logging.getLogger(__name__)

# Fallback soft-dependency imports for premium packages
OPTUNA_AVAILABLE = False
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    logger.info("Optuna not installed. Using native Combinatorial Permutation Evaluator fallback.")


class CombinatorialAuditor:
    """Mines signal metrics and optimizes multi-model confluence weights."""

    def __init__(self):
        self.client = get_supabase_client() if is_db_available() else None

    async def fetch_signal_matrix(self, days: int = 45) -> Optional[pd.DataFrame]:
        """Fetch historical completed prediction logs and build a pandas DataFrame."""
        if not self.client:
            logger.warning("Supabase client unavailable. Cannot fetch signal matrix.")
            return None

        try:
            # Calculate date range
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")
            
            # Fetch completed / stopped signals.
            # PostgREST caps each response at the server max-rows (1000), so a
            # single .limit(5000) silently truncates. Paginate with .range() to
            # cover the full window (same pattern as the mt5_trades loop below).
            cols = ("id, symbol, timeframe, ml_direction, ml_confidence, ml_entry_price, "
                    "model_type, status, targets_hit, highest_profit_pips, "
                    "lowest_drawdown_pips, exit_price, exit_time, stop_loss_pips, "
                    "targets, created_at, strategy, factors")
            data = []
            p_off, p_chunk, p_cap = 0, 1000, 60000
            while p_off < p_cap:
                page_res = self.client.table("prediction_logs") \
                    .select(cols) \
                    .neq("status", "active") \
                    .gte("created_at", cutoff_date) \
                    .order("created_at", desc=False) \
                    .range(p_off, p_off + p_chunk - 1) \
                    .execute()
                page = safe_get_data(page_res) or []
                data.extend(page)
                if len(page) < p_chunk:
                    break
                p_off += p_chunk
            if not data:
                logger.info("No completed signals found in the selected range.")
                return None

            # Honest 1m ground truth: attach replay corrections so the
            # simulated-fallback win (below) uses the 1m verdict, not the
            # inflated 5m-candle status label.
            from services.signal_analytics import attach_corrections
            attach_corrections(data, self.client)

            # Fetch matched mt5_trades to align with prediction_logs in memory (chunk-paginated)
            mt5_map = {}
            try:
                offset = 0
                chunk_size = 1000
                while True:
                    mt5_res = self.client.table("mt5_trades") \
                        .select("matched_prediction_id, price, profit, volume, direction, deal_time") \
                        .range(offset, offset + chunk_size - 1) \
                        .execute()
                    mt5_deals = safe_get_data(mt5_res) or []
                    for d in mt5_deals:
                        pred_id = d.get("matched_prediction_id")
                        if pred_id:
                            mt5_map[pred_id] = d
                    if len(mt5_deals) < chunk_size:
                        break
                    offset += chunk_size
                logger.info(f"Combinatorial Auditor: Loaded {len(mt5_map)} unique matched MT5 deals.")
            except Exception as mt5_err:
                logger.warning(f"Could not load matched mt5_trades: {mt5_err}")

            # Parse signal factors/JSON
            parsed_rows = []
            
            # Count how many signals have matched deals to dynamically filter simulated data
            has_real_count = sum(1 for s in data if s.get("id") in mt5_map)
            logger.info(f"Combinatorial Auditor: Identified {has_real_count} real-world matched trades in this window.")
            
            for s in data:
                factors = s.get("factors") or {}
                if isinstance(factors, str):
                    try:
                        factors = json.loads(factors)
                    except Exception:
                        factors = {}
                
                # Check if we have a matched MT5 deal for this signal
                matched_deal = mt5_map.get(s["id"])
                real_entry = float(s.get("ml_entry_price") or 0.0)
                real_exit = float(s.get("exit_price") or 0.0)
                real_pnl = 0.0
                slippage = 0.0
                has_real = False
                
                if matched_deal:
                    has_real = True
                    real_entry = float(matched_deal.get("price") or real_entry)
                    # Exit price from prediction log or the deal price if available
                    real_exit = float(s.get("exit_price") or real_entry)
                    
                    # Calculate real pips PnL
                    def _pips_diff(entry, exit, sym, direction):
                        diff = (exit - entry) if direction == "BUY" else (entry - exit)
                        sym_upper = sym.upper()
                        if "XAUUSD" in sym_upper:
                            return diff / 0.1
                        if "USOIL" in sym_upper or "CL" in sym_upper:
                            return diff / 0.01
                        return diff
                    
                    real_pnl = _pips_diff(real_entry, real_exit, s.get("symbol", ""), (s.get("ml_direction") or "HOLD").upper())
                    
                    # Calculate entry slippage in pips
                    sig_entry = float(s.get("ml_entry_price") or real_entry)
                    slippage = abs(_pips_diff(sig_entry, real_entry, s.get("symbol", ""), (s.get("ml_direction") or "HOLD").upper()))

                # Expose specific indicators as columns
                row = {
                    "id": s.get("id"),
                    "symbol": s.get("symbol"),
                    "timeframe": s.get("timeframe"),
                    "direction": (s.get("ml_direction") or "HOLD").upper(),
                    "confidence": s.get("ml_confidence", 0),
                    "model_type": s.get("model_type"),
                    "status": s.get("status"),
                    "highest_profit": float(s.get("highest_profit_pips") or 0.0),
                    "lowest_drawdown": float(s.get("lowest_drawdown_pips") or 0.0),
                    "created_at": s.get("created_at"),
                    # Real MT5 values
                    "real_entry": round(real_entry, 4),
                    "real_exit": round(real_exit, 4),
                    "real_pnl": round(real_pnl, 2),
                    "slippage": round(slippage, 2),
                    # Technical snapshot at entry
                    "rsi": float(factors.get("rsi_14") or factors.get("rsi") or 50.0),
                    "adx": float(factors.get("adx") or 20.0),
                    "atr": float(factors.get("atr_14") or factors.get("atr") or 0.0),
                    "regime": str(factors.get("regime") or "UNKNOWN").upper(),
                    "source_combo": str(factors.get("source_combo") or "").strip(),
                }
                
                # Ground truth outcome:
                # If we have a matched MT5 deal, use its profit/pips. Otherwise, fallback to simulation (win = completed)
                if has_real:
                    row["is_win"] = real_pnl > 0.0
                    row["pnl_score"] = real_pnl
                else:
                    # Prefer the honest 1m replay verdict; fall back to the 5m
                    # status label only when no correction is attached.
                    corrected_status = s.get("corrected_status")
                    replay_ok = (s.get("corrected_replay_status") or "ok") == "ok"
                    if corrected_status in ("completed", "stopped", "expired") and replay_ok:
                        row["is_win"] = corrected_status == "completed"
                    else:
                        row["is_win"] = s.get("status") == "completed"
                    # Fallback profit estimate: win gets highest_profit, loss gets lowest_drawdown
                    if row["is_win"]:
                        row["pnl_score"] = row["highest_profit"]
                    else:
                        row["pnl_score"] = row["lowest_drawdown"]

                # Parse created_at hour for session classification
                try:
                    dt = datetime.fromisoformat(str(s.get("created_at")).replace("Z", "+00:00"))
                    hour = dt.astimezone(timezone.utc).hour
                    if 13 <= hour < 21:
                        row["session"] = "US"
                    elif 8 <= hour < 13:
                        row["session"] = "LONDON"
                    elif 0 <= hour < 8:
                        row["session"] = "ASIA"
                    else:
                        row["session"] = "CLOSED"
                except Exception:
                    row["session"] = "UNKNOWN"

                # Dynamic Truth Alignment:
                # If we have real matched trades in this window, we skip simulated rows
                # to base the leaderboard and heatmaps entirely on actual broker performance!
                if has_real_count > 0 and not has_real:
                    continue

                parsed_rows.append(row)

            return pd.DataFrame(parsed_rows)

        except Exception as e:
            logger.error(f"Error building signal matrix: {e}", exc_info=True)
            return None

    def mine_combination_rules(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyze multi-model combinations and group by symbol, regime, and session
        to identify highly profitable rules.
        """
        results = []
        if df.empty:
            return results

        # Available model types in prediction logs
        # E.g. individual models: ml, pulse1, pulse2, pulse3, emel, smc
        # Source combos look like "ml+pulse3+emel"
        
        # We will parse source combos and group by combination permutations
        unique_symbols = df["symbol"].unique()
        unique_regimes = df["regime"].unique()
        unique_sessions = df["session"].unique()

        for symbol in unique_symbols:
            df_sym = df[df["symbol"] == symbol]
            if df_sym.empty:
                continue

            for regime in unique_regimes:
                df_reg = df_sym[df_sym["regime"] == regime]
                if df_reg.empty:
                    df_reg = df_sym  # Fallback to symbol-only if regime is empty

                # Extract and aggregate combinations
                combos_grouped = df_reg.groupby("source_combo")
                for combo_key, group in combos_grouped:
                    combo_key = str(combo_key).strip()
                    if not combo_key or combo_key == "nan":
                        continue

                    total = len(group)
                    wins = int(group["is_win"].sum())
                    losses = total - wins
                    win_rate = float(wins / total) if total > 0 else 0.0
                    
                    profits = group[group["pnl_score"] > 0]["pnl_score"]
                    losses_pips = group[group["pnl_score"] <= 0]["pnl_score"].abs()
                    
                    avg_prof = float(profits.mean()) if not profits.empty else 0.0
                    avg_loss = float(losses_pips.mean()) if not losses_pips.empty else 0.0
                    
                    total_prof = profits.sum()
                    total_loss = losses_pips.sum()
                    
                    profit_factor = float(total_prof / total_loss) if total_loss > 0 else (float(total_prof) if total_prof > 0 else 1.0)
                    expectancy = (win_rate * avg_prof) - ((1.0 - win_rate) * avg_loss)

                    results.append({
                        "combo_key": combo_key,
                        "symbol": symbol,
                        "regime": regime,
                        "total_signals": total,
                        "wins": wins,
                        "losses": losses,
                        "win_rate": round(win_rate, 4),
                        "profit_factor": round(profit_factor, 2),
                        "expectancy": round(expectancy, 2),
                        "avg_profit_pips": round(avg_prof, 1),
                        "avg_loss_pips": round(avg_loss, 1),
                    })

        return results

    async def sync_combination_stats(self, stats: List[Dict[str, Any]]):
        """Sync mined combination stats to the database table `meta_combination_stats`."""
        if not self.client or not stats:
            logger.warning("Database unavailable or no stats to sync.")
            return

        try:
            # We insert/update stats per combination
            for stat in stats:
                upsert_data = {
                    "combo_key": stat["combo_key"],
                    "symbol": stat["symbol"],
                    "regime": stat["regime"],
                    "total_signals": stat["total_signals"],
                    "wins": stat["wins"],
                    "losses": stat["losses"],
                    "win_rate": stat["win_rate"],
                    "profit_factor": stat["profit_factor"],
                    "expectancy": stat["expectancy"],
                    "avg_profit_pips": stat["avg_profit_pips"],
                    "avg_loss_pips": stat["avg_loss_pips"],
                    "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                }
                
                # Sync using robust select-and-update/insert pattern to bypass missing composite unique constraints
                try:
                    res = self.client.table("meta_combination_stats") \
                        .select("id") \
                        .eq("combo_key", stat["combo_key"]) \
                        .eq("symbol", stat["symbol"]) \
                        .eq("regime", stat["regime"]) \
                        .execute()
                    
                    existing = safe_get_data(res) or []
                    if existing:
                        record_id = existing[0]["id"]
                        # Chaining .eq() BEFORE calling .update() is mandatory in this custom Supabase wrapper
                        self.client.table("meta_combination_stats") \
                            .eq("id", record_id) \
                            .update(upsert_data)
                    else:
                        self.client.table("meta_combination_stats").insert(upsert_data)
                except Exception as db_err:
                    logger.warning(f"Failed to sync combination stats for {stat['combo_key']} - {stat['symbol']} - {stat['regime']}: {db_err}")
            
            logger.info(f"Successfully synced {len(stats)} combination stats with Supabase.")
        except Exception as e:
            logger.error(f"Error syncing combination stats: {e}")

    async def optimize_ensemble_weights(self, symbol: str) -> Dict[str, float]:
        """
        Uses native search or Optuna (if available) to calculate optimal
        weights for each of the 6 models to maximize win_rate & profit_factor.
        """
        df = await self.fetch_signal_matrix(days=30)
        if df is None or df.empty:
            logger.info(f"Insufficient data to optimize weights for {symbol}.")
            return {}

        df_sym = df[df["symbol"] == symbol]
        if len(df_sym) < 10:
            logger.info(f"Not enough recent signals ({len(df_sym)}) to calibrate weights.")
            return {}

        # Optuna premium optimization
        if OPTUNA_AVAILABLE:
            try:
                weights = self._run_optuna_optimization(df_sym)
                logger.info(f"Optuna weights optimized for {symbol}: {weights}")
                return weights
            except Exception as e:
                logger.error(f"Optuna optimization failed: {e}. Falling back to native optimizer.")

        # Native greedy permutation evaluator fallback
        return self._run_native_optimization(df_sym)

    def _run_native_optimization(self, df: pd.DataFrame) -> Dict[str, float]:
        """Native greedy weight optimizer to find best weights among 6 models."""
        models = ["ml", "pulse1", "pulse2", "pulse3", "emel", "smc"]
        best_weights = {m: 0.15 for m in models}
        best_score = -9999.0

        # Run heuristic search: calibrate each weight iteratively
        for m in models:
            for w in [0.0, 0.1, 0.2, 0.3, 0.4]:
                temp_weights = dict(best_weights)
                temp_weights[m] = w
                
                # Normalize weights
                w_sum = sum(temp_weights.values())
                if w_sum > 0:
                    temp_weights = {k: v / w_sum for k, v in temp_weights.items()}

                score = self._evaluate_weight_matrix(df, temp_weights)
                if score > best_score:
                    best_score = score
                    best_weights = temp_weights

        return best_weights

    def _run_optuna_optimization(self, df: pd.DataFrame) -> Dict[str, float]:
        """Optuna integration for multi-objective hyperparameter optimization."""
        models = ["ml", "pulse1", "pulse2", "pulse3", "emel", "smc"]

        def objective(trial):
            # Suggest weights between 0.0 and 1.0
            trial_weights = {m: trial.suggest_float(m, 0.0, 1.0) for m in models}
            
            # Normalize weights
            w_sum = sum(trial_weights.values())
            if w_sum == 0:
                return -100.0
            trial_weights = {k: v / w_sum for k, v in trial_weights.items()}

            # Evaluate score
            return self._evaluate_weight_matrix(df, trial_weights)

        # Silent Optuna search
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=50)

        best_params = study.best_params
        best_sum = sum(best_params.values())
        if best_sum > 0:
            return {k: v / best_sum for k, v in best_params.items()}
        return {m: 1.0 / len(models) for m in models}

    def _evaluate_weight_matrix(self, df: pd.DataFrame, weights: Dict[str, float]) -> float:
        """Evaluate weight matrix score using Expectancy and Profit Factor."""
        total_pnl = 0.0
        wins = 0
        total_signals = 0

        # Standard score calculation based on model confidence fusion simulation
        for _, row in df.iterrows():
            source_combo = str(row["source_combo"]).split("+")
            direction = row["direction"]
            
            # Calculate composite confidence
            agreeing_weight = 0.0
            disagreeing_weight = 0.0
            
            for model in source_combo:
                model = model.strip()
                if not model:
                    continue
                weight = weights.get(model, 0.1)
                agreeing_weight += weight

            # Consensus requirement: at least 40% of weights must agree
            if agreeing_weight >= 0.4:
                total_signals += 1
                pnl = float(row["pnl_score"])
                total_pnl += pnl
                if pnl > 0:
                    wins += 1

        if total_signals == 0:
            return -1000.0

        win_rate = wins / total_signals
        expectancy = total_pnl / total_signals
        
        # Fitness score = Expectancy + WinRate penalty for too few signals
        fitness = expectancy + (win_rate * 10)
        if total_signals < 5:
            fitness -= (5 - total_signals) * 5.0  # Penalize low volume

        return fitness


async def run_audit_cycle() -> Dict[str, Any]:
    """Background task hook to audit all signals and update meta stats."""
    auditor = CombinatorialAuditor()
    df = await auditor.fetch_signal_matrix(days=45)
    
    if df is None or df.empty:
        return {"success": False, "reason": "Empty signal matrix"}

    stats = auditor.mine_combination_rules(df)
    if stats:
        await auditor.sync_combination_stats(stats)
        
    return {
        "success": True,
        "total_signals_audited": len(df),
        "unique_combinations_mined": len(stats) if stats else 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
