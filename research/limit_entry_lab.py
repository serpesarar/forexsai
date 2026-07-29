#!/usr/bin/env python3
"""limit_entry_lab.py — LİMİT EMİRLE GİRİŞ: market yerine geri çekilmeden sat.

Neden: market girişinin kenarı spread + kayma kadar. Bugün canlıda 14 puan kayma
gözlendi. SELL LİMİT emri (a) daha iyi fiyattan doldurur, (b) girişte kayma yemez
— karşılığında (c) HER ZAMAN DOLMAZ ve (d) hemen kaçan (yani en iyi) işlemleri
ıskalayabilir. Bu dosya dördünü birlikte ölçer.

Model: barlar BID. SELL LİMİT L'de → bid L'ye yükselince dolar (high >= L), fiyat
tam L. Çıkışta ask'ten alınır → spread çıkışa gömülü (market versiyonuyla AYNI).
Yani buradaki tek avantaj daha iyi giriş fiyatı; kayma avantajı MODELLENMEDİ
(gerçekte ek artı). Dolum barında SL de mümkünse KAYIP sayılır (konservatif).
"""
from datetime import datetime, timezone
import numpy as np
import lab_vol_tpsl_grid as G

H = 72
LOT = 5.0


def main():
    t, o, h, l, c, v = G.load_csv("nas100_m5.csv")
    n = len(c)
    atr = G.wilder_atr(h, l, c)
    cut = t[int(n * 0.7)]

    def events(confirm):
        out = []
        for i in range(G.ATR_PERIOD + 5, n - H - 20):
            a = atr[i]
            if not np.isfinite(a) or a <= 0:
                continue
            body = o[i] - c[i]; rng_ = h[i] - l[i]
            if rng_ <= 0 or body <= 0 or body < a or body / rng_ < 0.55:
                continue
            if confirm == "red" and not (c[i + 1] < o[i + 1]):
                continue
            if confirm == "lowbreak" and not (c[i + 1] < l[i]):
                continue
            out.append((i, a))
        return out

    def market(e, tp_d, sl_d, spread):
        px = c[e]
        tp_px, sl_px = px - tp_d, px + sl_d
        end = min(e + H, n - 1)
        for j in range(e + 1, end + 1):
            if h[j] >= sl_px - spread:
                return "LOSS", px - sl_px
            if l[j] <= tp_px - spread:
                return "WIN", px - tp_px
        return "TIME", px - c[end] - spread

    def limit(e, L, expiry, tp_d, sl_d, spread, same_bar=True):
        fill = None
        for j in range(e + 1, min(e + expiry, n - 1) + 1):
            if h[j] >= L:
                fill = j
                break
        if fill is None:
            return None
        tp_px, sl_px = L - tp_d, L + sl_d
        start = fill if same_bar else fill + 1
        end = min(fill + H, n - 1)
        for j in range(start, end + 1):
            if h[j] >= sl_px - spread:
                return "LOSS", L - sl_px, fill - e
            if l[j] <= tp_px - spread:
                return "WIN", L - tp_px, fill - e
        return "TIME", L - c[end] - spread, fill - e

    def stats(rows, n_signal, label):
        """rows = [(outcome, net)]; n_signal = toplam sinyal (dolmayanlar dahil)"""
        if not rows:
            print(f"  {label:<40} dolum yok")
            return None
        net = np.asarray([r[1] for r in rows], dtype=float)
        fill_pct = 100.0 * len(rows) / n_signal
        tp = 100.0 * sum(1 for r in rows if r[0] == "WIN") / len(rows)
        sl = 100.0 * sum(1 for r in rows if r[0] == "LOSS") / len(rows)
        ev_fill = float(net.mean())
        ev_sig = float(net.sum() / n_signal)
        print(f"  {label:<40}{len(rows):>6}{fill_pct:>8.1f}{tp:>7.1f}{sl:>7.1f}"
              f"{ev_fill:>+9.2f}{ev_sig:>+10.2f}{net.sum() * LOT:>+11,.0f}")
        return {"n": len(rows), "fill": fill_pct, "tp": tp, "ev_fill": ev_fill,
                "ev_sig": ev_sig, "usd": float(net.sum() * LOT)}

    GEOS = [("TP80/SL30", 80.0, 30.0), ("TP120/SL25", 120.0, 25.0),
            ("TP80/SL110 (canlı)", 80.0, 110.0)]
    OFFSETS = [("market (offset 0)", 0.0), ("+0.10×ATR", 0.10), ("+0.20×ATR", 0.20),
               ("+0.30×ATR", 0.30), ("+0.50×ATR", 0.50), ("+0.75×ATR", 0.75),
               ("+1.00×ATR", 1.00)]
    EXPIRIES = (1, 2, 3, 6, 12)
    SPREAD = 1.5

    for confirm in ("lowbreak", "red"):
        evs = events(confirm)
        print("\n" + "=" * 118)
        print(f"LİMİT GİRİŞ — teyit={confirm} · n={len(evs):,} sinyal · spread={SPREAD} · "
              f"ufuk {H} bar · lot {LOT}")
        print("  'EV/sinyal' = dolmayanlar 0 sayılarak sinyal başına beklenti (asıl ölçüt)")
        print("=" * 118)
        for gname, tp_d, sl_d in GEOS:
            print(f"\n▸ {gname}")
            print(f"  {'giriş / geçerlilik':<40}{'n':>6}{'dolum%':>8}{'TP%':>7}{'SL%':>7}"
                  f"{'EV/işlem':>9}{'EV/sinyal':>10}{'$':>11}")
            rows_m = [market(e + 1, tp_d, sl_d, SPREAD) for e, a in evs]
            stats(rows_m, len(evs), "MARKET (teyit mumu kapanışı)")
            for oname, off in OFFSETS[1:]:
                for exp in EXPIRIES:
                    rows = []
                    for i, a in evs:
                        e = i + 1
                        r = limit(e, c[e] + off * a, exp, tp_d, sl_d, SPREAD)
                        if r:
                            rows.append((r[0], r[1]))
                    stats(rows, len(evs), f"{oname} / {exp} bar geçerli")

    # ── odak: en iyi konfigürasyonun kör testi + ters seçilim + kayma ──────
    evs = events("lowbreak")
    print("\n" + "=" * 118)
    print("ODAK — teyit=lowbreak, TP80/SL30: KÖR TEST · TERS SEÇİLİM · KAYMA")
    print("=" * 118)
    tp_d, sl_d = 80.0, 30.0
    for off, exp in ((0.20, 3), (0.30, 3), (0.30, 6), (0.50, 6), (0.50, 12)):
        for tag, want_train in (("EĞİTİM", True), ("TEST  ", False)):
            sub = [(i, a) for i, a in evs if (t[i] < cut) == want_train]
            rows = []
            for i, a in sub:
                e = i + 1
                r = limit(e, c[e] + off * a, exp, tp_d, sl_d, SPREAD)
                if r:
                    rows.append((r[0], r[1]))
            print(f"  {tag} ", end="")
            stats(rows, len(sub), f"+{off:.2f}×ATR / {exp} bar")

    print("\nTERS SEÇİLİM — limit dolmayan sinyaller market'te ne yapardı? (+0.30×ATR / 6 bar)")
    filled, missed = [], []
    for i, a in evs:
        e = i + 1
        r = limit(e, c[e] + 0.30 * a, 6, tp_d, sl_d, SPREAD)
        m = market(e, tp_d, sl_d, SPREAD)
        (filled if r else missed).append(m[1])
    print(f"  DOLAN sinyaller  n={len(filled):>5}  market'te EV={np.mean(filled):+.2f} p")
    print(f"  IŞKALANANLAR     n={len(missed):>5}  market'te EV={np.mean(missed):+.2f} p"
          f"  ← bu belirgin (+) ise limit iyi işlemleri kaçırıyor")

    print("\nKAYMA/FRİKSİYON DAYANIKLILIĞI (+0.30×ATR / 6 bar, TP80/SL30)")
    print(f"  {'spread':<10}{'n':>6}{'dolum%':>8}{'TP%':>7}{'SL%':>7}{'EV/işlem':>9}"
          f"{'EV/sinyal':>10}{'$':>11}")
    for sp in (1.5, 3.0, 5.0, 8.0):
        rows = []
        for i, a in evs:
            e = i + 1
            r = limit(e, c[e] + 0.30 * a, 6, tp_d, sl_d, sp)
            if r:
                rows.append((r[0], r[1]))
        stats(rows, len(evs), f"spread {sp}")
    print("  (market karşılaştırması aynı spread'lerde:)")
    for sp in (1.5, 3.0, 5.0, 8.0):
        rows = [market(i + 1, tp_d, sl_d, sp) for i, a in evs]
        stats(rows, len(evs), f"MARKET spread {sp}")

    print("\nDOLUM BARI VARSAYIMI (konservatif vs iyimser) — +0.30×ATR / 6 bar")
    for same, tag in ((True, "konservatif (dolum barında SL sayılır)"),
                      (False, "iyimser (çözüm sonraki bardan)")):
        rows = []
        for i, a in evs:
            e = i + 1
            r = limit(e, c[e] + 0.30 * a, 6, tp_d, sl_d, SPREAD, same_bar=same)
            if r:
                rows.append((r[0], r[1]))
        stats(rows, len(evs), tag)

    print("\nÇEYREKLİK (+0.30×ATR / 6 bar, TP80/SL30)")
    byq = {}
    for i, a in evs:
        e = i + 1
        r = limit(e, c[e] + 0.30 * a, 6, tp_d, sl_d, SPREAD)
        d = datetime.fromtimestamp(int(t[i]), tz=timezone.utc)
        q = f"{d.year}Ç{(d.month - 1) // 3 + 1}"
        byq.setdefault(q, {"rows": [], "sig": 0})
        byq[q]["sig"] += 1
        if r:
            byq[q]["rows"].append((r[0], r[1]))
    for q in sorted(byq):
        stats(byq[q]["rows"], byq[q]["sig"], q)


if __name__ == "__main__":
    main()
