"""KAPI KOMBİNASYONU DENETİMİ — botun kendi işlemleri üzerinde, sızıntısız.

Kullanıcı sorusu (2026-08-13): "sistemim kapıların KOMBİNASYONUNU yapıyordu,
tek kapı değil. Kombosu daha verimli/pozitif sonuç veriyor mu?"

Yöntem:
  · Son N günün GERÇEK MT5 işlemleri (scope = magic).
  · Her işlemin AÇILIŞ ANINDA, botun KENDİ kapı tanımlarıyla (aynı formüller,
    aynı pencereler) kapı durumları yeniden hesaplanır:
       trend   → 1h EMA50 hizası (trend_alignment)
       konum   → 4 saatlik dalga içindeki yer (entry_position; SELL≥0.40, BUY≤0.60)
       adx     → ADX(30m) < 25 (CHREV rejim kapısı)
       saat    → TQ çukur saatleri dışında mı (NDX 16,17,19 UTC / USOIL Perşembe)
    Barlar `_bars_upto` ile karar anında KAPANMIŞ olanlardan alınır → geleceğe
    bakış yok.
  · Sonra her kapının TEK BAŞINA ve KOMBİNASYON hâlinde ne eleyeceği ölçülür.
    Kapı ancak elediği küme NET ZARARLIYSA haklıdır.

Çalıştırma (kutuda): python backend/research/gate_combo_audit.py [gün]
"""
from __future__ import annotations

import itertools
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import MetaTrader5 as mt5  # noqa: E402

from _bars_upto import rates_upto  # noqa: E402

SCOPES = {52890969: "MOM/SR", 52890970: "CHREV", 52890971: "VIXREG",
          52890973: "DAYCOMBO", 52890974: "BREAKOUT"}
FXS = {"NAS100": "NDX.INDX", "USTEC": "NDX.INDX", "SpotCrude": "USOIL.FOREX",
       "XTIUSD": "USOIL.FOREX", "GER40": "GDAXI.INDX", "DE40": "GDAXI.INDX",
       "XAUUSD": "XAUUSD"}
SERVER_OFFSET_H = 3
POS_SELL_MIN, POS_BUY_MAX = 0.40, 0.60
ADX_MAX = 25.0
TQ_COOL = {"NDX.INDX": {16, 17, 19}}          # UTC saat
TQ_COOL_DOW = {"USOIL.FOREX": {3}}            # 0=Pzt → 3=Perşembe (ISO 4)


def ema_last(vals: np.ndarray, span: int) -> float:
    k = 2.0 / (span + 1)
    e = float(vals[-span])
    for v in vals[-span + 1:]:
        e = float(v) * k + e * (1 - k)
    return e


def adx30(sym: str, when: datetime, n: int = 14) -> float | None:
    r = rates_upto(sym, mt5.TIMEFRAME_M30, when, 3 * n + 10)
    if r is None or len(r) < 3 * n:
        return None
    h, l, c = r["high"].astype(float), r["low"].astype(float), r["close"].astype(float)
    a = 1.0 / n
    s_tr = s_p = s_m = 0.0
    adx = None
    for i in range(1, len(r)):
        up, dn = h[i] - h[i - 1], l[i - 1] - l[i]
        p = up if (up > dn and up > 0) else 0.0
        m = dn if (dn > up and dn > 0) else 0.0
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        if i == 1:
            s_tr, s_p, s_m = tr, p, m
            continue
        s_tr = s_tr * (1 - a) + tr * a
        s_p = s_p * (1 - a) + p * a
        s_m = s_m * (1 - a) + m * a
        if s_tr <= 0:
            continue
        pdi, mdi = 100 * s_p / s_tr, 100 * s_m / s_tr
        dx = 100 * abs(pdi - mdi) / (pdi + mdi) if (pdi + mdi) > 0 else 0.0
        adx = dx if adx is None else adx * (1 - a) + dx * a
    return adx


def gate_states(sym: str, fxs: str, direction: str, when: datetime,
                entry: float) -> dict:
    """Botun kapı tanımlarını karar anında yeniden hesapla (fail-open: None)."""
    out: dict = {}

    r1h = rates_upto(sym, mt5.TIMEFRAME_H1, when, 60)
    if r1h is not None and len(r1h) >= 55:
        c = r1h["close"].astype(float)
        e = ema_last(c, 50)
        above = float(c[-1]) > e
        out["trend"] = bool(above if direction == "BUY" else not above)
    else:
        out["trend"] = None

    r5 = rates_upto(sym, mt5.TIMEFRAME_M5, when, 48)
    if r5 is not None and len(r5) >= 20:
        hi, lo = float(r5["high"].max()), float(r5["low"].min())
        if hi > lo:
            pos = (entry - lo) / (hi - lo)
            out["pos_val"] = round(pos, 3)
            out["konum"] = bool(pos >= POS_SELL_MIN if direction == "SELL"
                                else pos <= POS_BUY_MAX)
        else:
            out["konum"] = None
    else:
        out["konum"] = None

    a = adx30(sym, when)
    out["adx_val"] = round(a, 1) if a is not None else None
    out["adx"] = bool(a < ADX_MAX) if a is not None else None

    utc = when - timedelta(hours=SERVER_OFFSET_H)
    cool = utc.hour in TQ_COOL.get(fxs, set()) or utc.weekday() in TQ_COOL_DOW.get(fxs, set())
    out["saat"] = not cool
    return out


