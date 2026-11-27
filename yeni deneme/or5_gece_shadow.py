"""or5_gece_shadow.py — Y1a (OR5 iki yön + gece hizası) GÖLGE kaydı + Y5 (ORB×VIX + gece hizası) için günlük gece yönü.

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Yalnız olayları ve sonuçları `or5_gece_shadow.jsonl`'e yazar.
Hatalar bot akışını etkilemez (çağıran try/except içinde kullanır).

KANIT: kartlar backend/data/evolution/go_live_cards/ndx_or5_gece_hiza.json (Y1a, B) ve ndx_orb_vix_gece_hiza.json (Y5, B);
defter §2.128–2.130. Duka 2018–26: Y1a hizalı +0,205R (n 854) / hizasız +0,012; Y5 gece yukarı +0,302R / aşağı −0,004.
Portföy önerisi (§2.130 IY-P): Y5 + 0,5 lot Y1a — canlı ORB×VIX'in maks. DD'sinde yıllık R 14,6 → 24,3. Kullanıcı kararı
2026-11-26: "gölgede başlat".

KURAL (dondurulmuş; araştırma kodu research/trader_tersine/gelistirme/turev_y1_y2_20261126/src/sinav.py ile birebir):
  Gece yönü g = sign(09:29 ET son kapanış − d−1 18:00 ET sonrası ilk açılış).
  OR5 = 09:30–09:34 M1 yüksek/düşük; m = sign(09:34 kapanış − 09:30 açılış), m = 0 → olay yok.
  09:35–10:30 arası ilk M1 kapanışı m yönünde OR5'i kırarsa → sonraki M1 açılışında m yönünde (AL/SAT).
  Stop = OR5'in karşı ucu; hedef yok; 15:59 ET kapanışında çıkış. Günde ≤ 1.
  Kol: "hizali" (g = m → Y1a işlemi) / "hizasiz" (g ≠ m → R0'ın Y1a'nın dışında kalan kısmı) — ikisi de ölçülür.
İki sonuç: R_model (sonraki M1 açılışı + tespit anı spread'i, M1'de önce stop) ve R_fill (tespit anı ask/bid).
Y5: her işlem günü 09:31 ET'de {"kind": "gece", "day", "g", "gece_bp"} yazılır; karne ORB×VIX gölge/canlı kayıtlarını buna bağlar.

DAX KOLU (2026-11-27, kullanıcı: "Yes, add DAX leg"): aynı kural DAX'a uyarlanmış hâliyle (defter §2.140 AV-01, kart
go_live_cards/dax_y1a.json LIVE 6/6: Duka 2018–26 hizalı +0,191R n 881 P 0,996 / hizasız +0,029; araştırma kodu
research/trader_tersine/gelistirme/avrupa_or5_20261127/src/avrupa.py ile birebir): yerel saat Berlin (EU DST);
OR5 09:00–09:04, giriş penceresi 09:05–10:00, çıkış 17:29 barının kapanışı, gece = d−1 17:35 sonrası ilk açılış → 08:59 son kapanış.
Kayıtlarda "market" alanı; NDX kayıtları eski biçimde (market alanı yoksa NDX sayılır).

Karne:   python or5_gece_shadow.py --karne
Kapatma: config.OR5_GECE_SHADOW_ENABLED = False (tümü) · config.OR5_GECE_DAX_ENABLED = False (yalnız DAX kolu)
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import caprev_shadow as cs   # saat dilimi yardımcıları; emir göndermez

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "or5_gece_shadow.jsonl"
STATE_FILE = HERE / "or5_gece_state.json"
ORB_SHADOW_JSONL = HERE / "orb_vix_shadow.jsonl"
CANLI_OLAYLAR = HERE / "kural_canli_olaylar.jsonl"

MARKET = "NDX.INDX"
TZ = "US"
OPEN_MIN = 570                  # 09:30 ET
OR_MIN = 5
ENTRY_LAST_MIN = 630            # 10:30 ET (son tetik kapanışı)
EXIT_MIN = 959                  # 15:59 ET barının kapanışı
GLOBEX_MIN = 1080               # 18:00 ET
# kol profilleri: NDX (asıl, eski kayıt biçimi) + DAX (2026-11-27)
NDX = {"market": MARKET, "tz": TZ, "open": OPEN_MIN, "entry_last": ENTRY_LAST_MIN, "exit": EXIT_MIN, "gece": GLOBEX_MIN, "etiket": "NDX"}
DAX = {"market": "GDAXI.INDX", "tz": "EU", "open": 540, "entry_last": 600, "exit": 1049, "gece": 1055, "etiket": "DAX"}
PROFILLER = {NDX["market"]: NDX, DAX["market"]: DAX}
POLL_EVERY_S = 60
FETCH_M1 = 1500                 # ≈ 25 saat: dünkü 18:00'den bugüne
MAX_LATE_S = 180
RESOLVE_GIVE_UP_S = 3 * 86400
Y1A_LOT_ORAN = 0.5              # portföy önerisi (yalnız karnede kullanılır)

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def local_bars(bars: list[dict], prof: dict = NDX) -> list[dict]:
    """UTC barlarına yerel (tarih, dakika) ekle, zaman sırasıyla."""
    out = []
    for b in sorted(bars, key=lambda x: x["t"]):
        d, m, _ = cs.to_local(b["t"], prof["tz"])
        out.append({**b, "d": d, "m": m})
    return out


def prev_session_date(today: date) -> date:
    p = today - timedelta(days=1)
    while p.weekday() >= 5:
        p -= timedelta(days=1)
    return p


def gece_yonu(lb: list[dict], today: date, prof: dict = NDX) -> tuple[int, float | None]:
    """g = sign(09:29 son kapanış − d−1 18:00 sonrası ilk açılış). (g, gece_bp); veri yoksa (0, None).

    Pazartesi: d−1 = Cuma; Cuma 18:00 sonrası bar yoksa (hafta sonu) Pazar 18:00 açılışı kullanılır."""
    onceki = prev_session_date(today)
    op, gm = prof["open"], prof["gece"]
    ac = [b for b in lb if (b["d"] == onceki and b["m"] >= gm) or (onceki < b["d"] < today) or (b["d"] == today and b["m"] < op)]
    pre = [b for b in lb if b["d"] == today and b["m"] < op]
    if not ac or not pre:
        return 0, None
    a, p = ac[0]["open"], pre[-1]["close"]
    bp = (p / a - 1) * 1e4 if a else None
    return (1 if p > a else -1 if p < a else 0), (round(bp, 2) if bp is not None else None)


def find_or5_trigger(lb: list[dict], today: date, prof: dict = NDX) -> dict | None:
    """OR5 + m + ilk m yönlü kırılım kapanışı (NDX 09:35–10:30 / DAX 09:05–10:00). entry_* sonraki bar; yoksa None alanlı."""
    op, el = prof["open"], prof["entry_last"]
    sess = [b for b in lb if b["d"] == today and op <= b["m"] <= prof["exit"]]
    rng = [b for b in sess if b["m"] < op + OR_MIN]
    if len(rng) < 4:
        return None
    tepe, dip = max(b["high"] for b in rng), min(b["low"] for b in rng)
    m = (rng[-1]["close"] > rng[0]["open"]) - (rng[-1]["close"] < rng[0]["open"])
    if m == 0:
        return None
    post = [b for b in sess if b["m"] >= op + OR_MIN]
    for i, b in enumerate(post):
        if b["m"] > el:
            return None
        if (b["close"] > tepe) if m > 0 else (b["close"] < dip):
            nxt = post[i + 1] if i + 1 < len(post) else None
            return {"m": m, "tepe": tepe, "dip": dip, "stop": dip if m > 0 else tepe, "trig_t": b["t"], "trig_close": b["close"],
                    "entry_t": nxt["t"] if nxt else None, "entry_open": nxt["open"] if nxt else None}
    return None


def walk(bars: list[dict], entry: float, stop: float, m: int, exit_t: float) -> tuple[float | None, str | None]:
    """Önce stop; hedef yok; exit_t barının kapanışında zaman çıkışı. (R, nasıl) — sonuçlanmadıysa (None, None)."""
    risk = (entry - stop) * m
    if risk <= 0:
        return None, "gecersiz"
    son = None
    for b in bars:
        if b["t"] > exit_t:
            break
        if (b["low"] <= stop) if m > 0 else (b["high"] >= stop):
            return -1.0, "sl"
        son = b
    if son is not None and son["t"] >= exit_t:
        return round((son["close"] - entry) * m / risk, 4), "time"
    return None, None


def summarize(records: list[dict]) -> dict:
    """Y1a kolları + Y5 (ORB×VIX kayıtları gece yönüyle) + paket."""
    def _ndx(r): return r.get("market", MARKET) == MARKET
    hepsi = [r for r in records if r.get("kind") == "result" and r.get("status") == "done"]
    res = [r for r in hepsi if _ndx(r)]
    gece = {r["day"]: r.get("g", 0) for r in records if r.get("kind") == "gece" and _ndx(r)}
    out = {"olay": sum(1 for r in records if r.get("kind") == "event"), "cozulen": len(res), "kollar": {}, "Y5": {}}
    for arm in ("hizali", "hizasiz"):
        sub = [r for r in res if r.get("arm") == arm]
        rm = [r["R_model"] for r in sub if r.get("R_model") is not None]
        rf = [r["R_fill"] for r in sub if r.get("R_fill") is not None]
        if sub:
            out["kollar"][arm] = {"n": len(sub), "R_model": round(sum(rm) / len(rm), 3) if rm else None,
                                  "toplam_R_model": round(sum(rm), 2), "R_fill": round(sum(rf) / len(rf), 3) if rf else None,
                                  "isabet": round(sum(x > 0 for x in rm) / len(rm), 3) if rm else None}
    orb = _orb_kayitlari()
    for ad, sec in (("gece_yukari", 1), ("gece_asagi", -1)):
        sub = [r for r in orb if gece.get(r["day"]) == sec]
        rr = [r["R"] for r in sub]
        if sub:
            out["Y5"][ad] = {"n": len(sub), "R": round(sum(rr) / len(rr), 3), "toplam_R": round(sum(rr), 2)}
    dax = [r for r in hepsi if r.get("market") == DAX["market"]]
    out["DAX"] = {}
    for arm in ("hizali", "hizasiz"):
        rm = [r["R_model"] for r in dax if r.get("arm") == arm and r.get("R_model") is not None]
        if rm:
            out["DAX"][arm] = {"n": len(rm), "R_model": round(sum(rm) / len(rm), 3), "toplam_R_model": round(sum(rm), 2),
                               "isabet": round(sum(x > 0 for x in rm) / len(rm), 3)}
    y1 = out["kollar"].get("hizali", {}).get("toplam_R_model") or 0.0
    y5 = out["Y5"].get("gece_yukari", {}).get("toplam_R") or 0.0
    orb_tum = sum(r["R"] for r in orb if r["day"] in gece)
    out["paket"] = {"Y5_+_0.5_Y1a_toplam_R": round(y5 + Y1A_LOT_ORAN * y1, 2), "ORBxVIX_tum_toplam_R": round(orb_tum, 2)}
    return out


def _orb_kayitlari() -> list[dict]:
    """ORB×VIX gölge (hi kol, R_model) ve canlı (kural ORBVIX, R) sonuçları → [{day, R, kaynak}]."""
    out = []
    try:
        for x in ORB_SHADOW_JSONL.read_text(encoding="utf-8").splitlines():
            r = json.loads(x) if x.strip() else {}
            if r.get("kind") == "result" and r.get("status") == "done" and r.get("arm") == "hi" and r.get("R_model") is not None:
                out.append({"day": r["day"], "R": r["R_model"], "kaynak": "golge"})
    except (OSError, ValueError):
        pass
    return out


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st.setdefault("fired", {})
    st.setdefault("gece", {})
    st.setdefault("open", [])
    return st


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ═════════════════════════ MT5 sarmalayıcı (emir yok) ═════════════════════════

def _m1(mt5, sym: str, offset_fn, n: int, prof: dict = NDX) -> list[dict] | None:
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 1, n)       # 1 → koşan bar hariç
    if r is None or len(r) == 0:
        return None
    return local_bars(cs._m15_utc(r, offset_fn(sym)), prof)


def _resolve_open(mt5, log, resolve_symbol, offset_fn, st: dict, now: float) -> bool:
    changed, still = False, []
    for ev in st["open"]:
        try:
            today = date.fromisoformat(ev["day"])
            prof = PROFILLER.get(ev.get("market", MARKET), NDX)
            exit_t = cs.local_to_utc(today, prof["exit"], prof["tz"])
            sym = resolve_symbol(prof["market"])
            n1 = min(int((now - ev["detect_t"]) / 60) + 30, 6000)
            lb = _m1(mt5, sym, offset_fn, n1, prof) if sym else None
            if lb is None:
                still.append(ev); continue
            out = dict(ev)
            if out.get("entry_model") is None:
                trig = find_or5_trigger(lb, today, prof)
                if trig and trig["entry_open"] is not None:
                    sp = ev.get("spread", 0.0)
                    out["entry_t"] = trig["entry_t"]
                    out["entry_model"] = round(trig["entry_open"] + (sp if ev["m"] > 0 else -sp), 3)
            if out.get("R_model") is None and out.get("entry_model") is not None:
                rest = [b for b in lb if b["t"] >= out["entry_t"]]
                r, how = walk(rest, out["entry_model"], ev["stop"], ev["m"], exit_t)
                if r is not None:
                    out["R_model"], out["how_model"] = r, how
                elif how == "gecersiz":
                    out["status"], out["reason"] = "invalid", "giriş stopun öte yanında"
            if out.get("R_fill") is None and ev.get("fill") is not None and out.get("how_fill") is None:
                rest = [b for b in lb if b["t"] >= ev["detect_t"] - ev["detect_t"] % 60]
                r, how = walk(rest, ev["fill"], ev["stop"], ev["m"], exit_t)
                if r is not None or how == "gecersiz":
                    out["R_fill"], out["how_fill"] = r, how
            ended = now >= exit_t + 120
            fill_done = ev.get("fill") is None or out.get("how_fill") is not None
            if out.get("status") == "invalid":
                pass
            elif out.get("R_model") is not None and fill_done:
                out["status"] = "done"
            elif ended and out.get("entry_model") is None:
                out["status"], out["reason"] = "invalid", "tetik sonrası bar yok"
            elif now - ev["detect_t"] > RESOLVE_GIVE_UP_S:
                out["status"] = "expired"
            else:
                out["status"] = "open"
        except Exception as exc:     # tek olayın hatası diğerini bozmasın
            log.debug("or5_gece çözüm hatası: %s", exc)
            still.append(ev); continue
        if out["status"] == "open":
            changed = changed or out != ev
            still.append(out)
        else:
            _append({"kind": "result", **out})
            log.info("OR5-GECE-GÖLGE sonuç %s kol=%s yön=%s: R_model=%s (%s) R_fill=%s %s", out["id"], out["arm"], out["m"],
                     out.get("R_model"), out.get("how_model"), out.get("R_fill"), out["status"])
            changed = True
    st["open"] = still
    return changed


def poll(mt5, log, resolve_symbol, offset_fn, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK. Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if not force and now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    st = _load_state()
    changed = False
    profs = [NDX] + ([DAX] if _dax_acik() else [])
    for prof in profs:
        try:
            changed = _tara(mt5, log, resolve_symbol, offset_fn, st, now, prof) or changed
        except Exception as exc:          # bir kolun hatası diğerini durdurmasın
            log.debug("or5_gece %s tarama hatası: %s", prof["etiket"], exc)
    today = cs.to_local(now, TZ)[0]
    if st["open"]:
        changed = _resolve_open(mt5, log, resolve_symbol, offset_fn, st, now) or changed
    if changed:
        cut = str(today - timedelta(days=10))
        st["fired"] = {k: v for k, v in st["fired"].items() if k.split("|")[1] >= cut}
        st["gece"] = {k: v for k, v in st["gece"].items() if k.split("|")[-1] >= cut}
        _save_state(st)


def _dax_acik() -> bool:
    try:
        import config
        return bool(getattr(config, "OR5_GECE_DAX_ENABLED", True))
    except Exception:
        return True


def _tara(mt5, log, resolve_symbol, offset_fn, st: dict, now: float, prof: dict) -> bool:
    """Bir kol (NDX/DAX) için gece yönü + OR5 tetik taraması. EMİR YOK. NDX durumu eski anahtarlarla (gün) tutulur."""
    today, mloc, _ = cs.to_local(now, prof["tz"])
    op, el, ex, mk = prof["open"], prof["entry_last"], prof["exit"], prof["market"]
    if today.weekday() >= 5 or not (op + 1 <= mloc < ex):
        return False
    sym = resolve_symbol(mk)
    lb = _m1(mt5, sym, offset_fn, FETCH_M1, prof) if sym else None
    if not lb:
        return False
    changed = False
    dkey = str(today)
    gkey = dkey if prof is NDX else f"{mk}|{dkey}"
    if gkey not in st["gece"]:
        g, bp = gece_yonu(lb, today, prof)
        if bp is not None:
            st["gece"][gkey] = g
            rec = {"kind": "gece", "day": dkey, "g": g, "gece_bp": bp}
            if prof is not NDX:
                rec["market"] = mk
            _append(rec)
            if prof is NDX:
                log.info("OR5-GECE-GÖLGE %s gece yönü g=%+d (%.1f bp) — Y5: ORB×VIX %s", dkey, g, bp,
                         "açılırdı" if g > 0 else "AÇILMAZDI (gölge etiketi; canlıya dokunulmaz)")
            else:
                log.info("OR5-GECE-GÖLGE %s %s gece yönü g=%+d (%.1f bp)", prof["etiket"], dkey, g, bp)
            changed = True
    key = f"{mk}|{today}"
    if key not in st["fired"] and mloc >= op + OR_MIN + 1 and gkey in st["gece"]:
        trig = find_or5_trigger(lb, today, prof)
        if trig is None and mloc > el + 1:
            st["fired"][key] = "yok"; changed = True
        elif trig is not None:
            tick = mt5.symbol_info_tick(sym)
            if tick is not None:
                st["fired"][key] = True
                g = st["gece"][gkey]
                late = now - (trig["trig_t"] + 60)
                fill = (tick.ask if trig["m"] > 0 else tick.bid) if late <= MAX_LATE_S else None
                ev = {"id": key, "day": dkey, "market": mk, "symbol": sym, "m": trig["m"], "g": g,
                      "arm": "hizali" if g == trig["m"] else "hizasiz", "tepe": trig["tepe"], "dip": trig["dip"],
                      "stop": trig["stop"], "trig_t": trig["trig_t"], "trig_close": trig["trig_close"],
                      "entry_t": trig["entry_t"], "entry_model": None, "detect_t": now, "latency_s": round(late, 1),
                      "ask": tick.ask, "bid": tick.bid, "spread": round(tick.ask - tick.bid, 3), "fill": fill, "status": "open"}
                st["open"].append(ev)
                _append({"kind": "event", **ev})
                log.info("OR5-GECE-GÖLGE %s %s kol=%s %s: OR5 %.2f–%.2f kırılım %.2f, stop %.2f (EMİR YOK)", prof["etiket"], dkey, ev["arm"],
                         "AL" if trig["m"] > 0 else "SAT", trig["dip"], trig["tepe"], trig["trig_close"], trig["stop"])
                changed = True
    return changed


def _karne() -> None:
    try:
        lines = EVENTS_JSONL.read_text(encoding="utf-8").splitlines()
    except OSError:
        print("henüz kayıt yok"); return
    print(json.dumps(summarize([json.loads(x) for x in lines if x.strip()]), ensure_ascii=False, indent=1))
    print("Kart beklentisi: hizali +0,10…+0,20R, hizasiz ≈ 0; Y5 gece yukarı +0,25…+0,30R, aşağı ≈ 0. "
          "DAX: hizali ≈ +0,19R, hizasiz ≈ +0,03R. n < 30 iken hüküm verme.")


if __name__ == "__main__":
    if "--karne" in sys.argv:
        _karne()
