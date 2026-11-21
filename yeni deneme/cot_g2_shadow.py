"""cot_g2_shadow.py — COT-G2 kesitsel kalabalık dönüşü GÖLGE kaydı (FX-YI EK-23, sınıf C).

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ. Yalnız sanal giriş/çıkışı `cot_g2_shadow.jsonl`'e yazar.
Hatalar bot akışını etkilemez (çağıran try/except içinde kullanır).

KANIT: research/fx_yuksek_isabet_20261120/PROTOCOL.md EK-23/23b/23c, defter §2.108 YI-27.
  TFF 2010–17 n 283 %82,7 +5,7 bp · 2018–26 n 337 %85,5 +11,3 bp (P 0,998, ayda 3,2) · AMA TFF 2007–10 −40 bp (2008 −104),
  legacy 1993–2009 −15,6 → SINIF C, canlıya uygun DEĞİL. Bu kayıt yalnız ileri (görülmemiş) kanıt toplar.

KURAL (dondurulmuş; değiştirmek kanıtı geçersiz kılar):
  CFTC TFF (yalnız vadeli) haftalık rapor, Salı pozisyonu, Cuma 15:30 ET yayını. 7 para birimi (EUR GBP JPY AUD CAD CHF NZD),
  kaldıraçlı fon net / açık pozisyon; z = (son değer − önceki 52 haftanın ort.) / std (en az 40 hafta). USD = 0.
  z_maks − z_min ≥ 2 → en uzun-kalabalık para birimini SAT, en kısa-kalabalığı AL. Çapraz çift listedeyse o çift, değilse
  |z|'si büyük olan para birimi USD karşısında. Giriş: yayın Cuma'sından sonraki ilk D1 barının açılışı.
  TP 0,5 × ATR20(D1, Cuma barı dahil), SL 3 × ATR20, en çok 10 D1 bar (giriş barı dahil; son barın kapanışında çık);
  aynı barda TP ve SL → SL. Çift başına aynı anda tek sanal pozisyon.

Karne:   python cot_g2_shadow.py --karne
Kapatma: config.COT_G2_SHADOW_ENABLED = False
"""
from __future__ import annotations

import csv
import io
import json
import math
import sys
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "cot_g2_shadow.jsonl"
STATE_FILE = HERE / "cot_g2_state.json"
CACHE_DIR = HERE / "cot_cache"
URL = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"

CODES = {"099741": "EUR", "096742": "GBP", "097741": "JPY", "232741": "AUD", "090741": "CAD", "092741": "CHF", "112741": "NZD"}
USD_PAIR = {"EUR": ("EURUSD", 1), "GBP": ("GBPUSD", 1), "AUD": ("AUDUSD", 1), "NZD": ("NZDUSD", 1),
            "JPY": ("USDJPY", -1), "CAD": ("USDCAD", -1), "CHF": ("USDCHF", -1)}
