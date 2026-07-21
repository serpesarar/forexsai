"""Çok-sembol işlem-yönetimi çalışması + tarih-dilimi (walk-forward) doğrulama.

Her sembol için AYNI sızıntısız pipeline:
  veri: MT5 deal CSV (A kohortu, [tp/sl X] comment'li) + positions.json (B) +
        1m barlar (paket CSV + candle_cache :00-hizalı, 07-21'e kadar uzatılmış)
  testler: baseline · BE@15/30/45 · kazananı-koştur (trail 0.4/0.6/0.8) ·
           KOMBO (BE30+trail0.6) · 10dk sabır kapısı — hepsi yön-kırılımlı
  doğrulama: haftalık tarih dilimlerinde Δ tutarlılığı (parametre füzü YOK —
             NDX'te seçilen sabit parametreler tüm sembollere olduğu gibi
             uygulanır; sembol başına ayar = overfit).

NDX için bu, Aşama-2/3 bulgusunun DİLİM-BAZLI sağlamasıdır.
"""
from __future__ import annotations

import bisect
import csv
import json
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PKG = ROOT / "analiz_paketi_2026-07-09"
sys.path.insert(0, str(ROOT / "backend"))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env"); load_dotenv(ROOT / ".env")
except ImportError:
    pass

random.seed(17)
MAX_BARS = 3 * 1440

SYMBOLS = {
    "NDX.INDX":    {"broker": "NAS100",    "pkg_csv": "NDX_INDX_1m_son_14gun.csv"},
    "GDAXI.INDX":  {"broker": "GER40",     "pkg_csv": "GDAXI_INDX_1m_son_14gun.csv"},
    "XAUUSD":      {"broker": "XAUUSD",    "pkg_csv": "XAUUSD_1m_son_14gun.csv"},
    "USOIL.FOREX": {"broker": "SpotCrude", "pkg_csv": "USOIL_FOREX_1m_son_14gun.csv"},
}


def parse_ts(text: str) -> int:
    t = text.strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    dt = datetime.fromisoformat(t)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


# ─── Veri kurulumu (build_dataset mantığının sembol-parametrik hali) ─────────

def build_trades(symbol: str) -> list[dict]:
    broker = SYMBOLS[symbol]["broker"]
    trades: list[dict] = []
    rows = list(csv.DictReader(open(PKG / "trades" / "mt5_deals_son_14gun.csv")))
    by_pos: dict[str, dict] = defaultdict(dict)
    for r in rows:
        if r["symbol"] != broker:
            continue
        by_pos[r["position_id"]]["in" if r["entry"] == "IN" else "out"] = r
    for pid, pair in by_pos.items():
        if "in" not in pair or "out" not in pair:
            continue
        i, o = pair["in"], pair["out"]
        c = o["comment"].strip()
        reason = "tp" if c.startswith("[tp") else ("sl" if c.startswith("[sl") else "other")
        trades.append({"cohort": "A", "pid": f"A{pid}",
                       "direction": "BUY" if i["type"] == "BUY" else "SELL",
                       "entry_time": i["time_utc"], "entry_px": float(i["price"]),
                       "close_reason": reason,
                       "trig_level": float(o["price"]) if reason != "other" else None})
    for p in json.load(open(ROOT / "bot_live_audit" / "positions.json")):
        if p.get("symbol") != symbol or p.get("close_reason") not in ("tp", "sl"):
            continue
        trades.append({"cohort": "B", "pid": f"B{p['pid']}",
                       "direction": p["direction"],
                       "entry_time": p["entry_time"] + "+00:00",
                       "entry_px": float(p["entry_px"]),
                       "close_reason": p["close_reason"],
                       "trig_level": float(p["level"]) if p.get("level") else None})

    # geometri: tetiklenen mesafelerin medyanıyla bilinmeyen tarafı doldur
    # Aşama-1 (build_dataset.fill_geometry) ile BİREBİR aynı kural: medyan
    # anahtarı (kohort, yön, taraf); belirsiz-geometri işlemler DAHİL (NDX
    # Aşama-2/3 bulguları bu kümede hesaplandı — tutarlılık şart).
    dists: dict[tuple, list[float]] = defaultdict(list)
    for t in trades:
        if t["trig_level"] is not None:
            dists[(t["cohort"], t["direction"], t["close_reason"])].append(
                abs(t["trig_level"] - t["entry_px"]))
    med = {k: statistics.median(v) for k, v in dists.items() if len(v) >= 3}

    def lookup(cohort, direction, side):
        for key in ((cohort, direction, side), (cohort, "BUY", side),
                    (cohort, "SELL", side)):
            if key in med:
                return med[key]
        pooled = [d for (c, _d, s), v in dists.items() if s == side for d in v]
        return statistics.median(pooled) if pooled else None

    out = []
    for t in trades:
        if t["trig_level"] is None:
            continue
        e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
        trig_d = abs(t["trig_level"] - e)
        if t["close_reason"] == "tp":
            tp_d, sl_d = trig_d, lookup(t["cohort"], t["direction"], "sl")
        else:
            sl_d, tp_d = trig_d, lookup(t["cohort"], t["direction"], "tp")
        if not tp_d or not sl_d:
            continue
        t.update({"tp_dist": tp_d, "sl_dist": sl_d,
                  "tp_px": e + sign * tp_d, "sl_px": e - sign * sl_d})
        out.append(t)
    return out


