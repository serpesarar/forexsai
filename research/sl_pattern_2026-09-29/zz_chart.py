"""Kural karşılaştırma grafiği: A+B (1.102 gerçek sinyal), 2 bar gecikme, boşluk-düzeltmeli."""
import pickle, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt
A, B, C = pickle.load(open("zz_ds.pkl", "rb"))
RULES = [("Klasik: TP yolu %60 →\nSL girişe", dict(n_p=1, first=0, P=0.6, L=0.2, lock=0.0)),
         ("Klasik + süre: 60 dk sonra\n%60 → SL girişe", dict(n_p=1, first=0, P=0.6, L=0.2, age=60, lock=0.0)),
         ("3 zikzak sonra →\nSL girişin 0.1R altına", dict(n_p=3, first=0, P=0.2, Pa=0.2, L=0.05, lock=-0.1)),
         ("Önce zarar → %60 kâr →\nSL'yi ½TP'ye (F1)", dict(n_p=1, first=-1, P=0.6, L=0.3, lock=0.5, lock_tp=True)),
         ("Önce zarar → %60 kâr →\nkapat (F3)", dict(n_p=1, first=-1, P=0.6, L=0.3, action=1))]
rows = []
for name, kw in RULES:
    tk = tr = sw = sr = 0; dR = 0.0; dC = 0.0
    for ds in (A, B):
        R, _ = ds.run(delay=2, **kw); b = ds.base
        w, l = b > 0, b < 0
        tk += int((w & (R <= 0)).sum()); tr += int((w & (R > 0) & (R < b - 1e-9)).sum())
        sw += int((l & (R > 0)).sum()); sr += int((l & (R <= 0) & (R > b + 1e-9)).sum()); dR += (R - b).sum()
    Rc, _ = C.run(delay=2, **kw); dC = (Rc - C.base).mean() * 100
    rows.append(dict(kural=name, tk=tk, tr=tr, sw=sw, sr=sr, dR=dR, dC=dC))
D = pd.DataFrame(rows); print(D.round(2).to_string(index=False))
S, T1, T2, G = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3de"
col = {"tk": "#e34948", "tr": "#eda100", "sw": "#1baf7a", "sr": "#2a78d6"}
lab = {"tk": "kazanan → ZARARA döndü (öldürüldü)", "tr": "kazananın kârı kırpıldı (hâlâ kârlı)",
       "sw": "kaybeden → KÂRA döndü", "sr": "kaybedenin zararı küçüldü"}
fig, ax = plt.subplots(figsize=(12.5, 6.4), dpi=150); fig.patch.set_facecolor(S); ax.set_facecolor(S)
x = np.arange(len(D)); w = 0.19
for i, k in enumerate(["tk", "tr", "sw", "sr"]):
    bars = ax.bar(x + (i - 1.5) * w, D[k], w - 0.02, color=col[k], label=lab[k], zorder=3)
    for bx, v in zip(bars, D[k]):
        ax.text(bx.get_x() + bx.get_width() / 2, v + 2, str(int(v)), ha="center", fontsize=8, color=T1)
for xi, r in zip(x, D.itertuples()):
    ax.text(xi, -48, f"net {r.dR:+.1f}R (A+B)\nsentetik {r.dC:+.2f} cR/işlem", ha="center", fontsize=8.5,
            color=T1)
ax.set_xticks(x); ax.set_xticklabels(D.kural, fontsize=8.8, color=T1)
ax.set_ylim(-60, max(D[["tk", "tr", "sw", "sr"]].max()) * 1.18)
ax.axhline(0, color=G, lw=1); ax.set_yticks(range(0, int(max(D[["tk", "tr", "sw", "sr"]].max()) * 1.18), 50))
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
for s_ in ("left", "bottom"): ax.spines[s_].set_color(G)
ax.tick_params(axis="y", colors=T2, labelsize=9); ax.grid(axis="y", color=G, lw=0.6); ax.set_axisbelow(True)
ax.set_ylabel("işlem sayısı (1.102 gerçek sinyal: bot + pulse)", color=T2, fontsize=9)
ax.legend(frameon=False, fontsize=8.5, loc="upper left", ncol=2)
fig.suptitle("SL'yi girişe değil KÂRA çekmek kazanan öldürmeyi ~sıfıra indiriyor — ama net kazanç gruplarda tutmuyor",
             x=0.01, ha="left", fontsize=12, color=T1, fontweight="bold")
ax.set_title("44.064 zikzak varyantından seçilmiş 5 kural · 2 bar bot gecikmesi · boşluk dolumu düzeltilmiş", loc="left",
             fontsize=9, color=T2)
plt.subplots_adjust(left=0.07, right=0.98, top=0.87, bottom=0.14)
fig.savefig(sys.argv[1], facecolor=S)
