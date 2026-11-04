"""A1 — C04 post-hoc betimsel ayrıştırma (verdikti değiştirmez)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

g = load_grid()
d1 = pd.read_parquet(os.path.join(DATA, "btc_1d.parquet"), columns=["ts", "close"])
d1["dvol20"] = np.log(d1["close"]).diff().rolling(20).std()
dvol_by_day = pd.Series(d1["dvol20"].to_numpy(), index=d1["ts"].dt.normalize())
macro = pd.read_parquet(os.path.join(DATA, "macro_daily.parquet")).sort_values("date").reset_index(drop=True)
sel = macro["qqq_close"].notna() & macro["qqq_open"].notna()
prev_close = macro["qqq_close"].ffill().shift(1)
rq = np.log(macro["qqq_close"].ffill()).diff()
sig_prev = rq.rolling(20).std().shift(1)
mq = macro.loc[sel].reset_index(drop=True)
gz = (np.log(mq["qqq_open"] / prev_close[sel].to_numpy()) / sig_prev[sel].to_numpy()).to_numpy()
prev_date = macro["date"].shift(1)[sel].to_numpy()
_v = ~pd.isna(prev_date)
mq, gz, prev_date = mq.loc[_v].reset_index(drop=True), gz[_v], prev_date[_v]

def et(d, h, mnt=0):
    return pd.Timestamp(d.year, d.month, d.day, h, mnt, tzinfo=NY).tz_convert("UTC")

t10 = pd.DatetimeIndex([et(d, 10) for d in mq["date"]])
t16p = pd.DatetimeIndex([et(pd.Timestamp(d), 16) for d in prev_date])
dec = m_of(t10).to_numpy(); m16 = m_of(t16p).to_numpy()
ok = (m16 > 30 * 1440) & (dec < m_of(pd.Timestamp("2026-10-20 12:00", tz="UTC")))
dec, m16, gz, t10 = dec[ok], m16[ok], gz[ok], t10[ok]
btc_on = np.log(g.C[dec - 1] / g.O[g.nv[m16]])           # BTC gece hareketi (bilinir: 10:00'dan önce kapanan bar)
on_sig = pd.Series(btc_on).rolling(20).std().shift(1).to_numpy()
bz = btc_on / on_sig
dv = dvol_by_day.reindex(t10.normalize() - pd.Timedelta(days=1)).to_numpy()
x = next_roll(g, dec) - 2
okk = ~np.isnan(dv) & ~np.isnan(gz) & ~np.isnan(bz)
dec, gz, bz, dv, x, t10 = dec[okk], gz[okk], bz[okk], dv[okk], x[okk], t10[okk]
n = len(dec)
RL = simulate(g, dec, np.ones(n, int), x, dv, [Var("t")], risk_is_frac=True)["t"]["R"]
RS = simulate(g, dec, -np.ones(n, int), x, dv, [Var("t")], risk_is_frac=True)["t"]["R"]
per = period_of(dec); dk = day_key(dec); yrs = t10.year.to_numpy()
def R_dir(d):
    return np.where(d > 0, RL, np.where(d < 0, RS, np.nan))
out = {"corr_gz_bz": float(np.corrcoef(gz, bz)[0, 1])}
rules = {
    "QQQ_bosluk_ters_0.5": np.where(np.abs(gz) > 0.5, -np.sign(gz), 0),
    "  kol_bosluk_yukari_SELL": np.where(gz > 0.5, -1, 0),
    "  kol_bosluk_asagi_BUY": np.where(gz < -0.5, 1, 0),
    "BTC_gece_ters_0.5": np.where(np.abs(bz) > 0.5, -np.sign(bz), 0),
    "QQQ_ters | BTC_gece ayni yon": np.where((np.abs(gz) > 0.5) & (np.sign(gz) == np.sign(bz)), -np.sign(gz), 0),
    "QQQ_ters | BTC_gece ters yon": np.where((np.abs(gz) > 0.5) & (np.sign(gz) != np.sign(bz)), -np.sign(gz), 0),
    "BTC_gece_ters | QQQ |z|<=0.5": np.where((np.abs(bz) > 0.5) & (np.abs(gz) <= 0.5), -np.sign(bz), 0),
}
for name, d in rules.items():
    R = R_dir(d); row = {}
    for p in ("DISC", "OOS", "BLIND"):
        m = (per == p) & (d != 0)
        b = basic(R[m], dk[m]); row[p] = (b.get("n"), round(b.get("meanR", np.nan), 4), round(b.get("P", np.nan), 3))
    row["yil"] = {int(y): round(float(np.nanmean(R[(yrs == y) & (d != 0)])), 3) for y in np.unique(yrs)}
    out[name] = row
    print(name, row)
json.dump(out, open(os.path.join(RES, "c04_posthoc.json"), "w"), indent=1, default=str)
