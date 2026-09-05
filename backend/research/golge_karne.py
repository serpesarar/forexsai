"""golge_karne.py — gölge kapı karnesi (EPIZOD BAZINDA, sahte çoğaltmasız).

⚠️ NEDEN BU DOSYA VAR (2026-09-05):
Bot 60-75 sn'de bir tarar ve aynı koşul sürdükçe aynı gölge kararını tekrar
yazardı. Ham kayıt sayısıyla yapılan her istatistik bu yüzden ŞİŞİKTİ:
    XAUUSD 617 kayıt =  36 gerçek olay (17,1×)
    USOIL  276 kayıt =  26 olay        (10,6×)
    GDAXI  113 kayıt =  14 olay        ( 8,1×)
GDAXI kapısı "22W/55L, p≈1e-10" sanılıp canlıya alındı; epizod bazında gerçek
tablo 2W/6L, p=0,022 (8 karşılaştırmada Bonferroni ile anlamsız). Karar geri alındı.

`shadow_log.py` artık yazarken bastırıyor (EPIZOD_SESSIZLIK), ama ESKİ kayıtlar
hâlâ şişik — bu script her iki durumda da doğru sonuç verir: kayıtları
zaman boşluğuna göre epizoda böler ve her epizodun İLK anını çözer.

Çalıştırma (kutuda):  python backend/research/golge_karne.py --gun 21
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok — bu script MT5 kutusunda çalışır.")
import config  # type: ignore

EPIZOD_BOSLUK = 1800          # 30 dk sessizlik → yeni epizod
UFUK_SAAT = 8                 # yarışı bu kadar süre izle
SYM = {"NDX.INDX": "NAS100", "GDAXI.INDX": "GER40",
       "USOIL.FOREX": "SpotCrude", "XAUUSD": "XAUUSD"}


def broker_offset() -> int:
    for _ in range(6):
        tk = mt5.symbol_info_tick("NAS100")
        if tk and tk.time:
            c = int(round((tk.time - time.time()) / 900.0) * 900)
            if -5 * 3600 <= c <= 5 * 3600:
                return c
        time.sleep(2)
    return 10800              # bilinen iyi değer (piyasa kapalıyken tick bayat)


def geometri(scope: str, fx: str, px: float):
    """Scope'un gerçek TP/SL mesafesi (fiyat birimi)."""
    son = scope.split(":")[-1]
    if son in ("VIXREG", "DAYCOMBO"):
        return 80.0, 110.0
    if son == "CHREV":
        c = (getattr(config, "CHANNEL_REVERSION", None) or {}).get(fx)
        if not c:
            return None, None
        tp, sl = float(c["tp"]), float(c["sl"])
        return (px * tp / 100, px * sl / 100) if c.get("is_pct") else (tp, sl)
    parca = scope.split(":")
    yon = parca[1] if len(parca) > 1 else ""
    c = (getattr(config, "ROBUST_SCOPES", None) or {}).get(f"{fx}:{yon}")
    if not c:
        return None, None
    tp, sl = float(c["tp"]), float(c["sl"])
    return (px * tp / 100, px * sl / 100) if c.get("is_pct") else (tp, sl)


