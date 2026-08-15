"""probation_exec.py — MOD-E probasyonu: sinyalden 5 bar sonra girme (CANLI icra).

Kural (2026-08-14 analizi, 2026-08-15 dış-örneklem doğrulaması):
    1. Sinyal oluştuğunda emir GÖNDERİLMEZ, kuyruğa alınır.
    2. 5 adet 1m bar beklenir.
    3. Bu 5 barda ALEYHE en fazla hareket > 1.28 × ATR14(1m) × √5 ise → İPTAL
       (Brownian %90 gürültü bandı; aşıldıysa sinyal ölmüş sayılır).
    4. Aşılmadıysa → o anki fiyattan market giriş, ARAŞTIRILMIŞ SABİT geometriyle.

Değerin kaynağı giriş KALİTESİ değil giriş FİYATI: 5 dk beklemek bedava bir
mikro-pullback limit emri gibi çalışıyor. Bu yüzden hedef KÜÇÜLTÜLMEZ —
probasyon + küçük TP birleşimi ölçümde daha kötü çıktı (yasak kombinasyon).

Kanıt (botun kendi işlemleri, 1m bar-bar replay, `backend/research/box_phase_oos.py`):
    dış-örneklem (2026-06-29→07-12) : n=112 WR %61.6 net +3.691$  (referans +1.607$)
    iç-örneklem  (2026-07-13→08-13) : n=126 WR %65.1 net +7.582$  (referans +2.842$)
    Faz-1 filtreleriyle birlikte    : dış n=70 +2.386$ · iç n=65 +8.537$
Faz-0'ın elenen kurallarının aksine İKİ dönemde de pozitif.

Kuyruk BELLEKTE: bot yeniden başlarsa bekleyen niyet kaybolur (giriş yapılmaz) —
konservatif ve kasıtlı. Tüm hata yolları girişi İPTAL eder (kör giriş yok).
"""
from __future__ import annotations

import time
from typing import Callable, Optional, Sequence

import config
import phase_rules as pr

_pending: list[dict] = []


# ── saf karar çekirdeği (test edilebilir) ───────────────────────────────────

def decide(elapsed_sec: float, bars_since: Sequence[dict], direction: str,
           signal_px: float, atr_1m: Optional[float], config_=None
           ) -> tuple[str, dict]:
    """('wait' | 'enter' | 'cancel', ayrıntı).

    bars_since: sinyalden SONRA açılmış 1m barlar (eski→yeni).
    """
    n_bars = int(pr.flag(config_, "PROBATION_BARS"))
    z = float(pr.flag(config_, "PROBATION_Z"))
    max_wait = float(pr.flag(config_, "PROBATION_MAX_WAIT_MIN"))

    if elapsed_sec > max_wait * 60:
        return "cancel", {"why": f"bayat niyet ({elapsed_sec/60:.0f}dk > {max_wait:.0f}dk)"}
    if elapsed_sec < n_bars * 60:
        return "wait", {"why": f"{elapsed_sec/60:.1f}/{n_bars} dk"}
    if not atr_1m or atr_1m <= 0:
        return "cancel", {"why": "ATR14(1m) yok — kör giriş yapılmaz"}
    if len(bars_since) < n_bars:
        return "wait", {"why": f"bar {len(bars_since)}/{n_bars}"}

    cancel, adverse, band = pr.probation_verdict(
        direction, signal_px, atr_1m, bars_since, n_bars, z)
    info = {"adverse": round(adverse, 2), "band": round(band, 2),
            "atr_1m": round(float(atr_1m), 2)}
    if cancel:
        info["why"] = (f"aleyhe {adverse:.1f}pt > band {band:.1f}pt "
                       f"(sinyal öldü)")
        return "cancel", info
    info["why"] = f"aleyhe {adverse:.1f}pt ≤ band {band:.1f}pt"
    return "enter", info


# ── kuyruk ──────────────────────────────────────────────────────────────────

