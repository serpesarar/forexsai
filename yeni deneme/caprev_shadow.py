"""caprev_shadow.py — CAPREV-2 (kapitülasyon alımı) GÖLGE kaydı + K5b gölge yardımcısı.

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Yalnız (a) olay anını, (b) sonradan 1m barlarla
sonucu `caprev_shadow.jsonl`'e yazar ve (c) K5b "stres günü + önceki RTH dibi altı
SELL" kararını gölge olarak işaretlemeye yardım eder. Hatalar fail-open: bot akışı
etkilenmez (çağıran try/except içinde kullanır).

KANIT (research/ndx_gate_forge/NIHAI_RAPOR.md, 2026-10-02):
  Koşul (gün başında bilinir): önceki işlem günü getirisi ≤ −%1,5 VEYA 5g ≤ −%4,
  ve VIX ≥ 18,4, Pzt–Per.
  Kademe 1: seans AÇILIŞINDA al → seans kapanışında çık (aynı gün).
  Kademe 2: pencere içinde önceki RTH dibinin altında İLK 15dk kapanışı → al
            (teyit beklenmez) → ertesi işlem günü kapanışında çık.
  Stop: 1 × günlük volatilite (önceki 20 işlem günü getiri std) × giriş fiyatı.
  NDX 1h/30m/15m ertesi gün +0,34/+0,45/+0,77 R, DAX +0,35/+0,47 (B+; canlı değil).
  Stressiz ∧ yüksek VIX hücresi ≈ 0 → iki şart BİRLİKTE gerekli.

Ölçümler (2026-10-02 eklendi): çıkış (a) seans sonu R_d0, (b) +1R/−1R ilk geçiş R_tp1 (hedef = giriş ask + stop mesafesi;
aynı barda ikisi → stop; hiçbiri değilse R_d0), karışım R_half = ½R_d0 + ½R_tp1; ertesi gün R_d1. VIX: bot günlük SON VIX değerini
kendi durum dosyasında tutar → olayda `vix_prev`, `vix_prev2`, `vix_chg_prev` (= önceki gün − ondan önceki gün) ve `vix_rising`
(araştırmadaki "artan VIX" filtresi: değişim ≥ 0). İlk 2 işlem gününde geçmiş yoksa alanlar None.

Veri: MT5 M15 barları (broker saati → UTC dönüşümü çağıran verir). Seans günü =
yerel takvim günü, RTH = yerel saat aralığı; DST kuralları elle (tzdata bağımsız).
"""
from __future__ import annotations

import json
import math
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "caprev_shadow.jsonl"
STATE_FILE = HERE / "caprev_state.json"

# ── dondurulmuş kural parametreleri (değiştirmek kanıtı geçersiz kılar) ──────────
STRESS_R1 = -0.015
STRESS_R5 = -0.04
VIX_MIN = 18.4
STOP_K = 1.0                    # × günlük vol
SLIP_PTS = 0.2                  # dolum başına ek kayma (araştırmayla aynı)
BAR_MIN = 15                    # tetikleyici/seans barı: M15
VOL_LOOKBACK = 20               # günlük getiri std penceresi
FULL_DAY_FRAC = 0.8             # RTH günü sayılması için bar doluluğu
MAX_LATE_S = 600                # olay barı kapanışından bu kadar sonra tespit → geçersiz
OPEN_GRACE_MIN = 5              # kademe 1: açılıştan sonra ilk 5 dk içinde alınabilir
FETCH_M15 = 3500                # ≈ 36 gün → ≥ 21 işlem günü kapanışı
POLL_EVERY_S = 60
VIX_HIST_DAYS = 15

