"""sim2.py — GENİŞLETİLMİŞ deney: "işlem sayısını öldürmeden kaliteyi artır".

sim.py'nin bulgusu: trend+konum kapıları kaliteyi ciddi artırıyor AMA işlem
sayısını ~%70 kesiyor. Kullanıcı isteği: "günde 1-2 işleme düşmesin, 4-5 hatta
daha fazla olsun; örüntüyü yakalayıp DOĞRU NOKTADAN girsin; son ~400 mumun
destek/direnç seviyelerini hesaba katsın."

FİKİR: kapıya takılan sinyali ATMAK yerine DOĞRU FİYATA TAŞI.
  Sinyal SELL ama fiyat dalganın dibinde → atma; en yakın DİRENCE
  SELL-LIMIT koy, N dakika geçerli. Fiyat oraya gelirse doğru noktadan
  gireriz; gelmezse emir iptal (kovalama yok).
Bot'ta bu mimari zaten var (`open_trade_sr`) ama yalnız ROBUST_SCOPES
kullanıyor; VIXREG/CHREV ham market emri atıyor.

TEST EDİLEN VARYANTLAR
  A market_ham        : sinyal anında market (bugünkü VIXREG davranışı)
  B kapı_at           : trend+konum kapısı, takılırsa AT (bugünkü canlı)
  C sr_limit          : takılırsa en yakın S/R seviyesine LIMIT taşı
  D sr_limit_hepsi    : HER sinyali S/R seviyesine taşı (kapı yok)
  E kapı_veya_limit   : kapıyı geçen market, takılan S/R limit (hibrit)

SIZINTI: S/R seviyeleri yalnız karar anına kadarki 400 mumdan; limit dolumu
sonraki barların high/low'u ile; dolum barından SONRAKİ barlarla çözüm;
aynı barda TP+SL → konservatif SL. Gelecek hiçbir yere girmiyor.
"""
from __future__ import annotations

import argparse
import bisect
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sim import (_client, fetch_bars, fetch_signals, Ctx, geom_for, stats,  # noqa: E402
                 GEOM, MAX_HOLD_BARS, parse_ts)

SINCE = "2026-06-01T00:00:00+00:00"
SR_LOOKBACK = 400              # kullanıcı isteği: son ~400 mum
SR_MIN_TOUCH = 4
ZONE_WIDTH = {"NDX.INDX": 10.0, "GDAXI.INDX": 10.0,
              "USOIL.FOREX": 0.12, "XAUUSD": 3.0}
LIMIT_VALID_MIN = 90           # limit emri kaç dakika geçerli
SR_MAX_DIST_ATR = 2.5          # bu kadar uzaktaki seviyeye emir koyma


# ─── S/R bölgeleri (sr_zones.py mantığının sadeleştirilmiş hali) ────────────

def detect_zones(bars: list[dict], width: float, min_touch: int = SR_MIN_TOUCH):
    """Yüksek-dokunuşlu S/R merkezleri (greedy non-maximum suppression)."""
    if not bars:
        return []
    cands = sorted({round(p, 5) for b in bars for p in (b["h"], b["l"], b["c"])})
    used = [False] * len(bars)
    zones = []
    half = width / 2.0
    while True:
        best, best_members = None, []
        for ctr in cands:
            mem = [i for i, b in enumerate(bars)
                   if not used[i] and (b["l"] <= ctr + half and b["h"] >= ctr - half)]
            if len(mem) > len(best_members):
                best, best_members = ctr, mem
        if best is None or len(best_members) < min_touch:
            break
        for i in best_members:
            used[i] = True
        zones.append({"center": best, "touches": len(best_members)})
        if len(zones) >= 12:
            break
    return sorted(zones, key=lambda z: z["center"])


def atr_of(bars: list[dict], n: int = 14) -> float:
    if len(bars) < n + 1:
        return 0.0
    trs = [max(bars[i]["h"] - bars[i]["l"],
               abs(bars[i]["h"] - bars[i - 1]["c"]),
               abs(bars[i]["l"] - bars[i - 1]["c"]))
           for i in range(len(bars) - n, len(bars))]
    return sum(trs) / len(trs)


