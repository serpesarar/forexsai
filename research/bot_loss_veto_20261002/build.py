"""Actual PnL cohort and independent clock/quote/risk audit before veto mining."""
import sys,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DATA=HERE/'data';OUT=HERE/'results'
START=int(pd.Timestamp('2026-06-29',tz='UTC').timestamp());END=int(pd.Timestamp('2026-10-02',tz='UTC').timestamp())
MAGICS=set(range(52890969,52890976))
def save(p,z):p.write_text(json.dumps(z,ensure_ascii=False,indent=2,default=str)+'\n')
def stamps(a):return pd.to_datetime(a,utc=True).dt.as_unit('s').astype('int64')

def trades():
    raw=json.loads((DATA/'mt5_deals_orders.json').read_text());deals=pd.DataFrame(raw['deals']);orders={x['ticket']:x for x in raw['opening_orders']}
    b=pd.DataFrame(json.loads((DATA/'bot_trades.json').read_text()));b=b[b.magic.isin(MAGICS)].copy()
    b['pid']=b.raw.map(lambda x:int(x['position_id']));b['entry_t']=stamps(b.open_time)-10800;b['exit_t']=stamps(b.close_time)-10800;b['net']=b.profit+b.commission+b.swap
    b['side']=np.where(b.direction=='BUY',1,-1);b['entry'],b['exit'],b['lot']=b.open_price,b.close_price,b.volume;b['source']='bot_archive';b['entry_order']=None
    archive=b.copy();fresh=[]
    for pid,z in deals[deals.magic.isin(MAGICS)].groupby('position_id'):
        ins=z[z.entry==0];outs=z[z.entry.isin([1,3])]
        if ins.empty or outs.empty or abs(ins.volume.sum()-outs.volume.sum())>1e-7:continue
        i=ins.sort_values('time_msc').iloc[0];o=outs.sort_values('time_msc').iloc[-1]
        fresh.append({'pid':pid,'symbol':i.symbol,'direction':'BUY'if i.type==0 else'SELL','side':1 if i.type==0 else -1,'magic':int(i.magic),'entry_t':int(i.time)-10800,'exit_t':int(o.time)-10800,
                      'entry':float((ins.price*ins.volume).sum()/ins.volume.sum()),'exit':float((outs.price*outs.volume).sum()/outs.volume.sum()),'lot':float(ins.volume.sum()),
                      'net':float((z.profit+z.commission+z.swap+z.fee).sum()),'profit':float(z.profit.sum()),'commission':float(z.commission.sum()),'swap':float(z.swap.sum()),'source':'fresh_MT5','entry_order':int(i.order),'comment':o.comment,'close_reason':int(o.reason)})
    f=pd.DataFrame(fresh);q=archive.merge(f,on='pid',suffixes=('_archive','_fresh'))
    assert (q.entry_t_archive==q.entry_t_fresh).all();assert(q.exit_t_archive==q.exit_t_fresh).all()
    net_error=(q.net_archive-q.net_fresh).abs();entry_error=(q.entry_archive-q.entry_fresh).abs();assert entry_error.max()<1e-7
    b=pd.concat([b[~b.pid.isin(f.pid)],f],ignore_index=True);b=b[(b.entry_t>=START)&(b.exit_t<END)].sort_values('entry_t').reset_index(drop=True)
    fps={int(x['ticket']):x for x in json.loads((DATA/'bot_entry_fingerprints.json').read_text())}
    rows=[]
    for r in b.to_dict('records'):
        fp=fps.get(r['pid']);order=orders.get(r.get('entry_order'));r['risk_source']='missing';r['sl0']=r['tp0']=np.nan;r['fp_valid']=False
        if fp:
            ts=int(pd.Timestamp(fp['ts']).timestamp());age=r['entry_t']-ts
            valid=fp['mt5_symbol']==r['symbol']and fp['direction']==r['direction']and -120<=age<=172800
            if valid:r.update(sl0=fp['sl'],tp0=fp['tp'],risk_source='entry_fingerprint',fp_valid=True)
            rawfp=fp.get('raw')or{}
            for key in ['entry_type','scope','tp_source','voters','rr','mom_stretch','mom_threshold','session','backend_conf','entry_zone_touches','n_zones']:
                r['fp_'+key]=fp.get(key,rawfp.get(key))
            r['fp_t']=ts;r['placement_to_fill_s']=age
        if order and order['sl']>0 and order['tp']>0:
            if r['fp_valid']:assert abs(r['sl0']-order['sl'])<.05 and abs(r['tp0']-order['tp'])<.05
            r.update(sl0=order['sl'],tp0=order['tp'],risk_source='initial_filled_order')
        risk=r['side']*(r['entry']-r['sl0']);reward=r['side']*(r['tp0']-r['entry']);r['risk']=risk if risk>0 else np.nan;r['reward']=reward if reward>0 else np.nan;r['rr0']=reward/risk if risk>0 and reward>0 else np.nan
        pv=raw['symbol_metadata'].get(r['symbol'],{});value=pv.get('trade_contract_size',np.nan)
        r['risk_cash']=risk*r['lot']*value if risk>0 else np.nan;r['R_actual']=r['net']/r['risk_cash']if r['risk_cash']>0 else np.nan
        r['initial_risk_verified']=bool(r['risk_source']!='missing'and risk>0 and reward>0)
        r['entry_utc']=pd.Timestamp(r['entry_t'],unit='s',tz='UTC');r['exit_utc']=pd.Timestamp(r['exit_t'],unit='s',tz='UTC');r['loss']=r['net']<0
        r['family']={52890969:'MOM_SR',52890970:'CHREV',52890971:'VIXREG',52890973:'DAYCOMBO',52890974:'BREAKOUT',52890975:'REENTRY'}.get(r['magic'],'OTHER_BOT');rows.append(r)
    b=pd.DataFrame(rows);b.to_csv(OUT/'all_actual_positions.csv',index=False)
    oil=b[b.symbol=='SpotCrude'].copy();oil.to_csv(OUT/'oil_actual_positions.csv',index=False)
    cash=oil.profit/(oil.side*(oil.exit-oil.entry)*oil.lot)
    audit={'actual_source':'bot archive + fresh current terminal history; neither guaranteed all accounts lifetime','symbol_counts':b.symbol.value_counts().to_dict(),'oil_positions':len(oil),'oil_fp_valid':int(oil.fp_valid.sum()),'oil_initial_risk_verified':int(oil.initial_risk_verified.sum()),
           'fresh_archive_overlap':len(q),'max_overlap_net_difference':float(net_error.max()),'verified_price_value_per_lot':{'median':float(cash.median()),'min':float(cash.min()),'max':float(cash.max())},'deal_offset_seconds':10800,'partial_fill_caveat':'Archive row is closing-deal level; current history has full ins/outs, archive duplicate position audit retained','archive_duplicate_pid':int(archive.pid.duplicated().sum())}
    save(OUT/'cohort_audit.json',audit);print(audit,flush=True);return oil

