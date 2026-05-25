"""
Model persistence over Supabase Storage.

Sorun: Railway her redeploy'da /app/models/'u siliyor → her commit = 25 dk
retrain. Çözüm: eğitim sonunda tüm modelleri Supabase Storage'a yükle,
startup'ta indir. Redeploy maliyeti 25 dk → 5-10 sn.

Bucket: forexsai-models (private; service key ile erişim).

Yerleşim:
  stage4/precision_meta_classifier.joblib         (combined)
  stage4/precision_meta_features.json
  stage4/per_symbol/<slug>/{model.joblib, features.json, normalizer.json}
  stage4/stage4_prediction_history.json
  manifest.json   ← kaynak doğrusu (version, hashes, timestamps)

Manifest mismatch (Python/lgbm versiyon, features_hash) → retrain tetikler.
Her dosya için sha256 — download sonrası bütünlük kontrolü.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BUCKET = os.getenv("SUPABASE_MODELS_BUCKET", "forexsai-models")
_MODELS_ROOT = Path(__file__).parent.parent / "models"
_MANIFEST_REMOTE = "manifest.json"
_MANIFEST_LOCAL = _MODELS_ROOT / "manifest.json"

# Stage 4 ile sınırlı — gelecekte başka model setleri için prefix listesi.
_TRACKED_FILES = [
    "stage4/precision_meta_classifier.joblib",
    "stage4/precision_meta_features.json",
    "stage4/stage4_prediction_history.json",
]
_PER_SYMBOL_PREFIX = "stage4/per_symbol/"
_PER_SYMBOL_FILES = ["model.joblib", "features.json", "normalizer.json"]


# ─── Supabase storage istemcisi ──────────────────────────────────────────────
_client = None


def _get_client():
    """Resmi supabase-py client (storage için). Service role key zorunlu."""
    global _client
    if _client is not None:
        return _client
    try:
        from supabase import create_client
    except ImportError as e:
        raise RuntimeError("supabase-py yüklü değil: %s" % e)
    url = os.getenv("SUPABASE_URL")
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_SERVICE_KEY")
            or os.getenv("SUPABASE_KEY"))
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY eksik")
    _client = create_client(url, key)
    return _client


def _ensure_bucket() -> None:
    """Bucket yoksa oluştur (private). Idempotent."""
    cli = _get_client()
    try:
        buckets = cli.storage.list_buckets()
        names = {b.name if hasattr(b, "name") else b.get("name") for b in buckets}
        if BUCKET not in names:
            cli.storage.create_bucket(BUCKET, options={"public": False})
            logger.info("[model-storage] bucket oluşturuldu: %s", BUCKET)
    except Exception as e:
        # create_bucket idempotency'si yumuşak — zaten varsa hata atabilir
        logger.debug("[model-storage] ensure_bucket: %s", e)


# ─── Yardımcılar ─────────────────────────────────────────────────────────────
def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _local_path_for(remote: str) -> Path:
    """Remote path → local Path (stage4/x.joblib → backend/models/stage4/x.joblib)."""
    return _MODELS_ROOT / remote


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _list_local_per_symbol_files() -> list[str]:
    """backend/models/stage4_per_symbol/<slug>/{model,features,normalizer}.{joblib,json}
    listesini remote-path formatında döner (model_loader._PER_SYMBOL_DIR ile aynı)."""
    base = _MODELS_ROOT / "stage4_per_symbol"
    out: list[str] = []
    if not base.exists():
        return out
    for sym_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        for fn in _PER_SYMBOL_FILES:
            fp = sym_dir / fn
            if fp.exists():
                out.append(f"stage4/per_symbol/{sym_dir.name}/{fn}")
    return out


def _physical_local_for(remote: str) -> Path:
    """Remote path → fiziksel local Path. Tek doğru: model_loader/train script
    okudukları yerle uyumlu olmalı.

      stage4/precision_meta_classifier.joblib →
        backend/models/precision_meta_classifier.joblib
      stage4/per_symbol/xauusd/model.joblib →
        backend/models/stage4_per_symbol/xauusd/model.joblib
    """
    if remote.startswith(_PER_SYMBOL_PREFIX):
        rest = remote[len(_PER_SYMBOL_PREFIX):]   # "xauusd/model.joblib"
        return _MODELS_ROOT / "stage4_per_symbol" / rest
    bare = remote.split("/", 1)[-1] if remote.startswith("stage4/") else remote
    return _MODELS_ROOT / bare


# ─── Upload ──────────────────────────────────────────────────────────────────
def _upload_one(remote: str, local: Path) -> dict:
    cli = _get_client()
    with open(local, "rb") as f:
        data = f.read()
    try:
        cli.storage.from_(BUCKET).upload(
            path=remote, file=data,
            file_options={"upsert": "true",
                          "content-type": "application/octet-stream"})
    except Exception as e:
        # upsert ön ayarı bazı supabase-py versiyonlarında reddedilebilir; sil-tekrar yükle
        try:
            cli.storage.from_(BUCKET).remove([remote])
        except Exception:
            pass
        cli.storage.from_(BUCKET).upload(path=remote, file=data)
    return {"remote": remote, "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def upload_all_models() -> dict:
    """Tüm Stage 4 modellerini Supabase'e yükle + manifest yaz.
    Eğitim sonunda otomatik çağrılır. Hata toleranslı: tek dosya yüklenemese de
    manifest diğer başarılıları kayıt eder."""
    started = time.time()
    _ensure_bucket()
    uploaded: list[dict] = []
    errors: list[dict] = []

    # 1) Sabit (combined + history) dosyalar
    for remote in _TRACKED_FILES:
        local = _physical_local_for(remote)
        if not local.exists():
            continue
        try:
            uploaded.append(_upload_one(remote, local))
        except Exception as e:
            logger.exception("[model-storage] upload hata %s", remote)
            errors.append({"remote": remote, "error": str(e)[:200]})

    # 2) Per-symbol dosyalar
    for remote in _list_local_per_symbol_files():
        local = _physical_local_for(remote)
        if not local.exists():
            continue
        try:
            uploaded.append(_upload_one(remote, local))
        except Exception as e:
            logger.exception("[model-storage] upload hata %s", remote)
            errors.append({"remote": remote, "error": str(e)[:200]})

    # 3) Manifest
    features_hash = ""
    feat_path = _MODELS_ROOT / "precision_meta_features.json"
    if feat_path.exists():
        try:
            with open(feat_path) as f:
                feats = json.load(f).get("features") or []
            features_hash = hashlib.sha256(
                json.dumps(feats, sort_keys=True).encode()).hexdigest()
        except Exception:
            pass
    lgbm_v = "unknown"
    try:
        import lightgbm as _lgb
        lgbm_v = getattr(_lgb, "__version__", "unknown")
    except Exception:
        pass
    manifest = {
        "version": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "lightgbm_version": lgbm_v,
        "features_hash": features_hash,
        "files": uploaded,
        "errors": errors,
        "bucket": BUCKET,
        "duration_seconds": round(time.time() - started, 2),
    }
    _MANIFEST_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    with open(_MANIFEST_LOCAL, "w") as f:
        json.dump(manifest, f, indent=2)
    # Manifest'i de upload et (eğer her şey başarısız olduysa bile)
    try:
        _upload_one(_MANIFEST_REMOTE, _MANIFEST_LOCAL)
    except Exception as e:
        logger.warning("[model-storage] manifest upload hata: %s", e)
        errors.append({"remote": _MANIFEST_REMOTE, "error": str(e)[:200]})
    logger.info("[model-storage] upload tamam: %d dosya, %d hata, %.1fs",
                 len(uploaded), len(errors), time.time() - started)
    return {"status": "ok" if not errors else "partial",
            "uploaded": len(uploaded), "errors": errors,
            "manifest": manifest}


# ─── Download ────────────────────────────────────────────────────────────────
def _download_one(remote: str, expect_sha: Optional[str] = None) -> dict:
    """Atomic: tmp → rename. Bütünlük: expect_sha verildiyse doğrula."""
    cli = _get_client()
    data = cli.storage.from_(BUCKET).download(remote)
    if not isinstance(data, (bytes, bytearray)):
        raise RuntimeError(f"beklenmedik download type: {type(data)}")
    actual_sha = hashlib.sha256(data).hexdigest()
    if expect_sha and actual_sha != expect_sha:
        raise RuntimeError(
            f"checksum mismatch {remote}: expected={expect_sha[:12]} "
            f"got={actual_sha[:12]}")
    local = _physical_local_for(remote)
    _ensure_parent(local)
    tmp = local.with_suffix(local.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
    tmp.replace(local)
    return {"remote": remote, "local": str(local),
            "size": len(data), "sha256": actual_sha}


def _fetch_manifest() -> Optional[dict]:
    try:
        cli = _get_client()
        raw = cli.storage.from_(BUCKET).download(_MANIFEST_REMOTE)
        if isinstance(raw, (bytes, bytearray)):
            return json.loads(raw.decode())
    except Exception as e:
        logger.info("[model-storage] manifest yok / okunamadı: %s", e)
    return None


def get_remote_manifest() -> Optional[dict]:
    """Endpoint'lerden okuma için public alias."""
    _ensure_bucket()
    return _fetch_manifest()


