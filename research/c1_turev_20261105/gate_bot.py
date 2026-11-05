import importlib.util, json, numpy as np, pandas as pd
from pathlib import Path
from lab2 import *
from r4_core import series, feats
R = Path(__file__).resolve().parents[2]; sp = importlib.util.spec_from_file_location("remote", R / "scripts/remote.py"); rm = importlib.util.module_from_spec(sp); sp.loader.exec_module(rm); c = rm._client()
rows, off = [], 0
while True:
    r = c.table("bot_trades").select("ticket,symbol,normalized_symbol,direction,volume,open_time,close_time,open_price,close_price,profit,commission,swap,comment,magic").not_.is_("close_time", "null").range(off, off + 999).execute().data
    rows += r; off += 1000
    if len(r) < 1000: break
t = pd.DataFrame(rows); t.to_parquet(HERE / "results/bot_trades.parquet"); print("işlem", len(t), t.normalized_symbol.value_counts().head(6).to_dict(), t.open_time.min()[:10], t.open_time.max()[:10]); print(t.magic.value_counts().head(8).to_dict())
t["ts"] = pd.to_datetime(t.open_time, utc=True, format="ISO8601").dt.tz_convert("America/New_York").dt.tz_localize(None); t["dir"] = t.direction.str.upper().str[:1].map({"B": 1, "S": -1}); t["bp"] = t.dir * (t.close_price.astype(float) / t.open_price.astype(float) - 1) * 1e4; t["usd"] = t.profit.astype(float) + t.commission.fillna(0).astype(float) + t.swap.fillna(0).astype(float)
n = t[t.symbol.str.contains("NAS", case=False, na=False) | t.normalized_symbol.astype(str).str.contains("NDX|NAS", case=False)].copy()
s = series("NAS100", "M15", 945); f = feats(s, "NAS100"); ind = pd.DataFrame({"rsi2": f.rsi2, "vix": f.vix, "t": s.index + pd.Timedelta(minutes=945)}).dropna(subset=["rsi2"]).sort_values("t")
n = pd.merge_asof(n.sort_values("ts"), ind, left_on="ts", right_on="t", direction="backward", tolerance=pd.Timedelta(days=5)).dropna(subset=["rsi2"])
n["kova"] = pd.cut(n.rsi2, [-1, 10, 25, 50, 75, 90, 101], labels=["<10", "10-25", "25-50", "50-75", "75-90", ">90"]); n["gün"] = n.ts.dt.normalize()
def st(g):
    days = g.groupby("gün").bp.mean(); rng = np.random.default_rng(1); ix = rng.integers(0, len(days), (3000, len(days))); return pd.Series({"n": len(g), "gün": g.gün.nunique(), "bp": round(g.bp.mean(), 1), "isabet": round((g.bp > 0).mean(), 3), "usd": round(g.usd.sum()), "P(gün bp>0)": round(float((days.to_numpy()[ix].mean(1) > 0).mean()), 3)})
pd.set_option("display.width", 200)
print(n.groupby(["dir", "kova"], observed=True).apply(st).to_string())
print(n.assign(vh=n.vix >= 18.4).groupby(["dir", "vh"]).apply(st).to_string())
print("\nkaynak (comment ön eki):")
n["kaynak"] = n.comment.fillna("").str.replace(r"^fxs ", "", regex=True).str.split().str[0].str[:10]
print(n.groupby(["kaynak", "dir"]).apply(st).query("n>=15").sort_values("usd").to_string())
print("\nSELL ∧ rsi2<25 kaynak:"); print(n[(n.dir < 0) & (n.rsi2 < 25)].groupby("kaynak").apply(st).query("n>=5").to_string())
