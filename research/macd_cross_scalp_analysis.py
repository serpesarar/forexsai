"""
RESEARCH ONLY — MACD sinyal-çizgisi kesişimi scalp analizi. Hiçbir şeye dokunmaz.

Soru: MACD kesişimi (12,26,9) keskin/yönlü kısa vadeli hareketleri öngörüyor mu,
ve kanal-aşırılığı (linreg z-skoru) edge'inin ÜZERİNE bir şey ekliyor mu?

Metodoloji (önceki dürüst bataryalarla aynı disiplin):
  - Veri: RECOVER/ MT5 1m barları (2026-02-11 → 2026-06-12), 4 sembol.
  - Sinyal TF: 5m (1m'den resample). Kesişim 5m kapanışında tespit edilir,
    GİRİŞ bir SONRAKİ 5m barın açılışında (lookahead yok).
  - Sonuç: TP=SL=1.0×ATR14(5m) simetrik scalp; 1m barlarla ilk-temas;
    aynı 1m barda iki taraf da vurulursa LOSS (muhafazakâr).
  - Her 5m bar için BUY ve SELL sonucu ÖNCEDEN hesaplanır → tüm segmentler
    ve placebo aynı sonuç dizisi üzerinde indeks aritmetiği (hız + tutarlılık).
  - Taban: tüm barların koşulsuz WR'si. Placebo: kesişim sayısı kadar rastgele
    bar, 200 tekrar, p95. OOS: 1 Mayıs öncesi/sonrası ayrı raporlanır.
  - Keskinlik: kesişim sonrası 30/60dk |getiri| medyanı vs koşulsuz medyan.
  - Kanal etkileşimi: z(50) linreg; segmentler:
      cross_only, chan_only(|z|>=2 fade), chan+cross_aligned, chan+cross_karşı.

SONUÇ (2026-07-03, Mar-Haz verisi, 4 sembol):
  1. KESKİNLİK YOK: kesişim sonrası 30/60dk |ret| medyanı taban ile aynı
     (oran 0.99-1.05). MACD kesişimi keskin hareket öngörmüyor.
  2. YÖN YOK: cross_only WR her sembolde taban ± gürültü; tek placebo-üstü
     hücre (USOIL BUY %55.7*) IS %60.0 → OOS %49.7 çöküyor = artefakt.
  3. KANALA KATKI YOK: chan_only ile chan_NO_cross birebir aynı; kanal
     aşırılığında AYNI YÖNDE kesişim hiç oluşmuyor (n=0, MACD gecikmesi
     yapısal) — görseldeki "bant + MACD teyidi" 5m'de fiziksel olarak
     kurulamıyor bile.
  KARAR: MACD kesişimi sisteme eklenmeyecek. PLAYBOOK "RSI/MACD tek başına
  zayıf" notu ve multi-asset scalp no-edge bulgusuyla tutarlı.
"""
from __future__ import annotations

import json
import math
import random
import sys
from bisect import bisect_left

DATA = {
    "GDAXI.INDX": "RECOVER/mt5_de40_1m_bars.json",
    "NDX.INDX": "RECOVER/mt5_ustec_1m_bars.json",
    "XAUUSD": "RECOVER/mt5_xauusd_1m_bars.json",
    "USOIL.FOREX": "RECOVER/mt5_xtiusd_1m_bars.json",
}
# tipik roundtrip spread (fiyat birimi) — friction breakeven için
SPREAD = {"GDAXI.INDX": 1.5, "NDX.INDX": 1.8, "XAUUSD": 0.35, "USOIL.FOREX": 0.035}

TF_SEC = 300
ATR_N = 14
CHAN_N = 50
Z_THR = 2.0
MAX_HOLD_1M = 1440          # 24 saat içinde çözülmezse EXPIRE (sayılmaz)
OOS_SPLIT = 1777593600      # 2026-05-01 00:00 UTC
PLACEBO_REPS = 200
SHARP_HORIZONS = (6, 12)    # 5m bar cinsinden 30dk / 60dk


def ema(vals, n):
    k = 2.0 / (n + 1)
    out = [vals[0]]
    for v in vals[1:]:
        out.append(out[-1] + k * (v - out[-1]))
    return out


def load_1m(path):
    d = json.load(open(path))
    bars = d["bars"] if isinstance(d, dict) else d
    bars.sort(key=lambda b: b["t"])
    return bars