def build_bars(symbol: str) -> tuple[dict[int, dict], list[int]]:
    cache = HERE / f"bars_{SYMBOLS[symbol]['broker']}.csv"
    bars: dict[int, dict] = {}
    if cache.exists():
        with open(cache) as f:
            for r in csv.DictReader(f):
                bars[int(r["ts"])] = {"o": float(r["open"]), "h": float(r["high"]),
                                      "l": float(r["low"]), "c": float(r["close"])}
        return bars, sorted(bars)
    with open(PKG / "prices" / SYMBOLS[symbol]["pkg_csv"]) as f:
        for r in csv.DictReader(f):
            ts = parse_ts(r["time_utc"])
            bars[ts] = {"o": float(r["open"]), "h": float(r["high"]),
                        "l": float(r["low"]), "c": float(r["close"])}
    from database.supabase_client import get_supabase_client
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase yok")
    cursor = "2026-06-14T00:00:00+00:00"
    while True:
        res = (client.table("candle_cache").select("candle_time,open,high,low,close")
               .eq("symbol", symbol).eq("timeframe", "1m")
               .gte("candle_time", cursor).lt("candle_time", "2026-07-22T00:00:00+00:00")
               .order("candle_time").limit(1000).execute())
        if res.get("error"):
            raise RuntimeError(res["error"])
        chunk = res.get("data") or []
        if not chunk:
            break
        for r in chunk:
            ts = parse_ts(r["candle_time"])
            if ts % 60 != 0:
                continue
            bars.setdefault(ts, {"o": float(r["open"]), "h": float(r["high"]),
                                 "l": float(r["low"]), "c": float(r["close"])})
        from datetime import timedelta
        cursor = (datetime.fromisoformat(chunk[-1]["candle_time"].replace("Z", "+00:00"))
                  + timedelta(seconds=1)).isoformat()
        if len(chunk) < 1000:
            break
    with open(cache, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "open", "high", "low", "close"])
        for ts in sorted(bars):
            b = bars[ts]
            w.writerow([ts, b["o"], b["h"], b["l"], b["c"]])
    return bars, sorted(bars)


# ─── Replay çekirdeği (aynı dürüstlük sözleşmesi) ────────────────────────────

