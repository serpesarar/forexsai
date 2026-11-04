"""Two frozen post-screen combinations; never mislabeled untouched validation."""
import hashlib
import json
from pathlib import Path
from paths import (HERE,OUT,prior,native,context,detect,replay,metrics,lab,M1_PERIODS,LONG_PERIODS)

def main():
    result={"protocol_sha256":hashlib.sha256((HERE/"PROTOCOL_COMBINATIONS.md").read_bytes()).hexdigest(),
            "code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"results":{}}
    ds=prior.load_data()
    sources=[(s,d,1,[1,5,15])for s,d in ds.items()]+[(f"native{tf}",native(tf),tf,[tf])for tf in[15,30,60]]
    for source,d,step,tfs in sources:
        periods=LONG_PERIODS if step>1 else {k:v for k,v in M1_PERIODS.items() if (k.startswith("D25") if source=="duka" else not k.startswith("D25"))}
        for tf in tfs:
            f=context(d,tf,step);ev=detect(f,"VIX_RISING")
            cases={"base":{},"spread3":{"spread_mult":3},"slip1":{"slip":1.},"delay1":{"delay":1}}
            if step==1 and tf!=1:cases={"base":{}}
            for case,kw in cases.items():
                base=replay(d,detect(f,"BASE"),"BASE",step,**kw)
                own=replay(d,ev,"VIX_RISING",step,**kw)
                for rule,exit_rule in [("HALF_RISING","HALF_RUNNER"),("TP1_RISING","FULL_TP1")]:
                    a=replay(d,ev,exit_rule,step,**kw);a.candidate=rule
                    a["source"],a["trigger_tf"],a["case"]=source,tf,case
                    a.to_csv(OUT/f"trades_{source}_{tf}_{case}_{rule}.csv",index=False)
                    for p,(start,end)in periods.items():
                        lo,hi=lab.stamp(start),lab.stamp(end)
                        z=a[(a.decision>=lo)&(a.exit_t<hi)]
                        b=base[(base.decision>=lo)&(base.exit_t<hi)]
                        v=own[(own.decision>=lo)&(own.exit_t<hi)]
                        rec=metrics(z,b);rec["delta_vs_rising_R"]=float(z.R.sum()-v.R.sum())
                        result["results"][f"{source}_{tf}_{case}_{p}_{rule}"]=rec
                print("COMBINATIONS",source,tf,case,flush=True)
    result["evaluation_cells"]=len(result["results"])
    lab.save_json(OUT/"combinations.json",result)
    print("DONE",len(result["results"]),flush=True)

if __name__=="__main__":main()
