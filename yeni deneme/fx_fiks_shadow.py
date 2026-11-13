"""fx_fiks_shadow.py — Forex fiks akışı dönüşü GÖLGE kaydı (FX-01 H8c + H9).

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Yalnız sanal giriş/çıkışı `fx_fiks_shadow.jsonl`'e yazar.
Hatalar bot akışını etkilemez (çağıran try/except içinde kullanır).

KANIT: research/fx_secim_20261113/RAPOR.md, defter §2.53, kartlar
  backend/data/evolution/go_live_cards/usdjpy_gotobi_fiks_donus.json (H8c, 5/6, B−)
  backend/data/evolution/go_live_cards/fx_aysonu_fiks_donus.json     (H9, 5/6, B−)

KURALLAR (dondurulmuş; değiştirmek kanıtı geçersiz kılar). Saatler UTC H1 bar AÇILIŞLARI:
  GOTOBI (H8c): gotobi günü D (ayın 5/10/15/20/25/30'u veya ayın son JP iş günü; hafta sonu/JP tatili → önceki JP iş günü)
    USDJPY open(D 01:00) > open(D−1 23:00) ise D 01:00'de SAT → D 06:00'da kapat. Stop yok.
  AYSONU (H9): ayın son hafta içi günü, her çift için r = open(16:00 Londra) − open(10:00 Londra);
    16:00 Londra'da −sign(r) yönünde gir → 20:00 Londra'da kapat. Çiftler: EURUSD GBPUSD USDJPY USDCHF USDCAD AUDUSD.
İki sonuç: bp_model (bar açılışları − kart maliyeti) ve bp_fill (tespit anındaki gerçek bid/ask; bar açılışından ≤ MAX_LATE_S sonra).

Karne:   python fx_fiks_shadow.py --karne
Kapatma: config.FX_FIKS_SHADOW_ENABLED = False
"""
from __future__ import annotations

import json
import math
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "fx_fiks_shadow.jsonl"
STATE_FILE = HERE / "fx_fiks_state.json"

GOTOBI_SYMBOL = "USDJPY"
GOTOBI_PRE_H, GOTOBI_IN_H, GOTOBI_OUT_H = 23, 1, 6            # UTC
AYSONU_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD")
AYSONU_PRE_H, AYSONU_IN_H, AYSONU_OUT_H = 10, 16, 20          # Londra
COST_BP = {"GOTOBI": 1.41, "EURUSD": 0.80, "GBPUSD": 0.85, "USDJPY": 0.95, "USDCHF": 1.05, "USDCAD": 1.00, "AUDUSD": 1.45}
FETCH_H1 = 72
POLL_EVERY_S = 60
MAX_LATE_S = 300
STALE_EXIT_H = 30
HOUR_S = 3600

# JP tatilleri (holidays.JP, 2026–2027). Takvim bitince her gün bir kez uyarı loglanır. Ezme: config.FX_JP_HOLIDAYS.
JP_HOLIDAYS: tuple[str, ...] = (
    "2026-01-01", "2026-01-12", "2026-02-11", "2026-02-23", "2026-03-20", "2026-04-29", "2026-05-03", "2026-05-04",
    "2026-05-05", "2026-05-06", "2026-07-20", "2026-08-11", "2026-09-21", "2026-09-22", "2026-09-23", "2026-10-12",
    "2026-11-03", "2026-11-23", "2027-01-01", "2027-01-11", "2027-02-11", "2027-02-23", "2027-03-21", "2027-03-22",
    "2027-04-29", "2027-05-03", "2027-05-04", "2027-05-05", "2027-07-19", "2027-08-11", "2027-09-20", "2027-09-23",
    "2027-10-11", "2027-11-03", "2027-11-23",
)

_last_poll = 0.0
_warned_day: str | None = None


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def _last_sunday(year: int, month: int) -> date:
    d = date(year + (month == 12), (month % 12) + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - 6) % 7)


