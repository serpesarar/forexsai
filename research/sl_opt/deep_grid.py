"""deep_grid.py — NDX SELL, 5.5 AYLIK derin ATR geometri ızgarası.

Kullanıcı isteği: "daha geçmişe git, ATR SL ile test et, ayrıca TP'yi de
ATR'ye bağlarsak kâr eder miyiz ölç."

KAPSAM: 2026-02-11 → 07-29 (1m barın başladığı tarih; ~8.100 SELL sinyali).
Önceki çalışma yalnız 13 gündü — bu 12 kat daha uzun.

⚠️ ZAMAN DAMGASI DÜZELTMESİ (zorunlu):
`candle_cache` barları broker sunucu saatiyle etiketlenmişti; sinyaller
gerçek UTC. Düzeltme (research/ndx_buy_lab/fix_time.py ile aynı tablo):
    < 2026-03-08         : bar_ts − 120 dk
    2026-03-08 → 07-16   : bar_ts − 180 dk
    ≥ 2026-07-16         : 0
Bu uygulanmazsa işlem sinyalden 2-3 saat ÖNCE açılmış olur (sızıntı imzası).

IZGARA: TP ∈ {0.75…3.0}×ATR  ×  SL ∈ {1.0…4.0}×ATR (+ sabit referanslar)
DOĞRULAMA: aylık dilim dayanıklılığı + kronolojik %60/%40 + blok bootstrap.
Sürtünme 1.3 puan. Aynı barda TP+SL → konservatif SL (her varyantta aynı).
"""
from __future__ import annotations

import argparse
import bisect
import json
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

random.seed(11)
SYMBOL = "NDX.INDX"
SINCE = "2026-02-11T00:00:00+00:00"
FRICTION = 1.3
MAX_HOLD_BARS = 2880
ATR_N = 14

# bar zaman damgası → gerçek UTC (saniye cinsinden eklenecek düzeltme)
DRIFT = [(datetime(2026, 3, 8, tzinfo=timezone.utc), -120 * 60),
         (datetime(2026, 7, 16, tzinfo=timezone.utc), -180 * 60),
         (datetime(2100, 1, 1, tzinfo=timezone.utc), 0)]


def drift_for(dt: datetime) -> int:
    for edge, off in DRIFT:
        if dt < edge:
            return off
    return 0


def parse_ts(t: str) -> datetime:
    t = t.replace("Z", "+00:00")
    d = datetime.fromisoformat(t)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _client():
    from database.supabase_client import get_supabase_client
    c = get_supabase_client()
    if c is None:
        sys.exit("Supabase erişilemedi")
    return c


def _page(client, table, select, filters, tcol, since):
    out, cursor = [], since
    while True:
        q = client.table(table).select(select)
        for f in filters:
            q = q.eq(*f)
        res = q.gte(tcol, cursor).order(tcol).limit(1000).execute()
        if res.get("error"):
            raise RuntimeError(res["error"])
        chunk = res.get("data") or []
        if not chunk:
            break
        out.extend(chunk)
        cursor = (parse_ts(chunk[-1][tcol]) + timedelta(microseconds=1)).isoformat()
        if len(chunk) < 1000:
            break
    return out


def load(client):
    cache = HERE / "deep_data.json"
    if cache.exists():
        d = json.loads(cache.read_text())
        return d["sigs"], d["b1"], d["b5"]
    sigs = []
    for m in ("pulse1", "pulse2", "pulse3"):
        for r in _page(client, "prediction_logs", "created_at,ml_direction",
                       [("symbol", SYMBOL), ("model_type", m)], "created_at", SINCE):
            if (r.get("ml_direction") or "").upper() == "SELL":
                sigs.append({"ts": int(parse_ts(r["created_at"]).timestamp()), "model": m})
    sigs.sort(key=lambda x: x["ts"])

    def bars(tf):
        out, seen = [], set()
        for r in _page(client, "candle_cache", "candle_time,high,low,close",
                       [("symbol", SYMBOL), ("timeframe", tf)], "candle_time", SINCE):
            dt = parse_ts(r["candle_time"])
            if tf == "1m" and dt.second:
                continue
            ts = int(dt.timestamp()) + drift_for(dt)      # ← DÜZELTME
            if ts in seen:
                continue
            seen.add(ts)
            out.append({"ts": ts, "h": float(r["high"]), "l": float(r["low"]),
                        "c": float(r["close"])})
        out.sort(key=lambda b: b["ts"])
        return out

    b1, b5 = bars("1m"), bars("5m")
    cache.write_text(json.dumps({"sigs": sigs, "b1": b1, "b5": b5}))
    return sigs, b1, b5


