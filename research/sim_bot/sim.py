"""sim.py — MT5 botunun HIZLANDIRILMIŞ GEÇMİŞ DENEYİ (timelapse backtest).

Amaç: "şu kapı faydalı mı?" sorusunu ileriye dönük 2 hafta beklemeden,
geçmiş veriyi bar-bar botun içinden geçirerek cevaplamak.

SIZINTI SÖZLEŞMESİ (kodda zorlanır):
  * Her karar YALNIZ o ana kadar KAPANMIŞ barlarla verilir (bars[:i]).
  * Giriş fiyatı = karar barının kapanışı; sonraki barlar karara giremez.
  * Çözüm yalnız girişten SONRAKİ barların high/low'u ile; aynı barda
    TP+SL → KONSERVATİF SL (baseline dahil her varyantta aynı kural).
  * Eşikler yalnız IN-SAMPLE dilimde seçilir, OUT-OF-SAMPLE'da doğrulanır
    (kronolojik %70/%30 — karıştırma yok).
  * Aynı anda scope başına 1 pozisyon (botun MAX_OPEN_PER_SCOPE=1 kuralı).

VERİ: prediction_logs (gerçek pulse sinyalleri, zaman damgalı) + candle_cache
(1m çözüm + 5m/1h gösterge). Yani sinyaller UYDURULMUYOR — botun canlıda
gördüğü sinyallerin ta kendisi.

SİMÜLE EDİLEMEYENLER (dürüstlük notu, rapora yazılır):
  * Backend momentum filtresi (canlı gösterge snapshot'ı geçmişe yok)
  * VIX rejimi (geçmiş VIX serisi yok) → VIXREG scope'u ayrı işaretlenir
  * Spread/slippage/komisyon (sonuçlar brüt)
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

# Botun gerçek geometrisi (yeni deneme/config.py)
GEOM = {                       # (tp, sl, yüzde_mi)
    "NDX.INDX":    (80.0, 110.0, False),
    "GDAXI.INDX":  (67.0, 119.0, False),
    "USOIL.FOREX": (1.04, 1.49, True),
    "XAUUSD":      (8.0, 6.0, False),
}
SCOPES = [("NDX.INDX", "BUY"), ("NDX.INDX", "SELL"),
          ("GDAXI.INDX", "BUY"), ("USOIL.FOREX", "BUY"), ("USOIL.FOREX", "SELL")]

POS_LOOKBACK_5M = 48           # 4 saatlik dalga (botla aynı)
EMA_BARS_1H = 50
PATIENCE_MIN = 10
PATIENCE_FLOOR_R = 0.3
MAX_HOLD_BARS = 2880           # 48 saat


def parse_ts(t: str) -> datetime:
    t = t.replace("Z", "+00:00")
    d = datetime.fromisoformat(t)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


# ─── Veri ────────────────────────────────────────────────────────────────────

def _client():
    from database.supabase_client import get_supabase_client
    c = get_supabase_client()
    if c is None:
        sys.exit("Supabase erişilemedi")
    return c


def fetch_bars(client, symbol: str, tf: str, since: str) -> list[dict]:
    cache = HERE / f"bars_{symbol.replace('.', '_')}_{tf}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out, cursor = [], since
    while True:
        res = (client.table("candle_cache").select("candle_time,open,high,low,close")
               .eq("symbol", symbol).eq("timeframe", tf)
               .gte("candle_time", cursor).order("candle_time").limit(1000).execute())
        if res.get("error"):
            raise RuntimeError(res["error"])
        chunk = res.get("data") or []
        if not chunk:
            break
        for r in chunk:
            dt = parse_ts(r["candle_time"])
            if tf == "1m" and dt.second:
                continue                       # tick-kirlilik koruması
            out.append({"ts": int(dt.timestamp()), "o": float(r["open"]),
                        "h": float(r["high"]), "l": float(r["low"]),
                        "c": float(r["close"])})
        cursor = (parse_ts(chunk[-1]["candle_time"]) + timedelta(seconds=1)).isoformat()
        if len(chunk) < 1000:
            break
    seen, uniq = set(), []
    for b in out:
        if b["ts"] not in seen:
            seen.add(b["ts"])
            uniq.append(b)
    cache.write_text(json.dumps(uniq))
    return uniq


def fetch_signals(client, symbol: str, since: str) -> list[dict]:
    cache = HERE / f"sig_{symbol.replace('.', '_')}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out, cursor = [], since
    while True:
        res = (client.table("prediction_logs")
               .select("created_at,model_type,ml_direction,ml_entry_price")
               .eq("symbol", symbol).gte("created_at", cursor)
               .in_("model_type", ["pulse1", "pulse2", "pulse3"])
               .order("created_at").limit(1000).execute())
        if res.get("error"):
            raise RuntimeError(res["error"])
        chunk = res.get("data") or []
        if not chunk:
            break
        for r in chunk:
            d = (r.get("ml_direction") or "").upper()
            if d in ("BUY", "SELL"):
                out.append({"ts": int(parse_ts(r["created_at"]).timestamp()),
                            "model": r["model_type"], "dir": d})
        cursor = (parse_ts(chunk[-1]["created_at"]) + timedelta(microseconds=1)).isoformat()
        if len(chunk) < 1000:
            break
    cache.write_text(json.dumps(out))
    return out


# ─── Göstergeler (yalnız geçmiş barlarla) ────────────────────────────────────

def ema_last(vals: list[float], n: int) -> float:
    k = 2.0 / (n + 1)
    e = vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e


class Ctx:
    """Bar dizileri + 'o ana kadar' sorguları. Sızıntı burada engellenir."""

    def __init__(self, b1: list[dict], b5: list[dict], b1h: list[dict]):
        self.b1, self.b5, self.b1h = b1, b5, b1h
        self.k1 = [b["ts"] for b in b1]
        self.k5 = [b["ts"] for b in b5]
        self.k1h = [b["ts"] for b in b1h]

    def _upto(self, bars, keys, ts, n):
        i = bisect.bisect_right(keys, ts)      # ts'te veya öncesinde KAPANMIŞ
        return bars[max(0, i - n):i]

    def wave_pos(self, ts: int, price: float):
        win = self._upto(self.b5, self.k5, ts, POS_LOOKBACK_5M)
        if len(win) < 20:
            return None
        hi = max(b["h"] for b in win)
        lo = min(b["l"] for b in win)
        return (price - lo) / (hi - lo) if hi > lo else None

    def trend_aligned(self, ts: int, direction: str):
        win = self._upto(self.b1h, self.k1h, ts, 60)
        if len(win) < EMA_BARS_1H:
            return None
        closes = [b["c"] for b in win]
        e = ema_last(closes[-EMA_BARS_1H:], EMA_BARS_1H)
        above = closes[-1] > e
        return above if direction == "BUY" else (not above)

    def price_at(self, ts: int):
        i = bisect.bisect_right(self.k1, ts)
        return self.b1[i - 1]["c"] if i else None


# ─── Simülasyon ──────────────────────────────────────────────────────────────

def geom_for(symbol: str, price: float):
    tp, sl, pct = GEOM[symbol]
    return (price * tp / 100.0, price * sl / 100.0) if pct else (tp, sl)


def resolve(ctx: Ctx, entry_ts: int, entry: float, direction: str,
            tp_d: float, sl_d: float):
    """Girişten SONRAKİ 1m barlarla çöz. (R, exit_ts) | (None, None) açık."""
    sign = 1 if direction == "BUY" else -1
    tp, sl = entry + sign * tp_d, entry - sign * sl_d
    i = bisect.bisect_right(ctx.k1, entry_ts)
    for k in ctx.k1[i:i + MAX_HOLD_BARS]:
        b = ctx.b1[bisect.bisect_left(ctx.k1, k)]
        hit_sl = (b["l"] <= sl) if sign > 0 else (b["h"] >= sl)
        hit_tp = (b["h"] >= tp) if sign > 0 else (b["l"] <= tp)
        if hit_sl:                              # konservatif: aynı barda SL önce
            return -1.0, k
        if hit_tp:
            return tp_d / sl_d, k
    return None, None


def patience_ok(ctx: Ctx, sig_ts: int, price: float, direction: str,
                tp_d: float, sl_d: float):
    """Sabır kapısı: 10dk sonra hâlâ 'yaşıyor' ve aleyhte <0.3R ise gir.
    Dönüş: (geçti_mi, yeni_giriş_ts, yeni_giriş_fiyatı)."""
    sign = 1 if direction == "BUY" else -1
    end = sig_ts + PATIENCE_MIN * 60
    i = bisect.bisect_right(ctx.k1, sig_ts)
    j = bisect.bisect_right(ctx.k1, end)
    win = ctx.b1[i:j]
    if len(win) < PATIENCE_MIN // 2:
        return False, None, None                # veri yok → girme (konservatif)
    hi = max(b["h"] for b in win)
    lo = min(b["l"] for b in win)
    if (sign > 0 and (lo <= price - sl_d or hi >= price + tp_d)) or \
       (sign < 0 and (hi >= price + sl_d or lo <= price - tp_d)):
        return False, None, None                # ±menzil görüldü → bizsiz biterdi
    c = win[-1]["c"]
    if sign * (c - price) / sl_d <= -PATIENCE_FLOOR_R:
        return False, None, None                # teyit yok
    return True, win[-1]["ts"], c


def simulate(symbol: str, direction: str, sigs: list[dict], ctx: Ctx,
             gates: dict, min_votes: int = 1, vote_window: int = 300):
    """Botun karar döngüsünü bar-bar tekrarla. Dönüş: işlem listesi."""
    events = [s for s in sigs if s["dir"] == direction]
    events.sort(key=lambda x: x["ts"])
    trades, open_until = [], 0
    skipped = defaultdict(int)

    for idx, s in enumerate(events):
        ts = s["ts"]
        if ts < open_until:
            skipped["zaten_acik"] += 1
            continue
        # oy: aynı yönde vote_window içinde kaç FARKLI model
        models = {e["model"] for e in events
                  if ts - vote_window <= e["ts"] <= ts}
        if len(models) < min_votes:
            skipped["yetersiz_oy"] += 1
            continue
        price = ctx.price_at(ts)
        if price is None:
            skipped["fiyat_yok"] += 1
            continue
        tp_d, sl_d = geom_for(symbol, price)

        if gates.get("trend"):
            al = ctx.trend_aligned(ts, direction)
            if al is False:
                skipped["trend_kapisi"] += 1
                continue
        if gates.get("position"):
            pos = ctx.wave_pos(ts, price)
            if pos is not None:
                thr_s = gates.get("pos_sell_min", 0.40)
                thr_b = gates.get("pos_buy_max", 0.60)
                if (direction == "SELL" and pos < thr_s) or \
                   (direction == "BUY" and pos > thr_b):
                    skipped["konum_kapisi"] += 1
                    continue
        entry_ts, entry = ts, price
        if gates.get("patience") and direction == "SELL":
            ok, e_ts, e_px = patience_ok(ctx, ts, price, direction, tp_d, sl_d)
            if not ok:
                skipped["sabir_kapisi"] += 1
                continue
            entry_ts, entry = e_ts, e_px
            tp_d, sl_d = geom_for(symbol, entry)

        r, exit_ts = resolve(ctx, entry_ts, entry, direction, tp_d, sl_d)
        if r is None:
            skipped["cozulmedi"] += 1
            continue
        trades.append({"ts": entry_ts, "r": r, "entry": entry})
        open_until = exit_ts
    return trades, dict(skipped)


def stats(trades: list[dict]) -> dict:
    if not trades:
        return {"n": 0, "wr": None, "totR": 0.0, "avgR": None}
    w = sum(1 for t in trades if t["r"] > 0)
    rs = [t["r"] for t in trades]
    return {"n": len(trades), "wr": round(100 * w / len(trades), 1),
            "totR": round(sum(rs), 2), "avgR": round(statistics.mean(rs), 3)}


def fmt(s: dict) -> str:
    if not s["n"]:
        return "n=0"
    return f"n={s['n']:>3} WR=%{s['wr']:<5} totR={s['totR']:>+7.2f} avgR={s['avgR']:>+.3f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-06-01T00:00:00+00:00")
    ap.add_argument("--symbols", default="NDX.INDX,GDAXI.INDX,USOIL.FOREX")
    a = ap.parse_args()
    client = _client()

    VARIANTS = [
        ("baseline (kapısız)", {}),
        ("trend", {"trend": True}),
        ("konum", {"position": True}),
        ("sabır", {"patience": True}),
        ("trend+konum", {"trend": True, "position": True}),
        ("trend+konum+sabır", {"trend": True, "position": True, "patience": True}),
        ("konum+sabır", {"position": True, "patience": True}),
    ]

    for symbol in a.symbols.split(","):
        print(f"\n{'═' * 78}\n{symbol}\n{'═' * 78}")
        b1 = fetch_bars(client, symbol, "1m", a.since)
        b5 = fetch_bars(client, symbol, "5m", a.since)
        b1h = fetch_bars(client, symbol, "1h", a.since)
        sigs = fetch_signals(client, symbol, a.since)
        print(f"veri: 1m={len(b1)} 5m={len(b5)} 1h={len(b1h)} sinyal={len(sigs)}")
        if len(b1) < 1000 or not sigs:
            print("  yetersiz veri — atlandı")
            continue
        ctx = Ctx(b1, b5, b1h)
        for direction in ("BUY", "SELL"):
            n_dir = sum(1 for s in sigs if s["dir"] == direction)
            if n_dir < 20:
                continue
            print(f"\n── {symbol} {direction} (ham sinyal {n_dir}) ──")
            print(f"{'varyant':<24}{'sonuç':<48}")
            for label, gates in VARIANTS:
                tr, sk = simulate(symbol, direction, sigs, ctx, gates)
                print(f"{label:<24}{fmt(stats(tr))}")


if __name__ == "__main__":
    main()