def london_offset_h(utc: datetime) -> int:
    """Londra − UTC (saat). BST: son Pazar Mart 01:00Z → son Pazar Ekim 01:00Z."""
    s = datetime.combine(_last_sunday(utc.year, 3), datetime.min.time(), timezone.utc).replace(hour=1)
    e = datetime.combine(_last_sunday(utc.year, 10), datetime.min.time(), timezone.utc).replace(hour=1)
    return 1 if s <= utc < e else 0


def london_to_utc(d: date, hour: int) -> int:
    """Londra (d, hour:00) → UTC epoch (saniye)."""
    guess = datetime.combine(d, datetime.min.time(), timezone.utc) + timedelta(hours=hour)
    return int((guess - timedelta(hours=london_offset_h(guess))).timestamp())


def utc_at(d: date, hour: int) -> int:
    return int((datetime.combine(d, datetime.min.time(), timezone.utc) + timedelta(hours=hour)).timestamp())


def jp_holidays(cfg=None) -> set[date]:
    raw = getattr(cfg, "FX_JP_HOLIDAYS", None) if cfg is not None else None
    return {date.fromisoformat(x) for x in (raw or JP_HOLIDAYS)}


def is_jp_bday(d: date, hol: set[date]) -> bool:
    return d.weekday() < 5 and d not in hol


def gotobi_days(year: int, month: int, hol: set[date]) -> set[date]:
    """Araştırmadaki tanımın birebir kopyası (research/fx_secim_20261113/hyp.py::gotobi_days)."""
    first = date(year, month, 1)
    nxt = date(year + (month == 12), (month % 12) + 1, 1)
    days = [first + timedelta(days=i) for i in range((nxt - first).days)]
    bdays = [d for d in days if is_jp_bday(d, hol)]
    last_bd = max(bdays) if bdays else None
    out: set[date] = set()
    for d in days:
        if d.day in (5, 10, 15, 20, 25, 30) or d == last_bd:
            e = d
            while not is_jp_bday(e, hol) and e >= first:
                e -= timedelta(days=1)
            if e >= first:
                out.add(e)
    return out


def last_weekday_of_month(d: date) -> date:
    e = date(d.year + (d.month == 12), (d.month % 12) + 1, 1) - timedelta(days=1)
    while e.weekday() >= 5:
        e -= timedelta(days=1)
    return e


VALID_OFFSETS_S = (7200, 10800)    # Pepperstone sunucu = New York + 7 → UTC+2 (kış) / UTC+3 (yaz)


def server_offset(raw_s: float) -> int | None:
    """Ölçülen sunucu−UTC farkını tam saate yuvarlar (piyasa kapanışında bayat tick ±30 dk sapar). Geçersizse None."""
    off = int(round(raw_s / 3600.0)) * 3600
    return off if off in VALID_OFFSETS_S else None


def bar_open(bars: dict[int, float], t_utc: int) -> float | None:
    """bars: {UTC epoch bar başı: open}."""
    return bars.get(t_utc)


def bp(side: int, entry: float, exit_: float, cost: float) -> float:
    return round(side * math.log(exit_ / entry) * 1e4 - cost, 2)


def summarize(records: list[dict]) -> dict:
    out = {}
    for leg in ("GOTOBI", "AYSONU"):
        res = [r for r in records if r.get("kind") == "result" and r.get("leg") == leg]
        bm = [r["bp_model"] for r in res if r.get("bp_model") is not None]
        bf = [r["bp_fill"] for r in res if r.get("bp_fill") is not None]
        out[leg] = {"n": len(bm), "bp_model": round(sum(bm) / len(bm), 2) if bm else None,
                    "isabet": round(sum(x > 0 for x in bm) / len(bm), 3) if bm else None, "toplam_bp": round(sum(bm), 1),
                    "n_fill": len(bf), "bp_fill": round(sum(bf) / len(bf), 2) if bf else None,
                    "atlanan": sum(1 for r in records if r.get("kind") == "skip" and r.get("leg") == leg),
                    "kacirilan": sum(1 for r in records if r.get("kind") == "missed" and r.get("leg") == leg)}
    return out


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st.setdefault("pos", [])        # açık sanal pozisyonlar
    st.setdefault("done", [])       # işlenmiş olay anahtarları
    return st


