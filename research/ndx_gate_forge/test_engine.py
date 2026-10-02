"""El yapımı fikstürler — simülatör doğrulaması."""
import numpy as np, pandas as pd
from common import simulate, fwd_points

def mk(rows, spread=1.0):
    d = pd.DataFrame(rows, columns=["open","high","low","close"])
    d["t"] = np.arange(len(d))*60 + 1_700_000_000
    for k,s in [("ao","open"),("ah","high"),("al","low"),("ac","close")]:
        d[k] = d[s] + spread
    return d

# BUY: giriş bar1 ask açılış 101+0.2 slip=101.2; TP 10 → 111.2 bid high; SL 10 → 91.2
d = mk([[100,100,100,100],[100,101,99,100],[100,112,99,110],[110,110,110,110]])
R,dur,why = simulate(d, np.array([0]), np.array([1]), np.array([10.]), np.array([10.]))
assert why[0]==1 and abs(R[0]-1.0)<1e-9, (R,why)
# Aynı barda TP ve SL → SL (belirsizlik kötümser)
d = mk([[100,100,100,100],[100,101,99,100],[100,115,85,100],[100,100,100,100]])
R,dur,why = simulate(d, np.array([0]), np.array([1]), np.array([10.]), np.array([10.]))
assert why[0]==2 and abs(R[0]-(-1.02))<1e-9, (R,why)
# SELL: giriş bid açılış 100-0.2=99.8; TP 10 → ask low <= 89.8 → bid low <= 88.8
d = mk([[100,100,100,100],[100,101,99,100],[95,96,88.8,90],[90,90,90,90]])
R,dur,why = simulate(d, np.array([0]), np.array([-1]), np.array([10.]), np.array([10.]))
assert why[0]==1 and abs(R[0]-1.0)<1e-9, (R,why)
# SELL SL boşluğu: ask açılış SL üstünde → açılıştan +slip dolar
d = mk([[100,100,100,100],[100,101,99,100],[120,121,119,120],[90,90,90,90]])
R,dur,why = simulate(d, np.array([0]), np.array([-1]), np.array([10.]), np.array([10.]))
assert why[0]==2 and abs(R[0]-(-(121.2-99.8)/10))<1e-9, (R,why)
# Süre dolumu: 2 dk tutma, kapanıştan çıkış
d = mk([[100,100,100,100],[100,101,99,100],[100,102,99,101],[101,103,100,102],[102,102,102,102]])
R,dur,why = simulate(d, np.array([0]), np.array([1]), np.array([50.]), np.array([50.]), maxhold_min=2)
assert why[0]==0, (R,why,dur)
assert abs(R[0]-((101-101.2)/50))<1e-9, R
# Giriş sonrası 120 sn'den uzun boşluk → giriş yok
d = mk([[100,100,100,100],[100,101,99,100]]); d.loc[1,"t"] += 600
R,dur,why = simulate(d, np.array([0]), np.array([1]), np.array([10.]), np.array([10.]))
assert np.isnan(R[0])
# İleri getiri: 2 dk sonra bid kapanış - ask giriş
d = mk([[100,100,100,100],[100,101,99,100],[100,102,99,105],[105,106,104,106]])
f = fwd_points(d, np.array([0]), np.array([1]), 2)
assert abs(f[0]-(105-101.2))<1e-9, f
print("engine fixtures OK")
