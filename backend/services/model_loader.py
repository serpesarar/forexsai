"""
Stage 4 — Per-symbol model registry.

Sorun (2026-05-25 OOS backtest): tek monolitik LightGBM model 4 sembolün
ortalamasına optimize oluyor. USOIL'de Spearman=null (model hiç ayrıştırma
yapmıyor), GDAXI'de Spearman pozitif ama realized R negatif (ters yön).
Sebep: feature scale'leri sembol bazlı çok farklı — USOIL %-tabanlı, XAUUSD
ham fiyat farkı, NDX/GDAXI index puanı.

Çözüm: her sembol için ayrı LightGBM + per-symbol z-score normalizer.
Inference'da sembole göre model + normalizer seçilir, fallback olarak
legacy birleşik model kullanılır.

Disk düzeni:
  backend/models/
    precision_meta_classifier.joblib       ← legacy fallback (combined)
    precision_meta_features.json           ← legacy feature list
    stage4_per_symbol/
      xauusd/
        model.joblib
        features.json   { "features":[...], "trained_at":..., "metrics":{...} }
        normalizer.json { "<feat>": {"mean":..., "std":...}, ... }
      ndx_indx/...
      gdaxi_indx/...
      usoil_forex/...

Cache: ilk get_model_for() çağrısında lazy load + dict cache. reload_all()
yeni eğitim sonrası cache'i temizler.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_MODELS_ROOT = Path(__file__).parent.parent / "models"
_PER_SYMBOL_DIR = _MODELS_ROOT / "stage4_per_symbol"

# Normalization skipped — bunlar zaten encoded küçük integer'lar
_NO_NORMALIZE_FEATURES = {
    "direction_code", "regime_code", "memory_zone_count",
    "recently_broken_zone_count", "swing_small_high_count",
    "swing_small_low_count", "swing_large_high_count",
    "swing_large_low_count", "near_zone_touches",
    "near_zone_rejections", "near_zone_breaks",
    "pdh_touches_today", "pdh_rejections_today",
    "pdl_touches_today", "pdl_rejections_today",
}


def slugify(symbol: str) -> str:
    """XAUUSD → xauusd; NDX.INDX → ndx_indx; USOIL.FOREX → usoil_forex."""
    return re.sub(r"[^a-z0-9]", "_", (symbol or "").lower()).strip("_")


# ─── Cache state ─────────────────────────────────────────────────────────────
# slug → {"model": ..., "features": [...], "normalizer": {...}, "meta": {...}}
_cache: dict[str, dict] = {}
_legacy_cache: Optional[dict] = None
_lock = threading.Lock()


def _load_one(symbol: str) -> Optional[dict]:
    """Disk'ten per-symbol model + features + normalizer yükle."""
    slug = slugify(symbol)
    base = _PER_SYMBOL_DIR / slug
    mp = base / "model.joblib"
    fp = base / "features.json"
    np_path = base / "normalizer.json"
    if not (mp.exists() and fp.exists()):
        return None
    try:
        import joblib
        model = joblib.load(mp)
        with open(fp) as f:
            meta = json.load(f)
        feature_names = meta.get("features") or []
        normalizer = {}
        if np_path.exists():
            with open(np_path) as f:
                normalizer = json.load(f) or {}
        return {"model": model, "features": feature_names,
                "normalizer": normalizer, "meta": meta,
                "is_regressor": "Regressor" in type(model).__name__,
                "source": str(base)}
    except Exception as e:
        logger.warning("[model-loader] %s yüklenemedi: %s", slug, e)
        return None


def _load_legacy() -> Optional[dict]:
    """Combined model fallback (mevcut precision_meta_classifier.joblib)."""
    mp = _MODELS_ROOT / "precision_meta_classifier.joblib"
    fp = _MODELS_ROOT / "precision_meta_features.json"
    if not (mp.exists() and fp.exists()):
        return None
    try:
        import joblib
        model = joblib.load(mp)
        with open(fp) as f:
            meta = json.load(f)
        return {"model": model, "features": meta.get("features") or [],
                "normalizer": {},   # legacy normalize edilmemiş
                "meta": meta,
                "is_regressor": "Regressor" in type(model).__name__,
                "source": str(mp)}
    except Exception as e:
        logger.warning("[model-loader] legacy model yüklenemedi: %s", e)
        return None


def get_model_for(symbol: str) -> Optional[dict]:
    """Sembole özel model döner; yoksa combined legacy model'e düşer.

    Cache'lidir; reload_all() çağrılana dek aynı modeli verir.
    None döndüğünde caller Stage 4'ü atlamalı."""
    if not symbol:
        return None
    slug = slugify(symbol)
    global _legacy_cache
    with _lock:
        if slug in _cache:
            return _cache[slug]
    entry = _load_one(symbol)
    if entry is None:
        with _lock:
            if _legacy_cache is None:
                _legacy_cache = _load_legacy()
        if _legacy_cache is None:
            logger.debug("[model-loader] %s için ne per-symbol ne legacy var",
                         slug)
            return None
        # Sembol için legacy'yi cache'le ama legacy işareti taşısın
        entry = dict(_legacy_cache, fallback_to_legacy=True, slug=slug)
    else:
        entry["fallback_to_legacy"] = False
        entry["slug"] = slug
    with _lock:
        _cache[slug] = entry
    return entry


def reload_all() -> dict:
    """Tüm cache'i sıfırla — yeni eğitim sonrası çağrılır."""
    global _legacy_cache
    with _lock:
        _cache.clear()
        _legacy_cache = None
    # Mevcut sembolleri tarayıp yeniden cache'le (raporlama için)
    found = {}
    if _PER_SYMBOL_DIR.exists():
        for child in _PER_SYMBOL_DIR.iterdir():
            if not child.is_dir():
                continue
            slug = child.name
            entry = _load_one(slug)  # slug doğrudan
            if entry is not None:
                found[slug] = {
                    "feature_count": len(entry["features"]),
                    "has_normalizer": bool(entry["normalizer"]),
                    "is_regressor": entry["is_regressor"],
                    "metrics": (entry["meta"] or {}).get("metrics"),
                    "trained_at": (entry["meta"] or {}).get("trained_at"),
                }
                with _lock:
                    _cache[slug] = entry
    legacy = _load_legacy()
    if legacy:
        with _lock:
            _legacy_cache = legacy
    return {"per_symbol_loaded": found,
            "legacy_loaded": legacy is not None,
            "per_symbol_dir": str(_PER_SYMBOL_DIR),
            "per_symbol_dir_exists": _PER_SYMBOL_DIR.exists()}


def state_snapshot() -> dict:
    """İnceleme — şu an cache'te ne var?"""
    with _lock:
        return {
            "cached_symbols": sorted(_cache.keys()),
            "legacy_cached": _legacy_cache is not None,
            "per_symbol_dir": str(_PER_SYMBOL_DIR),
            "per_symbol_dir_exists": _PER_SYMBOL_DIR.exists(),
            "per_symbol_subdirs": (sorted(p.name for p in _PER_SYMBOL_DIR.iterdir() if p.is_dir())
                                    if _PER_SYMBOL_DIR.exists() else []),
            "no_normalize_features": sorted(_NO_NORMALIZE_FEATURES),
        }


def get_normalizer_skip_set() -> set[str]:
    return set(_NO_NORMALIZE_FEATURES)
