"""box_m1_oos.py — M1 sinyalinin ("güç tepesinde BUY") derin örneklemde sınanması.

İddia: wave15(32×15m) ≥ 0.85 VE close > EMA50(4H) → BUY · n=38 WR %73.7 +5.700$

Panel tarafı (33.353 adet 1m bar / 1 ay) sonucu:
  · yeniden üretim  : n=41 WR %68.3 +4.050$  (iddiaya yakın ✓)
  · eşik platosu    : 0.75→0.95 arası hep %67-72 / +3.700…+5.800$  ✓ gerçek plato
  · KOŞULSUZ kontrol: "EMA4H üstünde BUY" n=104 WR %56.7 −1.150$ → M1 net geçiyor ✓
  · koşullu plasebo : p=0.102 ❌ %5 eşiğini geçemedi (sınırda)

Bu script aynı kuralı MT5'in DERİN geçmişinde (99.000 adet 1m bar ≈ 68 gün, ya
da 5m ile ~1 yıl) koşar. Örneklem büyüdüğünde plasebo kapısı geçilirse kural
canlıya alınabilir; geçilmezse gölgede kalır.

M2 (wave≤0.15 + EMA4H altı → SELL) bu scripte ALINMADI: panel tarafında
yeniden üretilemedi (iddia %97.2 / gerçek %52.2) ve koşullu plaseboyu p=0.910
ile kaybetti — yani rastgeleden kötü.

Çalıştırma (kutuda): python backend/research/box_m1_oos.py --split 2026-07-13
"""
from __future__ import annotations

import argparse
import random
import sys
from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok — bu script MT5 kutusunda çalışır.")

import config  # type: ignore

SYM = "NAS100"
LOT, TP_PT, SL_PT = 5.0, 80.0, 110.0
random.seed(53)


def s2u(e):
    naive = datetime(1970, 1, 1) + timedelta(seconds=int(e))
    try:
        from zoneinfo import ZoneInfo
        return naive.replace(tzinfo=ZoneInfo("Europe/Athens")).astimezone(timezone.utc)
    except Exception:
        return naive.replace(tzinfo=timezone.utc) - timedelta(minutes=180)


def connect():
    kw = {}
    if getattr(config, "MT5_ACCOUNT", None):
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                  server=config.MT5_SERVER)
    p = getattr(config, "MT5_TERMINAL_PATH", "")
    return bool(mt5.initialize(p, **kw) if p else mt5.initialize(**kw))


def bars(tf, n):
    r = mt5.copy_rates_from_pos(SYM, tf, 0, n)
    if r is None:
        return []
    return [{"t": int(x["time"]), "h": float(x["high"]), "l": float(x["low"]),
             "c": float(x["close"])} for x in r]


def ema_map(b, period):
    k = 2.0 / (period + 1)
    e = b[0]["c"]; out = {}
    for x in b:
        e = x["c"] * k + e * (1 - k)
        out[x["t"]] = e
    return out


def resolve(b5, i0, entry, direction, max_bars=600):
    sgn = 1 if direction == "BUY" else -1
    tp, sl = entry + sgn * TP_PT, entry - sgn * SL_PT
    for x in b5[i0:i0 + max_bars]:
        hit_sl = (x["l"] <= sl) if sgn > 0 else (x["h"] >= sl)
        hit_tp = (x["h"] >= tp) if sgn > 0 else (x["l"] <= tp)
        if hit_sl:
            return {"pnl": -SL_PT * LOT, "win": False}
        if hit_tp:
            return {"pnl": TP_PT * LOT, "win": True}
    return None


