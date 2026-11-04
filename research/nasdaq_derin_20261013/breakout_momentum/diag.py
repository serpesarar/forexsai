"""POST-HOC teşhis (kasa okunduktan SONRA; karar/seçim değiştirmez, yalnız mekanizma ve risk betimi).
H-S = NDX 1h F3 N=60 H=40 stop 1,5×ATR."""
import numpy as np
import pandas as pd
import bm

S = bm.ndx_sets()
F = bm.features(S["1h"], "1h")
m = bm.mask(F, "F3", 60, 1)


def ex_stats(H, k, delay=0, region="tum"):
    R, X = bm.outcome(F, H, k, 1)
    rg = bm.regions(F, H)[region] & np.isfinite(R)
    b = bm.base_map(F, R, rg, "yh")
    idx = np.where(m & rg)[0] + delay
    idx = idx[(idx < F["n"]) & rg[np.minimum(idx, F["n"] - 1)]]
    u = k if k else 1
    return len(idx), np.nanmean(R[idx]) / u, np.nanmean(R[idx] - b[idx]) / u


print("1) Stop duyarlılığı (H-S kuralı, tüm sinyaller, birim = stop mesafesi / stopsuzda ATR):")
for k in (0.0, 1.0, 1.5, 2.0, 3.0):
    n, r, e = ex_stats(40, k)
    print(f"   stop {k}: n={n} ortR {r:+.3f} fazla {e:+.3f}")
print("2) Gecikmeli giriş (sinyalden d mum sonra; ilk saatler mi taşıyor?):")
for d in (0, 1, 2, 4, 8):
    n, r, e = ex_stats(40, 1.5, delay=d)
    print(f"   gecikme {d}: n={n} fazla {e:+.3f}")
print("3) Sinyal saatine göre (UTC) fazla, stop 1,5, tüm sinyaller:")
R, X = bm.outcome(F, 40, 1.5, 1)
rg = bm.regions(F, 40)["tum"] & np.isfinite(R)
b = bm.base_map(F, R, rg, "yh")
idx = np.where(m & rg)[0]
hr = F["hour"][idx]
grp = np.select([(hr >= 22) | (hr < 7), hr < 13, hr < 20], ["Asya 22-07", "Avrupa 07-13", "ABD 13-20"], "akşam 20-22")
print(pd.DataFrame({"g": grp, "e": (R[idx] - b[idx]) / 1.5}).groupby("g").e.agg(["size", "mean"]).round(3).to_string())
print("4) Tek-pozisyon işlem listesi risk betimi (stop 1,5, R=stop):")
tr = bm.nonoverlap(idx, X)
r = R[tr] / 1.5
eq = np.cumsum(r)
dd = (eq - np.maximum.accumulate(eq)).min()
ls, cur = 0, 0
for v in r:
    cur = cur + 1 if v < 0 else 0
    ls = max(ls, cur)
hold_h = (X[tr] - tr).mean()
days = len(np.unique(F["date"][tr + 1]))
print(f"   işlem {len(tr)}, bağımsız giriş günü {days}, WR %{100 * (r > 0).mean():.1f}, ort {r.mean():+.3f}R, medyan {np.median(r):+.3f}R, "
      f"maks DD {dd:.1f}R, en uzun kayıp serisi {ls}, ort tutma {hold_h:.1f} mum, yılda ~{len(tr) / 10.3:.0f} işlem")
q = np.quantile(r, [0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
print("   dağılım q05/25/50/75/95/99:", np.round(q, 2), " | kazancın en iyi %10 işlemden payı:",
      round(float(np.sort(r)[::-1][:len(r) // 10].sum() / r.sum()), 2))
print("5) Aynı kural 30m/4h'te (tutma saat-eşdeğeri ~40 sa), stop 1,5, keşif+kasa:")
for tf, N, H in (("30m", 60, 40), ("4h", 10, 10), ("4h", 15, 10)):
    G = bm.features(S[tf], tf)
    R2, _ = bm.outcome(G, H, 1.5, 1)
    rg2 = bm.regions(G, H)["tum"] & np.isfinite(R2)
    b2 = bm.base_map(G, R2, rg2, "yh")
    i2 = np.where(bm.mask(G, "F3", N, 1) & rg2)[0]
    print(f"   {tf} F3 N={N} H={H}: n={len(i2)} fazla {np.mean(R2[i2] - b2[i2]) / 1.5:+.3f}")
