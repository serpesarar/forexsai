"""XAU GÖLGE SCOPE'LARI — 1m replay ile karne (kutuda çalışır).

`check_shadow_scopes()` XAUUSD BUY/SELL sinyallerini kapılardan geçirip
`gate_skipped.jsonl`'e `reason="shadow_signal"` olarak yazıyor ama işlem AÇMIYOR.
Bu betik o kayıtları gerçek M1 barlarıyla çözüp "açılsaydı ne olurdu"yu ölçer.

Sızıntı garantileri:
  * Giriş = kaydın KENDİ anındaki fiyatı (karar anında yazılmış ask/bid).
  * Çözümleme yalnız karar anından SONRAKİ M1 barlarıyla; aynı barda TP+SL →
    konservatif KAYIP.
  * Geometri kayıtta yok (bot işlem açmadığı için) → birkaç aday geometri
    ızgara olarak denenir; hiçbiri "sonradan seçilmiş en iyi" diye sunulmaz.

İki okuma:
  * HAM  — her kayıt bir işlem (gölge scope 60 sn'de bir loglar → aynı piyasa
    durumu onlarca kez sayılır, ŞİŞİK; yalnız referans).
  * AS-TRADED — scope başına aynı anda tek pozisyon (botun gerçek davranışı).
    Karar bunun üzerinden verilir.

Çalıştırma: python backend/research/xau_shadow_replay.py [gün]
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import MetaTrader5 as mt5  # noqa: E402

JSONL = ROOT / "yeni deneme" / "gate_skipped.jsonl"
SERVER_OFFSET_H = 3
MAX_HOLD_MIN = 24 * 60
RNG = np.random.default_rng(31)

# aday geometriler: (ad, tp_mode, tp_val, sl_mode, sl_val)  mode: "atr" | "abs"
GEOMETRIES = [
    ("TP=SL=1.0×ATR",        "atr", 1.0, "atr", 1.0),
    ("TP=1.5×ATR SL=1.0×ATR", "atr", 1.5, "atr", 1.0),
    ("TP=1.0×ATR SL=1.5×ATR", "atr", 1.0, "atr", 1.5),
    ("TP=2.0×ATR SL=1.0×ATR", "atr", 2.0, "atr", 1.0),
    ("config önerisi TP8/SL6", "abs", 8.0, "abs", 6.0),
]
TIME_STOPS = [None, 60, 240]      # dakika; None = TP/SL'e kadar bekle


def load_records(days: int) -> list[dict]:
    if not JSONL.exists():
        raise SystemExit(f"{JSONL} yok")
    cut = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for line in JSONL.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("reason") != "shadow_signal":
            continue
        ts = datetime.fromisoformat(r["ts"].replace("Z", "+00:00"))
        if ts < cut:
            continue
        r["_ts"] = ts
        out.append(r)
    return sorted(out, key=lambda r: r["_ts"])


def bars(symbol: str, tf: int, a: datetime, b: datetime) -> np.ndarray | None:
    r = mt5.copy_rates_range(symbol, tf,
                             a + timedelta(hours=SERVER_OFFSET_H),
                             b + timedelta(hours=SERVER_OFFSET_H))
    if r is None or len(r) == 0:
        return None
    return np.array([(int(x["time"]), float(x["open"]), float(x["high"]),
                      float(x["low"]), float(x["close"])) for x in r])


def atr_at(m5: np.ndarray, ts_server: float, n: int = 14) -> float | None:
    """Karar anında KAPANMIŞ son n 5m bardan ATR (bot ile aynı: düz TR ort.)."""
    k = int(np.searchsorted(m5[:, 0], ts_server - 300, side="right"))
    if k < n + 2:
        return None
    s = m5[max(0, k - n - 1):k]
    h, l, c = s[:, 2], s[:, 3], s[:, 4]
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    return float(tr.mean()) if len(tr) else None


def race(m1: np.ndarray, ts_server: float, direction: str, entry: float,
         tp: float, sl: float, time_stop: int | None):
    """(R, dakika) — aynı barda TP+SL → KAYIP. time_stop dolarsa piyasa fiyatından çık."""
    k = int(np.searchsorted(m1[:, 0], ts_server))
    if k >= len(m1) - 2 or m1[k, 0] - ts_server > 900:
        return None
    lim = min(len(m1) - k, time_stop or MAX_HOLD_MIN)
    hi, lo, cl = m1[k:k + lim, 2], m1[k:k + lim, 3], m1[k:k + lim, 4]
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    if direction == "BUY":
        tp_hit, sl_hit = hi >= tp, lo <= sl
    else:
        tp_hit, sl_hit = lo <= tp, hi >= sl
    t_i = int(np.argmax(tp_hit)) if tp_hit.any() else 10 ** 9
    s_i = int(np.argmax(sl_hit)) if sl_hit.any() else 10 ** 9
    if s_i <= t_i and s_i < 10 ** 9:
        return -1.0, s_i + 1
    if t_i < 10 ** 9:
        return abs(tp - entry) / risk, t_i + 1
    if time_stop:                                   # süre doldu → kapanıştan çık
        last = float(cl[-1])
        r = (last - entry) if direction == "BUY" else (entry - last)
        return r / risk, lim
    return None


def stat(rows: list[tuple[float, int]]) -> str:
    if not rows:
        return "n=0"
    R = np.array([r for r, _ in rows])
    w = float((R > 0).mean() * 100)
    lo = R.mean() - 1.96 * R.std(ddof=1) / np.sqrt(len(R)) if len(R) > 2 else float("nan")
    hi = R.mean() + 1.96 * R.std(ddof=1) / np.sqrt(len(R)) if len(R) > 2 else float("nan")
    return (f"n={len(R):>4} WR={w:5.1f}% ortR={R.mean():+.3f} topR={R.sum():+7.1f} "
            f"%95=[{lo:+.3f},{hi:+.3f}]")


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    if not mt5.initialize():
        raise SystemExit(f"mt5.initialize() hata: {mt5.last_error()}")
    recs = load_records(days)
    if not recs:
        raise SystemExit("shadow_signal kaydı yok")
    syms = {r.get("mt5_symbol") for r in recs}
    print(f"kayıt: {len(recs)}  sembol: {syms}  "
          f"{recs[0]['_ts']:%Y-%m-%d} → {recs[-1]['_ts']:%Y-%m-%d}")
    by_dir = defaultdict(int)
    for r in recs:
        by_dir[r.get("direction")] += 1
    print(f"yön dağılımı: {dict(by_dir)}")

    sym = recs[0].get("mt5_symbol") or "XAUUSD"
    info = mt5.symbol_info(sym)
    spread = round(info.spread * info.point, 5) if info else 0.0
    a, b = recs[0]["_ts"] - timedelta(days=3), recs[-1]["_ts"] + timedelta(days=2)
    m5, m1 = bars(sym, mt5.TIMEFRAME_M5, a, b), bars(sym, mt5.TIMEFRAME_M1, a, b)
    if m5 is None or m1 is None:
        raise SystemExit("bar alınamadı")
    print(f"{sym}: M5={len(m5)} M1={len(m1)} spread={spread}\n")

    for gname, tmode, tval, smode, sval in GEOMETRIES:
        for tstop in TIME_STOPS:
            ham, taken = defaultdict(list), defaultdict(list)
            busy = defaultdict(float)                # scope → serbest kalma zamanı
            for r in recs:
                d = r["direction"]
                ts_s = r["_ts"].timestamp() + SERVER_OFFSET_H * 3600
                entry = float(r["price"])
                if tmode == "atr":
                    atr = atr_at(m5, ts_s)
                    if not atr:
                        continue
                    tp_d, sl_d = tval * atr, sval * atr
                else:
                    tp_d, sl_d = tval, sval
                tp = entry + tp_d if d == "BUY" else entry - tp_d
                sl = entry - sl_d if d == "BUY" else entry + sl_d
                res = race(m1, ts_s, d, entry, tp, sl, tstop)
                if res is None:
                    continue
                ham[d].append(res)
                if ts_s >= busy[d]:                  # as-traded: tek pozisyon
                    taken[d].append(res)
                    busy[d] = ts_s + res[1] * 60
            allham = ham["BUY"] + ham["SELL"]
            alltak = taken["BUY"] + taken["SELL"]
            ts_txt = "TP/SL" if tstop is None else f"{tstop}dk stop"
            print(f"[{gname:<24} · {ts_txt:<9}]")
            print(f"   HAM        {stat(allham)}")
            print(f"   AS-TRADED  {stat(alltak)}")
            for d in ("BUY", "SELL"):
                if taken[d]:
                    print(f"     {d:<4}     {stat(taken[d])}")
        print()
    print("BITTI")


if __name__ == "__main__":
    main()
