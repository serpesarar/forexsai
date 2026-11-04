"""Motor doğrulama: binary lifting ilk-dokunuş = kaba tarama; basit LONG elle hesap."""
import sys; sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend")
import time, numpy as np
from lib_trend import M1
t0=time.time(); m1=M1(); print("yük", round(time.time()-t0,1), "s", m1.N)
rng=np.random.default_rng(0)
k=rng.integers(0,m1.N-40000,3000); e=k+rng.integers(0,30000,3000)
thr=m1.L[k]*(1-rng.uniform(0,0.15,3000))
p=m1._first(k,e,thr,True)
bad=0
for i in range(3000):
    seg=np.where(m1.L[k[i]:e[i]+1]<=thr[i])[0]
    want=k[i]+seg[0] if len(seg) else e[i]+1
    bad+= want!=p[i]
thr2=m1.H[k]*(1+rng.uniform(0,0.15,3000)); p2=m1._first(k,e,thr2,False)
for i in range(3000):
    seg=np.where(m1.H[k[i]:e[i]+1]>=thr2[i])[0]
    want=k[i]+seg[0] if len(seg) else e[i]+1
    bad+= want!=p2[i]
print("uyuşmazlık", bad)
# elle: 1 olay long, zaman çıkışı, SL uzak
i0=100000; dec=m1.T[i0]; r=m1.simulate([dec],[1],[1e9/1e4*0+50000],[np.nan],[dec+60],[m1.O[i0]])
h=m1.O[i0]*0.000185/2; ent=m1.O[i0]+h; ex=m1.C[i0+59]-h
print(r['R'][0]*50000, ex-ent, r['typ'])
