"""xau_shadow.py — XAUUSD 1h "yeni 20-mum tepesinde BUY" GÖLGE kaydı (MK-04 / R0B_G1) + S2 filtreli varyant.

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Yalnız sinyal anını ve sonradan sonucu `xau_shadow.jsonl`'e yazar.
Hatalar fail-open: bot akışı etkilenmez (çağıran try/except içinde kullanır).

KANIT: MK-04 (research/pinbar_20261010) → mekanik yeniden üretim R0B_G1 (research/decider_xau_tpsl_20261015/mekanik,
Dukascopy 2008-26 tek-poz +0,079R/işlem, B+). S2 "önceki UTC günü altın >+%1 ise ATLA" (MK-12, A; ön kayıt
research/xau_best_days_20261015/dogrulama/PROTOCOL.md): ortR +0,079→+0,110 ama bağımsız ileri kanıt 4 ay → bu yüzden
yalnız GÖLGEDE, filtresiz varyantla YAN YANA ölçülür (≥30 bayraklı olayda yeniden değerlendirme).
XAU gün-içi botta KAPALI (BLOCKED_SYMBOLS) — bu yüzden gölge.

KURAL (2026-10-16: mekanik tanıma — mech.prep_h1 + rules.events("R0") + mech.path_sim + mech.one_position — hizalandı):
  * Segment: ardışık iki bar arası > 3 saat → yeni segment (hafta sonu/tatil).
  * TR: segment başında h−l, aksi halde klasik. ATR = TR[i−13..i] ortalaması — sinyal barı DAHİL (eski gölge hariç
    tutuyordu).
  * Sinyal: kapanmış 1h bar i'nin yükseği ≥ bars[i−20..i−1] en yükseği (pencere boşluklardan kesilmez). Giriş barı
    (sonraki bar) aynı segmentte değilse olay YOK (Cuma son barı) → 'void'.
  * Araştırma girişi = giriş barı açılışı + 0,12 (SPREAD_RESEARCH); canlı bacak = sinyal kapanışından hemen sonraki ask.
    Stop = giriş − 1,5×ATR; TP yok. Çıkış: giriş barı dahil 20. barın kapanışı, ya da segment bitmeden önceki son barın
    kapanışı ('seg'); stop barın düşüğü ≤ stop → stop (j>0'da boşluk → bar açılışı).
  * Tek pozisyon (mech.one_position): pozisyon kilidi ARAŞTIRMA bacağının çıkış barıyla belirlenir. Her barda önce
    açık olaylar çözülür, SONRA sinyal bakılır → çıkış barında gelen sinyal açılır (mekanikteki gibi; eski gölge açmıyordu).
  * İki varyant aynı olay listesinde bayrakla: in_base (filtresiz MK-04) ve in_s2 (MK-04 + S2). S2'nin atladığı olay
    filtreli varyantta pozisyonu KİLİTLEMEZ (araştırmadaki filtre yeniden yürütmesi).
  * S2: giriş tarihi = UTC tarih(t_i + 1h); g1 = tarihi giriş tarihinden küçük son barın kapanışı; g2 = tarihi g1 barının
    tarihinden küçük son barın kapanışı (Pazar akşam seansı ayrı gün). prevday_ret = g1/g2 − 1; skip_s2 = > eşik.
  * YALNIZ KAYIT (emir/atlama kararına girmez): dens24 (S1 seri kırılım sayısı), fomc_in_window, D1 NR4/inside,
    D1 20g kırılım, 52 hafta tepesi yakınlığı, önceki NY gününün VIX'i.

Parite sınaması (Mac'te, Duka verisiyle): research/xau_best_days_20261015/golge_parite/parity.py
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "xau_shadow.jsonl"
STATE_FILE = HERE / "xau_shadow_state.json"
STATE_VER = 2

# ── dondurulmuş kural parametreleri (değiştirmek kanıtı geçersiz kılar) ──────────
LOOK = 20
ATR_N = 14
STOP_K = 1.5
HOLD = 20
BAR_S = 3600
GAP_S = 3 * 3600            # mech.GAP_H: bar arası > 3 saat → segment sonu
SPREAD_RESEARCH = 0.12      # mekanik R0B_G1 varsayımı (run_main.SPREAD_A)
MAX_LATE_S = 600            # bar kapanışından bu kadar sonra tespit → canlı bacak yok (dolum gecikmesi çok büyük)
FETCH_H1 = 200
FETCH_D1 = 262
POLL_EVERY_S = 30
EXPIRE_S = 20 * 86400
S2_THR = 0.010              # MK-12 ön kaydı; config XAU_SHADOW_S2_THR ile ezilebilir
DENS_N = 24
DENS_MIN_BARS = 45          # dens24 için gereken kapanmış bar sayısı (24 + 20 + 1)
FOMC_HOURS = 20
D1_NR = 4
D1_BRK = 20
D1_52W = 250
# 2026 planlı FOMC açıklamaları, 14:00 ET → UTC (DST: 03-08 → 11-01). Takvim bitince alan None yazılır.
FOMC_UTC = ("2026-01-28 19:00", "2026-03-18 18:00", "2026-04-29 18:00", "2026-06-17 18:00",
            "2026-07-29 18:00", "2026-09-16 18:00", "2026-10-28 18:00", "2026-12-09 19:00")


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def _utc_date(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")


def seg_start(bars: list[dict], j: int) -> bool:
    """bars[j] segmentin ilk barı mı (önceki bar yok ya da > 3 saat boşluk)."""
    return j == 0 or bars[j]["t"] - bars[j - 1]["t"] > GAP_S


def true_range(bars: list[dict], j: int) -> float:
    b = bars[j]
    if seg_start(bars, j):
        return b["high"] - b["low"]
    pc = bars[j - 1]["close"]
    return max(b["high"] - b["low"], abs(b["high"] - pc), abs(b["low"] - pc))


def atr_at(bars: list[dict], i: int) -> float | None:
    """mech.prep_h1 ATR'si: TR[i−13..i] ortalaması (sinyal barı DAHİL). Pencere başında önceki bar bilinmediği için
    TR[i−13]'ün önceki barı da pencerede olmalı → i ≥ 14."""
    if i < ATR_N:
        return None
    return sum(true_range(bars, j) for j in range(i - ATR_N + 1, i + 1)) / ATR_N


