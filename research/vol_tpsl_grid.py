#!/usr/bin/env python3
"""vol_tpsl_grid.py — HACİM × TP/SL GRID: büyük düşüş mumundan SONRAKİ mumda açılan
SELL'in en yüksek başarı oranını veren koşul + geometri kombinasyonunu arar.

Kullanıcı isteği (2026-07-28): "mumların hacimlerini ve TP/SL seviyelerini oynayarak
en yüksek başarı oranına sahip ... belki belirli bir hacim lazım, belki hacme dayalı
TP/SL seviyeleri lazım."

TASARIM
  * Giriş HER ZAMAN 2. mumun (teyit mumu) kapanışında — kullanıcının tarifi.
  * Hacim kovaları: sinyal mumunun hacmi / önceki 20 barın ortalaması (causal).
    Ayrıca teyit mumunun hacmi ve hacim ivmesi ayrı boyut olarak taranır.
  * TP/SL gridi hem ATR katları hem sabit puan olarak.
  * BAŞABAŞ DÜZELTMESİ: ham WR yanıltıcıdır (küçük TP + geniş SL = yüksek WR, eksi EV).
    Her hücrede WR ile başabaş-WR = SL/(TP+SL) farkı raporlanır. Asıl ölçüt bu fark.
  * ÇOKLU TEST DÜRÜSTLÜĞÜ: grid 1000+ hücre tarar → tesadüfen iyi görünen hücre
    kesin çıkar. Bu yüzden (a) sıralama YALNIZ eğitim setinde, (b) kazananların kör
    test sonucu, (c) tüm gridde eğitim↔test korelasyonu ve hayatta kalma oranı
    şansla karşılaştırmalı olarak yazılır.

Sızıntı: göstergeler yalnız kapanmış barlardan; çözüm girişten SONRAKİ barlarla;
aynı barda TP+SL → KAYIP; spread tetik koşullarına gömülü.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone

import numpy as np

ATR_PERIOD = 14
VOL_WINDOW = 20
SPREAD = 1.5
HORIZON = 72
LOT = 5.0
MIN_N_TRAIN = 150
TOP_SHOW = 15

TP_MULTS = (0.25, 0.4, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0)
SL_MULTS = (0.4, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0)
TP_POINTS = (20, 30, 40, 50, 60, 80, 100, 130)
SL_POINTS = (30, 40, 50, 70, 90, 110, 150, 200)


def load_csv(path):
    t, o, h, l, c, v = [], [], [], [], [], []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t.append(int(float(row["time"]))); o.append(float(row["open"]))
            h.append(float(row["high"])); l.append(float(row["low"]))
            c.append(float(row["close"])); v.append(float(row["vol"]))
    return (np.asarray(t), np.asarray(o), np.asarray(h),
            np.asarray(l), np.asarray(c), np.asarray(v))


def wilder_atr(high, low, close, period=ATR_PERIOD):
    n = len(close)
    tr = np.empty(n)
    tr[0] = high[0] - low[0]
    prev = close[:-1]
    tr[1:] = np.maximum(high[1:] - low[1:],
                        np.maximum(np.abs(high[1:] - prev), np.abs(low[1:] - prev)))
    atr = np.full(n, np.nan)
    atr[period] = tr[1:period + 1].mean()
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


class Book:
    """Olay defteri + vektörize TP/SL değerlendirici."""

    def __init__(self, entry, atr_e, ts, LO, HI, close_end):
        self.entry, self.atr, self.ts = entry, atr_e, ts
        self.LO, self.HI, self.close_end = LO, HI, close_end

    def evaluate(self, idx, tp_dist, sl_dist):
        """tp_dist/sl_dist: her olay için mesafe dizisi (puan). Dönen: (net, risk)."""
        e = self.entry[idx]
        tp_px = e - tp_dist
        sl_px = e + sl_dist
        hit_tp = self.LO[idx] <= (tp_px - SPREAD)[:, None]
        hit_sl = self.HI[idx] >= (sl_px - SPREAD)[:, None]
        any_tp, any_sl = hit_tp.any(1), hit_sl.any(1)
        big = self.LO.shape[1] + 1
        j_tp = np.where(any_tp, hit_tp.argmax(1), big)
        j_sl = np.where(any_sl, hit_sl.argmax(1), big)
        win = any_tp & (j_tp < j_sl)
        loss = any_sl & (j_sl <= j_tp)
        net = np.where(win, e - tp_px, np.where(loss, e - sl_px,
                                                e - self.close_end[idx] - SPREAD))
        return net, sl_dist, win, loss


def cell_stats(net, risk, win, loss, tp_dist, sl_dist):
    n = len(net)
    if n == 0:
        return None
    rr = net / risk
    be = float(np.mean(sl_dist / (tp_dist + sl_dist))) * 100.0   # başabaş WR (%)
    return {"n": n, "wr": 100.0 * float((net > 0).mean()),
            "tp_rate": 100.0 * float(win.mean()), "sl_rate": 100.0 * float(loss.mean()),
            "ev_r": float(rr.mean()), "ev_p": float(net.mean()),
            "usd": float(net.sum() * LOT), "be": be,
            "edge": 100.0 * float(win.mean()) - be}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="nas100_m5.csv")
    ap.add_argument("--body-atr", type=float, default=1.0)
    ap.add_argument("--body-ratio", type=float, default=0.55)
    ap.add_argument("--confirm", default="lowbreak",
                    choices=["none", "red", "lowbreak"],
                    help="2. mum koşulu: yok / kırmızı / 1. mumun dibini kırdı")
    args = ap.parse_args()

    t, o, h, l, c, v = load_csv(args.csv)
    n = len(c)
    atr = wilder_atr(h, l, c)
    vmean = np.full(n, np.nan)
    for i in range(VOL_WINDOW, n):
        vmean[i] = v[i - VOL_WINDOW:i].mean()

    rows = []
    for i in range(VOL_WINDOW + ATR_PERIOD + 2, n - HORIZON - 3):
        a = atr[i]
        if not np.isfinite(a) or a <= 0 or not np.isfinite(vmean[i]) or vmean[i] <= 0:
            continue
        body = o[i] - c[i]
        rng_ = h[i] - l[i]
        if rng_ <= 0 or body <= 0 or body < args.body_atr * a or body / rng_ < args.body_ratio:
            continue
        if args.confirm == "red" and not (c[i + 1] < o[i + 1]):
            continue
        if args.confirm == "lowbreak" and not (c[i + 1] < l[i]):
            continue
        rows.append((i, a, v[i] / vmean[i], v[i + 1] / vmean[i + 1], v[i + 1] / max(v[i], 1.0)))

    m = len(rows)
    H = HORIZON
    entry = np.empty(m); atr_e = np.empty(m); ts = np.empty(m, dtype=np.int64)
    vol1 = np.empty(m); vol2 = np.empty(m); vacc = np.empty(m)
    LO = np.empty((m, H)); HI = np.empty((m, H)); close_end = np.empty(m)
    for k, (i, a, v1, v2, va) in enumerate(rows):
        e = i + 1                                   # giriş barı = 2. mum
        entry[k] = c[e]; atr_e[k] = a; ts[k] = t[i]
        vol1[k] = v1; vol2[k] = v2; vacc[k] = va
        seg_lo = l[e + 1:e + 1 + H]; seg_hi = h[e + 1:e + 1 + H]
        LO[k] = np.minimum.accumulate(seg_lo)
        HI[k] = np.maximum.accumulate(seg_hi)
        close_end[k] = c[e + H]
    book = Book(entry, atr_e, ts, LO, HI, close_end)

    cut = t[int(n * 0.7)]
    is_train = ts < cut
    print("=" * 122)
    print(f"HACİM × TP/SL GRID — NAS100 5m · giriş: 2. mumun kapanışı · teyit={args.confirm}")
    print(f"olay n={m:,} · eğitim={int(is_train.sum()):,} / kör test={int((~is_train).sum()):,} "
          f"(kesim {datetime.fromtimestamp(int(cut), tz=timezone.utc):%Y-%m-%d}) · "
          f"spread={SPREAD}p · zaman-stopu {H} bar · lot {LOT}")
    print("  'edge' = TP-isabet% − başabaş% (asıl ölçüt; ham WR küçük TP ile şişer)")
    print("=" * 122)

    VOL_BUCKETS = [("hepsi", 0.0, 99.0), ("hacim <0.9× (sakin)", 0.0, 0.9),
                   ("hacim 0.9–1.2×", 0.9, 1.2), ("hacim 1.2–1.5×", 1.2, 1.5),
                   ("hacim 1.5–2.0×", 1.5, 2.0), ("hacim ≥2.0× (patlama)", 2.0, 99.0)]

    # ── 1) tam grid: hacim kovası × TP × SL ────────────────────────────────
    grid = []
    for bname, blo, bhi in VOL_BUCKETS:
        base = (vol1 >= blo) & (vol1 < bhi)
        for tp_m in TP_MULTS:
            for sl_m in SL_MULTS:
                for split, mask in (("train", base & is_train), ("test", base & ~is_train)):
                    idx = np.where(mask)[0]
                    if len(idx) == 0:
                        continue
                    tp_d = tp_m * atr_e[idx]; sl_d = sl_m * atr_e[idx]
                    net, risk, win, loss = book.evaluate(idx, tp_d, sl_d)
                    st = cell_stats(net, risk, win, loss, tp_d, sl_d)
                    grid.append({"bucket": bname, "tp": tp_m, "sl": sl_m,
                                 "split": split, **st})
    tr = {(g["bucket"], g["tp"], g["sl"]): g for g in grid if g["split"] == "train"}
    te = {(g["bucket"], g["tp"], g["sl"]): g for g in grid if g["split"] == "test"}

    cand = [k for k, g in tr.items() if g["n"] >= MIN_N_TRAIN and g["ev_r"] > 0]
    print(f"\n[1] EĞİTİMDE +EV olan hücre: {len(cand)} / {len(tr)} "
          f"(n≥{MIN_N_TRAIN} şartıyla)")

    print(f"\n[2] EĞİTİMDE EN YÜKSEK 'edge' (TP% − başabaş%) → KÖR TEST sonucu")
    print(f"  {'hacim kovası':<24}{'TP×ATR':>7}{'SL×ATR':>7}"
          f"{'| EĞİTİM n':>11}{'WR%':>7}{'TP%':>7}{'edge':>7}{'EV(R)':>8}"
          f"{'| TEST n':>9}{'WR%':>7}{'TP%':>7}{'edge':>7}{'EV(R)':>8}{'$':>11}")
    for k in sorted(cand, key=lambda k: -tr[k]["edge"])[:TOP_SHOW]:
        a_, b_ = tr[k], te.get(k)
        if not b_ or b_["n"] < 40:
            continue
        print(f"  {k[0]:<24}{k[1]:>7.2f}{k[2]:>7.2f}"
              f"{a_['n']:>11}{a_['wr']:>7.1f}{a_['tp_rate']:>7.1f}{a_['edge']:>+7.1f}{a_['ev_r']:>+8.3f}"
              f"{b_['n']:>9}{b_['wr']:>7.1f}{b_['tp_rate']:>7.1f}{b_['edge']:>+7.1f}"
              f"{b_['ev_r']:>+8.3f}{b_['usd']:>+11,.0f}")

    print(f"\n[3] HER HACİM KOVASININ KENDİ EN İYİ TP/SL'i (eğitimde seçildi → kör testte ölçüldü)")
    print("     = 'hacme dayalı TP/SL' sorusunun doğrudan cevabı")
    print(f"  {'hacim kovası':<24}{'en iyi TP/SL':>14}{'| EĞİTİM n':>11}{'TP%':>7}{'edge':>7}{'EV(R)':>8}"
          f"{'| TEST n':>9}{'TP%':>7}{'edge':>7}{'EV(R)':>8}{'$':>11}")
    for bname, _lo, _hi in VOL_BUCKETS:
        ks = [k for k in cand if k[0] == bname]
        if not ks:
            print(f"  {bname:<24}  (eğitimde +EV hücre yok)")
            continue
        k = max(ks, key=lambda k: tr[k]["edge"])
        a_, b_ = tr[k], te.get(k)
        tail = (f"{b_['n']:>9}{b_['tp_rate']:>7.1f}{b_['edge']:>+7.1f}{b_['ev_r']:>+8.3f}"
                f"{b_['usd']:>+11,.0f}") if b_ and b_["n"] >= 25 else "   (test n<25)"
        print(f"  {bname:<24}{f'{k[1]:.2f}/{k[2]:.2f}':>14}{a_['n']:>11}"
              f"{a_['tp_rate']:>7.1f}{a_['edge']:>+7.1f}{a_['ev_r']:>+8.3f}{tail}")

    # ── 4) sabit puan gridi (canlı bot geometrisi bu birimde) ──────────────
    print(f"\n[4] SABİT PUAN GRİDİ (bot bu birimi kullanıyor) — 'hepsi' kovası")
    best = []
    for tp_p in TP_POINTS:
        for sl_p in SL_POINTS:
            res = {}
            for split, mask in (("train", is_train), ("test", ~is_train)):
                idx = np.where(mask)[0]
                tp_d = np.full(len(idx), float(tp_p)); sl_d = np.full(len(idx), float(sl_p))
                net, risk, win, loss = book.evaluate(idx, tp_d, sl_d)
                res[split] = cell_stats(net, risk, win, loss, tp_d, sl_d)
            if res["train"]["n"] >= MIN_N_TRAIN:
                best.append((res["train"]["edge"], tp_p, sl_p, res))
    best.sort(reverse=True)
    print(f"  {'TP/SL (puan)':<14}{'| EĞİTİM TP%':>14}{'edge':>7}{'EV(R)':>8}"
          f"{'| TEST TP%':>12}{'edge':>7}{'EV(R)':>8}{'$':>11}")
    for _e, tp_p, sl_p, res in best[:8]:
        a_, b_ = res["train"], res["test"]
        print(f"  {f'{tp_p}/{sl_p}':<14}{a_['tp_rate']:>14.1f}{a_['edge']:>+7.1f}{a_['ev_r']:>+8.3f}"
              f"{b_['tp_rate']:>12.1f}{b_['edge']:>+7.1f}{b_['ev_r']:>+8.3f}{b_['usd']:>+11,.0f}")
    ref = [x for x in best if x[1] == 80 and x[2] == 110]
    if ref:
        a_, b_ = ref[0][3]["train"], ref[0][3]["test"]
        print(f"  {'80/110 (canlı)':<14}{a_['tp_rate']:>14.1f}{a_['edge']:>+7.1f}{a_['ev_r']:>+8.3f}"
              f"{b_['tp_rate']:>12.1f}{b_['edge']:>+7.1f}{b_['ev_r']:>+8.3f}{b_['usd']:>+11,.0f}")

    # ── 5) ÇOKLU TEST DÜRÜSTLÜK TESTİ ─────────────────────────────────────
    print(f"\n[5] GRID GERÇEKTEN BİR ŞEY BULUYOR MU? (çoklu-test dürüstlük kontrolü)")
    pairs = [(tr[k]["ev_r"], te[k]["ev_r"]) for k in tr
             if k in te and tr[k]["n"] >= MIN_N_TRAIN and te[k]["n"] >= 40]
    if len(pairs) > 10:
        a_arr = np.asarray([p[0] for p in pairs]); b_arr = np.asarray([p[1] for p in pairs])
        r = float(np.corrcoef(a_arr, b_arr)[0, 1])
        base_pos = 100.0 * float((b_arr > 0).mean())
        surv = [b for a, b in pairs if a > 0]
        surv_rate = 100.0 * float(np.mean(np.asarray(surv) > 0)) if surv else float("nan")
        print(f"  karşılaştırılan hücre: {len(pairs)}")
        print(f"  eğitim EV ↔ test EV korelasyonu: r = {r:+.3f}   "
              f"(r≈0 → grid gürültü madenciliği yapıyor)")
        print(f"  TÜM hücrelerde testte +EV oranı: %{base_pos:.0f}  ← şans çıtası")
        print(f"  EĞİTİMDE +EV olanların testte +EV kalma oranı: %{surv_rate:.0f}")
        print(f"  → fark {surv_rate - base_pos:+.0f} puan. Belirgin pozitif değilse seçim işe yaramıyor.")

    # ── 8) TABAN KARŞILAŞTIRMASI — kurgu mu kötü, dönem mi short'a düşman? ─
    print(f"\n[8] TABAN FARKI — aynı geometriyle KOŞULSUZ SELL (her 6. bar) ile karşılaştırma")
    bidx = [i for i in range(VOL_WINDOW + ATR_PERIOD + 2, n - HORIZON - 3, 6)
            if np.isfinite(atr[i]) and atr[i] > 0]
    bm = len(bidx)
    b_entry = np.empty(bm); b_atr = np.empty(bm); b_ts = np.empty(bm, dtype=np.int64)
    b_LO = np.empty((bm, H)); b_HI = np.empty((bm, H)); b_ce = np.empty(bm)
    for k, i in enumerate(bidx):
        b_entry[k] = c[i]; b_atr[k] = atr[i]; b_ts[k] = t[i]
        b_LO[k] = np.minimum.accumulate(l[i + 1:i + 1 + H])
        b_HI[k] = np.maximum.accumulate(h[i + 1:i + 1 + H])
        b_ce[k] = c[i + H]
    bbook = Book(b_entry, b_atr, b_ts, b_LO, b_HI, b_ce)
    b_train = b_ts < cut

    def ev_of(bk, idx, tp_mult, sl_mult, atr_arr, points=False):
        if len(idx) < 25:
            return None
        tp_d = (np.full(len(idx), tp_mult) if points else tp_mult * atr_arr[idx])
        sl_d = (np.full(len(idx), sl_mult) if points else sl_mult * atr_arr[idx])
        net, risk, win, loss = bk.evaluate(idx, tp_d, sl_d)
        return cell_stats(net, risk, win, loss, tp_d, sl_d)

    GEOS_CMP = [("ATR 2.0/3.0", 2.0, 3.0, False), ("ATR 3.0/4.0", 3.0, 4.0, False),
                ("ATR 1.0/1.0", 1.0, 1.0, False), ("puan 80/110 (canlı)", 80.0, 110.0, True),
                ("puan 80/30", 80.0, 30.0, True)]
    print(f"  {'geometri':<22}{'| EĞİTİM kurgu':>15}{'taban':>9}{'FARK':>9}"
          f"{'| TEST kurgu':>14}{'taban':>9}{'FARK':>9}")
    for gname, a_m, b_m2, pts in GEOS_CMP:
        line = f"  {gname:<22}"
        for want_train in (True, False):
            s = ev_of(book, np.where(is_train == want_train)[0], a_m, b_m2, atr_e, pts)
            b = ev_of(bbook, np.where(b_train == want_train)[0], a_m, b_m2, b_atr, pts)
            if s and b:
                line += f"{s['ev_r']:>+15.3f}{b['ev_r']:>+9.3f}{s['ev_r'] - b['ev_r']:>+9.3f}"
            else:
                line += f"{'-':>15}{'-':>9}{'-':>9}"
        print(line)
    print("  → FARK sütunu iki dönemde de belirgin (+) ise koşulun kendi katkısı var;")
    print("    ikisi de ≈0 ise kurgunun taşıdığı bilgi yok, sonuçlar rejimin.")

    # ── 7) İSTİKRAR SEÇİMİ (aşırı-uyuma karşı asıl panzehir) ──────────────
    print(f"\n[7] İSTİKRAR SEÇİMİ — 'en iyi hücre' yerine 'her çeyrekte tutan hücre'")
    print("     eğitim çeyreklerinin ≥%75'inde +EV + n≥150 → sonra KÖR TEST")
    qid = np.asarray([(datetime.fromtimestamp(int(x), tz=timezone.utc).year * 4 +
                       (datetime.fromtimestamp(int(x), tz=timezone.utc).month - 1) // 3)
                      for x in ts])
    stable = []
    for bname, blo, bhi in VOL_BUCKETS:
        base = (vol1 >= blo) & (vol1 < bhi)
        for tp_m in TP_MULTS:
            for sl_m in SL_MULTS:
                idx = np.where(base & is_train)[0]
                if len(idx) < MIN_N_TRAIN:
                    continue
                tp_d = tp_m * atr_e[idx]; sl_d = sl_m * atr_e[idx]
                net, risk, win, loss = book.evaluate(idx, tp_d, sl_d)
                rr = net / risk
                qs = qid[idx]
                good = tot = 0
                for q in np.unique(qs):
                    sel = qs == q
                    if sel.sum() < 25:
                        continue
                    tot += 1
                    good += int(rr[sel].mean() > 0)
                if tot >= 3 and good / tot >= 0.75 and rr.mean() > 0:
                    stable.append((bname, tp_m, sl_m, good, tot, float(rr.mean()), len(idx)))
    print(f"  istikrarlı hücre sayısı: {len(stable)} / {len(tr)}")
    if stable:
        print(f"  {'hacim kovası':<24}{'TP/SL':>12}{'çeyrek':>9}{'| EĞİTİM n':>11}{'EV(R)':>8}"
              f"{'| TEST n':>9}{'WR%':>7}{'TP%':>7}{'edge':>7}{'EV(R)':>8}{'$':>11}")
        surv_n = 0
        for bname, tp_m, sl_m, good, tot, ev_tr, n_tr in sorted(stable, key=lambda x: -x[5])[:12]:
            k = (bname, tp_m, sl_m)
            b_ = te.get(k)
            if b_ and b_["n"] >= 25:
                surv_n += int(b_["ev_r"] > 0)
                tail = (f"{b_['n']:>9}{b_['wr']:>7.1f}{b_['tp_rate']:>7.1f}"
                        f"{b_['edge']:>+7.1f}{b_['ev_r']:>+8.3f}{b_['usd']:>+11,.0f}")
            else:
                tail = "   (test n<25)"
            print(f"  {bname:<24}{f'{tp_m:.2f}/{sl_m:.2f}':>12}{f'{good}/{tot}':>9}"
                  f"{n_tr:>11}{ev_tr:>+8.3f}{tail}")
        print(f"  → istikrarlı hücrelerden kör testte +EV kalan: {surv_n}")

    # ── 6) hacim ivmesi ve teyit mumunun hacmi ────────────────────────────
    print(f"\n[6] HACİM YÖNÜ — 'hangi hacim deseni?' (en iyi ATR geometrisi sabit tutularak)")
    if cand:
        kbest = max(cand, key=lambda k: tr[k]["edge"])
        tp_m, sl_m = kbest[1], kbest[2]
        print(f"  geometri sabit: TP {tp_m}×ATR / SL {sl_m}×ATR (eğitim kazananı)")
        DIMS = [("teyit mumu hacmi ≥1.2×", vol2 >= 1.2),
                ("teyit mumu hacmi <1.2×", vol2 < 1.2),
                ("hacim ARTIYOR (2.mum>1.mum)", vacc >= 1.0),
                ("hacim DÜŞÜYOR (2.mum<1.mum)", vacc < 1.0),
                ("1.mum hacmi ≥1.5× ve artıyor", (vol1 >= 1.5) & (vacc >= 1.0)),
                ("1.mum hacmi ≥1.5× ve düşüyor", (vol1 >= 1.5) & (vacc < 1.0))]
        print(f"  {'desen':<32}{'| EĞİTİM n':>11}{'TP%':>7}{'edge':>7}{'EV(R)':>8}"
              f"{'| TEST n':>9}{'TP%':>7}{'edge':>7}{'EV(R)':>8}{'$':>11}")
        for dname, dmask in DIMS:
            out = {}
            for split, sm in (("train", is_train), ("test", ~is_train)):
                idx = np.where(dmask & sm)[0]
                if len(idx) < 25:
                    out[split] = None; continue
                tp_d = tp_m * atr_e[idx]; sl_d = sl_m * atr_e[idx]
                net, risk, win, loss = book.evaluate(idx, tp_d, sl_d)
                out[split] = cell_stats(net, risk, win, loss, tp_d, sl_d)
            a_, b_ = out["train"], out["test"]
            if not a_:
                continue
            tail = (f"{b_['n']:>9}{b_['tp_rate']:>7.1f}{b_['edge']:>+7.1f}{b_['ev_r']:>+8.3f}"
                    f"{b_['usd']:>+11,.0f}") if b_ else "   (test n<25)"
            print(f"  {dname:<32}{a_['n']:>11}{a_['tp_rate']:>7.1f}{a_['edge']:>+7.1f}"
                  f"{a_['ev_r']:>+8.3f}{tail}")


if __name__ == "__main__":
    main()
