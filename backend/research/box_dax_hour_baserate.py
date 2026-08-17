"""box_dax_hour_baserate.py — DAX saat/gün etkisinin BÜYÜK ÖRNEKLEMDE sınanması.

Soru: DAX raporunun "08/11/12 UTC + Salı zehirli" bulgusu 47 işlemden geldi.
Bu saatlerde YAPISAL bir dezavantaj var mı, yoksa küçük örneklem gürültüsü mü?

Yöntem: botun DAX geometrisiyle (TP 67 puan sabit, SL = 2.0×ATR14(5m), 30-120
bandına kırpılı — `ATR_GEOMETRY_DEFAULT["GDAXI.INDX:BUY"]`) her 5m barda
hipotetik bir BUY girişi açılır ve 5m barlarla bar-bar çözülür. Botun trend
kapısını taklit etmek için yalnız fiyat 1h EMA50 ÜSTÜNDEyken giriş yapılır
(bot da öyle yapıyor). Sonuç saat ve güne göre kırılır.

Bu binlerce örnek üretir → saat etkisi gerçekse görünür, değilse görünmez.
Sızıntı yok: ATR ve EMA yalnız giriş barından ÖNCEKİ barlardan hesaplanır.

Çalıştırma (kutuda): python backend/research/box_dax_hour_baserate.py
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
STEP = 3                     # her 3. 5m barda bir giriş (örtüşmeyi azaltır)
MAX_HOLD = 288               # 24 saat (5m bar)


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


def atr14(bars, i):
    """ATR14 — i barından ÖNCEKİ 15 bar (sızıntısız)."""
    seg = bars[max(0, i - 15):i]
    if len(seg) < 15:
        return None
    trs = []
    for j in range(1, len(seg)):
        h, l, pc = seg[j]["high"], seg[j]["low"], seg[j - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs) / len(trs) if trs else None


def main() -> None:
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    mt5.symbol_select(SYM, True)

    r5 = mt5.copy_rates_from_pos(SYM, mt5.TIMEFRAME_M5, 0, 99000)
    r1h = mt5.copy_rates_from_pos(SYM, mt5.TIMEFRAME_H1, 0, 20000)
    if r5 is None or r1h is None:
        sys.exit("bar alinamadi")
    b5 = [{"t": int(x["time"]), "o": float(x["open"]), "high": float(x["high"]),
           "low": float(x["low"]), "close": float(x["close"])} for x in r5]
    h1 = [{"t": int(x["time"]), "close": float(x["close"])} for x in r1h]
    h1t = [b["t"] for b in h1]
    print(f"{SYM}: 5m bar={len(b5)}  1h bar={len(h1)}")
    print(f"  {server_to_utc(b5[0]['t']):%Y-%m-%d} → {server_to_utc(b5[-1]['t']):%Y-%m-%d}")

    # 1h EMA50 serisi
    k = 2.0 / 51.0
    ema = h1[0]["close"]
    ema_at = {}
    for b in h1:
        ema = b["close"] * k + ema * (1 - k)
        ema_at[b["t"]] = ema

    by_hour = defaultdict(lambda: [0, 0, 0.0])     # [n, win, net_puan]
    by_dow = defaultdict(lambda: [0, 0, 0.0])
    total = [0, 0, 0.0]

    for i in range(20, len(b5) - MAX_HOLD, STEP):
        bar = b5[i]
        a = atr14(b5, i)
        if not a or a <= 0:
            continue
        # trend kapısı: fiyat 1h EMA50 üstünde (bot da böyle filtreliyor)
        j = bisect_left(h1t, bar["t"]) - 1
        if j < 0:
            continue
        e = ema_at.get(h1t[j])
        entry = bar["close"]
        if e is None or entry <= e:
            continue

        sl_d = min(max(SL_MULT * a, SL_MIN), SL_MAX)
        tp, sl = entry + TP_FIXED, entry - sl_d
        res = None
        for b in b5[i + 1:i + 1 + MAX_HOLD]:
            if b["low"] <= sl:
                res = -sl_d; break
            if b["high"] >= tp:
                res = TP_FIXED; break
        if res is None:
            continue
        u = server_to_utc(bar["t"])
        win = 1 if res > 0 else 0
        for d in (by_hour[u.hour], by_dow[u.isoweekday()], total):
            d[0] += 1; d[1] += win; d[2] += res

    print(f"\ntoplam hipotetik giris: {total[0]}  WR=%{100*total[1]/total[0]:.1f}  "
          f"net={total[2]:+.0f} puan  (islem basi {total[2]/total[0]:+.1f} puan)")
    base_wr = 100 * total[1] / total[0]

    print("\n── SAAT BAZINDA (UTC) ──")
    print(f"{'saat':<6}{'n':<7}{'WR':<9}{'islem basi puan':<18}{'baz farki'}")
    for h in sorted(by_hour):
        n, w, net = by_hour[h]
        if n < 50:
            continue
        wr = 100 * w / n
        mark = "  ← RAPOR BLOK" if h in (8, 11, 12) else ""
        print(f"{h:02d}    {n:<7}%{wr:<8.1f}{net/n:<+18.2f}{wr-base_wr:+.1f}pp{mark}")

    print("\n── GÜN BAZINDA ──")
    gun = {1: "Pzt", 2: "Sal", 3: "Car", 4: "Per", 5: "Cum"}
    for d in sorted(by_dow):
        n, w, net = by_dow[d]
        if n < 50:
            continue
        wr = 100 * w / n
        mark = "  ← RAPOR BLOK" if d == 2 else ""
        print(f"{gun.get(d, d):<6}{n:<7}%{wr:<8.1f}{net/n:<+18.2f}{wr-base_wr:+.1f}pp{mark}")

    blok_n = blok_w = 0; blok_net = 0.0
    kalan_n = kalan_w = 0; kalan_net = 0.0
    for h in by_hour:
        n, w, net = by_hour[h]
        if h in (8, 11, 12):
            blok_n += n; blok_w += w; blok_net += net
        else:
            kalan_n += n; kalan_w += w; kalan_net += net
    print(f"\n── RAPORUN BLOK SAATLERİ (8/11/12) vs DİĞERLERİ ──")
    print(f"  blok saatler : n={blok_n:<6} WR=%{100*blok_w/blok_n:.1f}  "
          f"işlem başı {blok_net/blok_n:+.2f} puan")
    print(f"  diğer saatler: n={kalan_n:<6} WR=%{100*kalan_w/kalan_n:.1f}  "
          f"işlem başı {kalan_net/kalan_n:+.2f} puan")
    mt5.shutdown()


if __name__ == "__main__":
    main()