def _save_state(st: dict) -> None:
    st["done"] = st["done"][-400:]
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ═════════════════════════ adım (saf mantık; mt5'siz test edilir) ═════════════════════════

def _open_pos(st, leg, sym, key, side, entry, t_in, t_out, tick, now, extra) -> None:
    on_time = tick is not None and now - t_in <= MAX_LATE_S
    fill = (tick[1] if side < 0 else tick[0]) if on_time else None
    p = {"leg": leg, "sym": sym, "key": key, "side": side, "E": entry, "t_in": t_in, "t_out": t_out, "fill": fill,
         "latency_s": round(now - t_in, 1), **extra}
    st["pos"].append(p)
    st["done"].append(key)
    _append({"kind": "signal", **p})


def _close_ready(st, bars_by_sym, ticks, now, log, append=_append) -> bool:
    changed, keep = False, []
    for p in st["pos"]:
        if now < p["t_out"]:
            keep.append(p)
            continue
        x = bar_open(bars_by_sym.get(p["sym"], {}), p["t_out"])
        if x is None:
            if now - p["t_out"] > STALE_EXIT_H * HOUR_S:
                append({"kind": "missed", "leg": p["leg"], "key": p["key"], "why": "cikis_bari_yok"})
                changed = True
            else:
                keep.append(p)
            continue
        cost = COST_BP["GOTOBI"] if p["leg"] == "GOTOBI" else COST_BP[p["sym"]]
        tk = ticks.get(p["sym"])
        on_time = tk is not None and now - p["t_out"] <= MAX_LATE_S and p.get("fill")
        bp_fill = None
        if on_time:
            xf = tk[0] if p["side"] < 0 else tk[1]       # kısa → ask'tan kapat, uzun → bid'den
            bp_fill = round(p["side"] * math.log(xf / p["fill"]) * 1e4, 2)
        r = {"kind": "result", "leg": p["leg"], "sym": p["sym"], "key": p["key"], "side": p["side"], "E": p["E"], "X": x,
             "bp_model": bp(p["side"], p["E"], x, cost), "bp_fill": bp_fill}
        append(r)
        log.info("FX-FİKS-GÖLGE çıkış %s %s: %.2f bp model, fill %s (EMİR YOK)", p["key"], p["sym"], r["bp_model"], bp_fill)
        changed = True
    st["pos"] = keep
    return changed


def step(st: dict, bars_by_sym: dict[str, dict[int, float]], ticks: dict, now: float, hol: set[date], log) -> bool:
    """Bir tarama. Değişiklik olduysa True. bars_by_sym: {sembol: {UTC bar başı: open}}; ticks: {sembol: (ask, bid)}."""
    changed = _close_ready(st, bars_by_sym, ticks, now, log)
    today = datetime.fromtimestamp(now, timezone.utc).date()

    # ── GOTOBI (USDJPY) ──
    key = f"GOTOBI:{today.isoformat()}"
    if today in gotobi_days(today.year, today.month, hol) and key not in st["done"]:
        t_in, t_pre = utc_at(today, GOTOBI_IN_H), utc_at(today - timedelta(days=1), GOTOBI_PRE_H)
        if now >= t_in:
            b = bars_by_sym.get(GOTOBI_SYMBOL, {})
            e, pre = bar_open(b, t_in), bar_open(b, t_pre)
            if e is None or pre is None:
                if now - t_in > 2 * HOUR_S:
                    _append({"kind": "missed", "leg": "GOTOBI", "key": key, "why": "bar_yok"})
                    st["done"].append(key)
                    changed = True
            elif e > pre:
                _open_pos(st, "GOTOBI", GOTOBI_SYMBOL, key, -1, e, t_in, utc_at(today, GOTOBI_OUT_H),
                          ticks.get(GOTOBI_SYMBOL), now, {"pre_bp": round(math.log(e / pre) * 1e4, 2)})
                log.info("FX-FİKS-GÖLGE gotobi SAT %s E=%.3f sabah +%.1f bp (EMİR YOK)", today, e, math.log(e / pre) * 1e4)
                changed = True
            else:
                _append({"kind": "skip", "leg": "GOTOBI", "key": key, "pre_bp": round(math.log(e / pre) * 1e4, 2)})
                st["done"].append(key)
                changed = True

    # ── AYSONU (6 majör) ──
    if today == last_weekday_of_month(today):
        t_in, t_pre, t_out = london_to_utc(today, AYSONU_IN_H), london_to_utc(today, AYSONU_PRE_H), london_to_utc(today, AYSONU_OUT_H)
        if now >= t_in:
            for sym in AYSONU_SYMBOLS:
                k = f"AYSONU:{today.isoformat()}:{sym}"
                if k in st["done"]:
                    continue
                b = bars_by_sym.get(sym, {})
                e, pre = bar_open(b, t_in), bar_open(b, t_pre)
                if e is None or pre is None or e == pre:
                    if now - t_in > 2 * HOUR_S or (e is not None and e == pre):
                        _append({"kind": "missed", "leg": "AYSONU", "key": k, "why": "bar_yok_veya_hareketsiz"})
                        st["done"].append(k)
                        changed = True
                    continue
                side = -1 if e > pre else 1
                _open_pos(st, "AYSONU", sym, k, side, e, t_in, t_out, ticks.get(sym), now,
                          {"pre_bp": round(math.log(e / pre) * 1e4, 2)})
                changed = True
    return changed


# ═════════════════════════ MT5 adaptörü ═════════════════════════

def _fetch(mt5, sym: str, srv_minus_utc: int) -> dict[int, float]:
    mt5.symbol_select(sym, True)
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, FETCH_H1)
    if r is None:
        return {}
    return {int(x["time"]) - srv_minus_utc: float(x["open"]) for x in r}


