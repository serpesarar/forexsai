"""A2 — sonradan: kalıcı (otokorelasyonlu) rejim sinyalleri için dairesel kaydırma plasebosu (yıl-içi permütasyonla kıyas)."""
import runpy, json, os, io, contextlib, numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path("10_regime.py")
R_of, per, dkey, VIX = G["R_of"], G["per"], G["dkey"], G["VIX"]
cluster_t = G["cluster_t"]; rng = np.random.default_rng(3)
vd = lambda v: np.where(np.isnan(v), 0, np.where(v >= 18.4, 1, -1))
out = {}
for pname, msk in (("DISC", per == "DISC"), ("POST", (per == "OOS") | (per == "BLIND"))):
    real = np.nanmean(R_of(1, "base", vd(VIX))[msk]); vals = []
    n = len(VIX)
    for _ in range(1000):
        sh = rng.integers(60, n - 60)
        vals.append(np.nanmean(R_of(1, "base", vd(np.roll(VIX, sh)))[msk]))
    vals = np.array(vals)
    out[f"C01_k1_{pname}"] = dict(real=float(real), circ_pct=float((vals < real).mean()), circ_med=float(np.median(vals)))
print(out)
json.dump(out, open("results/circular_placebo.json", "w"), indent=1)
