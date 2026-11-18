"""fz_oz_test.py — sentetik: tetik, 5m zamanlamaları, sızıntı (giriş ≥ karar), değerlendirici."""
import numpy as np
import pandas as pd
import fz
import veri

T0 = int(pd.Timestamp("2025-03-04 10:00", tz="America/New_York").timestamp())


def main():
    # 1h tetik 10:00–11:00: açılış 20000, dibe 19850 (alt fitil 0,75%), kapanış 19990; sonra 5m'ler: yeşil, yeşil, kırmızı, yeşil...
    t, o, h, l, c = [], [], [], [], []
    px = 20000.0
    for m in range(60):                                    # tetik saati
        a = 20000 - (150 if m == 30 else 0)
        t.append(T0 + 60 * m); o.append(px); hh = 20005 if m < 59 else 20000; h.append(hh); l.append(min(px, a) if m == 30 else px - 2); c.append(19990 if m == 59 else px)
    seq = [(19990, 20010), (20010, 20020), (20020, 20005), (20005, 20030)] + [(20030, 20030)] * 300
    for k, (a, z) in enumerate(seq):                      # 5m blokları, her blok 5 adet 1m
        for m in range(5):
            tt = T0 + 3600 + 300 * k + 60 * m
            oo = a if m == 0 else c[-1]; cc = z if m == 4 else oo
            t.append(tt); o.append(oo); c.append(cc); h.append(max(oo, cc)); l.append(min(oo, cc))
    n = len(t)
    p = veri.PathBars(np.array(t, np.int64), np.array(o), np.array(h), np.array(l), np.array(c), np.full(n, 1.0), 60, "s")
    e = fz.entries(p, "1h")
    got = dict(zip(e.typ, e.t_sig))
    assert "Z0" in got and got["Z0"] == T0 + 3600, got
    assert got["Z1"] == T0 + 3600 + 300 and got["Z2"] == T0 + 3600 + 600, got     # ilk iki 5m yeşil
    assert got["Z4"] == T0 + 3600 + 1200, got                                    # kırmızı (3.) sonrası tepesini aşan 4. mum
    assert (e.t_sig >= T0 + 3600).all()
    ev = fz.evaluate_all(p, e[e.typ == "Z0"].reset_index(drop=True))
    assert len(ev) and (ev.t_in >= T0 + 3600).all()
    print("fz_oz_test: tüm kontroller geçti", sorted(got))


if __name__ == "__main__":
    main()
