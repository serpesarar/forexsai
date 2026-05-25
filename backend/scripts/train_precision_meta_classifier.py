"""
Precision Meta Classifier — LightGBM regression eğitim scripti.

Hedef: target = realized_pips / stop_loss_pips (R-multiple).
Kazanan sinyaller pozitif R, kaybedenler negatif R verir. Classification
yerine regression: model "kazanan/kaybeden" demez, "bu sinyal X.X R verir"
der → live'da lot çarpanı buna göre belirlenir.

Veri kaynağı: prediction_replay_corrections (replay_status=ok).
Feature kaynağı: Stage 1c'nin ürettiği zengin Day Structure snapshot'ları.
NOT: ŞU AN feature'lar prediction_logs'ta SAKLI DEĞİL. Bu script bunu da
çözer — geçmiş sinyalleri yeniden replay edip feature'ları hesaplar.

Çalıştırma:
    python -m backend.scripts.train_precision_meta_classifier --days 90

Çıktı: backend/models/precision_meta_classifier.joblib +
       backend/models/precision_meta_features.json (feature isim sırası)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO,
                     format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("train_meta")


async def collect_training_data(days: int = 90) -> tuple[list[dict], list[float]]:
    """Her resolved sinyal için: (features dict, R-multiple target).

    Day Structure feature'larını hesaplamak için Stage 1c'yi point-in-time
    çalıştırırız (canlı veri leak'i olmasın diye)."""
    from database.supabase_client import get_supabase_client, is_db_available
    from services.signal_replay_1m import _load_all_1m_bars_sync
    from services.day_structure_service import compute_day_structure
    from services.precision_veto_backtest import _aggregate, _slice_up_to
    if not is_db_available():
        raise SystemExit("supabase yok")
    client = get_supabase_client()

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows: list[dict] = []
    offset = 0
    while True:
        q = (client.table("prediction_replay_corrections").select(
            "prediction_id,symbol,model_type,direction,entry_price,timeframe,"
            "signal_created_at,corrected_status,corrected_exit_price,"
            "corrected_mfe_pips,corrected_mae_pips,replay_status")
            .gte("signal_created_at", since)
            .order("signal_created_at", desc=False)
            .range(offset, offset + 999))
        res = q.execute() if hasattr(q, "execute") else q
        page = res.data if hasattr(res, "data") else (
            res.get("data") if isinstance(res, dict) else []) or []
        if not page: break
        rows.extend(page)
        if len(page) < 1000: break
        offset += 1000

    rows = [r for r in rows if r.get("replay_status") == "ok"
            and r.get("corrected_status") in ("completed", "stopped")
            and r.get("entry_price")]
    log.info("resolved sinyal sayısı: %d", len(rows))

    # Symbol başına 1m bars + agregasyonlar (replay backtest'ten reused)
    symbols = sorted({r["symbol"] for r in rows})
    bars_by_sym: dict = {}
    for sym in symbols:
        bars_1m = await asyncio.to_thread(_load_all_1m_bars_sync, sym)
        if not bars_1m: continue
        bars_by_sym[sym] = {
            "15m": _aggregate(bars_1m, "15m"),
            "1h": _aggregate(bars_1m, "1h"),
            "1d": _aggregate(bars_1m, "1d"),
        }
        bars_by_sym[sym]["15m_keys"] = [b["ts"] for b in bars_by_sym[sym]["15m"]]
        bars_by_sym[sym]["1h_keys"] = [b["ts"] for b in bars_by_sym[sym]["1h"]]
        bars_by_sym[sym]["1d_keys"] = [b["ts"] for b in bars_by_sym[sym]["1d"]]
        log.info("%s: 1m=%d 15m=%d 1h=%d 1d=%d", sym, len(bars_1m),
                 len(bars_by_sym[sym]["15m"]), len(bars_by_sym[sym]["1h"]),
                 len(bars_by_sym[sym]["1d"]))

    # SL pips (R-multiple denominator) — sabit config'ten
    try:
        from services.target_config import get_symbol_config
        sl_pips_by_sym = {s: get_symbol_config(s).stoploss_pips for s in symbols}
    except Exception:
        sl_pips_by_sym = {}

    def _parse(t):
        try: return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        except Exception: return None

    from services.target_config import pips_from_price_change

    X: list[dict] = []
    y: list[float] = []
    for r in rows:
        sym = r["symbol"]
        if sym not in bars_by_sym: continue
        cutoff = _parse(r["signal_created_at"])
        if cutoff is None: continue
        bs = bars_by_sym[sym]
        c_15m = _slice_up_to(bs["15m"], bs["15m_keys"], cutoff, last_n=400)
        c_1h = _slice_up_to(bs["1h"], bs["1h_keys"], cutoff, last_n=200)
        c_1d = _slice_up_to(bs["1d"], bs["1d_keys"], cutoff, last_n=30)
        if len(c_15m) < 30 or len(c_1d) < 2: continue
        tf = r.get("timeframe") or "15m"
        try:
            ds = await compute_day_structure(
                sym, tf,
                _injected_candles={"15m": c_15m, "1h": c_1h, "1d": c_1d, "tf": c_15m},
                _as_of=cutoff)
        except Exception:
            continue
        if ds is None: continue

        # Feature'ları üret — Stage 1c'nin yaptığı gibi
        feats = _extract_features(ds, r["direction"], float(r["entry_price"]), sym)
        # Target: realized R-multiple — ATR'e göre normalize (NOT current SL config)
        # Bu önemli: derived overrides aktifleştirildi diye OLD signals'in
        # SL'ini güncel config'e göre hesaplamak yanlış olur. ATR sinyal anında
        # hesaplanmış, evrensel — sembol/config bağımsız R birim sağlar.
        e = float(r["entry_price"]); x = float(r.get("corrected_exit_price") or 0)
        if x <= 0: continue
        diff = (x - e) if r["direction"] == "BUY" else (e - x)
        try:
            realized_pips = pips_from_price_change(abs(diff), sym) * (1 if diff >= 0 else -1)
        except Exception:
            realized_pips = diff
        # ATR pip cinsinden — sembol percentage ise pips_from_price_change zaten % verir
        try:
            atr_pips = pips_from_price_change(ds.atr, sym)
        except Exception:
            atr_pips = ds.atr
        if atr_pips <= 0: continue
        r_mult = realized_pips / atr_pips
        # Outlier kırpma — R > 8 ATR veya R < -4 ATR aşırı, muhtemelen veri hatası
        if r_mult > 8 or r_mult < -4: continue
        X.append(feats); y.append(r_mult)

    log.info("eğitim noktası sayısı: %d", len(X))
    return X, y


def _extract_features(ds, direction: str, price: float, symbol: str) -> dict:
    """Stage 1c'nin features dict'iyle birebir aynı — eğitim ve inference
    aynı feature'larla beslensin."""
    f: dict = {
        "ds_atr": ds.atr,
        "today_atr_ratio": ds.today_atr_ratio,
        "regime_code": {"TRENDING_UP": 1, "TRENDING_DOWN": -1,
                          "RANGING": 0, "TRANSITIONAL": 2, "UNKNOWN": 99}.get(ds.regime, 99),
        "regime_efficiency": ds.regime_efficiency,
        "memory_zone_count": len(ds.memory_zones),
        "recently_broken_zone_count": len(ds.recently_broken_zone_centers),
        "swing_small_high_count": len(ds.swings_small_highs),
        "swing_small_low_count": len(ds.swings_small_lows),
        "swing_large_high_count": len(ds.swings_large_highs),
        "swing_large_low_count": len(ds.swings_large_lows),
        "direction_code": 1 if direction == "BUY" else -1,
    }
    for name, lvl in [("pdh", ds.pdh), ("pdl", ds.pdl),
                       ("pwh", ds.pwh), ("pwl", ds.pwl)]:
        f[f"{name}_dist_atr"] = abs(lvl - price) / ds.atr if (lvl and ds.atr > 0) else -1
        f[f"{name}_dist_signed_atr"] = (lvl - price) / ds.atr if (lvl and ds.atr > 0) else 0
    for name, lvl in ds.pivots.items():
        f[f"pivot_{name.lower()}_dist_atr"] = abs(lvl - price) / ds.atr if ds.atr > 0 else -1
    f["pdh_touches_today"] = ds.pdh_touches_today
    f["pdh_rejections_today"] = ds.pdh_rejections_today
    f["pdl_touches_today"] = ds.pdl_touches_today
    f["pdl_rejections_today"] = ds.pdl_rejections_today
    nz = ds.nearest_memory_zone_in_direction(direction)
    if nz:
        f["near_zone_distance_atr"] = abs(nz.center - price) / ds.atr if ds.atr > 0 else -1
        f["near_zone_touches"] = nz.touches
        f["near_zone_rejections"] = nz.rejections
        f["near_zone_breaks"] = nz.breaks
        f["near_zone_freshness"] = nz.freshness
        total = max(1, nz.rejections + nz.breaks)
        f["near_zone_reject_ratio"] = nz.rejections / total
    else:
        for k in ("near_zone_distance_atr", "near_zone_touches", "near_zone_rejections",
                   "near_zone_breaks", "near_zone_freshness", "near_zone_reject_ratio"):
            f[k] = -1
    trend_dir = 1 if ds.regime == "TRENDING_UP" else -1 if ds.regime == "TRENDING_DOWN" else 0
    sig_dir = 1 if direction == "BUY" else -1
    f["trend_aligned_with_signal"] = int(trend_dir == sig_dir) if trend_dir != 0 else 0
    f["trend_against_signal"] = int(trend_dir == -sig_dir) if trend_dir != 0 else 0
    return f


def train(X: list[dict], y: list[float], model_out: Path, features_out: Path):
    import numpy as np
    try:
        import lightgbm as lgb
    except ImportError:
        log.error("lightgbm yok — pip install lightgbm")
        sys.exit(1)
    try:
        import joblib
    except ImportError:
        log.error("joblib yok — pip install joblib"); sys.exit(1)

    # Feature isim sırasını sabit tut (inference aynı sıra)
    feature_names = sorted({k for d in X for k in d.keys()})
    X_mat = np.array([[d.get(k, -1) for k in feature_names] for d in X], dtype=float)
    y_arr = np.array(y, dtype=float)

    # 70/15/15 time-based split: train → val (early stopping) → held-out test.
    # Val seti ile early stopping, test seti gerçek out-of-sample dürüst değer.
    n = len(X_mat)
    cut1 = int(n * 0.70)
    cut2 = int(n * 0.85)
    X_train, y_train = X_mat[:cut1], y_arr[:cut1]
    X_val, y_val = X_mat[cut1:cut2], y_arr[cut1:cut2]
    X_test, y_test = X_mat[cut2:], y_arr[cut2:]
    log.info("train=%d val=%d test=%d feature=%d",
             len(X_train), len(X_val), len(X_test), len(feature_names))

    model = lgb.LGBMRegressor(
        objective="regression", metric="rmse",
        num_leaves=31, learning_rate=0.05,
        feature_fraction=0.9, bagging_fraction=0.8, bagging_freq=5,
        n_estimators=500, verbose=-1, min_child_samples=20,
    )
    model.fit(X_train, y_train,
              eval_set=[(X_val, y_val)],
              callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)])

    # Gerçek out-of-sample değerlendirme (test set — early stopping görmedi)
    pred_test = model.predict(X_test)
    pred_val = model.predict(X_val)
    test_rmse = float(np.sqrt(np.mean((pred_test - y_test) ** 2)))
    test_mae = float(np.mean(np.abs(pred_test - y_test)))
    val_rmse = float(np.sqrt(np.mean((pred_val - y_val) ** 2)))
    val_mae = float(np.mean(np.abs(pred_val - y_val)))
    # R^2 (test) — naif baseline (sabit ortalama) ile karşılaştırma
    y_test_var = float(np.var(y_test)) or 1e-9
    test_r2 = float(1.0 - np.mean((pred_test - y_test) ** 2) / y_test_var)
    # Spearman rank corr (gerçek R sırasını tahmin edebiliyor mu?)
    test_spearman = None
    try:
        from scipy.stats import spearmanr
        rho, _ = spearmanr(pred_test, y_test)
        test_spearman = float(rho) if rho is not None and not np.isnan(rho) else None
        log.info("Test  RMSE=%.3f  MAE=%.3f  Spearman=%.3f  R²=%.3f",
                 test_rmse, test_mae, test_spearman or 0.0, test_r2)
    except Exception:
        log.info("Test  RMSE=%.3f  MAE=%.3f  R²=%.3f", test_rmse, test_mae, test_r2)
    # Compatibility (eski adlandırma)
    rmse, mae = test_rmse, test_mae

    # Feature importance
    imp = sorted(zip(feature_names, model.feature_importances_),
                 key=lambda x: -x[1])
    log.info("Top 10 feature importance:")
    for name, val in imp[:10]:
        log.info("  %30s  %d", name, int(val))

    # Kaydet
    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out)
    from datetime import datetime as _dt, timezone as _tz
    meta_out = {
        "features": feature_names,
        # legacy keys (geriye uyumlu)
        "rmse": rmse, "mae": mae,
        "n_train": len(X_train), "n_test": len(X_test),
        # zengin metrik seti — /train-meta/status okuyor
        "test_rmse": test_rmse, "test_mae": test_mae,
        "test_spearman": test_spearman, "r2": test_r2,
        "val_rmse": val_rmse, "val_mae": val_mae,
        "n_val": len(X_val),
        "is_regressor": True,
        "target": "r_mult (ATR-normalized realized_pips / atr_pips)",
        "trained_at": _dt.now(_tz.utc).isoformat(),
        "top_features": [{"name": n, "importance": int(v)}
                         for n, v in imp[:15]],
    }
    with open(features_out, "w") as fp:
        json.dump(meta_out, fp, indent=2)
    log.info("Model → %s", model_out)
    log.info("Feature listesi → %s", features_out)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    args = ap.parse_args()

    base = Path(__file__).parent.parent / "models"
    X, y = await collect_training_data(args.days)
    if len(X) < 200:
        log.error("yeterli veri yok (en az 200 örnek lazım)"); sys.exit(1)
    train(X, y, base / "precision_meta_classifier.joblib",
          base / "precision_meta_features.json")


if __name__ == "__main__":
    asyncio.run(main())
