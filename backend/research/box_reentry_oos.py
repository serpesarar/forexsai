"""box_reentry_oos.py — kapanış-sonrası re-entry kuralının DIŞ-ÖRNEKLEM sınaması.

Panel tarafı testi (1MDATA/mt5_islem_analizi/08_reentry_testi.py) kuralın üç
kapıyı da geçtiğini gösterdi — ama 2026-07-13→08-13 ayının İÇİNDE:
  bağımsızlık %57 · plasebo p=0.020 · eşit-riskte +4.350$ alfa

Bu script aynı kuralı MT5'teki TÜM NASDAQ geçmişinde koşar ve kuralın çıktığı
aydan ÖNCEKİ dönemi ayrı raporlar. NASDAQ'ta bu sınama daha önce belirleyici
oldu (ATR-TP iç-örneklemde parlayıp dışarıda çökmüştü).

Kural: ana işlem TP ile kapanınca +5 dk, SL ile kapanınca +1 dk sonra AYNI
yönde yeni giriş (TP 80 / SL 110 puan, zincirleme yok — bir anadan bir re-entry).

Çalıştırma (kutuda): python backend/research/box_reentry_oos.py --split 2026-07-13
"""
from __future__ import annotations

import argparse
import random
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

SYM = "NAS100"
LOT, TP_PT, SL_PT = 5.0, 80.0, 110.0
USD_PT = 1.0                       # 80pt × 5 lot = 400$
random.seed(31)


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


def load_pos(since):
    frm = since - timedelta(days=2)
    to = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)
    deals = mt5.history_deals_get(frm, to) or []
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
        i0 = il[0]
        rows.append({"t_srv": int(i0.time), "utc": s2u(int(i0.time)),
                     "entry": float(i0.price),
                     "dir": "BUY" if i0.type == mt5.DEAL_TYPE_BUY else "SELL"})
    rows.sort(key=lambda r: r["t_srv"])
    return rows


def resolve(bars, times, t_srv, entry, direction, max_bars=3000):
    sgn = 1 if direction == "BUY" else -1
    i0 = bisect_left(times, t_srv)
    if i0 >= len(bars) - 2:
        return None
    tp, sl = entry + sgn * TP_PT, entry - sgn * SL_PT
    for b in bars[i0:i0 + max_bars]:
        hit_sl = (b["low"] <= sl) if sgn > 0 else (b["high"] >= sl)
        hit_tp = (b["high"] >= tp) if sgn > 0 else (b["low"] <= tp)
        if hit_sl:
            return {"pnl": -SL_PT * LOT * USD_PT, "win": False,
                    "t_in": t_srv, "t_out": b["t"]}
        if hit_tp:
            return {"pnl": TP_PT * LOT * USD_PT, "win": True,
                    "t_in": t_srv, "t_out": b["t"]}
    return None


def px_at(bars, times, t):
    i = bisect_left(times, t)
    if i >= len(bars):
        return None
    j = i if (i < len(times) and times[i] == t) else max(0, i - 1)
    return bars[j]["close"]


def expo(poz):
    ev = []
    for p in poz:
        ev.append((p["t_in"], LOT)); ev.append((p["t_out"], -LOT))
    ev.sort()
    cur = mx = 0.0
    for _, d in ev:
        cur += d; mx = max(mx, cur)
    return mx


def st(rows):
    if not rows:
        return 0, 0.0, 0.0
    return len(rows), 100 * sum(1 for r in rows if r["win"]) / len(rows), sum(r["pnl"] for r in rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="2026-07-13")
    ap.add_argument("--since", default="2026-04-01")
    a = ap.parse_args()
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    split = datetime.fromisoformat(a.split).replace(tzinfo=timezone.utc)
    mt5.symbol_select(SYM, True)

    pos = load_pos(datetime.fromisoformat(a.since))
    r = mt5.copy_rates_from_pos(SYM, mt5.TIMEFRAME_M1, 0, 99000)
    bars = [{"t": int(x["time"]), "high": float(x["high"]), "low": float(x["low"]),
             "close": float(x["close"])} for x in r]
    times = [b["t"] for b in bars]
    print(f"{SYM}: pozisyon={len(pos)} 1m bar={len(bars)}")
    print(f"  {pos[0]['utc']:%Y-%m-%d} → {pos[-1]['utc']:%Y-%m-%d}\n")

    gruplar = {"DIŞ-ÖRNEKLEM (kuraldan önce)": [p for p in pos if p["utc"] < split],
               "İÇ-ÖRNEKLEM (kuralın ayı)": [p for p in pos if p["utc"] >= split]}

    for gad, sel in gruplar.items():
        print("=" * 66)
        print(f"{gad} — ham pozisyon n={len(sel)}")
        ana = []
        for p in sel:
            res = resolve(bars, times, p["t_srv"], p["entry"], p["dir"])
            if res:
                res["dir"] = p["dir"]; ana.append(res)
        if len(ana) < 10:
            print("  yeterli işlem yok\n"); continue
        n_a, w_a, p_a = st(ana)
        mx_a = expo(ana)
        print(f"  TABAN            n={n_a:<4} WR=%{w_a:5.1f} PnL={p_a:>+8.0f}$ "
              f"· maks {mx_a:.0f} lot")

        re_rows = []
        for x in ana:
            gec = 5 if x["win"] else 1
            t_k = x["t_out"] + gec * 60
            px = px_at(bars, times, t_k)
            if px is None:
                continue
            rr = resolve(bars, times, t_k, px, x["dir"])
            if rr:
                rr["dir"] = x["dir"]; rr["ana_win"] = x["win"]
                re_rows.append(rr)
        n_r, w_r, p_r = st(re_rows)
        print(f"  RE-ENTRY         n={n_r:<4} WR=%{w_r:5.1f} PnL={p_r:>+8.0f}$")
        if not re_rows:
            print(); continue

        ayni = sum(1 for x in re_rows if x["win"] == x["ana_win"])
        ku = [x for x in re_rows if x["ana_win"]]; kk = [x for x in re_rows if not x["ana_win"]]
        print(f"    bağımsızlık: sonuç örtüşmesi %{100*ayni/n_r:.0f} · "
              f"ana kazandıysa %{st(ku)[1]:.0f} / kaybettiyse %{st(kk)[1]:.0f}")

        # plasebo: aynı yönde rastgele zaman
        gec_idx = list(range(200, len(bars) - 3000))
        pl = []
        for _ in range(300):
            tot = 0.0
            for x in re_rows:
                i = random.choice(gec_idx)
                q = resolve(bars, times, bars[i]["t"], bars[i]["close"], x["dir"])
                if q:
                    tot += q["pnl"]
            pl.append(tot)
        pl.sort()
        p_val = sum(1 for v in pl if v >= p_r) / len(pl)
        print(f"    plasebo medyan {pl[len(pl)//2]:+.0f}$ · p={p_val:.3f} "
              f"{'✅' if p_val < 0.05 else '❌'}")

        birlesik = ana + re_rows
        n_b, w_b, p_b = st(birlesik)
        mx_b = expo(birlesik)
        k = mx_b / mx_a if mx_a else 1.0
        fark = p_b - p_a * k
        print(f"    eşit risk: taban×{k:.2f}={p_a*k:+.0f}$ vs birleşik {p_b:+.0f}$ "
              f"→ {fark:+.0f}$ {'✅ ALFA' if fark > 0 else '❌ kaldıraç'}")
        print(f"    birleşik: n={n_b} WR=%{w_b:.1f} maks {mx_b:.0f} lot\n")

    mt5.shutdown()


if __name__ == "__main__":
    main()