def bars():
    snaps={};aud={}
    for tf,mins in [('1m',1),('5m',5),('15m',15),('1h',60)]:
        d=pd.read_csv(DATA/('snap_'+tf+'.csv'));dt=pd.to_datetime(d.candle_time,utc=True)
        legacy=dt<pd.Timestamp('2026-07-28 18:00',tz='UTC');recent=dt>=pd.Timestamp('2026-07-28 21:00',tz='UTC');amb=int((~legacy&~recent).sum());d=d[legacy|recent].copy();dt=dt[legacy|recent]
        d['t']=dt.dt.as_unit('s').astype('int64')-np.where(legacy[legacy|recent],10800,0)
        d=d[d.t% (mins*60)==0].drop_duplicates('t',keep='last').sort_values('t').reset_index(drop=True)
        assert (d.high>=d[['open','close']].max(axis=1)-1e-6).all();assert(d.low<=d[['open','close']].min(axis=1)+1e-6).all()
        snaps[tf]=d;aud[tf]={'n':len(d),'ambiguous_removed':amb,'first_utc':str(pd.to_datetime(d.t.min(),unit='s',utc=True)),'last_utc':str(pd.to_datetime(d.t.max(),unit='s',utc=True))}
    d=snaps['1m'];direct=pd.read_csv(ROOT/'research/wti_transfer_20261002/data/mt5_1m.csv');direct=direct[direct.t<END]
    q=d[['t','close']].merge(direct[['t','close']],on='t',suffixes=('_snap','_direct'));err=(q.close_snap-q.close_direct).abs()
    aud['snapshot_direct_overlap']={'n':len(q),'median_abs':float(err.median()),'p99_abs':float(err.quantile(.99)),'max_abs':float(err.max())}
    assert len(q)>1000 and err.quantile(.99)<.03,'Snapshot/direct instrument integrity failure'
    d['spread_px']=.025;d['source']='MT5_snapshot';direct['source']='MT5_direct'
    d=pd.concat([d[~d.t.isin(direct.t)],direct],ignore_index=True).sort_values('t').reset_index(drop=True)
    d['ts']=pd.to_datetime(d.t,unit='s',utc=True);d.to_csv(DATA/'broker_1m.csv',index=False)
    # Legacy clock independently cross-checked against cached historical feed by daily-demeaned alignment.
    cache=pd.read_csv(ROOT/'research/wti_transfer_20261002/data/clean_1m.csv');scans=[]
    old=snaps['1m'];old=old[old.t<int(pd.Timestamp('2026-07-28 15:00',tz='UTC').timestamp())]
    for off in [0,10800,-10800]:
        q=old[['t','close']].assign(t=lambda x:x.t+off).merge(cache[['t','close']],on='t',suffixes=('_snap','_cache'));day=pd.to_datetime(q.t,unit='s',utc=True).dt.date;diff=q.close_snap-q.close_cache;e=diff-diff.groupby(day).transform('median');scans.append({'extra_offset':off,'n':len(q),'demeaned_mad':float(e.abs().median())})
    assert min(scans,key=lambda x:x['demeaned_mad'])['extra_offset']==0;aud['legacy_clock_crosscheck']=scans
    save(OUT/'bar_audit.json',aud);print('Bar audit',aud,flush=True);return d

def main():
    trades();bars()
if __name__=='__main__':main()