def is_live(forexsai_sym: str) -> bool:
    """MOD-E bu sembolde canlı mı?"""
    if not pr.flag(config, "PROBATION_LIVE"):
        return False
    syms = pr.flag(config, "PROBATION_SYMBOLS")
    return forexsai_sym in syms


def pending_scopes() -> set:
    return {p["scope_key"] for p in _pending}


def queue(log, scope_key: str, forexsai_sym: str, mt5_symbol: str,
          direction: str, signal_px: float, signal_srv_time: int,
          opener: Callable[[], None]) -> bool:
    """Sinyali probasyona al. Aynı scope zaten kuyruktaysa False döner."""
    if any(p["scope_key"] == scope_key for p in _pending):
        log.info("%s — probasyon kuyruğunda zaten var, atlandı", scope_key)
        return False
    _pending.append({
        "scope_key": scope_key, "fx": forexsai_sym, "mt5_symbol": mt5_symbol,
        "direction": direction, "signal_px": float(signal_px),
        "srv_t": int(signal_srv_time), "t0": time.time(), "opener": opener,
    })
    log.info("[PROBASYON] %s %s @%.2f kuyruğa alındı — %d bar (%d dk) sonra "
             "gürültü bandı kontrolüyle karar verilecek", scope_key, direction,
             signal_px, int(pr.flag(config, "PROBATION_BARS")),
             int(pr.flag(config, "PROBATION_BARS")))
    return True


def process(mt5, log, log_gate_skip: Callable | None = None) -> None:
    """Her taramada çağrılır. Fail-safe: karar verilemezse giriş İPTAL."""
    if not _pending:
        return
    now = time.time()
    done = []
    for p in list(_pending):
        try:
            elapsed = now - p["t0"]
            n_bars = int(pr.flag(config, "PROBATION_BARS"))
            bars_since: list[dict] = []
            atr14 = None
            if elapsed >= n_bars * 60:
                rates = mt5.copy_rates_from_pos(p["mt5_symbol"], mt5.TIMEFRAME_M1,
                                                0, 120)
                if rates is not None and len(rates) > 20:
                    all_bars = [{"t": int(r["time"]), "high": float(r["high"]),
                                 "low": float(r["low"]), "close": float(r["close"])}
                                for r in rates]
                    # sinyalden SONRA açılmış barlar (broker saatinde karşılaştır)
                    bars_since = [b for b in all_bars if b["t"] > p["srv_t"]]
                    pre = [b for b in all_bars if b["t"] <= p["srv_t"]]
                    atr14 = pr.atr_simple(pre[-60:], 14)

            verdict, info = decide(elapsed, bars_since, p["direction"],
                                   p["signal_px"], atr14, config)
            if verdict == "wait":
                continue
            done.append(p)
            if verdict == "cancel":
                log.info("[PROBASYON] %s İPTAL — %s", p["scope_key"], info.get("why"))
                if log_gate_skip:
                    log_gate_skip(p["scope_key"], p["mt5_symbol"], p["fx"],
                                  p["direction"], p["signal_px"],
                                  "probation_cancel", extra=info)
                continue
            tick = mt5.symbol_info_tick(p["mt5_symbol"])
            px = (tick.ask if p["direction"] == "BUY" else tick.bid) if tick else 0.0
            drift = (px - p["signal_px"]) * (1 if p["direction"] == "BUY" else -1)
            log.info("[PROBASYON] %s GEÇTİ (%s) → market giriş @%.2f "
                     "(sinyale göre %+.1fpt %s)", p["scope_key"], info.get("why"),
                     px, drift, "kötü" if drift > 0 else "iyi")
            p["opener"]()
        except Exception as exc:                       # kör giriş yapma
            log.warning("[PROBASYON] %s değerlendirilemedi (%s) → İPTAL",
                        p["scope_key"], exc)
            if p not in done:
                done.append(p)
    for p in done:
        if p in _pending:
            _pending.remove(p)
