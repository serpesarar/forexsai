"""
Stage 4 — Symbol-aware inference wrapper.

predict_r(symbol, features_dict) → (predicted_r, info)

Akış:
  1. model_loader.get_model_for(symbol) → per-symbol model + normalizer + feature list
  2. features_dict'ten model_features sırasına göre vektör oluştur (eksik=0)
  3. Z-score normalize (per-feature mean/std; encoded feature'lar atlanır)
  4. model.predict() → predicted_r
  5. info: hangi model kullanıldı (per-symbol mu legacy fallback mı), normalize
     yapıldı mı, eksik feature sayısı

Fallback: per-symbol model yok ise legacy combined model + normalizer yok
(legacy zaten normalize edilmemiş eğitilmişti). Her iki yolda da çıktı
aynı semantik (predicted_r in ATR units).
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _to_vector(features: dict, feature_names: list[str],
               normalizer: dict, skip_normalize: set) -> tuple[list[float], int]:
    """Features dict → feature_names sırasında float liste, normalize uygulanmış.

    Returns: (vec, missing_count)"""
    vec: list[float] = []
    missing = 0
    for name in feature_names:
        v = features.get(name)
        if v is None:
            v = 0.0
            missing += 1
        try:
            x = float(v)
        except (TypeError, ValueError):
            x = 0.0
            missing += 1
        # Normalize?
        if name not in skip_normalize and name in normalizer:
            ns = normalizer[name] or {}
            mean = float(ns.get("mean") or 0.0)
            std = float(ns.get("std") or 0.0)
            if std > 1e-9:
                x = (x - mean) / std
        vec.append(x)
    return vec, missing


def predict_r(symbol: str, features: dict
              ) -> tuple[Optional[float], dict]:
    """Sembole özel modelle predicted_r üret.

    Returns:
      (predicted_r, info)
      predicted_r=None → tahmin yapılamadı (model yok / hata)
      info: {model_source, used_per_symbol, normalized, missing_features,
             feature_count}
    """
    from services.model_loader import (get_model_for, get_normalizer_skip_set)
    entry = get_model_for(symbol)
    if entry is None:
        return None, {"skipped": "no_model"}
    feature_names = entry.get("features") or []
    if not feature_names:
        return None, {"skipped": "no_feature_list"}
    normalizer = entry.get("normalizer") or {}
    skip = get_normalizer_skip_set()
    try:
        import numpy as np
        vec, missing = _to_vector(features, feature_names, normalizer, skip)
        model = entry["model"]
        arr = np.array([vec], dtype=float)
        if entry.get("is_regressor"):
            pred = float(model.predict(arr)[0])
        else:
            pred = float(model.predict_proba(arr)[0][1])
        info = {
            "model_source": entry.get("source"),
            "used_per_symbol": not entry.get("fallback_to_legacy", False),
            "normalized": bool(normalizer),
            "missing_features": missing,
            "feature_count": len(feature_names),
            "is_regressor": bool(entry.get("is_regressor")),
        }
        return pred, info
    except Exception as e:
        logger.warning("[inference-stage4] %s tahmin hatası: %s", symbol, e)
        return None, {"error": str(e)[:120]}