class Ctx:
    def __init__(self, b1, b5):
        self.b1, self.b5 = b1, b5
        self.k1 = [b["ts"] for b in b1]
        self.k5 = [b["ts"] for b in b5]

    def price_at(self, ts):
        i = bisect.bisect_right(self.k1, ts)
        return self.b1[i - 1]["c"] if i else None

    def atr5(self, ts):
        i = bisect.bisect_right(self.k5, ts)
        win = self.b5[max(0, i - ATR_N - 1):i]
        if len(win) < ATR_N + 1:
            return None
        trs = [max(win[j]["h"] - win[j]["l"], abs(win[j]["h"] - win[j - 1]["c"]),
                   abs(win[j]["l"] - win[j - 1]["c"])) for j in range(1, len(win))]
        return sum(trs) / len(trs)

    def resolve_sell(self, ts, entry, tp_d, sl_d):
        e = entry - FRICTION
        tp, sl = e - tp_d, e + sl_d
        i = bisect.bisect_right(self.k1, ts)
        for k in self.k1[i:i + MAX_HOLD_BARS]:
            b = self.b1[bisect.bisect_left(self.k1, k)]
            if b["h"] + FRICTION >= sl:
                return -1.0, k
            if b["l"] <= tp:
                return tp_d / sl_d, k
        return None, None


def build_events(sigs, ctx):
    out = []
    for s in sigs:
        px = ctx.price_at(s["ts"])
        atr = ctx.atr5(s["ts"])
        if px and atr:
            out.append({"ts": s["ts"], "px": px, "atr": atr})
    return out


def run(events, ctx, tp_m=None, sl_m=None, tp_fix=None, sl_fix=None):
    """Scope başına tek pozisyon; TP/SL ya ATR-çarpanı ya sabit puan."""
    trades, open_until = [], 0
    for e in events:
        if e["ts"] < open_until:
            continue
        tp = tp_fix if tp_fix else tp_m * e["atr"]
        sl = sl_fix if sl_fix else sl_m * e["atr"]
        if tp <= 0 or sl <= 0:
            continue
        r, ex = ctx.resolve_sell(e["ts"], e["px"], tp, sl)
        if r is None:
            continue
        trades.append({"r": r, "ts": e["ts"]})
        open_until = ex
    return trades


def agg(tr):
    if not tr:
        return {"n": 0, "wr": 0, "tot": 0.0, "avg": 0.0}
    w = sum(1 for t in tr if t["r"] > 0)
    rs = [t["r"] for t in tr]
    return {"n": len(tr), "wr": round(100 * w / len(tr), 1),
            "tot": round(sum(rs), 2), "avg": round(statistics.mean(rs), 3)}


