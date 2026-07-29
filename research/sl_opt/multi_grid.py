"""multi_grid.py — ATR SL/TP ızgarası: USOIL + DAX (+ NDX referansı).

NDX SELL'de bulunan sonucu (SL=2.0×ATR, 6/6 ay pozitif) diğer sembollerde
sınar. Aynı sızıntısız protokol:
  * zaman kayması düzeltmesi (deep_grid.drift_for — tüm semboller aynı broker)
  * karar anına kadarki barlar; çözüm sonraki 1m barlarla; aynı barda TP+SL → SL
  * trend (1h EMA50 hizası) + konum (4h dalga) kapıları — NDX'te belirleyiciydi
  * aylık dayanıklılık + kronolojik %60/%40 + gün-bloklu bootstrap

Sembol geometrileri botun kendi sabitleri:
  NDX   TP 80p  / SL 110p
  GDAXI TP 67p  / SL 119p
  USOIL TP %1.04 / SL %1.49   ← yüzde bazlı, ATR karşılaştırması ilginç
"""
from __future__ import annotations

import argparse
import bisect
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from deep_grid import (_client, _page, parse_ts, drift_for, agg, block_boot,  # noqa: E402
                       Ctx, FRICTION, ATR_N, MAX_HOLD_BARS)

SINCE = "2026-02-11T00:00:00+00:00"
GEOM = {                       # (tp, sl, yüzde_mi)
    "NDX.INDX":    (80.0, 110.0, False),
    "GDAXI.INDX":  (67.0, 119.0, False),
    "USOIL.FOREX": (1.04, 1.49, True),
}
# sürtünme (puan) — USOIL fiyatı ~85 olduğu için oransal olarak farklı
FRICTION_BY = {"NDX.INDX": 1.3, "GDAXI.INDX": 1.3, "USOIL.FOREX": 0.03}
POS_LOOKBACK_5M = 48
EMA_1H = 50


def load_sym(client, symbol: str):
    cache = HERE / f"mg_{symbol.replace('.', '_')}.json"
    if cache.exists():
        d = json.loads(cache.read_text())
        return d["sigs"], d["b1"], d["b5"], d["b1h"]

    sigs = []
    for m in ("pulse1", "pulse2", "pulse3"):
        for r in _page(client, "prediction_logs", "created_at,ml_direction",
                       [("symbol", symbol), ("model_type", m)], "created_at", SINCE):
            d = (r.get("ml_direction") or "").upper()
            if d in ("BUY", "SELL"):
                sigs.append({"ts": int(parse_ts(r["created_at"]).timestamp()), "dir": d})
    sigs.sort(key=lambda x: x["ts"])

    def bars(tf):
        out, seen = [], set()
        for r in _page(client, "candle_cache", "candle_time,high,low,close",
                       [("symbol", symbol), ("timeframe", tf)], "candle_time", SINCE):
            dt = parse_ts(r["candle_time"])
            if tf == "1m" and dt.second:
                continue
            ts = int(dt.timestamp()) + drift_for(dt)     # zaman kayması düzeltmesi
            if ts in seen:
                continue
            seen.add(ts)
            out.append({"ts": ts, "h": float(r["high"]), "l": float(r["low"]),
                        "c": float(r["close"])})
        out.sort(key=lambda b: b["ts"])
        return out

    b1, b5, b1h = bars("1m"), bars("5m"), bars("1h")
    cache.write_text(json.dumps({"sigs": sigs, "b1": b1, "b5": b5, "b1h": b1h}))
    return sigs, b1, b5, b1h


class Ctx2(Ctx):
    def __init__(self, b1, b5, b1h, friction):
        super().__init__(b1, b5)
        self.b1h = b1h
        self.k1h = [b["ts"] for b in b1h]
        self.fr = friction

    def trend_aligned(self, ts, direction):
        i = bisect.bisect_right(self.k1h, ts)
        win = self.b1h[max(0, i - 60):i]
        if len(win) < EMA_1H:
            return None
        c = [b["c"] for b in win]
        k = 2 / (EMA_1H + 1)
        e = c[-EMA_1H]
        for v in c[-EMA_1H + 1:]:
            e = v * k + e * (1 - k)
        above = c[-1] > e
        return above if direction == "BUY" else (not above)

    def wave_pos(self, ts, px):
        i = bisect.bisect_right(self.k5, ts)
        win = self.b5[max(0, i - POS_LOOKBACK_5M):i]
        if len(win) < 20:
            return None
        hi = max(b["h"] for b in win)
        lo = min(b["l"] for b in win)
        return (px - lo) / (hi - lo) if hi > lo else None

    def resolve(self, ts, entry, direction, tp_d, sl_d):
        sign = 1 if direction == "BUY" else -1
        e = entry + sign * self.fr                      # giriş aleyhte kayar
        tp, sl = e + sign * tp_d, e - sign * sl_d
        i = bisect.bisect_right(self.k1, ts)
        for k in self.k1[i:i + MAX_HOLD_BARS]:
            b = self.b1[bisect.bisect_left(self.k1, k)]
            hit_sl = (b["l"] - self.fr <= sl) if sign > 0 else (b["h"] + self.fr >= sl)
            hit_tp = (b["h"] >= tp) if sign > 0 else (b["l"] <= tp)
            if hit_sl:
                return -1.0, k
            if hit_tp:
                return tp_d / sl_d, k
        return None, None