def is_signal(bars: list[dict], i: int) -> bool:
    """rules.events R0 BUY: high_i ≥ max(high_{i−20..i−1}) (rolling(20).max().shift(1); boşluklar kesmez)."""
    if i < LOOK:
        return False
    return bars[i]["high"] >= max(b["high"] for b in bars[i - LOOK: i])


def is_event_bar(bars: list[dict], j: int) -> bool:
    """Araştırma olay listesinde mi: sinyal + sonraki bar aynı segmentte (Cuma son barı sayılmaz)."""
    return j + 1 < len(bars) and is_signal(bars, j) and not seg_start(bars, j + 1)


def dens24(bars: list[dict], i: int) -> int | None:
    """S1 seri kırılım (anatomi xa_brk_density24): [i−24, i−1] içindeki olay barı sayısı. ≥45 kapanmış bar gerekir."""
    if i < DENS_MIN_BARS - 1:
        return None
    return sum(is_event_bar(bars, j) for j in range(i - DENS_N, i))


def prevday_ret(bars: list[dict], i: int) -> float | None:
    """S2 (makro 04_features gprev): g1 = giriş UTC tarihinden önceki son bar kapanışı, g2 = g1 tarihinden önceki son
    bar kapanışı. Bar olan her UTC günü sayılır (Pazar akşamı ayrı gün). Geçmiş yetmezse None."""
    ent_date = _utc_date(bars[i]["t"] + BAR_S)
    k1 = next((k for k in range(i, -1, -1) if _utc_date(bars[k]["t"]) < ent_date), None)
    if k1 is None:
        return None
    d1 = _utc_date(bars[k1]["t"])
    k2 = next((k for k in range(k1 - 1, -1, -1) if _utc_date(bars[k]["t"]) < d1), None)
    if k2 is None:
        return None
    return bars[k1]["close"] / bars[k2]["close"] - 1


