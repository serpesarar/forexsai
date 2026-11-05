import sys, pandas as pd, numpy as np
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 44)
f = sys.argv[1]; d = pd.read_csv(f)
print("hücre", len(d))
k = (d.k_n >= 40) & (d.k_R > 0) & (d.k_P >= .95) & (d.k_y1 >= 0) & (d.k_y2 >= 0)
print("keşif eşiği geçen", int(k.sum()))
ind = (d.b30_R > 0) & (d.b60_R > 0)
c = d[k & ind].copy()
cols = ["aile", "hücre", "filtre", "k_n", "k_R", "k_bp", "k_P", "b30_n", "b30_R", "b30_P", "b60_n", "b60_R", "b60_P", "s26_n", "s26_R", "s26_P"]
print(c[[x for x in cols if x in c]].sort_values("k_R", ascending=False).head(40).to_string(index=False))
print("\nkeşif geçip bağımsızda düşen örnek:"); print(d[k & ~ind][[x for x in cols if x in d]].sort_values("k_R", ascending=False).head(14).to_string(index=False))
