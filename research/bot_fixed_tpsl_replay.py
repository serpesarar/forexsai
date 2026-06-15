"""
RESEARCH ONLY — bot fixed-TP/SL 1m replay + PASS-filter EV proof.

Walks every pulse1/2/3 signal on the 3 bot scopes against the BOT'S FIXED
tp/sl (from ROBUST_SCOPES), NOT the signal's own multi-target ladder. Then
applies the "anti-extreme entry" PASS filter and measures WR + EV in R-units.

Does not touch prediction_logs or any production config. Pure read + compute.
"""
import sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict

sys.path.insert(0, "backend")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client

PAGE = 1000

# Bot's fixed levels (ROBUST_SCOPES in "yeni deneme/config.py")
SCOPES = {
    "NDX.INDX:BUY":     {"tp": 80.0,  "sl": 110.0, "is_pct": False},
    "GDAXI.INDX:SELL":  {"tp": 67.0,  "sl": 119.0, "is_pct": False},
    "USOIL.FOREX:SELL": {"tp": 1.04,  "sl": 1.49,  "is_pct": True},
}
MODELS = ["pulse1", "pulse2", "pulse3"]
MAX_HOLD_MIN = 1440   # walk up to ~1 trading day forward; gaps skip closed market

# M15 mean-reversion filter (from indicator_discrimination.py).
# BUY  wins on oversold dips:   stoch_k<45 & bb_pctb<0.45 & dist_ema20_atr<0
# SELL wins on overbought rallies: stoch_k>55 & bb_pctb>0.55 & dist_ema20_atr>0
def _fnum(v):
    try:
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None

def passes_filter(scope, f):
    """MOMENTUM-CONTINUATION filter, derived from fixed-tp/sl discrimination.
    The bot's far fixed tp rewards sustained pushes, not bounces."""
    g = lambda k: _fnum(f.get(k))
    if scope == "NDX.INDX:BUY":
        sk = g("M15_stoch_k"); de = g("M15_dist_ema20_atr"); sar = g("H1_sar_dist_atr")
        if None in (sk, de, sar): return None
        return (sk > 70) and (de > 0.8) and (sar > 0)          # buy strength/breakout
    if scope == "GDAXI.INDX:SELL":
        de200 = g("M15_dist_ema200_atr"); mh = g("H4_macd_hist"); adx = g("M15_adx_14")
        if None in (de200, mh, adx): return None
        return (de200 < -1.0) and (mh < 0) and (adx < 28)      # sell established downtrend
    if scope == "USOIL.FOREX:SELL":
        de = g("M30_dist_ema20_atr"); mh = g("M30_macd_hist"); sar = g("H1_sar_dist_atr")
        if None in (de, mh, sar): return None
        return (de < 0) and (mh < 0) and (sar < 0)             # sell downtrend continuation
    return None


def parse_iso(v):
    if not v: return None
    if isinstance(v, datetime): return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    try: return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception: return None


def load_bars(c, symbol):
    out = []; off = 0
    while True:
        r = (c.table("candle_cache").select("candle_time,open,high,low,close")
             .eq("symbol", symbol).eq("timeframe", "1m")
             .order("candle_time", desc=False).range(off, off + PAGE - 1).execute())
        page = (r.get("data") if isinstance(r, dict) else getattr(r, "data", [])) or []
        if not page: break
        for row in page:
            ts = parse_iso(row.get("candle_time"))
            if ts is None: continue
            out.append((ts, float(row["open"]), float(row["high"]),
                        float(row["low"]), float(row["close"])))
        if len(page) < PAGE: break
        off += PAGE
    out.sort(key=lambda x: x[0])
    return out


