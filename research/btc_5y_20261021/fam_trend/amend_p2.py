"""A1: H4 trend-filtreli hücreler için P2 (trend-koşullu taban + plasebo) ve swap etkisi."""
import sys, json; sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend")
import numpy as np, pandas as pd, lib_trend as lt, run_trend as rt
m1 = lt.M1(); F = rt.frames(m1); CL = {c["name"]: c for c in rt.cells(F, m1)}
H4 = F["H4"]; Hv = H4[~H4["excl"] & H4["atr"].notna()]
e30 = Hv["dec"].to_numpy() + 30 * 240
out = {}
for nm, d, col in (("H4D20-T-L", 1, "d_up"), ("H4D55-T-L", 1, "d_up"), ("H4D20-T-S", -1, "d_dn"), ("H4D55-T-S", -1, "d_dn")):
    s = Hv[Hv[col].to_numpy()]
    b = rt.mk(s, d, 2, 4, s["dec"].to_numpy() + 30 * 240)
    br = m1.simulate(b["dec"], b["dir"], b["sl"], b["tp"], b["end"], b["sig"])["R"]
    bsp = lt.split_of(b["dec"].to_numpy()); ok = np.isfinite(br) & (bsp != "")
    code = rt.keycode(b["dec"].to_numpy()[ok], b["dir"].to_numpy()[ok]); o = np.argsort(code)
    code, bR = code[o], br[ok][o]
    ev = CL[nm]["ev"].sort_values("dec").reset_index(drop=True)
    er = m1.simulate(ev["dec"], ev["dir"], ev["sl"], ev["tp"], ev["end"], ev["sig"])["R"]
    esp = lt.split_of(ev["dec"].to_numpy()); eok = np.isfinite(er) & (esp != "")
    res = {}
    for w, sps in (("FULL", ("DISC", "OOS", "BLIND")), ("POST", ("OOS", "BLIND")), ("DISC", ("DISC",)), ("OOS", ("OOS",)), ("BLIND", ("BLIND",))):
        em = eok & np.isin(esp, sps)
        ec = rt.keycode(ev["dec"].to_numpy()[em], ev["dir"].to_numpy()[em])
        lo_, hi_ = np.searchsorted(code, ec, "left"), np.searchsorted(code, ec, "right"); cnt = hi_ - lo_; g = cnt > 0
        U = np.random.default_rng(5).random((200, int(g.sum())))
        pm = bR[lo_[g] + np.floor(U * cnt[g]).astype(int)].mean(axis=1)
        bm = np.isin(bsp[ok][o], sps)
        res[w] = dict(n=int(em.sum()), cell=float(er[em].mean()), P2_mean=float(bR[bm].mean()), P2_n=int(bm.sum()),
                      P2_plac_mean=float(pm.mean()), P2_plac_pct=float(np.mean(pm < er[em][g].mean()) * 100))
    out[nm] = res
    print(nm, json.dumps(res))
# swap etkisi
sw = {}
for nm in ("GD55-L", "MX10-L-H6", "H4D20-T-L", "H4D55-T-L", "R0B-L", "MX10-L-1d"):
    ev = CL[nm]["ev"]; sp = lt.split_of(ev["dec"].to_numpy())
    a = (ev["dec"], ev["dir"], ev["sl"], ev["tp"], ev["end"], ev["sig"])
    r1 = m1.simulate(*a)["R"]
    L0, S0 = lt.SWAP_LONG, lt.SWAP_SHORT; lt.SWAP_LONG = lt.SWAP_SHORT = 0.0
    r0 = m1.simulate(*a)["R"]; lt.SWAP_LONG, lt.SWAP_SHORT = L0, S0
    ok = np.isfinite(r1) & np.isfinite(r0) & (sp != "")
    sw[nm] = dict(with_swap=float(r1[ok].mean()), no_swap=float(r0[ok].mean()), swap_cost_R=float(r0[ok].mean() - r1[ok].mean()))
    print(nm, sw[nm])
(lt.ROOT / "results" / "amend_p2_swap.json").write_text(json.dumps({"P2": out, "swap": sw}, indent=1))
