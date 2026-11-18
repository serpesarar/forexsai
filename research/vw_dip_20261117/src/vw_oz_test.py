"""oz_test.py — çok-çıkışlı değerlendiricinin elle hesaplanan sentetik sınaması."""
import numpy as np
import pandas as pd
import vw
import veri

T0 = int(pd.Timestamp("2025-03-04 10:00", tz="America/New_York").timestamp())


def path(prices_hl):
    n = len(prices_hl)
    t = T0 + 60 * np.arange(n)
    o = np.array([x[0] for x in prices_hl], float); h = np.array([x[1] for x in prices_hl], float)
    l = np.array([x[2] for x in prices_hl], float); c = np.array([x[3] for x in prices_hl], float)
    return veri.PathBars(t.astype(np.int64), o, h, l, c, np.full(n, 1.0), 60, "s")


def main():
    # giriş 1. bar açılışı 100 (+1 spread = 101); stop 99 → risk 2; 1R=103, 2R=105
    bars = [(100, 100, 100, 100)] + [(100, 104, 100, 103)] + [(103, 103, 98, 99)] + [(99, 99, 99, 99)] * 400
    p = path(bars)
    ev = vw.evaluate(p, T0 + 30, 99.0)
    iR = {k: n for n, k in enumerate(vw.TPS)}
    # TP1R (103) bar1'de değer → +1R (finansman 0); TP2R (105) hiç değmez → bar2'de stop (−1R)
    assert abs(ev.R[iR[1.0], 0] - (103 / 101 - 1) * 1e4 / (2 / 101 * 1e4)) < 1e-9, ev.R
    assert abs(ev.R[iR[2.0], 0] - (99 / 101 - 1) * 1e4 / (2 / 101 * 1e4)) < 1e-9
    # aynı barda TP ve stop → stop
    bars2 = [(100, 100, 100, 100), (100, 106, 98, 100)] + [(100, 100, 100, 100)] * 300
    ev2 = vw.evaluate(path(bars2), T0 + 30, 99.0)
    assert ev2.R[iR[1.0], 0] < 0
    # zaman çıkışı: 4 sa sonra açılış
    bars3 = [(100, 100, 100, 100)] + [(100, 100.5, 99.5, 100)] * 400
    ev3 = vw.evaluate(path(bars3), T0 + 30, 99.0)
    assert abs(ev3.R[iR[np.inf], 0] - (100 / 101 - 1) * 1e4 / (2 / 101 * 1e4)) < 1e-9
    # iyimser: sinyal kapanışı 100, spread 0 → giriş 100
    ev4 = vw.evaluate(path(bars3), T0 + 30, 99.0, sig_close=100.0)
    assert abs(ev4.R[iR[np.inf], 0]) < 1e-9
    # giriş karar anından sonra
    assert ev.t_in >= T0 + 30
    print("oz_test: tüm kontroller geçti")


if __name__ == "__main__":
    main()
