"""box_usoil_exit_oos.py — USOIL WinRate raporunun ÇIKIŞ kuralı: dış-örneklem.

Rapor (2026-08-18) TP=1.0R + BE@0.3R→giriş+0.1R kuralını 2026-07-13→08-14
penceresindeki 74 işlemden çıkardı ve AYNI veride ölçtü (WR %48.6→%73.0,
+793$→+4.485$). Panel tarafında bağımsız simülatörle birebir doğrulandı
(%73.0 / +4.433$) — aritmetik sağlam.

Kalan soru: kural o aya mı özgü? MT5 geçmişinde daha ESKİ USOIL işlemleri var;
bu script kuralı hem raporun ayında hem ondan ÖNCEKİ dönemde koşturur.

Ek olarak TP taraması yapar: panel tarafı ölçümünde WR TP'den bağımsız (BE
belirliyor) ama PARA TP ile birlikte artıyordu — raporun seçtiği 1.0R para
açısından optimal değil. Bunun dış-örneklemde de geçerli olup olmadığı ölçülür.

Çalıştırma (kutuda): python backend/research/box_usoil_exit_oos.py --split 2026-07-13
"""
from __future__ import annotations

import argparse
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

SYM = "SpotCrude"
BREAKOUT_MAGIC = getattr(config, "MAGIC_NUMBER", 52890969) + 5


def server_to_utc(epoch: int) -> datetime:
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


def load_positions(since: datetime) -> list[dict]:
    frm = since - timedelta(days=2)
    to = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)
    deals = mt5.history_deals_get(frm, to) or []
    orders = mt5.history_orders_get(frm, to) or []
    sltp: dict[int, tuple[float, float]] = {}
    for o in sorted(orders, key=lambda x: x.time_setup):
        pid = int(getattr(o, "position_id", 0) or 0)
        if pid and pid not in sltp and (o.sl or o.tp):
            sltp[pid] = (float(o.sl or 0), float(o.tp or 0))
    ins: dict[int, list] = defaultdict(list)
    outs: dict[int, list] = defaultdict(list)
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
        sl, tp = sltp.get(pid, (0.0, 0.0))
        if not sl:
            continue
        entry = float(i0.price)
        sl_d = abs(entry - float(sl))
        if sl_d <= 0:
            continue
        profit = sum(x.profit for x in ol)
        move = (float(last.price) - entry) * (1 if i0.type == mt5.DEAL_TYPE_BUY else -1)
        rows.append({
            "pid": pid, "dir": "BUY" if i0.type == mt5.DEAL_TYPE_BUY else "SELL",
            "magic": int(getattr(i0, "magic", 0) or 0), "t_srv": int(i0.time),
            "utc": server_to_utc(int(i0.time)), "entry": entry, "sl_d": sl_d,
            "tp_d": abs(float(tp) - entry) if tp else 0.0, "profit": float(profit),
            "usd_pu": (abs(profit) / abs(move)) if move and profit else 1000.0,
        })
    rows.sort(key=lambda r: r["t_srv"])
    return rows


def simulate(t, bars, times, tp_r=None, be_r=None, be_off=0.10):
    sgn = 1 if t["dir"] == "BUY" else -1
    entry, sl_d = t["entry"], t["sl_d"]
    tp_d = t["tp_d"] if tp_r is None else tp_r * sl_d
    if tp_d <= 0:
        return None
    i0 = bisect_left(times, t["t_srv"])
    if i0 >= len(bars) - 2:
        return None
    tp = entry + sgn * tp_d
    sl = entry - sgn * sl_d
    armed = False
    for b in bars[i0:i0 + 6000]:
        fav = (b["high"] - entry) if sgn > 0 else (entry - b["low"])
        adv = (b["low"] <= sl) if sgn > 0 else (b["high"] >= sl)
        tph = (b["high"] >= tp) if sgn > 0 else (b["low"] <= tp)
        if adv:
            r = (sl - entry) * sgn / sl_d
            return {"r": r, "pnl": r * sl_d * t["usd_pu"], "win": r > 0}
        if tph:
            return {"r": tp_d / sl_d, "pnl": tp_d * t["usd_pu"], "win": True}
        if be_r and not armed and fav >= be_r * sl_d:
            armed = True
            sl = entry + sgn * be_off * sl_d
    return None


