"""c3b_shadow.py — NDX RSI2 geri dönüşü (C3b + C3) GÖLGE kaydı.

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Yalnız sinyali ve sonucu `c3b_shadow.jsonl`'e yazar.
Hatalar bot akışını etkilemez (çağıran try/except içinde kullanır).

KANIT: research/c1_turev_20261105/RAPOR.md, kartlar backend/data/evolution/go_live_cards/ndx_c3b_rsi2_upexit.json
ve ndx_c3_rsi2.json (ikisi 6/6). MT5 2016-26 C3b n=155 +65 bp %78. Kör: US500 +53,8 bp, US30 +34,4 bp.

KURAL (dondurulmuş; değiştirmek kanıtı geçersiz kılar):
  Her işlem günü S = 15:30 ET barından önceki M30 barın kapanışı, E = 15:30 barının açılışı.
  RSI2 (Wilder, S serisinden) < 10 → E'de uzun. Çıkış: ilk S_t > S_{t−1} günü E_t'de; en geç 5 işlem günü.
  Tek pozisyon; çıkış günü yeni sinyal varsa aynı açılışta yeniden girilir. Stop yok. Finansman 2 bp/gece.
İki kol:
  C3b: yukarıdaki. C3: her sinyal, tam 1 işlem günü sonra E'de çıkış (çakışma serbest).
İki sonuç:
  bp_model: kartla birebir (spread 1,3 pt). bp_fill: tespit anındaki gerçek ask/bid (tarama gecikmesi dahil).
`caprev_gunu`: sinyal gününde stres (r1 ≤ −%1,5 veya r5 ≤ −%4) ∧ VIX(dün) ≥ 18,4 → CAPREV ile çakışma ölçülür.

Karne:   python c3b_shadow.py --karne
Kapatma: config.C3B_SHADOW_ENABLED = False
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import caprev_shadow as cs   # saat dilimi yardımcıları + VIX geçmişi; ikisi de emir göndermez

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "c3b_shadow.jsonl"
STATE_FILE = HERE / "c3b_state.json"
CAPREV_STATE = HERE / "caprev_state.json"

MARKET = "NDX.INDX"
TZ = "US"
ENTRY_MIN = 930                 # 15:30 ET
BAR_MIN = 30
MAX_PREV_GAP_S = 3 * BAR_MIN * 60
RSI_TH = 10.0
RSI_ALPHA = 0.5                 # Wilder(2)
MAX_HOLD = 5
SPREAD_MODEL = 1.3
FIN_BP = 2.0
CAPREV_VIX = 18.4
CAPREV_R1 = -150.0
CAPREV_R5 = -400.0
FETCH_M30 = 6000                # ≈ 125 işlem günü; RSI2 ısınması ≪ bu
POLL_EVERY_S = 60
MAX_LATE_S = 300

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def daily_series(bars: list[dict]) -> list[dict]:
    """M30 barlarından gün serisi: [{d, S, E}]. S = 15:30 barından önceki bar kapanışı. Hafta sonu ve boşluk atılır."""
    out: dict[date, dict] = {}
    rows = sorted(bars, key=lambda x: x["t"])
    for i, b in enumerate(rows):
        d, m, wd = cs.to_local(b["t"], TZ)
        if m != ENTRY_MIN or wd >= 5 or i == 0 or d in out:
            continue
        prev = rows[i - 1]
        if b["t"] - prev["t"] > MAX_PREV_GAP_S:
            continue
        out[d] = {"d": d, "S": prev["close"], "E": b["open"], "t": b["t"]}
    return [out[k] for k in sorted(out)]


def rsi2(values: list[float]) -> list[float]:
    """Wilder RSI(2), pandas ewm(alpha=.5, adjust=False) ile aynı özyineleme; ilk değer NaN."""
    out, up, dn = [], 0.0, 0.0
    for i, v in enumerate(values):
        if i == 0:                        # ilk değerde değişim yok: RSI tanımsız, sinyal üretmez
            out.append(float("nan"))
            continue
        g = v - values[i - 1]
        if i == 1:
            up, dn = max(g, 0.0), max(-g, 0.0)
        else:
            up = RSI_ALPHA * max(g, 0.0) + (1 - RSI_ALPHA) * up
            dn = RSI_ALPHA * max(-g, 0.0) + (1 - RSI_ALPHA) * dn
        out.append(100.0 - 100.0 / (1.0 + up / (dn + 1e-12)))
    return out


def model_bp(entry_e: float, exit_e: float, days: int, spread: float = SPREAD_MODEL) -> float:
    return (exit_e / (entry_e + spread) - 1.0) * 1e4 - FIN_BP * days


def step(pos: dict | None, i: int, series: list[dict], rsi: list[float]) -> tuple[dict | None, dict | None, bool]:
    """Bir gün ilerlet. (yeni pozisyon, kapanan işlem, giriş oldu mu)."""
    closed = None
    day = series[i]
    if pos is not None:
        held = i - pos["i"]
        if day["S"] > series[i - 1]["S"] or held >= MAX_HOLD:
            closed = {"entry_d": str(series[pos["i"]]["d"]), "exit_d": str(day["d"]), "days": held,
                      "bp_model": round(model_bp(series[pos["i"]]["E"], day["E"], held), 2),
                      "how": "yukselis" if day["S"] > series[i - 1]["S"] else "sure"}
            pos = None
    entered = False
    if pos is None and rsi[i] < RSI_TH and i + 1 <= len(series):
        pos, entered = {"i": i, "d": str(day["d"])}, True
    return pos, closed, entered


def replay(series: list[dict]) -> list[dict]:
    """Tüm seride C3b işlemleri (kart paritesi için). Son açık pozisyon sayılmaz."""
    rsi = rsi2([s["S"] for s in series])
    pos, out = None, []
    for i in range(len(series)):
        pos, closed, _ = step(pos, i, series, rsi)
        if closed:
            out.append(closed)
    return out


def caprev_flag(series: list[dict], i: int, vix_prev: float | None) -> bool | None:
    """CAPREV stres şartı karar anı fiyatıyla (yaklaşık); VIX yoksa None."""
    if vix_prev is None or i < 5:
        return None
    r1 = (series[i]["S"] / series[i - 1]["S"] - 1) * 1e4
    r5 = (series[i]["S"] / series[i - 5]["S"] - 1) * 1e4
    return bool((r1 <= CAPREV_R1 or r5 <= CAPREV_R5) and vix_prev >= CAPREV_VIX)


def summarize(records: list[dict]) -> dict:
    res = {}
    for arm in ("C3b", "C3"):
        sub = [r for r in records if r.get("kind") == "result" and r.get("arm") == arm]
        if not sub:
            continue
        bm = [r["bp_model"] for r in sub if r.get("bp_model") is not None]
        bf = [r["bp_fill"] for r in sub if r.get("bp_fill") is not None]
        res[arm] = {"n": len(sub), "bp_model": round(sum(bm) / len(bm), 1) if bm else None,
                    "isabet_model": round(sum(x > 0 for x in bm) / len(bm), 3) if bm else None,
                    "toplam_bp_model": round(sum(bm), 1), "n_fill": len(bf),
                    "bp_fill": round(sum(bf) / len(bf), 1) if bf else None}
    res["sinyal"] = sum(1 for r in records if r.get("kind") == "signal")
    return res


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st.setdefault("last_d", None)
    st.setdefault("pos", None)
    st.setdefault("c3_open", [])
    if not st.get("vix_hist"):     # ilk açılış: CAPREV gölgesinin VIX geçmişini salt okunur devral
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


# ═════════════════════════ gün işleme ═════════════════════════

def _result(arm: str, pos: dict, day: dict, days: int, how: str, bid: float | None) -> dict:
    fill = pos.get("fill")
    bp_fill = None if fill is None or bid is None else round((bid / fill - 1.0) * 1e4 - FIN_BP * days, 2)
    return {"kind": "result", "arm": arm, "entry_d": pos["d"], "exit_d": str(day["d"]), "days": days, "how": how,
            "E_entry": pos["E"], "E_exit": day["E"], "bp_model": round(model_bp(pos["E"], day["E"], days), 2), "bp_fill": bp_fill,
            "caprev_gunu": pos.get("caprev_gunu"), "vix_prev": pos.get("vix_prev"), "rsi2": pos.get("rsi2")}


def process_day(st: dict, series: list[dict], i: int, tick, now: float, vix_prev: float | None, log) -> None:
    """Tek gün: önce çıkışlar, sonra giriş. `tick` yalnız bugün ve zamanında ise verilir; yoksa bp_fill ölçülmez."""
    day, rsi = series[i], rsi2([s["S"] for s in series])
    ask, bid = (tick.ask, tick.bid) if tick is not None else (None, None)
    idx = {str(s["d"]): k for k, s in enumerate(series)}
    still = []
    for p in st["c3_open"]:           # C3: 1 işlem günü sonra
        if p["d"] in idx and i - idx[p["d"]] >= 1:
            _append(_result("C3", p, day, i - idx[p["d"]], "bir_gun", bid))
        else:
            still.append(p)
    st["c3_open"] = still
    pos = st["pos"]
    if pos is not None and pos["d"] in idx:
        held = i - idx[pos["d"]]
        rising = i > 0 and day["S"] > series[i - 1]["S"]
        if rising or held >= MAX_HOLD:
            r = _result("C3b", pos, day, held, "yukselis" if rising else "sure", bid)
            _append(r)
            log.info("C3b-GÖLGE çıkış %s→%s: %.1f bp model, fill %s (EMİR YOK)", pos["d"], day["d"], r["bp_model"], r["bp_fill"])
            st["pos"] = None
    if rsi[i] < RSI_TH:
        sig = {"d": str(day["d"]), "E": day["E"], "S": day["S"], "rsi2": round(rsi[i], 2), "vix_prev": vix_prev,
               "caprev_gunu": caprev_flag(series, i, vix_prev), "fill": ask, "spread": None if ask is None else round(ask - bid, 3),
               "latency_s": None if tick is None else round(now - day["t"], 1)}
        _append({"kind": "signal", "c3b_giris": st["pos"] is None, **sig})
        st["c3_open"].append(sig)
        if st["pos"] is None:
            st["pos"] = sig
        log.info("C3b-GÖLGE sinyal %s: RSI2=%.1f S=%.2f E=%.2f ask=%s (EMİR YOK)", day["d"], rsi[i], day["S"], day["E"], ask)


def poll(mt5, log, resolve_symbol, get_vix, offset_fn, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK. Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if not force and now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    st = _load_state()
    today, mloc, wd = cs.to_local(now, TZ)
    vix = get_vix()
    changed = False
    if vix is not None:
        st["vix_hist"] = cs.update_vix_hist(st.get("vix_hist", {}), today, vix)
        changed = True
    done_today = st["last_d"] is not None and st["last_d"] >= str(today)
    if wd < 5 and mloc >= ENTRY_MIN and not done_today:
        sym = resolve_symbol(MARKET)
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M30, 0, FETCH_M30) if sym else None   # 0 → 15:30 barı açılışı görünür
        if rates is not None and len(rates) > 0:
            series = daily_series(cs._m15_utc(rates, offset_fn(sym)))
            if series and st["last_d"] is None:
                prior = [s for s in series if s["d"] < today]
                st["last_d"] = str(prior[-1]["d"]) if prior else None     # ilk açılışta geçmiş yeniden oynanmaz
            for i, day in enumerate(series):
                if st["last_d"] is not None and str(day["d"]) <= st["last_d"]:
                    continue
                on_time = day["d"] == today and now - day["t"] <= MAX_LATE_S
                tick = mt5.symbol_info_tick(sym) if on_time else None
                vf = cs.vix_features(st.get("vix_hist", {}), day["d"], None)
                process_day(st, series, i, tick, now, vf["vix_prev"], log)
                st["last_d"] = str(day["d"])
                changed = True
    if changed:
        _save_state(st)


def _karne() -> None:
    try:
        lines = EVENTS_JSONL.read_text(encoding="utf-8").splitlines()
    except OSError:
        print("henüz kayıt yok")
        return
    print(json.dumps(summarize([json.loads(x) for x in lines if x.strip()]), ensure_ascii=False, indent=1))
    print("Kart beklentisi: C3b +65 bp %78, C3 +46 bp %62 (geçmiş üst sınır). n < 30 iken hüküm verme; C3b yılda ≈15 işlem.")


if __name__ == "__main__":
    if "--karne" in sys.argv:
        _karne()
