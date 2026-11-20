"""ksg_shadow.py — KSG GÖLGE etiketleri: sabah kurtarma (KZ-02), 18:30 ekleme (KZ-03), olay öncesi gece (OG-01), OPEX vetosu (GX-06).

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Her KSG sinyal gecesi (OPEX ile vetolananlar DAHİL) için bar açılışlarından sanal sonuçları
`ksg_shadow.jsonl`'e yazar. Hatalar bot akışını etkilemez (çağıran try/except içinde kullanır).

KANIT (hepsi C / C+ — canlı değil, ileri ölçüm):
  research/ksg_tpsl_20261119/RAPOR.md  KZ-02 sabah kurtarma: 09:30'da açık net ≤ −60 bp → 16:00'a tut. Duka +1,7 bp/gece, KSG'ye özgü
      (karşı kol eksi) ama 2016–17'de −1,5 → C. KZ-03 ekleme: 18:30 açılışında açık net ≤ −40 bp → ikinci birim (18:00 hali E97 artefaktı).
  research/ksg_olay_gecesi_20261119/RAPOR.md  OG-01: ertesi gün FOMC ∨ ertesi sabah CPI/NFP ∨ bilanço gecesi → C+.
  research/ksg_opex_canli_20261119  GX-06: OPEX vetosu CANLI (ksg_live); vetolanan gece burada izlenir.
KURAL (KSG ile aynı, dondurulmuş): 15:00 → 16:00 ET M30 açılışı aşağı → 16:00 ask AL → sonraki hafta içi 09:30 ET bid SAT (ksg_live ile aynı
çıkış). Modelde ask = açılış + SPREAD_MODEL, finansman 1,756 bp/takvim günü.
Olay etiketleri: FOMC ertesi gün burada (dax_fomc_shadow takvimi); CPI/NFP/bilanço değerlendirmede takvimle eklenir (tarih kaydı yeter).

Durdurma/karar ölçütü (önceden yazılı): kurtarma n ≥ 40 tutulan gecede ort(16:00 − 09:30) > 0 ve medyan > 0 → canlı kararı kullanıcıya;
ekleme n ≥ 30 eklenen gecede ort > 0 ve en iyi 5 hariç > 0 → kullanıcıya; aksi halde kapat.
Karne:   python ksg_shadow.py --karne
Kapatma: config.KSG_SHADOW_ENABLED = False
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

import c3b_shadow as sh          # TZ="US", MARKET="NDX.INDX"
import caprev_shadow as cs
import ksg_live as ks

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "ksg_shadow.jsonl"
STATE_FILE = HERE / "ksg_shadow_state.json"
SPREAD_MODEL = 1.5               # NAS100 puan (araştırma U1/EET30 ile aynı)
FIN_BP_PER_DAY = 6.41 / 365 * 100
RESCUE_BP = -60.0                # KZ-02
ADD_BP = -40.0                   # KZ-03
ADD_MIN = 18 * 60 + 30           # 18:30 ET (18:00 yeniden açılışı E97 → kullanılmaz)
OPEN_MIN = 9 * 60 + 30
CLOSE_MIN = 16 * 60
FETCH_M30 = 400                  # ≈ 8 işlem günü
POLL_EVERY_S = 60
STALE_DAYS = 6                   # bu kadar gün sonra tamamlanamayan gece 'eksik' kapanır

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def _opens(bars: list[dict]) -> dict[tuple[date, int], float]:
    out = {}
    for b in bars:
        d, m, _ = cs.to_local(b["t"], sh.TZ)
        out[(d, m)] = b["open"]
    return out


def _next_session(op: dict, d: date) -> date | None:
    """ksg_live.exit_due ile aynı: d'den sonraki ilk hafta içi gün, 09:30 barı olan."""
    cands = sorted({k[0] for k in op if k[0] > d and k[1] == OPEN_MIN and k[0].weekday() < 5})
    return cands[0] if cands else None


def fomc_tomorrow(nd: date | None, cfg=None) -> bool:
    if nd is None:
        return False
    try:
        import dax_fomc_shadow as dfs
        dates = getattr(cfg, "DAX_FOMC_DATES", None) or dfs.FOMC_DATES
        return str(nd) in set(dates)
    except Exception:
        return False


