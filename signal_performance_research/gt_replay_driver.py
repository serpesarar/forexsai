"""Ground-truth driver: reuse the production-validated replay_signal_row to walk
every resolved signal against the real 1m bars, then aggregate corrected WR per
model and symbol vs the production-reported status.

Uses the SAME TP/SL helpers production resolves with (calculate_target_prices /
calculate_stoploss_price from the MT5 1m entry) + 1m walk + OHLC bar-path tie
heuristic. Caveat: USOIL TP/SL config was changed 2026-05-27 (after these
signals), so USOIL levels reflect the new wider TP1 — reported separately.
"""
import sys, os, json, asyncio
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from services.signal_replay_1m import replay_signal_row  # noqa: E402

SYMBOL_FILE = {"XAUUSD": "xauusd", "NDX.INDX": "ustec",
               "USOIL.FOREX": "xtiusd", "GDAXI.INDX": "de40"}
PIP = {"XAUUSD": 0.1, "USOIL.FOREX": 0.01, "NDX.INDX": 1.0, "GDAXI.INDX": 1.0}


def pnl_pips(sym, direction, entry, exit_px):
    if not entry or not exit_px:
        return 0.0
    diff = (exit_px - entry) if direction == "BUY" else (entry - exit_px)
    return diff / PIP[sym]


def load_bars(sym):
    d = json.load(open(f"1MDATA/mt5_{SYMBOL_FILE[sym]}_1m_bars.json"))
    bars, keys = [], []
    for x in d["bars"]:
        ts = datetime.fromtimestamp(x["t"], tz=timezone.utc)
        bars.append({"ts": ts, "open": x["o"], "high": x["h"],
                     "low": x["l"], "close": x["c"]})
        keys.append(ts)
    return bars, keys


async def main():
    sigs = json.load(open("signal_performance_research/signals_priced.json"))
    bars = {s: load_bars(s) for s in SYMBOL_FILE}
    print(f"signals={len(sigs)}; bars loaded for {list(bars)}")

    from collections import defaultdict
    # gt buckets: completed(win)/stopped(loss)/expired(neutral)/nodata
    gm = defaultdict(lambda: defaultdict(int))   # model -> status -> n
    gs = defaultdict(lambda: defaultdict(int))   # symbol -> status -> n
    pm = defaultdict(lambda: [0, 0])             # model -> [prodwin, total]
    ps = defaultdict(lambda: [0, 0])             # symbol -> [prodwin, total]
    conf = defaultdict(int)
    n = 0
    dump = open("signal_performance_research/gt_per_signal.jsonl", "w")
    for s in sigs:
        sym = s["symbol"]
        if sym not in bars:
            continue
        b, k = bars[sym]
        r = await replay_signal_row(s, b, k)
        ok = r.get("replay_status") == "ok"
        st = r.get("corrected_status") if ok else r.get("replay_status")
        mt = s["model_type"]
        prod_win = 1 if s["status"] == "completed" else 0
        d = (s.get("ml_direction") or "").upper()
        gt_flag = {"completed": 1, "stopped": 0, "expired": -1}.get(st, None) if ok else None
        pips = 0.0
        if ok and st in ("completed", "stopped"):
            pips = pnl_pips(sym, d, r.get("entry_price"), r.get("corrected_exit_price"))
        dump.write(json.dumps({
            "sym": sym, "mt": mt, "dir": d,
            "t": int(datetime.fromisoformat(s["created_at"].replace("Z", "+00:00"))
                     .timestamp()),
            "tf": s.get("timeframe"), "combo": s.get("source_combo"),
            "regime": s.get("regime"), "prod_win": prod_win,
            "gt": gt_flag, "pips": round(pips, 2),
        }) + "\n")
        # only count signals the replay could actually evaluate
        if ok and st in ("completed", "stopped", "expired"):
            gm[mt][st] += 1; gs[sym][st] += 1
            pm[mt][0] += prod_win; pm[mt][1] += 1
            ps[sym][0] += prod_win; ps[sym][1] += 1
            gt_lbl = {"completed": "WIN", "stopped": "LOSS", "expired": "NEUT"}[st]
            conf[("WIN" if prod_win else "LOSS", gt_lbl)] += 1
        else:
            gm[mt][st] += 1; gs[sym][st] += 1
        n += 1
        if n % 10000 == 0:
            print(f"  ...{n}")

    def wr(d):
        w, l = d.get("completed", 0), d.get("stopped", 0)
        res = w + l
        return (w / res if res else 0), res, d.get("expired", 0), \
               d.get("no_candles", 0) + d.get("no_entry", 0)

    out = ["GROUND TRUTH (1m replay, production TP/SL helpers) vs PRODUCTION\n"]
    out.append("=== by SYMBOL ===")
    for sym in sorted(gs, key=lambda x: -ps[x][1]):
        gwr, res, neut, nod = wr(gs[sym])
        pwr = ps[sym][0] / ps[sym][1] if ps[sym][1] else 0
        out.append(f"  {sym:13s} prodWR {pwr:5.1%} (N={ps[sym][1]:6d}) | "
                   f"GT-WR {gwr:5.1%} (res={res:6d}) | neut={neut:5d} nodata={nod:5d} | Δ {gwr-pwr:+5.1%}")
    out.append("\n=== by MODEL ===")
    for mt in sorted(gm, key=lambda x: -pm[x][1]):
        gwr, res, neut, nod = wr(gm[mt])
        pwr = pm[mt][0] / pm[mt][1] if pm[mt][1] else 0
        out.append(f"  {mt:18s} prodWR {pwr:5.1%} (N={pm[mt][1]:6d}) | "
                   f"GT-WR {gwr:5.1%} (res={res:6d}) | neut={neut:5d} nodata={nod:5d} | Δ {gwr-pwr:+5.1%}")
    out.append("\n=== CONFUSION (prod -> ground-truth) ===")
    tot = sum(conf.values())
    for kk in sorted(conf, key=lambda x: -conf[x]):
        out.append(f"  prod={kk[0]:4s} -> GT={kk[1]:4s}  {conf[kk]:7d} ({conf[kk]/tot:5.1%})")
    pw = sum(conf[("WIN", g)] for g in ("WIN", "LOSS", "NEUT"))
    if pw:
        out.append(f"\nOf {pw} production WINS: GT-confirmed {conf[('WIN','WIN')]} "
                   f"({conf[('WIN','WIN')]/pw:.1%}), GT-loss {conf[('WIN','LOSS')]} "
                   f"({conf[('WIN','LOSS')]/pw:.1%}), GT-neutral {conf[('WIN','NEUT')]} "
                   f"({conf[('WIN','NEUT')]/pw:.1%})")
    text = "\n".join(out)
    print(text)
    open("signal_performance_research/ground_truth_results.txt", "w").write(text)
    dump.close()
    print("\nper-signal GT dumped -> gt_per_signal.jsonl")


asyncio.run(main())