class Ctx2(Ctx):
    _zcache: dict = {}

    def sr_levels(self, ts: int, symbol: str):
        """Karar anına kadarki son 400×5m bardan S/R + ATR. Sızıntı yok."""
        i = bisect.bisect_right(self.k5, ts)
        # Aynı 5m barı paylaşan sinyaller aynı S/R'ı görür → tekrar hesaplama.
        # (Sızıntı yok: pencere hâlâ yalnız geçmiş barlar.)
        key = (symbol, i)
        hit = self._zcache.get(key)
        if hit is not None:
            return hit
        win = self.b5[max(0, i - SR_LOOKBACK):i]
        if len(win) < 60:
            out = ([], 0.0)
        else:
            out = (detect_zones(win, ZONE_WIDTH.get(symbol, 10.0)), atr_of(win))
        if len(self._zcache) > 4000:
            self._zcache.clear()
        self._zcache[key] = out
        return out

    def limit_fill(self, ts: int, level: float, direction: str, valid_min: int):
        """Limit emri dolar mı? Dönüş: (dolum_ts, dolum_fiyatı) | (None, None).
        SELL-LIMIT üstte → fiyat yükselip seviyeye değerse dolar."""
        i = bisect.bisect_right(self.k1, ts)
        end = ts + valid_min * 60
        for k in self.k1[i:]:
            if k > end:
                return None, None
            b = self.b1[bisect.bisect_left(self.k1, k)]
            if direction == "SELL" and b["h"] >= level:
                return k, level
            if direction == "BUY" and b["l"] <= level:
                return k, level
        return None, None


def resolve2(ctx: Ctx2, entry_ts: int, entry: float, direction: str,
             tp_d: float, sl_d: float):
    sign = 1 if direction == "BUY" else -1
    tp, sl = entry + sign * tp_d, entry - sign * sl_d
    i = bisect.bisect_right(ctx.k1, entry_ts)
    for k in ctx.k1[i:i + MAX_HOLD_BARS]:
        b = ctx.b1[bisect.bisect_left(ctx.k1, k)]
        hit_sl = (b["l"] <= sl) if sign > 0 else (b["h"] >= sl)
        hit_tp = (b["h"] >= tp) if sign > 0 else (b["l"] <= tp)
        if hit_sl:
            return -1.0, k
        if hit_tp:
            return tp_d / sl_d, k
    return None, None


def nearest_level(zones, price, direction, atr):
    """SELL → üstteki en yakın direnç; BUY → alttaki en yakın destek."""
    if not zones:
        return None
    if direction == "SELL":
        c = [z for z in zones if z["center"] > price]
        z = min(c, key=lambda x: x["center"] - price) if c else None
    else:
        c = [z for z in zones if z["center"] < price]
        z = max(c, key=lambda x: x["center"]) if c else None
    if z is None:
        return None
    if atr > 0 and abs(z["center"] - price) > SR_MAX_DIST_ATR * atr:
        return None                      # çok uzak → kovalama yok
    return z["center"]


# ─── Varyant motoru ─────────────────────────────────────────────────────────