def block_boot(tr, iters=2000, block_days=3):
    """Gün-bloklu bootstrap (örtüşen etiketler i.i.d. değil)."""
    if not tr:
        return 0.0
    byday = defaultdict(list)
    for t in tr:
        d = int(t["ts"] // (block_days * 86400))
        byday[d].append(t["r"])
    blocks = list(byday.values())
    n = len(blocks)
    if n < 3:
        return 0.0
    pos = 0
    for _ in range(iters):
        s = 0.0
        for _ in range(n):
            s += sum(blocks[random.randrange(n)])
        if s > 0:
            pos += 1
    return round(100 * pos / iters, 1)


def monthly(tr):
    by = defaultdict(float)
    for t in tr:
        m = datetime.fromtimestamp(t["ts"], timezone.utc).strftime("%m")
        by[m] += t["r"]
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()
    client = _client()
    sigs, b1, b5 = load(client)
    ctx = Ctx(b1, b5)
    ev = build_events(sigs, ctx)
    span = (ev[-1]["ts"] - ev[0]["ts"]) / 86400 if ev else 0
    print(f"NDX SELL DERİN IZGARA · {datetime.fromtimestamp(ev[0]['ts'], timezone.utc):%Y-%m-%d} → "
          f"{datetime.fromtimestamp(ev[-1]['ts'], timezone.utc):%Y-%m-%d}  ({span:.0f} gün)")
    print(f"sinyal={len(sigs)}  olay={len(ev)}  1m bar={len(b1)}  "
          f"sürtünme={FRICTION}p  (zaman kayması DÜZELTİLDİ)\n")

    rows = []
    # sabit referanslar
    for tpf, slf, lbl in ((80, 110, "SABİT TP80/SL110 (canlı)"),
                          (80, 150, "SABİT TP80/SL150"),
                          (110, 150, "SABİT TP110/SL150")):
        rows.append((lbl, agg(run(ev, ctx, tp_fix=tpf, sl_fix=slf)), None, None))
    # ATR ızgarası
    for tp_m in (0.75, 1.0, 1.5, 2.0, 2.5, 3.0):
        for sl_m in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
            tr = run(ev, ctx, tp_m=tp_m, sl_m=sl_m)
            rows.append((f"TP {tp_m}×ATR / SL {sl_m}×ATR", agg(tr), tp_m, sl_m))

    print(f"{'geometri':<28}{'n':>5}{'WR':>7}{'başabaş':>9}{'marj':>8}"
          f"{'totR':>9}{'avgR':>8}")
    print("─" * 74)
    for lbl, s, tp_m, sl_m in rows:
        if not s["n"]:
            continue
        be = 100 * (sl_m / (tp_m + sl_m)) if tp_m else 100 * 110 / 190
        if "TP80/SL150" in lbl:
            be = 100 * 150 / 230
        elif "TP110/SL150" in lbl:
            be = 100 * 150 / 260
        print(f"{lbl:<28}{s['n']:>5}{s['wr']:>6.1f}%{be:>8.1f}%"
              f"{s['wr'] - be:>+7.1f}pp{s['tot']:>+9.2f}{s['avg']:>+8.3f}")

    # en iyi adayların dayanıklılığı
    atr_rows = [(l, s, t, sm) for l, s, t, sm in rows if t]
    best = sorted(atr_rows, key=lambda x: -x[1]["tot"])[:5]
    print(f"\n{'═' * 74}\nEN İYİ 5 — AYLIK DAYANIKLILIK + BLOK BOOTSTRAP\n{'═' * 74}")
    ev_sorted = sorted(ev, key=lambda e: e["ts"])
    cut = ev_sorted[int(len(ev_sorted) * 0.6)]["ts"]
    e_in = [e for e in ev_sorted if e["ts"] < cut]
    e_out = [e for e in ev_sorted if e["ts"] >= cut]
    for lbl, s, tp_m, sl_m in best:
        tr = run(ev, ctx, tp_m=tp_m, sl_m=sl_m)
        mo = monthly(tr)
        pos = sum(1 for v in mo.values() if v > 0)
        si = agg(run(e_in, ctx, tp_m=tp_m, sl_m=sl_m))
        so = agg(run(e_out, ctx, tp_m=tp_m, sl_m=sl_m))
        print(f"\n{lbl}  totR={s['tot']:+.2f}  P(kâr>0)={block_boot(tr)}%")
        print("   aylık: " + "  ".join(f"{k}:{v:+.1f}" for k, v in sorted(mo.items()))
              + f"   → {pos}/{len(mo)} ay pozitif")
        print(f"   IN (%60): n={si['n']} WR=%{si['wr']} R={si['tot']:+.2f}   "
              f"OUT (%40): n={so['n']} WR=%{so['wr']} R={so['tot']:+.2f}")


if __name__ == "__main__":
    main()
