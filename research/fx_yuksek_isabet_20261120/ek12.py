"""EK-12: F1 bant dönüşü meta-etiketleme (LightGBM), PROTOCOL.md EK-12."""
import json
import numpy as np, pandas as pd, lightgbm as lgb
import core, families as F

GRID = F.FAMS["F1"][1]
CELLS = [GRID.index(("B", 2.0, 0.5, 2.5, 24)), GRID.index(("C", 2.0, 0.5, 2.5, 24))]
VIX = pd.read_csv(core.SRC / "data" / "vix_1990.csv")
VIX = VIX.set_index(pd.to_datetime(VIX[VIX.columns[0]]))[[c for c in VIX.columns if c.lower() == "vix"][0]]
PAR = dict(n_estimators=200, learning_rate=0.03, num_leaves=15, min_child_samples=100, subsample=0.8, subsample_freq=1, verbose=-1, random_state=3)
FEATS = ["hr", "dow", "pair_c", "z", "atr_bp", "atr_rel", "dop", "prng", "slope", "body", "c_tp", "vix", "side"]


def feats() -> pd.DataFrame:
    T = pd.read_parquet(core.RES / "trades_F1.parquet")
    T = T[T.cell.isin(CELLS)].reset_index(drop=True)
    out = []
    for p, g in T.groupby("pair"):
        x = core.load(p)
        s = g.sig.values
        d = x.groupby("day").agg(h=("h", "max"), l=("l", "min"))
        prng = ((d.h - d.l).shift(1) / 1).reindex(x.day).values
        f = pd.DataFrame(index=g.index)
        f["z"] = ((x.c - x.sma) / x.sd).values[s]
        f["atr_bp"] = (x.atr / x.c * 1e4).values[s]
        f["atr_rel"] = (x.atr / x.atr.rolling(96).mean()).values[s]
        f["dop"] = ((x.c - x.dopen) / x.atrd).values[s]
        f["prng"] = (prng / x.atrd.values)[s]
        f["slope"] = ((x.sma - x.sma.shift(20)) / x.atr).values[s]
        f["body"] = ((x.c - x.o) / x.atr).values[s]
        out.append(f)
    T = T.join(pd.concat(out))
    T["dow"] = pd.to_datetime(T.time).dt.dayofweek
    T["pair_c"] = T.pair.astype("category").cat.codes
    T["c_tp"] = T.cost / T.tp_bp
    vd = pd.to_datetime(T.day) - pd.Timedelta(days=1)
    T["vix"] = VIX.reindex(VIX.index.union(vd.unique())).sort_index().ffill().reindex(vd).values
    T["y"] = (T.net > 0).astype(int)
    return T.sort_values("time").reset_index(drop=True)


def main() -> None:
    T = feats()
    K, B = T[T.time < core.SPLIT].reset_index(drop=True), T[T.time >= core.SPLIT].reset_index(drop=True)
    print("taban KEŞİF", core.summ(K), "\ntaban KÖR", core.summ(B))
    q = pd.to_datetime(K.time).dt.to_period("Q")
    qs = sorted(q.unique())
    blocks = np.array_split(np.array(qs), 5)
    oos = pd.Series(np.nan, index=K.index)
    for b in blocks[1:]:
        t0 = pd.Period(b[0]).start_time
        tr = K[pd.to_datetime(K.time) < t0 - pd.Timedelta(days=5)]
        te = q.isin(b)
        m = lgb.LGBMClassifier(**PAR).fit(tr[FEATS], tr.y, categorical_feature=["pair_c"])
        oos[te] = m.predict_proba(K.loc[te, FEATS])[:, 1]
    O = K[oos.notna()].assign(p=oos[oos.notna()])
    print("CV OOS taban", core.summ(O))
    rows = []
    for top in (0.05, 0.10, 0.20, 0.30):
        thr = O.p.quantile(1 - top)
        rows.append({"top": top, "thr": round(thr, 4), **core.summ(O[O.p >= thr])})
    R = pd.DataFrame(rows); print(R.to_string(index=False))
    S = R[(R.wr >= 80) & (R.ort > 0) & (R.n >= 200)]
    res = {"cv": rows, "taban_kor": core.summ(B, boot=True)}
    if len(S):
        s = S.sort_values("t", ascending=False).iloc[0]
        m = lgb.LGBMClassifier(**PAR).fit(K[FEATS], K.y, categorical_feature=["pair_c"])
        B["p"] = m.predict_proba(B[FEATS])[:, 1]
        sel = B[B.p >= s.thr]
        res["secim"] = {"top": float(s.top), "thr": float(s.thr)}
        res["KOR"] = core.summ(sel, boot=True)
        rng = np.random.default_rng(9)
        pl = np.array([B.net.values[rng.choice(len(B), len(sel), replace=False)].mean() for _ in range(400)]) if len(sel) else np.array([0])
        res["plasebo_p95"] = round(float(np.quantile(pl, 0.95)), 3)
        res["onem"] = dict(zip(FEATS, m.feature_importances_.tolist()))
    print(json.dumps(res, indent=1, default=str))
    (core.RES / "ek12.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