# market → profil. Dakikalar YEREL gün dakikası. win = kademe-2 tetikleyici penceresi
# (bar bitişi ≤ win_end). Araştırma: NDX 03:00–15:00 NY, DAX 08:00–16:30 Berlin.
PROFILES: dict[str, dict] = {
    "NDX.INDX": {"tz": "US", "open": 570, "close": 960, "win": (180, 900)},
    "GDAXI.INDX": {"tz": "EU", "open": 540, "close": 1050, "win": (480, 990)},
}
TRADE_WEEKDAYS = (0, 1, 2, 3)   # Pzt–Per (Cuma yok: botun Cuma yasağıyla uyumlu)


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def _last_weekday(year: int, month: int, weekday: int) -> date:
    d = date(year + (month == 12), (month % 12) + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def tz_offset_min(utc: datetime, tz: str) -> int:
    """Yerel − UTC (dakika). US: 2. Pazar Mart 07:00Z → 1. Pazar Kasım 06:00Z. EU: son Pazar Mart/Ekim 01:00Z."""
    y = utc.year
    if tz == "US":
        s = datetime.combine(_nth_weekday(y, 3, 6, 2), datetime.min.time(), timezone.utc).replace(hour=7)
        e = datetime.combine(_nth_weekday(y, 11, 6, 1), datetime.min.time(), timezone.utc).replace(hour=6)
        return -240 if s <= utc < e else -300
    s = datetime.combine(_last_weekday(y, 3, 6), datetime.min.time(), timezone.utc).replace(hour=1)
    e = datetime.combine(_last_weekday(y, 10, 6), datetime.min.time(), timezone.utc).replace(hour=1)
    return 120 if s <= utc < e else 60


def to_local(t_utc: float, tz: str) -> tuple[date, int, int]:
    """UTC epoch → (yerel tarih, yerel gün-dakikası, haftanın günü)."""
    u = datetime.fromtimestamp(t_utc, timezone.utc)
    loc = u + timedelta(minutes=tz_offset_min(u, tz))
    return loc.date(), loc.hour * 60 + loc.minute, loc.weekday()


def local_to_utc(d: date, minute: int, tz: str) -> float:
    """Yerel (tarih, gün-dakikası) → UTC epoch (DST'li; geçiş saatleri hafta sonu)."""
    guess = datetime.combine(d, datetime.min.time(), timezone.utc) + timedelta(minutes=minute)
    off = tz_offset_min(guess, tz)
    u = guess - timedelta(minutes=off)
    off2 = tz_offset_min(u, tz)
    return (guess - timedelta(minutes=off2)).timestamp()


def next_trading_date(d: date) -> date:
    n = d + timedelta(days=1)
    while n.weekday() >= 5:
        n += timedelta(days=1)
    return n


def rth_days(bars: list[dict], prof: dict) -> dict[date, dict]:
    """M15 barlarından (UTC 't' = bar başı) tam RTH günleri: {tarih: {low, high, close, n}}.
    Bir bar RTH'dedir: yerel dakika ∈ [open, close). Bar sayısı < FULL_DAY_FRAC × beklenen → gün atılır."""
    need = int((prof["close"] - prof["open"]) / BAR_MIN * FULL_DAY_FRAC)
    acc: dict[date, dict] = {}
    for b in bars:
        d, m, _ = to_local(b["t"], prof["tz"])
        if not (prof["open"] <= m < prof["close"]):
            continue
        a = acc.setdefault(d, {"low": b["low"], "high": b["high"], "close": b["close"], "n": 0, "_last": -1})
        a["low"], a["high"] = min(a["low"], b["low"]), max(a["high"], b["high"])
        if b["t"] > a["_last"]:
            a["_last"], a["close"] = b["t"], b["close"]
        a["n"] += 1
    return {d: {k: v for k, v in a.items() if k != "_last"} for d, a in sorted(acc.items()) if a["n"] >= need}


def daily_context(days: dict[date, dict], today: date) -> dict | None:
    """Bugünden ÖNCEKİ tam işlem günlerinden r1, r5, dvol, pdl. Veri yetersizse None."""
    ds = [d for d in sorted(days) if d < today]
    if len(ds) < VOL_LOOKBACK + 1:
        return None
    cl = [days[d]["close"] for d in ds]
    rets = [cl[i] / cl[i - 1] - 1 for i in range(1, len(cl))]
    w = rets[-VOL_LOOKBACK:]
    mu = sum(w) / len(w)
    dvol = math.sqrt(sum((x - mu) ** 2 for x in w) / (len(w) - 1))
    r1 = rets[-1]
    r5 = cl[-1] / cl[-6] - 1 if len(cl) >= 6 else None
    stress = bool(r1 <= STRESS_R1 or (r5 is not None and r5 <= STRESS_R5))
    return {"prev_day": str(ds[-1]), "r1": r1, "r5": r5, "dvol": dvol, "stress": stress,
            "pdl": days[ds[-1]]["low"], "pdh": days[ds[-1]]["high"], "pdc": cl[-1]}


def update_vix_hist(hist: dict, day: date, vix: float | None) -> dict:
    """Günün SON görülen VIX değerini sakla (kapanışa yaklaşır); son VIX_HIST_DAYS gün tutulur."""
    if vix is not None:
        hist[str(day)] = float(vix)
    for k in sorted(hist)[:-VIX_HIST_DAYS]:
        hist.pop(k, None)
    return hist


def vix_features(hist: dict, today: date, vix: float | None) -> dict:
    """Bugünden ÖNCEKİ iki günün son VIX'i → önceki gün değişimi (araştırmadaki 'artan VIX' girdisi)."""
    prev = [k for k in sorted(hist) if k < str(today)]
    p1 = hist[prev[-1]] if len(prev) >= 1 else None
    p2 = hist[prev[-2]] if len(prev) >= 2 else None
    chg = None if p1 is None or p2 is None else round(p1 - p2, 3)
    return {"vix_prev": p1, "vix_prev2": p2, "vix_chg_prev": chg,
            "vix_rising": None if chg is None else bool(chg >= 0),
            "vix_chg_live": None if p1 is None or vix is None else round(float(vix) - p1, 3)}


def tier2_trigger(bars: list[dict], prof: dict, today: date, pdl: float) -> dict | None:
    """Bugün pencere içindeki ilk KAPANMIŞ M15 barı: kapanış < önceki RTH dibi. Bar bitişi ≤ pencere sonu."""
    lo, hi = prof["win"]
    for b in bars:
        d, m, _ = to_local(b["t"], prof["tz"])
        if d != today:
            continue
        if m >= lo and m + BAR_MIN <= hi and b["close"] < pdl:
            return b
    return None


def make_event(market: str, tier: str, today: date, ctx: dict, vix: float, ask: float, bid: float,
               t_now: float, trig_t: float | None, prof: dict, vixf: dict | None = None) -> dict:
    stop = ask * (1 - STOP_K * ctx["dvol"])
    d0 = local_to_utc(today, prof["close"], prof["tz"])
    d1 = local_to_utc(next_trading_date(today), prof["close"], prof["tz"])
    return {"id": f"{market}|{today}|{tier}", "market": market, "tier": tier, "date": str(today),
            "entry_t": t_now, "entry_ask": ask, "entry_bid": bid, "stop": stop, "stop_dist": ask - stop,
            "dvol": ctx["dvol"], "r1": ctx["r1"], "r5": ctx["r5"], "vix": vix, "pdl": ctx["pdl"],
            "trigger_bar_t": trig_t, "latency_s": None if trig_t is None else round(t_now - (trig_t + BAR_MIN * 60), 1),
            "tp1_price": ask + (ask - stop), "d0_t": d0, "d1_t": d1, "status": "open", **(vixf or {})}


def resolve_event(ev: dict, m1: list[dict], now: float) -> dict:
    """M1 (BID; 't' = bar başı UTC) üzerinde BUY sonucu. R = (çıkış − giriş − 2·kayma) / stop_dist (1×gvol stop → R≈gvol).

    d0/d1 için: önce stop (bar low ≤ stop; boşluk → açılış), sonra hedef zamandaki bar kapanışı.
    Hedef barı henüz kapanmadıysa o ufuk None kalır (sonra tekrar denenir). Dönen: ev kopyası + R_d0/R_d1 + durum."""
    out = dict(ev)
    entry, stop, sd = ev["entry_ask"] + SLIP_PTS, ev["stop"], ev["stop_dist"]
    bars = [b for b in m1 if b["t"] >= ev["entry_t"] - 60 and b["t"] + 60 <= now]
    stop_t = stop_px = None
    mfe = mae = 0.0
    for b in bars:
        if b["t"] + 60 <= ev["entry_t"]:
            continue
        if stop_t is None and b["low"] <= stop:
            stop_t = b["t"]
            stop_px = min(b["open"], stop) if b["t"] > ev["entry_t"] else stop
        if stop_t is None:
            mfe, mae = max(mfe, (b["high"] - entry) / sd), min(mae, (b["low"] - entry) / sd)
    for key, tgt in (("d0", ev["d0_t"]), ("d1", ev["d1_t"])):
        if out.get(f"R_{key}") is not None:
            continue
        if stop_t is not None and stop_t < tgt:
            out[f"R_{key}"] = round((stop_px - SLIP_PTS - entry) / sd, 4)
            out[f"stopped_{key}"] = True
            continue
        last = [b for b in bars if b["t"] < tgt]
        if now >= tgt + 60 and last and last[-1]["t"] >= tgt - 5 * 60:
            out[f"R_{key}"] = round((last[-1]["close"] - SLIP_PTS - entry) / sd, 4)
            out[f"stopped_{key}"] = False
    out["mfe_R"], out["mae_R"] = round(mfe, 3), round(mae, 3)
    # (b) +1R/−1R ilk geçiş (aynı seans günü, en geç d0 çıkışı); aynı barda ikisi → stop (kötümser)
    tp_px = ev.get("tp1_price", ev["entry_ask"] + sd)
    if out.get("R_tp1") is None:
        for b in bars:
            if b["t"] >= ev["d0_t"]:
                break
            if b["t"] + 60 <= ev["entry_t"]:
                continue
            first = b["t"] > ev["entry_t"]
            if b["low"] <= stop:
                px = min(b["open"], stop) if first else stop
                out["R_tp1"], out["tp1_how"] = round((px - SLIP_PTS - entry) / sd, 4), "stop"
                break
            if b["high"] >= tp_px:
                px = max(b["open"], tp_px) if first else tp_px
                out["R_tp1"], out["tp1_how"] = round((px - SLIP_PTS - entry) / sd, 4), "target"
                break
        if out.get("R_tp1") is None and out.get("R_d0") is not None:
            out["R_tp1"], out["tp1_how"] = out["R_d0"], "time"          # ne hedef ne stop → seans sonu
    if out.get("R_d0") is not None and out.get("R_tp1") is not None:
        out["R_half"] = round(0.5 * out["R_d0"] + 0.5 * out["R_tp1"], 4)
    if out.get("R_d0") is not None and out.get("R_d1") is not None and out.get("R_tp1") is not None:
        out["status"] = "done"
    elif now > ev["d1_t"] + 6 * 86400:
        out["status"] = "expired"
    return out


# ═════════════════════════ durum / kayıt ═════════════════════════

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"fired": {}, "open": []}


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with open(EVENTS_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# K5b için paylaşılan, her taramada tazelenen bağlam: market → {date, stress, pdl, ...}
_K5B: dict[str, dict] = {}
_last_poll = 0.0


def k5b_check(market: str, price: float) -> tuple[bool, dict]:
    """K5b gölge: stres günü VE fiyat < önceki RTH dibi → SELL'i 'bloklardı'. Bağlam bayatsa (>10 dk) False."""
    c = _K5B.get(market)
    if not c or time.time() - c["t"] > 600 or not c["stress"] or c["pdl"] is None:
        return False, {}
    if price < c["pdl"]:
        return True, {"k5b": True, "r1": round(c["r1"], 4), "r5": None if c["r5"] is None else round(c["r5"], 4),
                      "pdl": round(c["pdl"], 2), "dvol": round(c["dvol"], 5)}
    return False, {}


# ═════════════════════════ MT5 sarmalayıcı (emir yok) ═════════════════════════

def _m15_utc(rates, off_s: int) -> list[dict]:
    return [{"t": int(r["time"]) - off_s, "open": float(r["open"]), "high": float(r["high"]),
             "low": float(r["low"]), "close": float(r["close"])} for r in rates]


def poll(mt5, log, resolve_symbol, get_vix, offset_fn, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK. Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if not force and now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    st = _load_state()
    vix = get_vix()                                   # cache'li; her taramada (geçmişi biriktirmek için)
    us_today = to_local(now, "US")[0]
    if vix is not None:
        st["vix_hist"] = update_vix_hist(st.get("vix_hist", {}), us_today, vix)
    vixf = vix_features(st.get("vix_hist", {}), us_today, vix)
    changed = vix is not None
    for market, prof in PROFILES.items():
        sym = resolve_symbol(market)
        if not sym:
            continue
        off = offset_fn(sym)
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 1, FETCH_M15)     # 1 → koşan bar hariç
        if rates is None or len(rates) < 500:
            continue
        bars = _m15_utc(rates, off)
        today, mloc, wd = to_local(now, prof["tz"])
        ctx = daily_context(rth_days(bars, prof), today)
        if ctx is None:
            continue
        _K5B[market] = {"t": now, **ctx} if market == "NDX.INDX" else _K5B.get(market, {})
        if wd not in TRADE_WEEKDAYS or not ctx["stress"]:
            continue
        if vix is None or vix < VIX_MIN:
            continue
        tick = mt5.symbol_info_tick(sym)
        if tick is None:
            continue
        # kademe 1: açılıştan sonraki ilk OPEN_GRACE_MIN dakikada
        k1 = f"{market}|{today}|k1"
        if prof["open"] <= mloc < prof["open"] + OPEN_GRACE_MIN and k1 not in st["fired"]:
            ev = make_event(market, "k1", today, ctx, vix, tick.ask, tick.bid, now, None, prof, vixf)
            st["fired"][k1] = True
            st["open"].append(ev)
            _append({"kind": "event", **ev})
            log.info("CAPREV-GÖLGE %s k1: stres(r1=%.3f r5=%s) VIX=%.1f ask=%.2f stop=%.2f (EMİR YOK)",
                     market, ctx["r1"], ctx["r5"], vix, tick.ask, ev["stop"])
            changed = True
        # kademe 2: ilk dip-altı M15 kapanışı
        k2 = f"{market}|{today}|k2"
        if k2 not in st["fired"]:
            trig = tier2_trigger(bars, prof, today, ctx["pdl"])
            if trig is not None:
                st["fired"][k2] = True
                late = now - (trig["t"] + BAR_MIN * 60)
                if late > MAX_LATE_S:
                    _append({"kind": "skip", "id": k2, "reason": "late", "latency_s": round(late, 1), "ts": now})
                else:
                    ev = make_event(market, "k2", today, ctx, vix, tick.ask, tick.bid, now, trig["t"], prof, vixf)
                    st["open"].append(ev)
                    _append({"kind": "event", **ev})
                    log.info("CAPREV-GÖLGE %s k2: dip altı kapanış %.2f < pdl %.2f, VIX=%.1f ask=%.2f stop=%.2f (EMİR YOK)",
                             market, trig["close"], ctx["pdl"], vix, tick.ask, ev["stop"])
                changed = True
    # açık olayların çözümü
    still = []
    for ev in st["open"]:
        try:
            sym = resolve_symbol(ev["market"])
            n = min(int((now - ev["entry_t"]) / 60) + 30, 6000)
            r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, n) if sym else None
            if r is None or len(r) == 0:
                still.append(ev)
                continue
            m1 = _m15_utc(r, offset_fn(sym))
            new = resolve_event(ev, m1, now)
        except Exception as exc:                       # tek olayın hatası diğerlerini bozmasın
            log.debug("caprev çözüm hatası: %s", exc)
            still.append(ev)
            continue
        if new["status"] in ("done", "expired"):
            _append({"kind": "result", **new})
            log.info("CAPREV-GÖLGE sonuç %s: R_d0=%s R_tp1=%s(%s) R_d1=%s (%s)", new["id"], new.get("R_d0"),
                     new.get("R_tp1"), new.get("tp1_how"), new.get("R_d1"), new["status"])
            changed = True
        else:
            still.append(new)
    if len(st["open"]) != len(still) or changed:
        st["open"] = still
        st["fired"] = {k: v for k, v in st["fired"].items() if k.split("|")[1] >= str(date.fromtimestamp(now) - timedelta(days=10))}
        _save_state(st)
