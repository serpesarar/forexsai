"""box_runner_fix_oos.py — "kazananı koştur" canlıda uygulanabilir mi? (2026-10-20)

Bulgu: trade_manager runner'ı bid ≥ orig_tp'de TP'yi kaldırmaya çalışıyor; sunucu TP'si önce doluyor → 07-21'den beri
37 TP kapanışında 0 runner. Bu betik, botun yönettiği BUY işlemlerinde (MAGIC +0 MOM, +1 CHREV, +2 VIXREG; NAS100 +
GER40) gerçek M1 barlarıyla karşı-olgusal sınar (BE dahil DEĞİL — yalnız runner etkisi):

  BASE      sabit SL/TP (bugünkü canlı davranış)
  IDEAL     araştırma kuralı: high ≥ TP → TP kaldır, SL = TP − 0,6R, kapanışlarla 0,6R iz (canlıda yapılamıyor)
  ARM_a     kapanış ≥ TP − a·R → sunucu TP'si kaldırılır (sanal TP); kapanış ≥ TP görülürse runner (IDEAL gibi);
            TP'ye bar içinde değip kapanışta geri düşerse runner YOK, orijinal SL kalır (tarama ~1 dk kapanışı görür)
  LOCK_a    kapanış ≥ TP − a·R → TP kaldır + SL = max(SL, TP − 0,6R), sonra kapanışlarla 0,6R iz
Bar içi sıralama: önce SL (temkinli). En uzun tutma 5 gün. R = SL mesafesi. Dönem: ≤ 2026-07-21 araştırma, sonrası
bağımsız. Çalıştırma (kutuda): python backend/research/box_runner_fix_oos.py
"""
from __future__ import annotations

import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok.")
import config  # type: ignore  # noqa: E402

BASE_MAGIC = int(getattr(config, "MAGIC_NUMBER", 52890969))
MAGICS = {BASE_MAGIC, BASE_MAGIC + 1, BASE_MAGIC + 2}
SYMS = ("NAS100", "GER40")
SINCE = datetime(2026, 5, 15)
SPLIT = datetime(2026, 7, 21)
TRAIL_R = 0.6
HOLD_MIN = 5 * 24 * 60
ARMS = (0.1, 0.2, 0.3)
B = 5000


def connect() -> bool:
    return bool(mt5.initialize(login=config.MT5_LOGIN, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
                or mt5.initialize())


def load_trades() -> list[dict]:
    frm, to = SINCE - timedelta(days=3), datetime.now() + timedelta(days=3)
    deals = mt5.history_deals_get(frm, to) or []
    orders = mt5.history_orders_get(frm, to) or []
    sltp: dict[int, tuple[float, float]] = {}
    for o in sorted(orders, key=lambda x: x.time_setup):
        pid = int(getattr(o, "position_id", 0) or 0)
        if pid and pid not in sltp and o.sl and o.tp:
            sltp[pid] = (float(o.sl), float(o.tp))
    ins, outs = defaultdict(list), defaultdict(list)
    for d in deals:
        if d.symbol not in SYMS:
            continue
        (ins if d.entry == mt5.DEAL_ENTRY_IN else outs)[d.position_id].append(d)
    rows = []
    for pid, il in ins.items():
        i0 = il[0]
        if int(getattr(i0, "magic", 0) or 0) not in MAGICS or i0.type != mt5.DEAL_TYPE_BUY or pid not in sltp:
            continue
        sl, tp = sltp[pid]
        e = float(i0.price)
        if not (sl < e < tp):
            continue
        rows.append({"pid": pid, "sym": i0.symbol, "t": int(i0.time), "e": e, "sl": sl, "tp": tp,
                     "magic": int(i0.magic) - BASE_MAGIC, "closed": bool(outs.get(pid))})
    return sorted(rows, key=lambda r: r["t"])


def m1(sym: str, t: int) -> list[tuple]:
    r = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M1, datetime.fromtimestamp(t - 60, timezone.utc),
                             datetime.fromtimestamp(t + HOLD_MIN * 60, timezone.utc))
    if r is None:
        return []
    return [(int(x["time"]), float(x["high"]), float(x["low"]), float(x["close"])) for x in r if int(x["time"]) >= t - 59]


def sim(tr: dict, bars: list[tuple], mode: str, a: float = 0.0) -> float | None:
    e, sl, tp = tr["e"], tr["sl"], tr["tp"]
    d = e - sl
    server_tp, run, armed = (None if mode == "IDEAL" else tp), False, False
    for _t, h, l, c in bars:
        if l <= sl:
            return (sl - e) / d
        if server_tp is not None and h >= server_tp:
            return (server_tp - e) / d
        if mode == "IDEAL" and not run and h >= tp:
            run, server_tp = True, None
            sl = max(sl, tp - TRAIL_R * d)
        if mode == "ARM":
            if not armed and c >= tp - a * d:
                armed, server_tp = True, None
            if armed and not run and c >= tp:
                run = True
                sl = max(sl, tp - TRAIL_R * d)
        if mode == "LOCK" and not run and c >= tp - a * d:
            run, server_tp = True, None
            sl = max(sl, tp - TRAIL_R * d)
        if run:
            sl = max(sl, c - TRAIL_R * d)
    if not bars:
        return None
    return (bars[-1][3] - e) / d


def boot_p(x: list[float]) -> float:
    if len(x) < 5:
        return float("nan")
    n = len(x)
    return sum(1 for _ in range(B) if sum(random.choice(x) for _ in range(n)) > 0) / B


def main() -> None:
    random.seed(20261020)
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    trades = load_trades()
    variants = [("BASE", "BASE", 0.0), ("IDEAL", "IDEAL", 0.0)] + [(f"ARM_{a}", "ARM", a) for a in ARMS] + \
               [(f"LOCK_{a}", "LOCK", a) for a in ARMS]
    res = defaultdict(lambda: defaultdict(list))
    skipped = 0
    for tr in trades:
        bars = m1(tr["sym"], tr["t"])
        if len(bars) < 30:
            skipped += 1
            continue
        per = "arastirma" if datetime.fromtimestamp(tr["t"]) <= SPLIT else "bagimsiz"
        rs = {name: sim(tr, bars, mode, a) for name, mode, a in variants}
        if any(v is None for v in rs.values()):
            skipped += 1
            continue
        for key in (per, f"{per}|{tr['sym']}", "tum"):
            for name, v in rs.items():
                res[key][name].append(v)
    print(f"islem: {len(trades)} (M1 eksik/atlanan {skipped}); magics +0/+1/+2 BUY {SYMS}")
    for key in sorted(res):
        base = res[key]["BASE"]
        print(f"\n== {key}  n={len(base)}  BASE toplam {sum(base):+.1f}R ort {sum(base) / len(base):+.3f}R")
        for name in [v[0] for v in variants][1:]:
            x = res[key][name]
            diff = [p - q for p, q in zip(x, base)]
            print(f"  {name:9s} toplam {sum(x):+7.1f}R  ort {sum(x) / len(x):+.3f}R  fark {sum(diff):+6.1f}R  "
                  f"P(fark>0) {boot_p(diff):.3f}  kötüleşen {sum(1 for q in diff if q < -1e-9)}")


if __name__ == "__main__":
    main()
