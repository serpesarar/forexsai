"""dax_fomc_shadow.py — FOMC öncesi DAX uzun (DP-03) GÖLGE kaydı.

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Yalnız sanal giriş/çıkışı `dax_fomc_shadow.jsonl`'e yazar.
Hatalar bot akışını etkilemez (çağıran try/except içinde kullanır).

KANIT: research/dax_profesor_20261112/RAPOR.md, kart backend/data/evolution/go_live_cards/dax_fomc_oncesi.json
(B, 5/6 — yalnız hacim geçmedi). ^GDAXI 2008-26 n=144 +28,1 bp vs +2,7; broker GER40 2019-26 n=52 net +31,9 bp.

KURAL (dondurulmuş; değiştirmek kanıtı geçersiz kılar):
  FOMC duyuru gününden önceki hafta içi günü 17:30 Berlin M30 barının AÇILIŞINDA GER40 uzun →
  FOMC günü 19:30 Berlin M30 barının AÇILIŞINDA çıkış (duyuru 20:00 Berlin, Xetra 17:30'da kapalı). Stop yok.
İki sonuç:
  bp_model: kartla birebir (bar açılışları, spread 1,35 pt, swap 1,35 bp/gece).
  bp_fill: tespit anındaki gerçek ask/bid (yalnız bar açılışından ≤ MAX_LATE_S sonra görülürse).
`vix_prev` (önceki gün VIX) kaydedilir: kartta VIX ≥ 18,4 → +38 bp, altı → +20 bp (sonradan, karar dışı).

FOMC takvimi elle tutulur (federalreserve.gov). Ezme: config.DAX_FOMC_DATES = ["2027-01-27", ...].
Takvimde ileri tarih kalmayınca her gün bir kez uyarı loglanır.

Karne:   python dax_fomc_shadow.py --karne
Kapatma: config.DAX_FOMC_SHADOW_ENABLED = False
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import caprev_shadow as cs   # saat dilimi yardımcıları + VIX geçmişi; ikisi de emir göndermez

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "dax_fomc_shadow.jsonl"
STATE_FILE = HERE / "dax_fomc_state.json"
CAPREV_STATE = HERE / "caprev_state.json"

MARKET = "GDAXI.INDX"
TZ = "EU"
ENTRY_MIN = 17 * 60 + 30         # önceki gün 17:30 Berlin
EXIT_MIN = 19 * 60 + 30          # FOMC günü 19:30 Berlin
SPREAD_MODEL = 1.35              # puan (araştırmadaki 1,5 × medyan spread)
SWAP_BP_NIGHT = 4.94 / 365 * 100
FETCH_M30 = 400                  # ≈ 8 işlem günü
POLL_EVERY_S = 60
MAX_LATE_S = 300
STALE_EXIT_DAYS = 3              # çıkış barı bu kadar gün bulunamazsa olay 'kayıp' kapanır

# Duyuru günleri (iki günlük toplantının ikinci günü). Kaynak: federalreserve.gov FOMC takvimi.
FOMC_DATES: tuple[str, ...] = (
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
)

_last_poll = 0.0
_warned_day: str | None = None


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def fomc_dates(cfg=None) -> list[date]:
    raw = getattr(cfg, "DAX_FOMC_DATES", None) if cfg is not None else None
    return sorted(date.fromisoformat(x) for x in (raw or FOMC_DATES))


def prev_weekday(d: date) -> date:
    p = d - timedelta(days=1)
    while p.weekday() >= 5:
        p -= timedelta(days=1)
    return p


def next_event(today: date, dates: list[date]) -> date | None:
    """Bugün veya sonrasında ilk FOMC duyuru günü."""
    for d in dates:
        if d >= today:
            return d
    return None


def bar_open_at(bars: list[dict], d: date, minute: int) -> dict | None:
    """Berlin (d, minute) anında AÇILAN M30 bar (UTC epoch'lu)."""
    for b in bars:
        bd, bm, _ = cs.to_local(b["t"], TZ)
        if bd == d and bm == minute:
            return b
    return None


def model_bp(entry: float, exit_: float, nights: int, spread: float = SPREAD_MODEL) -> float:
    return (exit_ / (entry + spread) - 1.0) * 1e4 - SWAP_BP_NIGHT * nights


def summarize(records: list[dict]) -> dict:
    res = [r for r in records if r.get("kind") == "result"]
    bm = [r["bp_model"] for r in res if r.get("bp_model") is not None]
    bf = [r["bp_fill"] for r in res if r.get("bp_fill") is not None]
    return {"n": len(bm), "bp_model": round(sum(bm) / len(bm), 1) if bm else None,
            "isabet": round(sum(x > 0 for x in bm) / len(bm), 3) if bm else None, "toplam_bp": round(sum(bm), 1),
            "n_fill": len(bf), "bp_fill": round(sum(bf) / len(bf), 1) if bf else None,
            "kacirilan": sum(1 for r in records if r.get("kind") == "missed")}


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st.setdefault("pos", None)          # açık sanal pozisyon
    st.setdefault("done", [])           # kapanmış/kaçırılmış FOMC günleri
    if not st.get("vix_hist"):
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


# ═════════════════════════ adım (saf mantık; mt5'siz test edilir) ═════════════════════════

def step(st: dict, bars: list[dict], now: float, dates: list[date], tick, vix_prev: float | None, log) -> bool:
    """Bir tarama. Değişiklik olduysa True. `tick` = (ask, bid) veya None."""
    today, mloc, _ = cs.to_local(now, TZ)
    changed = False
    pos = st["pos"]
    if pos is not None:                                   # çıkış
        fd = date.fromisoformat(pos["fomc"])
        if today > fd + timedelta(days=STALE_EXIT_DAYS):
            _append({"kind": "missed", "fomc": pos["fomc"], "why": "cikis_bari_yok"})
            st["pos"], changed = None, True
            st["done"].append(pos["fomc"])
        elif today > fd or (today == fd and mloc >= EXIT_MIN):
            b = bar_open_at(bars, fd, EXIT_MIN)
            if b is not None:
                nights = (fd - date.fromisoformat(pos["d"])).days
                on_time = tick is not None and today == fd and now - b["t"] <= MAX_LATE_S
                fill = pos.get("fill")
                bp_fill = round((tick[1] / fill - 1.0) * 1e4 - SWAP_BP_NIGHT * nights, 2) if on_time and fill else None
                r = {"kind": "result", "fomc": pos["fomc"], "entry_d": pos["d"], "E_entry": pos["E"], "E_exit": b["open"],
                     "nights": nights, "bp_model": round(model_bp(pos["E"], b["open"], nights), 2), "bp_fill": bp_fill,
                     "vix_prev": pos.get("vix_prev")}
                _append(r)
                log.info("DAX-FOMC-GÖLGE çıkış %s: %.1f bp model, fill %s (EMİR YOK)", pos["fomc"], r["bp_model"], bp_fill)
                st["pos"], changed = None, True
                st["done"].append(pos["fomc"])
        return changed
    ev = next_event(today, dates)                         # giriş
    if ev is None or ev.isoformat() in st["done"]:
        return changed
    ed = prev_weekday(ev)
    if today == ed and mloc >= ENTRY_MIN:
        b = bar_open_at(bars, ed, ENTRY_MIN)
        if b is None:
            if mloc >= ENTRY_MIN + 60:                   # bar hâlâ yok (tatil/boşluk) → kaçırıldı
                _append({"kind": "missed", "fomc": ev.isoformat(), "why": "giris_bari_yok"})
                st["done"].append(ev.isoformat())
                changed = True
            return changed
        on_time = tick is not None and now - b["t"] <= MAX_LATE_S
        st["pos"] = {"fomc": ev.isoformat(), "d": ed.isoformat(), "E": b["open"], "fill": tick[0] if on_time else None,
                     "spread": round(tick[0] - tick[1], 3) if on_time else None, "vix_prev": vix_prev,
                     "latency_s": round(now - b["t"], 1)}
        _append({"kind": "signal", **st["pos"]})
        log.info("DAX-FOMC-GÖLGE giriş %s (FOMC %s) E=%.1f ask=%s (EMİR YOK)", ed, ev, b["open"], st["pos"]["fill"])
        changed = True
    elif today > ed:                                      # giriş günü geçti, pozisyon yok → kaçırıldı (bot kapalıydı)
        _append({"kind": "missed", "fomc": ev.isoformat(), "why": "bot_kapali"})
        st["done"].append(ev.isoformat())
        changed = True
    return changed


def poll(mt5, log, resolve_symbol, get_vix, offset_fn, cfg=None, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK. Hata → çağıran yakalar."""
    global _last_poll, _warned_day
    now = time.time() if now is None else now
    if not force and now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    dates = fomc_dates(cfg)
    today, mloc, _ = cs.to_local(now, TZ)
    st = _load_state()
    if next_event(today, dates) is None and st["pos"] is None:
        if _warned_day != str(today):
            log.warning("DAX-FOMC-GÖLGE: takvimde ileri FOMC tarihi yok — FOMC_DATES / config.DAX_FOMC_DATES güncelle")
            _warned_day = str(today)
        return
    vix = get_vix()
    changed = False
    if vix is not None:
        st["vix_hist"] = cs.update_vix_hist(st.get("vix_hist", {}), today, vix)
        changed = True
    ev = next_event(today, dates)
    near = st["pos"] is not None or (ev is not None and today >= prev_weekday(ev))
    if near:
        sym = resolve_symbol(MARKET)
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M30, 0, FETCH_M30) if sym else None
        if rates is not None and len(rates) > 0:
            bars = cs._m15_utc(rates, offset_fn(sym))
            t = mt5.symbol_info_tick(sym)
            tick = (t.ask, t.bid) if t is not None else None
            vf = cs.vix_features(st.get("vix_hist", {}), today, None)
            changed = step(st, bars, now, dates, tick, vf["vix_prev"], log) or changed
    if changed:
        _save_state(st)


def _karne() -> None:
    try:
        lines = EVENTS_JSONL.read_text(encoding="utf-8").splitlines()
    except OSError:
        print("henüz kayıt yok")
        return
    print(json.dumps(summarize([json.loads(x) for x in lines if x.strip()]), ensure_ascii=False, indent=1))
    print("Kart beklentisi: broker +31,9 bp/olay, isabet %63 (2019-26). Yılda 8 olay; n < 16 iken hüküm verme.")


if __name__ == "__main__":
    if "--karne" in sys.argv:
        _karne()
