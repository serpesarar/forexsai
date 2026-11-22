"""EK-4: NY cut sabitlemesi (PROTOCOL.md EK-4)."""
import itertools
import numpy as np, pandas as pd
import core

PAIRS = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "EURJPY"]
GRID = list(itertools.product([50, 100], [10, 20], [15, 30], [16, 16.5]))
TIMES = {"VADE": 0, "K03": -6, "K13": 4}  # srv saat kaydırması (16:00 → 10:00 / 20:00)


def pip(p): return 0.01 if p.endswith("JPY") else 0.0001


def trades(p, x, cell, shift, ghost):
    A, D, S, ent = cell
    hh = ent + shift
    h, mnt = int(hh), int(round((hh % 1) * 60))
    ok = (x.hr.values == h) & (x.srv.dt.minute.values == mnt)
    idx = np.where(ok)[0] - 1  # sinyal = önceki barın kapanışı; giriş = idx+1 açılışı
    idx = idx[idx >= 0]
    pp = pip(p)
    c = x.c.values[idx]
    step = A * pp
    off = step / 2 if ghost else 0.0
    lvl = np.round((c - off) / step) * step + off
    d = lvl - c
    m = (np.abs(d) > 2 * pp) & (np.abs(d) <= D * pp)
    idx, d = idx[m], d[m]
    if len(idx) == 0:
        return pd.DataFrame()
    side = np.sign(d).astype(int)
    exit_h = (16 + shift) + 1  # vadeye kadar: 10:00 ET = srv 17:00 → son bar 16:45
    nb = np.array([int(round((exit_h - (ent + shift)) * 4)) for _ in idx])
    e = x.o.values[np.minimum(idx + 1, len(x) - 1)]
    tp = np.abs(lvl[m] - e)
    t = core.run(x, idx, side, np.maximum(tp, 1e-9), np.full(len(idx), S * pp), nb)
    return t


rows = []
for p in PAIRS:
    x = core.load(p)
    for ci, cell in enumerate(GRID):
        for tn, sh in TIMES.items():
            for ghost in (False, True):
                t = trades(p, x, cell, sh, ghost)
                if len(t):
                    t["pair"], t["cell"], t["tn"], t["ghost"] = p, ci, tn, ghost
                    rows.append(t)
T = pd.concat(rows, ignore_index=True)
T.to_parquet(core.RES / "trades_PIN.parquet")
K = T[T.time < core.SPLIT]
out = []
for (ci, tn, gh), g in K.groupby(["cell", "tn", "ghost"]):
    out.append({"cell": ci, "def": GRID[ci], "tn": tn, "hayalet": gh, **core.summ(g)})
H = pd.DataFrame(out)
H.to_csv(core.RES / "kesif_PIN.csv", index=False)
pd.set_option("display.width", 250)
v = H[(H.tn == "VADE") & (~H.hayalet)].set_index("cell")
gst = H[(H.tn == "VADE") & (H.hayalet)].set_index("cell")
k3 = H[(H.tn == "K03") & (~H.hayalet)].set_index("cell")
k13 = H[(H.tn == "K13") & (~H.hayalet)].set_index("cell")
v["hayalet_ort"], v["k03_ort"], v["k13_ort"] = gst.ort, k3.ort, k13.ort
v["hayalet_wr"] = gst.wr
print(v[["def", "n", "wr", "ort", "t", "brut", "maliyet", "hayalet_wr", "hayalet_ort", "k03_ort", "k13_ort"]].to_string())
