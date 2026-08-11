"""GİRİŞ SKORU KAPISI — botun GERÇEK MT5 işlemleri üzerinde geriye dönük doğrulama.

Soru: entry_gate.py (8 koşullu skor + seans saat bloğu) canlıda uygulansaydı,
botun gerçekten açtığı işlemlerin hangileri elenirdi ve elenen küme kârlı mı,
zararlı mıydı? (Kapı ancak elediği küme NET ZARARLI ise haklıdır.)

Sızıntı yok: skor, işlemin AÇILIŞ ANINA kadarki barlarla hesaplanır
(copy_rates_from(..., açılış_zamanı, n) — sonraki barlar görülmez).

Çalıştırma (kutuda): python backend/research/entry_gate_live_validation.py [gün]
"""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "yeni deneme"))

import MetaTrader5 as mt5  # noqa: E402

from entry_gate import compute_entry_score  # noqa: E402

MAGIC_BASE = 52890969
SCOPES = {MAGIC_BASE: "MOM/SR", MAGIC_BASE + 1: "CHREV",
          MAGIC_BASE + 2: "VIXREG", MAGIC_BASE + 5: "BREAKOUT"}
# broker sembolü → ForexSAI adı (kapı kapsamı bu adla tanımlı)
FXS = {"NAS100": "NDX.INDX", "USTEC": "NDX.INDX", "SpotCrude": "USOIL.FOREX",
       "XAUUSD": "XAUUSD", "GER40": "GDAXI.INDX", "DE40": "GDAXI.INDX"}
GATED = {"MOM/SR", "VIXREG"}            # otopsi kapsamı (CHREV hariç)
SERVER_UTC_OFFSET = 3
MIN_SCORE = 7


def bars(symbol: str, tf: int, when: datetime, n: int):
    r = mt5.copy_rates_from(symbol, tf, when, n)
    if r is None or len(r) < 30:
        return None
    return [{"high": float(x["high"]), "low": float(x["low"]),
             "close": float(x["close"]), "volume": float(x["tick_volume"])} for x in r]


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    if not mt5.initialize():
        raise SystemExit(f"mt5.initialize() hata: {mt5.last_error()}")
    a, b = datetime.now() - timedelta(days=days), datetime.now() + timedelta(days=1)
    deals = mt5.history_deals_get(a, b) or []
    pos = defaultdict(dict)
    for d in deals:
        if d.magic not in SCOPES:
            continue
        p = pos[d.position_id]
        if d.entry == 0:
            p.update(t=d.time, price=d.price, dirn="BUY" if d.type == 0 else "SELL",
                     sym=d.symbol, magic=d.magic, vol=d.volume)
        else:
            p["pnl"] = p.get("pnl", 0.0) + d.profit
            p["closed"] = True
    rows = [p for p in pos.values() if p.get("closed") and "t" in p]
    rows.sort(key=lambda p: p["t"])
    print(f"kapanmış işlem: {len(rows)}  ({days} gün)\n")

    out = []
    for p in rows:
        scope = SCOPES[p["magic"]]
        fxs = FXS.get(p["sym"], p["sym"])
        when = datetime.utcfromtimestamp(p["t"])          # sunucu saati (MT5 böyle bekler)
        hour_utc = (when.hour - SERVER_UTC_OFFSET) % 24
        c1 = bars(p["sym"], mt5.TIMEFRAME_M1, when, 240)
        c5 = bars(p["sym"], mt5.TIMEFRAME_M5, when, 60)
        c30 = bars(p["sym"], mt5.TIMEFRAME_M30, when, 60)
        score, fails = compute_entry_score(fxs, p["dirn"], c1, c5, c30, hour_utc)
        out.append(dict(scope=scope, sym=fxs, dirn=p["dirn"], pnl=p["pnl"],
                        score=score, fails=fails, hour=hour_utc,
                        t=when - timedelta(hours=SERVER_UTC_OFFSET),
                        gated=scope in GATED))

    def rep(name, sel):
        if not sel:
            print(f"  {name:<34} n=   0")
            return
        n = len(sel)
        w = sum(1 for r in sel if r["pnl"] > 0)
        pnl = sum(r["pnl"] for r in sel)
        print(f"  {name:<34} n={n:>4}  WR={100*w/n:5.1f}%  netPnL={pnl:>9.1f}$  ort={pnl/n:>7.1f}$")

    for scope in ("MOM/SR", "VIXREG", "CHREV", "BREAKOUT"):
        sel = [r for r in out if r["scope"] == scope]
        if not sel:
            continue
        print(f"[{scope}]  (kapı kapsamında: {scope in GATED})")
        rep("tümü", sel)
        rep(f"kapıdan GEÇEN (skor≥{MIN_SCORE})", [r for r in sel if r["score"] >= MIN_SCORE])
        rep(f"kapının ELEDİĞİ (skor<{MIN_SCORE})", [r for r in sel if r["score"] < MIN_SCORE])
        for s in sel:
            pass
        print()

    print("[KAPI KAPSAMINDAKİ TÜM SCOPE'LAR — asıl karar tablosu]")
    gsel = [r for r in out if r["gated"]]
    rep("tümü", gsel)
    rep(f"GEÇEN (skor≥{MIN_SCORE})", [r for r in gsel if r["score"] >= MIN_SCORE])
    rep(f"ELENEN (skor<{MIN_SCORE})", [r for r in gsel if r["score"] < MIN_SCORE])
    print("\n  skor eşiği duyarlılığı (kapsam içi):")
    for thr in (5, 6, 7, 8):
        keep = [r for r in gsel if r["score"] >= thr]
        drop = [r for r in gsel if r["score"] < thr]
        kp = sum(r["pnl"] for r in keep)
        dp = sum(r["pnl"] for r in drop)
        print(f"    eşik≥{thr}: kalan n={len(keep):>3} PnL={kp:>9.1f}$ | elenen n={len(drop):>3} "
              f"PnL={dp:>9.1f}$  → kapının kazandırdığı: {-dp:>+9.1f}$")

    print("\n  sembol kırılımı (kapsam içi, eşik≥7):")
    for sym in sorted({r["sym"] for r in gsel}):
        s = [r for r in gsel if r["sym"] == sym]
        rep(f"{sym} tümü", s)
        rep(f"{sym} elenen", [r for r in s if r["score"] < MIN_SCORE])

    print("\n  en sık ihlal edilen koşullar (elenenler):")
    cnt = defaultdict(int)
    for r in gsel:
        if r["score"] < MIN_SCORE:
            for f in r["fails"]:
                cnt[f] += 1
    for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
        print(f"    {k:<20} {v}")
    print("\nBITTI")


if __name__ == "__main__":
    main()
