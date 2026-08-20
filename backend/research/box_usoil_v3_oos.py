"""box_usoil_v3_oos.py — USOIL v3 raporunun (F1+F2 giris rejim filtresi) DERIN sinamasi.

Rapor iddiasi (74 islem, 2026-07-13→08-14, ic-orneklem):
    F1: ATR14(1m)/ATR60(1m) <= 1.09     (volatilite soku rejimini ele)
    F2: pos_in_range(son 4 saat) <= 0.85 (dalga tepesinden alma)
    -> n=23  WR %82.6  +4.020$  ·  permutasyon p<0.001  ·  Wilson alt %63
    Rapor H4 (derin dis-orneklem) maddesini "yerelde calistirilamaz" diye ACIK birakti.

Panel tarafinda yapilan yerel denetim (1MDATA/usoil_islem_analizi/07_v3_denetim.py):
  * aritmetik dogrulandi (n=23/%82.6/+4.020$) — ama n=23 icin BUY sarti da gerekiyor
  * esik SABIT tutulunca p=0.006; esik IZGARASI da permute edilince p=0.038
  * kumenin medyan RR'i 0.78 -> basabas WR %56.2; bu nulle karsi binom p=0.151
  * cooldown (2 SL -> 4s) izgara aramali plaseboda p=0.225 -> GURULTU
  * TP=0.6R tek basina canli bazda +5.951$, F1+F2 eklenince +4.288$ -> filtre EKSILTIYOR

Bu script iki bagimsiz derin sinama yapar:

  A) ISLEM-BAZLI DIS-ORNEKLEM — MT5 gecmisindeki TUM SpotCrude MOM/SR BUY
     islemleri; raporun cikarildigi pencere (IC) ile disi (DIS) ayri raporlanir.

  B) BAR-BAZLI KOSULLU TEST — botun GERCEK USOIL:BUY momentum kosullari
     (M30 stoch_k>70, M30 dist_ema20/atr>0.8, H1 sar_dist/atr>0) bar-bar
     uygulanir; binlerce hipotetik girisle F1/F2'nin kenari olculur.
     Ek kapilar: kosulsuz kontrol, esik platosu, izgara aramali plasebo.

Sizinti korumasi: her gosterge yalniz giris barindan ONCEKI KAPALI barlardan.

Calistirma (kutuda):
    python backend/research/box_usoil_v3_oos.py
    python backend/research/box_usoil_v3_oos.py --spread 0.03 --deep-tf m5
"""
from __future__ import annotations

import argparse
import random
import sys
from bisect import bisect_left, bisect_right
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok — bu script MT5 kutusunda calisir.")

import config  # type: ignore

SYM = "SpotCrude"
MOM_MAGIC = getattr(config, "MAGIC_NUMBER", 52890969)
LOT = float(getattr(config, "LOT_SIZE", 5.0))
CONTRACT = 100.0                      # 1 lot = 100 varil -> 1.00$ hareket = 100$/lot
TP_PCT, SL_PCT = 1.04, 1.49           # config.SCOPE_GEOMETRY USOIL.FOREX:BUY
F1_GRID = [0.85, 0.90, 0.95, 1.00, 1.05, 1.09, 1.15, 1.20, 1.30, 1.50]
F2_GRID = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
random.seed(20260820)


# ── altyapi ─────────────────────────────────────────────────────────────────

def s2u(epoch: int) -> datetime:
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
    if r is None or len(r) == 0:
        return [], []
    b = [{"t": int(x["time"]), "o": float(x["open"]), "h": float(x["high"]),
          "l": float(x["low"]), "c": float(x["close"])} for x in r]
    return b, [x["t"] for x in b]


def atr_of(seg) -> float | None:
    if len(seg) < 2:
        return None
    trs = [max(seg[j]["h"] - seg[j]["l"], abs(seg[j]["h"] - seg[j - 1]["c"]),
               abs(seg[j]["l"] - seg[j - 1]["c"])) for j in range(1, len(seg))]
    return sum(trs) / len(trs) if trs else None


def ema_series(vals, period):
    k = 2.0 / (period + 1)
    e = vals[0]
    out = [e]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
        out.append(e)
    return out


def stoch_k(seg, k=14) -> float | None:
    if len(seg) < k:
        return None
    w = seg[-k:]
    hi = max(x["h"] for x in w)
    lo = min(x["l"] for x in w)
    if hi <= lo:
        return 50.0
    return 100.0 * (seg[-1]["c"] - lo) / (hi - lo)


