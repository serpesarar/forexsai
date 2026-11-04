"""Tanılar: (a) 15m TF / 15m ufuk kümesindeki sistematik kaymanın kaynağı — son mumun dönüşü (1-gecikme)?
(b) ön-düzeltme adaylarının sessiz-seans / sürüklenme dökümü. Çalıştır: python3 tanilar.py"""
import numpy as np, pandas as pd
from _lit import HZ, NC, RES, RULES, TOLS, XS, load, query_grid, lib_lo
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
A = pd.read_csv(RES / "aile.csv"); E = pd.read_csv(RES / "aday_eleme.csv")

def cred(call, sy):
    return np.where(call == 0, np.nan, (call == sy).astype(float))

print("=== (a) Basit son-mum kuralları, aynı sorgu ızgarası (karşılaştırma için; aileye dahil DEĞİL) ===")
rows = []
for tf in ("1m", "5m", "15m", "1h"):
    D = load(tf); Q = np.load(RES / f"q_{tf}.npz"); qs = Q["qs"]
    body = np.sign(D["c"][qs] - D["o"][qs]).astype(int)
    for h, hn in enumerate(HZ[tf]):
        Y = Q["Y"][h]; sy = np.sign(np.nan_to_num(Y)).astype(int); ok = np.isfinite(Y) & (sy != 0) & (body != 0)
        b0 = Q["B0"][h]; bh = Q["BH"][h]
        for name, call in (("dönüş (−son gövde)", -body), ("devam (+son gövde)", body)):
            c = cred(call, sy)[ok]; c0 = np.where(b0 == 0, .5, (b0 == sy))[ok]; ch = np.where(bh == 0, .5, (bh == sy))[ok]
            rows.append(dict(tf=tf, ufuk=hn, kural=name, n=int(ok.sum()), isabet=100 * c.mean(), taban=100 * max(c0.mean(), ch.mean()),
                             fazla=100 * (c.mean() - max(c0.mean(), ch.mean())), hareket=float(np.mean(call[ok] * Y[ok]))))
r = pd.DataFrame(rows); print(r.round(2).to_string()); r.to_csv(RES / "tani_son_mum.csv", index=False)

print("\n=== (a2) 15m/15m aktif yapılandırmaların çağrıları ile dönüş kuralının uyumu ===")
D = load("15m"); Q = np.load(RES / "q_15m.npz"); qs = Q["qs"]; Z = np.load(RES / "calls_15m.npz"); C, Hc = Z["C"], Z["H"]
body = np.sign(D["c"][qs] - D["o"][qs]).astype(int)
f = A[(A.tf == "15m") & A.cid.notna()].sort_values("cid").reset_index(drop=True)
agree = []
for i in range(len(C)):
    m = C[i] != 0
    agree.append(np.mean(C[i][m] == -body[m]) if m.any() else np.nan)
f["donus_uyum"] = agree
g = f[f.ufuk == "15m"]
print("15m/15m: dönüşle uyum ortalaması", round(g.donus_uyum.mean(), 3), "| fazla≥2 olanlarda", round(g[g.fazla >= 2].donus_uyum.mean(), 3),
      "| korelasyon(uyum, fazla)", round(np.corrcoef(g.donus_uyum, g.fazla)[0, 1], 3))
print("15m/1h :", round(f[f.ufuk == '1h'].donus_uyum.mean(), 3), " 15m/1d:", round(f[f.ufuk == '1d'].donus_uyum.mean(), 3))

print("\n=== (b) Ön-düzeltme adayları: seans, uygunluk, yön dökümü ===")
tol_idx = {(r, t): i for i, (r, t) in enumerate(TOLS)}
out = []
for _, row in E[E.aday].iterrows():
    tf = row.tf; D = load(tf); Q = np.load(RES / f"q_{tf}.npz"); qs = Q["qs"]; tq = Q["tq"]
    h = HZ[tf].index(row.ufuk); xi = int(np.flatnonzero(XS == row.X)[0]); r = [x[0] for x in RULES].index(row.kural)
    c = int(row.uygunluk) + 2 * int(row.seans); Z = np.load(RES / "scan" / f"{tf}_{tol_idx[(row.rep, row.tol)]}.npz")
    u_, d_ = Z["up"][:, h, xi, r, c].astype(int), Z["dn"][:, h, xi, r, c].astype(int); n_ = u_ + d_
    qm = Z["qvalid"][:, xi] & (Z["qelig"][:, xi] if c & 1 else True); u = np.where(n_ > 0, u_ / np.maximum(n_, 1), np.nan)
    has = qm & (n_ >= row.n_min)
    call = np.where(has & (u >= (0.7 if row.guclu_oy else 0.5000001)), 1, np.where(has & (u <= (0.3 if row.guclu_oy else 0.4999999)), -1, 0))
    Y = Q["Y"][h]; sy = np.sign(np.nan_to_num(Y)); idx = np.flatnonzero((call != 0) & np.isfinite(Y) & (sy != 0))
    hr = D["hour"][qs[idx]]; asia = (hr >= 23) | (hr < 7); eu = (hr >= 7) & (hr < 13); us = (hr >= 13) & (hr < 21)
    corr = (call[idx] == sy[idx]); base_up = (sy[idx] > 0).mean()
    elig_q = Z["qelig"][idx, xi]
    def acc(m):
        return round(100 * corr[m].mean(), 1) if m.sum() else np.nan
    out.append(dict(tf=tf, rep=row.rep, tol=row.tol, X=row.X, kural=row.kural, seans=row.seans, ufuk=row.ufuk, n=len(idx),
                    pay_asya=round(asia.mean(), 2), pay_avr=round(eu.mean(), 2), pay_abd=round(us.mean(), 2),
                    isabet_asya=acc(asia), isabet_avr=acc(eu), isabet_abd=acc(us),
                    pay_uygun_sorgu=round(elig_q.mean(), 2), alt_kume_yukari_orani=round(100 * base_up, 1),
                    yukari_cagri_isabet=acc(call[idx] > 0), asagi_cagri_isabet=acc(call[idx] < 0),
                    donus_uyum=round(np.mean(call[idx] == -np.sign(D["c"][qs[idx]] - D["o"][qs[idx]])), 2),
                    yil_ay_ilk=str(pd.Timestamp(tq[idx[0]]))[:10], son=str(pd.Timestamp(tq[idx[-1]]))[:10]))
o = pd.DataFrame(out); print(o.to_string()); o.to_csv(RES / "tani_adaylar.csv", index=False)
