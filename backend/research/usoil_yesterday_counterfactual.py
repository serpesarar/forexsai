"""Dünkü (2026-08-09..11) USOIL BREAKOUT işlemleri — kapı ne kurtarırdı, ne kurtarmazdı?

Kullanıcının gözlemi: "USOIL bugün BUY yönünde devam etti (yön doğruydu) ama
5 işlemin 4'ü yanlış GİRİŞ yüzünden kaybetti." Bu betik o iddiayı test eder:

Her gerçek işlem için:
  · aşım (kırılım seviyesinin kaç ATR üstünden alındı)
  · giriş skoru (entry_gate, açılış anına kadarki barlarla — sızıntısız)
  · hangi kapı bloklardı: aşım freni / skor / seans saati / gölge modu
  · KARŞI-OLGUSAL 1: aynı sinyal, giriş kırılım SEVİYESİNDEN (geri çekilme limiti)
  · KARŞI-OLGUSAL 2: aynı giriş, SL'e takılmasa TP'yi görecek miydi (ve ne kadar sonra)
  · KARŞI-OLGUSAL 3: aynı giriş, SL 1.5×/2.0×ATR olsaydı

Çalıştırma (kutuda): python backend/research/usoil_yesterday_counterfactual.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "yeni deneme"))

import MetaTrader5 as mt5  # noqa: E402

from _bars_upto import candles_upto, rates_upto  # noqa: E402
from entry_gate import compute_entry_score  # noqa: E402

SYMBOL = "SpotCrude"
FXS = "USOIL.FOREX"
MAGIC = 52890974
SERVER_UTC_OFFSET = 3
MIN_SCORE = 7
MAX_OVERSHOOT = 0.5
N_DON, N_ATR = 48, 14


def m5_context(when_server: datetime, n: int = 300):
    """Karar anına kadarki KAPALI 5m barlar (sonrası KESİLİR — sızıntı yok)."""
    r = rates_upto(SYMBOL, mt5.TIMEFRAME_M5, when_server, n)
    return r if r is not None and len(r) > 260 else None


def bars_for_gate(when: datetime, tf: int, n: int):
    return candles_upto(SYMBOL, tf, when, n)


def m1_from(when: datetime, minutes: int = 1440):
    a = when - timedelta(minutes=5)
    b = when + timedelta(minutes=minutes)
    r = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M1, a, b)
    return r if r is not None and len(r) else None


def race(m1, start_t: float, entry: float, tp: float, sl: float):
    """(sonuç, dakika) — 'TP' | 'SL' | 'AÇIK'. Aynı barda ikisi de → SL (konservatif)."""
    for x in m1:
        if x["time"] < start_t:
            continue
        hit_tp, hit_sl = x["high"] >= tp, x["low"] <= sl
        if hit_sl:
            return "SL", int((x["time"] - start_t) / 60)
        if hit_tp:
            return "TP", int((x["time"] - start_t) / 60)
    return "AÇIK", None


def main():
    if not mt5.initialize():
        raise SystemExit(f"mt5.initialize() hata: {mt5.last_error()}")
    a = datetime.now() - timedelta(days=3)
    b = datetime.now() + timedelta(days=1)
    deals = [d for d in (mt5.history_deals_get(a, b) or []) if d.magic == MAGIC]
    pos = {}
    for d in deals:
        p = pos.setdefault(d.position_id, {})
        if d.entry == 0:
            p.update(t=d.time, price=d.price, vol=d.volume)
        else:
            p["pnl"] = p.get("pnl", 0.0) + d.profit
            p["exit"] = d.price
    rows = sorted([p for p in pos.values() if "t" in p and "exit" in p], key=lambda p: p["t"])
    print(f"işlem: {len(rows)}  (son 3 gün, magic={MAGIC})\n")

    hdr = (f"{'#':>2} {'UTC':<16}{'dolum':>8}{'seviye':>8}{'aşım':>7}{'skor':>5}"
           f"{'saat':>5}{'gerçek':>8}{'PnL$':>8}   BLOKLAYAN KAPI")
    print(hdr)
    print("-" * len(hdr))
    tot, saved, cf1_win, cf2_win = 0.0, 0.0, 0, 0
    detail = []
    for i, p in enumerate(rows, 1):
        when = datetime.utcfromtimestamp(p["t"])                 # sunucu saati
        utc = when - timedelta(hours=SERVER_UTC_OFFSET)
        r5 = m5_context(when)
        if r5 is None:
            print(f"{i:>2} {str(utc)[:16]:<16}  5m bağlam yok")
            continue
        highs = np.array([float(x["high"]) for x in r5])
        closes = np.array([float(x["close"]) for x in r5])
        lows = np.array([float(x["low"]) for x in r5])
        # kırılım seviyesi = sinyal barından ÖNCEKİ 48 barın en yükseği
        level = highs[-1 - N_DON:-1].max()
        tr = np.maximum(highs[1:] - lows[1:],
                        np.maximum(abs(highs[1:] - closes[:-1]), abs(lows[1:] - closes[:-1])))
        atr = tr[-N_ATR:].mean()
        overshoot = (closes[-1] - level) / atr
        score, fails = compute_entry_score(
            FXS, "BUY", bars_for_gate(when, mt5.TIMEFRAME_M1, 240),
            bars_for_gate(when, mt5.TIMEFRAME_M5, 60),
            bars_for_gate(when, mt5.TIMEFRAME_M30, 60), utc.hour)

        blocks = []
        if overshoot > MAX_OVERSHOOT:
            blocks.append(f"aşım({overshoot:.2f}>{MAX_OVERSHOOT})")
        if score < MIN_SCORE:
            blocks.append(f"skor({score}/8)")
        if 0 <= utc.hour < 12:
            blocks.append(f"seans({utc.hour:02d}UTC)")
        blocks.append("GÖLGE")                                    # bugünkü hâl: hepsi durur

        real = "TP" if p["pnl"] > 0 else "SL"
        tot += p["pnl"]
        if p["pnl"] < 0:
            saved += -p["pnl"]
        print(f"{i:>2} {str(utc)[:16]:<16}{p['price']:>8.3f}{level:>8.3f}{overshoot:>7.2f}"
              f"{score:>5}{utc.hour:>5}{real:>8}{p['pnl']:>8.1f}   {' + '.join(blocks[:-1]) or '—'}")
        detail.append((i, utc, p, level, atr, overshoot, score, fails))

    print(f"\ntoplam: {tot:+.1f}$  (kayıpların toplamı: −{saved:.1f}$)")

    print("\n" + "=" * 78)
    print("KARŞI-OLGUSAL: yön doğruydu da giriş mi kötüydü?")
    print("=" * 78)
    print(f"{'#':>2} {'gerçek':>7} | {'A) seviyeden limit girseydi':<34} | "
          f"{'B) SL yemese TP gelir miydi':<28}")
    for (i, utc, p, level, atr, overshoot, score, fails) in detail:
        when = datetime.utcfromtimestamp(p["t"])
        m1 = m1_from(when, 1440)
        if m1 is None:
            continue
        t0 = p["t"]
        real = "TP" if p["pnl"] > 0 else "SL"

        # A) geri-çekilme limiti: seviye+0.1×ATR, 3 bar (15dk) geçerli
        limit = level + 0.1 * atr
        spread = 0.028
        fill_t = None
        for x in m1:
            if x["time"] < t0 or x["time"] > t0 + 15 * 60:
                continue
            if x["low"] <= limit - spread:
                fill_t = x["time"]; break
        if fill_t is None:
            a_txt = "limit DOLMADI (fiyat geri gelmedi)"
        else:
            res, mins = race(m1, fill_t, limit, limit + atr, limit - atr)
            a_txt = f"dolum {limit:.3f} → {res}" + (f" ({mins}dk)" if mins else "")
            if res == "TP":
                cf1_win += 1

        # B) gerçek girişten TP'ye ulaşma (SL yok sayılarak)
        entry = p["price"]
        tp = entry + atr
        reach = None
        for x in m1:
            if x["time"] >= t0 and x["high"] >= tp:
                reach = int((x["time"] - t0) / 60); break
        b_txt = f"TP {tp:.3f} {reach}dk sonra geldi" if reach else "24s içinde TP gelmedi"
        if reach and real == "SL":
            cf2_win += 1
        print(f"{i:>2} {real:>7} | {a_txt:<34} | {b_txt:<28}")

    print(f"\n  A) seviyeden limit girişle kazanan: {cf1_win}/{len(detail)}")
    print(f"  B) SL'e takılmasa TP'yi görecek olan kaybeden: {cf2_win}")

    print("\n" + "=" * 78)
    print("KARŞI-OLGUSAL: aynı giriş, daha geniş SL")
    print("=" * 78)
    for mult in (1.0, 1.5, 2.0, 3.0):
        wins = losses = 0
        for (i, utc, p, level, atr, overshoot, score, fails) in detail:
            when = datetime.utcfromtimestamp(p["t"])
            m1 = m1_from(when, 1440)
            if m1 is None:
                continue
            e = p["price"]
            res, _ = race(m1, p["t"], e, e + atr, e - mult * atr)
            if res == "TP":
                wins += 1
            elif res == "SL":
                losses += 1
        n = wins + losses
        print(f"  SL={mult}×ATR (TP=1×ATR): {wins}K/{losses}Z  WR={100*wins/n if n else 0:.0f}%  "
              f"→ R toplamı {wins*1.0 - losses*mult:+.1f}R")
    print("\nBITTI")


if __name__ == "__main__":
    main()
