"""KASA — 2026-07-01 → 2026-10-02, BİR KEZ açılır. Tanımlar run.py ile birebir."""
import json, numpy as np, pandas as pd
from engine import *  # noqa
from long_data import macro as load_macro
MAC = load_macro(); ET = "America/New_York"; BER = "Europe/Berlin"
L0 = pd.Timestamp("2026-07-01")
S = {
    "S1_NIGHT": Win("S1", ET, ("pcal", 18, 0), (0, 9, 30)), "S2_CTO": Win("S2", ET, (-1, 16, 0), (0, 9, 30)),
    "S3_EU": Win("S3", ET, (0, 1, 0), (0, 4, 0)), "S4_OD": Win("S4", ET, (0, 2, 0), (0, 3, 0)),
    "S5_EU_dn05": Win("S5", ET, (0, 1, 0), (0, 4, 0), "dn0.5"), "S6_EU_dn10": Win("S6", ET, (0, 1, 0), (0, 4, 0), "dn1.0"),
    "S7_NIGHT_dn05": Win("S7", ET, ("pcal", 18, 0), (0, 9, 30), "dn0.5"), "S8_NIGHT_dn10": Win("S8", ET, ("pcal", 18, 0), (0, 9, 30), "dn1.0"),
    "S9_EU_vix": Win("S9", ET, (0, 1, 0), (0, 4, 0), "vix"), "S10_EU_dn05vix": Win("S10", ET, (0, 1, 0), (0, 4, 0), "dn0.5vix"),
    "INTRA": Win("IN", ET, (0, 9, 30), (0, 16, 0)), "HOLD": Win("HO", ET, (-1, 16, 0), (0, 16, 0)),
}
out = {}
def rep(tag, ev):
    ev = ev[ev.index >= L0]
    d = dict(n=len(ev), ortR=ev.R.mean(), sumR=ev.R.sum(), R_sp3=ev.R_sp3.mean(), bp_net=ev.ret_net.mean() * 1e4,
             wr=(ev.R > 0).mean(), P=month_boot(ev) if len(ev) else np.nan)
    print(f"{tag:26s} n={d['n']:3d} ortR={d['ortR']:+.4f} ΣR={d['sumR']:+.2f} R(sp3)={d['R_sp3']:+.4f} bp_net={d['bp_net']:+.2f} wr={d['wr']:.2f} P={d['P']:.2f}")
    out[tag] = d
m1 = load_bars("ndx1m"); m1 = m1[m1.ts >= pd.Timestamp("2026-02-10", tz="UTC")].reset_index(drop=True)
m30 = load_bars("ndx30m_new")
print("=== NDX 1m (T+1dk + 1,5p) ===")
for k, w in S.items():
    rep("1m " + k, build_events(m1, w, (16, 0), False, MAC, ARR_USD, delay=1))
print("=== NDX 30m birebir ===")
for k, w in S.items():
    rep("30m " + k, build_events(m30, w, (16, 0), True, MAC, ARR_USD))
d1 = load_bars("dax1h"); d1 = d1[d1.ts >= pd.Timestamp("2025-06-01", tz="UTC")].reset_index(drop=True)
d30 = load_bars("dax30m")
print("=== DAX ===")
DX = {"DX_EU": (d1, Win("DE", ET, (0, 1, 0), (0, 4, 0)), (17, 0)), "DX_PRE": (d1, Win("DP", BER, (0, 8, 0), (0, 9, 0)), (17, 0)),
      "DX_EU_dn05": (d1, Win("DE5", ET, (0, 1, 0), (0, 4, 0), "dn0.5"), (17, 0)), "DX_EU_dn10": (d1, Win("DE10", ET, (0, 1, 0), (0, 4, 0), "dn1.0"), (17, 0)),
      "DX_NIGHT": (d30, Win("DN", BER, (-1, 17, 30), (0, 9, 0)), (17, 30))}
for k, (b, w, ref) in DX.items():
    rep(k, build_events(b, w, ref, True, None, ARR_EUR, ref_tz=BER))
json.dump(out, open("results/lockbox.json", "w"), indent=1, default=float)