def load_signals(c, symbol, direction, since_iso):
    out = []; off = 0
    while True:
        r = (c.table("prediction_logs")
             .select("id,model_type,ml_direction,created_at,factors,status,resolution_reason")
             .eq("symbol", symbol).eq("ml_direction", direction)
             .in_("model_type", MODELS)
             .gte("created_at", since_iso)
             .order("created_at", desc=False).range(off, off + PAGE - 1).execute())
        page = (r.get("data") if isinstance(r, dict) else getattr(r, "data", [])) or []
        if not page: break
        out.extend(page)
        if len(page) < PAGE: break
        off += PAGE
    return out


import bisect
def replay_fixed(entry_ts, entry, direction, tp, sl, is_pct, bars, ts_keys):
    """Walk 1m bars from entry_ts; return ('WIN'/'LOSS'/'OPEN', exit_ts)."""
    if is_pct:
        tp_px = entry * (1 + tp/100) if direction == "BUY" else entry * (1 - tp/100)
        sl_px = entry * (1 - sl/100) if direction == "BUY" else entry * (1 + sl/100)
    else:
        tp_px = entry + tp if direction == "BUY" else entry - tp
        sl_px = entry - sl if direction == "BUY" else entry + sl
    end_ts = entry_ts + timedelta(minutes=MAX_HOLD_MIN)
    lo = bisect.bisect_left(ts_keys, entry_ts)
    for i in range(lo, len(bars)):
        ts, o, h, l, cl = bars[i]
        if ts > end_ts: break
        if direction == "BUY":
            hit_tp = h >= tp_px; hit_sl = l <= sl_px
        else:
            hit_tp = l <= tp_px; hit_sl = h >= sl_px
        if hit_tp and hit_sl:
            # in-bar ambiguity — OHLC heuristic
            bullish = cl >= o
            tp_first = (not bullish) if direction == "BUY" else bullish
            return ("WIN" if tp_first else "LOSS"), ts
        if hit_tp: return "WIN", ts
        if hit_sl: return "LOSS", ts
    return "OPEN", None


def ev_per_trade(wr, tp, sl):
    """EV in R-units where 1R = sl risk. win pays tp/sl R, loss pays -1R."""
    return wr * (tp/sl) - (1 - wr) * 1.0


