import sys, pandas as pd, numpy as np
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 42)
d = pd.read_csv(sys.argv[1]); cols = ["hücre", "filtre", "k_n", "k_R", "k_P", "b30_n", "b30_R", "b30_P", "b60_n", "b60_R", "b60_P", "s26_n", "s26_R"]
for fam in sys.argv[2:]:
    g = d[d.aile == fam]
    print(f"\n== {fam} n={len(g)} (ort. tutarlılık sırası)")
    g = g.assign(minR=g[["k_R", "b30_R", "b60_R"]].min(axis=1), maxR=g[["k_R", "b30_R", "b60_R"]].max(axis=1))
    print(g.sort_values("minR", ascending=False).head(6)[cols].to_string(index=False))
    print(" en kötü:"); print(g.sort_values("maxR").head(4)[cols].to_string(index=False, header=False))