def fomc_in_window(entry_t: float, fomc_utc=FOMC_UTC, hours: int = FOMC_HOURS) -> bool | None:
    """Planlı FOMC açıklama anı ∈ [giriş, giriş+20 saat) mı. Takvim giriş anını kapsamıyorsa None."""
    ts = sorted(datetime.strptime(x, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() for x in fomc_utc)
    if not ts or entry_t > ts[-1]:
        return None
    return any(entry_t <= f < entry_t + hours * 3600 for f in ts)


def d1_features(d1: list[dict], high_i: float, close_i: float) -> dict:
    """Son KAPANMIŞ D1 barlarından (eski→yeni) kayıt alanları — erken_sinyal F2/F6/F7 ve anatomi 52h tanımları."""
    out = {"d1_nr4": None, "d1_inside": None, "d1_nr4_inside": None, "d1_hh20": None, "d1_brk20": None,
           "d1_hh250": None, "at_52wh": None, "dist_52wh_pct": None}
    if len(d1) >= 2:
        a, b = d1[-2], d1[-1]
        out["d1_inside"] = bool(b["high"] <= a["high"] and b["low"] >= a["low"])
    if len(d1) >= D1_NR:
        rng = [x["high"] - x["low"] for x in d1[-D1_NR:]]
        out["d1_nr4"] = bool(rng[-1] <= min(rng))
    if out["d1_nr4"] is not None and out["d1_inside"] is not None:
        out["d1_nr4_inside"] = out["d1_nr4"] or out["d1_inside"]
    if len(d1) >= D1_BRK:
        hh = max(x["high"] for x in d1[-D1_BRK:])
        out["d1_hh20"], out["d1_brk20"] = hh, bool(high_i >= hh)
    if len(d1) >= D1_52W:
        hh = max(x["high"] for x in d1[-D1_52W:])
        out["d1_hh250"], out["at_52wh"] = hh, bool(high_i >= hh)
        out["dist_52wh_pct"] = round(close_i / hh - 1, 5)
    return out


def _leg(entry: float, stop: float, seq: list[dict]) -> tuple[str, float, int] | None:
    """Tek bacak (mech.path_sim, TP yok). seq: giriş barından itibaren kapanmış barlar.
    Dönüş (how, çıkış fiyatı, çıkış barının seq indeksi) ya da None (sürüyor)."""
    for j, b in enumerate(seq[:HOLD]):
        if j and b["t"] - seq[j - 1]["t"] > GAP_S:
            return "seg", seq[j - 1]["close"], j - 1
        if b["low"] <= stop:
            return "stop", (min(b["open"], stop) if j else stop), j
    if len(seq) >= HOLD:
        return "time", seq[HOLD - 1]["close"], HOLD - 1
    return None


def advance(ev: dict, bars: list[dict]) -> str:
    """Olayın bacaklarını ilerletir (ev yerinde güncellenir: 'rx' araştırma, 'lx' canlı).
    Dönüş: 'void' (giriş barı başka segmentte → mekanikte olay yok) | 'done' | 'pending'."""
    seq = [b for b in bars if b["t"] > ev["sig_t"]]
    if not seq:
        return "pending"
    if seq[0]["t"] - ev["sig_t"] > GAP_S:
        return "void"
    sd = ev["stop_dist"]
    if "rx" not in ev:
        entry_r = seq[0]["open"] + SPREAD_RESEARCH
        r = _leg(entry_r, entry_r - sd, seq)
        if r is not None:
            how, px, j = r
            ev["rx"] = {"how": how, "exit_px": px, "exit_bar_t": seq[j]["t"], "entry": entry_r,
                        "entry_bar_open": seq[0]["open"], "R": round((px - entry_r) / sd, 4), "bars_held": j + 1}
    if ev.get("entry_ask") is not None and "lx" not in ev:
        r = _leg(ev["entry_ask"], ev["stop"], seq)
        if r is not None:
            how, px, j = r
            ev["lx"] = {"how": how, "exit_px": px, "exit_bar_t": seq[j]["t"], "bars_held": j + 1,
                        "R": round((px - ev["entry_ask"]) / sd, 4),
                        "R_paper": round((px - ev["paper_close"]) / sd, 4)}
    done = "rx" in ev and (ev.get("entry_ask") is None or "lx" in ev)
    return "done" if done else "pending"


def _result(ev: dict) -> dict:
    rx, lx = ev["rx"], ev.get("lx") or {}
    res = {**{k: v for k, v in ev.items() if k not in ("rx", "lx")}, "status": "done",
           "how_research": rx["how"], "exit_px_research": rx["exit_px"], "exit_bar_t_research": rx["exit_bar_t"],
           "entry_research": rx["entry"], "entry_bar_open": rx["entry_bar_open"], "R_research": rx["R"],
           "bars_held_research": rx["bars_held"]}
    if lx:
        res.update(how=lx["how"], exit_px=lx["exit_px"], exit_bar_t=lx["exit_bar_t"], bars_held=lx["bars_held"],
                   R=lx["R"], R_paper=lx["R_paper"],
                   slip_r=round((ev["entry_ask"] - ev["paper_close"]) / ev["stop_dist"], 4),
                   slip_vs_research_r=round((ev["entry_ask"] - rx["entry"]) / ev["stop_dist"], 4))
    return res


def _busy(open_evs: list[dict], key: str) -> bool:
    """Varyantın pozisyonu dolu mu: araştırma bacağı henüz bitmemiş bir olay var mı (mech.one_position)."""
    return any(e.get(key) and "rx" not in e for e in open_evs)


def step(st: dict, bars: list[dict], i: int, cfg: dict | None = None, live: dict | None = None,
         ctx_fn=None) -> list[dict]:
    """bars[i] kapandığında bir adım: önce açık olayları çöz, sonra sinyal. Yalnız bars[:i+1] görülür.
    cfg: {"s2_enabled", "s2_thr", "fomc_utc", "warmup"}; live: {"now", "ask", "bid"} (yalnız en son bar);
    ctx_fn(sig_t, high, close) → ek kayıt alanları (D1/VIX). Dönüş: jsonl'e yazılacak kayıtlar."""
    cfg = cfg or {}
    view = bars[: i + 1]
    recs: list[dict] = []
    keep = []
    for ev in st["open"]:
        s = advance(ev, view)
        if s == "void":
            recs.append({"kind": "result", **ev, "status": "void",
                         "reason": "segment sonu: giriş barı > 3 saat sonra (mekanikte olay yok)"})
        elif s == "done":
            recs.append({"kind": "result", **_result(ev)})
        elif view[-1]["t"] - ev["sig_t"] > EXPIRE_S:
            recs.append({"kind": "result", **{k: v for k, v in ev.items() if k not in ("rx", "lx")},
                         "status": "expired"})
        else:
            keep.append(ev)
    st["open"] = keep

    if not is_signal(view, i):
        return recs
    atr = atr_at(view, i)
    if atr is None:
        return recs
    b = view[i]
    pr = prevday_ret(view, i)
    skip_s2 = pr is not None and pr > cfg.get("s2_thr", S2_THR)
    dn = dens24(view, i)
    base_open = not _busy(keep, "in_base")
    s2_on = cfg.get("s2_enabled", True)
    if not s2_on:
        s2_dec = "off"
    elif skip_s2:
        s2_dec = "skip_s2"
    else:
        s2_dec = "open" if not _busy(keep, "in_s2") else "overlap"
    base = {"sig_t": b["t"], "sig_high": b["high"], "paper_close": b["close"], "atr": round(atr, 5),
            "stop_dist": STOP_K * atr, "spread_assumed": SPREAD_RESEARCH,
            "base_decision": "open" if base_open else "overlap", "s2_decision": s2_dec,
            "in_base": base_open, "in_s2": s2_dec == "open",
            "prevday_ret": None if pr is None else round(pr, 6), "skip_s2": bool(skip_s2),
            "dens24": dn, "skip_s1_candidate": None if dn is None else dn >= 2,
            "fomc_in_window": fomc_in_window(b["t"] + BAR_S, cfg.get("fomc_utc", FOMC_UTC))}
    if cfg.get("warmup"):
        base["warmup"] = True
    if ctx_fn is not None:
        try:
            base.update(ctx_fn(b["t"], b["high"], b["close"]))
        except Exception as e:                       # yalnız kayıt alanları — kararı etkilemez
            base["ctx_error"] = str(e)[:120]
    if not (base["in_base"] or base["in_s2"]):
        recs.append({"kind": "skip", "reason": f"base={base['base_decision']} s2={s2_dec}", **base})
        return recs

    ev = {**base, "status": "open", "entry_ask": None, "live_reason": None}
    late = None if live is None else live["now"] - (b["t"] + BAR_S)
    if live is None or live.get("ask") is None:
        ev["live_reason"] = "geride kalındı / tick yok"
    elif late > MAX_LATE_S:
        ev["live_reason"], ev["latency_s"] = "geç tespit", round(late, 1)
    else:
        ask, bid = float(live["ask"]), float(live["bid"])
        ev.update(entry_t=live["now"], entry_ask=ask, entry_bid=bid, spread=round(ask - bid, 3),
                  stop=ask - ev["stop_dist"], latency_s=round(late, 1))
    st["open"].append(ev)
    recs.append({"kind": "event", **ev})
    return recs


# ═════════════════════════ durum / kayıt ═════════════════════════

def _new_state() -> dict:
    return {"ver": STATE_VER, "last_bar": None, "open": [], "vix_hist": {}}


def _load_state() -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return _new_state()
    if st.get("ver") != STATE_VER:
        for ev in st.get("open", []):
            _append({"kind": "result", **ev, "status": "void", "reason": "kural v2'ye geçti (mekanik hizalama)"})
        return _new_state()
    return st


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with open(EVENTS_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **rec}, ensure_ascii=False) + "\n")


