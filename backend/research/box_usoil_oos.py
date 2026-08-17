"""box_usoil_oos.py — USOIL raporundaki kuralların DIŞ-ÖRNEKLEM sınaması.

Rapor (USOIL_ANALIZ_RAPORU_v2) 2026-07-13→08-13 arası 74 işlemden çıkarıldı ve
AYNI veride optimize edildi (n 74→34, WR %88.2 iddiası). NASDAQ'ta birebir aynı
kalıp dış-örneklemde çökmüştü (ATR-TP: WR ↑ ama para ↓). Bu script aynı sınamayı
USOIL için yapar: MT5'teki TÜM geçmiş çekilir, kuralın çıkarıldığı ay (İÇ) ile
ondan önceki dönem (DIŞ) ayrı ayrı raporlanır.

⚠️ CANLI DURUM (kuralları değerlendirirken referans budur):
  * USOIL_BREAKOUT_LIVE=False  → BREAKOUT scope'u zaten GÖLGE (rapor B1 uygulanmış)
  * ('USOIL.FOREX','SELL') BLOCKED → USOIL SELL zaten tamamen kapalı (B3'ten sıkı)
Bu yüzden "baz" senaryo, bu ikisi uygulanmış hâldir — yeni kurallar bunun
ÜSTÜNE ne katıyor, ölçülen budur.

Sınanan kurallar:
  B2  TP = 2 × ATR14(1m)                    (raporun şampiyonu)
  B3b BUY yalnız close > EMA50(4H)          (BUY tarafı trend kapısı)
  E7  Spike filtresi: giriş barı range > 2×ATR14(1m) → işlem yok
  E5  Scope cooldown: 3 ardışık SL → 4 saat duraklat
  E6  Cuma 20:00+ yalnız limit (fxs-sr)

Çalıştırma (kutuda):
    python backend/research/box_usoil_oos.py --split 2026-07-13
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
import phase_rules as pr  # type: ignore

SYM = "SpotCrude"
BREAKOUT_MAGIC = getattr(config, "MAGIC_NUMBER", 52890969) + 5
BAR_REQUEST = 99000


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
        sl_dist = abs(entry - float(sl))
        if sl_dist <= 0:
            continue
        profit = sum(x.profit for x in ol)
        move = (float(last.price) - entry) * (1 if i0.type == mt5.DEAL_TYPE_BUY else -1)
        rows.append({
            "pid": pid, "dir": "BUY" if i0.type == mt5.DEAL_TYPE_BUY else "SELL",
            "magic": int(getattr(i0, "magic", 0) or 0),
            "t_srv": int(i0.time), "utc": server_to_utc(int(i0.time)),
            "entry": entry, "sl_dist": sl_dist,
            "tp_dist": abs(float(tp) - entry) if tp else 0.0,
            "profit": float(profit), "comment": str(i0.comment or ""),
            "usd_pt": (abs(profit) / abs(move)) if move and profit else 1000.0,
        })
    rows.sort(key=lambda r: r["t_srv"])
    return rows


def load_bars(tf, n=BAR_REQUEST):
    r = mt5.copy_rates_from_pos(SYM, tf, 0, n)
    if r is None or len(r) == 0:
        return [], []
    bars = [{"t": int(x["time"]), "high": float(x["high"]), "low": float(x["low"]),
             "close": float(x["close"]), "open": float(x["open"])} for x in r]
    return bars, [b["t"] for b in bars]


def ema_at(bars: list[dict], times: list[int], t_srv: int, period: int) -> float | None:
    """t_srv anındaki (o barı DAHİL ETMEDEN) EMA — sızıntısız."""
    i = bisect_left(times, t_srv)
    seg = bars[max(0, i - period * 4):i]
    if len(seg) < period + 1:
        return None
    k = 2.0 / (period + 1)
    e = seg[0]["close"]
    for b in seg[1:]:
        e = b["close"] * k + e * (1 - k)
    return e


# ── kural bileşenleri ───────────────────────────────────────────────────────

def rule_trend_buy(t: dict, h4, h4t) -> bool:
    """B3b: BUY yalnız close > EMA50(4H). SELL zaten kapalı."""
    if t["dir"] != "BUY":
        return True
    e = ema_at(h4, h4t, t["t_srv"], 50)
    if e is None:
        return True                        # fail-open
    i = bisect_left(h4t, t["t_srv"])
    px = h4[max(0, i - 1)]["close"]
    return px > e


def rule_spike(t: dict, m1, m1t) -> bool:
    """E7: giriş barının range'i > 2×ATR14(1m) ise işlem yok."""
    i = bisect_left(m1t, t["t_srv"])
    j = i if (i < len(m1t) and m1t[i] == t["t_srv"]) else max(0, i - 1)
    if j < 20:
        return True
    bar = m1[j]
    atr = pr.atr_simple(m1[max(0, j - 30):j], 14)
    if not atr:
        return True
    return (bar["high"] - bar["low"]) <= 2.0 * atr


