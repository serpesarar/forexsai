"""xau_rr.py — XAUUSD RR düzeltmesi: decider'ın KENDİ kararları üzerinde test.

Sorun: decider XAU'da STOP_ATR=(1.0, 2.5) kullanıyor → TP 1.0×ATR / SL 2.5×ATR,
yani RR ≈ 0.40-0.54. Başabaş WR = 2.5/(1.0+2.5) = **%71.4**. Gözlenen WR %58-63
→ yapısal olarak −EV. Geniş SL "patient WR" gereği (hafıza: dar stop XAU'yu
öldürüyor), o yüzden çözüm SL'i daraltmak değil **TP'yi uzatmak**.

Test: journal'daki gerçek OPEN kararlarının (entry_price, atr, direction, ts)
üzerinden farklı (tp_mult, sl_mult) çiftlerini 1m barlarla sızıntısız replay.
Karar anı ve ATR olduğu gibi alınır — yalnız geometri değişir.

Sızıntı: çözüm yalnız karar zamanından SONRAKİ barlarla; aynı barda TP+SL →
konservatif SL; zaman kayması düzeltmesi uygulanır; 48h sonra EXPIRE (0R).
"""
from __future__ import annotations

import bisect
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from deep_grid import _client, _page, parse_ts, drift_for, block_boot  # noqa: E402

SYMBOL = "XAUUSD"
SINCE = "2026-02-11T00:00:00+00:00"
SPREAD = 0.24            # journal'da ölçülen ortalama XAU spread'i
MAX_HORIZON_H = 48


def load():
    cache = HERE / "xau_rr_data.json"
    if cache.exists():
        d = json.loads(cache.read_text())
        return d["dec"], d["b1"]
    client = _client()
    dec = []
    for r in _page(client, "decider_journal", "ts,symbol,raw,outcome",
                   [("symbol", SYMBOL)], "ts", SINCE):
        raw = r.get("raw") or {}
        d = (raw.get("decision") or {})
        tr = raw.get("trade") or raw.get("counterfactual") or {}
        if str(d.get("action", "")).upper() != "OPEN":
            continue
        direction = d.get("direction") or tr.get("dir")
        if direction not in ("BUY", "SELL") or not tr.get("entry_price") or not tr.get("atr"):
            continue
        dec.append({"ts": int(parse_ts(r["ts"]).timestamp()),
                    "dir": direction, "px": float(tr["entry_price"]),
                    "atr": float(tr["atr"])})
    dec.sort(key=lambda x: x["ts"])
    b1, seen = [], set()
    for r in _page(client, "candle_cache", "candle_time,high,low,close",
                   [("symbol", SYMBOL), ("timeframe", "1m")], "candle_time", SINCE):
        dt = parse_ts(r["candle_time"])
        if dt.second:
            continue
        ts = int(dt.timestamp()) + drift_for(dt)
        if ts in seen:
            continue
        seen.add(ts)
        b1.append({"ts": ts, "h": float(r["high"]), "l": float(r["low"])})
    b1.sort(key=lambda b: b["ts"])
    cache.write_text(json.dumps({"dec": dec, "b1": b1}))
    return dec, b1


def run(dec, b1, k1, tp_m, sl_m):
    trades, open_until = [], 0
    for e in dec:
        if e["ts"] < open_until:
            continue                       # tek açık pozisyon
        sign = 1 if e["dir"] == "BUY" else -1
        entry = e["px"] + sign * SPREAD    # giriş aleyhte kayar
        tp_d, sl_d = tp_m * e["atr"], sl_m * e["atr"]
        tp, sl = entry + sign * tp_d, entry - sign * sl_d
        i = bisect.bisect_right(k1, e["ts"])
        deadline = e["ts"] + MAX_HORIZON_H * 3600
        res, ex = None, None
        for k in k1[i:]:
            if k > deadline:
                res, ex = 0.0, k           # EXPIRE (nötr)
                break
            b = b1[bisect.bisect_left(k1, k)]
            hit_sl = (b["l"] - SPREAD <= sl) if sign > 0 else (b["h"] + SPREAD >= sl)
            hit_tp = (b["h"] >= tp) if sign > 0 else (b["l"] <= tp)
            if hit_sl:
                res, ex = -1.0, k
                break
            if hit_tp:
                res, ex = tp_d / sl_d, k
                break
        if res is None:
            continue
        trades.append({"r": res, "ts": e["ts"], "dir": e["dir"]})
        open_until = ex
    return trades


def stat(tr):
    if not tr:
        return None
    res = [t for t in tr if t["r"] != 0.0]
    w = sum(1 for t in res if t["r"] > 0)
    return {"n": len(tr), "coz": len(res), "w": w, "l": len(res) - w,
            "wr": round(100 * w / len(res), 1) if res else 0,
            "tot": round(sum(t["r"] for t in tr), 2),
            "avg": round(statistics.mean([t["r"] for t in tr]), 3)}


def monthly_pos(tr):
    by = defaultdict(float)
    for t in tr:
        by[datetime.fromtimestamp(t["ts"], timezone.utc).strftime("%m")] += t["r"]
    return sum(1 for v in by.values() if v > 0), len(by)


def main():
    dec, b1 = load()
    k1 = [b["ts"] for b in b1]
    print(f"XAUUSD decider OPEN kararı: {len(dec)}  |  1m bar: {len(b1)}  "
          f"spread={SPREAD}\n")
    print(f"{'geometri':<26}{'RR':>6}{'başabaş':>9}{'n':>6}{'WR':>7}{'marj':>8}"
          f"{'totR':>9}{'avgR':>8}{'ay':>6}{'P(kâr)':>8}")
    print("─" * 93)
    GRID = [(1.0, 2.5), (1.5, 2.5), (2.0, 2.5), (2.5, 2.5), (3.0, 2.5),
            (1.0, 1.5), (1.5, 1.5), (2.0, 1.5), (2.0, 2.0), (2.5, 2.0), (3.0, 3.0)]
    for tp_m, sl_m in GRID:
        tr = run(dec, b1, k1, tp_m, sl_m)
        s = stat(tr)
        if not s or not s["coz"]:
            continue
        rr = tp_m / sl_m
        be = 100 * sl_m / (tp_m + sl_m)
        pos, tot_m = monthly_pos(tr)
        mark = " ← MEVCUT" if (tp_m, sl_m) == (1.0, 2.5) else ""
        print(f"TP {tp_m}×ATR / SL {sl_m}×ATR{'':<3}{rr:>6.2f}{be:>8.1f}%"
              f"{s['n']:>6}{s['wr']:>6.1f}%{s['wr'] - be:>+7.1f}pp"
              f"{s['tot']:>+9.2f}{s['avg']:>+8.3f}{pos:>4}/{tot_m}"
              f"{block_boot(tr):>7.1f}%{mark}")

    # yön kırılımı — en iyi 3
    print("\nYÖN KIRILIMI (en umutlu 3 geometri)")
    best = sorted(((tp, sl, stat(run(dec, b1, k1, tp, sl))) for tp, sl in GRID),
                  key=lambda x: -(x[2]["tot"] if x[2] else -9))[:3]
    for tp_m, sl_m, _s in best:
        tr = run(dec, b1, k1, tp_m, sl_m)
        line = f"  TP {tp_m}/SL {sl_m}:"
        for d in ("BUY", "SELL"):
            sub = [t for t in tr if t["dir"] == d]
            ss = stat(sub)
            if ss:
                line += (f"   {d} n={ss['n']:>3} WR=%{ss['wr']:<5} "
                         f"R={ss['tot']:>+7.2f}")
        print(line)


if __name__ == "__main__":
    main()
