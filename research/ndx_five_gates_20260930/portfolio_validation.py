"""Predeclared frozen five-rule portfolio, without optimizing final priority."""
from __future__ import annotations

import json
import pandas as pd
import lab
from second_search import GEOMETRIES, extra_features, detect
from transfer import fresh, duka


def portfolio(fs,grids,specs,period):
    raw=[]
    for priority,spec in enumerate(specs):
        ts,side=detect(fs,spec)
        r=lab.replay(ts,side,grids[spec["geometry"]],period,False).copy()
        r["candidate"],r["priority"]=spec["id"],priority
        raw.append(r)
    allrows=pd.concat(raw).sort_values(["decision","priority"]).reset_index(drop=True)
    keep=[];busy=-1;last=-1
    for i,r in enumerate(allrows.itertuples()):
        if r.decision<busy or r.decision-last<600:continue
        keep.append(i);busy,last=r.exit_t,r.decision
    return allrows.iloc[keep].reset_index(drop=True)


def main():
    specs=json.loads((lab.OUT/"frozen_second_five.json").read_text())["candidates"]
    lab.PERIODS.update({"year_a":("2025-01-02","2025-07-01"),"year_b":("2025-07-01","2025-12-31"),
        "mt5_presep":("2026-05-20","2026-08-29"),"september":("2026-09-01","2026-09-30"),
        "september_a":("2026-09-01","2026-09-16"),"september_b":("2026-09-16","2026-09-30")})
    results={}
    for source in ["2025","2026"]:
        d=duka() if source=="2025" else fresh()
        f=extra_features(d,1)
        cases={"primary":{},"spread_1_5":{"spread_mult":1.5},"spread_3":{"spread_mult":3},"slip_1":{"slip":1.},"delay_1m":{"delay":1}}
        for case,args in cases.items():
            if source=="2025" and case!="primary":continue
            grids={g:lab.simulate_grid(d,**{**kw,**args}) for g,kw in GEOMETRIES.items()}
            periods=["year_a","year_b"] if source=="2025" else ["mt5_presep","september","september_a","september_b"]
            for period in periods:
                r=portfolio(f,grids,specs,period)
                rec={**lab.stats(r),"bootstrap":lab.bootstrap(r),"contributions":{n:lab.stats(v) for n,v in r.groupby("candidate")}}
                results[f"{period}_{case}"]=rec
                print("PORTFOLIO CHECK",period,case,"n",rec["n"],"EV",rec["ev"],"R",rec["total_R"],flush=True)
    lab.save_json(lab.OUT/"portfolio_validation.json",results)


if __name__=="__main__":main()
