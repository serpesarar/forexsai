"""Twenty frozen mechanism derivatives, historical chronological evaluation."""
from __future__ import annotations
import hashlib
import json
import time
import numpy as np
import pandas as pd
from data import HERE, OUT, lab, old2, datasets, context

PERIODS = {"D25a":("2025-01-02","2025-07-01"),"D25b":("2025-07-01","2025-12-31"),
           "C26":("2026-02-11","2026-05-16"),"M26":("2026-05-20","2026-08-29"),
           "S26":("2026-09-01","2026-09-30"),"S26a":("2026-09-01","2026-09-16"),
           "S26b":("2026-09-16","2026-09-30")}
lab.PERIODS.update(PERIODS)
GEOM = {"core":{},"fixed":{"geometry":"fixed"}}
TITLES = {"D1":"Yönlerin birleştiği geri çekilme", "D2":"Geri alınan seviyenin kabulü",
          "D3":"Sabırlı ve fiyatı kovalamayan giriş", "D4":"Stres sonrası teyitli toparlanma",
          "D5":"Yol ve tetikleyici uyumu"}


def definitions():
    return [{"family":fam,"variant":v,"geometry":g,"id":f"{fam}_{v}_{g}"}
            for fam,vs in [("D1",["m15","h1m15"]),("D2",["wait2","wait5"]),
                          ("D3",["wait3","wait5"]),("D4",["absolute","scaled"]),
                          ("D5",["breakout","both"])] for v in vs for g in GEOM]


def event(f, fam, look=30, ctx="none", side="both"):
    s = {"family":fam,"lookback":look,"context":ctx,"side":side}
    tf = int((f.decision.iloc[0] - f.ts.iloc[0].timestamp()) / 60)
    t,sd = old2.detect(f,s,tf)
    ix = np.searchsorted(f.decision.to_numpy(),t)
    z = f.iloc[ix].copy().reset_index(drop=True)
    z["origin"],z["side"] = t,sd
    return z


def parent(f,spec):
    fam=spec["family"]
    if fam in ["D1","D3"]:
        x=event(f,"efficient_pullback",30,"efficiency")
        if fam=="D3":x=x[x.m15_dir*x.side>0]
    elif fam=="D2":x=event(f,"failed_break",60)
    elif fam=="D4":
        x=pd.concat([event(f,"failed_break",60,side="buy"),
                     event(f,"efficient_pullback",30,"efficiency","buy")]).drop_duplicates(["origin","side"])
    else:
        x=event(f,"variance_switch",30,"quiet")
        x["branch"]=np.where(x.vr30>1.25,"breakout","fade")
    return x.sort_values("origin").reset_index(drop=True)


def delayed(d,x,w):
    """All confirmation values become known at origin+w minutes, never earlier."""
    x=x.copy()
    t=d.t.to_numpy();i=np.searchsorted(t,x.origin.to_numpy())
    ok=i+w<=len(d)
    safe=np.minimum(i,len(d)-1)
    ok &= t[safe]==x.origin.to_numpy()
    # The entry open belongs to execution, not to the decision feature path.
    for k in range(w):
        j=np.minimum(i+k,len(d)-1)
        ok &= t[j]==x.origin.to_numpy()+k*60
    x=x[ok].copy().reset_index(drop=True);i=i[ok]
    close=d.close.to_numpy();low=d.low.to_numpy();high=d.high.to_numpy()
    side=x.side.to_numpy()
    path=np.stack([close[i+k] for k in range(w)],axis=1)
    x["decision"]=x.origin+w*60
    x["fair_price"]=side*(path[:,-1]-x.close.to_numpy())<=.5*x.atr70.to_numpy()
    level=np.where(side>0,x.lo60.shift(0),x.hi60.shift(0))
    # For failed_break the crossed boundary is the PREVIOUS feature row's bound.
    if "reclaimed_level" in x:level=x.reclaimed_level.to_numpy()
    x["level_held"]=np.all(side[:,None]*(path-level[:,None])>0,axis=1)
    extreme=np.where(side[:,None]>0,np.stack([low[i+k] for k in range(w)],axis=1),
                     np.stack([high[i+k] for k in range(w)],axis=1))
    adverse=np.maximum(0, np.max(-side[:,None]*(extreme-x.close.to_numpy()[:,None]),axis=1))
    x["band_alive"]=adverse<=1.28*x.atr14.to_numpy()*np.sqrt(w)
    return x


