"""
Stage 4 — Per-symbol training script.

Eğitim verilerini collect_training_data ile topla, her sembol için ayrı
LightGBM + z-score normalizer eğit, backend/models/stage4_per_symbol/{slug}/
altına yaz.

Kullanım:
  python -m scripts.train_stage4 --days 90
  → her sembol için model.joblib, features.json, normalizer.json üretir

Endpoint ile:
  POST /api/precision-veto/train-stage4?days=90

Tasarım kuralları:
- Sembol kodlaması YOK (model symbol'ü proxy olarak kullanmasın)
- Ham feature dict aynı (collect_training_data 38 feature üretiyor)
- Normalize: encoded olmayan continuous feature'lara mean/std (training set'ten)
- Min sample per symbol: 300 — altındaysa o sembolü atla (legacy fallback kalır)
- 70/15/15 train/val/test split (kronolojik, leak-siz)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO,
                     format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("train_stage4")

MIN_SAMPLES_PER_SYMBOL = 300


def _build_normalizer(X: list[dict], feature_names: list[str],
                      skip: set) -> dict:
    """Train set'inden mean/std (per-feature)."""
    import numpy as np
    norm: dict = {}
    for name in feature_names:
        if name in skip:
            continue
        vals = []
        for row in X:
            v = row.get(name)
            if v is None:
                continue
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                continue
        if not vals:
            norm[name] = {"mean": 0.0, "std": 1.0}
            continue
        arr = np.array(vals, dtype=float)
        m = float(arr.mean())
        s = float(arr.std())
        # std==0 ise normalize bypass (1.0 = no-op)
        norm[name] = {"mean": round(m, 6),
                       "std": round(s if s > 1e-9 else 1.0, 6)}
    return norm


def _vectorize(X: list[dict], feature_names: list[str],
                normalizer: dict, skip: set):
    import numpy as np
    rows = []
    for row in X:
        vec = []
        for n in feature_names:
            v = row.get(n)
            try:
                x = float(v) if v is not None else 0.0
            except (TypeError, ValueError):
                x = 0.0
            if n not in skip and n in normalizer:
                ns = normalizer[n]
                m = float(ns.get("mean") or 0.0)
                s = float(ns.get("std") or 1.0)
                if s > 1e-9:
                    x = (x - m) / s
            vec.append(x)
        rows.append(vec)
    return np.array(rows, dtype=float)


