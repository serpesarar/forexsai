"""
Stage 4 — Percentile-based ML sizing.

Sorun: Stage 4 ML modeli ATR-normalize R-multiple tahmin ediyor ama çıktısı
çok dar aralıkta sıkışmış (0.06-0.12). Mutlak threshold (predicted_r < -0.2)
HİÇBİR ZAMAN tetiklenmiyor. Honest OOS backtest'te (2026-05-25) ortaya
çıktı: Spearman 0.20 var (rank gücü iyi), D9 muhteşem (81% WR, 0.19R) ama
mevcut absolute-threshold logic bunu yakalayamıyor.

Çözüm: Mutlak değer yerine ROLLING PERCENTILE. Her sembol için son N=500
tahminin dağılımını tut, yeni tahminin bu dağılım içindeki yüzdelik dilimine
göre size çarpanı uygula:

  percentile < 10%   → 0.0x  (HARD VETO — modelin en kötü dilimi)
  percentile < 30%   → 0.25x (küçük pozisyon)
  percentile 30-70%  → 1.0x  (baseline)
  percentile > 70%   → 1.2x  (boost)
  percentile > 90%   → 1.5x  (max — D9 yakalama)

History'ye sadece RESOLVED tahminler eklenir (canlı trade kapandıktan sonra
resolve_prediction çağrılır). Böylece dağılım "geçmişte tahmin edilebildiği
kanıtlanmış" sinyaller üzerinden oluşur, look-ahead bias yok.

Cold start: history < 50 örnek varken pass-through (1.0x, veto yok). Yeni
sembol veya yeni model deploy sonrası güvenli başlangıç sağlar.

Thread-safe: threading.Lock ile history + pending erişimi serileştirilmiş.
Persistence: backend/models/stage4_prediction_history.json'a kaydedilir,
process restart'ta otomatik yüklenir.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Konfigürasyon ───────────────────────────────────────────────────────────
_HISTORY_PATH = (Path(__file__).parent.parent / "models"
                  / "stage4_prediction_history.json")
_DEQUE_MAX = 500            # sembol başına rolling window
_MIN_HISTORY = 50           # bunun altında filtreleme yapma (cold start)
_PENDING_TTL_SEC = 7 * 86400  # 7 günden eski pending tahminleri at

# Sizing map — (upper_percentile_exclusive, multiplier, action_name)
# percentile ∈ [0,1], küçük percentile = modelin "kötü" dediği sinyal
_SIZING_MAP: list[tuple[float, float, str]] = [
    (0.10, 0.0, "hard_veto"),       # bottom 10% → veto
    (0.30, 0.25, "size_quarter"),   # 10-30%     → 0.25x
    (0.70, 1.0, "size_normal"),     # 30-70%     → 1x (baseline)
    (0.90, 1.2, "size_boost"),      # 70-90%     → 1.2x
    (1.01, 1.5, "size_max"),        # 90-100%    → 1.5x (>1.0 guard)
]

# ─── State (lock'lı) ─────────────────────────────────────────────────────────
# symbol → deque of (predicted_r, realized_r, ts_epoch)
_history: dict[str, deque] = {}
# signal_id → {symbol, predicted_r, ts}
_pending: dict[str, dict] = {}
_lock = threading.Lock()
_loaded = False


# ─── Persistence ─────────────────────────────────────────────────────────────
def _load_history() -> None:
    """Disk'ten history + pending'i yükle (process restart sonrası)."""
    global _loaded
    if _loaded:
        return
    try:
        if _HISTORY_PATH.exists():
            with open(_HISTORY_PATH) as f:
                data = json.load(f)
            with _lock:
                for sym, entries in (data.get("history") or {}).items():
                    d = deque(maxlen=_DEQUE_MAX)
                    for e in entries[-_DEQUE_MAX:]:
                        if isinstance(e, (list, tuple)) and len(e) >= 3:
                            d.append((float(e[0]), float(e[1]), int(e[2])))
                    if d:
                        _history[sym] = d
                _pending.update(data.get("pending") or {})
            logger.info("[stage4-sizing] history yüklendi: %s",
                         {s: len(d) for s, d in _history.items()})
    except Exception as e:
        logger.warning("[stage4-sizing] history yüklenemedi: %s", e)
    finally:
        _loaded = True


def _save_history() -> None:
    """History + pending'i disk'e yaz. Sık yazma maliyetli olmasın diye
    yalnızca resolve_prediction çağrılarında tetiklenir."""
    try:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            data = {
                "history": {s: list(d) for s, d in _history.items()},
                "pending": dict(_pending),
                "saved_at": time.time(),
            }
        tmp = _HISTORY_PATH.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f)
        tmp.replace(_HISTORY_PATH)
    except Exception as e:
        logger.warning("[stage4-sizing] history kaydedilemedi: %s", e)


# ─── Public API ──────────────────────────────────────────────────────────────
def get_sizing(symbol: str, predicted_r: float) -> dict:
    """Yeni bir predicted_r için percentile-based sizing kararı döner.

    Cold start (history < _MIN_HISTORY): pass-through (1.0x, veto yok).
    Aksi halde son 500 tahminin dağılımında percentile hesaplar ve
    _SIZING_MAP'tan ilgili kovayı uygular.

    Returns:
        {
          "sizing_mult": float,        # 0.0 (veto) | 0.25 | 1.0 | 1.2 | 1.5
          "action": str,                # "hard_veto"|"size_quarter"|...
          "percentile": float|None,    # [0,1] veya None (cold start)
          "history_size": int,
          "predicted_r": float,
          "cold_start": bool,
        }
    """
    _load_history()
    with _lock:
        d = _history.get(symbol)
        history_size = len(d) if d else 0
        if d is None or history_size < _MIN_HISTORY:
            return {
                "sizing_mult": 1.0,
                "action": "cold_start_passthrough",
                "percentile": None,
                "history_size": history_size,
                "predicted_r": round(float(predicted_r), 4),
                "cold_start": True,
            }
        preds_sorted = sorted(e[0] for e in d)

    # Percentile: kaç tahmin predicted_r'den küçük/eşit
    # bisect kullanmak daha temiz
    import bisect
    rank = bisect.bisect_right(preds_sorted, float(predicted_r))
    pct = rank / len(preds_sorted)
    # Bucket bul
    mult, action = 1.0, "size_normal"
    for upper, m, a in _SIZING_MAP:
        if pct < upper:
            mult, action = m, a
            break
    return {
        "sizing_mult": mult,
        "action": action,
        "percentile": round(pct, 4),
        "history_size": history_size,
        "predicted_r": round(float(predicted_r), 4),
        "cold_start": False,
    }


def record_prediction(signal_id: str, symbol: str, predicted_r: float) -> None:
    """Sinyal aktif olarak hayata geçtiğinde (prediction_logs insert sonrası)
    çağrılır. Tahmin pending bucket'a alınır; trade kapanınca resolve_prediction
    onu history'ye taşır."""
    if not signal_id or not symbol or predicted_r is None:
        return
    _load_history()
    with _lock:
        _pending[str(signal_id)] = {
            "symbol": str(symbol),
            "predicted_r": float(predicted_r),
            "ts": time.time(),
        }


