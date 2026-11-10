"""MA-05 B: lot zamanlaması beceri taşıdı mı? Aile içi lot karıştırma plasebosu. Ön kayıt: PROTOCOL.md EK-2."""
import json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; OUT = Path(__file__).resolve().parent / "results"; B = 5000
t = pd.read_parquet(ROOT / "tp_sonrasi_ters_20261109/data/ndx_trades.parquet"); t = t[t.sl0 > 0].copy()
t["dist"] = (t.open_price - t.sl0).abs(); t["gun"] = t.entry_utc.dt.date
d = t.groupby(["family", "decision"]).agg(lot=("volume", "sum"), dist=("dist", "mean"), net=("net", "sum"), gun=("gun", "first")).reset_index()
d["R"] = d.net / (d.dist * d.lot); d["pnl1"] = d.R * d.dist          # 1 lot başına $ (lot ile çarpılınca gerçek net)
assert abs((d.pnl1 * d.lot).sum() - d.net.sum()) < 1
rng = np.random.default_rng(41); fam = d.family.to_numpy(); lot = d.lot.to_numpy(); pnl1 = d.pnl1.to_numpy(); gi = pd.factorize(d.gun)[0]; ng = gi.max() + 1
def stats(l):
    pnl = pnl1 * l; day = np.bincount(gi, pnl, ng); return pnl.sum(), np.sort(day)[:5].sum(), day.mean() / day.std(ddof=1)
real = stats(lot); sims = np.empty((B, 3)); idx = {f: np.flatnonzero(fam == f) for f in np.unique(fam)}
for b in range(B):
    l = lot.copy()
    for f, ix in idx.items(): l[ix] = rng.permutation(lot[ix])
    sims[b] = stats(l)
res = {"karar": int(len(d)), "gercek": {"net": round(real[0]), "enkotu5": round(real[1]), "gunlukSR": round(real[2], 3)},
       "plasebo": {"net_medyan": round(float(np.median(sims[:, 0]))), "net_%5_%95": [round(float(np.quantile(sims[:, 0], q))) for q in (.05, .95)], "enkotu5_medyan": round(float(np.median(sims[:, 1]))), "SR_medyan": round(float(np.median(sims[:, 2])), 3)},
       "gercek_net_yuzdelik": round(float((sims[:, 0] < real[0]).mean()), 3), "gercek_enkotu5_yuzdelik": round(float((sims[:, 1] < real[1]).mean()), 3), "gercek_SR_yuzdelik": round(float((sims[:, 2] < real[2]).mean()), 3)}
# aile bazında: gerçek net vs sabit (aile ortalaması) lot
res["aile"] = {f: {"karar": int(len(ix)), "lotlar": {str(k): int(v) for k, v in pd.Series(lot[ix]).round(1).value_counts().head(5).items()}, "gercek_net": round(float((pnl1[ix] * lot[ix]).sum())), "sabit_ort_lot_net": round(float(pnl1[ix].sum() * lot[ix].mean())),
                   "corr_lot_R": round(float(np.corrcoef(lot[ix], d.R.to_numpy()[ix])[0, 1]), 3) if np.std(lot[ix]) > 0 else None} for f, ix in idx.items() if len(ix) >= 10}
res["olcut_beceri"] = bool(res["gercek_net_yuzdelik"] >= .95)
print(json.dumps(res, indent=1, ensure_ascii=False)); (OUT / "ma05b.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