def main():
    c = get_supabase_client()
    since = "2026-04-25T00:00:00+00:00"   # ~45d
    print(f"=== Bot fixed-TP/SL 1m replay (since {since[:10]}) ===\n")

    for scope, lv in SCOPES.items():
        symbol, direction = scope.split(":")
        bars = load_bars(c, symbol)
        ts_keys = [b[0] for b in bars]
        sigs = load_signals(c, symbol, direction, since)
        print(f"--- {scope}  tp{lv['tp']}/sl{lv['sl']}{'%' if lv['is_pct'] else ''}  "
              f"({len(bars)} bars, {len(sigs)} signals) ---")

        # ── Per-LOG replay (every signal row, incl. dup logs of same trade) ──
        rows = []  # (created_at, result, passed)
        open_cnt = 0
        # prep chronological list with entry + result for dedup pass
        evald = []  # (cat, entry, res, exit_ts, passed)
        for s in sigs:
            cat = parse_iso(s.get("created_at"))
            if cat is None: continue
            lo = bisect.bisect_left(ts_keys, cat)
            if lo >= len(bars): continue
            entry = bars[lo][1]
            if entry <= 0: continue
            res, exit_ts = replay_fixed(cat, entry, direction, lv["tp"], lv["sl"],
                                        lv["is_pct"], bars, ts_keys)
            f = s.get("factors") or {}
            p = passes_filter(scope, f)
            if res == "OPEN":
                open_cnt += 1
            else:
                rows.append((cat, res, p))
            evald.append((cat, entry, res, exit_ts, p))
        print(f"  resolved={len(rows)}  open/unresolved={open_cnt}")

        def wr_ev(subset, tag):
            n = len(subset); w = sum(1 for r in subset if r[1] == "WIN")
            if n == 0: print(f"  {tag:10s} n=0"); return
            wr = w/n; be = lv["sl"]/(lv["tp"]+lv["sl"]); ev = ev_per_trade(wr, lv["tp"], lv["sl"])
            verdict = "+EV" if wr > be else "-EV"
            print(f"  {tag:10s} n={n:4d}  WR={wr*100:5.1f}%  breakeven={be*100:4.1f}%  "
                  f"EV={ev:+.3f}R  {verdict}")

        print("  [per-LOG: every signal row]")
        wr_ev(rows, "ALL")
        passed = [r for r in rows if r[2] is True]
        wr_ev(passed, "PASS")
        failed = [r for r in rows if r[2] is False]
        wr_ev(failed, "FAIL")

        # ── Per-TRADE (bot dedup): one open position per scope, then cooldown ──
        # Mirrors the bot: when a trade opens it stays open until exit; signals
        # firing in that window are ignored; a cooldown gap follows each exit.
        evald.sort(key=lambda x: x[0])
        be = lv["sl"]/(lv["tp"]+lv["sl"])

        def dedup_trades(candidates, cooldown):
            """Bot model: enter on first eligible signal, hold to exit, cooldown."""
            trades = []; busy_until = None
            for cat, entry, res, exit_ts, p in candidates:
                if res == "OPEN":
                    continue
                if busy_until is not None and cat < busy_until:
                    continue
                trades.append(res)
                busy_until = (exit_ts or cat) + timedelta(minutes=cooldown)
            return trades

        for cd in (0, 30, 60):
            # UNFILTERED: bot enters on any signal
            unf = dedup_trades(evald, cd)
            # FILTERED: bot enters ONLY on signals passing the M15 filter
            filt_candidates = [e for e in evald if e[4] is True]
            flt = dedup_trades(filt_candidates, cd)
            def stat(trs):
                n = len(trs); w = sum(1 for r in trs if r == "WIN")
                wr = w/n if n else 0
                return n, wr, ev_per_trade(wr, lv["tp"], lv["sl"])
            un_n, un_wr, un_ev = stat(unf)
            fn, fwr, fev = stat(flt)
            print(f"  [cd={cd:2d}m] UNFILT trades={un_n:3d} WR={un_wr*100:5.1f}% EV={un_ev:+.3f}R "
                  f"{'+EV' if un_wr>be else '-EV'}   ||  MOMO-FILT trades={fn:3d} "
                  f"WR={fwr*100:5.1f}% EV={fev:+.3f}R {'+EV' if fwr>be else '-EV'}   (be={be*100:.1f}%)")

        # weekly walk-forward folds (PASS vs ALL)
        print("  weekly folds (wk: ALL_WR -> PASS_WR, pass_n):")
        by_wk = defaultdict(lambda: {"all": [], "pass": []})
        for cat, res, p in rows:
            wk = (cat - timedelta(days=cat.weekday())).strftime("%m-%d")
            by_wk[wk]["all"].append(res)
            if p is True: by_wk[wk]["pass"].append(res)
        folds_pass = folds_total = 0
        for wk in sorted(by_wk):
            a = by_wk[wk]["all"]; pa = by_wk[wk]["pass"]
            awr = sum(1 for x in a if x=="WIN")/len(a)*100 if a else 0
            pwr = sum(1 for x in pa if x=="WIN")/len(pa)*100 if pa else None
            be = lv["sl"]/(lv["tp"]+lv["sl"])*100
            beats = (pwr is not None and pwr > awr)
            if pa:
                folds_total += 1; folds_pass += 1 if beats else 0
            mark = ">be" if (pwr is not None and pwr > be) else ""
            print(f"    {wk}: {awr:5.1f} -> {('%.1f'%pwr) if pwr is not None else '  -':>5} "
                  f"(n={len(pa):3d}) {'PASS>ALL' if beats else ''} {mark}")
        if folds_total:
            print(f"  walk-forward: PASS beat ALL in {folds_pass}/{folds_total} weeks\n")
        else:
            print()


if __name__ == "__main__":
    main()