def rule_friday_limit(t: dict) -> bool:
    """E6: Cuma 20:00 UTC sonrası yalnız fxs-sr (limit)."""
    u = t["utc"]
    if u.isoweekday() == 5 and u.hour >= 20:
        return t["comment"].startswith("fxs-sr")
    return True


def apply_cooldown(rows: list[dict], streak_need=3, hours=4) -> set:
    """E5: aynı scope'ta N ardışık SL → `hours` saat duraklat. Bloklanan pid'ler."""
    blocked = set()
    streak: dict[str, int] = defaultdict(int)
    until: dict[str, float] = {}
    for t in rows:
        scope = f"{t['dir']}:{t['magic']}"
        if scope in until and t["t_srv"] < until[scope]:
            blocked.add(t["pid"])
            continue
        if t["profit"] < 0:
            streak[scope] += 1
            if streak[scope] >= streak_need:
                until[scope] = t["t_srv"] + hours * 3600
                streak[scope] = 0
        else:
            streak[scope] = 0
    return blocked


# ── simülasyon ──────────────────────────────────────────────────────────────

def simulate(t: dict, m1, m1t, tp_mode: str, tp_mult: float) -> dict | None:
    i0 = bisect_left(m1t, t["t_srv"])
    if i0 >= len(m1) - 6:
        return None
    entry, sl_dist = t["entry"], t["sl_dist"]
    sgn = 1 if t["dir"] == "BUY" else -1

    if tp_mode == "atr":
        atr = pr.atr_simple(m1[max(0, i0 - 40):i0], 14)
        if not atr:
            return None
        tp_dist = tp_mult * atr
    else:
        tp_dist = t["tp_dist"] or sl_dist

    tp = entry + sgn * tp_dist
    sl = entry - sgn * sl_dist
    for b in m1[i0:i0 + 5000]:
        hit_tp = (b["high"] >= tp) if t["dir"] == "BUY" else (b["low"] <= tp)
        hit_sl = (b["low"] <= sl) if t["dir"] == "BUY" else (b["high"] >= sl)
        if hit_sl:
            return {"pnl": -sl_dist * t["usd_pt"], "win": False}
        if hit_tp:
            return {"pnl": tp_dist * t["usd_pt"], "win": True}
    return None


def stats(rows):
    res = [r for r in rows if r and r.get("win") is not None]
    wr = 100 * sum(1 for r in res if r["win"]) / len(res) if res else 0.0
    return len(res), wr, sum(r["pnl"] for r in res)