def rep(name: str, sel: list[dict]) -> str:
    if not sel:
        return f"{name:<34} n=  0"
    n = len(sel)
    w = sum(1 for r in sel if r["pnl"] > 0)
    p = sum(r["pnl"] for r in sel)
    return (f"{name:<34} n={n:>3}  WR={100*w/n:5.1f}%  net={p:>9.1f}$  "
            f"ort={p/n:>7.1f}$")


def main() -> None:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    if not mt5.initialize():
        raise SystemExit(f"mt5.initialize() hata: {mt5.last_error()}")
    a, b = datetime.now() - timedelta(days=days), datetime.now() + timedelta(days=1)
    deals = mt5.history_deals_get(a, b) or []
    pos: dict = {}
    for d in deals:
        if d.magic not in SCOPES:
            continue
        p = pos.setdefault(d.position_id, {})
        if d.entry == 0:
            p.update(t=d.time, price=d.price, sym=d.symbol, magic=d.magic,
                     dirn="BUY" if d.type == 0 else "SELL")
        else:
            p["pnl"] = p.get("pnl", 0.0) + d.profit
            p["closed"] = True
    rows = [p for p in pos.values() if p.get("closed") and "t" in p]
    rows.sort(key=lambda p: p["t"])
    print(f"kapanmış işlem: {len(rows)} ({days} gün)\n", flush=True)

    out = []
    for p in rows:
        when = datetime.utcfromtimestamp(p["t"])
        fxs = FXS.get(p["sym"], p["sym"])
        g = gate_states(p["sym"], fxs, p["dirn"], when, float(p["price"]))
        out.append({**g, "scope": SCOPES[p["magic"]], "sym": fxs,
                    "dirn": p["dirn"], "pnl": p["pnl"],
                    "t": when - timedelta(hours=SERVER_OFFSET_H)})

    GATES = ["trend", "konum", "adx", "saat"]
    print("[1] TEK TEK KAPILAR — kapı ancak elediği küme ZARARLIYSA haklıdır")
    print(f"  {'':34}{'GEÇEN küme':>46}{'ELENEN küme':>48}")
    for g in GATES:
        ok = [r for r in out if r.get(g) is True]
        no = [r for r in out if r.get(g) is False]
        print(f"  {g:<8} {rep('geçen', ok)}")
        print(f"  {'':<8} {rep('ELENEN', no)}"
              f"   → kapının kazandırdığı: {-sum(r['pnl'] for r in no):+.1f}$")

    print("\n[2] KOMBİNASYONLAR — hepsi geçerse aç")
    best = []
    for k in range(1, len(GATES) + 1):
        for combo in itertools.combinations(GATES, k):
            keep = [r for r in out if all(r.get(g) is not False for g in combo)]
            drop = [r for r in out if any(r.get(g) is False for g in combo)]
            if not keep:
                continue
            net = sum(r["pnl"] for r in keep)
            best.append((net, combo, keep, drop))
    best.sort(reverse=True, key=lambda x: x[0])
    base = sum(r["pnl"] for r in out)
    print(f"  {'KAPISIZ (bugünkü hâl)':<34} n={len(out):>3}  "
          f"WR={100*sum(1 for r in out if r['pnl']>0)/len(out):5.1f}%  net={base:>9.1f}$")
    for net, combo, keep, drop in best[:10]:
        w = sum(1 for r in keep if r["pnl"] > 0)
        print(f"  {'+'.join(combo):<34} n={len(keep):>3}  WR={100*w/len(keep):5.1f}%  "
              f"net={net:>9.1f}$  (elenen {len(drop)} işlem {sum(r['pnl'] for r in drop):+.0f}$)")

    print("\n[3] SCOPE BAZINDA — hangi scope hangi kapıyı hak ediyor")
    for sc in sorted({r["scope"] for r in out}):
        sel = [r for r in out if r["scope"] == sc]
        print(f"\n  ── {sc} ── {rep('tümü', sel)}")
        for g in GATES:
            no = [r for r in sel if r.get(g) is False]
            if no:
                print(f"       {g:<6} elenecek: {rep('', no).strip()}")

    print("\n[4] HAFTA HAFTA — kapısız vs en iyi kombo")
    if best:
        _, combo, keep, _ = best[0]
        keep_ids = {id(r) for r in keep}
        wk = defaultdict(lambda: [0.0, 0.0, 0, 0])
        for r in out:
            y, w, _ = r["t"].isocalendar()
            k = f"{y}-H{w:02d}"
            wk[k][0] += r["pnl"]; wk[k][2] += 1
            if id(r) in keep_ids:
                wk[k][1] += r["pnl"]; wk[k][3] += 1
        print(f"  en iyi kombo: {'+'.join(combo)}")
        print(f"  {'hafta':<10}{'kapısız':>16}{'kombo':>16}{'fark':>12}")
        for k in sorted(wk):
            v = wk[k]
            print(f"  {k:<10}{v[0]:>11.0f}$ ({v[2]:>2}){v[1]:>11.0f}$ ({v[3]:>2})"
                  f"{v[1]-v[0]:>11.0f}$")
    print("\nBITTI")


if __name__ == "__main__":
    main()
