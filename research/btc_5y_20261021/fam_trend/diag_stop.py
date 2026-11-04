"""Teşhis: hem LONG hem SHORT stoplu tabanın pozitif çıkması motor hatası mı, gerçek trend mi?
(1) stop sonrası kalan hareket (stop→zaman çıkışı) stop yönünde mi devam ediyor?
(2) sentetik martingal (1m getirileri karıştırılmış yol) üzerinde aynı tabanların ortR'si ≈ −maliyet olmalı."""
import sys; sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend")
import numpy as np, lib_trend as lt, run_trend as rt
m1 = lt.M1()
CL = {c["name"]: c for c in rt.cells(rt.frames(m1), m1)}
def chk(m, name, lab):
    b = CL[name]["base"]
    sp = lt.split_of(b["dec"].to_numpy())
    for d in (1, -1):
        s = b[(b["dir"] == d).to_numpy() & (sp != "")]
        r = m.simulate(s["dec"], s["dir"], s["sl"], s["tp"], s["end"], s["sig"], spread=0.0)
        R = r["R"]; ok = np.isfinite(R)
        # stop sonrası kalan hareket (R biriminde, pozisyon yönünde)
        e = np.searchsorted(m.T, s["end"].to_numpy(), "left") - 1
        k = np.searchsorted(m.T, s["dec"].to_numpy(), "left")
        stp = ok & (r["typ"] == 0)
        ent = m.O[k]
        slp = ent - d * s["sl"].to_numpy()
        rem = d * (m.C[e] - slp) / s["sl"].to_numpy()
        print(f"{lab:6s} {name:10s} dir={d:+d} n={ok.sum()} ortR(spread0)={R[ok].mean():+.4f} stop payı={stp[ok].mean():.2f} "
              f"stop sonrası kalan(R)={rem[stp].mean():+.3f}")
for nm in ("H3-ROD", "MX10-L-1d", "R0B-L", "H4D20-L"):
    chk(m1, nm, "gerçek")
# sentetik martingal: 1m log getirilerini karıştır, OHLC'yi göreli kur
rng = np.random.default_rng(1)
lc = np.log(m1.C); r = np.diff(lc, prepend=lc[0]); r = rng.permutation(r)
nc = np.exp(np.log(m1.C[0]) + np.cumsum(r))
f = nc / m1.C
m1.O, m1.H, m1.L, m1.C = m1.O * f, m1.H * f, m1.L * f, nc
m1.__init__.__func__  # tabloları yeniden kur
import types
pad = (1 << m1.levels) + 2
lo = np.concatenate([m1.L, np.full(pad, np.inf)]); hi = np.concatenate([m1.H, np.full(pad, -np.inf)])
m1.mn, m1.mx = [lo], [hi]
for lv in range(1, m1.levels):
    s = 1 << (lv - 1); a, b = m1.mn[-1], m1.mx[-1]
    m1.mn.append(np.minimum(a, np.concatenate([a[s:], np.full(s, np.inf)])))
    m1.mx.append(np.maximum(b, np.concatenate([b[s:], np.full(s, -np.inf)])))
for nm in ("H3-ROD", "R0B-L"):
    chk(m1, nm, "sentet")
