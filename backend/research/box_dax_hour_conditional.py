"""box_dax_hour_conditional.py — DAX saat etkisinin KOŞULLU taban-oran testi.

Neden bu script var: `box_dax_hour_baserate.py` saat kalitesini KOŞULSUZ ölçtü
(her trend-hizalı barda giriş). DAX raporunun ERRATA'sı haklı bir itiraz getirdi:
iddia "o saatlerde piyasa kötü" değil, "**botun sinyali** o saatlerde kötü"ydi.
İkisi mantıken bağdaşabilir — bu script farkı kapatır.

Burada botun GERÇEK momentum-continuation koşulları bar-bar uygulanır ve yalnız
o koşulların hepsini sağlayan barlarda hipotetik giriş açılır:

  1. M15 Stochastic %K(14) > 70              (bot_router.MOMENTUM_FILTER)
  2. M15 dist(close, EMA20) / ATR14 > 0.8    (aynı)
  3. 1h close > EMA50                        (bot: _trend_gate_blocks)
  4. 4h dalga konumu ≤ 0.60                  (bot: _position_gate_blocks, BUY)

Geometri botun DAX ayarı: TP 67 puan sabit, SL = 2.0×ATR14(5m), 30-120 kırpılı.
Sızıntı yok: her gösterge yalnız giriş barından ÖNCEKİ barlardan hesaplanır.

Çalıştırma (kutuda): python backend/research/box_dax_hour_conditional.py
"""
from __future__ import annotations

import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok — bu script MT5 kutusunda çalışır.")

import config  # type: ignore

SYM = "GER40"
TP_FIXED = 67.0
SL_MULT, SL_MIN, SL_MAX = 2.0, 30.0, 120.0
MAX_HOLD_5M = 288
STOCH_MIN = 70.0
STRETCH_MIN = 0.8
POS_BUY_MAX = 0.60


def server_to_utc(epoch: int) -> datetime:
    naive = datetime(1970, 1, 1) + timedelta(seconds=int(epoch))
    try:
        from zoneinfo import ZoneInfo
        return naive.replace(tzinfo=ZoneInfo("Europe/Athens")).astimezone(timezone.utc)
    except Exception:
        return naive.replace(tzinfo=timezone.utc) - timedelta(minutes=180)


def connect() -> bool:
    kw = {}
    if getattr(config, "MT5_ACCOUNT", None):
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                  server=config.MT5_SERVER)
    path = getattr(config, "MT5_TERMINAL_PATH", "")
    return bool(mt5.initialize(path, **kw) if path else mt5.initialize(**kw))


def bars(tf, n):
    r = mt5.copy_rates_from_pos(SYM, tf, 0, n)
    if r is None:
        return [], []
    b = [{"t": int(x["time"]), "high": float(x["high"]), "low": float(x["low"]),
          "close": float(x["close"])} for x in r]
    return b, [x["t"] for x in b]


def atr(seg):
    if len(seg) < 15:
        return None
    trs = [max(seg[j]["high"] - seg[j]["low"],
               abs(seg[j]["high"] - seg[j - 1]["close"]),
               abs(seg[j]["low"] - seg[j - 1]["close"])) for j in range(1, len(seg))]
    return sum(trs) / len(trs) if trs else None


def stoch_k(seg, period=14):
    """Stochastic %K — seg son bar DAHİL (giriş barından önceki barlar verilir)."""
    if len(seg) < period:
        return None
    w = seg[-period:]
    hi = max(x["high"] for x in w)
    lo = min(x["low"] for x in w)
    if hi <= lo:
        return None
    return 100.0 * (w[-1]["close"] - lo) / (hi - lo)


def ema_series(b, period):
    k = 2.0 / (period + 1)
    e = b[0]["close"]
    out = {}
    for x in b:
        e = x["close"] * k + e * (1 - k)
        out[x["t"]] = e
    return out


