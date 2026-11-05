import pandas as pd, sys
pd.set_option("display.width", 230); pd.set_option("display.max_colwidth", 30)
d = pd.read_csv("results/r2.csv"); print("hücre", len(d))
k = (d.k_n >= 40) & (d.k_R > 0) & (d.k_P >= .95) & (d.k_y1 >= 0) & (d.k_y2 >= 0)
c = ["çapa", "aile", "filtre", "k_n", "k_R", "k_bp", "k_P", "b_n", "b_R", "b_P", "s_n", "s_R", "s_P", "m5_n", "m5_R"]
for sym, g in d.groupby("sym"):
    gk = g[k.loc[g.index]]; ok = gk[(gk.b_R > 0) & (gk.b_P >= .9) & (gk.s_R >= 0)]
    print(f"\n=== {sym}: hücre {len(g)}, keşif geçen {len(gk)}, tam aday {len(ok)}")
    print(ok.sort_values("k_R", ascending=False)[c].head(22).to_string(index=False))
    print(" tutarlı 3-dönem (kesif olmasa da): min(k,b,s) en yüksek")
    gg = g.assign(mn=g[["k_R", "b_R", "s_R"]].min(axis=1)); print(gg[(gg.k_n >= 40) & (gg.b_n >= 40) & (gg.s_n >= 40)].sort_values("mn", ascending=False)[c + ["mn"]].head(8).to_string(index=False, header=False))
