"""Canli 19 BREAKOUT olayini candle_cache 5m barlarindan yeniden uret (veri dogrulama)."""
import numpy as np, pandas as pd
from pathlib import Path

D = Path(__file__).resolve().parent / "data"
df = pd.read_parquet(D / "USOIL_FOREX_5m.parquet")
h, c, l = df.high.to_numpy(), df.close.to_numpy(), df.low.to_numpy()
N_DON, N_EMA, N_ATR = 48, 200, 14

ema = pd.Series(c).ewm(span=N_EMA, adjust=False).mean().to_numpy()
tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
atr = np.full(len(c), np.nan)
atr[1:] = pd.Series(tr).rolling(N_ATR).mean().to_numpy()   # bot: duz ortalama TR(14)

roll_max = pd.Series(h).rolling(N_DON).max().to_numpy()     # i dahil son 48
ev = []
for i in range(N_EMA + N_DON + 2, len(c)):
    lvl_now, lvl_prev = roll_max[i - 1], roll_max[i - 2]     # i'den ONCEKI 48 bar
    if c[i] > lvl_now and c[i - 1] <= lvl_prev and c[i] > ema[i] and not np.isnan(atr[i]):
        ev.append((df.candle_time.iloc[i], lvl_now, c[i], ema[i], atr[i]))
e = pd.DataFrame(ev, columns=["bar_time", "level", "close", "ema200", "atr"])
print(f"toplam olay: {len(e)}  ({e.bar_time.iloc[0]} → {e.bar_time.iloc[-1]})")

# canli log (kutu yerel saat = UTC-4) → UTC bar-KAPANIS saati; bar_time = kapanis - 5dk
live = [("2026-08-06 04:15", 75.936, 75.956, 75.454, 0.225), ("2026-08-06 06:26", 76.101, 76.111, 75.566, 0.202),
        ("2026-08-06 06:55", 76.271, 76.291, 75.506, 0.189), ("2026-08-06 07:55", 76.356, 76.492, 75.564, 0.153),
        ("2026-08-06 08:25", 76.522, 76.524, 75.675, 0.234), ("2026-08-06 09:10", 76.756, 76.888, 75.742, 0.253),
        ("2026-08-06 11:20", 77.173, 77.395, 75.952, 0.218), ("2026-08-06 11:55", 77.491, 78.202, 76.039, 0.306),
        ("2026-08-06 15:30", 78.436, 78.439, 76.727, 0.175), ("2026-08-06 16:50", 78.617, 78.634, 76.887, 0.255),
        ("2026-08-07 00:20", 78.698, 78.889, 77.746, 0.126), ("2026-08-07 00:30", 78.891, 78.984, 77.784, 0.141),
        ("2026-08-07 10:05", 77.770, 77.852, 77.798, 0.234), ("2026-08-07 11:00", 78.248, 78.364, 77.883, 0.263),
        ("2026-08-09 18:05", 78.648, 79.364, 77.945, 0.286), ("2026-08-10 13:05", 81.794, 81.819, 79.799, 0.201),
        ("2026-08-10 13:35", 81.871, 81.951, 79.944, 0.198), ("2026-08-10 14:21", 82.176, 82.411, 80.133, 0.170),
        ("2026-08-10 21:45", 82.589, 82.592, 81.248, 0.159)]
print(f"\n{'canli bar(UTC)':<18}{'lvl_canli':>10}{'lvl_repro':>10}{'cls_canli':>10}{'cls_repro':>10}{'atr_c':>7}{'atr_r':>7}  eslesme")
ok = 0
for t, lvl, cl, em, a in live:
    bt = pd.Timestamp(t, tz="UTC") + pd.Timedelta(hours=4) - pd.Timedelta(minutes=5)
    m = e[e.bar_time == bt]
    if len(m):
        r = m.iloc[0]; ok += 1
        print(f"{str(bt)[:16]:<18}{lvl:>10.3f}{r.level:>10.3f}{cl:>10.3f}{r.close:>10.3f}{a:>7.3f}{r.atr:>7.3f}  ✓")
    else:
        near = e[(e.bar_time >= bt - pd.Timedelta(minutes=15)) & (e.bar_time <= bt + pd.Timedelta(minutes=15))]
        print(f"{str(bt)[:16]:<18}{lvl:>10.3f}{'-':>10}{cl:>10.3f}{'-':>10}{a:>7.3f}{'-':>7}  ✗ (±15dk: {len(near)})")
print(f"\neslesen: {ok}/{len(live)}")
