"""Tespit doğrulaması: rastgele seçilen (sonuca bakılmadan) işlemlerin 1H / 15m / LTF grafiği → grafik/*.png."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import akn as A  # noqa: E402

OUT = A.HERE / "grafik"


def candles(ax, T, a, z, title):
    for k, i in enumerate(range(a, z)):
        col = "#2a9d6a" if T.c[i] >= T.o[i] else "#d1495b"
        ax.vlines(k, T.l[i], T.h[i], color=col, lw=0.8)
        ax.add_patch(plt.Rectangle((k - 0.35, min(T.o[i], T.c[i])), 0.7, max(abs(T.c[i] - T.o[i]), 1e-6), color=col))
    ax.set_title(title, fontsize=9)


def idx(T, base_i):
    return int(np.searchsorted(T.last, base_i, side="left"))


def plot(cx: A.Ctx, r: pd.Series, path: Path) -> None:
    fig, axs = plt.subplots(1, 3, figsize=(17, 5))
    for ax, tf, back, fwd in ((axs[0], 60, 20, 6), (axs[1], 15, 30, 12), (axs[2], int(r.ltf), 40, 40)):
        T = cx.T[tf]
        i0 = idx(T, int(r.t0))
        a, z = max(0, i0 - back), min(len(T.first), i0 + fwd)
        candles(ax, T, a, z, f"{tf} dk")
        ax.axvline(i0 - a, color="#e9c46a", lw=5, alpha=0.3)
        if tf == r.ltf:
            ax.axhline(r.entry, color="#264653", lw=1, label="giriş (FVG limiti)")
            ax.axhline(r.stop, color="#d1495b", lw=1, label="stop")
            if np.isfinite(r.t1_r):
                ax.axhline(r.entry + r.side * r.t1_r * r.risk, color="#2a9d6a", lw=1, label=f"T1 {r.t1_r:.1f}R")
            ax.axvline(idx(T, int(r.f)) - a, color="#264653", lw=0.6, ls=":")
            ax.legend(fontsize=7)
    when = pd.Timestamp(int(r.um) * 60, unit="s", tz="UTC").tz_convert(A.M.TZ)
    fig.suptitle(f"{r.chain} · {'SAT' if r.side == -1 else 'AL'} · dolum {when:%Y-%m-%d %H:%M} ET · T1 sonucu {r.RT1:+.2f}R"
                 " — sarı şerit: 15m onayı")
    fig.tight_layout()
    fig.savefig(path, dpi=105)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    cx = A.build(A.load())
    t = pd.read_parquet(A.HERE / "results" / "islemler.parquet")
    rng = np.random.default_rng(16)
    for chain in ("K1K2n", "K1K2"):
        d = t[(t.chain == chain) & (t.ltf_v == "C53") & (t.giris == "E50")]
        for j, i in enumerate(rng.choice(len(d), 3, replace=False)):
            plot(cx, d.iloc[int(i)], OUT / f"{chain}_{j + 1}.png")
    print(sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