def resolve_prediction(signal_id: str, realized_r: float) -> bool:
    """Sinyal kapanınca (lifecycle TP/SL/expire) çağrılır. Pending'den
    çıkarıp history'ye yazar. realized_r = realized_pips / atr_pips (training
    target ile aynı birim).

    Returns True ise history güncellendi, False ise pending'de bulunamadı."""
    if not signal_id or realized_r is None:
        return False
    _load_history()
    with _lock:
        p = _pending.pop(str(signal_id), None)
        if p is None:
            return False
        sym = p["symbol"]
        d = _history.setdefault(sym, deque(maxlen=_DEQUE_MAX))
        d.append((round(p["predicted_r"], 4),
                   round(float(realized_r), 4),
                   int(p["ts"])))
    _save_history()
    return True


def prune_stale_pending() -> int:
    """7 günden eski pending tahminleri at (sinyal kapatma sinyali kaçırılırsa
    bellek sızıntısı olmasın). Periyodik çağrılması önerilir."""
    _load_history()
    cutoff = time.time() - _PENDING_TTL_SEC
    removed = 0
    with _lock:
        stale = [sid for sid, p in _pending.items()
                 if (p.get("ts") or 0) < cutoff]
        for sid in stale:
            _pending.pop(sid, None)
            removed += 1
    if removed:
        _save_history()
        logger.info("[stage4-sizing] %d stale pending purged", removed)
    return removed