def seq_for(t, bars, keys):
    entry_bar = (parse_ts(t["entry_time"]) // 60) * 60
    i = bisect.bisect_right(keys, entry_bar)
    return [(k, bars[k]) for k in keys[i:i + MAX_BARS]]


def base_path(t, seq):
    sign = 1 if t["direction"] == "BUY" else -1
    for idx, (ts, b) in enumerate(seq):
        hit_sl = (b["l"] <= t["sl_px"]) if sign > 0 else (b["h"] >= t["sl_px"])
        hit_tp = (b["h"] >= t["tp_px"]) if sign > 0 else (b["l"] <= t["tp_px"])
        if hit_sl:
            return "sl", idx
        if hit_tp:
            return "tp", idx
    return "open", len(seq)


def base_r(t, seq):
    out, _ = base_path(t, seq)
    return t["tp_dist"] / t["sl_dist"] if out == "tp" else (-1.0 if out == "sl" else 0.0)


def be_after_r(t, seq, thr):
    e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
    sl = t["sl_px"]
    for m, (ts, b) in enumerate(seq, 1):
        if ((b["l"] <= sl) if sign > 0 else (b["h"] >= sl)):
            return sign * (sl - e) / t["sl_dist"]
        if ((b["h"] >= t["tp_px"]) if sign > 0 else (b["l"] <= t["tp_px"])):
            return t["tp_dist"] / t["sl_dist"]
        if m >= thr and sign * (b["c"] - e) > 0 and sign * (e - sl) > 0:
            sl = e
    return 0.0


def combo_r(t, seq, be=30, trail=0.6):
    """BE@be dk + TP'de çıkmayıp trail×sl_dist iz süren SL ile koşturma."""
    e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
    sl, tp = t["sl_px"], t["tp_px"]
    running = False
    for m, (ts, b) in enumerate(seq, 1):
        if ((b["l"] <= sl) if sign > 0 else (b["h"] >= sl)):
            return sign * (sl - e) / t["sl_dist"]
        if not running and ((b["h"] >= tp) if sign > 0 else (b["l"] <= tp)):
            running = True
            sl = tp - sign * trail * t["sl_dist"]
            continue
        if running:
            new = b["c"] - sign * trail * t["sl_dist"]
            if sign * (new - sl) > 0:
                sl = new
        elif m >= be and sign * (b["c"] - e) > 0 and sign * (e - sl) > 0:
            sl = e
    return sign * (sl - e) / t["sl_dist"] if running else (
        sign * (seq[-1][1]["c"] - e) / t["sl_dist"] if seq else 0.0)


def patience_r(t, seq, wait=10, floor=-0.3):
    """Sinyalden wait dk sonra teyitli giriş; 0.0 = atlandı."""
    if len(seq) <= wait:
        return None
    out0, _ = base_path(t, seq[:wait])
    if out0 in ("sl", "tp"):
        return 0.0
    e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
    c = seq[wait - 1][1]["c"]
    if sign * (c - e) / t["sl_dist"] <= floor:
        return 0.0
    t2 = {**t, "entry_px": c, "tp_px": c + sign * t["tp_dist"],
          "sl_px": c - sign * t["sl_dist"]}
    out2, _ = base_path(t2, seq[wait:])
    return (t["tp_dist"] / t["sl_dist"] if out2 == "tp"
            else -1.0 if out2 == "sl" else 0.0)


def boot(deltas, iters=4000):
    n = len(deltas)
    if n == 0:
        return None
    s = sorted(sum(deltas[random.randrange(n)] for _ in range(n)) for _ in range(iters))
    return {"p05": round(s[int(.05 * iters)], 1), "p50": round(s[iters // 2], 1),
            "p95": round(s[int(.95 * iters)], 1),
            "p_pos": round(100 * sum(1 for x in s if x > 0) / iters, 1)}


def week_of(t) -> str:
    dt = datetime.fromtimestamp(parse_ts(t["entry_time"]), tz=timezone.utc)
    return f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"


def study(symbol: str) -> dict:
    trades = build_trades(symbol)
    bars, keys = build_bars(symbol)
    seqs = {t["pid"]: seq_for(t, bars, keys) for t in trades}
    trades = [t for t in trades if len(seqs[t["pid"]]) >= 5]
    rep: dict = {"symbol": symbol, "n": len(trades)}

    for d in ("BUY", "SELL"):
        sub = [t for t in trades if t["direction"] == d]
        if len(sub) < 8:
            rep[d] = {"n": len(sub), "note": "örneklem çok küçük"}
            continue
        rb = [base_r(t, seqs[t["pid"]]) for t in sub]
        block = {"n": len(sub), "baseline_tot": round(sum(rb), 2)}
        for name, fn in [("be15", lambda t, s: be_after_r(t, s, 15)),
                         ("be30", lambda t, s: be_after_r(t, s, 30)),
                         ("be45", lambda t, s: be_after_r(t, s, 45)),
                         ("run04", lambda t, s: combo_r(t, s, be=10 ** 9, trail=0.4)),
                         ("run06", lambda t, s: combo_r(t, s, be=10 ** 9, trail=0.6)),
                         ("run08", lambda t, s: combo_r(t, s, be=10 ** 9, trail=0.8)),
                         ("combo", lambda t, s: combo_r(t, s, 30, 0.6))]:
            rs = [fn(t, seqs[t["pid"]]) for t in sub]
            deltas = [a - b for a, b in zip(rs, rb)]
            block[name] = {"tot": round(sum(rs), 2), "delta": round(sum(deltas), 2),
                           "boot": boot(deltas)}
        # sabır kapısı
        pr = [(patience_r(t, seqs[t["pid"]]), b) for t, b in zip(sub, rb)]
        pr = [(a, b) for a, b in pr if a is not None]
        block["patience10"] = {"tot": round(sum(a for a, _ in pr), 2),
                               "delta": round(sum(a - b for a, b in pr), 2),
                               "girilen": sum(1 for a, _ in pr if a != 0.0)}
        # tarih dilimleri: haftalık kombo Δ
        weekly = defaultdict(list)
        for t, b in zip(sub, rb):
            weekly[week_of(t)].append(combo_r(t, seqs[t["pid"]], 30, 0.6) - b)
        block["combo_weekly_delta"] = {w: {"n": len(v), "delta": round(sum(v), 2)}
                                       for w, v in sorted(weekly.items())}
        rep[d] = block
    return rep


def main():
    out = {}
    for sym in SYMBOLS:
        print(f"\n══════ {sym} ══════")
        rep = study(sym)
        out[sym] = rep
        for d in ("BUY", "SELL"):
            b = rep.get(d)
            if not b or "note" in b:
                print(f"  {d}: {b}")
                continue
            print(f"  {d} n={b['n']} base={b['baseline_tot']}")
            for k in ("be15", "be30", "be45", "run04", "run06", "run08", "combo"):
                v = b[k]
                bo = v["boot"]
                print(f"    {k:<7} tot={v['tot']:>8} Δ={v['delta']:>7}  "
                      f"[{bo['p05']},{bo['p95']}] P(+)={bo['p_pos']}%")
            p = b["patience10"]
            print(f"    patience10 tot={p['tot']} Δ={p['delta']} girilen={p['girilen']}/{b['n']}")
            print(f"    haftalık kombo Δ: "
                  + " ".join(f"{w}:{v['delta']}" for w, v in b["combo_weekly_delta"].items()))
    json.dump(out, open(HERE / "results_multi_symbol.json", "w"), indent=1)


if __name__ == "__main__":
    main()
