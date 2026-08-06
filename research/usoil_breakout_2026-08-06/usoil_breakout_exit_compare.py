"""
USOIL BREAKOUT (Donchian+EMA200 BUY) icin cikis stratejisi karsilastirmasi:
sabit TP=1xATR vs BE+trailing. Kronolojik train/test, ayni giris kurali.

Veri: usoil_5m_indicators.npz + usoil_5m_times.json (bkz. usoil_breakout_
detect.py) — bu script'in calismasi icin scratchpad'deki bu iki dosyanin
ayni dizinde/yolda olmasi gerekir (SC degiskenini kendi yoluna gore ayarla).
"""
import json
import numpy as np

SC = "."  # usoil_5m_indicators.npz + usoil_5m_times.json buradan okunur
d = np.load(f"{SC}/usoil_5m_indicators.npz")
h, l, c = d["h"], d["l"], d["c"]
atr14 = d["atr14"]
with open(f"{SC}/usoil_5m_times.json") as f:
    times = json.load(f)
n = len(c)


def ema(x, p):
    k = 2.0 / (p + 1)
    e = np.empty_like(x, dtype=float)
    e[0] = x[0]
    for i in range(1, len(x)):
        e[i] = x[i] * k + e[i - 1] * (1 - k)
    return e


ema200 = ema(c, 200)
N = 48
roll_max = np.array([h[max(0, i - N):i].max() if i > 0 else np.nan for i in range(n)])
MAX_BARS = 288  # 24 saat tavan


def sim_trailing(sl_mult, trail_mult, be_after_r, idx_lo, idx_hi):
    events = []
    for i in range(max(N + 201, idx_lo), min(idx_hi, n - MAX_BARS - 1)):
        if atr14[i] <= 0 or np.isnan(roll_max[i]) or np.isnan(roll_max[i - 1]):
            continue
        up_break = c[i] > roll_max[i] and c[i - 1] <= roll_max[i - 1]
        if not up_break or c[i] <= ema200[i]:
            continue
        entry = c[i]
        atr_e = atr14[i]
        sl = entry - sl_mult * atr_e
        r_unit = entry - sl
        peak = entry
        be_armed = False
        outcome_r = None
        for j in range(i + 1, min(i + 1 + MAX_BARS, n)):
            if l[j] <= sl:
                outcome_r = (sl - entry) / r_unit
                break
            peak = max(peak, h[j])
            if not be_armed and (peak - entry) >= be_after_r * r_unit:
                be_armed = True
                sl = max(sl, entry)
            if be_armed:
                sl = max(sl, peak - trail_mult * atr_e)
        else:
            outcome_r = (c[min(i + MAX_BARS, n - 1)] - entry) / r_unit
        events.append(outcome_r)
    arr = np.array(events)
    if len(arr) == 0:
        return None
    wins = (arr > 0).sum()
    return len(arr), 100 * wins / len(arr), arr.mean(), arr.sum()


def sim_fixed_tp(tp_mult, sl_mult, idx_lo, idx_hi, race_bars=36):
    events = []
    for i in range(max(N + 201, idx_lo), min(idx_hi, n - race_bars - 1)):
        if atr14[i] <= 0 or np.isnan(roll_max[i]) or np.isnan(roll_max[i - 1]):
            continue
        up_break = c[i] > roll_max[i] and c[i - 1] <= roll_max[i - 1]
        if not up_break or c[i] <= ema200[i]:
            continue
        entry = c[i]
        atr_e = atr14[i]
        tp = entry + tp_mult * atr_e
        sl = entry - sl_mult * atr_e
        outcome = None
        for j in range(i + 1, min(i + 1 + race_bars, n)):
            if h[j] >= tp and l[j] <= sl:
                outcome = -1.0
                break
            if h[j] >= tp:
                outcome = tp_mult / sl_mult
                break
            if l[j] <= sl:
                outcome = -1.0
                break
        if outcome is not None:
            events.append(outcome)
    arr = np.array(events)
    return len(arr), 100 * (arr > 0).sum() / len(arr), arr.mean(), arr.sum()


if __name__ == "__main__":
    split = int(n * 0.7)
    print(f"split index={split}  train<={times[split][:10]}  test>{times[split][:10]}\n")

    print("=== sabit TP=1xATR (BE/trail YOK) ===")
    tr = sim_fixed_tp(1.0, 1.0, 0, split)
    te = sim_fixed_tp(1.0, 1.0, split, n)
    print(f"TRAIN n={tr[0]} WR={tr[1]:.1f}% ort_R={tr[2]:+.3f} toplam_R={tr[3]:+.1f}")
    print(f"TEST  n={te[0]} WR={te[1]:.1f}% ort_R={te[2]:+.3f} toplam_R={te[3]:+.1f}\n")

    print("=== BE + trailing varyantlari ===")
    for be_r, trail in [(0.5, 1.0), (1.0, 1.0), (1.0, 1.5), (1.5, 1.0)]:
        trn = sim_trailing(1.0, trail, be_r, 0, split)
        tst = sim_trailing(1.0, trail, be_r, split, n)
        print(f"BE={be_r}R trail={trail}xATR:")
        print(f"  TRAIN n={trn[0]} WR={trn[1]:.1f}% ort_R={trn[2]:+.3f} toplam_R={trn[3]:+.1f}")
        print(f"  TEST  n={tst[0]} WR={tst[1]:.1f}% ort_R={tst[2]:+.3f} toplam_R={tst[3]:+.1f}")
