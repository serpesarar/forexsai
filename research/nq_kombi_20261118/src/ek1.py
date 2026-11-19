"""EK-1: kopya, bağımsız dönem, veto birleşik."""
import json
import numpy as np, pandas as pd
import vk as V

def ndx_ohlc():
    d = pd.read_parquet(V.ROOT / "research/nq_akis_20261118/data/NDX.parquet")
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return pd.DataFrame({"o": d.Open, "h": d.High, "l": d.Low, "c": d.Close}).astype(float).dropna()

def trades_from(x):
    c, o, h, l, idx = x.c.values, x.o.values, x.h.values, x.l.values, x.index
    r2 = V.rsi2(x.c).values; rows=[]; i=0
    while i < len(x)-1:
        if r2[i] < 10:
            j=i+1
            while j < min(i+5,len(x)-1) and not c[j] > c[j-1]: j+=1
            rows.append({"d":idx[i],"net":(c[j]/c[i]-1)*1e4-2-V.FIN*(idx[j]-idx[i]).days}); i=j; continue
        i+=1
    k1=(c<=(h+l)/2*0.995)&(c<o); ii=np.flatnonzero(k1[:-1])
    return {"C3b":pd.DataFrame(rows),"K1":pd.DataFrame({"d":idx[ii],"net":(c[ii+1]/c[ii]-1)*1e4-2-V.FIN*(idx[ii+1]-idx[ii]).days.values}),
            "ES":pd.DataFrame({"d":idx[ii],"net":(c[ii+1]/o[ii+1]-1)*1e4-2})}

def stat(tr, m, ok):
    return V.diff_stat(tr, m & ok, ok)

out={}
# (a) kopya
for t, iv in (("QQQ", V.vxn()), ("SPY", V.vix())):
    tr = V.rule_trades(t)["C3b"]; tr = tr[tr.d >= "2001-01-01"].reset_index(drop=True)
    D = V.dims(t, iv)
    vp = D["B1_VP1"].reindex(tr.d).fillna(False).values.astype(bool)
    vx = D["B6_VIX18"].reindex(tr.d).fillna(False).values.astype(bool)
    ok = D["_valid"]["B1_VP1"].reindex(tr.d).fillna(False).values.astype(bool)
    out[f"a_{t}_C3b_VP1_VIXust"] = stat(tr, vp, ok & vx)
    out[f"a_{t}_C3b_VP1_VIXalt"] = stat(tr, vp, ok & ~vx)
# (b) bağımsız dönem
nd = ndx_ohlc(); ndf = V.U.frame(nd.c)
p_nd = V.vrp_pct(ndf, V.vix())
for rn, tr in trades_from(nd).items():
    if rn == "ES": continue
    tr = tr[(tr.d >= "1990-01-01") & (tr.d <= "2000-12-31")].reset_index(drop=True)
    pv = p_nd.reindex(tr.d); ok = pv.notna().values
    out[f"b_NDX9000_{rn}_VP1"] = stat(tr, (pv >= 0.8).values, ok)
    out[f"b_NDX9000_{rn}_VPdusuk"] = stat(tr, (pv <= 0.2).values, ok)
sp = V.ohlc("SPY"); spf = V.N.frame("SPY"); p_sp = V.vrp_pct(spf, V.vix())
on = np.log(spf.o / spf.c.shift(1)); idr = np.log(spf.c / spf.o); tug = V.N.pct(on.rolling(20).sum() - idr.rolling(20).sum())
for rn, tr in trades_from(sp).items():
    tr = tr[(tr.d >= "1993-01-01") & (tr.d <= "2000-12-31")].reset_index(drop=True)
    pv = p_sp.reindex(tr.d); ok = pv.notna().values
    out[f"b_SPY9300_{rn}_VP1"] = stat(tr, (pv >= 0.8).values, ok)
    out[f"b_SPY9300_{rn}_VPdusuk"] = stat(tr, (pv <= 0.2).values, ok)
    tg = tug.reindex(tr.d); okt = tg.notna().values
    out[f"b_SPY9300_{rn}_cekisme"] = stat(tr, (tg >= 0.8).values, okt)
# (c) veto birleşik 2001+
for t, iv in (("QQQ", V.vxn()), ("SPY", V.vix())):
    R = V.rule_trades(t); D = V.dims(t, iv)
    for rn in ("C3b", "K1", "ES"):
        tr = R[rn]; tr = tr[tr.d >= "2001-01-01"].reset_index(drop=True)
        lo = D["B2_VPdusuk"].reindex(tr.d).fillna(False).values.astype(bool)
        ok = D["_valid"]["B2_VPdusuk"].reindex(tr.d).fillna(False).values.astype(bool)
        out[f"c_{t}_{rn}_VPdusuk_tum"] = stat(tr, lo, ok)
for k, v in out.items(): print(k, v)
V.RES.joinpath("ek1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
