"""shadow_log.py — gölge kural kayıtları + sonradan çözümleme (Faz 2/3).

Canlı icraya HİÇ dokunmaz. İki iş yapar:

1. `record_shadow(...)` — bir gölge kuralın "ben bloklardım / ben beklerdim"
   kararını karar anındaki fiyat+geometriyle `gate_skipped.jsonl`'e yazar
   (sızıntısız: sonuç bilinmeden kaydedilir).
2. `resolve_pending(...)` — bot her taramada çağırır; yeterli bar geçmiş
   kayıtların sonucunu 1m barlardan ölçüp `shadow_followup.jsonl`'e yazar:
     * Faz 2 kuralları  → GERÇEK geometriyle çözüm (scope'un TP/SL mesafesi,
       bar-bar yarış, en fazla OUTCOME_MAX_MIN) + sonraki 10 barın özeti.
       ⚠️ 2026-09-02 DÜZELTMESİ: eskiden YALNIZ 10 barlık MFE/MAE yazılıyordu.
       TP'si 80 / SL'i 110 puan olan bir işlemi 10 bar çözemez — bu yüzden
       946 kayıtlık POS_TIGHT gölge karnesi backtest ile ÇELİŞİYORDU ve
       hiçbir kapı kararı kanıtla kapanamıyordu.
     * Faz 3 probasyon  → 5 barlık gürültü bandı verdikti + hipotetik TP/SL sonucu

Durum `shadow_pending.json`'da tutulur (restart-dayanıklı). Tüm yollar fail-open:
bu modülün hatası emir akışını ASLA etkilemez.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Sequence

import phase_rules as pr

HERE = Path(__file__).resolve().parent
GATE_SKIP_JSONL = HERE / "gate_skipped.jsonl"
FOLLOWUP_JSONL = HERE / "shadow_followup.jsonl"
PENDING_FILE = HERE / "shadow_pending.json"

# ⚠️ 2026-09-05 SAHTE ÇOĞALTMA DÜZELTMESİ
# Bot 60-75 sn'de bir tarıyor ve aynı KOŞUL sürdükçe aynı gölge kararını tekrar
# tekrar yazıyordu: XAUUSD 617 kayıt = 36 gerçek olay (17,1× şişme), GDAXI 113
# kayıt = 14 olay (8,1×). Bu, karnedeki n'i sahte büyütüp p değerlerini
# felaket derecede yanlış gösterdi (GDAXI p~1e-10 sanıldı, gerçekte 0,022).
# Artık: aynı (scope, kural) için EPIZOD_SESSIZLIK boyunca sessizlik olmadan
# ikinci kayıt YAZILMAZ. Bir epizod = kapının aralıksız ateşlediği süre.
EPIZOD_SESSIZLIK = 1800           # sn — bu kadar sessizlikten sonra YENİ epizod
_son_gorulme: dict = {}           # (scope, kural) -> son ateşleme zamanı

FOLLOWUP_BARS = 10                # Faz-2: kısa özet (geriye dönük uyumluluk)
FOLLOWUP_MAX_MIN = 480            # Faz-2: gerçek TP/SL çözümü için üst sınır
OUTCOME_MAX_MIN = 480             # Faz-3: hipotetik işlem en fazla 8 saat izlenir

_pending: Optional[list] = None


# ── durum ────────────────────────────────────────────────────────────────────

def _load() -> list:
    global _pending
    if _pending is None:
        try:
            _pending = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
        except Exception:
            _pending = []
    return _pending


def _save() -> None:
    try:
        PENDING_FILE.write_text(json.dumps(_pending or [], ensure_ascii=False,
                                           indent=1), encoding="utf-8")
    except Exception:
        pass


def _append(path: Path, rec: dict) -> None:
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── 1) kayıt ────────────────────────────────────────────────────────────────

def record_shadow(scope_key: str, forexsai_sym: str, mt5_symbol: str,
                  direction: str, rule: str, decision: str, price: float,
                  sl: float | None = None, tp: float | None = None,
                  extra: dict | None = None, follow: bool = True,
                  tp_dist: float | None = None,
                  sl_dist: float | None = None) -> None:
    """Gölge kararı yaz + (follow=True ise) sonuç takibine al.

    decision: 'would_block' | 'would_wait' | 'would_allow' — kural gerçekten
    uygulansaydı ne olurdu. Canlı davranış BUNDAN ETKİLENMEZ.

    tp_dist/sl_dist: scope'un GERÇEK geometrisi (puan). Verilirse çözümleme
    10 barlık özet yerine gerçek TP/SL yarışıyla yapılır — karar verilebilir
    bir karne ancak böyle çıkar (bkz. modül başlığındaki 2026-09-02 düzeltmesi).
    """
    try:
        # ── EPIZOD BASTIRMA: süregelen aynı koşulu tekrar yazma ────────────
        _anahtar = (scope_key, rule)
        _simdi = time.time()
        _onceki = _son_gorulme.get(_anahtar)
        _son_gorulme[_anahtar] = _simdi
        if _onceki is not None and (_simdi - _onceki) <= EPIZOD_SESSIZLIK:
            return                     # aynı epizodun tekrarı — kayıt YOK

        rec = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "scope": scope_key, "symbol": forexsai_sym, "mt5_symbol": mt5_symbol,
            "direction": direction, "reason": f"shadow:{rule}",
            "rule": rule, "decision": decision,
            "price": round(float(price), 5),
            "sl": None if sl is None else round(float(sl), 5),
            "tp": None if tp is None else round(float(tp), 5),
            "shadow": True,
        }
        if extra:
            rec.update(extra)
        _append(GATE_SKIP_JSONL, rec)
        if not follow:
            return
        p = _load()
        p.append({
            "id": f"{int(time.time()*1000)}_{scope_key}_{rule}",
            "ts": rec["ts"], "t0": time.time(), "stage": "followup",
            "scope": scope_key, "symbol": forexsai_sym, "mt5_symbol": mt5_symbol,
            "direction": direction, "rule": rule, "decision": decision,
            "price": rec["price"], "sl": rec["sl"], "tp": rec["tp"],
            "tp_dist": None if tp_dist is None else float(tp_dist),
            "sl_dist": None if sl_dist is None else float(sl_dist),
            "extra": extra or {},
        })
        _save()
    except Exception:
        pass


def record_probation(scope_key: str, forexsai_sym: str, mt5_symbol: str,
                     direction: str, signal_price: float, atr_1m: float,
                     tp_dist: float, sl_dist: float, config=None) -> None:
    """Faz-3 MOD-E: sinyal anını kaydet; 5 bar sonra bandı ve sonucu ölç."""
    try:
        bars = int(pr.flag(config, "PROBATION_BARS"))
        z = float(pr.flag(config, "PROBATION_Z"))
        band = pr.probation_band(atr_1m, bars, z)
        _append(GATE_SKIP_JSONL, {
            "ts": datetime.now(timezone.utc).isoformat(), "scope": scope_key,
            "symbol": forexsai_sym, "mt5_symbol": mt5_symbol,
            "direction": direction, "reason": "shadow:probation_signal",
            "rule": "probation", "decision": "would_wait",
            "price": round(float(signal_price), 5),
            "atr_1m": round(float(atr_1m), 3), "band": round(band, 3),
            "tp_dist": round(float(tp_dist), 2), "sl_dist": round(float(sl_dist), 2),
            "shadow": True,
        })
        p = _load()
        p.append({
            "id": f"{int(time.time()*1000)}_{scope_key}_probation",
            "ts": datetime.now(timezone.utc).isoformat(), "t0": time.time(),
            "stage": "probation", "scope": scope_key, "symbol": forexsai_sym,
            "mt5_symbol": mt5_symbol, "direction": direction, "rule": "probation",
            "decision": "would_wait", "price": round(float(signal_price), 5),
            "atr_1m": float(atr_1m), "band": band, "bars": bars,
            "tp_dist": float(tp_dist), "sl_dist": float(sl_dist), "extra": {},
        })
        _save()
    except Exception:
        pass


# ── 2) çözümleme ────────────────────────────────────────────────────────────

def _bars_since(fetch_bars: Callable[[str, int], Optional[Sequence[dict]]],
                mt5_symbol: str, age_sec: float, want: int) -> list[dict]:
    """Karardan bu yana geçen ~dakika kadar 1m bar (en fazla `want` adet)."""
    n_since = int(age_sec // 60)
    if n_since < 1:
        return []
    bars = fetch_bars(mt5_symbol, min(max(n_since, want) + 2, 600)) or []
    take = min(n_since, want)
    return list(bars)[-take:] if take > 0 else []


def _excursions(direction: str, ref: float, bars: Sequence[dict]) -> tuple[float, float]:
    """(lehe_max, aleyhe_max) — ref fiyata göre, yön düzeltmeli."""
    if not bars:
        return 0.0, 0.0
    hi = max(float(b["high"]) for b in bars)
    lo = min(float(b["low"]) for b in bars)
    if direction == "BUY":
        return max(hi - ref, 0.0), max(ref - lo, 0.0)
    return max(ref - lo, 0.0), max(hi - ref, 0.0)


def _hypothetical_outcome(direction: str, entry: float, tp_dist: float,
                          sl_dist: float, bars: Sequence[dict]) -> Optional[str]:
    """Bar-bar TP/SL yarışı. Aynı barda ikisi de → konservatif LOSS."""
    for b in bars:
        h, l = float(b["high"]), float(b["low"])
        if direction == "BUY":
            hit_tp, hit_sl = h >= entry + tp_dist, l <= entry - sl_dist
        else:
            hit_tp, hit_sl = l <= entry - tp_dist, h >= entry + sl_dist
        if hit_sl:
            return "LOSS"
        if hit_tp:
            return "WIN"
    return None


def resolve_pending(fetch_bars: Callable[[str, int], Optional[Sequence[dict]]],
                    log=None) -> None:
    """Bot her taramada çağırır. Fail-open."""
    try:
        pend = _load()
        if not pend:
            return
        now = time.time()
        keep: list[dict] = []
        changed = False
        for it in pend:
            try:
                age = now - float(it.get("t0") or now)
                stage = it.get("stage")

                if stage == "followup":
                    tp_d, sl_d = it.get("tp_dist"), it.get("sl_dist")
                    geo = tp_d and sl_d
                    # Geometri varsa: yarış çözülene kadar bekle (tavan
                    # FOLLOWUP_MAX_MIN). Yoksa eski 10-bar davranışı.
                    if age < (FOLLOWUP_BARS + 1) * 60:
                        keep.append(it); continue
                    if geo:
                        uzun = _bars_since(fetch_bars, it["mt5_symbol"], age,
                                           min(int(age // 60) + 2, 600))
                        sonuc = _hypothetical_outcome(it["direction"], it["price"],
                                                      float(tp_d), float(sl_d), uzun)
                        if sonuc is None and age < FOLLOWUP_MAX_MIN * 60:
                            keep.append(it); continue     # yarış sürüyor, bekle
                    else:
                        sonuc = None
                    bars = _bars_since(fetch_bars, it["mt5_symbol"], age, FOLLOWUP_BARS)
                    fav, adv = _excursions(it["direction"], it["price"], bars)
                    _append(FOLLOWUP_JSONL, {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "decided_at": it["ts"], "scope": it["scope"],
                        "symbol": it["symbol"], "direction": it["direction"],
                        "rule": it["rule"], "decision": it["decision"],
                        "price": it["price"], "bars": len(bars),
                        "next10_high": max((float(b["high"]) for b in bars), default=None),
                        "next10_low": min((float(b["low"]) for b in bars), default=None),
                        "next10_close": float(bars[-1]["close"]) if bars else None,
                        "mfe": round(fav, 2), "mae": round(adv, 2),
                        # ⭐ asıl karne: gerçek TP/SL yarışının sonucu
                        "outcome": sonuc,          # WIN | LOSS | None(çözülmedi)
                        "tp_dist": tp_d, "sl_dist": sl_d,
                        "extra": it.get("extra") or {},
                    })
                    changed = True
                    continue

                if stage == "probation":
                    need = (int(it.get("bars", 5)) + 1) * 60
                    if age < need:
                        keep.append(it); continue
                    seg = _bars_since(fetch_bars, it["mt5_symbol"], age, int(it.get("bars", 5)))
                    cancel, adverse, band = pr.probation_verdict(
                        it["direction"], it["price"], it.get("atr_1m") or 0.0,
                        seg, int(it.get("bars", 5)))
                    if cancel or not seg:
                        _append(FOLLOWUP_JSONL, {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "decided_at": it["ts"], "scope": it["scope"],
                            "symbol": it["symbol"], "direction": it["direction"],
                            "rule": "probation", "decision": "cancelled" if cancel else "no_data",
                            "signal_price": it["price"], "adverse": round(adverse, 2),
                            "band": round(band, 2), "outcome": None,
                        })
                        changed = True
                        continue
                    entry = float(seg[-1]["close"])
                    it.update({"stage": "probation_outcome", "entry": entry,
                               "t_entry": now, "adverse": adverse, "band": band})
                    keep.append(it)
                    changed = True
                    continue

                if stage == "probation_outcome":
                    since_entry = now - float(it.get("t_entry") or now)
                    bars = _bars_since(fetch_bars, it["mt5_symbol"], since_entry, 600)
                    outcome = _hypothetical_outcome(
                        it["direction"], it["entry"], it["tp_dist"], it["sl_dist"], bars)
                    if outcome is None and since_entry < OUTCOME_MAX_MIN * 60:
                        keep.append(it); continue
                    _append(FOLLOWUP_JSONL, {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "decided_at": it["ts"], "scope": it["scope"],
                        "symbol": it["symbol"], "direction": it["direction"],
                        "rule": "probation", "decision": "entered",
                        "signal_price": it["price"], "entry": it["entry"],
                        "slippage_vs_signal": round(
                            (it["entry"] - it["price"]) *
                            (1 if it["direction"] == "BUY" else -1), 2),
                        "adverse": round(it.get("adverse", 0.0), 2),
                        "band": round(it.get("band", 0.0), 2),
                        "tp_dist": it["tp_dist"], "sl_dist": it["sl_dist"],
                        "minutes": round(since_entry / 60, 1),
                        "outcome": outcome or "TIMEOUT",
                    })
                    changed = True
                    continue

                changed = True          # bilinmeyen aşama → düş
            except Exception:
                changed = True          # bozuk kayıt kuyruğu tıkamasın
        if changed:
            globals()["_pending"] = keep
            _save()
            if log:
                log.debug("[GÖLGE] bekleyen kayıt: %d", len(keep))
    except Exception as exc:
        if log:
            log.debug("shadow resolve fail-open: %s", exc)