def epizodlara_bol(kayitlar: list) -> list:
    """Zaman boşluğuna göre epizoda böl; her epizodun İLK kaydını döndür."""
    kayitlar.sort(key=lambda x: x[0])
    ilkler, grup = [], [kayitlar[0]]
    for i in range(1, len(kayitlar)):
        if (kayitlar[i][0] - kayitlar[i - 1][0]).total_seconds() > EPIZOD_BOSLUK:
            ilkler.append((grup[0], len(grup)))
            grup = []
        grup.append(kayitlar[i])
    ilkler.append((grup[0], len(grup)))
    return ilkler


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gun", type=int, default=21)
    ap.add_argument("--bosluk", type=int, default=EPIZOD_BOSLUK)
    a = ap.parse_args()

    if not mt5.initialize():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    off = broker_offset()
    base = os.path.join(ROOT, "yeni deneme")
    cutoff = datetime.now(timezone.utc) - timedelta(days=a.gun)

    ham = collections.defaultdict(list)
    for line in open(os.path.join(base, "gate_skipped.jsonl"),
                     encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if not r.get("shadow") and r.get("decision") != "would_block":
            continue
        if r.get("decision") != "would_block":
            continue
        try:
            t = datetime.fromisoformat(r["ts"])
        except Exception:
            continue
        if t < cutoff:
            continue
        ham[(r.get("rule"), r.get("symbol"), r.get("direction"), r.get("scope"))].append((t, r))

    bar_cache: dict = {}

    def barlar(ms: str, t0: datetime):
        key = (ms, t0.strftime("%Y%m%d%H"))
        if key in bar_cache:
            return bar_cache[key]
        r = mt5.copy_rates_range(ms, mt5.TIMEFRAME_M1,
                                 t0 + timedelta(seconds=off),
                                 t0 + timedelta(seconds=off) + timedelta(hours=UFUK_SAAT))
        out = [] if r is None else [(int(x[0]) - off, float(x[2]), float(x[3])) for x in r]
        bar_cache[key] = out
        return out

    def coz(yon: str, entry: float, tp_d: float, sl_d: float, bs: list):
        for _t, h, l in bs:
            if yon == "BUY":
                htp, hsl = h >= entry + tp_d, l <= entry - sl_d
            else:
                htp, hsl = l <= entry - tp_d, h >= entry + sl_d
            if hsl:
                return "LOSS"
            if htp:
                return "WIN"
        return None

    sonuc = collections.defaultdict(lambda: collections.Counter())
    basabas: dict = {}
    for (kural, fx, yon, scope), v in ham.items():
        ms = SYM.get(fx)
        if not ms or not v:
            continue
        for (t0, r), ham_adet in epizodlara_bol(v):
            px = float(r["price"])
            tp_d, sl_d = geometri(scope, fx, px)
            if not tp_d or not sl_d:
                continue
            basabas[fx] = sl_d / (tp_d + sl_d) * 100
            s = coz(yon, px, tp_d, sl_d, barlar(ms, t0))
            k = (kural, fx, yon)
            sonuc[k][s or "COZULMEDI"] += 1
            sonuc[k]["_ham"] += ham_adet

    print("=" * 96)
    print(f"GÖLGE KARNESİ — EPİZOD BAZINDA (son {a.gun} gün, boşluk {a.bosluk}s)")
    print("=" * 96)
    print(f"  {'kural':<10}{'sembol':<13}{'yön':<6}{'ham':>6}{'epizod':>8}{'W':>4}{'L':>4}"
          f"{'?':>4}{'WR':>8}{'başabaş':>9}{'fark':>8}{'p':>8}  hüküm")
    for k in sorted(sonuc, key=lambda x: -(sonuc[x]["WIN"] + sonuc[x]["LOSS"])):
        c = sonuc[k]
        w, l = c["WIN"], c["LOSS"]
        n = w + l
        ep = n + c["COZULMEDI"]
        be = basabas.get(k[1])
        if n == 0 or be is None:
            print(f"  {k[0]:<10}{k[1]:<13}{k[2]:<6}{c['_ham']:>6}{ep:>8}{w:>4}{l:>4}"
                  f"{c['COZULMEDI']:>4}{'—':>8}{'—':>9}{'—':>8}{'—':>8}  veri yok")
            continue
        wr = w / n * 100
        p0 = be / 100
        z = (w / n - p0) / math.sqrt(p0 * (1 - p0) / n)
        pv = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
        fark = wr - be
        hkm = ("KAPI HAKLI" if fark < 0 else "KAPI HAKSIZ") if pv < 0.05 else "KANIT YOK"
        print(f"  {k[0]:<10}{k[1]:<13}{k[2]:<6}{c['_ham']:>6}{ep:>8}{w:>4}{l:>4}"
              f"{c['COZULMEDI']:>4}{wr:>7.1f}%{be:>8.1f}%{fark:>+8.1f}{pv:>8.3f}  {hkm}")

    n_kars = len([k for k in sonuc if sonuc[k]["WIN"] + sonuc[k]["LOSS"] > 0])
    print(f"\n  ⚠️ {n_kars} karşılaştırma yapıldı → Bonferroni eşiği p < {0.05/max(n_kars,1):.4f}")
    print("     fark<0 = kapı haklı (bloklananlar başabaşın altında)")
    print("     fark>0 = kapı haksız (bloklamak para kaybettirir)")
    mt5.shutdown()


if __name__ == "__main__":
    main()