def sar_last(seg, step=0.02, maxstep=0.2) -> float:
    h = [x["h"] for x in seg]
    l = [x["l"] for x in seg]
    n = len(h)
    if n < 2:
        return l[-1]
    sar, ep, af, up = l[0], h[0], step, True
    for i in range(1, n):
        sar = sar + af * (ep - sar)
        if up:
            sar = min(sar, l[i - 1], l[i - 2] if i >= 2 else l[i - 1])
            if h[i] > ep:
                ep, af = h[i], min(af + step, maxstep)
            if l[i] < sar:
                up, sar, ep, af = False, ep, l[i], step
        else:
            sar = max(sar, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if l[i] < ep:
                ep, af = l[i], min(af + step, maxstep)
            if h[i] > sar:
                up, sar, ep, af = True, ep, h[i], step
    return float(sar)


def stats(rows):
    rows = [r for r in rows if r]
    if not rows:
        return 0, 0.0, 0.0
    return (len(rows), 100.0 * sum(1 for r in rows if r["win"]) / len(rows),
            sum(r["pnl"] for r in rows))


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return 100 * (c - h), 100 * (c + h)


def line(label, rows, extra=""):
    n, wr, net = stats(rows)
    k = sum(1 for r in rows if r and r["win"])
    lo, _ = wilson(k, n)
    print(f"  {label:<44} n={n:<5} WR=%{wr:5.1f} net={net:>+10.0f}$ "
          f"Wilson_alt=%{lo:4.0f} {extra}")


# ── A) islem-bazli dis-orneklem ─────────────────────────────────────────────

def load_positions(since: datetime) -> list[dict]:
    frm = since - timedelta(days=3)
    to = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=3)
    deals = mt5.history_deals_get(frm, to) or []
    orders = mt5.history_orders_get(frm, to) or []
    sltp = {}
    for o in sorted(orders, key=lambda x: x.time_setup):
        pid = int(getattr(o, "position_id", 0) or 0)
        if pid and pid not in sltp and (o.sl or o.tp):
            sltp[pid] = (float(o.sl or 0), float(o.tp or 0))
    ins, outs = defaultdict(list), defaultdict(list)
    for d in deals:
        if d.symbol != SYM:
            continue
        if d.entry == mt5.DEAL_ENTRY_IN:
            ins[d.position_id].append(d)
        elif d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY):
            outs[d.position_id].append(d)
    rows = []
    for pid, il in ins.items():
        ol = sorted(outs.get(pid) or [], key=lambda d: d.time)
        if not ol:
            continue
        i0, last = il[0], ol[-1]
        sl, _tp = sltp.get(pid, (0.0, 0.0))
        entry = float(i0.price)
        sl_dist = abs(entry - float(sl)) if sl else 0.0
        profit = sum(x.profit for x in ol)
        rows.append({
            "pid": pid, "dir": "BUY" if i0.type == mt5.DEAL_TYPE_BUY else "SELL",
            "magic": int(getattr(i0, "magic", 0) or 0), "t": int(i0.time),
            "utc": s2u(int(i0.time)), "entry": entry, "sl_dist": sl_dist,
            "pnl": float(profit), "win": float(profit) > 0,
            "comment": str(i0.comment or ""),
        })
    rows.sort(key=lambda r: r["t"])
    return rows


def m1_features(t_srv: int, m1, m1t) -> dict | None:
    """F1/F2 — giris barini DAHIL ETMEDEN (D7)."""
    i = bisect_left(m1t, t_srv)
    if i < 250:
        return None
    pre = m1[:i]
    a14, a60 = atr_of(pre[-15:]), atr_of(pre[-61:])
    if not a14 or not a60 or a60 <= 0:
        return None
    w = pre[-240:]
    hi, lo = max(x["h"] for x in w), min(x["l"] for x in w)
    px = pre[-1]["c"]
    return {"f1": a14 / a60,
            "f2": (px - lo) / (hi - lo) if hi > lo else 0.5}