def _train_one(symbol: str, X_sym: list[dict], y_sym: list[float],
                out_dir: Path, skip: set) -> Optional[dict]:
    """Tek sembol için eğit, kaydet, metrics döndür."""
    import lightgbm as lgb
    import joblib
    import numpy as np
    n = len(X_sym)
    if n < MIN_SAMPLES_PER_SYMBOL:
        log.warning("%s: %d örnek — atlandı (min %d)",
                     symbol, n, MIN_SAMPLES_PER_SYMBOL)
        return None

    feature_names = sorted({k for row in X_sym for k in row.keys()})
    log.info("%s: %d örnek, %d feature", symbol, n, len(feature_names))

    cut1 = int(n * 0.70)
    cut2 = int(n * 0.85)
    X_train_raw = X_sym[:cut1]
    X_val_raw = X_sym[cut1:cut2]
    X_test_raw = X_sym[cut2:]
    y_train = np.array(y_sym[:cut1], dtype=float)
    y_val = np.array(y_sym[cut1:cut2], dtype=float)
    y_test = np.array(y_sym[cut2:], dtype=float)

    # Normalizer SADECE train set'ten — leak yok
    normalizer = _build_normalizer(X_train_raw, feature_names, skip)
    X_train = _vectorize(X_train_raw, feature_names, normalizer, skip)
    X_val = _vectorize(X_val_raw, feature_names, normalizer, skip)
    X_test = _vectorize(X_test_raw, feature_names, normalizer, skip)

    model = lgb.LGBMRegressor(
        objective="regression", metric="rmse",
        num_leaves=15, learning_rate=0.05,    # daha az leaf — sembol başına az veri
        feature_fraction=0.85, bagging_fraction=0.8, bagging_freq=5,
        n_estimators=400, verbose=-1, min_child_samples=15,
    )
    model.fit(X_train, y_train,
              eval_set=[(X_val, y_val)],
              callbacks=[lgb.early_stopping(40), lgb.log_evaluation(0)])

    pred_test = model.predict(X_test)
    pred_val = model.predict(X_val)
    test_rmse = float(np.sqrt(np.mean((pred_test - y_test) ** 2)))
    test_mae = float(np.mean(np.abs(pred_test - y_test)))
    val_rmse = float(np.sqrt(np.mean((pred_val - y_val) ** 2)))
    y_test_var = float(np.var(y_test)) or 1e-9
    test_r2 = float(1.0 - np.mean((pred_test - y_test) ** 2) / y_test_var)
    test_spearman = None
    try:
        from scipy.stats import spearmanr
        rho, _ = spearmanr(pred_test, y_test)
        if rho is not None and not np.isnan(rho):
            test_spearman = float(rho)
    except Exception:
        pass

    imp = sorted(zip(feature_names, model.feature_importances_),
                  key=lambda x: -x[1])
    log.info("  %s test: RMSE=%.3f MAE=%.3f Spearman=%s R²=%.3f",
              symbol, test_rmse, test_mae,
              round(test_spearman, 3) if test_spearman is not None else "—",
              test_r2)

    # Kayıt
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_dir / "model.joblib")
    metrics = {
        "test_rmse": test_rmse, "test_mae": test_mae,
        "test_spearman": test_spearman, "test_r2": test_r2,
        "val_rmse": val_rmse,
        "n_train": len(X_train_raw), "n_val": len(X_val_raw),
        "n_test": len(X_test_raw),
    }
    with open(out_dir / "features.json", "w") as fp:
        json.dump({
            "features": feature_names,
            "metrics": metrics,
            "is_regressor": True,
            "target": "r_mult (ATR-normalized)",
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "min_samples_per_symbol": MIN_SAMPLES_PER_SYMBOL,
            "normalizer_skipped_features": sorted(skip & set(feature_names)),
            "top_features": [{"name": n, "importance": int(v)}
                              for n, v in imp[:15]],
        }, fp, indent=2)
    with open(out_dir / "normalizer.json", "w") as fp:
        json.dump(normalizer, fp, indent=2)
    return {"symbol": symbol, "n": n, "feature_count": len(feature_names),
            "metrics": metrics}


async def train_all(days: int = 90) -> dict:
    """Tüm semboller için ayrı modeller eğit. collect_training_data
    legacy script'ten reuse — feature pipeline tek noktada."""
    from scripts.train_precision_meta_classifier import collect_training_data
    from services.model_loader import (_PER_SYMBOL_DIR, get_normalizer_skip_set,
                                         slugify, reload_all)
    X, y, M = await collect_training_data(days=days, return_meta=True)
    if len(X) < MIN_SAMPLES_PER_SYMBOL:
        return {"status": "error", "error": f"yetersiz toplam veri: {len(X)}"}

    # Sembol bazlı ayır (kronolojik sırayı koru — collect_training_data zaten
    # signal_created_at ascending döner)
    per_sym: dict = {}
    for i, meta in enumerate(M):
        sym = meta["symbol"]
        per_sym.setdefault(sym, {"X": [], "y": []})
        per_sym[sym]["X"].append(X[i])
        per_sym[sym]["y"].append(y[i])

    skip = get_normalizer_skip_set()
    results = []
    for sym, d in per_sym.items():
        slug = slugify(sym)
        out_dir = _PER_SYMBOL_DIR / slug
        try:
            r = _train_one(sym, d["X"], d["y"], out_dir, skip)
            if r:
                results.append(r)
            else:
                results.append({"symbol": sym, "skipped": True,
                                 "n": len(d["X"])})
        except Exception as e:
            log.exception("%s eğitim hatası", sym)
            results.append({"symbol": sym, "error": str(e)[:200]})

    # Cache temizle (servis bir sonraki çağrıda yeni modeli yüklesin)
    reload_info = reload_all()
    return {"status": "ok", "trained": results,
            "reload": reload_info, "total_samples": len(X)}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    args = ap.parse_args()
    res = await train_all(days=args.days)
    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
