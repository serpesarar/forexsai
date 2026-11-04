"""Closed-bar indicators mapped to actual fill time; no loss labels in feature code."""
from build import *

def atr(d,n=14):
    prev=d.close.shift();tr=pd.concat([d.high-d.low,(d.high-prev).abs(),(d.low-prev).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False,min_periods=n).mean()

def bar_features(d,tf):
    x=d.copy();x['ts']=pd.to_datetime(x.t,unit='s',utc=True)
    if tf>1:
        x=x.set_index('ts').resample(str(tf)+'min').agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),volume=('volume','sum'),n=('t','size'))
        x=x[x.n==tf].reset_index();x['t']=x.ts.dt.as_unit('s').astype('int64')
    x['available']=x.t+tf*60;x['atr']=atr(x)
    e20=x.close.ewm(span=20,adjust=False,min_periods=20).mean();e50=x.close.ewm(span=50,adjust=False,min_periods=50).mean()
    x['ema20']=e20;x['ema50']=e50;x['dir']=np.where((x.close>e20)&(e20>e20.shift(3)),1,np.where((x.close<e20)&(e20<e20.shift(3)),-1,0))
    x.loc[e20.isna(),'dir']=np.nan;x['stretch']=(x.close-e20)/x.atr
    dif=x.close.diff();up=dif.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean();dn=(-dif.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean();x['rsi']=100-100/(1+up/dn.replace(0,np.nan))
    m=x.close.ewm(span=12,adjust=False,min_periods=26).mean()-x.close.ewm(span=26,adjust=False,min_periods=26).mean();x['macd']=m-m.ewm(span=9,adjust=False,min_periods=9).mean()
    pu=x.high.diff();pdn=-x.low.diff();plus=pu.where((pu>pdn)&(pu>0),0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()/x.atr;minus=pdn.where((pdn>pu)&(pdn>0),0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()/x.atr
    x['adx']=(100*(plus-minus).abs()/(plus+minus).replace(0,np.nan)).ewm(alpha=1/14,adjust=False,min_periods=28).mean()
    x['clv']=(2*x.close-x.high-x.low)/(x.high-x.low).replace(0,np.nan);x['body']=(x.close-x.open)/(x.high-x.low).replace(0,np.nan)
    x['vol_ratio']=x.volume/x.volume.shift().rolling(20).median().replace(0,np.nan)
    ny=x.ts.dt.tz_convert('America/New_York');x['slot']=ny.dt.hour*60+ny.dt.minute
    x['season_vol']=x.volume/x.groupby('slot').volume.transform(lambda z:z.shift().rolling(20,min_periods=10).median()).replace(0,np.nan)
    x['age_valid']=x.t.diff().eq(tf*60).rolling(max(1,60//tf)).sum().eq(max(1,60//tf))
    if tf==1:
        x['cont240']=x.t.diff().eq(60).rolling(240).sum().eq(240)
        x['hi60']=x.high.shift().rolling(60).max();x['lo60']=x.low.shift().rolling(60).min()
        x['hi240']=x.high.rolling(240).max();x['lo240']=x.low.rolling(240).min()
        x['er60']=x.close.diff(60).abs()/dif.abs().rolling(60).sum();x['drift60']=x.close.diff(60)
        x['vr15']=x.close.diff(15).rolling(240).var()/(15*dif.rolling(240).var().replace(0,np.nan))
        x['break_fail_buy']=(x.close.shift()>x.hi60.shift())&(x.close<x.hi60.shift());x['break_fail_sell']=(x.close.shift()<x.lo60.shift())&(x.close>x.lo60.shift())
        day=ny.dt.tz_localize(None).dt.strftime('%Y-%m-%d');v=x.volume.where(x.slot>=540,0);p=((x.high+x.low+x.close)/3)*v;x['vwap']=p.groupby(day).cumsum()/v.groupby(day).cumsum().replace(0,np.nan)
        x['cross_buy']=(x.close.shift()>e20.shift())&(x.close<e20);x['cross_sell']=(x.close.shift()<e20.shift())&(x.close>e20)
    return x

def compute(d):return {tf:bar_features(d,tf)for tf in [1,5,15,60]}

def map_rows(bars,rows):
    r=rows.copy();t=r.entry_t.to_numpy();r['decision_t']=t
    for tf,x in bars.items():
        j=np.searchsorted(x.available,t,side='right')-1;k=np.maximum(j,0);ok=(j>=0)&(t-x.available.to_numpy()[k]<tf*60*2)&x.age_valid.to_numpy()[k]
        for c in ['close','atr','dir','stretch','rsi','macd','adx','clv','body','vol_ratio','season_vol','ema20','ema50']+(['cont240','hi60','lo60','hi240','lo240','er60','drift60','vr15','vwap','break_fail_buy','break_fail_sell','cross_buy','cross_sell']if tf==1 else []):
            r[f'm{tf}_{c}']=np.where(ok,x[c].to_numpy()[k],np.nan)
        r[f'm{tf}_available']=np.where(ok,x.available.to_numpy()[k],np.nan)
    r['feature_valid']=r.m1_available.notna()&r.m5_available.notna()
    r['m5_stretch_dir']=r.m5_stretch*r.side;r['drift60_dir']=r.m1_drift60*r.side/r.m5_atr
    pos=(r.m1_close-r.m1_lo240)/(r.m1_hi240-r.m1_lo240);r['pos_dir']=np.where(r.side>0,pos,1-pos)
    r['wave_valid']=r.m1_cont240.eq(1)
    r['sl_atr5']=r.risk/r.m5_atr;r['tp_atr5']=r.reward/r.m5_atr
    # Recorded/proxy quote spread observable at fill; never a future price feature.
    d=pd.read_csv(DATA/'broker_1m.csv');j=np.searchsorted(d.t,t//60*60);k=np.minimum(j,len(d)-1);r['spread_px']=np.where((j<len(d))&(d.t.to_numpy()[k]==t//60*60),d.spread_px.to_numpy()[k],np.nan)
    r['spread_risk']=r.spread_px/r.risk
    ny=pd.to_datetime(t,unit='s',utc=True).tz_convert('America/New_York');r['ny_min']=ny.hour*60+ny.minute;r['day']=ny.strftime('%Y-%m-%d');r['utc_hour']=pd.to_datetime(t,unit='s',utc=True).hour
    return r

def decisions(r):
    r=r.copy();r['bucket']=r.entry_t//60*60;rows=[]
    for (bucket,side),z in r.groupby(['bucket','side'],sort=True):
        a=z.sort_values('entry_t').iloc[0].to_dict();a['decision_id']=str(bucket)+'_'+str(side);a['positions']=len(z);a['pids']='|'.join(str(int(v))for v in z.pid);a['net']=float(z.net.sum());a['lot']=float(z.lot.sum());a['loss']=a['net']<0;a['exit_t']=int(z.exit_t.max())
        a['risk_cash']=float(z.risk_cash.sum())if z.initial_risk_verified.all()else np.nan;a['R_actual']=a['net']/a['risk_cash']if a['risk_cash']>0 else np.nan;a['family']=z.family.iloc[0]if z.family.nunique()==1 else'MIXED';rows.append(a)
    return pd.DataFrame(rows)

def main():
    d=pd.read_csv(DATA/'broker_1m.csv');b=compute(d);r=pd.read_csv(OUT/'oil_actual_positions.csv');r=map_rows(b,r);r.to_csv(OUT/'oil_position_features.csv',index=False)
    a=decisions(r);a.to_csv(OUT/'oil_decisions.csv',index=False)
    for tf,x in b.items():x.to_pickle(OUT/f'features_m{tf}.pkl')
    print('Feature availability',len(a),int(a.feature_valid.sum()),'positions',len(r),flush=True)
if __name__=='__main__':main()