def bolum_a(split: datetime, end: datetime, m1, m1t):
    print("=" * 92)
    print("A) ISLEM-BAZLI DIS-ORNEKLEM — botun gercek USOIL MOM/SR BUY islemleri")
    print("=" * 92)
    pos = load_positions(datetime(2026, 1, 1, tzinfo=timezone.utc))
    live = [p for p in pos if p["magic"] == MOM_MAGIC and p["dir"] == "BUY"]
    print(f"  tum SpotCrude pozisyon={len(pos)} · MOM/SR BUY={len(live)}")
    if not live:
        print("  islem yok\n"); return
    print(f"  {live[0]['utc']:%Y-%m-%d} -> {live[-1]['utc']:%Y-%m-%d}")
    if m1t:
        print(f"  1m bar kapsami: {s2u(m1t[0]):%Y-%m-%d} -> {s2u(m1t[-1]):%Y-%m-%d}")
    else:
        print("  1m bar YOK — F1 yalniz 5m vekiliyle olculecek")

    feat_ok = 0
    for p in live:
        f = m1_features(p["t"], m1, m1t)
        if f:
            p.update(f); feat_ok += 1
    print(f"  F1/F2 hesaplanabilen (1m gecmisi yeten): {feat_ok}/{len(live)}\n")

    gruplar = [
        ("IC-ORNEKLEM (raporun ayi)", [p for p in live if split <= p["utc"] < end]),
        ("DIS-ORNEKLEM (oncesi)", [p for p in live if p["utc"] < split]),
        ("DIS-ORNEKLEM (sonrasi)", [p for p in live if p["utc"] >= end]),
        ("DIS-ORNEKLEM (toplam)", [p for p in live
                                   if p["utc"] < split or p["utc"] >= end]),
    ]
    for ad, sel in gruplar:
        print(f"── {ad} ──")
        if not sel:
            print("   islem yok\n"); continue
        line("baz (gerceklesmis)", sel)
        okf = [p for p in sel if "f1" in p]
        if not okf:
            print("   F1/F2 hesaplanamadi (1m gecmisi yok)\n"); continue
        line("F1 (atr<=1.09)", [p for p in okf if p["f1"] <= 1.09])
        line("F2 (pos<=0.85)", [p for p in okf if p["f2"] <= 0.85])
        line("F1+F2", [p for p in okf if p["f1"] <= 1.09 and p["f2"] <= 0.85])
        line("ELENEN (F1+F2 disi)",
             [p for p in okf if not (p["f1"] <= 1.09 and p["f2"] <= 0.85)])
        print()


# ── B) bar-bazli kosullu test ───────────────────────────────────────────────

def build_signals(b5, t5, b30, t30, b1h, t1h, m1, m1t, spread, cooldown_min=60,
                  tp_mode="pct", tp_r=0.6):
    """Botun USOIL:BUY momentum kosullarini bar-bar uygular, hipotetik girisler uretir."""
    out = []
    son = None
    # M30 EMA20 serisi (hizli erisim)
    c30 = [x["c"] for x in b30]
    ema20_30 = ema_series(c30, 20) if c30 else []
    for i in range(300, len(b5)):
        t = b5[i]["t"]
        if son is not None and (t - son) < cooldown_min * 60:
            continue
        j = bisect_right(t30, t) - 1          # son KAPALI M30 bari
        if j < 60:
            continue
        # M30 bari gercekten kapali mi? (kapanis zamani = t30[j] + 1800)
        if t30[j] + 1800 > t:
            j -= 1
            if j < 60:
                continue
        seg30 = b30[j - 29:j + 1]
        k = stoch_k(seg30, 14)
        a30 = atr_of(seg30[-15:])
        if k is None or not a30:
            continue
        e20 = ema20_30[j]
        dist = (seg30[-1]["c"] - e20) / a30
        if not (k > 70.0 and dist > 0.8):
            continue
        h = bisect_right(t1h, t) - 1
        if h < 60:
            continue
        if t1h[h] + 3600 > t:
            h -= 1
            if h < 60:
                continue
        seg1h = b1h[max(0, h - 199):h + 1]
        a1h = atr_of(seg1h[-15:])
        if not a1h:
            continue
        sar = sar_last(seg1h)
        if not ((seg1h[-1]["c"] - sar) / a1h > 0.0):
            continue

        feat = m1_features(t, m1, m1t) if m1 else None
        # 5m vekil ozellikler (derin donem icin)
        pre5 = b5[:i]
        a3_5, a12_5 = atr_of(pre5[-4:]), atr_of(pre5[-13:])
        w48 = pre5[-48:]
        hi, lo = max(x["h"] for x in w48), min(x["l"] for x in w48)
        px = pre5[-1]["c"]
        f1p = (a3_5 / a12_5) if (a3_5 and a12_5) else None
        f2p = (px - lo) / (hi - lo) if hi > lo else 0.5

        entry = b5[i]["c"] + spread            # BUY -> ask
        sl_d = entry * SL_PCT / 100.0
        tp_d = entry * TP_PCT / 100.0 if tp_mode == "pct" else tp_r * sl_d
        tp, sl = entry + tp_d, entry - sl_d
        res = None
        for x in b5[i + 1:i + 1200]:
            if x["l"] <= sl:
                res = {"pnl": -sl_d * LOT * CONTRACT, "win": False}; break
            if x["h"] >= tp:
                res = {"pnl": tp_d * LOT * CONTRACT, "win": True}; break
        if not res:
            continue
        res.update({"utc": s2u(t), "t": t,
                    "f1": feat["f1"] if feat else None,
                    "f2": feat["f2"] if feat else None,
                    "f1p": f1p, "f2p": f2p})
        out.append(res)
        son = t
    return out


