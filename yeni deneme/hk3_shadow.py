"""hk3_shadow.py — USDHKD 7,75 taahhüt ucu alımı (HK3) İLERİ GÖLGE kaydı.

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ (Pepperstone'da USDHKD zaten işleme kapalı: trade_mode = 0; fiyat yayınlanıyor).
Yalnız sanal giriş/çıkışı `hk3_shadow.jsonl`'e yazar. Hatalar bot akışını etkilemez (çağıran try/except içinde kullanır).

KANIT: research/fx_yuksek_isabet_20261120/PROTOCOL.md EK-8, `hk3.py`, defter §2.108 YI-08 (sınıf B).
  2010–2026 H1: 71 işlem, isabet %91,5, ort +2,1 bp, en kötü −9,4 bp; ayda ort. 0,37 işlem (194 ayın 38'inde, kümeli).
  Hayalet seviyeler (7,77…7,82) %53–62 ve eksi → kazanç HKMA taahhüdünden.

KURAL (dondurulmuş): kapanmış H1 barının kapanışı ≤ 7,7520 → sonraki H1 barının açılışında AL. SL 7,7470 (en az 5 pip),
  TP giriş + 20 pip, en çok 1.500 H1 bar; aynı barda TP ve SL → SL; aynı anda tek sanal pozisyon.
  bp_model = bar fiyatları − maliyet (1,5 × bar spread + 0,7 bp, araştırmayla aynı); bp_fill = tespit anındaki gerçek ask/bid.

Karne:   python hk3_shadow.py --karne
Kapatma: config.HK3_SHADOW_ENABLED = False
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "hk3_shadow.jsonl"
STATE_FILE = HERE / "hk3_state.json"
SYMBOL = "USDHKD"
TRIG, SL_LVL, PIP, TP_PIP, MIN_SL_PIP, HOLD_BARS = 7.7520, 7.7470, 0.0001, 20, 5, 1500
COMM_BP, SPREAD_MULT = 0.7, 1.5
POLL_EVERY_S = 60
FETCH_BARS = 60
_last_poll = 0.0


# ═════════════════════════ saf mantık (mt5 olmadan test edilir) ═════════════════════════

def cost_bp(spread_pts: float, point: float, price: float) -> float:
    return SPREAD_MULT * spread_pts * point / price * 1e4 + COMM_BP


def find_entry(bars: list[dict], last_t: int) -> tuple[int, dict] | None:
    """bars: eskiden yeniye KAPANMIŞ H1 ({'t','o','h','l','c','sp'}). last_t'den sonra kapanışı ≤ TRIG olan ilk barın
    ardından gelen barı döndürür (sinyal barı indeksi, giriş barı). Giriş barı henüz yoksa None."""
    for i, b in enumerate(bars):
        if b["t"] <= last_t or b["c"] > TRIG:
            continue
        if i + 1 < len(bars):
            return i, bars[i + 1]
        return None
    return None


def levels(entry_open: float, signal_close: float) -> tuple[float, float]:
    """(TP fiyatı, SL fiyatı). SL mesafesi = max(sinyal kapanışı − 7,7470, 5 pip), girişten ölçülür (araştırma gibi)."""
    d = max(signal_close - SL_LVL, MIN_SL_PIP * PIP)
    return entry_open + TP_PIP * PIP, entry_open - d


def resolve(pos: dict, bars_after: list[dict]) -> dict | None:
    """Giriş barından itibaren kapanmış barlar. Sonuç hazırsa çıkış kaydı, değilse None."""
    for i, b in enumerate(bars_after[:HOLD_BARS]):
        hit_sl, hit_tp = b["l"] <= pos["sl"], b["h"] >= pos["tp"]
        if hit_sl or hit_tp:
            x, why = (pos["sl"], "SL") if hit_sl else (pos["tp"], "TP")
            return {"X": x, "why": why, "bars": i + 1, "t_out": b["t"]}
    if len(bars_after) >= HOLD_BARS:
        b = bars_after[HOLD_BARS - 1]
        return {"X": b["c"], "why": "ZAMAN", "bars": HOLD_BARS, "t_out": b["t"]}
    return None


def summarize(recs: list[dict]) -> dict:
    res = [r for r in recs if r.get("kind") == "result"]
    if not res:
        return {"n": 0, "sinyal": sum(r.get("kind") == "entry" for r in recs), "kanit": "2010–26 n 71 %91,5 +2,1 bp"}
    v = [r["bp_model"] for r in res]
    w = [r.get("bp_model_swap", r["bp_model"]) for r in res]
    return {"n": len(v), "isabet_swapsiz": round(100 * sum(x > 0 for x in v) / len(v), 1), "ort_bp_swapsiz": round(sum(v) / len(v), 2),
            "isabet_swapli": round(100 * sum(x > 0 for x in w) / len(w), 1), "ort_bp_swapli": round(sum(w) / len(w), 2),
            "en_kotu": min(v), "kanit": "2010–26 n 71: swapsız %85,9 +0,6 bp / swaplı %91,5 +2,1 bp"}


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st.setdefault("pos", None)
    st.setdefault("last_t", 0)          # işlenmiş son sinyal barı (sunucu epoch)
    return st


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ═════════════════════════ adım + MT5 adaptörü ═════════════════════════

def swap_nights(t_in: int, t_out: int) -> int:
    """Sunucu günü değişimi sayısı (devir 00:00 sunucu); Çarşamba devri ×3 (araştırma swap_adj gibi)."""
    d0, d1 = t_in // 86400, t_out // 86400
    n = 0
    for d in range(d0 + 1, d1 + 1):
        wd = (d + 3) % 7                          # 1970-01-01 Perşembe → 0=Pzt … 6=Paz
        if wd >= 5:
            continue                              # hafta sonu sunucu günü yok (bar yok)
        n += 3 if wd == 3 else 1                  # Perşembe'ye geçiş = Çarşamba devri ×3
    return n


def step(st: dict, bars: list[dict], tick: tuple[float, float] | None, point: float, log, swap_long_pts: float = 0.0) -> bool:
    """bars: kapanmış H1 barları. tick: (ask, bid). Değişiklik olduysa True."""
    changed = False
    if st["pos"] is None:
        if st["last_t"] == 0 and bars:
            st["last_t"] = bars[-1]["t"]          # ilk çalıştırma: geçmişi işleme, yalnız bundan sonrasını izle
            return True
        hit = find_entry(bars, st["last_t"])
        if hit is not None:
            i, e = hit
            s = bars[i]
            tp, sl = levels(e["o"], s["c"])
            st["pos"] = {"t_sig": s["t"], "t_in": e["t"], "E": e["o"], "tp": tp, "sl": sl, "sig_c": s["c"],
                         "cost": round(cost_bp(e.get("sp", 0), point, e["o"]), 3), "fill": tick[0] if tick else None,
                         "swap_pts": swap_long_pts, "point": point}
            st["last_t"] = s["t"]
            _append({"kind": "entry", **st["pos"]})
            log.info("HK3-GÖLGE AL USDHKD E=%.5f TP=%.5f SL=%.5f (sinyal kapanışı %.5f) — EMİR YOK", e["o"], tp, sl, s["c"])
            changed = True
        elif bars and bars[-1]["c"] > TRIG:
            st["last_t"] = bars[-1]["t"]
    if st["pos"] is not None:
        p = st["pos"]
        r = resolve(p, [b for b in bars if b["t"] >= p["t_in"]])
        if r is not None:
            bp_model = round((r["X"] / p["E"] - 1) * 1e4 - p["cost"], 2)
            bp_fill = round((tick[1] / p["fill"] - 1) * 1e4, 2) if (tick and p.get("fill")) else None
            nights = swap_nights(p["t_in"], r["t_out"])
            swap_bp = round(nights * p.get("swap_pts", 0.0) * p.get("point", point) / p["E"] * 1e4, 2)
            _append({"kind": "result", "t_in": p["t_in"], "E": p["E"], **r, "bp_model": bp_model, "geceler": nights,
                     "swap_bp": swap_bp, "bp_model_swap": round(bp_model + swap_bp, 2), "bp_fill_yaklasik": bp_fill})
            log.info("HK3-GÖLGE çıkış %s %.5f → %.2f bp (EMİR YOK)", r["why"], r["X"], bp_model)
            st["pos"], st["last_t"] = None, r["t_out"] - 1    # araştırma gibi: çıkış barı yeni sinyal barı olabilir
            changed = True
    return changed


def _bars(mt5) -> tuple[list[dict], float, float]:
    mt5.symbol_select(SYMBOL, True)
    si = mt5.symbol_info(SYMBOL)
    r = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_H1, 1, FETCH_BARS)   # pos 1 → koşan bar hariç (yalnız kapanmış)
    if r is None or si is None:
        return [], 0.0, 0.0
    return [{"t": int(x["time"]), "o": float(x["open"]), "h": float(x["high"]), "l": float(x["low"]), "c": float(x["close"]),
             "sp": float(x["spread"])} for x in r], float(si.point), float(si.swap_long or 0.0)


def poll(mt5, log, cfg=None, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden çağrılır; dakikada bir iş yapar. EMİR YOK. Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if not force and now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    bars, point, swl = _bars(mt5)
    if not bars:
        return
    t = mt5.symbol_info_tick(SYMBOL)
    tick = (float(t.ask), float(t.bid)) if t is not None and t.ask and t.bid else None
    st = _load_state()
    if st["pos"] is not None:          # açık pozisyon 60 bardan uzun sürebilir → giriş barından itibaren çek
        r = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_H1, st["pos"]["t_in"], int(now) + 4 * 3600) if hasattr(mt5, "copy_rates_range") else None
        if r is not None and len(r) > 1:
            bars = [{"t": int(x["time"]), "o": float(x["open"]), "h": float(x["high"]), "l": float(x["low"]),
                     "c": float(x["close"]), "sp": float(x["spread"])} for x in r][:-1]
    if step(st, bars, tick, point, log, swap_long_pts=swl):
        _save_state(st)


def _karne() -> None:
    recs = []
    if EVENTS_JSONL.exists():
        recs = [json.loads(x) for x in EVENTS_JSONL.read_text(encoding="utf-8").splitlines() if x.strip()]
    print(json.dumps(summarize(recs), ensure_ascii=False, indent=1))


if __name__ == "__main__" and "--karne" in sys.argv:
    _karne()