def build(sigs, ctx, direction, gated):
    out = []
    for s in sigs:
        if s["dir"] != direction:
            continue
        px = ctx.price_at(s["ts"])
        atr = ctx.atr5(s["ts"])
        if not px or not atr:
            continue
        if gated:
            if ctx.trend_aligned(s["ts"], direction) is False:
                continue
            p = ctx.wave_pos(s["ts"], px)
            if p is not None:
                if (direction == "SELL" and p < 0.40) or (direction == "BUY" and p > 0.60):
                    continue
        out.append({"ts": s["ts"], "px": px, "atr": atr})
    return out


def run(ev, ctx, direction, symbol, tp_m=None, sl_m=None, fixed=False):
    tpc, slc, pct = GEOM[symbol]
    trades, open_until = [], 0
    for e in ev:
        if e["ts"] < open_until:
            continue
        if fixed:
            tp = e["px"] * tpc / 100.0 if pct else tpc
            sl = e["px"] * slc / 100.0 if pct else slc
        else:
            tp = (e["px"] * tpc / 100.0 if pct else tpc) if tp_m is None else tp_m * e["atr"]
            sl = sl_m * e["atr"]
        if tp <= 0 or sl <= 0:
            continue
        r, ex = ctx.resolve(e["ts"], e["px"], direction, tp, sl)
        if r is None:
            continue
        trades.append({"r": r, "ts": e["ts"]})
        open_until = ex
    return trades


def monthly(tr):
    by = defaultdict(float)
    for t in tr:
        by[datetime.fromtimestamp(t["ts"], timezone.utc).strftime("%m")] += t["r"]
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="USOIL.FOREX,GDAXI.INDX")
    a = ap.parse_args()
    client = _client()

    for symbol in a.symbols.split(","):
        sigs, b1, b5, b1h = load_sym(client, symbol)
        ctx = Ctx2(b1, b5, b1h, FRICTION_BY.get(symbol, 1.3))
        print(f"\n{'═' * 84}\n{symbol}  ·  sinyal={len(sigs)}  1m={len(b1)}  "
              f"sürtünme={ctx.fr}\n{'═' * 84}")
        for direction in ("BUY", "SELL"):
            ev_g = build(sigs, ctx, direction, gated=True)
            ev_r = build(sigs, ctx, direction, gated=False)
            if len(ev_g) < 30:
                print(f"\n── {direction}: kapılı olay {len(ev_g)} — yetersiz")
                continue
            print(f"\n── {direction} ──  olay: kapısız={len(ev_r)}  KAPILI={len(ev_g)}")
            base_raw = agg(run(ev_r, ctx, direction, symbol, fixed=True))
            print(f"   sabit geometri, KAPISIZ : n={base_raw['n']:>4} "
                  f"WR=%{base_raw['wr']:<5} R={base_raw['tot']:>+8.2f}")

            rows = []
            tr_fix = run(ev_g, ctx, direction, symbol, fixed=True)
            rows.append(("sabit (canlı)", agg(tr_fix), tr_fix, None))
            for sl_m in (1.5, 2.0, 2.5, 3.0):
                tr = run(ev_g, ctx, direction, symbol, tp_m=None, sl_m=sl_m)
                rows.append((f"sabit TP / SL {sl_m}×ATR", agg(tr), tr, sl_m))
            for tp_m, sl_m in ((1.5, 2.0), (2.0, 2.0), (1.5, 2.5), (2.0, 2.5)):
                tr = run(ev_g, ctx, direction, symbol, tp_m=tp_m, sl_m=sl_m)
                rows.append((f"TP {tp_m}×ATR / SL {sl_m}×ATR", agg(tr), tr, sl_m))

            evs = sorted(ev_g, key=lambda e: e["ts"])
            cut = evs[int(len(evs) * 0.6)]["ts"]
            ein = [e for e in evs if e["ts"] < cut]
            eout = [e for e in evs if e["ts"] >= cut]

            print(f"   {'geometri':<24}{'n':>5}{'WR':>7}{'totR':>9}{'aylık':>8}"
                  f"{'OUT-R':>8}{'P(kâr)':>8}")
            for lbl, s, tr, sl_m in rows:
                if not s["n"]:
                    continue
                mo = monthly(tr)
                pos = sum(1 for v in mo.values() if v > 0)
                kw = dict(fixed=True) if sl_m is None else \
                    dict(tp_m=None if "sabit TP" in lbl else float(lbl.split()[1].split("×")[0]),
                         sl_m=sl_m)
                so = agg(run(eout, ctx, direction, symbol, **kw))
                print(f"   {lbl:<24}{s['n']:>5}{s['wr']:>6.1f}%{s['tot']:>+9.2f}"
                      f"{pos:>6}/{len(mo)}{so['tot']:>+8.2f}{block_boot(tr):>7.1f}%")


if __name__ == "__main__":
    main()
