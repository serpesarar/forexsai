"""ME-09 adım 2 — en benzer 12 çakışmasız bölge (SONRASI GÖSTERİLMEZ) → tur1_etiketleme.png
Aday pencereler: her 2 saatte bir biten pencere, L ∈ LS, üç şablonun en yakını (f = 1). Şablon aralığıyla çakışan pencereler hariç.
Çalıştır: nice python3.13 research/benzerlik_tepe_20261019/sablon/etiketleme_gorseli.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import HERE, OUT, TEMPL, load_ndx, r_from_d, shapes, tpl_index, tpl_shape, window_lengths  # noqa: E402

STEP = 2
N_PICK = 12


def candles(ax: plt.Axes, s: pd.DataFrame) -> None:
    k = (s.set_index("ts").resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna())
    x = np.arange(len(k))
    up = (k.close >= k.open).to_numpy()
    col = np.where(up, "#26a69a", "#ef5350")
    ax.vlines(x, k.low, k.high, color=col, lw=0.8)
    ax.bar(x, (k.close - k.open).abs().clip(lower=1e-9), bottom=np.minimum(k.open, k.close), color=col, width=0.7)
    ax.set_xlim(-1, len(k)); ax.set_xticks([]); ax.grid(alpha=0.25, axis="y"); ax.tick_params(labelsize=7)


def main() -> None:
    d = load_ndx(); ts = d.ts; c = np.log(d.close.to_numpy())
    tpl = tpl_index(ts); LS = window_lengths(tpl)
    vec = {k: tpl_shape(c, a, b) for k, (a, b) in tpl.items()}
    t_lo = min(a for a, _ in tpl.values()); t_hi = max(b for _, b in tpl.values())
    rows = []
    ends = np.arange(max(LS), len(c), STEP)
    for L in LS:
        st = ends - L + 1
        S = shapes(c, st, L)
        for k, tv in vec.items():
            dist = np.sqrt(((S - tv) ** 2).sum(1))
            rows.append(pd.DataFrame({"bas": st, "son": ends, "L": L, "sablon": k, "D": dist}))
    cand = pd.concat(rows)
    cand = cand[np.isfinite(cand.D) & ((cand.son < t_lo) | (cand.bas > t_hi))].sort_values("D")
    picked: list[tuple[int, int]] = []
    out = []
    for r in cand.itertuples():
        if any(not (r.son < a or r.bas > b) for a, b in picked):
            continue
        picked.append((r.bas, r.son))
        out.append({"no": len(out) + 1, "baslangic": ts.iloc[r.bas], "bitis": ts.iloc[r.son], "L": r.L,
                    "en_yakin_sablon": r.sablon, "D": round(r.D, 3), "r": round(float(r_from_d(r.D)), 3)})
        if len(out) == N_PICK:
            break
    pk = pd.DataFrame(out); pk.to_csv(OUT / "tur1_secilenler.csv", index=False)
    print(pk.to_string(index=False))
    fig, axes = plt.subplots(4, 4, figsize=(18, 13.5))
    for j, (k, (a, b)) in enumerate(tpl.items()):
        ax = axes[0, j]; candles(ax, d.iloc[a:b + 1])
        ax.set_title(f"SENİN: {k}  {ts.iloc[a]:%d.%m.%Y} → {ts.iloc[b]:%d.%m.%Y}", color="darkgreen", fontweight="bold", fontsize=11)
    ax = axes[0, 3]; ax.axis("off")
    ax.text(0.02, 0.95, "Nasıl okunur\n\n• Üst satır: senin 3 bölgen (T1–T3).\n• #1–#12: 2016–2026 arasında\n  ölçeksiz şekil ölçüsünün en benzer\n  bulduğu çakışmasız bölgeler.\n• Her bölgenin SONRASI gösterilmiyor\n  (etiketin sonuçtan etkilenmesin diye).\n• Parantezde: en çok benzediği şablon\n  ve şekil korelasyonu r.\n\nHer #numara için yaz:\n  benzer / benzer değil / kısmen\n  — ve nedenini.",
            va="top", fontsize=11, transform=ax.transAxes)
    for i, r in pk.iterrows():
        ax = axes[1 + i // 4, i % 4]
        a = int(ts.searchsorted(r.baslangic)); b = int(ts.searchsorted(r.bitis))
        candles(ax, d.iloc[a:b + 1])
        ax.set_title(f"#{r.no}  {r.baslangic:%d.%m.%Y} → {r.bitis:%d.%m.%Y}  ({r.en_yakin_sablon}, r={r.r:.2f})", fontsize=11, fontweight="bold")
    fig.suptitle("NAS100 1h — senin 3 'dalgalı tepe' bölgen + algoritmanın 10 yılda en benzer bulduğu 12 bölge "
                 "(4 saatlik mumlar, ölçeksiz + süre-esnek şekil eşleşmesi)\nSonrası gösterilmiyor — her #numara için: benzer / benzer değil / kısmen, ve nedenini yaz",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(HERE / "tur1_etiketleme.png", dpi=100)


if __name__ == "__main__":
    main()