def line(label, rows):
    n, wr, net = stats(rows)
    print(f"  {label:<40} n={n:<4} WR=%{wr:5.1f}  net={net:>9.0f}$")


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
    m1, m1t = load_bars(mt5.TIMEFRAME_M1)
    h4, h4t = load_bars(mt5.TIMEFRAME_H4, 5000)
    print(f"{SYM}: pozisyon={len(pos)}  1m bar={len(m1)}  4h bar={len(h4)}")
    if pos:
        print(f"  {pos[0]['utc']:%Y-%m-%d} → {pos[-1]['utc']:%Y-%m-%d}")

    # eksen denetimi
    ok = tot = 0
    for p in pos:
        i = bisect_left(m1t, p["t_srv"])
        j = i if (i < len(m1t) and m1t[i] == p["t_srv"]) else max(0, i - 1)
        if j < len(m1) and p["t_srv"] >= m1t[0]:
            tot += 1
            ok += int(m1[j]["low"] - 0.05 <= p["entry"] <= m1[j]["high"] + 0.05)
    print(f"zaman ekseni: giriş fiyatı kendi 1m barında {ok}/{tot}\n")

    # CANLI DURUM: BREAKOUT gölgede + SELL kapalı → baz bu
    live_base = [p for p in pos
                 if p["magic"] != BREAKOUT_MAGIC and p["dir"] != "SELL"]
    cooldown_blocked = apply_cooldown(live_base)

    groups = {
        "DIŞ-ÖRNEKLEM (rapordan önce)": [p for p in live_base if p["utc"] < split],
        "İÇ-ÖRNEKLEM (raporun çıktığı ay)": [p for p in live_base if p["utc"] >= split],
    }

    for gname, sel in groups.items():
        print(f"═══ {gname} — n={len(sel)} ═══")
        if not sel:
            print("  işlem yok\n"); continue
        w = sum(1 for p in sel if p["profit"] > 0)
        print(f"  {'GERÇEKLEŞEN (canlı durum bazı)':<40} n={len(sel):<4} "
              f"WR=%{100*w/len(sel):5.1f}  net={sum(p['profit'] for p in sel):>9.0f}$")

        base = [simulate(p, m1, m1t, "orig", 0) for p in sel]
        line("baz (sim, orijinal TP)", base)

        print("  ── rapor kuralları tek tek ──")
        for mult in (1.5, 2.0, 2.5):
            line(f"B2) TP = {mult}×ATR14(1m)",
                 [simulate(p, m1, m1t, "atr", mult) for p in sel])
        line("B3b) BUY yalnız EMA50(4H) üstü",
             [simulate(p, m1, m1t, "orig", 0) for p in sel if rule_trend_buy(p, h4, h4t)])
        line("E7) spike filtresi",
             [simulate(p, m1, m1t, "orig", 0) for p in sel if rule_spike(p, m1, m1t)])
        line("E5) scope cooldown (3 SL → 4s)",
             [simulate(p, m1, m1t, "orig", 0) for p in sel if p["pid"] not in cooldown_blocked])
        line("E6) Cuma 20:00+ yalnız limit",
             [simulate(p, m1, m1t, "orig", 0) for p in sel if rule_friday_limit(p)])

        print("  ── paketler ──")
        filt = [p for p in sel if rule_trend_buy(p, h4, h4t) and rule_spike(p, m1, m1t)
                and rule_friday_limit(p) and p["pid"] not in cooldown_blocked]
        line("C2-filtreler (TP orijinal)",
             [simulate(p, m1, m1t, "orig", 0) for p in filt])
        line("C2-tam (filtreler + TP=2×ATR14)",
             [simulate(p, m1, m1t, "atr", 2.0) for p in filt])
        print()

    print("═══ HAFTALIK KARARLILIK (C2-tam) ═══")
    weeks: dict[str, list] = defaultdict(list)
    for p in live_base:
        weeks[f"{p['utc']:%G-H%V}"].append(p)
    for wk in sorted(weeks):
        sel = weeks[wk]
        filt = [p for p in sel if rule_trend_buy(p, h4, h4t) and rule_spike(p, m1, m1t)
                and rule_friday_limit(p) and p["pid"] not in cooldown_blocked]
        n0, wr0, net0 = stats([simulate(p, m1, m1t, "orig", 0) for p in sel])
        n1, wr1, net1 = stats([simulate(p, m1, m1t, "atr", 2.0) for p in filt])
        mark = "DIŞ" if sel[0]["utc"] < split else "İÇ "
        print(f"  {wk} [{mark}] baz n={n0:<3} %{wr0:4.0f}/{net0:+7.0f}$ · "
              f"C2 n={n1:<3} %{wr1:4.0f}/{net1:+7.0f}$")

    mt5.shutdown()


if __name__ == "__main__":
    main()