def stats(rows):
    if not rows:
        return 0, 0.0, 0.0
    return len(rows), 100 * sum(1 for r in rows if r["win"]) / len(rows), sum(r["pnl"] for r in rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="2026-07-13")
    ap.add_argument("--mode", default="m1", choices=["m1", "m2"],
                    help="m1: wave>=esik + EMA4H ustu -> BUY | "
                         "m2: wave<=esik + EMA4H alti -> SELL")
    a = ap.parse_args()
    M2 = a.mode == "m2"
    YON = "SELL" if M2 else "BUY"
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    split = datetime.fromisoformat(a.split).replace(tzinfo=timezone.utc)
    mt5.symbol_select(SYM, True)

    b5 = bars(mt5.TIMEFRAME_M5, 99000)
    b15 = bars(mt5.TIMEFRAME_M15, 40000)
    b4 = bars(mt5.TIMEFRAME_H4, 6000)
    if not b5 or not b15 or not b4:
        sys.exit("bar alinamadi")
    print(f"{SYM}: 5m={len(b5)} 15m={len(b15)} 4h={len(b4)}")
    print(f"  {s2u(b5[0]['t']):%Y-%m-%d} → {s2u(b5[-1]['t']):%Y-%m-%d}\n")

    t15 = [x["t"] for x in b15]; t4 = [x["t"] for x in b4]
    ema4 = ema_map(b4, 50)

    # her 5m bar için (wave15, ema4h_ustu) — sızıntısız: KAPANMIŞ barlar
    ctx = {}
    for i, x in enumerate(b5):
        j = bisect_right(t15, x["t"]) - 1
        if j < 33:
            continue
        w = b15[j - 32:j]
        hi = max(y["h"] for y in w); lo = min(y["l"] for y in w)
        if hi <= lo:
            continue
        k = bisect_right(t4, x["t"]) - 1
        if k < 51:
            continue
        e = ema4.get(t4[k])
        if e is None:
            continue
        ctx[i] = ((x["c"] - lo) / (hi - lo), x["c"] > e)

    def tara(esik, ustu=None, cooldown=60):
        if ustu is None:
            ustu = not M2
        out = []; son = None
        for i in sorted(ctx):
            wave, above = ctx[i]
            u = s2u(b5[i]["t"])
            if u.isoweekday() == 5 or not (7 <= u.hour < 20):
                continue
            if above != ustu:
                continue
            if (wave > esik) if M2 else (wave < esik):
                continue
            if son and (b5[i]["t"] - son) < cooldown * 60:
                continue
            r = resolve(b5, i, b5[i]["c"], YON)
            if r:
                r["utc"] = u; out.append(r); son = b5[i]["t"]
        return out

    ANA_ESIK = 0.15 if M2 else 0.85
    tum = tara(ANA_ESIK)
    dis = [r for r in tum if r["utc"] < split]
    ic = [r for r in tum if r["utc"] >= split]
    print(f"1) {'M2 (wave≤0.15 + EMA4H altı → SELL)' if M2 else 'M1 (wave≥0.85 + EMA4H üstü → BUY)'}")
    for ad, rows in (("TÜM DÖNEM", tum), ("DIŞ-ÖRNEKLEM", dis), ("İÇ-ÖRNEKLEM", ic)):
        n, wr, p = stats(rows)
        print(f"   {ad:<16} n={n:<5} WR=%{wr:5.1f} {p:>+9.0f}$")

    print("\n2) EŞİK PLATOSU (tüm dönem)")
    for th in ((0.10, 0.15, 0.20, 0.25, 0.30) if M2 else (0.75, 0.80, 0.85, 0.90, 0.95)):
        n, wr, p = stats(tara(th))
        print(f"   wave{'≤' if M2 else '≥'}{th:.2f}  n={n:<5} WR=%{wr:5.1f} {p:>+9.0f}$")

    print(f"\n3) KOŞULSUZ KONTROL — 'EMA4H {'altında SELL' if M2 else 'üstünde BUY'}' (wave şartı YOK)")
    ks = tara(1.0 if M2 else 0.0)
    n, wr, p = stats(ks)
    print(f"   n={n:<5} WR=%{wr:5.1f} {p:>+9.0f}$  ← M1 bunu geçmeli")

    print(f"\n4) KOŞULLU PLASEBO — EMA4H {'altında' if M2 else 'üstünde'} RASTGELE anlarda {YON}")
    havuz = [i for i in ctx if ctx[i][1] != M2
             and s2u(b5[i]["t"]).isoweekday() != 5
             and 7 <= s2u(b5[i]["t"]).hour < 20]
    print(f"   havuz: {len(havuz)} bar")
    for ad, rows in (("TÜM DÖNEM", tum), ("DIŞ-ÖRNEKLEM", dis)):
        n_o, wr_o, p_o = stats(rows)
        if n_o < 10:
            continue
        sim = []
        for _ in range(400):
            tot = 0.0
            for _ in range(n_o):
                i = random.choice(havuz)
                r = resolve(b5, i, b5[i]["c"], YON)
                if r:
                    tot += r["pnl"]
            sim.append(tot)
        sim.sort()
        pv = sum(1 for x in sim if x >= p_o) / len(sim)
        print(f"   {ad:<14} M1={p_o:+.0f}$ · plasebo medyan {sim[len(sim)//2]:+.0f}$ "
              f"→ p={pv:.3f} {'✅' if pv < 0.05 else '❌'}")

    mt5.shutdown()


if __name__ == "__main__":
    main()
