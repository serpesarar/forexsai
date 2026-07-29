"""ndx_sell_sl.py — NDX SELL için SL optimizasyonu (sabit + ATR-uyarlamalı).

Soru: mevcut 80/110 geometrisinde SL'i genişletmek kâr oranını artırır mı?

VERİ PENCERESİ — KRİTİK: `candle_cache` barları 2026-07-16'ya kadar MT5 broker
sunucu saatiyle (UTC+2/+3) etiketlenmişti (research/ndx_buy_lab/RAPOR.md §1).
Sinyal↔bar eşlemesi o dönemde 3 saat kaymış olur. Bu yüzden bu çalışma
**yalnız 2026-07-16 sonrası** veriyi kullanır — kullanıcının istediği "son 1
hafta" zaten bu temiz bölgede.

SIZINTI: karar anı = sinyalin gerçek UTC damgası; giriş = o ana kadar KAPANMIŞ
son 1m barın kapanışı; ATR yalnız geçmiş barlardan; çözüm girişten SONRAKİ
barların high/low'u ile; aynı barda TP+SL → KONSERVATİF SL (her varyantta aynı).
Sürtünme: 1.3 puan (ndx_buy_lab'ın ölçtüğü MT5 1m spread medyanı).
"""
from __future__ import annotations

import argparse
import bisect
import json
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

CLEAN_SINCE = "2026-07-16T00:00:00+00:00"      # zaman-damgası düzeltmesi sonrası
SYMBOL = "NDX.INDX"
TP_BASE, SL_BASE = 80.0, 110.0                 # botun canlı VIXREG geometrisi
FRICTION = 1.3                                 # ölçülmüş spread (puan)
MAX_HOLD_BARS = 2880
EMA_1H = 50
POS_LOOKBACK_5M = 48


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


def fetch(client, table, select, filters, tcol, since):
    out, cursor = [], since
    while True:
        q = client.table(table).select(select)
        for f in filters:
            q = q.eq(*f) if len(f) == 2 else q.in_(*f[1:])
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


def load(client, since):
    cache = HERE / f"data_{since[:10]}.json"
    if cache.exists():
        d = json.loads(cache.read_text())
        return d["sigs"], d["b1"], d["b5"], d["b1h"]

    sigs = []
    for m in ("pulse1", "pulse2", "pulse3"):
        for r in fetch(client, "prediction_logs", "created_at,model_type,ml_direction",
                       [("symbol", SYMBOL), ("model_type", m)], "created_at", since):
            if (r.get("ml_direction") or "").upper() == "SELL":
                sigs.append({"ts": int(parse_ts(r["created_at"]).timestamp()),
                             "model": m})
    sigs.sort(key=lambda x: x["ts"])

    def bars(tf):
        out = []
        for r in fetch(client, "candle_cache", "candle_time,high,low,close",
                       [("symbol", SYMBOL), ("timeframe", tf)], "candle_time", since):
            dt = parse_ts(r["candle_time"])
            if tf == "1m" and dt.second:
                continue
            out.append({"ts": int(dt.timestamp()), "h": float(r["high"]),
                        "l": float(r["low"]), "c": float(r["close"])})
        seen, uniq = set(), []
        for b in out:
            if b["ts"] not in seen:
                seen.add(b["ts"])
                uniq.append(b)
        return uniq

    b1, b5, b1h = bars("1m"), bars("5m"), bars("1h")
    cache.write_text(json.dumps({"sigs": sigs, "b1": b1, "b5": b5, "b1h": b1h}))
    return sigs, b1, b5, b1h


class Ctx:
    def __init__(self, b1, b5, b1h):
        self.b1, self.b5, self.b1h = b1, b5, b1h
        self.k1 = [b["ts"] for b in b1]
        self.k5 = [b["ts"] for b in b5]
        self.k1h = [b["ts"] for b in b1h]

    def price_at(self, ts):
        i = bisect.bisect_right(self.k1, ts)
        return self.b1[i - 1]["c"] if i else None

    def atr5(self, ts, n=14):
        """ATR(n) — yalnız karar anına kadar kapanmış 5m barlardan."""
        i = bisect.bisect_right(self.k5, ts)
        win = self.b5[max(0, i - n - 1):i]
        if len(win) < n + 1:
            return None
        trs = [max(win[j]["h"] - win[j]["l"],
                   abs(win[j]["h"] - win[j - 1]["c"]),
                   abs(win[j]["l"] - win[j - 1]["c"]))
               for j in range(1, len(win))]
        return sum(trs) / len(trs)

    def trend_aligned_sell(self, ts):
        i = bisect.bisect_right(self.k1h, ts)
        win = self.b1h[max(0, i - 60):i]
        if len(win) < EMA_1H:
            return None
        closes = [b["c"] for b in win]
        k = 2.0 / (EMA_1H + 1)
        e = closes[-EMA_1H]
        for v in closes[-EMA_1H + 1:]:
            e = v * k + e * (1 - k)
        return closes[-1] < e                       # SELL → fiyat EMA50 ALTINDA

    def wave_pos(self, ts, price):
        i = bisect.bisect_right(self.k5, ts)
        win = self.b5[max(0, i - POS_LOOKBACK_5M):i]
        if len(win) < 20:
            return None
        hi = max(b["h"] for b in win)
        lo = min(b["l"] for b in win)
        return (price - lo) / (hi - lo) if hi > lo else None

    def resolve_sell(self, ts, entry, tp_d, sl_d):
        """SELL çözümü. Sürtünme: giriş aleyhte kayar + hedefler zorlaşır."""
        e = entry - FRICTION                        # SELL'de bid'den gireriz
        tp, sl = e - tp_d, e + sl_d
        i = bisect.bisect_right(self.k1, ts)
        for k in self.k1[i:i + MAX_HOLD_BARS]:
            b = self.b1[bisect.bisect_left(self.k1, k)]
            if b["h"] + FRICTION >= sl:             # SL önce (konservatif)
                return -1.0, k
            if b["l"] <= tp:
                return tp_d / sl_d, k
        return None, None


