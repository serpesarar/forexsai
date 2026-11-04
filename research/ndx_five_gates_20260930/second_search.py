"""Additional research selected on 2025 + pre-September 2026 only."""
from __future__ import annotations

import hashlib
import json
import numpy as np
import pandas as pd
import lab
from transfer import duka, fresh

GEOMETRIES = {
    "fast":dict(risk_mult=2.,hold_minutes=15,reward_ratio=2.),
    "core":dict(risk_mult=5.,hold_minutes=90,reward_ratio=1.5),
    "slow":dict(risk_mult=8.,hold_minutes=240,reward_ratio=2.),
}
EXTRA = ["innovation_revert","variance_switch","shock_continuation"]


def extra_features(d: pd.DataFrame, tf: int) -> pd.DataFrame:
    f=lab.features(d,tf)
    ret=f.close.diff()
    for look in [15,30,60]:
        n=max(5,round(look/tf))
        lag=ret.shift()
        cov=ret.rolling(n).cov(lag)
        phi=(cov/lag.rolling(n).var().replace(0,np.nan)).clip(-.95,.95)
        # One-step prediction coefficients come only from the previous bar.
        innovation=ret-phi.shift()*lag
        scale=innovation.shift().rolling(n).std().replace(0,np.nan)
        f[f"phi{look}"]=phi
        f[f"innov{look}"]=innovation/scale
        k=max(2,round(5/tf))
        f[f"vr{look}"]=f.close.diff(k).rolling(n).var()/(k*ret.rolling(n).var().replace(0,np.nan))
    return f


def detect(f: pd.DataFrame,spec: dict,tf: int=1):
    fam=spec["family"]
    if fam not in EXTRA:
        return lab.events(f,spec,tf)
    look=spec["lookback"]
    c,o=f.close,f.open
    z=f[f"innov{look}"]
    phi=f[f"phi{look}"]
    if fam=="innovation_revert":
        bu=(phi.shift()<-.1)&(z.shift()<-1.5)&(c>f.high.shift())&(f.clv>.2)
        se=(phi.shift()<-.1)&(z.shift()>1.5)&(c<f.low.shift())&(f.clv<-.2)
    elif fam=="variance_switch":
        vr=f[f"vr{look}"]
        # Trend regime follows a breakout; anti-persistent regime fades a sweep.
        hi,lo=f[f"hi{look}"],f[f"lo{look}"]
        bu=((vr>1.25)&(c>hi)&(f.body>.4))|((vr<.75)&(f.low<lo)&(c>lo)&(f.clv>.4))
        se=((vr>1.25)&(c<lo)&(f.body<-.4))|((vr<.75)&(f.high>hi)&(c<hi)&(f.clv<-.4))
    else:
        bu=(z>2)&(f.body>.5)&(f.clv>.5)&(phi>0)
        se=(z<-2)&(f.body<-.5)&(f.clv<-.5)&(phi>0)
    ctx=spec["context"]
    if ctx=="h1":
        bu &= f.h1_fresh & (f.h1_dir>0);se &= f.h1_fresh & (f.h1_dir<0)
    elif ctx=="efficiency":
        bu &= (f.eff>.2)&(f.path_dir>0);se &= (f.eff>.2)&(f.path_dir<0)
    elif ctx=="quiet":
        bu &= (f.atr14/f.atr70<1);se &= (f.atr14/f.atr70<1)
    if spec["side"]=="buy":se &= False
    if spec["side"]=="sell":bu &= False
    bu &= f.valid;se &= f.valid
    both=bu&se;bu &= ~both;se &= ~both
    mask=(bu|se).to_numpy()
    return f.decision.to_numpy()[mask],np.where(bu.to_numpy()[mask],1,-1)


def definitions():
    out=[]
    for fam in lab.FAMILIES+EXTRA:
        for look in [15,30,60]:
            for ctx in ["none","h1","efficiency","quiet"]:
                for side in ["both","buy","sell"]:
                    out.append(dict(id=f"{fam}_{look}_{ctx}_{side}",family=fam,lookback=look,context=ctx,side=side))
    return out


def baseline(grid: dict,p: str):
    lo,hi=map(lab.stamp,lab.PERIODS[p])
    full=pd.concat(list(grid.values()),ignore_index=True)
    full=full[(full.decision>=lo)&(full.exit_t<hi)]
    return full.groupby(["day","hour","side"]).R.mean().rename("base_R")


def score(rows: pd.DataFrame,base: pd.Series):
    stat=lab.stats(rows)
    if len(rows):
        z=rows.merge(base,on=["day","hour","side"],how="left")
        stat["baseline_ev"]=float(z.base_R.mean())
        stat["lift"]=float((z.R-z.base_R).mean())
    else:
        stat["baseline_ev"],stat["lift"]=0.,0.
    return stat


