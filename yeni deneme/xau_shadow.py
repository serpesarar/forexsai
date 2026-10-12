"""xau_shadow.py — XAUUSD 1h "yeni 20-mum tepesinde BUY" GÖLGE kaydı.

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Yalnız sinyal anını ve sonradan sonucu `xau_shadow.jsonl`'e yazar.
Hatalar fail-open: bot akışı etkilenmez (çağıran try/except içinde kullanır).

KANIT (research/pinbar_20261010, MK-03/MK-04, 2026-10-10): XAU 1h, 2016-06 → 2026-08, tek pozisyon, SL 1,5×ATR,
20 mum zaman çıkışı → 1.857 işlem, +0,107R; aynı stoplu rastgele BUY +0,042R (max +0,093); 9/11 yıl pozitif.
Kart 5/6: icra ölçütü ✗ — sinyal mumu kapanışından giriş +0,169R, gerçek giriş +0,107R. Bu gölgenin asıl amacı
GERÇEK dolum farkını ölçmektir (alan: slip_r = (entry_ask − paper_close)/stop_dist).
Uyarılar: kural XAU'da post-hoc seçildi (genel "yeni tepede al" sınavı USOIL'de geçmedi); 2016-26 altın boğa piyasası;
XAU gün-içi botta KAPALI (BLOCKED_SYMBOLS) — bu yüzden gölge.

KURAL (araştırma scan.features/deep.pin_mask(kind="hepsi") ile birebir):
  * Sinyal: son KAPANMIŞ 1h barın yükseği ≥ ondan önceki 20 barın en yükseği.
  * ATR = sinyal barından ÖNCEKİ 14 barın ortalama gerçek aralığı (sinyal barı dahil DEĞİL).
  * Giriş: sinyal barı kapandıktan hemen sonra ask (araştırmada sonraki barın açılışı + 0,25 spread).
  * Stop = giriş − 1,5×ATR; çıkış: giriş barından itibaren 20. 1h barın kapanışı; stop barın düşüğü ≤ stop → stop
    (boşluk → bar açılışı). R = (çıkış − giriş) / (1,5×ATR).
  * Tek pozisyon: açık gölge olayı varken yeni sinyal 'overlap' olarak kaydedilir ama açılmaz; olay stop veya
    20. barda sonuçlanınca boşalır (sonuçlandığı barda gelen sinyal de overlap sayılır — araştırmayla aynı).
"""
from __future__ import annotations

import json
import time
from datetime import timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "xau_shadow.jsonl"
STATE_FILE = HERE / "xau_shadow_state.json"

# ── dondurulmuş kural parametreleri (değiştirmek kanıtı geçersiz kılar) ──────────
LOOK = 20
ATR_N = 14
STOP_K = 1.5
HOLD = 20
BAR_S = 3600
MAX_LATE_S = 600            # bar kapanışından bu kadar sonra tespit → geçersiz (dolum gecikmesi çok büyük)
FETCH_H1 = 200
POLL_EVERY_S = 30
MAX_GAP_S = 4 * 86400       # araştırmadaki seg kuralı: bar arası > 4 gün → veri boşluğu
EXPIRE_S = 20 * 86400


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def _contiguous(bars: list[dict]) -> bool:
    return all(b["t"] - a["t"] <= MAX_GAP_S for a, b in zip(bars, bars[1:]))


def atr_before(bars: list[dict], i: int) -> float | None:
    """bars[i-14 .. i-1] ortalama gerçek aralık (bars[i] dahil değil). TR ilk barda önceki kapanışa ihtiyaç duyar."""
    if i < ATR_N + 1:
        return None
    tr = []
    for j in range(i - ATR_N, i):
        pc = bars[j - 1]["close"]
        tr.append(max(bars[j]["high"] - bars[j]["low"], abs(bars[j]["high"] - pc), abs(bars[j]["low"] - pc)))
    return sum(tr) / ATR_N


def is_signal(bars: list[dict], i: int) -> bool:
    """bars[i] yeni tepe mi: yüksek ≥ bars[i-20..i-1] en yükseği; pencere kesintisiz."""
    if i < LOOK + 1:
        return False
    win = bars[max(0, i - LOOK - ATR_N - 1): i + 1]
    if not _contiguous(win):
        return False
    return bars[i]["high"] >= max(b["high"] for b in bars[i - LOOK: i])