def _bars(rates, off_s: int) -> list[dict]:
    return [{"t": int(r["time"]) - off_s, "open": float(r["open"]), "high": float(r["high"]),
             "low": float(r["low"]), "close": float(r["close"])} for r in rates]


def _cfg(config) -> dict:
    return {"s2_enabled": bool(getattr(config, "XAU_SHADOW_S2_ENABLED", True)),
            "s2_thr": float(getattr(config, "XAU_SHADOW_S2_THR", S2_THR)),
            "fomc_utc": tuple(getattr(config, "XAU_SHADOW_FOMC_UTC", FOMC_UTC))}


def _make_ctx_fn(mt5, sym: str, off: int, st: dict):
    """D1 + önceki NY günü VIX kayıt alanları (lazy D1 çekimi; yalnız sinyal olursa)."""
    cache: dict = {}

    def fn(sig_t: float, high: float, close: float) -> dict:
        if "d1" not in cache:
            r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, FETCH_D1)
            cache["d1"] = _bars(r, off) if r is not None else []
        d1 = [x for x in cache["d1"] if x["t"] + 86400 <= sig_t + BAR_S]   # karar anında kapanmış günler
        out = d1_features(d1, high, close)
        out["vix_prev"] = None
        try:
            from caprev_shadow import to_local
            ny_day = str(to_local(sig_t + BAR_S, "US")[0])
            prev = [k for k in sorted(st.get("vix_hist", {})) if k < ny_day]
            out["vix_prev"] = st["vix_hist"][prev[-1]] if prev else None
        except Exception:
            pass
        return out
    return fn