def candidates(d,f,spec,mode="candidate"):
    x=parent(f,spec);fam,v=spec["family"],spec["variant"]
    if mode=="parent":return x
    if fam=="D1":
        good=x.m15_dir*x.side>0
        if v=="h1m15":good &= x.h1_fresh & (x.h1_dir*x.side>0)
    elif fam in ["D2","D3"]:
        if fam=="D2":
            j=np.searchsorted(f.decision.to_numpy(),x.origin.to_numpy())
            x["reclaimed_level"]=np.where(x.side>0,f.lo60.to_numpy()[j-1],f.hi60.to_numpy()[j-1])
        x=delayed(d,x,int(v[-1]));good=pd.Series(True,index=x.index)
        if mode!="blind":
            good &= x.level_held if fam=="D2" else x.band_alive
        if mode=="candidate":good &= x.fair_price
    elif fam=="D4":
        stress=(x.ret1<=-.015)|(x.ret5<=-.04) if v=="absolute" else x.z5<=-1
        good=stress & (x.m15_dir>0)
        if mode=="macro_only":good=stress
        if mode=="micro_only":good=x.m15_dir>0
    else:
        breaking=x.branch.eq("breakout") & (x.vr120>1.2)&(x.er60_m1>.2)&(x.drift60_m1*x.side>0)
        fading=x.branch.eq("fade") & (x.vr120<.8)&(x.m15_dir*x.side>0)
        good=breaking if v=="breakout" else breaking|fading
        good &= x.cont240
    return x[good].reset_index(drop=True)


def replay(x,g,p,sequential=True):
    x=x[x.origin.ge(lab.stamp(PERIODS[p][0]))]
    return lab.replay(x.decision.to_numpy(),x.side.to_numpy(),g,p,sequential)


def sequential(raw):
    raw=raw.sort_values(["decision","priority"] if "priority" in raw else ["decision"]).reset_index(drop=True)
    keep=[];busy,last=-1,-1
    for i,r in enumerate(raw.itertuples()):
        if r.decision<busy or r.decision-last<600:continue
        keep.append(i);busy,last=r.exit_t,r.decision
    return raw.iloc[keep].reset_index(drop=True)


def delta_boot(a,b,n=4000):
    """Paired executable total R difference on the union of candidate/base dates."""
    z=pd.concat([a.groupby("day").R.sum().rename("a"),b.groupby("day").R.sum().rename("b")],axis=1).fillna(0)
    if z.empty:return {"mean_daily_delta_R":0.,"ci95":[0.,0.],"p_positive":0.,"one_sided_p":1.,"days":0}
    v=(z.a-z.b).to_numpy();rng=np.random.default_rng(931)
    m=v[rng.integers(0,len(v),size=(n,len(v)))].mean(axis=1)
    p=float((1+(m-v.mean()>=v.mean()).sum())/(n+1))
    return {"mean_daily_delta_R":float(v.mean()),"ci95":np.quantile(m,[.025,.975]).tolist(),
            "p_positive":float((m>0).mean()),"one_sided_p":p,"days":len(v)}


def cached_features(d,source,tf):
    p=OUT/f"features_{source}_{tf}.pkl"
    if p.exists():return pd.read_pickle(p)
    tic=time.monotonic();f=context(d,tf);f.to_pickle(p)
    print("context",source,tf,len(f),round(time.monotonic()-tic,2),flush=True)
    return f


def search():
    tic=time.monotonic();ds=datasets();print("datasets",{k:len(v) for k,v in ds.items()},flush=True)
    fs={s:cached_features(d,s,1) for s,d in ds.items()}
    records=[]
    for geom,kw in GEOM.items():
        gs={s:lab.simulate_grid(d,**kw) for s,d in ds.items()};print("grid",geom,flush=True)
        for spec in [x for x in definitions() if x["geometry"]==geom]:
            xs={s:candidates(ds[s],fs[s],spec) for s in ds}
            parents={s:parent(fs[s],spec) for s in ds}
            metrics={}
            for p in ["D25a","D25b","C26"]:
                s="duka" if p.startswith("D25") else "mt5"
                a=replay(xs[s],gs[s],p);b=replay(parents[s],gs[s],p)
                metrics[p]={**lab.stats(a),"parent":lab.stats(b),"delta_total_R":float(a.R.sum()-b.R.sum())}
            eligible=(sum(m["n"] for m in metrics.values())>=100 and min(m["n"] for m in metrics.values())>=15
                      and all(m["ev"]>0 and m.get("worst_gap_ev",0)>=0 for m in metrics.values()))
            rec={**spec,"metrics":metrics,"eligible":eligible,"rank":min(m["ev"] for m in metrics.values())}
            records.append(rec);print("SCREEN",spec["id"],eligible,[(p,m["n"],round(m["ev"],3)) for p,m in metrics.items()],flush=True)
    chosen=[]
    for fam in TITLES:
        options=[r for r in records if r["family"]==fam]
        chosen.append(max(options,key=lambda r:(r["eligible"],r["rank"],sum(m["n"] for m in r["metrics"].values()))))
    lab.save_json(OUT/"screen_20.json",records)
    lab.save_json(OUT/"frozen_derivatives.json",{"candidates":chosen,"configurations":20,
        "protocol_sha256":hashlib.sha256((HERE/"PROTOCOL.md").read_bytes()).hexdigest(),
        "selection_periods":["D25a","D25b","C26"],"all_history_previously_seen":True})
    print("FROZEN",[x["id"] for x in chosen],"seconds",round(time.monotonic()-tic,1),flush=True)


