import sys, json, pandas as pd
sys.path.insert(0, ".")
from scripts.islem_otopsi import data as D
cl = D.get_client()
rows = D.fetch_table(cl, "decider_journal", "id,ts,symbol,decision,outcome,raw", [("ts","gte","2026-06-25")], "ts")
out=[]
for r in rows:
    raw = r.get("raw") or {}
    dec = raw.get("decision") or {}
    if isinstance(r.get("decision"), str):
        try: dec = {**json.loads(r["decision"]), **dec}
        except Exception: pass
    tr = raw.get("trade") or {}; live = raw.get("live") or {}; reg = raw.get("regime") or {}; vix = raw.get("vix") or {}
    out.append(dict(id=r["id"], ts=r["ts"], symbol=r["symbol"], action=dec.get("action"), direction=dec.get("direction") or tr.get("direction") or raw.get("direction"),
        size=dec.get("size_factor"), outcome=r.get("outcome") or raw.get("outcome"), pnl_r=raw.get("pnl_r"), cf_pnl_r=raw.get("cf_pnl_r"),
        rr=tr.get("rr"), atr=tr.get("atr"), spread_atr=tr.get("spread_atr"), entry=tr.get("entry_price"), sl=tr.get("sl"), tp=tr.get("tp"),
        session=live.get("session"), gate_fired=live.get("gate_fired"), rev_chan=live.get("rev_chan"), rev_vwap=live.get("rev_vwap"), adx5=live.get("adx"),
        vix=reg.get("vix") or vix.get("value"), vix_regime=vix.get("regime"), favored=vix.get("favored_ndx"), adx_1h=reg.get("adx_1h"), adx_4h=reg.get("adx_4h"),
        tf_uyum=reg.get("tf_uyum"), tf_yatay=reg.get("tf_yatay"), atrp_4h=reg.get("atrp_4h"), vol_4h=reg.get("vol_4h"), dxy=reg.get("dxy"),
        mode=raw.get("mode"), model=raw.get("model"), keys=",".join(sorted(raw.keys()))))
df = pd.DataFrame(out); df["ts"]=pd.to_datetime(df.ts, utc=True)
df.to_parquet("research/ortak_kapi_20261113/data/journal.parquet")
print(len(df)); print(df.groupby(["symbol","action","direction"],dropna=False).agg(n=("id","size"),cf=("cf_pnl_r","mean"),p=("pnl_r","mean")).round(3).to_string())
print(df["keys"].value_counts().head(5))
