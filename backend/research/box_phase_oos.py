"""box_phase_oos.py — faz kurallarının DIŞ-ÖRNEKLEM doğrulaması (kutuda çalışır).

Neden kutuda: 1m bar geçmişi (~99k bar) ve tam deal geçmişi MT5'te; panele
taşımak yerine replay'i kaynağın yanında koşup yalnız TABLOYU döndürüyoruz.

Ne yapar:
  1. Tüm deal geçmişini pozisyonlara birleştirir (SL/TP seviyeleriyle).
  2. Her broker sembolü için elde edilebilen en derin 1m barı çeker.
  3. `phase_rules` (botun ÇALIŞTIRDIĞI kural modülü) ile her işlemi yeniden çözer.
  4. Sonuçları üç eksende kırar:
       · dönem  : kural setinin çıkarıldığı ay (İÇ) vs ondan ÖNCESİ (DIŞ/OOS)
       · sembol : NASDAQ (kural kapsamı) vs DAX/petrol (kapsam dışı kontrol)
       · hafta  : haftalık kararlılık (tek haftanın taşıdığı sonuç güvenilmez)

⚠️ ZAMAN EKSENİ: MT5'in `time` alanı BROKER saatidir. Yarış çözümü tamamen
broker saatinde yapılır (deal ve bar aynı eksende → offset gerekmez). Yalnız
Faz-1'in seans/gün kapıları gerçek UTC ister; bunun için sunucu saati EET/EEST
(Europe/Athens) kabul edilip çevrilir — `--offset-min` ile elle de verilebilir.
Tick'ten offset ÖLÇÜLMEZ: piyasa kapalıyken tick bayattır ve yanlış değer verir
(2026-08-15 00:56 UTC'de −105 dk ölçüldü, doğrusu +180).

Çalıştırma (kutuda):
    python backend/research/box_phase_oos.py --since 2026-05-01 --split 2026-07-13
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

FX = {"NAS100": "NDX.INDX", "GER40": "GDAXI.INDX", "SpotCrude": "USOIL.FOREX",
      "USTEC": "NDX.INDX", "DE40": "GDAXI.INDX", "XTIUSD": "USOIL.FOREX"}
MAGIC = {0: "?", }
BAR_REQUEST = 99000          # MT5 tavanı ~99k


class Cfg:
    def __init__(self, **kw):
        self._o = kw

    def __getattr__(self, k):
        if k in self._o:
            return self._o[k]
        raise AttributeError(k)


PHASE1 = dict(NDX_SESSION_BLOCK_ENABLED=True,
              NDX_SESSION_BLOCK=(("22:00", "07:00"),),
              NDX_FRIDAY_BLOCK=True, NDX_WEEKEND_HOLD_BLOCK=True,
              NDX_SR_ENTRY_ENABLED=False)
OFF = dict(NDX_SESSION_BLOCK_ENABLED=False, NDX_FRIDAY_BLOCK=False,
           NDX_WEEKEND_HOLD_BLOCK=False, NDX_SR_ENTRY_ENABLED=True)


# ── zaman ekseni ────────────────────────────────────────────────────────────

def server_to_utc(epoch: int, fixed_offset_min: int | None) -> datetime:
    """Broker sunucu saatini gerçek UTC'ye çevir (DST'ye duyarlı)."""
    naive = datetime(1970, 1, 1) + timedelta(seconds=int(epoch))
    if fixed_offset_min is not None:
        return naive.replace(tzinfo=timezone.utc) - timedelta(minutes=fixed_offset_min)
    try:
        from zoneinfo import ZoneInfo
        return naive.replace(tzinfo=ZoneInfo("Europe/Athens")).astimezone(timezone.utc)
    except Exception:
        return naive.replace(tzinfo=timezone.utc) - timedelta(minutes=180)


# ── veri toplama ────────────────────────────────────────────────────────────

def connect() -> bool:
    kw = {}
    if getattr(config, "MT5_ACCOUNT", None):
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                  server=config.MT5_SERVER)
    path = getattr(config, "MT5_TERMINAL_PATH", "")
    return bool(mt5.initialize(path, **kw) if path else mt5.initialize(**kw))


def load_positions(since: datetime, offset_min: int | None) -> list[dict]:
    frm = since - timedelta(days=2)
    to = datetime.utcnow() + timedelta(days=2)
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
            continue                      # SL yoksa geometri replay'i anlamsız
        entry = float(i0.price)
        sl_dist = abs(entry - float(sl))
        tp_dist = abs(float(tp) - entry) if tp else 0.0
        if sl_dist <= 0:
            continue
        profit = sum(x.profit for x in ol)
        move = (float(last.price) - entry) * (1 if i0.type == mt5.DEAL_TYPE_BUY else -1)
        rows.append({
            "pid": pid, "sym": i0.symbol, "fx": FX.get(i0.symbol, i0.symbol),
            "dir": "BUY" if i0.type == mt5.DEAL_TYPE_BUY else "SELL",
            "magic": int(getattr(i0, "magic", 0) or 0),
            "t_srv": int(i0.time), "utc": server_to_utc(int(i0.time), offset_min),
            "entry": entry, "sl_dist": sl_dist, "tp_dist": tp_dist,
            "profit": float(profit), "move": move,
            "comment": str(i0.comment or ""),
            "usd_pt": (abs(profit) / abs(move)) if move and profit else 5.0,
        })
    rows.sort(key=lambda r: r["t_srv"])
    return rows


def load_bars(sym: str) -> tuple[list[dict], list[int]]:
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, BAR_REQUEST)
    if r is None or len(r) == 0:
        return [], []
    bars = [{"t": int(x["time"]), "high": float(x["high"]), "low": float(x["low"]),
             "close": float(x["close"])} for x in r]
    return bars, [b["t"] for b in bars]


# ── replay ──────────────────────────────────────────────────────────────────

def simulate(t: dict, bars: list[dict], times: list[int], cfg,
             probation: bool = False) -> dict | None:
    i0 = bisect_left(times, t["t_srv"])
    if i0 >= len(bars) - 6:
        return None
    entry, sl_dist = t["entry"], t["sl_dist"]
    sgn = 1 if t["dir"] == "BUY" else -1

    if probation:
        atr14 = pr.atr_simple(bars[max(0, i0 - 60):i0], 14)
        if atr14 is None:
            return None
        n = int(pr.flag(cfg, "PROBATION_BARS"))
        seg = bars[i0:i0 + n]
        cancel, _, _ = pr.probation_verdict(t["dir"], entry, atr14, seg, n,
                                            float(pr.flag(cfg, "PROBATION_Z")))
        if cancel:
            return {"status": "cancelled", "pnl": 0.0, "win": None}
        entry = float(seg[-1]["close"])
        i0 += n

    pre = bars[max(0, i0 - 200):i0]
    scope = f"{t['fx']}:{t['dir']}"
    if t["magic"] == getattr(config, "MAGIC_NUMBER", 0) + 4:
        scope += ":DAYCOMBO"
    tp_dist, src = pr.tp_distance(scope, t["fx"], pre,
                                  t["tp_dist"] or sl_dist * 0.73, cfg,
                                  sl_dist=sl_dist)
    tp = entry + sgn * tp_dist
    sl = entry - sgn * sl_dist
    stop_min = float(pr.flag(cfg, "MGMT_TIME_STOP_MIN") or 0)
    deadline = bars[i0]["t"] + stop_min * 60 if stop_min else None

    for b in bars[i0:i0 + 5000]:
        hit_tp = (b["high"] >= tp) if t["dir"] == "BUY" else (b["low"] <= tp)
        hit_sl = (b["low"] <= sl) if t["dir"] == "BUY" else (b["high"] >= sl)
        if hit_sl:
            return {"status": "sl", "pnl": -sl_dist * t["usd_pt"], "win": False}
        if hit_tp:
            return {"status": "tp", "pnl": tp_dist * t["usd_pt"], "win": True}
        if deadline and b["t"] >= deadline:
            mv = sgn * (b["close"] - entry)
            return {"status": "time_stop", "pnl": mv * t["usd_pt"], "win": mv > 0}
    return None


def passes_phase1(t: dict, cfg) -> bool:
    blocked, _ = pr.entry_window_block(t["utc"], t["fx"], cfg)
    if blocked:
        return False
    if t["comment"].startswith("fxs-sr") and not pr.sr_entry_allowed(t["fx"], cfg):
        return False
    return True


def stats(rows: list[dict]) -> tuple[int, float, float]:
    res = [r for r in rows if r.get("win") is not None]
    wr = 100 * sum(1 for r in res if r["win"]) / len(res) if res else 0.0
    return len(res), wr, sum(r["pnl"] for r in rows)


def line(label: str, rows: list[dict]) -> None:
    n, wr, net = stats(rows)
    print(f"  {label:<34} n={n:<4} WR=%{wr:5.1f}  net={net:>9.0f}$")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-05-01")
    ap.add_argument("--split", default="2026-07-13",
                    help="bu tarihten ÖNCESİ dış-örneklem (kural bu veriden çıkmadı)")
    ap.add_argument("--offset-min", type=int, default=None,
                    help="sunucu−UTC farkı (dk). Verilmezse EET/EEST varsayılır.")
    a = ap.parse_args()

    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    since = datetime.fromisoformat(a.since)
    split = datetime.fromisoformat(a.split).replace(tzinfo=timezone.utc)

    pos = load_positions(since, a.offset_min)
    print(f"pozisyon={len(pos)}  ilk={pos[0]['utc']:%Y-%m-%d}  son={pos[-1]['utc']:%Y-%m-%d}")

    bars_by: dict[str, tuple[list, list]] = {}
    for sym in sorted({p["sym"] for p in pos}):
        mt5.symbol_select(sym, True)
        b, t = load_bars(sym)
        bars_by[sym] = (b, t)
        if b:
            print(f"  {sym:<10} 1m bar={len(b)}  "
                  f"{server_to_utc(b[0]['t'], a.offset_min):%Y-%m-%d} → "
                  f"{server_to_utc(b[-1]['t'], a.offset_min):%Y-%m-%d}")

    # ── zaman ekseni öz-denetimi: giriş fiyatı kendi barının içinde mi? ──
    print("\nzaman ekseni denetimi (giriş fiyatı kendi 1m barında):")
    for sym in sorted(bars_by):
        b, t = bars_by[sym]
        tol = 3.0 if sym in ("NAS100", "GER40") else 0.15
        ok = tot = 0
        for p in pos:
            if p["sym"] != sym or not b:
                continue
            i = bisect_left(t, p["t_srv"])
            if i >= len(b) or p["t_srv"] < t[0]:
                continue
            # işlemin İÇİNDE olduğu bar: times[i] > t_srv ise bir öncekidir
            j = i if (i < len(t) and t[i] == p["t_srv"]) else max(0, i - 1)
            tot += 1
            ok += int(b[j]["low"] - tol <= p["entry"] <= b[j]["high"] + tol)
        if tot:
            print(f"  {sym:<10} {ok}/{tot}  (%{100*ok/tot:.0f})")

    def run(cfg_kw, filt_kw=None, prob=False, sel=None) -> list[dict]:
        cfg = Cfg(**cfg_kw)
        filt = Cfg(**filt_kw) if filt_kw else None
        out = []
        for p in (sel if sel is not None else pos):
            b, t = bars_by.get(p["sym"], ([], []))
            if not b:
                continue
            if filt is not None and not passes_phase1(p, filt):
                continue
            r = simulate(p, b, t, cfg, probation=prob)
            if r:
                out.append(r)
        return out

    BASE = {**OFF, "TP_MODE": "fixed", "MGMT_TIME_STOP_MIN": 0}
    P0 = {**OFF, "TP_MODE": "atr", "TP_ATR_MULT": 2.5, "TP_ATR_PERIOD": 70,
          "TP_ATR_MIN_R": 0.3, "MGMT_TIME_STOP_MIN": 240}
    P01 = {**PHASE1, "TP_MODE": "atr", "TP_ATR_MULT": 2.5, "TP_ATR_PERIOD": 70,
           "TP_ATR_MIN_R": 0.3, "MGMT_TIME_STOP_MIN": 240}
    MODE = {**PHASE1, "TP_MODE": "fixed", "MGMT_TIME_STOP_MIN": 0,
            "PROBATION_BARS": 5, "PROBATION_Z": 1.28}

    groups = {
        "DIŞ-ÖRNEKLEM (kuraldan önce)": [p for p in pos if p["utc"] < split],
        "İÇ-ÖRNEKLEM (kuralın çıktığı ay)": [p for p in pos if p["utc"] >= split],
    }
    for gname, sel in groups.items():
        ndx = [p for p in sel if p["fx"] == "NDX.INDX"]
        print(f"\n═══ {gname} — NASDAQ (n={len(ndx)}) ═══")
        if not ndx:
            print("  işlem yok")
            continue
        gerc_w = sum(1 for p in ndx if p["profit"] > 0)
        print(f"  {'GERÇEKLEŞEN (canlı)':<34} n={len(ndx):<4} "
              f"WR=%{100*gerc_w/len(ndx):5.1f}  net={sum(p['profit'] for p in ndx):>9.0f}$")
        line("mevcut kural (BE'siz sim)", run(BASE, sel=ndx))
        print("  ── bileşenler tek tek (TP sabit tabanı) ──")
        line("A) yalnız zaman stopu 240", run({**BASE, "MGMT_TIME_STOP_MIN": 240}, sel=ndx))
        line("B) yalnız ATR TP (stop yok)",
             run({**OFF, "TP_MODE": "atr", "TP_ATR_MULT": 2.5, "TP_ATR_PERIOD": 70,
                  "TP_ATR_MIN_R": 0.3, "MGMT_TIME_STOP_MIN": 0}, sel=ndx))
        line("B2) ATR TP çarpan 4.0",
             run({**OFF, "TP_MODE": "atr", "TP_ATR_MULT": 4.0, "TP_ATR_PERIOD": 70,
                  "TP_ATR_MIN_R": 0.3, "MGMT_TIME_STOP_MIN": 0}, sel=ndx))
        line("C) yalnız Faz-1 filtreleri (TP sabit)",
             run({**PHASE1, "TP_MODE": "fixed", "MGMT_TIME_STOP_MIN": 0},
                 filt_kw=PHASE1, sel=ndx))
        print("  ── paketler ──")
        line("FAZ 0 (ATR TP+taban+stop240)", run(P0, sel=ndx))
        line("FAZ 0+1 (giriş filtreleri)", run(P01, filt_kw=PHASE1, sel=ndx))
        line("MOD-E (probasyon+TP sabit+Faz1)", run(MODE, filt_kw=PHASE1, prob=True, sel=ndx))
        line("MOD-E filtresiz", run({**OFF, "TP_MODE": "fixed", "MGMT_TIME_STOP_MIN": 0,
                                     "PROBATION_BARS": 5, "PROBATION_Z": 1.28},
                                    prob=True, sel=ndx))

    print("\n═══ KAPSAM DIŞI KONTROL (kural NASDAQ için yazıldı) ═══")
    for fx in ("GDAXI.INDX", "USOIL.FOREX"):
        sel = [p for p in pos if p["fx"] == fx]
        if not sel:
            continue
        print(f"  ── {fx} (n={len(sel)}) ──")
        line("mevcut kural", run(BASE, sel=sel))
        line("FAZ 0 kuralları uygulansaydı",
             run({**P0, "TP_ATR_SYMBOLS": (fx,)}, sel=sel))

    print("\n═══ HAFTALIK KARARLILIK — NASDAQ, FAZ 0 ═══")
    ndx = [p for p in pos if p["fx"] == "NDX.INDX"]
    weeks: dict[str, list] = defaultdict(list)
    for p in ndx:
        weeks[f"{p['utc']:%G-H%V}"].append(p)
    for wk in sorted(weeks):
        sel = weeks[wk]
        n0, wr0, net0 = stats(run(BASE, sel=sel))
        n1, wr1, net1 = stats(run(P0, sel=sel))
        n2, wr2, net2 = stats(run(P01, filt_kw=PHASE1, sel=sel))
        mark = "DIŞ" if sel[0]["utc"] < split else "İÇ "
        print(f"  {wk} [{mark}] n={n0:<3} mevcut %{wr0:4.0f}/{net0:+7.0f}$ · "
              f"faz0 %{wr1:4.0f}/{net1:+7.0f}$ · faz0+1 n={n2:<3} %{wr2:4.0f}/{net2:+7.0f}$")

    mt5.shutdown()


if __name__ == "__main__":
    main()
