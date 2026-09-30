"""Ticket 390567007 anatomi grafiği (broker 1m, onarılmış zaman ekseni)."""
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DATA = sys.argv[1] if len(sys.argv) > 1 else "."
m = pd.read_pickle(f"{DATA}/fx_USOIL.FOREX_1m.pkl").loc["2026-09-28 11:00":"2026-09-28 20:30"]
e, tp, sl = 98.648, 99.675, 95.584
slc = round(e * (1 - 0.0149), 3)
lock = round(e + 0.5 * (tp - e), 3)
trig = round(e + 0.6 * (tp - e), 3)
S, T1, T2, G = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3de"

fig, ax = plt.subplots(figsize=(12, 6.2), dpi=150)
fig.patch.set_facecolor(S); ax.set_facecolor(S)
ax.plot(m.index, m.close, color="#2a78d6", lw=1.4, zorder=3)
levels = [(tp, tp, "TP 99.675 (%1.04)", "#1baf7a", "--"),
          (trig, trig + 0.07, f"kilit tetiği {trig} (TP yolunun %60'ı)", "#4a3aa7", ":"),
          (lock, lock - 0.07, f"kilit stopu {lock} (TP yolunun %50'si)", "#4a3aa7", "-."),
          (e, e, "giriş 98.648", "#52514e", "--"),
          (slc, slc, f"config SL {slc} (%1.49)", "#eb6834", "--"),
          (sl, sl, "GERÇEK SL 95.584 (%3.1 = besleme farkı)", "#e34948", "-")]
for y, yl, label, c, style in levels:
    ax.axhline(y, color=c, ls=style, lw=1.2, zorder=2)
    ax.text(m.index[-1] + pd.Timedelta(minutes=6), yl, label, color=T1, fontsize=8.5, va="center")
events = [("2026-09-28 12:10", "giriş 12:10", e, (0, 14)),
          ("2026-09-28 14:01", "−0.44R (−1.340$)\n14:00", 97.309, (0, -34)),
          ("2026-09-28 14:57", "+0.21R zirve (+658$)\nTP'ye 0.37 kala", 99.306, (0, 14)),
          ("2026-09-28 16:20", "ani çöküş\nSL'ye 0.006 kala", 95.59, (-8, -34)),
          ("2026-09-28 17:11", "SL 17:11\n−3.064$", 95.584, (40, -30))]
for t, label, y, off in events:
    t = pd.Timestamp(t, tz="UTC")
    ax.scatter([t], [y], s=36, color=T1, zorder=5, edgecolor=S, linewidth=1.5)
    ax.annotate(label, (t, y), xytext=off, textcoords="offset points", ha="center",
                fontsize=8.5, color=T1)
ax.set_xlim(m.index[0], m.index[-1] + pd.Timedelta(minutes=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz="UTC"))
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
for s_ in ("left", "bottom"):
    ax.spines[s_].set_color(G)
ax.tick_params(colors=T2, labelsize=9)
ax.grid(axis="y", color=G, lw=0.6); ax.set_axisbelow(True)
ax.set_ylabel("SpotCrude (broker, 1m kapanış)", color=T2, fontsize=9)
ax.set_xlabel("28 Eylül 2026, UTC", color=T2, fontsize=9)
fig.suptitle("Ticket 390567007 — SpotCrude BUY 10 lot: gerçek −3.064$ · config SL ile −1.470$ · "
             "config SL + kâr kilidi ile +514$", x=0.01, ha="left", fontsize=12, color=T1,
             fontweight="bold")
ax.set_title("SL mesafesi bot hatasıyla broker−backend besleme farkına eşitlendi (RR 0.34). "
             "Kilit kuralı bu işlemi kurtarır ama 487 işlemde net zararlı.", loc="left",
             fontsize=9, color=T2)
plt.subplots_adjust(left=0.07, right=0.74, top=0.88, bottom=0.1)
fig.savefig(sys.argv[2] if len(sys.argv) > 2 else "islem_390567007.png", facecolor=S)