def stats(rows):
    res = [r for r in rows if r]
    if not res:
        return 0, 0.0, 0.0, 0.0
    w = sum(1 for r in res if r["win"])
    return (len(res), 100 * w / len(res), sum(r["pnl"] for r in res),
            sum(r["r"] for r in res) / len(res))


def line(label, rows):
    n, wr, net, er = stats(rows)
    print(f"  {label:<38} n={n:<4} WR=%{wr:5.1f}  net={net:>8.0f}$  E[R]={er:+.3f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="2026-07-13")
    ap.add_argument("--since", default="2026-04-01")
    a = ap.parse_args()
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    split = datetime.fromisoformat(a.split).replace(tzinfo=timezone.utc)

    mt5.symbol_select(SYM, True)
    pos = load_positions(datetime.fromisoformat(a.since))
    r = mt5.copy_rates_from_pos(SYM, mt5.TIMEFRAME_M1, 0, 99000)
    bars = [{"t": int(x["time"]), "high": float(x["high"]), "low": float(x["low"]),
             "close": float(x["close"])} for x in r]
    times = [b["t"] for b in bars]
    print(f"{SYM}: pozisyon={len(pos)}  1m bar={len(bars)}")
    print(f"  {pos[0]['utc']:%Y-%m-%d} → {pos[-1]['utc']:%Y-%m-%d}")

    ok = tot = 0
    for p in pos:
        i = bisect_left(times, p["t_srv"])
        j = i if (i < len(times) and times[i] == p["t_srv"]) else max(0, i - 1)
        if j < len(bars) and p["t_srv"] >= times[0]:
            tot += 1
            ok += int(bars[j]["low"] - 0.05 <= p["entry"] <= bars[j]["high"] + 0.05)
    print(f"zaman ekseni: {ok}/{tot}\n")

    # canlı durum: BREAKOUT gölgede + SELL kapalı
    live = [p for p in pos if p["magic"] != BREAKOUT_MAGIC and p["dir"] != "SELL"]
    groups = {
        "DIŞ-ÖRNEKLEM (rapordan önce)": [p for p in live if p["utc"] < split],
        "İÇ-ÖRNEKLEM (raporun ayı)": [p for p in live if p["utc"] >= split],
    }
    for gname, sel in groups.items():
        print(f"═══ {gname} — n={len(sel)} ═══")
        if len(sel) < 5:
            print("  yeterli işlem yok\n"); continue
        w = sum(1 for p in sel if p["profit"] > 0)
        print(f"  {'GERÇEKLEŞEN (canlı)':<38} n={len(sel):<4} "
              f"WR=%{100*w/len(sel):5.1f}  net={sum(p['profit'] for p in sel):>8.0f}$")
        line("baz (sim, orijinal geometri)", [simulate(p, bars, times) for p in sel])
        print("  ── raporun kuralı ve bileşenleri ──")
        line("yalnız BE@0.3R", [simulate(p, bars, times, be_r=0.3) for p in sel])
        line("yalnız TP=1.0R", [simulate(p, bars, times, tp_r=1.0) for p in sel])
        line("TP=1.0R + BE@0.3R ← RAPOR",
             [simulate(p, bars, times, tp_r=1.0, be_r=0.3) for p in sel])
        print("  ── TP taraması (BE@0.3R sabit) ──")
        for tpr in (1.5, 2.0, 2.5):
            line(f"TP={tpr}R + BE@0.3R",
                 [simulate(p, bars, times, tp_r=tpr, be_r=0.3) for p in sel])
        print()

    print("═══ HAFTALIK (TP=1.0R + BE@0.3R) ═══")
    weeks: dict[str, list] = defaultdict(list)
    for p in live:
        weeks[f"{p['utc']:%G-H%V}"].append(p)
    for wk in sorted(weeks):
        sel = weeks[wk]
        n0, wr0, net0, _ = stats([simulate(p, bars, times) for p in sel])
        n1, wr1, net1, _ = stats([simulate(p, bars, times, tp_r=1.0, be_r=0.3) for p in sel])
        mark = "DIŞ" if sel[0]["utc"] < split else "İÇ "
        print(f"  {wk} [{mark}] baz n={n0:<3} %{wr0:4.0f}/{net0:+7.0f}$ · "
              f"kural n={n1:<3} %{wr1:4.0f}/{net1:+7.0f}$")
    mt5.shutdown()


if __name__ == "__main__":
    main()
