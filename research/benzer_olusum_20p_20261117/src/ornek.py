"""ornek.py — bir TP oluşumu + en benzer 5 geçmiş oluşum ve sonuçları (görsel inceleme). Çıktı results/ornek_*.png"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib
OUT = Path(__file__).resolve().parents[1] / "results"
df = pd.read_parquet(OUT / "entries.parquet"); X = np.load(OUT / "forms.npy"); m1 = lib.load_m1()
rs = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
q = rs.choice(np.where((df.W.values == sys.argv[2] if len(sys.argv) > 2 else "BUY_TP") & (df.year.values == 2025))[0])
past = np.where(df.t.values < df.t.values[q] - 86400)[0]
_, ix = NearestNeighbors(n_neighbors=5).fit(X[past]).kneighbors(X[q:q + 1]); nb = past[ix[0]]
fig, axes = plt.subplots(2, 3, figsize=(18, 8), dpi=80)
for ax, i in zip(axes.ravel(), [q, *nb]):
    j = int(df.j.values[i]); a, b = j - 30, j + 60
    o, h, l, c = m1.o[a:b], m1.h[a:b], m1.l[a:b], m1.c[a:b]; x = np.arange(b - a); ref = m1.c[j - 1]
    col = np.where(c >= o, "#2e7d32", "#c62828")
    ax.vlines(x, l - ref, h - ref, color=col, lw=0.7); ax.bar(x, np.maximum(abs(c - o), .3), bottom=np.minimum(o, c) - ref, color=col, width=.7)
    ax.axvline(29.5, color="k", lw=.8); ax.axhline(20, ls="--", c="g", lw=.7); ax.axhline(-20, ls="--", c="r", lw=.7)
    ax.set_title(("SORGU " if i == q else "benzer ") + f"{df.d.values[i]} → {df.W.values[i]}", fontsize=10); ax.set_ylim(-45, 45)
fig.suptitle("Solda 30 mum = oluşum (son kapanışa göre puan), dikey çizgi = giriş, ±20 puan TP/SL"); fig.tight_layout()
p = OUT / f"ornek_{df.d.values[q]}.png"; fig.savefig(p); print(p)
