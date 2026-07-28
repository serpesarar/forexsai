"""Yardimci: SADECE train+val gosterir. test asla okunmaz."""
import numpy as np, pandas as pd
from miner import Lab

lab = Lab(direction="BUY")
B = lab.base()
BT, BV = B['train'].ev, B['val'].ev

def ev(mask):
    st = lab.eval_mask(mask)
    return dict(n_tr=st['train'].n, wr_tr=st['train'].wr, ev_tr=st['train'].ev,
                lift_tr=st['train'].ev-BT,
                n_val=st['val'].n, wr_val=st['val'].wr, ev_val=st['val'].ev,
                lift_val=st['val'].ev-BV)

def show(label, mask):
    d = ev(mask)
    ok = "OK " if (d['n_tr']>=300 and d['n_val']>=150) else "n! "
    print(f"{ok}{label:62s} tr n={d['n_tr']:5d} WR={d['wr_tr']*100:5.1f}% EV={d['ev_tr']:+.4f} L={d['lift_tr']:+.4f} | "
          f"val n={d['n_val']:5d} WR={d['wr_val']*100:5.1f}% EV={d['ev_val']:+.4f} L={d['lift_val']:+.4f}")
    return d

def months(mask, splits=('train','val')):
    m = mask.reindex(lab.df.index).fillna(False).astype(bool)
    x = lab.df[m & lab.df.split.isin(splits)].copy()
    x['ay'] = x.ts.dt.to_period('M')
    g = x.groupby('ay').agg(n=('r','size'), wr=('outcome','mean'), ev=('r','mean')).round(3)
    b = lab.df[lab.df.split.isin(splits)].copy()
    b['ay'] = b.ts.dt.to_period('M')
    gb = b.groupby('ay').agg(base_n=('r','size'), base_ev=('r','mean')).round(3)
    return g.join(gb)
