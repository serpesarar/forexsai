"""
Gösterge Olay Taraması — indicator_snapshots üzerinde dürüst batarya.

data_recorder'ın biriktirdiği 1m gösterge kayıtlarındaki OLAYLARI (kesişim /
eşik aşımı) tarar ve her birinin scalp ayrıştırıcı gücünü ölçer:
  - Sonuç: giriş SONRAKİ 1m barın açılışında, TP=SL=1.0×ATR14, ilk-temas;
    aynı barda çift temas = LOSS (muhafazakâr). Lookahead YOK.
  - Kontroller: her-bar taban WR, 200× placebo p95, zaman bazlı %70/%30
    IS/OOS ayrımı, olay başına ≥5 bar dedup (örtüşen örneklem şişmesin).
  - Veri boşluğu korumaları: >5dk sonraki bar yoksa giriş atlanır; çözüm
    penceresinde >10dk boşluk varsa sonuç sayılmaz.

Kullanım (bot makinesinde, calistir/15_gosterge_tarama.bat):
  python indicator_event_scan.py                  # tüm semboller, tüm veri
  python indicator_event_scan.py --symbol XAU     # tek sembol
  python indicator_event_scan.py --days 14        # son 14 gün

Okuma amaçlı — hiçbir tabloya yazmaz, üretime dokunmaz.
Referans metodoloji: research/macd_cross_scalp_analysis.py (2026-07-03,
MACD kesişimi bu bataryadan geçemedi — yeni adaylar da aynı çıtadan geçmeli).
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import requests

try:
    import decider_config as cfg
except ImportError:
    cfg = None

SYMBOLS = ["NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX"]
PAGE = 1000
MAX_HOLD = 240          # 1m bar; 4 saatte çözülmezse sayma
ENTRY_GAP_S = 300       # giriş barı 5dk'dan uzaksa atla
RESOLVE_GAP_S = 600     # çözüm penceresinde >10dk boşluk = sayma
DEDUP_BARS = 5
PLACEBO_REPS = 200
MIN_N = 30              # bunun altı "veri az" uyarısı
OOS_FRAC = 0.30


def creds():
    url = (getattr(cfg, "SUPABASE_URL", "") or os.getenv("SUPABASE_URL", "")).strip()
    key = (getattr(cfg, "SUPABASE_SERVICE_KEY", "")
           or os.getenv("SUPABASE_SERVICE_KEY", "")
           or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
           or os.getenv("SUPABASE_KEY", "")).strip()
    if not url or not key:
        print("HATA: SUPABASE_URL/SUPABASE_SERVICE_KEY yok (decider_config veya env).")
        sys.exit(1)
    return url.rstrip("/"), key


def fetch_rows(url, key, symbol, since_iso):
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}
    rows, offset = [], 0
    while True:
        q = (f"{url}/rest/v1/indicator_snapshots"
             f"?symbol=eq.{symbol}&timeframe=eq.1m"
             f"&candle_time=gte.{since_iso}"
             f"&select=candle_time,open,high,low,close,ind"
             f"&order=candle_time.asc&limit={PAGE}&offset={offset}")
        r = requests.get(q, headers=hdr, timeout=30)
        r.raise_for_status()
        batch = r.json()
        rows.extend(batch)
        if len(batch) < PAGE:
            return rows
        offset += PAGE


def parse(rows):
    """→ paralel diziler: t(epoch), o/h/l/c, ind listesi."""
    t, o, h, l, c, ind = [], [], [], [], [], []
    for r in rows:
        try:
            ts = datetime.fromisoformat(r["candle_time"].replace("Z", "+00:00"))
        except (ValueError, KeyError):
            continue
        t.append(ts.timestamp())
        o.append(r["open"]); h.append(r["high"]); l.append(r["low"]); c.append(r["close"])
        ind.append(r.get("ind") or {})
    return t, o, h, l, c, ind


def precompute(t, o, h, l, ind):
    """Her bar i için BUY/SELL sonucu (1=TP, 0=SL, None=çözümsüz/boşluk)."""
    n = len(t)
    buy, sell = [None] * n, [None] * n
    for i in range(n - 1):
        atr = (ind[i] or {}).get("atr14")
        if not atr or atr <= 0 or t[i + 1] - t[i] > ENTRY_GAP_S:
            continue
        e = o[i + 1]
        b_tp, b_sl, s_tp, s_sl = e + atr, e - atr, e - atr, e + atr
        rb = rs = None
        for j in range(i + 1, min(i + 1 + MAX_HOLD, n)):
            if j > i + 1 and t[j] - t[j - 1] > RESOLVE_GAP_S:
                break  # boşluk — çözülmemiş taraflar None kalır
            if rb is None:
                tp, sl = h[j] >= b_tp, l[j] <= b_sl
                rb = 0 if (tp and sl) else (1 if tp else (0 if sl else None))
            if rs is None:
                tp, sl = l[j] <= s_tp, h[j] >= s_sl
                rs = 0 if (tp and sl) else (1 if tp else (0 if sl else None))
            if rb is not None and rs is not None:
                break
        buy[i], sell[i] = rb, rs
    return buy, sell


def g(ind, i, k):
    v = (ind[i] or {}).get(k)
    return v if isinstance(v, (int, float)) and v == v else None


def events(t, c, ind):
    """(olay_adı, yön) → bar indeksleri. Kesişimler i-1→i geçişiyle tanımlı."""
    out = {}

    def add(name, d, i):
        key = (name, d)
        lst = out.setdefault(key, [])
        if not lst or i - lst[-1] >= DEDUP_BARS:
            lst.append(i)

    for i in range(1, len(c)):
        if t[i] - t[i - 1] > ENTRY_GAP_S:
            continue  # boşluk sonrası ilk bar — önceki barla kıyas anlamsız
        p, q = ind[i - 1] or {}, ind[i] or {}

        def pv(k):
            v = p.get(k)
            return v if isinstance(v, (int, float)) and v == v else None

        m0, s0 = pv("macd"), pv("macd_signal")
        m1, s1 = g(ind, i, "macd"), g(ind, i, "macd_signal")
        if None not in (m0, s0, m1, s1):
            if m0 - s0 <= 0 < m1 - s1:
                add("macd_kesisim", "BUY", i)
            elif m0 - s0 >= 0 > m1 - s1:
                add("macd_kesisim", "SELL", i)

        r0, r1 = pv("rsi14"), g(ind, i, "rsi14")
        if None not in (r0, r1):
            if r0 < 30 <= r1:
                add("rsi_30_yukari", "BUY", i)
            if r0 > 70 >= r1:
                add("rsi_70_asagi", "SELL", i)
        if r1 is not None:
            if r1 < 25:
                add("rsi_asiri<25_fade", "BUY", i)
            if r1 > 75:
                add("rsi_asiri>75_fade", "SELL", i)

        k0, d0 = pv("stoch_k"), pv("stoch_d")
        k1, d1 = g(ind, i, "stoch_k"), g(ind, i, "stoch_d")
        if None not in (k0, d0, k1, d1):
            if k0 - d0 <= 0 < k1 - d1 and k1 < 25:
                add("stoch_dip_kesisim", "BUY", i)
            elif k0 - d0 >= 0 > k1 - d1 and k1 > 75:
                add("stoch_tepe_kesisim", "SELL", i)

        b0, b1 = pv("bb_pct_b"), g(ind, i, "bb_pct_b")
        if b1 is not None:
            if b1 < 0:
                add("bb_alt_tasma_fade", "BUY", i)
            if b1 > 1:
                add("bb_ust_tasma_fade", "SELL", i)
        if None not in (b0, b1):
            if b0 < 0 <= b1:
                add("bb_alt_geri_giris", "BUY", i)
            if b0 > 1 >= b1:
                add("bb_ust_geri_giris", "SELL", i)

        z1 = g(ind, i, "vwap_z")
        if z1 is not None:
            if z1 <= -1.5:
                add("vwap_z_fade", "BUY", i)
            if z1 >= 1.5:
                add("vwap_z_fade", "SELL", i)

        sar0, sar1 = pv("sar"), g(ind, i, "sar")
        if None not in (sar0, sar1):
            if c[i - 1] - sar0 <= 0 < c[i] - sar1:
                add("sar_flip", "BUY", i)
            elif c[i - 1] - sar0 >= 0 > c[i] - sar1:
                add("sar_flip", "SELL", i)

        a0, a1 = pv("adx14"), g(ind, i, "adx14")
        pdi, mdi = g(ind, i, "plus_di"), g(ind, i, "minus_di")
        if None not in (a0, a1, pdi, mdi) and a0 < 25 <= a1:
            add("adx25_kirilim", "BUY" if pdi > mdi else "SELL", i)

        e0, e1 = pv("ema20"), g(ind, i, "ema20")
        if None not in (e0, e1):
            if c[i - 1] - e0 <= 0 < c[i] - e1:
                add("ema20_kesisim", "BUY", i)
            elif c[i - 1] - e0 >= 0 > c[i] - e1:
                add("ema20_kesisim", "SELL", i)

        de = g(ind, i, "dist_ema20_atr")
        if de is not None:
            if de <= -2:
                add("ema20_uzak_fade", "BUY", i)
            if de >= 2:
                add("ema20_uzak_fade", "SELL", i)
    return out


def wr(idxs, res):
    v = [res[i] for i in idxs if res[i] is not None]
    return (sum(v) / len(v), len(v)) if v else (None, 0)


def scan_symbol(url, key, symbol, since_iso):
    rows = fetch_rows(url, key, symbol, since_iso)
    t, o, h, l, c, ind = parse(rows)
    if len(t) < 500:
        print(f"\n{symbol}: {len(t)} bar — tarama için çok az, atlandı.")
        return
    days = (t[-1] - t[0]) / 86400
    buy, sell = precompute(t, o, h, l, ind)
    valid = [i for i in range(len(t)) if buy[i] is not None or sell[i] is not None]
    wb, nb = wr(valid, buy)
    ws, ns = wr(valid, sell)
    print(f"\n{'='*76}\n{symbol}  bar={len(t)}  kapsam={days:.1f} gün  "
          f"TABAN: BUY {wb*100:.1f}% / SELL {ws*100:.1f}% (n={nb})")
    if days < 30:
        print("  UYARI: <30 gün veri — sonuçlar İŞARET niteliğinde, karar için erken.")

    split_t = t[0] + (t[-1] - t[0]) * (1 - OOS_FRAC)
    rng = random.Random(42)

    def placebo_p95(res, n_pick):
        pool = [i for i in valid if res[i] is not None]
        ws_ = []
        for _ in range(PLACEBO_REPS):
            pk = rng.sample(pool, min(n_pick, len(pool)))
            w, _n = wr(pk, res)
            if w is not None:
                ws_.append(w)
        ws_.sort()
        return ws_[int(0.95 * len(ws_))] if ws_ else None

    results = []
    for (name, d), idxs in events(t, c, ind).items():
        res = buy if d == "BUY" else sell
        w_all, n_all = wr(idxs, res)
        if w_all is None:
            continue
        w_is, n_is = wr([i for i in idxs if t[i] < split_t], res)
        w_os, n_os = wr([i for i in idxs if t[i] >= split_t], res)
        p95 = placebo_p95(res, n_all)
        edge = (w_all - p95) if p95 is not None else 0.0
        results.append((edge, name, d, w_all, n_all, w_is, n_is, w_os, n_os, p95))

    results.sort(reverse=True)
    print(f"  {'olay':22s} {'yön':4s} {'TUM':>14s} {'IS':>14s} {'OOS':>14s} "
          f"{'p95':>6s} işaret")
    for edge, name, d, w_all, n_all, w_is, n_is, w_os, n_os, p95 in results:
        def f(w, n):
            return f"{w*100:5.1f}% n={n:<5d}" if w is not None else f"  n/a n={n:<5d}"
        flags = []
        if p95 is not None and w_all > p95:
            flags.append("*plasebo-üstü")
        if w_os is not None and n_os >= 10 and w_os < 0.50:
            flags.append("OOS-zayıf")
        if n_all < MIN_N:
            flags.append("veri-az")
        print(f"  {name:22s} {d:4s} {f(w_all,n_all):>14s} {f(w_is,n_is):>14s} "
              f"{f(w_os,n_os):>14s} {p95*100 if p95 else 0:5.1f}% "
              f"{' '.join(flags)}")
    print("  Çıta: *plasebo-üstü + OOS>=50 + n>=30 birlikte sağlanmadan aday bile değil.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default=None, help="sembol filtresi (örn XAU)")
    ap.add_argument("--days", type=int, default=0, help="son N gün (0=tümü)")
    args = ap.parse_args()
    url, key = creds()
    since = (datetime.now(timezone.utc) - timedelta(days=args.days or 3650)
             ).strftime("%Y-%m-%dT%H:%M:%SZ")
    for sym in SYMBOLS:
        if args.symbol and args.symbol.upper() not in sym.upper():
            continue
        try:
            scan_symbol(url, key, sym, since)
        except requests.RequestException as e:
            print(f"\n{sym}: veri çekilemedi — {e}")
    print("\nBitti. Salt-okuma tarama — hiçbir tabloya yazılmadı.")


if __name__ == "__main__":
    main()
