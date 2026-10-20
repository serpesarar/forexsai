"""xau_swing_shadow.py — XAUUSD "Golden Donchian" günlük swing GÖLGE kaydı (yalnız BUY).

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Sinyali ve sonradan sonucunu `xau_swing_shadow.jsonl`'e yazar; hatalar fail-open.

KANIT: 2026-06-16 `xau_swing_research/` (broker D1 2021-05→2026-04: 31 işlem, WR %64,5, +0,69R, 5/5 WF katı +) ve
2026-10-20 bağımsız dönem XS-01 (`research/xau_swing_oos_20261020/`, Dukascopy 2008-01→2021-04, kural değişmeden):
54 işlem, ortR +0,39 (her gün BUY tabanı +0,15), P(EV>0) %98, iki yarı +. Toplam 18 yılda 86 işlem → kartın hacim
ölçütü (≥150) yapısal olarak geçilemiyor → 2. KURAL gereği GÖLGE. Gerçek dolum/spread farkını ölçmek için kaydedilir.

KURAL (dondurulmuş — değiştirmek kanıtı geçersiz kılar):
  * D1 (broker günü ≈ NY 17:00) kapanışı ≥ önceki 55 D1 barın en yükseği ∧ kapanış > EMA200(D1, adjust=False).
  * Giriş: sonraki D1 barının açılışı (araştırma bacağı) + canlı bacak = tespit anındaki ask.
  * SL = giriş − 2×ATR14(D1, sinyal barı dahil), TP = giriş + 4×ATR14; H1 içinde aynı barda önce SL.
  * Zaman stopu: girişten itibaren 480 H1 barı (≈ 20 gün) → son barın kapanışı. Tek pozisyon. Sürtünme $0,40.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "xau_swing_shadow.jsonl"
STATE_FILE = HERE / "xau_swing_shadow_state.json"

DON_N = 55
EMA_N = 200
ATR_N = 14
SL_K = 2.0
TP_K = 4.0
HOLD_H1 = 20 * 24
FRICTION = 0.40
FETCH_D1 = 1000            # EMA200 ısınması: (1 − 2/201)^1000 ≈ e^−10
FETCH_H1 = 900
POLL_EVERY_S = 300


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def ema_series(closes: list[float], span: int = EMA_N) -> list[float]:
    a = 2.0 / (span + 1)
    out: list[float] = []
    for i, c in enumerate(closes):
        out.append(c if i == 0 else a * c + (1 - a) * out[-1])
    return out


def atr_at(d1: list[dict], i: int, n: int = ATR_N) -> float | None:
    if i < n:
        return None
    trs = []
    for j in range(i - n + 1, i + 1):
        h, l, pc = d1[j]["h"], d1[j]["l"], d1[j - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs) / n


def is_signal(d1: list[dict], i: int, ema: list[float]) -> bool:
    """Kapanmış D1 barı i sinyal mi (yalnız ≤ i verisi)."""
    if i < max(DON_N, EMA_N) or i >= len(d1):
        return False
    hh = max(b["h"] for b in d1[i - DON_N:i])
    return d1[i]["c"] >= hh and d1[i]["c"] > ema[i]


def advance(ev: dict, h1: list[dict]) -> str:
    """Açık olayı H1 barlarıyla ilerlet. Dönüş: 'open' | 'tp' | 'sl' | 'time'. ev yerinde güncellenir."""
    seq = [b for b in h1 if b["t"] >= ev["entry_t"]]
    for k, b in enumerate(seq[:HOLD_H1]):
        if b["l"] <= ev["sl"]:
            return _close(ev, "sl", ev["sl"], b["t"])
        if b["h"] >= ev["tp"]:
            return _close(ev, "tp", ev["tp"], b["t"])
    if len(seq) >= HOLD_H1:
        b = seq[HOLD_H1 - 1]
        return _close(ev, "time", b["c"], b["t"])
    return "open"


def _close(ev: dict, how: str, px: float, t: float) -> str:
    risk = ev["entry"] - ev["sl"]
    ev.update(status=how, exit_px=px, exit_t=t, R=(px - ev["entry"] - FRICTION) / risk if risk > 0 else None)
    if ev.get("live_entry"):
        ev["R_live"] = (px - ev["live_entry"]) / risk if risk > 0 else None
    return how


def step(st: dict, d1: list[dict], h1: list[dict], live_ask: float | None = None) -> list[dict]:
    """d1: kapanmış barlar + sonda oluşmakta olan bar. Yeni/kapanan olay kayıtlarını döndürür."""
    recs: list[dict] = []
    for ev in st["open"]:
        if advance(ev, h1) != "open":
            recs.append(dict(ev, kind="close"))
    st["open"] = [e for e in st["open"] if e.get("status") in (None, "open")]
    if len(d1) < 2:
        return recs
    i = len(d1) - 2                                # son KAPANMIŞ D1 barı
    key = int(d1[i]["t"])
    if key == st.get("last_checked"):
        return recs
    st["last_checked"] = key
    ema = ema_series([b["c"] for b in d1[:i + 1]])
    if not is_signal(d1, i, ema):
        return recs
    if st["open"]:
        recs.append({"kind": "skip_busy", "signal_t": key})
        return recs
    a = atr_at(d1, i)
    if not a:
        return recs
    entry = d1[i + 1]["o"]
    ev = {"signal_t": key, "entry_t": int(d1[i + 1]["t"]), "entry": entry, "atr": a,
          "sl": entry - SL_K * a, "tp": entry + TP_K * a, "status": "open",
          "signal_close": d1[i]["c"], "hh55": max(b["h"] for b in d1[i - DON_N:i]), "ema200": ema[i],
          "live_entry": live_ask}
    st["open"].append(ev)
    recs.append(dict(ev, kind="open"))
    return recs


# ═════════════════════════ MT5 kabuğu ═════════════════════════

def _bars(rates) -> list[dict]:
    return [{"t": int(r["time"]), "o": float(r["open"]), "h": float(r["high"]), "l": float(r["low"]),
             "c": float(r["close"])} for r in (rates if rates is not None else [])]


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"open": [], "last_checked": None, "last_poll": 0}


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    rec = dict(rec, logged_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    with open(EVENTS_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def poll(mt5, log, resolve_symbol, now: float | None = None, force: bool = False) -> list[dict]:
    """Botun ana döngüsünden çağrılır (try/except içinde). Emir YOK."""
    now = time.time() if now is None else now
    st = _load_state()
    if not force and now - st.get("last_poll", 0) < POLL_EVERY_S:
        return []
    st["last_poll"] = now
    sym = resolve_symbol("XAUUSD")
    d1 = _bars(mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, FETCH_D1))
    h1 = _bars(mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, FETCH_H1))
    tick = mt5.symbol_info_tick(sym)
    recs = step(st, d1, h1, live_ask=float(tick.ask) if tick is not None else None)
    for r in recs:
        _append(r)
        log.info("[GÖLGE] XAU swing %s — giriş %.2f SL %.2f TP %.2f %s", r["kind"], r.get("entry", 0.0),
                 r.get("sl", 0.0), r.get("tp", 0.0), f"R={r['R']:.2f}" if r.get("R") is not None else "")
    _save_state(st)
    return recs
