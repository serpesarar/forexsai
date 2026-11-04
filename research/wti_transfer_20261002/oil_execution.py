"""Oil-scale adapter of the audited bid/ask execution engine; original source unchanged."""
import numpy as np
import pandas as pd

def simulate_grid(d: pd.DataFrame, spread_mult: float = 1, slip: float = .002,
                  geometry: str = "primary", delay: int = 0,
                  optimistic: bool = False, risk_mult: float = 5.,
                  hold_minutes: int = 90, reward_ratio: float = 1.5, window_start: int = 180, window_end: int = 930, deadline: int = 955, allowed_weekdays: int = 4, min_stop: float = .05) -> dict[int, pd.DataFrame]:
    """Vectorized bid/ask TP/SL engine, every eligible minute, both directions.

    Risk is frozen at the original decision, even in delayed-entry stress.
    Time exits are fills at next open (or earlier stop/target); 15:55 is a known
    daily deadline. Invalid future gaps are surfaced, never silently discarded.
    """
    t = d.t.to_numpy()
    risk = np.maximum(min_stop, risk_mult*d.atr70.shift().to_numpy())
    rr = reward_ratio
    if geometry == "fixed":
        risk = d.close.shift().to_numpy() * .0149
        rr = .0104/.0149
    elif geometry == "symmetric":
        rr = 1.
    valid = d.valid60.shift(fill_value=False).to_numpy() & np.isfinite(risk)
    valid &= d.weekday.lt(allowed_weekdays).to_numpy() & d.ny_min.between(window_start, window_end).to_numpy()
    valid &= np.r_[False, np.diff(t) == 60]
    ix = np.flatnonzero(valid)
    eix = ix+delay
    keep = eix < len(d)-1
    ix, eix = ix[keep], eix[keep]
    keep = t[eix]-t[ix] == 60*delay
    ix, eix = ix[keep], eix[keep]
    op, hp, lp, cp = [d[x].to_numpy() for x in ["open", "high", "low", "close"]]
    sp = d.spread_px.to_numpy()*spread_mult
    exact_ask = "ask_open" in d and not optimistic
    nymin = d.ny_min.to_numpy()
    out = {}
    for side in [1, -1]:
        unit = risk[ix]
        bid = cp[ix-1] if optimistic else op[eix]
        if side == 1 and exact_ask:
            entry = d.ask_open.to_numpy()[eix]+(spread_mult-1)*d.spread_px.to_numpy()[eix]+slip
        else:
            entry = bid+(sp[eix] if side == 1 else 0.)+side*slip
        target = entry+side*rr*unit
        stop = entry-side*unit
        active = np.ones(len(ix), dtype=bool)
        r = np.full(len(ix), np.nan)
        px = np.full(len(ix), np.nan)
        exitix = np.full(len(ix), -1, dtype=int)
        reason = np.full(len(ix), "", dtype="U12")
        ambiguous = np.zeros(len(ix), dtype=bool)
        for j in range(hold_minutes+1):
            w = np.flatnonzero(active)
            if not len(w):
                break
            k = eix[w]+j
            exists = k < len(d)
            gap = ~exists
            gap[exists] |= t[k[exists]] != t[eix[w[exists]]]+j*60
            if gap.any():
                wg = w[gap]
                kg = np.minimum(eix[wg]+max(j-1,0), len(d)-1)
                if side == -1 and exact_ask:
                    exitpx = d.ask_close.to_numpy()[kg]+(spread_mult-1)*d.spread_px.to_numpy()[kg]+slip
                else:
                    exitpx = cp[kg]+(sp[kg] if side == -1 else 0.)-side*slip
                px[wg], exitix[wg], reason[wg] = exitpx, kg, "data_gap"
                r[wg] = side*(exitpx-entry[wg])/unit[wg]
                active[wg] = False
            w, k = w[~gap], k[~gap]
            if not len(w):
                continue
            ask = sp[k] if side == -1 else 0.
            oo, hh, ll = op[k]+ask, hp[k]+ask, lp[k]+ask
            if side == -1 and exact_ask:
                extra = (spread_mult-1)*d.spread_px.to_numpy()[k]
                oo,hh,ll = [d[col].to_numpy()[k]+extra for col in ["ask_open","ask_high","ask_low"]]
            expired = (j == hold_minutes) | (nymin[k] >= deadline)
            hs = ll <= stop[w] if side == 1 else hh >= stop[w]
            ht = hh >= target[w] if side == 1 else ll <= target[w]
            # At the time-stop open, only an opening gap can beat the time exit.
            gapstop = oo <= stop[w] if side == 1 else oo >= stop[w]
            gaptarget = oo >= target[w] if side == 1 else oo <= target[w]
            hs = np.where(expired, gapstop, hs)
            ht = np.where(expired, gaptarget, ht)
            # An already crossed target at the open predates any intrabar stop.
            hs &= ~gaptarget
            ws = w[hs]
            if len(ws):
                val = np.minimum(oo[hs],stop[ws]) if side == 1 else np.maximum(oo[hs],stop[ws])
                val -= side*slip
                px[ws], exitix[ws], reason[ws] = val, k[hs], "stop"
                r[ws] = side*(val-entry[ws])/unit[ws]
                ambiguous[ws] = ht[hs] & ~expired[hs]
                active[ws] = False
            wt = w[ht & ~hs]
            if len(wt):
                val = target[wt]-side*slip  # no optimistic price improvement
                px[wt], exitix[wt], reason[wt] = val, k[ht & ~hs], "target"
                r[wt] = side*(val-entry[wt])/unit[wt]
                active[wt] = False
            we = w[expired & ~hs & ~ht]
            if len(we):
                val = oo[expired & ~hs & ~ht]-side*slip
                px[we], exitix[we], reason[we] = val, k[expired & ~hs & ~ht], "time"
                r[we] = side*(val-entry[we])/unit[we]
                active[we] = False
        good = np.isfinite(r)
        out[side] = pd.DataFrame({"decision": t[ix[good]], "entry_t": t[eix[good]],
            "exit_t": t[exitix[good]]+60, "entry_ix": eix[good], "exit_ix": exitix[good],
            "side": side, "entry": entry[good], "exit": px[good], "risk": unit[good],
            "R": r[good], "points": side*(px[good]-entry[good]), "reason": reason[good],
            "ambiguous": ambiguous[good], "day": d.day.to_numpy()[ix[good]],
            "hour": d.ny_min.to_numpy()[ix[good]]//60}).set_index("decision", drop=False)
    return out