def grid_placebo(rows, key1, key2, reps=800, min_n=40):
    """Izgara aramali plasebo: sonuclari karistir, ayni 2B aramayi tekrarla.

    Hucre uyeliklerini BIR KEZ hesaplar; her permutasyonda yalniz toplam alinir.
    """
    cells = []
    for a in F1_GRID:
        for b in F2_GRID:
            idx = [i for i, r in enumerate(rows)
                   if r[key1] is not None and r[key1] <= a and r[key2] <= b]
            if len(idx) >= min_n:
                cells.append(idx)
    if not cells:
        return 0.0, 1.0
    payload = [r["pnl"] for r in rows]

    def best_of(pay):
        return max(sum(pay[i] for i in idx) for idx in cells)

    obs = best_of(payload)
    hits = 0
    for _ in range(reps):
        random.shuffle(payload)
        hits += int(best_of(payload) >= obs)
    return obs, hits / reps


def bolum_b(sig, split, end, key1, key2, etiket):
    print("=" * 92)
    print(f"B) BAR-BAZLI KOSULLU TEST — {etiket}")
    print("=" * 92)
    ok = [r for r in sig if r[key1] is not None]
    if len(ok) < 40:
        print(f"  yeterli sinyal yok (n={len(ok)})\n"); return
    print(f"  hipotetik giris: {len(ok)}  "
          f"({ok[0]['utc']:%Y-%m-%d} -> {ok[-1]['utc']:%Y-%m-%d})")
    line("KOSULSUZ BAZ (botun momentum kosullari)", ok)
    f1o = [r for r in ok if r[key1] <= 1.09]
    f2o = [r for r in ok if r[key2] <= 0.85]
    both = [r for r in ok if r[key1] <= 1.09 and r[key2] <= 0.85]
    line("F1 (<=1.09)", f1o)
    line("F2 (<=0.85)", f2o)
    line("F1+F2", both)
    line("ELENEN", [r for r in ok if not (r[key1] <= 1.09 and r[key2] <= 0.85)])

    print("\n  ── F1 esik platosu ──")
    for th in F1_GRID:
        line(f"  atr_ratio <= {th:.2f}", [r for r in ok if r[key1] <= th])
    print("  ── F2 esik platosu ──")
    for th in F2_GRID:
        line(f"  pos <= {th:.2f}", [r for r in ok if r[key2] <= th])

    print("\n  ── donem ayrimi (F1+F2) ──")
    for ad, sel in (("IC (07-13..08-14)", [r for r in both if split <= r["utc"] < end]),
                    ("DIS (oncesi)", [r for r in both if r["utc"] < split]),
                    ("DIS (sonrasi)", [r for r in both if r["utc"] >= end])):
        line(f"  {ad}", sel)
    print("  ── ayni donemler, FILTRESIZ ──")
    for ad, sel in (("IC (07-13..08-14)", [r for r in ok if split <= r["utc"] < end]),
                    ("DIS (oncesi)", [r for r in ok if r["utc"] < split]),
                    ("DIS (sonrasi)", [r for r in ok if r["utc"] >= end])):
        line(f"  {ad}", sel)

    obs, p = grid_placebo(ok, key1, key2)
    print(f"\n  >>> IZGARA ARAMALI PLASEBO: en iyi hucre {obs:+.0f}$ · p={p:.3f} "
          f"{'ANLAMLI' if p < 0.05 else 'GURULTUDEN AYRISMIYOR'}")

    # aylik kararlilik
    print("\n  ── aylik (F1+F2 vs filtresiz) ──")
    ay = defaultdict(lambda: ([], []))
    for r in ok:
        key = f"{r['utc']:%Y-%m}"
        ay[key][0].append(r)
        if r[key1] <= 1.09 and r[key2] <= 0.85:
            ay[key][1].append(r)
    for key in sorted(ay):
        a, b = ay[key]
        n0, w0, p0 = stats(a)
        n1, w1, p1 = stats(b)
        print(f"    {key}  filtresiz n={n0:<4} %{w0:5.1f} {p0:>+9.0f}$  |  "
              f"F1+F2 n={n1:<4} %{w1:5.1f} {p1:>+9.0f}$")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="2026-07-13")
    ap.add_argument("--end", default="2026-08-14")
    ap.add_argument("--spread", type=float, default=0.03)
    ap.add_argument("--tp", default="pct", choices=["pct", "r06"])
    ap.add_argument("--m1", type=int, default=99000)
    ap.add_argument("--m5", type=int, default=99000)
    a = ap.parse_args()
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    mt5.symbol_select(SYM, True)
    split = datetime.fromisoformat(a.split).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(a.end).replace(tzinfo=timezone.utc)

    m1, m1t = bars(mt5.TIMEFRAME_M1, a.m1)
    b5, t5 = bars(mt5.TIMEFRAME_M5, a.m5)
    b30, t30 = bars(mt5.TIMEFRAME_M30, 40000)
    b1h, t1h = bars(mt5.TIMEFRAME_H1, 20000)
    if not b5:
        for n in (60000, 40000, 20000, 10000):
            b5, t5 = bars(mt5.TIMEFRAME_M5, n)
            if b5:
                break
    if not m1:
        for n in (60000, 40000, 20000):
            m1, m1t = bars(mt5.TIMEFRAME_M1, n)
            if m1:
                break
    if not b5:
        sys.exit("5m bar alinamadi")
    print(f"{SYM}: 1m={len(m1)} 5m={len(b5)} 30m={len(b30)} 1h={len(b1h)}")
    if b5:
        print(f"  5m kapsam: {s2u(t5[0]):%Y-%m-%d} -> {s2u(t5[-1]):%Y-%m-%d}")
    if m1:
        print(f"  1m kapsam: {s2u(m1t[0]):%Y-%m-%d} -> {s2u(m1t[-1]):%Y-%m-%d}")
    print(f"  geometri: TP {TP_PCT}% / SL {SL_PCT}% (RR {TP_PCT/SL_PCT:.2f} -> "
          f"basabas WR %{100/(1+TP_PCT/SL_PCT):.1f}) · spread {a.spread} · lot {LOT}\n")

    bolum_a(split, end, m1, m1t)

    sig = build_signals(b5, t5, b30, t30, b1h, t1h, m1, m1t, a.spread,
                        tp_mode=("pct" if a.tp == "pct" else "r"), tp_r=0.6)
    print(f"uretilen hipotetik giris (cozulmus): {len(sig)}\n")

    # B1: 1m-tabanli GERCEK F1/F2 (1m gecmisi kadar)
    bolum_b(sig, split, end, "f1", "f2",
            "GERCEK F1/F2 (1m tabanli, 1m gecmisiyle sinirli)")
    # B2: 5m vekil (derin donem)
    ov = [r for r in sig if r["f1"] is not None and r["f1p"] is not None]
    if len(ov) > 30:
        import statistics
        agree = sum(1 for r in ov
                    if (r["f1"] <= 1.09) == (r["f1p"] <= 1.09)) / len(ov)
        try:
            corr = statistics.correlation([r["f1"] for r in ov], [r["f1p"] for r in ov])
        except Exception:
            corr = float("nan")
        print(f"VEKIL DOGRULAMA (ortusen {len(ov)} sinyal): "
              f"korelasyon={corr:.2f} · '<=1.09' karar uyumu=%{100*agree:.0f}\n")
    bolum_b(sig, split, end, "f1p", "f2p",
            "5m VEKIL F1/F2 (derin donem — ATR3/ATR12 5m, 4s konum 48x5m)")

    mt5.shutdown()


if __name__ == "__main__":
    main()