def validate_manifest(remote: Optional[dict] = None) -> dict:
    """Local Python/lgbm versiyonu remote manifest'la uyumlu mu?

    Strict mismatch (lgbm major version diff) → retrain önerilir."""
    m = remote or _fetch_manifest()
    if not m:
        return {"compatible": False, "reason": "no_remote_manifest"}
    issues = []
    try:
        import lightgbm as _lgb
        local_lgbm = getattr(_lgb, "__version__", "unknown")
    except Exception:
        local_lgbm = "missing"
    remote_lgbm = m.get("lightgbm_version") or ""
    if remote_lgbm and local_lgbm != "missing":
        if remote_lgbm.split(".")[0] != local_lgbm.split(".")[0]:
            issues.append(f"lightgbm major mismatch: remote={remote_lgbm} local={local_lgbm}")
    return {"compatible": not issues, "issues": issues,
            "remote_version": m.get("version"),
            "remote_files": len(m.get("files") or [])}


def download_all_models() -> dict:
    """Manifest'i indir + her dosyayı atomic+checksumlu indir. Startup'ta
    çağrılır; hata toleranslı (bir dosya başarısızsa diğerleri devam)."""
    started = time.time()
    _ensure_bucket()
    manifest = _fetch_manifest()
    if not manifest:
        return {"status": "no_manifest",
                "note": "remote bucket boş — önce eğitim + upload yapılmalı"}
    sha_index = {f["remote"]: f.get("sha256")
                  for f in (manifest.get("files") or [])}
    files_to_get = list(sha_index.keys())
    downloaded: list[dict] = []
    errors: list[dict] = []
    for remote in files_to_get:
        try:
            downloaded.append(_download_one(remote, sha_index.get(remote)))
        except Exception as e:
            logger.exception("[model-storage] download hata %s", remote)
            errors.append({"remote": remote, "error": str(e)[:200]})
    # Manifest'i de yerelle (state_snapshot için)
    try:
        _MANIFEST_LOCAL.parent.mkdir(parents=True, exist_ok=True)
        with open(_MANIFEST_LOCAL, "w") as f:
            json.dump(manifest, f, indent=2)
    except Exception:
        pass
    val = validate_manifest(manifest)
    logger.info("[model-storage] download tamam: %d dosya, %d hata, %.1fs",
                 len(downloaded), len(errors), time.time() - started)
    return {"status": "ok" if not errors else "partial",
            "downloaded": len(downloaded), "errors": errors,
            "manifest_version": manifest.get("version"),
            "compatibility": val,
            "duration_seconds": round(time.time() - started, 2)}


def storage_state() -> dict:
    """Tek bakışta durum — debug + dashboard için."""
    cli_ok = False
    err = None
    try:
        _get_client()
        cli_ok = True
    except Exception as e:
        err = str(e)[:200]
    return {
        "bucket": BUCKET,
        "client_ready": cli_ok,
        "client_error": err,
        "models_root": str(_MODELS_ROOT),
        "models_root_exists": _MODELS_ROOT.exists(),
        "local_files": {
            "combined": (_MODELS_ROOT / "precision_meta_classifier.joblib").exists(),
            "features": (_MODELS_ROOT / "precision_meta_features.json").exists(),
            "history": (_MODELS_ROOT / "stage4_prediction_history.json").exists(),
            "manifest": _MANIFEST_LOCAL.exists(),
            "per_symbol_count": len(_list_local_per_symbol_files()),
        },
        "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
        "service_key_set": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                                  or os.getenv("SUPABASE_SERVICE_KEY")),
    }
