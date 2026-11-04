"""Frozen five-rule test on an independent year/provider, plus fresh September."""
from __future__ import annotations

import json
import numpy as np
import pandas as pd
import lab


def prepare(d: pd.DataFrame, source: str) -> pd.DataFrame:
    d = d.sort_values("t").drop_duplicates("t").reset_index(drop=True)
    d["ts"] = pd.to_datetime(d.t,unit="s",utc=True)
    d["source"] = source
    d["atr70"],d["atr14"] = lab.atr(d,70),lab.atr(d,14)
    ny=d.ts.dt.tz_convert("America/New_York")
    d["ny_min"],d["day"],d["weekday"] = ny.dt.hour*60+ny.dt.minute,ny.dt.tz_localize(None).dt.strftime("%Y-%m-%d"),ny.dt.weekday
    d["valid60"] = d.t.diff().eq(60).rolling(60,min_periods=60).sum().eq(60)
    return d


def duka() -> pd.DataFrame:
    z=np.load(lab.OUT/"duka_2025.npz")
    return prepare(pd.DataFrame({k:z[k] for k in z.files}),"dukascopy_2025")


def fresh() -> pd.DataFrame:
    x=json.loads((lab.OUT/"fresh_mt5_september.json").read_text())
    d=pd.DataFrame(x["rows"],columns=["t","open","high","low","close","volume","spread"])
    points={m["point"] for m in x["chunks"]}
    assert len(points)==1
    d["spread_px"]=d.spread*points.pop()
    # Historical warmup comes only from the verified direct-MT5 export.
    old=lab.load();old=old[old.source.eq("mt5")].drop(columns=["ts"]).copy()
    return prepare(pd.concat([old,d],ignore_index=True),"mt5")


def transfer(source: str) -> None:
    d=duka() if source=="2025" else fresh()
    periods={"2025":("2025-01-02","2025-12-31"),"2025_a":("2025-01-02","2025-07-01"),
        "2025_b":("2025-07-01","2025-12-31"),"september":("2026-09-01","2026-09-30"),
        "september_a":("2026-09-01","2026-09-16"),"september_b":("2026-09-16","2026-09-30")}
    lab.PERIODS.update(periods)
    frozen=json.loads((lab.OUT/"frozen_five.json").read_text())
    grid=lab.simulate_grid(d)
    results=[]
    for tf in [1,3,5]:
        f=lab.features(d,tf)
        for spec in frozen["candidates"]:
            ts,sides=lab.events(f,spec,tf)
            p="2025" if source=="2025" else "september"
            r=lab.replay(ts,sides,grid,p)
            rec={"spec":spec["id"],"timeframe":tf,"period":p,"stats":lab.stats(r),"bootstrap":lab.bootstrap(r),
                "halves":{s:lab.stats(lab.replay(ts,sides,grid,p+s)) for s in ["_a","_b"]}}
            results.append(rec)
            r.to_csv(lab.OUT/f"transfer_{p}_{tf}m_{spec['id']}.csv",index=False)
            print("TRANSFER",p,tf,spec["id"],rec["stats"],flush=True)
    lab.save_json(lab.OUT/f"transfer_{source}.json",results)


if __name__=="__main__":
    import sys
    transfer(sys.argv[1])
