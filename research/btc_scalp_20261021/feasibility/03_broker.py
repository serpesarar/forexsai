"""İcra gerçekçiliği: Binance 1m vs Pepperstone BTCUSD M1 (BID) örtüşen pencere.

(a) bar-içi aralık (bp), ardışık açılış boşluğu
(b) aynı giriş dakikalarında simetrik braket (H=60) sonucu: Binance yolu vs broker BID yolu (maliyetsiz),
    ve broker gerçekçi icra (long giriş ask=bid+S, çıkış bid; short giriş bid, çıkış ask) vs Binance + 1×S maliyet.
(c) aynı-bar TP+SL belirsizlik oranı, kötümser/iyimser/OHLC-sezgisel puanlama ile EV sınırları.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

H = 60
LEVELS = [3, 5, 7.5, 10, 15, 20, 30, 50]
S_FIX = 15.0

bk = pd.read_parquet(f"{lib.DATA}/broker_btcusd_m1.parquet")
bn = pd.read_parquet(f"{lib.DATA}/btc_1m.parquet", columns=["ts", "open", "high", "low", "close"])
t0 = bk["ts_utc"].min()
t1 = min(bk["ts_utc"].max(), bn["ts"].max()) + pd.Timedelta(minutes=1)
n = int((t1 - t0) / pd.Timedelta(minutes=1))


def grid(df, tcol, cols):
    i = ((df[tcol] - t0) / pd.Timedelta(minutes=1)).to_numpy().astype(np.int64)
    k = (i >= 0) & (i < n)
    out = {}
    for c in cols:
        a = np.full(n, np.nan)
        a[i[k]] = df[c].to_numpy()[k]
        out[c] = a
    return out


B = grid(bn, "ts", ["open", "high", "low", "close"])
K = grid(bk, "ts_utc", ["open", "high", "low", "close", "spread_usd"])
both = ~np.isnan(B["close"]) & ~np.isnan(K["close"])
res = {"window_utc": [str(t0), str(t1)], "minutes": n, "common_minutes": int(both.sum())}

# (a) aralık
rb = (B["high"] - B["low"]) / B["open"] * 1e4
rk = (K["high"] - K["low"]) / K["open"] * 1e4
res["range_bp"] = {
    "binance_med": float(np.median(rb[both])), "binance_p90": float(np.percentile(rb[both], 90)),
    "broker_med": float(np.median(rk[both])), "broker_p90": float(np.percentile(rk[both], 90)),
    "ratio_med_of_ratios": float(np.median(rk[both] / np.maximum(rb[both], 1e-9))),
    "corr": float(np.corrcoef(rb[both], rk[both])[0, 1]),
    "broker_range_lt_spread_share": float(np.mean(rk[both] * K["open"][both] / 1e4 < S_FIX)),
}
gb = np.abs(B["open"][1:] / B["close"][:-1] - 1) * 1e4
gk = np.abs(K["open"][1:] / K["close"][:-1] - 1) * 1e4
okg = both[1:] & both[:-1]
res["open_gap_bp"] = {"binance_med": float(np.median(gb[okg])), "binance_p99": float(np.percentile(gb[okg], 99)),
                      "broker_med": float(np.median(gk[okg])), "broker_p99": float(np.percentile(gk[okg], 99))}

# (b) girişler: karar barı ve 60 dk penceresi iki kaynakta da tam
idx = np.arange(1, n - H)
win_ok = np.array([both[e - 1:e + H].all() for e in idx])
E = idx[win_ok]
res["entries"] = int(len(E))
res["entry_days"] = int(len(np.unique((E + int((t0 - lib.T0) / pd.Timedelta(minutes=1))) // 1440)))
W = E[:, None] + np.arange(H)[None, :]


def first_k(mat_bool):
    any_ = mat_bool.any(axis=1)
    k = np.where(any_, mat_bool.argmax(axis=1), H)
    return k


def sim(hh, ll, oo, cc, p_entry, tp_up, sl_dn, side, sl_fill_from_open=True, extra_exit_cost=0.0):
    """hh/ll/oo: pencere matrisleri (çıkış tarafı fiyatı). long: TP hh>=tp_up, SL ll<=sl_dn.
    short: tp_up = aşağı hedef (ll<=), sl_dn = yukarı stop (hh>=). Dönüş bp (giriş fiyatına göre), sınıf, amb, OHLC-sezgisel."""
    if side == 1:
        ktp = first_k(hh >= tp_up[:, None]); ksl = first_k(ll <= sl_dn[:, None])
    else:
        ktp = first_k(ll <= tp_up[:, None]); ksl = first_k(hh >= sl_dn[:, None])
    tpf = (ktp < ksl) & (ktp < H)
    slf = (ksl <= ktp) & (ksl < H)
    amb = (ktp == ksl) & (ktp < H)
    r = np.empty(len(p_entry))
    r[tpf] = side * (tp_up[tpf] / p_entry[tpf] - 1) * 1e4
    rows = np.arange(len(p_entry))
    kk = np.minimum(ksl, H - 1)
    op = oo[rows, kk]
    if side == 1:
        slpx = np.minimum(sl_dn, op) if sl_fill_from_open else sl_dn
    else:
        slpx = np.maximum(sl_dn, op) if sl_fill_from_open else sl_dn
    r[slf] = side * (slpx[slf] / p_entry[slf] - 1) * 1e4
    ts = ~(tpf | slf)
    r[ts] = side * (cc[ts, -1] / p_entry[ts] - 1) * 1e4
    r -= extra_exit_cost
    # OHLC sezgisi: belirsiz barda açılış hangi uca yakınsa o önce
    hb, lb = hh[rows, kk], ll[rows, kk]
    near_high_first = np.abs(op - hb) < np.abs(op - lb)
    tp_first_heur = near_high_first if side == 1 else ~near_high_first
    r_opt = r.copy()
    tp_ret = side * (tp_up / p_entry - 1) * 1e4 - extra_exit_cost
    r_opt[amb] = tp_ret[amb]
    r_heur = r.copy()
    r_heur[amb & tp_first_heur] = tp_ret[amb & tp_first_heur]
    cls = np.where(tpf, 1, np.where(slf, -1, 0))
    return r, cls, amb, r_opt, r_heur


bo, bh, bl, bc = (B[c][W] for c in ["open", "high", "low", "close"])
ko, kh, kl, kc = (K[c][W] for c in ["open", "high", "low", "close"])
S = np.maximum(K["spread_usd"][E], S_FIX)  # bar spread'i = minimum; tick medyanı 15$
rows = []
for b in LEVELS:
    f = b / 1e4
    for side in (1, -1):
        sd = "L" if side == 1 else "S"
        pb = B["open"][E]
        if side == 1:
            r1, c1, a1, o1, h1 = sim(bh, bl, bo, bc, pb, pb * (1 + f), pb * (1 - f), 1)
        else:
            r1, c1, a1, o1, h1 = sim(bh, bl, bo, bc, pb, pb * (1 - f), pb * (1 + f), -1)
        pk = K["open"][E]
        if side == 1:
            r2, c2, a2, o2, h2 = sim(kh, kl, ko, kc, pk, pk * (1 + f), pk * (1 - f), 1)
        else:
            r2, c2, a2, o2, h2 = sim(kh, kl, ko, kc, pk, pk * (1 - f), pk * (1 + f), -1)
        # broker gerçekçi: long giriş ask=bid+S, çıkış bid; short giriş bid, çıkış ask=bid+S (ask yolu = bid yolu + S)
        if side == 1:
            pe = pk + S
            r3, c3, a3, _, _ = sim(kh, kl, ko, kc, pe, pe * (1 + f), pe * (1 - f), 1)
        else:
            pe = pk
            Sm = S[:, None]
            r3, c3, a3, _, _ = sim(kh + Sm, kl + Sm, ko + Sm, kc + Sm, pe, pe * (1 - f), pe * (1 + f), -1)
        cost_bin = S / pb * 1e4
        r1n = r1 - cost_bin
        rows.append({
            "bp": b, "side": sd, "n": len(E),
            "agree_class": float((c1 == c2).mean()),
            "binance_tp": float((c1 == 1).mean()), "broker_tp": float((c2 == 1).mean()),
            "binance_ts": float((c1 == 0).mean()), "broker_ts": float((c2 == 0).mean()),
            "amb_binance": float(a1.mean()), "amb_broker": float(a2.mean()),
            "gross_bp_binance": float(r1.mean()), "gross_bp_broker_bid": float(r2.mean()),
            "net_bp_binance_plus_S": float(r1n.mean()), "net_bp_broker_real": float(r3.mean()),
            "net_R_binance_plus_S": float(r1n.mean() / b), "net_R_broker_real": float(r3.mean() / b),
            "evR_binance_pess": float(r1.mean() / b), "evR_binance_heur": float(h1.mean() / b),
            "evR_binance_opt": float(o1.mean() / b),
            "evR_broker_pess": float(r2.mean() / b), "evR_broker_opt": float(o2.mean() / b),
            "mean_abs_diff_bp": float(np.abs(r1 - r2).mean()),
        })
df = pd.DataFrame(rows)
df.to_csv(f"{lib.OUT}/broker_compare.csv", index=False)
res["spread_used_med_usd"] = float(np.median(S))
json.dump(res, open(f"{lib.OUT}/broker_compare.json", "w"), indent=1)
print(json.dumps(res, indent=1))
pd.set_option("display.width", 250)
print(df.round(3).to_string())
