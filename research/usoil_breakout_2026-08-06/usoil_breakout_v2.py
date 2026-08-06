"""
V2: daha buyuk yapisal kirilimlar (N=96/144 bar) + 2-bar teyit (arka arkaya 2
kapanis seviyenin otesinde) — gurultu azaltma denemesi.
"""
import json
import numpy as np
from collections import Counter

SC = "/private/tmp/claude-501/-Users-melihcanodacioglu-Desktop-panel/7df45e44-1b5f-4bfc-bd93-c236cdbc275f/scratchpad"
d = np.load(f"{SC}/usoil_5m_indicators.npz")
o, h, l, c, v = d["o"], d["h"], d["l"], d["c"], d["v"]
atr14, adx, plus_di, minus_di = d["atr14"], d["adx"], d["plus_di"], d["minus_di"]
rsi14, macd_hist, dist_ema20_atr, vol_ratio = d["rsi14"], d["macd_hist"], d["dist_ema20_atr"], d["vol_ratio"]
with open(f"{SC}/usoil_5m_times.json") as f:
    times = json.load(f)
n = len(c)


def detect(N, confirm_bars, race_bars=48, target_atr=1.0):
    roll_max = np.array([h[max(0, i - N):i].max() if i > 0 else np.nan for i in range(n)])
    roll_min = np.array([l[max(0, i - N):i].min() if i > 0 else np.nan for i in range(n)])
    events = []
    for i in range(N + confirm_bars + 1, n - race_bars - 1):
        if atr14[i] <= 0 or np.isnan(roll_max[i]):
            continue
        # teyit: son confirm_bars kapanisin HEPSI seviyenin otesinde, ondan onceki degildi
        up_ok = all(c[i - k] > roll_max[i - k] for k in range(confirm_bars)) and \
                c[i - confirm_bars] <= roll_max[i - confirm_bars]
        dn_ok = all(c[i - k] < roll_min[i - k] for k in range(confirm_bars)) and \
                c[i - confirm_bars] >= roll_min[i - confirm_bars]
        if not (up_ok or dn_ok):
            continue
        direction = "BUY" if up_ok else "SELL"
        level = roll_max[i] if up_ok else roll_min[i]
        cont_target = c[i] + target_atr * atr14[i] if direction == "BUY" else c[i] - target_atr * atr14[i]
        rev_target = level - target_atr * atr14[i] if direction == "BUY" else level + target_atr * atr14[i]
        outcome = "AMBIGUOUS"
        for j in range(i + 1, min(i + 1 + race_bars, n)):
            if direction == "BUY":
                hc, hr = h[j] >= cont_target, l[j] <= rev_target
            else:
                hc, hr = l[j] <= cont_target, h[j] >= rev_target
            if hc and hr:
                outcome = "AMBIGUOUS"; break
            if hc:
                outcome = "GENUINE"; break
            if hr:
                outcome = "FAKE"; break
        events.append({"idx": i, "time": times[i], "direction": direction, "outcome": outcome})
    return events


for N in (48, 96, 144, 288):
    for cb in (1, 2, 3):
        ev = detect(N, cb)
        ev_r = [e for e in ev if e["outcome"] in ("GENUINE", "FAKE")]
        ev_r.sort(key=lambda e: e["time"])
        split = int(len(ev_r) * 0.7)
        train, test = ev_r[:split], ev_r[split:]

        def wr(rs, dirn=None):
            xs = [r for r in rs if dirn is None or r["direction"] == dirn]
            if not xs:
                return None, 0
            g = sum(1 for r in xs if r["outcome"] == "GENUINE")
            return 100 * g / len(xs), len(xs)

        b_tr, nb_tr = wr(train, "BUY"); b_te, nb_te = wr(test, "BUY")
        s_tr, ns_tr = wr(train, "SELL"); s_te, ns_te = wr(test, "SELL")
        print(f"N={N:>3d} confirm={cb}  n_total={len(ev_r):4d}  "
              f"BUY train={b_tr if b_tr is None else f'{b_tr:.1f}%'}(n={nb_tr}) test={b_te if b_te is None else f'{b_te:.1f}%'}(n={nb_te})  |  "
              f"SELL train={s_tr if s_tr is None else f'{s_tr:.1f}%'}(n={ns_tr}) test={s_te if s_te is None else f'{s_te:.1f}%'}(n={ns_te})")