def resample_5m(bars_1m):
    out = []
    cur_t = None
    for b in bars_1m:
        t5 = b["t"] - (b["t"] % TF_SEC)
        if t5 != cur_t:
            out.append({"t": t5, "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]})
            cur_t = t5
        else:
            o = out[-1]
            o["h"] = max(o["h"], b["h"])
            o["l"] = min(o["l"], b["l"])
            o["c"] = b["c"]
    return out


def atr14(b5):
    trs = [b5[0]["h"] - b5[0]["l"]]
    for i in range(1, len(b5)):
        h, l, pc = b5[i]["h"], b5[i]["l"], b5[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return ema(trs, ATR_N)


def chan_z(closes, i, n=CHAN_N):
    """Son n kapanışa linreg kanal z-skoru (channel_filter.py ile aynı mantık)."""
    if i + 1 < n:
        return None
    ys = closes[i + 1 - n: i + 1]
    xs = list(range(n))
    mx = (n - 1) / 2.0
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((xs[j] - mx) * (ys[j] - my) for j in range(n))
    slope = sxy / sxx
    resid = [ys[j] - (my + slope * (xs[j] - mx)) for j in range(n)]
    sigma = math.sqrt(sum(r * r for r in resid) / n)
    if sigma <= 0:
        return None
    return resid[-1] / sigma


def precompute_outcomes(b5, atr, bars_1m):
    """Her 5m bar i için: giriş i+1 açılışı, TP/SL=1.0*ATR[i], 1m ilk-temas.
    Dönüş: buy[i], sell[i] ∈ {1,0,None}. None = veri bitti / expire / atr yok."""
    t1 = [b["t"] for b in bars_1m]
    n5 = len(b5)
    buy = [None] * n5
    sell = [None] * n5
    for i in range(n5 - 1):
        d = atr[i]
        if not d or d <= 0 or i < ATR_N:
            continue
        entry_t = b5[i + 1]["t"]
        entry = b5[i + 1]["o"]
        j0 = bisect_left(t1, entry_t)
        if j0 >= len(bars_1m):
            continue
        b_tp, b_sl = entry + d, entry - d
        s_tp, s_sl = entry - d, entry + d
        rb = rs = None
        jmax = min(j0 + MAX_HOLD_1M, len(bars_1m))
        for j in range(j0, jmax):
            h, l = bars_1m[j]["h"], bars_1m[j]["l"]
            if rb is None:
                hit_tp, hit_sl = h >= b_tp, l <= b_sl
                if hit_tp and hit_sl:
                    rb = 0
                elif hit_tp:
                    rb = 1
                elif hit_sl:
                    rb = 0
            if rs is None:
                hit_tp, hit_sl = l <= s_tp, h >= s_sl
                if hit_tp and hit_sl:
                    rs = 0
                elif hit_tp:
                    rs = 1
                elif hit_sl:
                    rs = 0
            if rb is not None and rs is not None:
                break
        buy[i], sell[i] = rb, rs
    return buy, sell


def macd_crosses(closes):
    """i barının KAPANIŞINDA kesin kesişim: diff işareti i-1→i değişti."""
    e12, e26 = ema(closes, 12), ema(closes, 26)
    macd = [a - b for a, b in zip(e12, e26)]
    sig = ema(macd, 9)
    diff = [m - s for m, s in zip(macd, sig)]
    bull, bear = [], []
    for i in range(35, len(diff)):     # warmup
        if diff[i - 1] <= 0 < diff[i]:
            bull.append(i)
        elif diff[i - 1] >= 0 > diff[i]:
            bear.append(i)
    return bull, bear, macd


def wr(idxs, res):
    v = [res[i] for i in idxs if res[i] is not None]
    if not v:
        return None, 0
    return sum(v) / len(v), len(v)


def fmt(w, n):
    return f"{w*100:5.1f}% (n={n})" if w is not None else f"  n/a (n={n})"


def placebo_p95(pool, res, n_pick, reps=PLACEBO_REPS):
    """Havuzdan n_pick rastgele bar, reps kez → WR p95."""
    rng = random.Random(42)
    ws = []
    for _ in range(reps):
        pick = rng.sample(pool, min(n_pick, len(pool)))
        w, n = wr(pick, res)
        if w is not None:
            ws.append(w)
    ws.sort()
    return ws[int(0.95 * len(ws))] if ws else None


def analyze(sym, path):
    bars_1m = load_1m(path)
    b5 = resample_5m(bars_1m)
    closes = [b["c"] for b in b5]
    atr = atr14(b5)
    print(f"\n{'='*74}\n{sym}  1m={len(bars_1m)}  5m={len(b5)}  "
          f"{b5[0]['t']}→{b5[-1]['t']}")

    buy_res, sell_res = precompute_outcomes(b5, atr, bars_1m)
    bull, bear, macd = macd_crosses(closes)
    zs = [chan_z(closes, i) for i in range(len(b5))]

    # ── friction breakeven (TP=SL=d, roundtrip maliyet c → be = (d+c)/2d)
    med_atr = sorted(a for a in atr[ATR_N:] if a)[len(atr) // 2]
    be = (med_atr + SPREAD[sym]) / (2 * med_atr)
    print(f"medyan ATR={med_atr:.3f}  spread={SPREAD[sym]}  "
          f"NET breakeven WR≈{be*100:.1f}%  (brüt %50)")

    # ── keskinlik: kesişim sonrası |getiri| vs koşulsuz
    def med_absret(idxs, h):
        v = [abs(closes[i + h] - closes[i]) / atr[i]
             for i in idxs if i + h < len(closes) and atr[i]]
        v.sort()
        return v[len(v) // 2] if v else None

    all_idx = list(range(CHAN_N, len(b5) - 13))
    for h, lbl in zip(SHARP_HORIZONS, ("30dk", "60dk")):
        base = med_absret(all_idx, h)
        mb = med_absret(bull + bear, h)
        r = (mb / base) if base and mb else None
        print(f"keskinlik {lbl}: kesişim-sonrası |ret| medyan {mb:.2f} ATR vs "
              f"taban {base:.2f} ATR → oran {r:.2f}" if r else
              f"keskinlik {lbl}: veri yetersiz")

    # ── segment tanımları (yön = işlem yönü)
    def fade_dir(i):
        z = zs[i]
        if z is None:
            return None
        if z <= -Z_THR:
            return "BUY"
        if z >= Z_THR:
            return "SELL"
        return None

    segs = {}  # (name, dir) -> idx list
    for i in all_idx:
        fd = fade_dir(i)
        ib, ie = i in set(), None  # placeholder
    bull_s, bear_s = set(bull), set(bear)
    for i in all_idx:
        fd = fade_dir(i)
        if i in bull_s:
            segs.setdefault(("cross_only", "BUY"), []).append(i)
            if fd == "BUY":
                segs.setdefault(("chan+cross_ALIGNED", "BUY"), []).append(i)
            elif fd == "SELL":
                segs.setdefault(("chan+cross_KARSI", "SELL"), []).append(i)
        if i in bear_s:
            segs.setdefault(("cross_only", "SELL"), []).append(i)
            if fd == "SELL":
                segs.setdefault(("chan+cross_ALIGNED", "SELL"), []).append(i)
            elif fd == "BUY":
                segs.setdefault(("chan+cross_KARSI", "BUY"), []).append(i)
        if fd:
            segs.setdefault(("chan_only", fd), []).append(i)
            # kanal-aşırılığı + kesişim TEYİDİ YOK (saf kanal kıyası için)
            if i not in bull_s and i not in bear_s:
                segs.setdefault(("chan_NO_cross", fd), []).append(i)

    # ── rapor: IS (Şub-Nis) / OOS (May-Haz) + taban + placebo
    def report(name, d, idxs):
        res = buy_res if d == "BUY" else sell_res
        is_i = [i for i in idxs if b5[i]["t"] < OOS_SPLIT]
        os_i = [i for i in idxs if b5[i]["t"] >= OOS_SPLIT]
        w_all, n_all = wr(idxs, res)
        w_is, n_is = wr(is_i, res)
        w_os, n_os = wr(os_i, res)
        p95 = placebo_p95(all_idx, res, max(n_all, 1))
        star = " *" if (w_all is not None and p95 is not None and w_all > p95) else ""
        print(f"  {name:24s} {d:4s} TUM {fmt(w_all,n_all)}  "
              f"IS {fmt(w_is,n_is)}  OOS {fmt(w_os,n_os)}  "
              f"placebo_p95 {p95*100:.1f}%{star}" if p95 is not None else
              f"  {name:24s} {d:4s} TUM {fmt(w_all,n_all)}")

    print(f"\n  {'segment':24s} {'yön':4s} (TP=SL=1.0×ATR, brüt WR; "
          f"* = placebo p95 üstü)")
    for d in ("BUY", "SELL"):
        w_base, n_base = wr(all_idx, buy_res if d == "BUY" else sell_res)
        print(f"  {'TABAN (her bar)':24s} {d:4s} TUM {fmt(w_base, n_base)}")
    for (name, d) in sorted(segs):
        report(name, d, segs[(name, d)])


if __name__ == "__main__":
    random.seed(42)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for sym, path in DATA.items():
        if only and only not in sym:
            continue
        analyze(sym, path)
    print("\nBitti. RESEARCH ONLY — hiçbir üretim dosyasına dokunulmadı.")
