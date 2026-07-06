"""
RESEARCH ONLY — hardening battery for the momentum filter across ALL 8 scopes.

Two correctness tests on top of the single-split battery:
  (1) MULTI-SPLIT walk-forward — filtered TEST WR/EV at 3 held-out split points
      (05-20, 05-27, 06-03). An edge must hold across windows, not one lucky cut.
  (2) FRICTION model — adverse entry+exit cost (spread+slippage) applied to fill,
      tp/sl levels AND breakeven, swept at 0x/1x/2x. Critical for tight targets
      (XAUUSD tp8). Frictionless 0x is the sanity baseline vs the prior runs.

Controls: the 3 PRODUCTION-validated scopes (NDX:BUY, GDAXI:SELL, USOIL:SELL)
are included so we can confirm the method reproduces their known verdicts.

Touches nothing. Pure read + compute.
"""
import sys, bisect
from datetime import datetime, timedelta, timezone
from collections import defaultdict

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client

from bot_fixed_tpsl_replay import MODELS, parse_iso, load_bars, _fnum

PAGE = 1000
SINCE = "2026-04-25T00:00:00+00:00"
SPLITS = ["2026-05-20T00:00:00+00:00", "2026-05-27T00:00:00+00:00", "2026-06-03T00:00:00+00:00"]
MAX_HOLD_MIN = 1440

# scope -> tp/sl, is_pct, factor suffix, friction unit (same unit as tp/sl: pts or %)
SCOPES = {
    # ── controls (already validated in production) ──
    "NDX.INDX:BUY":     {"tp": 80.0,  "sl": 110.0, "is_pct": False, "sfx": "M15", "fric": 1.0,  "ctrl": True},
    "GDAXI.INDX:SELL":  {"tp": 67.0,  "sl": 119.0, "is_pct": False, "sfx": "M15", "fric": 1.5,  "ctrl": True},
    "USOIL.FOREX:SELL": {"tp": 1.04,  "sl": 1.49,  "is_pct": True,  "sfx": "M30", "fric": 0.03, "ctrl": True},
    # ── the 5 new directions ──
    "NDX.INDX:SELL":    {"tp": 80.0,  "sl": 110.0, "is_pct": False, "sfx": "M15", "fric": 1.0,  "ctrl": False},
    "GDAXI.INDX:BUY":   {"tp": 67.0,  "sl": 119.0, "is_pct": False, "sfx": "M15", "fric": 1.5,  "ctrl": False},
    "USOIL.FOREX:BUY":  {"tp": 1.04,  "sl": 1.49,  "is_pct": True,  "sfx": "M30", "fric": 0.03, "ctrl": False},
    "XAUUSD:BUY":       {"tp": 8.0,   "sl": 15.0,  "is_pct": False, "sfx": "M30", "fric": 1.5,  "ctrl": False},
    "XAUUSD:SELL":      {"tp": 8.0,   "sl": 15.0,  "is_pct": False, "sfx": "M30", "fric": 1.5,  "ctrl": False},
}


def momo_pass(direction, sfx, f):
    g = lambda k: _fnum(f.get(k))
    sar = g("H1_sar_dist_atr")
    if direction == "BUY":
        sk = g(f"{sfx}_stoch_k"); de = g(f"{sfx}_dist_ema20_atr")
        if None in (sk, de, sar): return None
        return (sk > 70) and (de > 0.8) and (sar > 0)
    de = g(f"{sfx}_dist_ema20_atr"); mh = g(f"{sfx}_macd_hist")
    if None in (de, mh, sar): return None
    return (de < 0) and (mh < 0) and (sar < 0)


def blind_keys(direction, sfx):
    if direction == "BUY":
        return [(f"{sfx}_stoch_k", ">"), (f"{sfx}_dist_ema20_atr", ">"), ("H1_sar_dist_atr", ">")]
    return [(f"{sfx}_dist_ema20_atr", "<"), (f"{sfx}_macd_hist", "<"), ("H1_sar_dist_atr", "<")]


def load_signals(c, symbol, direction):
    out = []; off = 0
    while True:
        r = (c.table("prediction_logs").select("created_at,factors")
             .eq("symbol", symbol).eq("ml_direction", direction).in_("model_type", MODELS)
             .gte("created_at", SINCE).order("created_at", desc=False)
             .range(off, off+PAGE-1).execute())
        page = r.get("data") if isinstance(r, dict) else getattr(r, "data", [])
        if not page: break
        out.extend(page)
        if len(page) < PAGE: break
        off += PAGE
    return out


def replay_friction(entry_open, direction, tp, sl, is_pct, cin, cout, bars, tsk, entry_ts):
    """Adverse fill by cin; tp/sl placed from fill. Returns (res, exit_ts).
    cin/cout in same unit as tp/sl (pts or %)."""
    s = 1 if direction == "BUY" else -1
    if is_pct:
        fill = entry_open * (1 + s * cin / 100.0)
        tp_px = fill * (1 + s * tp / 100.0)
        sl_px = fill * (1 - s * sl / 100.0)
    else:
        fill = entry_open + s * cin
        tp_px = fill + s * tp
        sl_px = fill - s * sl
    end_ts = entry_ts + timedelta(minutes=MAX_HOLD_MIN)
    lo = bisect.bisect_left(tsk, entry_ts)
    for i in range(lo, len(bars)):
        ts, o, h, l, cl = bars[i]
        if ts > end_ts: break
        if direction == "BUY":
            hit_tp = h >= tp_px; hit_sl = l <= sl_px
        else:
            hit_tp = l <= tp_px; hit_sl = h >= sl_px
        if hit_tp and hit_sl:
            bullish = cl >= o
            tp_first = (not bullish) if direction == "BUY" else bullish
            return ("WIN" if tp_first else "LOSS"), ts
        if hit_tp: return "WIN", ts
        if hit_sl: return "LOSS", ts
    return "OPEN", None


