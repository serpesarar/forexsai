"""Tek hücre KÖR + plasebo. Kullanım: kor.py F1 53 USDJPY,GBPJPY,EURCHF,CHFJPY"""
import sys, json
import numpy as np, pandas as pd
import core, families as F
fam, ci, pairs = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(",")
fn, grid = F.FAMS[fam]; cell = grid[ci]
T = pd.read_parquet(core.RES / f"trades_{fam}.parquet")
T = T[(T.cell == ci) & T.pair.isin(pairs)]
out = {"cell": str(cell), "pairs": pairs}
for nm, g in (("KESIF", T[T.time < core.SPLIT]), ("KOR", T[T.time >= core.SPLIT])):
    out[nm] = core.summ(g, boot=True)
    out[nm + "_cift"] = {p: core.summ(gg) for p, gg in g.groupby("pair")}
# plasebo (KÖR): aynı çift, aynı saat, rastgele bar & yön, aynı ATR katları
K = T[T.time >= core.SPLIT]
rng = np.random.default_rng(11)
tpk = cell[2] if cell[2] != "MID" else None
pl = []
for draw in range(40):
    res = []
    for p, g in K.groupby("pair"):
        x = core.load(p)
        pool = {h: np.where((x.hr.values == h) & (x.srv.values >= np.datetime64(core.SPLIT)) & (x.atr.values > 0))[0] for h in g.hr.unique()}
        idx = np.array([rng.choice(pool[h]) for h in g.hr.values])
        side = rng.choice([-1, 1], len(idx))
        a = x.atr.values[idx]
        tp = (tpk * a) if tpk else g.tp_bp.values / 1e4 * x.c.values[idx]
        t = core.run(x, idx, side, tp, cell[3] * a, np.full(len(idx), cell[4]))
        res.append(t.net.values)
    v = np.concatenate(res)
    pl.append((v.mean(), (v > 0).mean() * 100))
pl = np.array(pl)
out["plasebo"] = {"ort_p95": round(float(np.percentile(pl[:, 0], 95)), 3), "ort_med": round(float(np.median(pl[:, 0])), 3),
                  "wr_med": round(float(np.median(pl[:, 1])), 1), "hucre_yuzdelik": round(float((pl[:, 0] < out["KOR"]["ort"]).mean()), 3)}
# stres
out["KOR"]["stres15"] = round(float((K.gross - 1.5 * K.cost).mean()), 3)
print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
(core.RES / f"kor_{fam}_{ci}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
