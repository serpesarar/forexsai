from miner import Lab, _stat
import pandas as pd, numpy as np
pd.set_option('display.width',260)
lab=Lab('BUY'); d=lab.df; B=lab.base()
TR=B['train'].ev; VA=B['val'].ev

def rep(expr, label=None):
    m = eval(expr, {'d':d,'np':np,'pd':pd})
    m = m.reindex(d.index).fillna(False).astype(bool)
    st = lab.eval_mask(m)
    tr,va = st['train'], st['val']
    ntrd = d[m&(d.split=='train')].day.nunique(); nvad = d[m&(d.split=='val')].day.nunique()
    lab_ = label or expr
    print(f'{lab_:58s}')
    print(f'   TR n={tr.n:5d} g={ntrd:3d} WR={tr.wr*100:5.1f}% EV={tr.ev:+.4f} lift={tr.ev-TR:+.4f} | VAL n={va.n:5d} g={nvad:3d} WR={va.wr*100:5.1f}% EV={va.ev:+.4f} lift={va.ev-VA:+.4f}')
    return m

def halves(m, label=''):
    """train ve val'i ikiye bol, alt-donem kararliligi"""
    out=[]
    for sp in ('train','val'):
        blk = d[d.split==sp]
        days = sorted(blk.day.unique()); mid = days[len(days)//2]
        for half,sub in (('H1',blk[blk.day<mid]),('H2',blk[blk.day>=mid])):
            sel = sub[m.loc[sub.index]]
            out.append(dict(split=sp,half=half,n=len(sel),
                wr=sel.outcome.mean() if len(sel) else np.nan,
                ev=sel.r.mean() if len(sel) else np.nan,
                base=sub.r.mean(), lift=(sel.r.mean()-sub.r.mean()) if len(sel) else np.nan))
    print(label); print(pd.DataFrame(out).round(4).to_string(index=False))