def resolve(ev: dict, bars: list[dict]) -> dict | None:
    """Olay için sonuç. Stop görüldüğü AN sonuçlanır (gerçek strateji stopta çıkar → pozisyon boşalır);
    stop yoksa giriş barından itibaren 20 kapanmış bar dolunca zaman çıkışı. Aksi halde None.

    bars: UTC 't' = bar başı, artan, yalnız KAPANMIŞ barlar. Giriş barı = t ≥ sig_t + 3600 olan ilk bar."""
    seq = [b for b in bars if b["t"] >= ev["sig_t"] + BAR_S][:HOLD]
    if not seq:
        return None
    entry, stop, sd = ev["entry_ask"], ev["stop"], ev["stop_dist"]
    out = how = None
    j_exit = len(seq) - 1
    for j, b in enumerate(seq):
        if j and b["t"] - seq[j - 1]["t"] > MAX_GAP_S:
            return {**ev, "status": "void", "reason": "veri boşluğu"}
        if b["low"] <= stop:
            out, how, j_exit = (min(b["open"], stop) if j > 0 else stop), "stop", j
            break
    if how is None:
        if len(seq) < HOLD:
            return None
        out, how = seq[-1]["close"], "time"
    res = {**ev, "status": "done", "how": how, "exit_px": out, "exit_bar_t": seq[j_exit]["t"],
           "R": round((out - entry) / sd, 4), "R_paper": round((out - ev["paper_close"]) / sd, 4),
           "R_research": round((out - (seq[0]["open"] + ev.get("spread_assumed", 0.25))) / sd, 4),
           "entry_bar_open": seq[0]["open"], "bars_held": j_exit + 1}
    res["slip_r"] = round((entry - ev["paper_close"]) / sd, 4)
    return res


# ═════════════════════════ durum / kayıt ═════════════════════════

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"last_bar": None, "open": []}


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with open(EVENTS_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **rec}, ensure_ascii=False) + "\n")


def _h1(rates, off_s: int) -> list[dict]:
    return [{"t": int(r["time"]) - off_s, "open": float(r["open"]), "high": float(r["high"]),
             "low": float(r["low"]), "close": float(r["close"])} for r in rates]


# ═════════════════════════ MT5 sarmalayıcı (emir yok) ═════════════════════════

_last_poll = 0.0


def poll(mt5, log, resolve_symbol, offset_fn, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK. Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if not force and now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    sym = resolve_symbol("XAUUSD")
    if not sym:
        return
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 1, FETCH_H1)       # 1 → koşan bar hariç
    if rates is None or len(rates) < LOOK + ATR_N + 5:
        return
    bars = _h1(rates, offset_fn(sym))
    st = _load_state()
    changed = False

    # 1) yeni kapanmış bar → sinyal?
    last = bars[-1]
    if st.get("last_bar") != last["t"]:
        st["last_bar"] = last["t"]
        changed = True
        i = len(bars) - 1
        if is_signal(bars, i):
            late = now - (last["t"] + BAR_S)
            atr = atr_before(bars, i)
            tick = mt5.symbol_info_tick(sym)
            base = {"sig_t": last["t"], "sig_high": last["high"], "paper_close": last["close"], "atr": atr,
                    "latency_s": round(late, 1)}
            if atr is None or tick is None:
                _append({"kind": "skip", "reason": "ATR/tick yok", **base})
            elif late > MAX_LATE_S:
                _append({"kind": "skip", "reason": "geç tespit", **base})
            elif st["open"]:
                _append({"kind": "skip", "reason": "overlap (açık gölge olayı var)", **base})
                log.info("XAU-GÖLGE sinyal ama açık olay var → atlandı (tek pozisyon)")
            else:
                ask, bid = float(tick.ask), float(tick.bid)
                sd = STOP_K * atr
                ev = {**base, "entry_t": now, "entry_ask": ask, "entry_bid": bid, "spread": round(ask - bid, 3),
                      "spread_assumed": 0.25, "stop": ask - sd, "stop_dist": sd, "status": "open"}
                st["open"].append(ev)
                _append({"kind": "event", **ev})
                log.info("XAU-GÖLGE yeni 20-mum tepesi: ask=%.2f stop=%.2f (1.5×ATR=%.2f) kapanış→ask kayması %.2f (EMİR YOK)",
                         ask, ev["stop"], sd, ask - last["close"])

    # 2) açık olayların çözümü
    still = []
    for ev in st["open"]:
        r = resolve(ev, bars)
        if r is None:
            if now - ev["sig_t"] > EXPIRE_S:
                _append({"kind": "result", **ev, "status": "expired"})
                changed = True
            else:
                still.append(ev)
            continue
        _append({"kind": "result", **r})
        log.info("XAU-GÖLGE sonuç: %s R=%s (paper %s, research %s, slip_r %s)", r.get("how"), r.get("R"),
                 r.get("R_paper"), r.get("R_research"), r.get("slip_r"))
        changed = True
    if changed or len(still) != len(st["open"]):
        st["open"] = still
        _save_state(st)