PAIRS = {"AUDCAD", "AUDJPY", "AUDNZD", "AUDUSD", "CADJPY", "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY",
         "EURUSD", "GBPAUD", "GBPCHF", "GBPJPY", "GBPUSD", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"}
COST_BP = {"EURUSD": 0.80, "GBPUSD": 0.85, "USDJPY": 0.95, "USDCHF": 1.05, "USDCAD": 1.00, "AUDUSD": 1.45, "NZDUSD": 1.6}
DEFAULT_COST_BP = 2.0
Z_WIN, Z_MIN = 52, 40
SPREAD_MIN = 2.0
TP_ATR, SL_ATR, HOLD_BARS, ATR_N = 0.5, 3.0, 10, 20
CHECK_EVERY_S = 900
RELEASE_LAG_DAYS = 3          # Salı → Cuma
RELEASE_READY_UTC_H = 21      # Cuma 15:30 ET yayını; 21:00 UTC sonrası güvenli (yaz/kış)
_last_check = 0.0


# ═════════════════════════ saf mantık (mt5/ağ olmadan test edilir) ═════════════════════════

def parse_tff(text: str) -> dict[str, dict[date, float]]:
    """TFF metin dosyası → {para birimi: {rapor tarihi: kaldıraçlı fon net / OI}}."""
    out: dict[str, dict[date, float]] = {c: {} for c in CODES.values()}
    for r in csv.DictReader(io.StringIO(text)):
        code = (r.get("CFTC_Contract_Market_Code") or "").strip()
        if code not in CODES:
            continue
        try:
            d = datetime.strptime(str(int(float(r["As_of_Date_In_Form_YYMMDD"]))).zfill(6), "%y%m%d").date()
            oi = float(r["Open_Interest_All"])
            v = (float(r["Lev_Money_Positions_Long_All"]) - float(r["Lev_Money_Positions_Short_All"])) / oi
        except (KeyError, ValueError, ZeroDivisionError):
            continue
        out[CODES[code]][d] = v
    return out


def zscore_last(series: dict[date, float], rep: date) -> float | None:
    """rep tarihindeki değerin önceki Z_WIN haftaya göre z'si (rep hariç). Yetersiz geçmiş → None."""
    if rep not in series:
        return None
    prev = [series[d] for d in sorted(series) if d < rep][-Z_WIN:]
    if len(prev) < Z_MIN:
        return None
    mu = sum(prev) / len(prev)
    sd = math.sqrt(sum((x - mu) ** 2 for x in prev) / (len(prev) - 1))
    return (series[rep] - mu) / sd if sd > 0 else None


def select(z: dict[str, float]) -> tuple[str, int, str, str] | None:
    """z: {para birimi: z} (USD dahil edilmez; 0 kabul edilir). → (çift, yön, güçlü-kalabalık, zayıf-kalabalık) veya None."""
    zz = {k: v for k, v in z.items() if v is not None and not math.isnan(v)}
    if len(zz) < 5:
        return None
    zz["USD"] = 0.0
    hi = max(zz, key=lambda k: zz[k])
    lo = min(zz, key=lambda k: zz[k])
    if zz[hi] - zz[lo] < SPREAD_MIN:
        return None
    if hi + lo in PAIRS:
        return hi + lo, -1, hi, lo
    if lo + hi in PAIRS:
        return lo + hi, 1, hi, lo
    k = hi if abs(zz[hi]) >= abs(zz[lo]) else lo
    pair, s = USD_PAIR[k]
    return pair, (-s if k == hi else s), hi, lo


def atr(bars: list[dict], n: int = ATR_N) -> float | None:
    """bars: eskiden yeniye D1 ({'o','h','l','c'}); son barı dahil eden n'lik ortalama gerçek aralık."""
    if len(bars) < n + 1:
        return None
    tr = []
    for i in range(len(bars) - n, len(bars)):
        pc = bars[i - 1]["c"]
        b = bars[i]
        tr.append(max(b["h"] - b["l"], abs(b["h"] - pc), abs(b["l"] - pc)))
    return sum(tr) / n


def resolve(pos: dict, bars_after: list[dict]) -> dict | None:
    """Giriş barından itibaren D1 barları (giriş barı dahil). Sonuç hazırsa çıkış kaydı, değilse None."""
    up = pos["E"] + (pos["tp"] if pos["side"] > 0 else pos["sl"])
    dn = pos["E"] - (pos["sl"] if pos["side"] > 0 else pos["tp"])
    for i, b in enumerate(bars_after[:HOLD_BARS]):
        hu, hd = b["h"] >= up, b["l"] <= dn
        if hu or hd:
            if pos["side"] > 0:
                x, why = (dn, "SL") if hd else (up, "TP")
            else:
                x, why = (up, "SL") if hu else (dn, "TP")
            return {"X": x, "why": why, "bars": i + 1}
    if len(bars_after) >= HOLD_BARS:
        return {"X": bars_after[HOLD_BARS - 1]["c"], "why": "ZAMAN", "bars": HOLD_BARS}
    return None


def bp(side: int, e: float, x: float, cost: float) -> float:
    return round(side * (x / e - 1) * 1e4 - cost, 2)


def release_due(rep: date, now: float) -> bool:
    fri = rep + timedelta(days=RELEASE_LAG_DAYS)
    ready = datetime(fri.year, fri.month, fri.day, RELEASE_READY_UTC_H, tzinfo=timezone.utc).timestamp()
    return now >= ready


def summarize(recs: list[dict]) -> dict:
    res = [r for r in recs if r.get("kind") == "result"]
    if not res:
        return {"n": 0, "sinyal": sum(r.get("kind") == "signal" for r in recs)}
    v = [r["bp_model"] for r in res]
    return {"n": len(v), "isabet": round(100 * sum(x > 0 for x in v) / len(v), 1), "ort_bp": round(sum(v) / len(v), 2),
            "toplam_bp": round(sum(v), 1), "en_kotu": min(v), "kanit_kart": "KÖR %85,5 / +11,3 bp (2018–26)"}


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st.setdefault("pos", [])        # sanal pozisyonlar (bekleyen giriş dahil)
    st.setdefault("done", [])       # işlenmiş rapor tarihleri
    return st


def _save_state(st: dict) -> None:
    st["done"] = st["done"][-200:]
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ═════════════════════════ ağ + MT5 adaptörü ═════════════════════════

def _tff_text(year: int, force: bool) -> str:
    CACHE_DIR.mkdir(exist_ok=True)
    f = CACHE_DIR / f"fut_fin_txt_{year}.zip"
    if force or not f.exists() or time.time() - f.stat().st_mtime > 6 * 3600:
        import requests
        r = requests.get(URL.format(year=year), timeout=60)
        r.raise_for_status()
        f.write_bytes(r.content)
    with zipfile.ZipFile(f) as z:
        return z.read(z.namelist()[0]).decode("utf-8", errors="replace")


def _series(now: float) -> dict[str, dict[date, float]]:
    y = datetime.fromtimestamp(now, timezone.utc).year
    out: dict[str, dict[date, float]] = {c: {} for c in CODES.values()}
    for yy in (y - 1, y):
        try:
            part = parse_tff(_tff_text(yy, force=(yy == y)))
        except Exception:
            if yy == y:
                raise
            continue
        for c, s in part.items():
            out[c].update(s)
    return out


def _d1(mt5, sym: str, n: int = 40) -> list[dict]:
    mt5.symbol_select(sym, True)
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, n)
    if r is None:
        return []
    return [{"d": datetime.fromtimestamp(int(x["time"]), timezone.utc).date(), "o": float(x["open"]), "h": float(x["high"]),
             "l": float(x["low"]), "c": float(x["close"])} for x in r]