def night_record(bars: list[dict], d: date, cfg=None) -> dict | None:
    """d bir KSG sinyal günüyse gölge kaydı (tamamlanmamış alanlar None, 'tam' bayrağı); değilse None."""
    sig = ks.find_signal(bars, d)
    if sig is None:
        return None
    op = _opens(bars)
    ask = sig["o16"] + SPREAD_MODEL
    nd = _next_session(op, d)
    veto, k = ks.opex_blocks(d, bool(getattr(cfg, "KSG_OPEX_VETO", True)))
    r = {"kind": "ksg_golge", "day": str(d), "nd": str(nd) if nd else None, "o15": sig["o15"], "o16": sig["o16"],
         "ret_bp": sig["ret_bp"], "ask_model": ask, "opex_veto": veto, "vadeye_gun": k, "fomc_oncesi": fomc_tomorrow(nd, cfg),
         "base_bp": None, "x930_bp": None, "p1830_bp": None, "ekleme": None, "ek_birim_bp": None,
         "kurtarma": None, "hold16_bp": None, "kurtarma_fark_bp": None, "tam": False}
    p1830 = op.get((d, ADD_MIN))
    if p1830 is not None:
        r["p1830_bp"] = round((p1830 / ask - 1) * 1e4, 2)
        r["ekleme"] = r["p1830_bp"] <= ADD_BP
    if nd is None:
        return r
    fin = FIN_BP_PER_DAY * (nd - d).days
    o930 = op[(nd, OPEN_MIN)]
    x930 = (o930 / ask - 1) * 1e4
    r |= {"x930_bp": round(x930, 2), "base_bp": round(x930 - fin, 2), "kurtarma": x930 <= RESCUE_BP}
    if r["ekleme"]:
        r["ek_birim_bp"] = round((o930 / (p1830 + SPREAD_MODEL) - 1) * 1e4 - fin, 2)
    if r["kurtarma"]:
        o16n = op.get((nd, CLOSE_MIN))
        if o16n is None:
            return r
        r["hold16_bp"] = round((o16n / ask - 1) * 1e4 - fin, 2)
        r["kurtarma_fark_bp"] = round(r["hold16_bp"] - r["base_bp"], 2)
    if r["ekleme"] is None:                 # 18:30 barı yok (Cuma kapanışı / veri boşluğu) → ekleme fırsatı yok (araştırmayla aynı)
        r["ekleme"] = False
    r["tam"] = True
    return r


# ═════════════════════════ durum + döngü ═════════════════════════

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"done": []}


def _save_state(st: dict) -> None:
    st["done"] = sorted(st.get("done", []))[-200:]
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def poll(mt5, log, resolve_symbol, offset_fn, cfg=None, now: float | None = None) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK."""
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    sym = resolve_symbol(sh.MARKET)
    if not sym:
        return
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M30, 0, FETCH_M30)
    if rates is None or len(rates) < 40:
        return
    bars = cs._m15_utc(rates, offset_fn(sym))
    today = cs.to_local(now, sh.TZ)[0]
    st = _load_state()
    done = set(st.get("done", []))
    days = sorted({cs.to_local(b["t"], sh.TZ)[0] for b in bars})
    changed = False
    for d in days:
        if str(d) in done or d >= today:
            continue
        r = night_record(bars, d, cfg)
        if r is None:
            if d < today:
                done.add(str(d))
                changed = True
            continue
        stale = (today - d).days > STALE_DAYS
        if r["tam"] or stale:
            r["durum"] = "tam" if r["tam"] else "eksik"
            _append(r)
            done.add(str(d))
            changed = True
            log.info("KSG gölge kaydı %s: base %s bp, kurtarma %s, ekleme %s, OPEX %s", d, r["base_bp"], r["kurtarma"], r["ekleme"],
                     r["opex_veto"])
    if changed:
        st["done"] = list(done)
        _save_state(st)


# ═════════════════════════ karne ═════════════════════════

def karne(path: Path = EVENTS_JSONL) -> dict:
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()] if path.exists() else []
    rows = [r for r in rows if r.get("durum") == "tam"]

    def st(v: list[float]) -> dict:
        v = sorted(x for x in v if x is not None)
        if not v:
            return {"n": 0}
        return {"n": len(v), "ort": round(sum(v) / len(v), 1), "medyan": round(v[len(v) // 2], 1),
                "en_iyi5_haric": round(sum(v[:-5]) / len(v[:-5]), 1) if len(v) > 5 else None}
    return {"gece": len(rows), "taban_canli": st([r["base_bp"] for r in rows if not r["opex_veto"]]),
            "opex_vetolu": st([r["base_bp"] for r in rows if r["opex_veto"]]),
            "kurtarma_fark": st([r["kurtarma_fark_bp"] for r in rows if r["kurtarma"]]),
            "ekleme_birim": st([r["ek_birim_bp"] for r in rows if r["ekleme"]]),
            "fomc_oncesi": st([r["base_bp"] for r in rows if r["fomc_oncesi"]]),
            "fomc_disi": st([r["base_bp"] for r in rows if not r["fomc_oncesi"]])}


if __name__ == "__main__":
    if "--karne" in sys.argv:
        print(json.dumps(karne(), indent=1, ensure_ascii=False))
