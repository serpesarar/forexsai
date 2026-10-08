"""Statik PNG grafikler (rapor.md içine gömülür). Renk = kimlik: TP mavi, SL turuncu
(referans paletin ilk iki kategorik slotu, CVD doğrulamalı); tek eksen; ince çizgi.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import settings as S  # noqa: E402
from .compare import LOSS, WIN  # noqa: E402
from .features import make_ctx  # noqa: E402

C_TP, C_SL = "#2a78d6", "#eb6834"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
VOL_BAR = "#b9b8b2"          # hacim çubukları nötr; şok barları (≥VOL_SHOCK_SEAS) koyu
DPI = 130


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor(SURF)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _fig(w: float = 7.5, h: float = 3.6) -> tuple:
    fig, ax = plt.subplots(figsize=(w, h), dpi=DPI)
    fig.patch.set_facecolor(SURF)
    _style(ax)
    return fig, ax


def divergence_chart(ep: dict, div: dict, path: Path) -> bool:
    """Giriş-hizalı ortalama R (yalnız hâlâ açık işlemler) — SL vs TP."""
    R, OPEN, lab = ep["R"], ep["OPEN"], ep["lab"]
    if R.size == 0:
        return False
    fig, ax = _fig()
    k = np.arange(1, R.shape[1] + 1)
    for name, col, txt in ((WIN, C_TP, "TP ile bitenler"), (LOSS, C_SL, "SL ile bitenler")):
        m = (lab == name)[:, None] & OPEN
        cnt = m.sum(axis=0)
        mean = np.where(cnt >= 3, np.nansum(np.where(m, R, 0), axis=0) / np.maximum(cnt, 1), np.nan)
        ax.plot(k, mean, color=col, linewidth=2, label=f"{txt} (açık olanlar)")
        last = np.flatnonzero(np.isfinite(mean))
        if last.size:
            ax.annotate(txt, (k[last[-1]], mean[last[-1]]), color=INK2, fontsize=8,
                        xytext=(4, 0), textcoords="offset points", va="center")
    ax.axhline(0, color=INK2, linewidth=0.8)
    if div:
        ax.axvline(div["dakika"], color=INK2, linewidth=1, linestyle="--")
        ax.annotate(f"ayrışma: {div['dakika']}. dk", (div["dakika"], ax.get_ylim()[1]), color=INK,
                    fontsize=8, xytext=(4, -10), textcoords="offset points")
    ax.set_xlabel("girişten sonra dakika", color=INK2, fontsize=9)
    ax.set_ylabel("ortalama R (kapanış)", color=INK2, fontsize=9)
    ax.set_title("SL ve TP işlemleri girişten sonra ne zaman ayrışıyor?", color=INK, fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return True


def exit_volume_chart(curves: dict, path: Path) -> bool:
    """Çıkıştan önceki 30 dk: mevsimsel hacim medyanı (1 = saatine göre normal)."""
    if not curves:
        return False
    fig, ax = _fig()
    for name, col, txt in ((WIN, C_TP, "TP'ye giden"), (LOSS, C_SL, "SL'ye giden")):
        if name in curves:
            x, y, n = curves[name]
            ax.plot(x, y, color=col, linewidth=2, label=f"{txt} (n={n})")
    ax.axhline(1.0, color=INK2, linewidth=0.8, linestyle=":")
    ax.annotate("saatine göre normal hacim", (-S.EVENT_EXIT_PRE_MIN, 1.0), color=INK2, fontsize=7,
                xytext=(2, 3), textcoords="offset points")
    ax.set_xlabel("çıkışa kalan dakika (0 = çıkış barı)", color=INK2, fontsize=9)
    ax.set_ylabel("hacim / aynı saat medyanı", color=INK2, fontsize=9)
    ax.set_title("Çıkışa giderken hacim: SL'de sönüyor mu, patlıyor mu?", color=INK, fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return True


def exit_volume_curves(t: pd.DataFrame, sbs: dict) -> dict:
    out = {}
    for name in (WIN, LOSS):
        rows = []
        for _, r in t[t["outcome"] == name].iterrows():
            c = make_ctx(r, sbs[r["symbol"]])
            if c is None:
                continue
            js = np.arange(c.i_exit - S.EVENT_EXIT_PRE_MIN, c.i_exit + 1)
            v = np.where((js >= c.i_in0) & (js < c.sb.a["vol_seas"].size),
                         c.sb.a["vol_seas"][np.clip(js, 0, c.sb.a["vol_seas"].size - 1)], np.nan)
            rows.append(v)
        if len(rows) >= S.MIN_GROUP_N:
            m = np.vstack(rows)
            ok = np.isfinite(m).sum(axis=0) >= 3
            med = np.where(ok, np.nanmedian(np.where(np.isfinite(m), m, np.nan), axis=0), np.nan)
            out[name] = (np.arange(-S.EVENT_EXIT_PRE_MIN, 1), med, len(rows))
    return out


def auc_chart(fc: pd.DataFrame, path: Path, top: int = 15) -> bool:
    """En ayırt edici özellikler: AUC − 0,5 (sağ = SL'de yüksek, sol = TP'de yüksek)."""
    d = fc.head(top).iloc[::-1]
    if d.empty:
        return False
    fig, ax = _fig(7.5, 0.32 * len(d) + 1.2)
    vals = d["auc"] - 0.5
    cols = [C_SL if v > 0 else C_TP for v in vals]
    ax.barh(range(len(d)), vals, color=cols, height=0.6)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels([f"{f}{' *' if q < S.FDR_Q else ''}" for f, q in zip(d["feature"], d["q"])], fontsize=7, color=INK2)
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.set_xlabel("AUC − 0,5   (→ SL'de yüksek · ← TP'de yüksek)   * = q<0,10", color=INK2, fontsize=8)
    ax.set_title("SL ile TP'yi en çok ayıran özellikler", color=INK, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return True


def trade_chart(r: pd.Series, sb, path: Path, pad_min: int = 60) -> bool:
    """Tek işlem: fiyat (kapanış) + giriş/SL/TP çizgileri, altında hacim (aynı zaman ekseni)."""
    m1 = sb.m1
    w = m1.loc[r["entry_utc"] - pd.Timedelta(minutes=pad_min): r["exit_utc"] + pd.Timedelta(minutes=pad_min)]
    if len(w) < 5:
        return False
    fig, (ax, axv) = plt.subplots(2, 1, figsize=(7.5, 3.8), dpi=DPI, sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1]})
    fig.patch.set_facecolor(SURF)
    _style(ax)
    _style(axv)
    x = w.index.tz_convert("Europe/Istanbul").tz_localize(None)
    ax.plot(x, w["close"], color=INK, linewidth=1)
    for lvl, col, lab in ((r["open_price"], INK2, "giriş"), (r["sl0"], C_SL, "SL"), (r["tp0"], C_TP, "TP")):
        if np.isfinite(lvl):
            ax.axhline(lvl, color=col, linewidth=1, linestyle="--")
            ax.annotate(lab, (x[0], lvl), color=col, fontsize=7, xytext=(2, 2), textcoords="offset points")
    for ts in (r["entry_utc"], r["exit_utc"]):
        ax.axvline(ts.tz_convert("Europe/Istanbul").tz_localize(None), color=INK2, linewidth=0.8)
    vs = w["vol_seas"].clip(upper=5)
    axv.bar(x, vs, width=1 / 1440 * 0.8, color=[INK2 if v >= S.VOL_SHOCK_SEAS else VOL_BAR for v in vs])
    axv.axhline(1.0, color=INK2, linewidth=0.6, linestyle=":")
    axv.set_ylabel("hacim×", color=INK2, fontsize=7)
    ax.set_title(f"{r['outcome']} · {r['broker_symbol']} {r['direction']} · {r['family']} · #{r['pid']} (TSİ)",
                 color=INK, fontsize=9, loc="left")
    axv.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return True
