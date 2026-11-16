"""draw.py — 1m mum grafiği çizici (gözle inceleme fazı). Kullanım: python src/draw.py 2020-03-12 [baş_dk son_dk] [etiket]"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "charts"


def draw(m1, d: date, m0: int = 570, m_end: int = 960, tag: str = "", marks: dict | None = None) -> Path:
    a, b = int(np.searchsorted(m1.t, lib.utc(d, m0))), int(np.searchsorted(m1.t, lib.utc(d, m_end)))
    o, h, l, c, mm = m1.o[a:b], m1.h[a:b], m1.l[a:b], m1.c[a:b], m1.m[a:b]
    x = np.arange(len(o))
    fig, ax = plt.subplots(figsize=(22, 8), dpi=80)
    up = c >= o
    col = np.where(up, "#2e7d32", "#c62828")
    ax.vlines(x, l, h, color=col, linewidth=0.7)
    ax.bar(x, np.maximum(np.abs(c - o), (h - l).max() * 0.002), bottom=np.minimum(o, c), color=col, width=0.75)
    ticks = [i for i in x if mm[i] % 30 == 0]
    ax.set_xticks(ticks, [f"{mm[i]//60:02d}:{mm[i]%60:02d}" for i in ticks])
    for k, v in (marks or {}).items():
        ax.axhline(v, ls="--", lw=0.8, color="#555")
        ax.text(0, v, k, fontsize=9)
    ax.set_title(f"NDX 1m {d} {tag}")
    ax.grid(alpha=0.2)
    OUT.mkdir(exist_ok=True)
    p = OUT / f"{d}_{m0}_{m_end}{('_' + tag) if tag else ''}.png"
    fig.tight_layout(); fig.savefig(p); plt.close(fig)
    return p


if __name__ == "__main__":
    m1 = lib.load_m1()
    d = date.fromisoformat(sys.argv[1])
    m0 = int(sys.argv[2]) if len(sys.argv) > 2 else 570
    m_end = int(sys.argv[3]) if len(sys.argv) > 3 else 960
    print(draw(m1, d, m0, m_end, sys.argv[4] if len(sys.argv) > 4 else ""))
