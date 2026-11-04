"""Replay all original opportunities when adding rare CAPREV episodes."""
import hashlib
from pathlib import Path
import pandas as pd
from paths import HERE,OUT,prior,lab,metrics,M1_PERIODS

def main():
    lab.PERIODS.update(M1_PERIODS)
    result={"protocol_sha256":hashlib.sha256((HERE/"PROTOCOL_PORTFOLIO.md").read_bytes()).hexdigest(),
            "code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"results":{}}
    for source,d in prior.load_data().items():
        f=pd.read_pickle(prior.OUT/f"features_{source}_1.pkl")
        x=prior.events(f,1)
        periods=[p for p in M1_PERIODS if p.startswith("D25")== (source=="duka")]
        for case,kw in {"base":{},"spread3":{"spread_mult":3},"slip1":{"slip":1.},"delay1":{"delay":1}}.items():
            geoms=prior.old2.GEOMETRIES
            grids={g:lab.simulate_grid(d,**{**params,**kw})for g,params in geoms.items()}
            for period in periods:
                raw=[]
                for (priority,name,geom),z in x.groupby(["priority","candidate","geometry"]):
                    a=lab.replay(z.decision.to_numpy(),z.side.to_numpy(),grids[geom],period,False)
                    a["priority"],a["candidate"]=int(priority)+1,name
                    raw.append(a)
                raw=pd.concat(raw,ignore_index=True)
                base=prior.sequential(raw)
                base.to_csv(OUT/f"portfolio_{period}_{case}_BASE.csv",index=False)
                result["results"][f"{period}_{case}_BASE"]=metrics(base,base)
                lo,hi=map(lab.stamp,M1_PERIODS[period])
                for rule in ["BASE","HALF_RISING","TP1_RISING"]:
                    cap=pd.read_csv(OUT/f"trades_{source}_1_{case}_{rule}.csv")
                    cap=cap[(cap.decision>=lo)&(cap.exit_t<hi)].copy();cap["priority"],cap["candidate"]=0,"CAP_"+rule
                    a=prior.sequential(pd.concat([raw,cap],ignore_index=True))
                    a.to_csv(OUT/f"portfolio_{period}_{case}_{rule}_ADD.csv",index=False)
                    info=metrics(a,base)
                    info["cap_raw_n"]=len(cap)
                    info["cap_taken_n"]=int(a.candidate.str.startswith("CAP_").sum())
                    info["cap_taken_R"]=float(a.loc[a.candidate.str.startswith("CAP_"),"R"].sum())
                    result["results"][f"{period}_{case}_{rule}_ADD"]=info
                print("PORTFOLIO",source,period,case,flush=True)
    result["evaluation_cells"]=len(result["results"])
    lab.save_json(OUT/"portfolio.json",result)
    print("DONE",len(result["results"]),flush=True)

if __name__=="__main__":main()