# ═════════════════════════ MT5 sarmalayıcı (emir yok) ═════════════════════════

_last_poll = 0.0


def poll(mt5, log, resolve_symbol, offset_fn, now: float | None = None, force: bool = False,
         get_vix=None, config=None) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK. Hata → çağıran yakalar.
    Son kayıttan bu yana kapanan TÜM barlar sırayla işlenir (kopuşta durum makinesi mekanikten sapmasın)."""
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
    off = offset_fn(sym)
    bars = _bars(rates, off)
    st = _load_state()
    changed = False
    if get_vix is not None:
        try:
            from caprev_shadow import to_local, update_vix_hist
            v = get_vix()
            if v is not None:
                st["vix_hist"] = update_vix_hist(st.get("vix_hist", {}), to_local(now, "US")[0], v)
        except Exception:
            pass

    cfg = _cfg(config)
    last_t = st.get("last_bar")
    warm = last_t is None
    todo = [k for k, b in enumerate(bars) if last_t is None or b["t"] > last_t]
    if not todo:
        return
    ctx_fn = _make_ctx_fn(mt5, sym, off, st)
    tick = mt5.symbol_info_tick(sym)
    for k in todo:
        live = None
        if k == len(bars) - 1 and tick is not None:
            live = {"now": now, "ask": float(tick.ask), "bid": float(tick.bid)}
        for rec in step(st, bars, k, {**cfg, "warmup": warm}, live, ctx_fn):
            _append(rec)
            if warm:
                continue
            if rec["kind"] == "event":
                log.info("XAU-GÖLGE yeni 20-mum tepesi: base=%s s2=%s ask=%s stop_dist=%.2f prevday=%s dens24=%s "
                         "(EMİR YOK)", rec["base_decision"], rec["s2_decision"], rec.get("entry_ask"),
                         rec["stop_dist"], rec["prevday_ret"], rec["dens24"])
            elif rec["kind"] == "result":
                log.info("XAU-GÖLGE sonuç %s: R=%s (araştırma %s %s) base=%s s2=%s", rec.get("status"),
                         rec.get("R"), rec.get("how_research"), rec.get("R_research"), rec.get("in_base"),
                         rec.get("in_s2"))
        changed = True
    st["last_bar"] = bars[-1]["t"]
    if changed:
        _save_state(st)