def search():
    lab.PERIODS.update({"year_a":("2025-01-02","2025-07-01"),"year_b":("2025-07-01","2025-12-31"),
        "mt5_presep":("2026-05-20","2026-08-29")})
    d1,d2=duka(),lab.load()
    f1,f2=extra_features(d1,1),extra_features(d2,1)
    recs=[]
    for geom,kw in GEOMETRIES.items():
        g1,g2=lab.simulate_grid(d1,**kw),lab.simulate_grid(d2,**kw)
        bases={p:baseline(g,p) for p,g in [("year_a",g1),("year_b",g1),("mt5_presep",g2)]}
        for i,spec in enumerate(definitions()):
            t1,s1=detect(f1,spec);t2,s2=detect(f2,spec)
            metrics={p:score(lab.replay(t,s,g,p),bases[p]) for p,t,s,g in
                [("year_a",t1,s1,g1),("year_b",t1,s1,g1),("mt5_presep",t2,s2,g2)]}
            a,b,c=metrics["year_a"],metrics["year_b"],metrics["mt5_presep"]
            volume=(a["n"]+b["n"]>=100 and min(a["n"],b["n"])>=30 and c["n"]>=60)
            eligible=volume and all(m["ev"]>0 and m["lift"]>=0 and m["worst_gap_ev"]>=0 for m in metrics.values())
            rank=min(min(m["ev"],m["lift"]) for m in metrics.values())
            recs.append({**spec,"geometry":geom,"id":spec["id"]+"_"+geom,"metrics":metrics,
                         "eligible":eligible,"volume":volume,"rank":rank})
            if i%180==179:print("second search",geom,i+1,"/540",flush=True)
    ordered=sorted(recs,key=lambda r:(r["eligible"],r["rank"]),reverse=True)
    selected=[];used=set()
    for r in ordered:
        if not r["volume"] or r["family"] in used:continue
        selected.append(r);used.add(r["family"])
        if len(selected)==5:break
    lab.save_json(lab.OUT/"second_search_1620.json",recs)
    lab.save_json(lab.OUT/"frozen_second_five.json",{"protocol_sha256":hashlib.sha256((lab.HERE/"PROTOCOL_V2.md").read_bytes()).hexdigest(),
        "evaluations":len(recs),"eligible":sum(r["eligible"] for r in recs),"candidates":selected})
    for r in selected:print("SECOND FROZEN",r["id"],"pass",r["eligible"],"metrics",r["metrics"],flush=True)


def evaluate():
    # This function is called only after frozen_second_five.json is saved.
    frozen=json.loads((lab.OUT/"frozen_second_five.json").read_text())
    d=fresh()
    lab.PERIODS["final"]=("2026-09-01","2026-09-30")
    lab.PERIODS["final_a"]=("2026-09-01","2026-09-16")
    lab.PERIODS["final_b"]=("2026-09-16","2026-09-30")
    fs={tf:extra_features(d,tf) for tf in [1,3,5]}
    results=[];portfolio=[]
    for priority,spec in enumerate(frozen["candidates"]):
        kw=GEOMETRIES[spec["geometry"]]
        grid=lab.simulate_grid(d,**kw)
        ts,sides=detect(fs[1],spec)
        rows=lab.replay(ts,sides,grid,"final")
        base,paired=lab.matched(rows,grid)
        stress={}
        for label,args in {"spread_1_5":{"spread_mult":1.5},"spread_3":{"spread_mult":3},"slip_1":{"slip":1},
            "delay_1m":{"delay":1},"fixed_80_110":{"geometry":"fixed"},
            "symmetric":{"reward_ratio":1.},"optimistic_close":{"spread_mult":0,"slip":0,"optimistic":True}}.items():
            g=lab.simulate_grid(d,**{**kw,**args})
            stress[label]=lab.stats(lab.replay(ts,sides,g,"final"))
        tr={}
        for tf in [3,5]:
            tt,ss=detect(fs[tf],spec,tf)
            tr[str(tf)]=lab.stats(lab.replay(tt,ss,grid,"final"))
        stat=lab.stats(rows);boot=lab.bootstrap(rows)
        halves={p:lab.stats(lab.replay(ts,sides,grid,p)) for p in ["final_a","final_b"]}
        checks={"volume_150":stat["n"]>=150,"positive_ev_day_bootstrap_90":stat["ev"]>0 and boot["p_positive"]>=.9,
            "both_calendar_halves":all(m["n"]>0 and m["ev"]>=0 for m in halves.values()),"spread_1_5":stress["spread_1_5"]["ev"]>0,
            "honest_vs_close_entry":abs(stress["optimistic_close"]["ev"]-stat["ev"])<=.5*abs(stat["ev"]),"one_position":stat["ev"]>0}
        results.append({"spec":spec,"final":stat,"bootstrap":boot,"matched_baseline":base,"stress":stress,
            "halves":halves,"timeframe_transfer":tr,"go_live_checks":checks,"bar_card_passes":all(checks.values()),
            "verdict":"SHADOW" if stat["n"]>=150 else "RED"})
        paired.to_csv(lab.OUT/f"second_trades_{spec['id']}.csv",index=False)
        raw=lab.replay(ts,sides,grid,"final",False);raw["candidate"],raw["priority"]=spec["id"],priority;portfolio.append(raw)
        print("SECOND FINAL",spec["id"],stat,"alpha",base,"TF",tr,flush=True)
    order=sorted(range(len(results)),key=lambda i:results[i]["matched_baseline"]["one_sided_p"])
    running=0.
    for j,i in enumerate(order):
        running=max(running,min(1.,(len(order)-j)*results[i]["matched_baseline"]["one_sided_p"]))
        results[i]["matched_baseline"]["holm_p_five"]=running
    raw=pd.concat(portfolio).sort_values(["decision","priority"]).reset_index(drop=True)
    keep=[];busy=-1;last=-1
    for i,r in enumerate(raw.itertuples()):
        if r.decision<busy or r.decision-last<600:continue
        keep.append(i);busy,last=r.exit_t,r.decision
    port=raw.iloc[keep];port.to_csv(lab.OUT/"second_portfolio_trades.csv",index=False)
    lab.save_json(lab.OUT/"second_final.json",{"candidates":results,"portfolio":{**lab.stats(port),"bootstrap":lab.bootstrap(port)},
        "freeze_sha256":hashlib.sha256((lab.OUT/"frozen_second_five.json").read_bytes()).hexdigest()})


if __name__=="__main__":
    import sys
    search() if sys.argv[1]=="search" else evaluate()