def poll(mt5, log, offset_fn, cfg=None, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK. Hata → çağıran yakalar.
    offset_fn(sembol) = broker sunucu saati − UTC (saniye)."""
    global _last_poll, _warned_day
    now = time.time() if now is None else now
    if not force and now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    hol = jp_holidays(cfg)
    today = datetime.fromtimestamp(now, timezone.utc).date()
    if max(hol) < today and _warned_day != str(today):
        log.warning("FX-FİKS-GÖLGE: JP tatil takvimi bitti — JP_HOLIDAYS / config.FX_JP_HOLIDAYS güncelle")
        _warned_day = str(today)
    st = _load_state()
    need = set(p["sym"] for p in st["pos"])
    tomorrow = today + timedelta(days=1)
    if today in gotobi_days(today.year, today.month, hol) or tomorrow in gotobi_days(tomorrow.year, tomorrow.month, hol):
        need.add(GOTOBI_SYMBOL)
    if today == last_weekday_of_month(today):
        need.update(AYSONU_SYMBOLS)
    if not need:
        return
    off = server_offset(offset_fn(GOTOBI_SYMBOL))
    if off is None:
        log.warning("FX-FİKS-GÖLGE: sunucu saat farkı ölçülemedi (bayat tick?) — tarama atlandı")
        return
    bars, ticks = {}, {}
    for s in need:
        bars[s] = _fetch(mt5, s, off)
        t = mt5.symbol_info_tick(s)
        if t is not None and t.ask and t.bid:
            ticks[s] = (float(t.ask), float(t.bid))
    if step(st, bars, ticks, now, hol, log):
        _save_state(st)


def _karne() -> None:
    recs = []
    if EVENTS_JSONL.exists():
        recs = [json.loads(x) for x in EVENTS_JSONL.read_text(encoding="utf-8").splitlines() if x.strip()]
    print(json.dumps(summarize(recs), ensure_ascii=False, indent=1))


if __name__ == "__main__" and "--karne" in sys.argv:
    _karne()
