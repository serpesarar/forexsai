"""Most-charitable edge search: find conditional pockets with high WR on TRAIN,
then check if they hold on held-out TEST. Tests directional rules conditioned on
(hour, volatility bucket, short-term momentum sign)."""
import numpy as np
import engine as E
import strategies as S

t, o, h, l, c, v = E.load()
n = len(o)
ws, ts = E.slices(n)

# precompute per-bar features for conditioning
atr = np.zeros(n)
tr = np.maximum(h-l, np.maximum(np.abs(h-np.roll(c,1)), np.abs(l-np.roll(c,1))))
tr[0]=h[0]-l[0]
k=14; atr[k]=tr[1:k+1].mean()
for i in range(k+1,n): atr[i]=(atr[i-1]*(k-1)+tr[i])/k
mom3 = np.zeros(n); mom3[3:] = np.sign(c[3:]-c[:-3])
hour = ((t % 86400)//3600).astype(int)
atr_med = np.median(atr[ws:ts]) if ts>ws else 1.0
vol_bucket = (atr > atr_med).astype(int)  # 0 low, 1 high

# precompute BUY/SELL outcome per bar (entry i+1)
def outcomes(direction):
    res = np.full(n, -9, dtype=np.int8)
    for i in range(n-1):
        out,_ = E.simulate_trade(o,h,l,c,t,i+1,direction)
        if out=="win": res[i]=1
        elif out=="loss": res[i]=0
    return res
buy_out = outcomes("BUY")
sell_out = outcomes("SELL")

def slice_mask(lo,hi):
    m=np.zeros(n,bool); m[lo:hi]=True; return m
train_m = slice_mask(ws,ts)
test_m  = slice_mask(ts, n-E.MAX_HOLD-1)

# enumerate cells: (hour, vol_bucket, mom_sign, direction)
cells=[]
for hr in range(24):
    for vb in (0,1):
        for ms in (-1,0,1):
            for d,out in (("BUY",buy_out),("SELL",sell_out)):
                cond = (hour==hr)&(vol_bucket==vb)&(mom3==ms)
                tr_sel = train_m & cond & (out>=0)
                te_sel = test_m & cond & (out>=0)
                ntr=tr_sel.sum()
                if ntr<150: continue
                wtr=out[tr_sel].sum(); wr_tr=wtr/ntr
                nte=te_sel.sum(); wte=out[te_sel].sum() if nte else 0
                wr_te=wte/nte if nte else 0
                cells.append((wr_tr,ntr,wr_te,nte,hr,vb,ms,d))

cells.sort(reverse=True)
print("Top 15 TRAIN cells (>=150 train trades) and their HELD-OUT TEST WR:")
print(f"{'WR_tr':>6}{'n_tr':>7}  {'WR_te':>6}{'n_te':>7}  hr vb mom dir")
for wr_tr,ntr,wr_te,nte,hr,vb,ms,d in cells[:15]:
    print(f"{wr_tr:>6.1%}{ntr:>7}  {wr_te:>6.1%}{nte:>7}  {hr:>2} {vb}  {ms:>2} {d}")

# how many train cells >=65%? and do they hold >=65% on test?
hi_train=[x for x in cells if x[0]>=0.65]
held=[x for x in hi_train if x[3]>=50 and x[2]>=0.65]
print(f"\ncells with TRAIN WR>=65%: {len(hi_train)}")
print(f"  of those, holding TEST WR>=65% (n_te>=50): {len(held)}")
if hi_train:
    avg_drop=np.mean([x[0]-x[2] for x in hi_train if x[3]>=50])
    print(f"  avg WR drop train->test among them: {avg_drop:.1%}")