def main() -> None:
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    mt5.symbol_select(SYM, True)

    b5, t5 = bars(mt5.TIMEFRAME_M5, 99000)
    b15, t15 = bars(mt5.TIMEFRAME_M15, 40000)
    b1h, t1h = bars(mt5.TIMEFRAME_H1, 20000)
    if not b5 or not b15 or not b1h:
        sys.exit("bar alinamadi")
    print(f"{SYM}: 5m={len(b5)}  15m={len(b15)}  1h={len(b1h)}")
    print(f"  {server_to_utc(b5[0]['t']):%Y-%m-%d} → {server_to_utc(b5[-1]['t']):%Y-%m-%d}")

    ema20_15 = ema_series(b15, 20)
    ema50_1h = ema_series(b1h, 50)

    by_hour = defaultdict(lambda: [0, 0, 0.0])
    by_dow = defaultdict(lambda: [0, 0, 0.0])
    total = [0, 0, 0.0]
    checked = passed = 0

    for i in range(60, len(b5) - MAX_HOLD_5M):
        bar = b5[i]
        checked += 1
        # ── koşul 3: 1h EMA50 üstü ──
        j1 = bisect_left(t1h, bar["t"]) - 1
        if j1 < 50:
            continue
        e50 = ema50_1h.get(t1h[j1])
        if e50 is None or bar["close"] <= e50:
            continue
        # ── koşul 1+2: M15 stoch ve EMA20 gerilmesi ──
        j15 = bisect_left(t15, bar["t"]) - 1
        if j15 < 30:
            continue
        seg15 = b15[max(0, j15 - 30):j15 + 1]
        k = stoch_k(seg15)
        a15 = atr(seg15)
        e20 = ema20_15.get(t15[j15])
        if k is None or a15 is None or e20 is None or a15 <= 0:
            continue
        if k <= STOCH_MIN:
            continue
        if (seg15[-1]["close"] - e20) / a15 <= STRETCH_MIN:
            continue
        # ── koşul 4: 4h dalga konumu ≤0.60 (48×5m) ──
        w = b5[i - 48:i]
        hi = max(x["high"] for x in w); lo = min(x["low"] for x in w)
        if hi <= lo:
            continue
        pos = (bar["close"] - lo) / (hi - lo)
        if pos > POS_BUY_MAX:
            continue
        # ── geometri ──
        a5 = atr(b5[max(0, i - 15):i])
        if not a5 or a5 <= 0:
            continue
        passed += 1
        sl_d = min(max(SL_MULT * a5, SL_MIN), SL_MAX)
        tp, sl = bar["close"] + TP_FIXED, bar["close"] - sl_d
        res = None
        for x in b5[i + 1:i + 1 + MAX_HOLD_5M]:
            if x["low"] <= sl:
                res = -sl_d; break
            if x["high"] >= tp:
                res = TP_FIXED; break
        if res is None:
            continue
        u = server_to_utc(bar["t"])
        win = 1 if res > 0 else 0
        for d in (by_hour[u.hour], by_dow[u.isoweekday()], total):
            d[0] += 1; d[1] += win; d[2] += res

    if not total[0]:
        sys.exit("kosullari saglayan giris bulunamadi")
    base_wr = 100 * total[1] / total[0]
    print(f"\ntaranan 5m bar: {checked}  ·  botun 4 kosulunu saglayan: {passed}")
    print(f"cozulmus hipotetik giris: {total[0]}  WR=%{base_wr:.1f}  "
          f"islem basi {total[2]/total[0]:+.2f} puan")

    print("\n── SAAT BAZINDA (UTC) — botun sinyal kosullariyla ──")
    print(f"{'saat':<6}{'n':<7}{'WR':<9}{'islem basi':<14}{'baz farki'}")
    for h in sorted(by_hour):
        n, w, net = by_hour[h]
        if n < 15:
            continue
        wr = 100 * w / n
        mark = "  ← RAPOR BLOK" if h in (8, 11, 12) else ""
        print(f"{h:02d}    {n:<7}%{wr:<8.1f}{net/n:<+14.2f}{wr-base_wr:+.1f}pp{mark}")

    print("\n── GÜN BAZINDA ──")
    gun = {1: "Pzt", 2: "Sal", 3: "Car", 4: "Per", 5: "Cum"}
    for d in sorted(by_dow):
        n, w, net = by_dow[d]
        if n < 15:
            continue
        wr = 100 * w / n
        mark = "  ← RAPOR BLOK" if d == 2 else ""
        print(f"{gun.get(d, d):<6}{n:<7}%{wr:<8.1f}{net/n:<+14.2f}{wr-base_wr:+.1f}pp{mark}")

    bn = bw = 0; bnet = 0.0
    kn = kw_ = 0; knet = 0.0
    for h in by_hour:
        n, w, net = by_hour[h]
        if h in (8, 11, 12):
            bn += n; bw += w; bnet += net
        else:
            kn += n; kw_ += w; knet += net
    print("\n── RAPORUN BLOK SAATLERİ (8/11/12) vs DİĞERLERİ ──")
    if bn and kn:
        print(f"  blok saatler : n={bn:<6} WR=%{100*bw/bn:.1f}  islem basi {bnet/bn:+.2f} puan")
        print(f"  diger saatler: n={kn:<6} WR=%{100*kw_/kn:.1f}  islem basi {knet/kn:+.2f} puan")
    tn, tw, tnet = by_dow.get(2, [0, 0, 0.0])
    on = sum(by_dow[d][0] for d in by_dow if d != 2)
    ow = sum(by_dow[d][1] for d in by_dow if d != 2)
    onet = sum(by_dow[d][2] for d in by_dow if d != 2)
    if tn and on:
        print(f"  Salı         : n={tn:<6} WR=%{100*tw/tn:.1f}  islem basi {tnet/tn:+.2f} puan")
        print(f"  diger gunler : n={on:<6} WR=%{100*ow/on:.1f}  islem basi {onet/on:+.2f} puan")
    mt5.shutdown()


if __name__ == "__main__":
    main()
