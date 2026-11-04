"""Motor doğrulama (prereg §10): (a) kayma 0 iken T03 olaylarında lib_trend.M1.simulate ile birebir;
(b) 3.000 rastgele olayda (piyasa/limit, iki yön, TP'li/TP'siz, kaymalı, 3 maliyet modu) kaba döngü ile birebir."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lib_st as L
import sleeves as SV

t0 = time.time()
E = SV.engine()
print(f"motor {time.time()-t0:.0f}s; sıcak dakika eşiği (DISC p99 |1m|) {E.hot_thr:.2f} bp")
ev = SV.core_events()
mine = E.simulate(ev.ent, ev.dir, ev.sl_d, ev.tp_d, ev.end, ev.sig, mode="base", slip=False)
ref = E.m1.simulate(ev.dec.to_numpy(), ev.dir.to_numpy(), ev.sl_d.to_numpy(), ev.tp_d.to_numpy(), ev.end.to_numpy(), ev.sig.to_numpy())
a, b = mine.R.to_numpy(), ref["R"]
okk = np.isfinite(a) | np.isfinite(b)
mism = np.sum(~(np.isclose(a[okk], b[okk], atol=1e-9, equal_nan=True)))
print(f"(a) T03 n={okk.sum()} lib_trend ile uyuşmazlık: {mism}; ortR mine {np.nanmean(a):+.4f} ref {np.nanmean(b):+.4f}")
rng = np.random.default_rng(5)
n = 3000
T = E.T
ent = rng.choice(T[(T > T[0] + 100000) & (T < T[-1] - 10000)], n)
d = rng.choice([1, -1], n)
px = E.O[E.row_at_or_after(ent)]
sl = px * rng.uniform(5, 300, n) * 1e-4
tp = np.where(rng.random(n) < 0.3, np.nan, sl * rng.choice([0.5, 1, 2, 4], n))
end = ent + rng.integers(3, 4000, n)
kind = rng.integers(0, 4, n)  # 0 piyasa, 1 limit skip, 2 limit market, 3 piyasa abs
mode = np.where(kind == 3, "abs", np.where(rng.random(n) < 0.3, "stress", "base"))
depth = px * rng.uniform(2, 40, n) * 1e-4
W = rng.choice([15, 60], n)
bad = 0
cnt = 0
for kd in range(4):
    for md in ("base", "stress", "abs"):
        for w in (15, 60):
            s = (kind == kd) & (mode == md) & ((W == w) | (kd in (0, 3)))
            if kd in (0, 3) and w == 60:
                continue
            if not s.any():
                continue
            lk = depth[s] if kd in (1, 2) else None
            fb = "market" if kd == 2 else "skip"
            r = E.simulate(ent[s], d[s], sl[s], tp[s], end[s], mode=md, slip=True, limit_k=lk, limit_W=int(w), limit_fallback=fb).R.to_numpy()
            ii = np.where(s)[0]
            for j, i in enumerate(ii):
                rb = L.brute(E, ent[i], d[i], sl[i], tp[i], end[i], mode=md, slip=True,
                             limit_k=(depth[i] if kd in (1, 2) else None), limit_W=int(w), fb=fb)
                cnt += 1
                if not ((np.isnan(rb) and np.isnan(r[j])) or abs(rb - r[j]) < 1e-9):
                    bad += 1
                    if bad < 5:
                        print("UYUŞMAZ", kd, md, w, i, r[j], rb)
print(f"(b) kaba döngü: {cnt} karşılaştırma, uyuşmazlık {bad}; süre {time.time()-t0:.0f}s")
assert mism == 0 and bad == 0
print("SELFTEST OK")