def placebo(raw,accepted,repetitions=300):
    """Label-blind random gate, same raw opportunity counts by hour and side."""
    counts=accepted.groupby(["hour","side"]).size().to_dict()
    groups=list(raw.groupby(["hour","side"]).indices.items())
    rng=np.random.default_rng(934);ev=[];total=[]
    for _ in range(repetitions):
        idx=[]
        for key,ix in groups:
            n=min(len(ix),counts.get(key,0))
            if n:idx.extend(rng.choice(ix,size=n,replace=False).tolist())
        x=sequential(raw.iloc[idx]) if idx else raw.iloc[:0]
        ev.append(float(x.R.mean()) if len(x) else 0.);total.append(float(x.R.sum()))
    return {"repetitions":repetitions,"total_R_q05_q50_q95":np.quantile(total,[.05,.5,.95]).tolist(),
            "ev_q05_q50_q95":np.quantile(ev,[.05,.5,.95]).tolist(),"total_R_samples":total}


def evaluate():
    frozen=json.loads((OUT/"frozen_derivatives.json").read_text());specs=frozen["candidates"]
    ds=datasets();fs={s:{tf:cached_features(d,s,tf) for tf in [1,3,5]} for s,d in ds.items()}
    gs={s:{geom:lab.simulate_grid(d,**kw) for geom,kw in GEOM.items()} for s,d in ds.items()}
    result=[];port_raw={p:[] for p in ["D25a","D25b","C26","M26","S26"]};count=20
    for priority,spec in enumerate(specs):
        geom=spec["geometry"];recs={};tr={};variants={}
        for p in port_raw:
            source="duka" if p.startswith("D25") else "mt5"
            d,f,g=ds[source],fs[source][1],gs[source][geom]
            a=candidates(d,f,spec);b=parent(f,spec)
            ar=replay(a,g,p);br=replay(b,g,p)
            raw=replay(a,g,p,False);raw["candidate"],raw["priority"]=spec["id"],priority;port_raw[p].append(raw)
            accepted_orig=set(a.origin)
            rejected=b[~b.origin.isin(accepted_orig)]
            rejected_replay=replay(rejected,g,p)
            recs[p]={"candidate":lab.stats(ar),"parent":lab.stats(br),"rejected_parent":lab.stats(rejected_replay),
                     "delta_total_R":float(ar.R.sum()-br.R.sum()),"delta_bootstrap":delta_boot(ar,br),"bootstrap":lab.bootstrap(ar)}
            if p in ["M26","S26"]:
                rawbase=b
                if spec["family"] in ["D2","D3"]:rawbase=candidates(d,f,spec,"blind")
                pr=placebo(replay(rawbase,g,p,False),raw)
                pr["p_random_ge_observed_total"]=(1+sum(v>=ar.R.sum() for v in pr.pop("total_R_samples")))/301
                recs[p]["random_gate_placebo"]=pr
                opposite=a.copy();opposite["side"]*=-1
                recs[p]["opposite_same_decisions"]=lab.stats(replay(opposite,g,p));count+=2
                for tf in [3,5]:
                    ft=fs[source][tf]
                    # Only trigger bars aggregate; fixed M1 context and wait durations persist.
                    at=candidates(d,ft,spec)
                    tr.setdefault(p,{})[str(tf)]=lab.stats(replay(at,g,p));count+=1
                if spec["family"] in ["D2","D3"]:
                    for mode in ["blind","band_only"]:
                        variants.setdefault(p,{})[mode]=lab.stats(replay(candidates(d,f,spec,mode),g,p));count+=1
                if spec["family"]=="D4":
                    for mode in ["macro_only","micro_only"]:
                        variants.setdefault(p,{})[mode]=lab.stats(replay(candidates(d,f,spec,mode),g,p));count+=1
            ar.to_csv(OUT/f"trades_{spec['id']}_{p}.csv",index=False)
        d,f=ds["mt5"],fs["mt5"][1];a=candidates(d,f,spec)
        stress={}
        for label,extra in {"spread_1_5":{"spread_mult":1.5},"spread_3":{"spread_mult":3},
                            "slip_1":{"slip":1},"extra_delay_1m":{"delay":1},
                            "optimistic_close":{"optimistic":True,"spread_mult":0,"slip":0}}.items():
            gg=lab.simulate_grid(d,**{**GEOM[geom],**extra})
            stress[label]={p:lab.stats(replay(a,gg,p)) for p in ["M26","S26"]};count+=2
        halves={p:lab.stats(replay(a,gs["mt5"][geom],p)) for p in ["S26a","S26b"]}
        st=recs["S26"]["candidate"];bo=recs["S26"]["bootstrap"]
        bo["degenerate_single_day"]=bo["effective_days"]<2
        checks={"n_150":st["n"]>=150,"ev_and_daybootstrap90":st["ev"]>0 and bo["p_positive"]>=.9 and not bo["degenerate_single_day"],
                "both_halves":all(x["n"]>0 and x["ev"]>0 for x in halves.values()),
                "spread_stress":stress["spread_1_5"]["S26"]["ev"]>0,
                "close_entry_sensitivity":abs(stress["optimistic_close"]["S26"]["ev"]-st["ev"])<=.5*max(abs(st["ev"]),1e-9),
                "one_position":st["ev"]>0}
        result.append({"spec":spec,"periods":recs,"tf_transfer":tr,"ablation":variants,"stress":stress,
                       "halves":halves,"six_historical_checks":checks,"live_status":"RED / offline hypothesis"})
        print("EVALUATED",spec["id"],[(p,m["candidate"]["n"],round(m["candidate"]["total_R"],2))for p,m in recs.items()],flush=True)
    portfolio={}
    for p,raws in port_raw.items():
        raw=pd.concat(raws,ignore_index=True);x=sequential(raw);x.to_csv(OUT/f"portfolio_{p}.csv",index=False)
        portfolio[p]={**lab.stats(x),"bootstrap":lab.bootstrap(x)}
    port_checks={}
    for label,extra in {"spread_1_5":{"spread_mult":1.5},"spread_3":{"spread_mult":3},
                        "slip_1":{"slip":1},"extra_delay_1m":{"delay":1}}.items():
        grids={geom:lab.simulate_grid(ds["mt5"],**{**kw,**extra}) for geom,kw in GEOM.items()}
        for p in ["M26","S26"]:
            raws=[]
            for priority,spec in enumerate(specs):
                a=candidates(ds["mt5"],fs["mt5"][1],spec)
                raw=replay(a,grids[spec["geometry"]],p,False);raw["priority"]=priority;raws.append(raw)
            port_checks.setdefault(label,{})[p]=lab.stats(sequential(pd.concat(raws,ignore_index=True)));count+=1
    for tf in [3,5]:
        for p in ["M26","S26"]:
            raws=[]
            for priority,spec in enumerate(specs):
                a=candidates(ds["mt5"],fs["mt5"][tf],spec)
                raw=replay(a,gs["mt5"][spec["geometry"]],p,False);raw["priority"]=priority;raws.append(raw)
            port_checks.setdefault(f"tf_{tf}",{})[p]=lab.stats(sequential(pd.concat(raws,ignore_index=True)));count+=1
    # Familywise adjustment covers selected derivatives only, not previous discovery rounds.
    order=sorted(range(5),key=lambda i:result[i]["periods"]["S26"]["delta_bootstrap"]["one_sided_p"])
    running=0.
    for rank,i in enumerate(order):
        running=max(running,min(1.,(5-rank)*result[i]["periods"]["S26"]["delta_bootstrap"]["one_sided_p"]))
        result[i]["periods"]["S26"]["delta_bootstrap"]["holm_p_selected_five"]=running
    lab.save_json(OUT/"evaluation.json",{"candidates":result,"portfolio":portfolio,"portfolio_controls":port_checks,"configurations_and_control_cells":count,
        "frozen_sha256":hashlib.sha256((OUT/"frozen_derivatives.json").read_bytes()).hexdigest(),
        "code_sha256":hashlib.sha256((HERE/"experiment.py").read_bytes()).hexdigest(),
        "all_history_previously_seen":True})
    print("PORTFOLIO",portfolio,flush=True)

if __name__=="__main__":
    import sys
    if sys.argv[1]=="search":search()
    elif sys.argv[1]=="evaluate":evaluate()
    else:
        x=json.loads((OUT/"evaluation.json").read_text())
        for r in x["candidates"]:
            print(r["spec"]["id"],{p:{"n":m["candidate"]["n"],"R":round(m["candidate"]["total_R"],3)} for p,m in r["periods"].items()})
        print("All live statuses RED; retrospective derivative research.")
