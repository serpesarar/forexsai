#!/usr/bin/env python
"""
ForexSAI - Offline Combinatorial Backtester & Optimizer CLI
────────────────────────────────────────────────────────────
Executes combinatorial permutations backtesting over prediction logs,
calculates optimal model weights, and updates the DB stats.

Usage:
  python backend/scripts/run_offline_backtest.py --days 60 --symbol NDX.INDX
"""
from __future__ import annotations

import os
import sys
import argparse
import asyncio
import logging

# Setup python path to import backend modules properly
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

# Initialize basic logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("combinatorial_backtester")


async def main():
    parser = argparse.ArgumentParser(description="ForexSAI Combinatorial Optimizer CLI")
    parser.add_argument("--days", type=int, default=45, help="Number of historical days to backtest")
    parser.add_argument("--symbol", type=str, default=None, help="Specific symbol to optimize (e.g. NDX.INDX)")
    parser.add_argument("--optimize-weights", action="store_true", help="Calibrate and optimize ensemble weights via Optuna")
    args = parser.parse_args()

    logger.info(f"Starting Offline Combinatorial Backtest | Days: {args.days} | Target Symbol: {args.symbol or 'ALL'}")

    try:
        from services.combinatorial_auditor import CombinatorialAuditor
        auditor = CombinatorialAuditor()
        
        # 1. Fetch signal logs matrix
        logger.info("Fetching signal logs from database...")
        df = await auditor.fetch_signal_matrix(days=args.days)
        
        if df is None or df.empty:
            logger.error("Signal matrix is empty. Ensure prediction_logs table has historical data.")
            sys.exit(1)

        logger.info(f"Loaded {len(df)} historical completed signals for analysis.")

        # Filter by symbol if requested
        if args.symbol:
            df = df[df["symbol"] == args.symbol]
            logger.info(f"Filtered signal logs to {len(df)} rows for {args.symbol}.")

        # 2. Mine combinations & calculate success rates
        logger.info("Analyzing model combination permutations...")
        stats = auditor.mine_combination_rules(df)
        
        if not stats:
            logger.warning("No combination statistics mined. Ensure signals have 'source_combo' populated in factors.")
        else:
            logger.info(f"Successfully mined {len(stats)} unique model/regime combination rules.")
            
            # 3. Sync to Supabase meta_combination_stats
            logger.info("Upserting mined combination stats back to database...")
            await auditor.sync_combination_stats(stats)
            logger.info("Upsert completed successfully.")

        # 4. Calibration of ensemble weights (Optional)
        if args.optimize_weights:
            symbols = [args.symbol] if args.symbol else ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]
            logger.info("Starting weight matrix optimization for ensemble models...")
            
            for sym in symbols:
                logger.info(f"Calibrating weights for {sym}...")
                optimal_weights = await auditor.optimize_ensemble_weights(sym)
                if optimal_weights:
                    logger.info(f"Optimal weights calibrated for {sym}:")
                    for k, v in optimal_weights.items():
                        logger.info(f"  - {k}: {v:.2%}")
                else:
                    logger.info(f"Skipping weight calibration for {sym} due to low sample volume.")

        logger.info("Offline backtesting and optimization cycle completed successfully.")

    except Exception as e:
        logger.error(f"Error in backtest execution pipeline: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