def run(symbol, direction, sigs, ctx: Ctx2, mode: str, min_votes=1,
        vote_window=300, pos_sell_min=0.40, pos_buy_max=0.60):
    events = sorted([s for s in sigs if s["dir"] == direction], key=lambda x: x["ts"])
    trades, open_until = [], 0
    counts = defaultdict(int)

    for s in events:
        ts = s["ts"]
        if ts < open_until:
            counts["zaten_acik"] += 1
            continue
        models = {e["model"] for e in events if ts - vote_window <= e["ts"] <= ts}
        if len(models) < min_votes:
            continue
        price = ctx.price_at(ts)
        if price is None:
            continue
        tp_d, sl_d = geom_for(symbol, price)

        # kapı değerlendirmesi (bilgi olarak — moda göre kullanılır)
        aligned = ctx.trend_aligned(ts, direction)
        pos = ctx.wave_pos(ts, price)
        gate_ok = True
        if aligned is False:
            gate_ok = False
        if pos is not None:
            if (direction == "SELL" and pos < pos_sell_min) or \
               (direction == "BUY" and pos > pos_buy_max):
                gate_ok = False

        entry_ts, entry = ts, price
        if mode == "A":                              # ham market
            pass
        elif mode == "B":                            # kapı: takılırsa at
            if not gate_ok:
                counts["kapi_atti"] += 1
                continue
        elif mode in ("C", "E"):                     # takılırsa S/R limite taşı
            if not gate_ok:
                zones, atr = ctx.sr_levels(ts, symbol)
                lvl = nearest_level(zones, price, direction, atr)
                if lvl is None:
                    counts["sr_yok"] += 1
                    continue
                f_ts, f_px = ctx.limit_fill(ts, lvl, direction, LIMIT_VALID_MIN)
                if f_ts is None:
                    counts["limit_dolmadi"] += 1
                    continue
                entry_ts, entry = f_ts, f_px
                tp_d, sl_d = geom_for(symbol, entry)
                counts["sr_limit_doldu"] += 1
        elif mode == "D":                            # HER sinyal S/R limite
            zones, atr = ctx.sr_levels(ts, symbol)
            lvl = nearest_level(zones, price, direction, atr)
            if lvl is None:
                counts["sr_yok"] += 1
                continue
            f_ts, f_px = ctx.limit_fill(ts, lvl, direction, LIMIT_VALID_MIN)
            if f_ts is None:
                counts["limit_dolmadi"] += 1
                continue
            entry_ts, entry = f_ts, f_px
            tp_d, sl_d = geom_for(symbol, entry)
            counts["sr_limit_doldu"] += 1

        r, exit_ts = resolve2(ctx, entry_ts, entry, direction, tp_d, sl_d)
        if r is None:
            counts["cozulmedi"] += 1
            continue
        trades.append({"ts": entry_ts, "r": r})
        open_until = exit_ts
    return trades, dict(counts)


MODES = [("A market_ham", "A"), ("B kapı_at", "B"), ("C kapı+SR_limit", "C"),
         ("D hepsi_SR_limit", "D")]


def days_span(sigs):
    if not sigs:
        return 1
    t0, t1 = min(s["ts"] for s in sigs), max(s["ts"] for s in sigs)
    return max(1, (t1 - t0) / 86400)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="NDX.INDX,GDAXI.INDX,USOIL.FOREX")
    ap.add_argument("--split", type=float, default=0.60)
    a = ap.parse_args()
    client = _client()
    print("A=ham market · B=kapı(at) · C=kapı+S/R limit · D=hepsi S/R limit")
    print(f"S/R: son {SR_LOOKBACK}×5m mum, dokunuş≥{SR_MIN_TOUCH}, "
          f"limit {LIMIT_VALID_MIN}dk geçerli, max {SR_MAX_DIST_ATR}×ATR uzaklık\n")

    for symbol in a.symbols.split(","):
        b1 = fetch_bars(client, symbol, "1m", SINCE)
        b5 = fetch_bars(client, symbol, "5m", SINCE)
        b1h = fetch_bars(client, symbol, "1h", SINCE)
        sigs = fetch_signals(client, symbol, SINCE)
        if len(b1) < 1000 or not sigs:
            continue
        ctx = Ctx2(b1, b5, b1h)
        ss = sorted(sigs, key=lambda x: x["ts"])
        cut = ss[int(len(ss) * a.split)]["ts"]
        ins = [s for s in ss if s["ts"] < cut]
        outs = [s for s in ss if s["ts"] >= cut]
        d_in, d_out = days_span(ins), days_span(outs)
        print(f"\n{'═' * 92}\n{symbol}\n{'═' * 92}")
        for direction in ("BUY", "SELL"):
            if sum(1 for s in ss if s["dir"] == direction) < 40:
                continue
            print(f"\n── {direction} ──")
            print(f"{'varyant':<20}{'IN-SAMPLE':<40}{'OUT-OF-SAMPLE':<40}")
            for label, mode in MODES:
                ti, _ = run(symbol, direction, ins, ctx, mode)
                to, co = run(symbol, direction, outs, ctx, mode)
                si, so = stats(ti), stats(to)
                fi = (f"n={si['n']:>3} {si['n']/d_in:>4.1f}/gün WR=%{si['wr'] or 0:<5} "
                      f"R={si['totR']:>+6.1f}" if si["n"] else "n=0")
                fo = (f"n={so['n']:>3} {so['n']/d_out:>4.1f}/gün WR=%{so['wr'] or 0:<5} "
                      f"R={so['totR']:>+6.1f} avgR={so['avgR']:>+.3f}" if so["n"] else "n=0")
                print(f"{label:<20}{fi:<40}{fo:<40}")


if __name__ == "__main__":
    main()