def _new_signal(st: dict, mt5, log, now: float) -> bool:
    S = _series(now)
    reps = sorted(set().union(*[set(s) for s in S.values()]))
    if not reps:
        return False
    rep = reps[-1]
    key = rep.isoformat()
    if key in st["done"] or not release_due(rep, now):
        return False
    z = {c: zscore_last(S[c], rep) for c in CODES.values()}
    sel = select(z)
    st["done"].append(key)
    zr = {k: (round(v, 2) if v is not None else None) for k, v in z.items()}
    if sel is None:
        _append({"kind": "skip", "rep": key, "z": zr, "why": "uc_fark_kucuk"})
        log.info("COT-G2-GÖLGE %s sinyal yok (uç fark < %.1f) (EMİR YOK)", key, SPREAD_MIN)
        return True
    pair, side, hi, lo = sel
    if any(p["sym"] == pair for p in st["pos"]):
        _append({"kind": "skip", "rep": key, "z": zr, "sym": pair, "why": "cift_mesgul"})
        return True
    fri = rep + timedelta(days=RELEASE_LAG_DAYS)
    p = {"rep": key, "sym": pair, "side": side, "hi": hi, "lo": lo, "fri": fri.isoformat(), "E": None, "z": zr}
    st["pos"].append(p)
    _append({"kind": "signal", **p})
    log.info("COT-G2-GÖLGE %s %s %s (kalabalık uzun %s / kısa %s) — giriş Pazartesi açılışı (EMİR YOK)",
             key, "AL" if side > 0 else "SAT", pair, hi, lo)
    return True


def _manage(st: dict, mt5, log) -> bool:
    changed, keep = False, []
    for p in st["pos"]:
        bars = _d1(mt5, p["sym"])
        fri = date.fromisoformat(p["fri"])
        upto = [b for b in bars if b["d"] <= fri]
        after = [b for b in bars if b["d"] > fri]
        if p["E"] is None:
            a = atr(upto)
            if not after or a is None:
                keep.append(p)
                continue
            p["E"], p["tp"], p["sl"], p["entry_d"] = after[0]["o"], TP_ATR * a, SL_ATR * a, after[0]["d"].isoformat()
            _append({"kind": "entry", "rep": p["rep"], "sym": p["sym"], "side": p["side"], "E": p["E"], "tp": p["tp"], "sl": p["sl"]})
            changed = True
        closed = [b for b in after if b["d"] < datetime.now(timezone.utc).date()]   # yalnız kapanmış barlar
        r = resolve(p, closed)
        if r is None:
            keep.append(p)
            continue
        rec = {"kind": "result", "rep": p["rep"], "sym": p["sym"], "side": p["side"], "E": p["E"], **r,
               "bp_model": bp(p["side"], p["E"], r["X"], COST_BP.get(p["sym"], DEFAULT_COST_BP))}
        _append(rec)
        log.info("COT-G2-GÖLGE çıkış %s %s %s: %.2f bp (EMİR YOK)", p["rep"], p["sym"], r["why"], rec["bp_model"])
        changed = True
    st["pos"] = keep
    return changed


def poll(mt5, log, cfg=None, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden çağrılır; 15 dk'da bir iş yapar. EMİR YOK. Hata → çağıran yakalar."""
    global _last_check
    now = time.time() if now is None else now
    if not force and now - _last_check < CHECK_EVERY_S:
        return
    _last_check = now
    st = _load_state()
    changed = False
    wd = datetime.fromtimestamp(now, timezone.utc).weekday()
    if wd in (4, 5, 6, 0):          # Cuma akşamı → Pazartesi arası yeni rapor ara
        try:
            changed |= _new_signal(st, mt5, log, now)
        except Exception as e:
            log.warning("COT-G2-GÖLGE: CFTC raporu okunamadı: %s", e)
    if st["pos"]:
        changed |= _manage(st, mt5, log)
    if changed:
        _save_state(st)


def _karne() -> None:
    recs = []
    if EVENTS_JSONL.exists():
        recs = [json.loads(x) for x in EVENTS_JSONL.read_text(encoding="utf-8").splitlines() if x.strip()]
    print(json.dumps(summarize(recs), ensure_ascii=False, indent=1))


if __name__ == "__main__" and "--karne" in sys.argv:
    _karne()