def ev_fric(wr, tp, sl, cout):
    return wr * ((tp - cout) / sl) - (1 - wr) * ((sl + cout) / sl)


def be_fric(tp, sl, cout):
    return (sl + cout) / ((tp - cout) + (sl + cout))


def dedup(cands, cooldown=30):
    trades = []; busy = None
    for cat, res, exit_ts, p in cands:
        if res is None or res == "OPEN": continue
        if busy is not None and cat < busy: continue
        trades.append((cat, res, p))
        busy = (exit_ts or cat) + timedelta(minutes=cooldown)
    return trades


def stat(trades, tp, sl, cout):
    n = len(trades); w = sum(1 for t in trades if t[1] == "WIN")
    wr = w / n if n else 0.0
    return n, wr, ev_fric(wr, tp, sl, cout)


def main():
    c = get_supabase_client()
    for scope, lv in SCOPES.items():
        symbol, direction = scope.rsplit(":", 1)
        sfx = lv["sfx"]; tp = lv["tp"]; sl = lv["sl"]; ip = lv["is_pct"]
        bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
        sigs = load_signals(c, symbol, direction)

        # precompute per-signal: cat, entry_open, momo-pass, factors  (filter membership
        # is friction-independent; only outcomes change with friction)
        base = []
        for sgl in sigs:
            cat = parse_iso(sgl.get("created_at"))
            if cat is None: continue
            lo = bisect.bisect_left(tsk, cat)
            if lo >= len(bars): continue
            eo = bars[lo][1]
            if eo <= 0: continue
            f = sgl.get("factors") or {}
            base.append((cat, eo, momo_pass(direction, sfx, f), f))
        base.sort(key=lambda x: x[0])

        tag = "CONTROL" if lv["ctrl"] else "NEW"
        print(f"\n{'='*74}\n{scope}  [{tag}]  tp{tp}/sl{sl}{'%' if ip else ''}  "
              f"({len(bars)} bars, {len(base)} signals)")

        # cache outcomes per friction multiplier
        def evald_for(mult):
            cin = lv["fric"] * mult; cout = lv["fric"] * mult
            out = []
            for cat, eo, p, f in base:
                res, ex = replay_friction(eo, direction, tp, sl, ip, cin, cout, bars, tsk, cat)
                out.append((cat, res, ex, p, f))
            return out, cout

        # ── (1) Multi-split walk-forward at BASE friction (1x) ──
        ev1, cout1 = evald_for(1.0)
        be1 = be_fric(tp, sl, cout1)
        print(f"  (1) MULTI-SPLIT filtered TEST @1x friction (be={be1*100:.1f}%):")
        for sp in SPLITS:
            sd = parse_iso(sp)
            test = [e for e in ev1 if e[0] >= sd]
            unf = dedup([(e[0], e[1], e[2], e[3]) for e in test])
            un_n, un_wr, un_ev = stat(unf, tp, sl, cout1)
            ft = dedup([(e[0], e[1], e[2], e[3]) for e in test if e[3] is True])
            fn, fwr, fev = stat(ft, tp, sl, cout1)
            verdict = "+EV" if fwr > be1 else "-EV"
            print(f"      split {sp[5:10]}: UNFILT n={un_n:3d} WR={un_wr*100:5.1f}%  ||  "
                  f"MOMO n={fn:3d} WR={fwr*100:5.1f}% EV={fev:+.3f}R {verdict}")

        # ── (2) Friction sensitivity at the central split 05-27, filtered TEST ──
        sd = parse_iso(SPLITS[1])
        print(f"  (2) FRICTION sweep (split 05-27, filtered TEST):")
        for mult in (0.0, 1.0, 2.0):
            evx, coutx = evald_for(mult)
            bex = be_fric(tp, sl, coutx)
            test = [e for e in evx if e[0] >= sd]
            ft = dedup([(e[0], e[1], e[2], e[3]) for e in test if e[3] is True])
            fn, fwr, fev = stat(ft, tp, sl, coutx)
            verdict = "+EV" if fwr > bex else "-EV"
            print(f"      {mult:.0f}x (cout={coutx:.3f}, be={bex*100:4.1f}%): "
                  f"MOMO n={fn:3d} WR={fwr*100:5.1f}% EV={fev:+.3f}R {verdict}")

        # ── (3) BLIND thresholds from TRAIN(<05-27) wins, applied to TEST @1x ──
        train = [e for e in ev1 if e[0] < sd]; test = [e for e in ev1 if e[0] >= sd]
        wins_tr = [e for e in train if e[1] == "WIN"]
        bk = blind_keys(direction, sfx); thr = {}
        for k, side in bk:
            vals = sorted(v for v in (_fnum(e[4].get(k)) for e in wins_tr) if v is not None)
            thr[k] = vals[len(vals)//2] if vals else None
        def bpass(f):
            for k, side in bk:
                v = _fnum(f.get(k))
                if v is None or thr[k] is None: return None
                if side == ">" and not (v > thr[k]): return False
                if side == "<" and not (v < thr[k]): return False
            return True
        tb = dedup([(e[0], e[1], e[2], bpass(e[4])) for e in test if bpass(e[4]) is True])
        bn, bwr, bev = stat(tb, tp, sl, cout1)
        print(f"  (3) BLIND→TEST @1x: n={bn:3d} WR={bwr*100:5.1f}% EV={bev:+.3f}R "
              f"{'+EV' if bwr>be1 else '-EV'}")


if __name__ == "__main__":
    main()