def episodes(sigs, ctx, gated: bool, vote_window=300, min_votes=1):
    """Sinyalleri işleme çevir (scope başına tek açık pozisyon)."""
    out, open_until = [], 0
    for s in sigs:
        ts = s["ts"]
        if ts < open_until:
            continue
        models = {e["model"] for e in sigs if ts - vote_window <= e["ts"] <= ts}
        if len(models) < min_votes:
            continue
        price = ctx.price_at(ts)
        if price is None:
            continue
        if gated:
            if ctx.trend_aligned_sell(ts) is False:
                continue
            pos = ctx.wave_pos(ts, price)
            if pos is not None and pos < 0.40:
                continue
        atr = ctx.atr5(ts)
        out.append({"ts": ts, "price": price, "atr": atr})
        open_until = ts + 60          # geçici; gerçek kapanış varyanta göre değişir
    return out


def run_variant(eps, ctx, tp_d, sl_d, atr_mult=None, tp_mult=None):
    """Bir geometri varyantını koştur. atr_mult verilirse SL = atr_mult×ATR."""
    trades, open_until = [], 0
    for e in eps:
        if e["ts"] < open_until:
            continue
        if atr_mult is not None:
            if not e["atr"]:
                continue
            sl = atr_mult * e["atr"]
            tp = (tp_mult * e["atr"]) if tp_mult else tp_d
        else:
            sl, tp = sl_d, tp_d
        if sl <= 0 or tp <= 0:
            continue
        r, exit_ts = ctx.resolve_sell(e["ts"], e["price"], tp, sl)
        if r is None:
            continue
        trades.append({"r": r, "tp": tp, "sl": sl})
        open_until = exit_ts
    return trades


def summarize(trades):
    if not trades:
        return {"n": 0}
    w = sum(1 for t in trades if t["r"] > 0)
    rs = [t["r"] for t in trades]
    tp = statistics.mean(t["tp"] for t in trades)
    sl = statistics.mean(t["sl"] for t in trades)
    be = 100 * sl / (tp + sl)
    return {"n": len(trades), "wr": round(100 * w / len(trades), 1),
            "totR": round(sum(rs), 2), "avgR": round(statistics.mean(rs), 3),
            "be": round(be, 1), "tp": round(tp, 1), "sl": round(sl, 1)}


def line(label, s):
    if not s["n"]:
        return f"{label:<26} n=0"
    marj = s["wr"] - s["be"]
    return (f"{label:<26} n={s['n']:>3}  TP/SL={s['tp']:>5.0f}/{s['sl']:>5.0f}  "
            f"WR=%{s['wr']:<5} başabaş=%{s['be']:<5} marj={marj:>+5.1f}pp  "
            f"totR={s['totR']:>+7.2f}  avgR={s['avgR']:>+.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=CLEAN_SINCE)
    ap.add_argument("--week", action="store_true", help="yalnız son 7 gün")
    a = ap.parse_args()
    client = _client()
    sigs, b1, b5, b1h = load(client, CLEAN_SINCE)
    ctx = Ctx(b1, b5, b1h)

    if a.week:
        cut = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())
        sigs = [s for s in sigs if s["ts"] >= cut]
        etiket = "SON 7 GÜN"
    else:
        etiket = f"TEMİZ DÖNEM ({CLEAN_SINCE[:10]} →)"

    print(f"NDX SELL — SL OPTİMİZASYONU · {etiket}")
    print(f"sinyal={len(sigs)}  1m bar={len(b1)}  sürtünme={FRICTION}p\n")

    for gated, gl in ((False, "KAPISIZ"), (True, "trend+konum KAPILI")):
        eps = episodes(sigs, ctx, gated)
        if len(eps) < 5:
            print(f"── {gl}: yetersiz olay ({len(eps)})\n")
            continue
        print(f"{'═' * 108}\n{gl}  (olay {len(eps)})\n{'═' * 108}")

        print("\n【A】 SABİT SL taraması — TP sabit 80")
        for sl in (110, 130, 150, 180, 220, 260):
            print("  " + line(f"TP80 / SL{sl}", summarize(run_variant(eps, ctx, 80.0, sl))))

        print("\n【B】 SABİT — TP de büyür (RR 0.73 korunur)")
        for sl in (110, 150, 200, 260):
            print("  " + line(f"TP{sl * 80 // 110} / SL{sl}",
                              summarize(run_variant(eps, ctx, sl * 80.0 / 110.0, sl))))

        print("\n【C】 ATR-UYARLAMALI SL — TP sabit 80")
        for m in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
            print("  " + line(f"TP80 / SL {m}×ATR",
                              summarize(run_variant(eps, ctx, 80.0, 0, atr_mult=m))))

        print("\n【D】 TAM ATR — hem TP hem SL ATR ölçekli")
        for tm, sm in ((1.0, 1.5), (1.5, 2.0), (1.5, 2.5), (2.0, 2.5), (2.0, 3.0), (2.5, 3.5)):
            print("  " + line(f"TP {tm}×ATR / SL {sm}×ATR",
                              summarize(run_variant(eps, ctx, 0, 0, atr_mult=sm, tp_mult=tm))))
        print()


if __name__ == "__main__":
    main()
