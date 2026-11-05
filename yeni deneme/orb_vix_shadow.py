"""orb_vix_shadow.py — NDX açılış aralığı kırılımı × VIX (C1) GÖLGE kaydı.

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Yalnız kırılım anını ve sonradan sonucu `orb_vix_shadow.jsonl`'e yazar.
Hatalar bot akışını etkilemez (çağıran try/except içinde kullanır).

KANIT: research/haber_derin_20261105/RAPOR.md, kart backend/data/evolution/go_live_cards/ndx_orb_vix.json (6/6).
10 yılda VIX ≥ 18,4 n=605 +0,185R; VIX < 18,4 n=859 +0,004R. 2026 zayıf (5m +0,098R): gölgenin ölçeceği soru bu.

KURAL (dondurulmuş; değiştirmek kanıtı geçersiz kılar):
  09:30–09:45 ET ilk 15 dk aralığı (3 M5 bar). İlk M5 kapanışı aralık tepesinin üstünde (bar bitişi ≤ 15:30 ET)
  → sonraki bar açılışı BUY. Stop aralık ortası, hedef 2R, 15:55 ET zaman çıkışı. Günde ≤ 1. Kısa yok.
  Risk < giriş × %0,05 → olay yok. Koşul: önceki işlem gününün son VIX'i ≥ 18,4.

İki kol da yazılır (arm=hi|lo|unknown): VIX altı kol, kartın karşı tarafını canlıda ölçer.
İki sonuç yazılır:
  R_model: kartla birebir (sonraki M5 açılışı + o anki spread; M5 barlarında önce stop).
  R_fill : botun gerçekte alabileceği fiyat (tespit anı ask; M1 barlarında önce stop). Tarama gecikmesinin bedeli budur.
Cuma filtresi uygulanmaz (kartta yok); olayda `friday` alanı var, bot NDX Cuma yasağıyla kıyas sonradan yapılır.

Karne:  python orb_vix_shadow.py --karne
Kapatma: config.ORB_VIX_SHADOW_ENABLED = False
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import caprev_shadow as cs   # saat dilimi yardımcıları + VIX geçmişi; ikisi de emir göndermez

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "orb_vix_shadow.jsonl"
STATE_FILE = HERE / "orb_vix_state.json"
CAPREV_STATE = HERE / "caprev_state.json"

MARKET = "NDX.INDX"
TZ = "US"
OPEN_MIN = 570                  # 09:30 ET
OR_MIN = 15
BAR_MIN = 5
OR_BARS = OR_MIN // BAR_MIN
SESSION_END_MIN = 955           # 15:55 ET
LAST_ENTRY_GAP_MIN = 25         # bar bitişi ≤ 15:30 ET
MIN_RISK_FRAC = 0.0005
TARGET_R = 2.0
VIX_MIN = 18.4
POLL_EVERY_S = 60
FETCH_M5 = 150                  # ≈ 12,5 saat: bugünün seansı
MAX_LATE_S = 300                # tespit bu kadar gecikmişse R_fill ölçülmez (yeniden başlatma vb.)
RESOLVE_GIVE_UP_S = 3 * 86400

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def session_bars(bars: list[dict], today: date) -> list[dict]:
    """Bugünün RTH barları (yerel dakika ∈ [09:30, 15:55)), `m` alanıyla, zaman sırasıyla."""
    out = []
    for b in sorted(bars, key=lambda x: x["t"]):
        d, m, _ = cs.to_local(b["t"], TZ)
        if d == today and OPEN_MIN <= m < SESSION_END_MIN:
            out.append({**b, "m": m})
    return out


def find_trigger(sess: list[dict]) -> dict | None:
    """Açılış aralığı + ilk tepe üstü kapanış. Aralık eksikse veya kırılım yoksa None.

    Dönen `entry_t` tetik sonrası ilk barın başı; o bar henüz yoksa None'dır.
    """
    rng = [b for b in sess if b["m"] < OPEN_MIN + OR_MIN]
    if len(rng) < OR_BARS:
        return None
    oh, ol = max(b["high"] for b in rng), min(b["low"] for b in rng)
    post = [b for b in sess if b["m"] >= OPEN_MIN + OR_MIN]
    for i, b in enumerate(post):
        if b["m"] + BAR_MIN > SESSION_END_MIN - LAST_ENTRY_GAP_MIN:
            return None
        if b["close"] > oh:
            nxt = post[i + 1] if i + 1 < len(post) else None
            return {"oh": oh, "ol": ol, "stop": (oh + ol) / 2, "trig_t": b["t"], "trig_close": b["close"],
                    "entry_t": nxt["t"] if nxt else None, "entry_open": nxt["open"] if nxt else None}
    return None


def walk(bars: list[dict], entry: float, stop: float) -> tuple[float | None, str | None, float]:
    """Önce stop, sonra 2R hedef. (R, nasıl, risk). Sonuçlanmadıysa (None, None, risk)."""
    risk = entry - stop
    target = entry + TARGET_R * risk
    for b in bars:
        if b["low"] <= stop:
            return -1.0, "sl", risk
        if b["high"] >= target:
            return TARGET_R, "tp", risk
    return None, None, risk


def session_end_utc(today: date) -> float:
    return cs.local_to_utc(today, SESSION_END_MIN, TZ)


def resolve_event(ev: dict, m5: list[dict], m1: list[dict], now: float) -> dict:
    """R_model (kart) ve R_fill (gerçek ask). Seans bitmeden hedef/stop görülmediyse alan None kalır."""
    out = dict(ev)
    today = date.fromisoformat(ev["day"])
    ended = now >= session_end_utc(today)
    sess5 = session_bars(m5, today)
    if out.get("entry_model") is None:
        trig = find_trigger(sess5)
        if trig and trig["entry_open"] is not None:
            out["entry_t"], out["entry_model"] = trig["entry_t"], round(trig["entry_open"] + ev.get("spread", 0.0), 3)
    if out.get("R_model") is None and out.get("entry_model") is not None:
        e, st = out["entry_model"], ev["stop"]
        if e - st <= MIN_RISK_FRAC * e:
            out["status"], out["reason"] = "invalid", "risk çok dar"
            return out
        rest = [b for b in sess5 if b["t"] >= out["entry_t"]]
        r, how, risk = walk(rest, e, st)
        if r is None and ended and rest:
            r, how = (rest[-1]["close"] - e) / risk, "time"
        if r is not None:
            out["R_model"], out["how_model"], out["risk_pts"] = round(r, 3), how, round(risk, 2)
    if out.get("R_fill") is None and ev.get("fill") is not None:
        e, st = ev["fill"], ev["stop"]
        if e <= st:
            out["R_fill"], out["how_fill"] = None, "stop_altinda"
        elif out.get("how_fill") is None:
            rest = [b for b in session_bars(m1, today) if b["t"] >= ev["detect_t"] - ev["detect_t"] % 60]
            r, how, risk = walk(rest, e, st)
            if r is None and ended and rest:
                r, how = (rest[-1]["close"] - e) / risk, "time"
            if r is not None:
                out["R_fill"], out["how_fill"] = round(r, 3), how
    fill_done = ev.get("fill") is None or out.get("how_fill") is not None
    if out.get("R_model") is not None and fill_done:
        out["status"] = "done"
    elif ended and out.get("entry_model") is None:
        out["status"], out["reason"] = "invalid", "tetik sonrası bar yok"
    elif now - ev["detect_t"] > RESOLVE_GIVE_UP_S:
        out["status"] = "expired"
    else:
        out["status"] = "open"
    return out


def arm_of(vix_prev: float | None) -> str:
    if vix_prev is None:
        return "unknown"
    return "hi" if vix_prev >= VIX_MIN else "lo"


def summarize(records: list[dict]) -> dict:
    """jsonl satırlarından kol bazında karne."""
    res = [r for r in records if r.get("kind") == "result" and r.get("status") == "done"]
    out = {"olay": sum(1 for r in records if r.get("kind") == "event"), "cozulen": len(res), "kollar": {}}
    for arm in ("hi", "lo", "unknown"):
        sub = [r for r in res if r.get("arm") == arm]
        if not sub:
            continue
        rm = [r["R_model"] for r in sub if r.get("R_model") is not None]
        rf = [r["R_fill"] for r in sub if r.get("R_fill") is not None]
        out["kollar"][arm] = {
            "n": len(sub), "R_model": round(sum(rm) / len(rm), 3) if rm else None,
            "isabet_model": round(sum(x > 0 for x in rm) / len(rm), 3) if rm else None,
            "toplam_R_model": round(sum(rm), 2), "n_fill": len(rf), "R_fill": round(sum(rf) / len(rf), 3) if rf else None,
            "spread_ort": round(sum(r.get("spread", 0.0) for r in sub) / len(sub), 2),
            "gecikme_s_ort": round(sum(r.get("latency_s", 0.0) for r in sub) / len(sub), 1),
        }
    return out


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st.setdefault("fired", {})
    st.setdefault("open", [])
    if not st.get("vix_hist"):      # ilk açılış: CAPREV gölgesinin VIX geçmişini salt okunur devral
        try:
            st["vix_hist"] = dict(json.loads(CAPREV_STATE.read_text(encoding="utf-8")).get("vix_hist", {}))
        except (OSError, ValueError):
            st["vix_hist"] = {}
    return st


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ═════════════════════════ MT5 sarmalayıcı (emir yok) ═════════════════════════

def _resolve_open(mt5, log, resolve_symbol, offset_fn, st: dict, now: float) -> bool:
    changed, still = False, []
    for ev in st["open"]:
        try:
            sym = resolve_symbol(MARKET)
            off = offset_fn(sym)
            r5 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M5, 1, FETCH_M5)
            n1 = min(int((now - ev["detect_t"]) / 60) + 30, 6000)
            r1 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 1, n1)
            if r5 is None or r1 is None:
                still.append(ev)
                continue
            new = resolve_event(ev, cs._m15_utc(r5, off), cs._m15_utc(r1, off), now)
        except Exception as exc:     # tek olayın hatası diğerini bozmasın
            log.debug("orb_vix çözüm hatası: %s", exc)
            still.append(ev)
            continue
        if new["status"] == "open":
            changed = changed or new != ev
            still.append(new)
        else:
            _append({"kind": "result", **new})
            log.info("ORB×VIX-GÖLGE sonuç %s kol=%s: R_model=%s (%s) R_fill=%s (%s) %s", new["id"], new["arm"],
                     new.get("R_model"), new.get("how_model"), new.get("R_fill"), new.get("how_fill"), new["status"])
            changed = True
    st["open"] = still
    return changed


def poll(mt5, log, resolve_symbol, get_vix, offset_fn, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK. Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if not force and now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    st = _load_state()
    today, mloc, _ = cs.to_local(now, TZ)
    vix = get_vix()
    changed = False
    if vix is not None:
        st["vix_hist"] = cs.update_vix_hist(st.get("vix_hist", {}), today, vix)
        changed = True
    key = f"{MARKET}|{today}"
    in_window = OPEN_MIN + OR_MIN <= mloc < SESSION_END_MIN and today.weekday() < 5
    if in_window and key not in st["fired"]:
        sym = resolve_symbol(MARKET)
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M5, 1, FETCH_M5) if sym else None   # 1 → koşan bar hariç
        if rates is not None and len(rates) > 0:
            trig = find_trigger(session_bars(cs._m15_utc(rates, offset_fn(sym)), today))
            tick = mt5.symbol_info_tick(sym) if trig else None
            if trig and tick is not None:
                st["fired"][key] = True
                late = now - (trig["trig_t"] + BAR_MIN * 60)
                vf = cs.vix_features(st.get("vix_hist", {}), today, vix)
                ev = {"id": key, "day": str(today), "market": MARKET, "symbol": sym, "arm": arm_of(vf["vix_prev"]),
                      "vix_prev": vf["vix_prev"], "vix_live": vix, "friday": today.weekday() == 4,
                      "oh": trig["oh"], "ol": trig["ol"], "stop": trig["stop"], "trig_t": trig["trig_t"],
                      "trig_close": trig["trig_close"], "entry_t": trig["entry_t"],
                      "entry_model": None, "detect_t": now, "latency_s": round(late, 1),
                      "ask": tick.ask, "bid": tick.bid, "spread": round(tick.ask - tick.bid, 3),
                      "fill": tick.ask if late <= MAX_LATE_S else None, "status": "open"}
                st["open"].append(ev)
                _append({"kind": "event", **ev})
                log.info("ORB×VIX-GÖLGE %s kol=%s: tepe %.2f üstü kapanış %.2f, VIX(dün)=%s ask=%.2f stop=%.2f "
                         "(EMİR YOK)", today, ev["arm"], trig["oh"], trig["trig_close"], vf["vix_prev"], tick.ask, trig["stop"])
                changed = True
    if st["open"]:
        changed = _resolve_open(mt5, log, resolve_symbol, offset_fn, st, now) or changed
    if changed:
        cut = str(today - timedelta(days=5))
        st["fired"] = {k: v for k, v in st["fired"].items() if k.split("|")[1] >= cut}
        _save_state(st)


def _karne() -> None:
    try:
        lines = EVENTS_JSONL.read_text(encoding="utf-8").splitlines()
    except OSError:
        print("henüz kayıt yok")
        return
    print(json.dumps(summarize([json.loads(x) for x in lines if x.strip()]), ensure_ascii=False, indent=1))
    print("Kart beklentisi: hi +0,10…+0,18R (10 yıl +0,185R), lo ≈ 0. n < 30 iken hüküm verme.")


if __name__ == "__main__":
    if "--karne" in sys.argv:
        _karne()