def get_state(verbose: bool = False) -> dict:
    """İnceleme endpoint'i için dağılım istatistikleri."""
    _load_history()
    with _lock:
        per_sym: dict = {}
        for sym, d in _history.items():
            preds = [e[0] for e in d]
            realized = [e[1] for e in d]
            if not preds:
                continue
            preds_sorted = sorted(preds)
            n = len(preds_sorted)
            per_sym[sym] = {
                "n": n,
                "filtering_active": n >= _MIN_HISTORY,
                "predicted_r": {
                    "min": round(preds_sorted[0], 4),
                    "p10": round(preds_sorted[max(0, n // 10 - 1)], 4),
                    "p30": round(preds_sorted[max(0, int(n * 0.3) - 1)], 4),
                    "p50": round(preds_sorted[n // 2], 4),
                    "p70": round(preds_sorted[min(n - 1, int(n * 0.7))], 4),
                    "p90": round(preds_sorted[min(n - 1, int(n * 0.9))], 4),
                    "max": round(preds_sorted[-1], 4),
                    "mean": round(sum(preds) / n, 4),
                },
                "realized_r": {
                    "mean": round(sum(realized) / n, 4) if realized else None,
                    "win_rate_pct": round(100 * sum(1 for r in realized if r > 0) / n, 1)
                                       if realized else None,
                },
            }
            if verbose:
                per_sym[sym]["last_10"] = list(d)[-10:]
        return {
            "history_path": str(_HISTORY_PATH),
            "history_path_exists": _HISTORY_PATH.exists(),
            "deque_max": _DEQUE_MAX,
            "min_history_for_filtering": _MIN_HISTORY,
            "pending_ttl_days": _PENDING_TTL_SEC // 86400,
            "sizing_map": [{"upper_percentile": u, "mult": m, "action": a}
                            for u, m, a in _SIZING_MAP],
            "pending_count": len(_pending),
            "per_symbol": per_sym,
        }


def seed_from_backtest(rows: list[dict]) -> int:
    """Bootstrap: backtest sonuçlarıyla history'yi tohumla.

    rows: [{symbol, predicted_r, realized_r, ts_epoch?}, ...]
    Yeni deploy sonrası cold start'ı atlamak için tek seferlik çalıştırılır.
    Mevcut history'yi SİLMEZ — ekler (deque rotasyonla eski en eskisini atar).
    """
    _load_history()
    added = 0
    now = int(time.time())
    with _lock:
        for r in rows:
            sym = r.get("symbol")
            p = r.get("predicted_r")
            x = r.get("realized_r")
            if not sym or p is None or x is None:
                continue
            d = _history.setdefault(sym, deque(maxlen=_DEQUE_MAX))
            d.append((round(float(p), 4), round(float(x), 4),
                       int(r.get("ts_epoch") or now)))
            added += 1
    _save_history()
    logger.info("[stage4-sizing] seed: %d satır eklendi", added)
    return added


# Modül yüklenirken disk'ten history'yi getir
_load_history()
