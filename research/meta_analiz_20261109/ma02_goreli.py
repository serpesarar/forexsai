"""MA-02: ABD endekslerinde göreli RSI2 geri dönüşü (piyasa-nötr). Ön kayıt: PROTOCOL.md."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MT5 = ROOT / "c1_turev_20261105/data/mt5"
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(exist_ok=True)
RSI_LO, RSI_HI, MAX_HOLD = 10.0, 90.0, 5
COST_YAHOO_BP, FIN_BP, SPREAD_STRESS = 4.0, 1.5, 1.5
N_BOOT, N_PLACEBO = 3000, 500


def rsi2(s: pd.Series) -> pd.Series:
    g = s.diff()
    up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean()
    dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean()
    return 100 - 100 / (1 + up / (dn + 1e-12))


def rel(logp: pd.DataFrame) -> pd.DataFrame:
    """X_i = ln P_i − diğerlerinin ortalaması."""
    n = logp.shape[1]
    tot = logp.sum(axis=1)
    return logp.apply(lambda c: c - (tot - c) / (n - 1))


def simulate(xs: np.ndarray, xe: np.ndarray, sig: np.ndarray, side: int, cost: np.ndarray) -> list[tuple[int, int, float, float]]:
    """xs: sinyal fiyatından göreli seri, xe: icra fiyatından göreli seri. Tek pozisyon zinciri."""
    out, i, n = [], 0, len(xs)
    while i < n - 1:
        if sig[i]:
            j = next((k for k in range(i + 1, min(i + MAX_HOLD + 1, n)) if side * (xs[k] - xs[k - 1]) > 0), min(i + MAX_HOLD, n - 1))
            gross = side * (xe[j] - xe[i]) * 1e4
            out.append((i, j, gross, gross - cost[i] - FIN_BP * (j - i)))
            i = j
            continue
        i += 1
    return out


def month_p(idx: pd.DatetimeIndex, v: np.ndarray, rng) -> float:
    ym = idx.to_period("M").astype(str)
    groups = [v[ym == u] for u in np.unique(ym)]
    c = 0
    for _ in range(N_BOOT):
        pick = rng.integers(0, len(groups), len(groups))
        c += np.concatenate([groups[k] for k in pick]).mean() > 0
    return c / N_BOOT


def run(XS: pd.DataFrame, XE: pd.DataFrame, COST: pd.DataFrame, side: int, rng, label: str) -> dict:
    rows = []
    for col in XS.columns:
        r = rsi2(XS[col]).to_numpy()
        sig = (r < RSI_LO) if side == 1 else (r > RSI_HI)
        sig[:20] = False
        for i, j, g, net in simulate(XS[col].to_numpy(), XE[col].to_numpy(), sig, side, COST[col].to_numpy()):
            rows.append((XS.index[i], col, j - i, g, net))
    tr = pd.DataFrame(rows, columns=["t", "sym", "hold", "gross", "net"]).sort_values("t")
    if tr.empty:
        return {"etiket": label, "n": 0}
    idx = pd.DatetimeIndex(tr.t)
    # plasebo: sinyali dairesel kaydır
    pl = []
    for _ in range(N_PLACEBO):
        vals = []
        for col in XS.columns:
            r = rsi2(XS[col]).to_numpy()
            sig = (r < RSI_LO) if side == 1 else (r > RSI_HI)
            sig[:20] = False
            sig = np.roll(sig, int(rng.integers(20, len(sig) - 20)))
            vals += [x[3] for x in simulate(XS[col].to_numpy(), XE[col].to_numpy(), sig, side, COST[col].to_numpy())]
        pl.append(np.mean(vals) if vals else np.nan)
    pl = np.array(pl)
    h = len(tr) // 2
    return {
        "etiket": label, "n": int(len(tr)), "brut_ort": round(float(tr.gross.mean()), 2), "net_ort": round(float(tr.net.mean()), 2),
        "net_med": round(float(tr.net.median()), 2), "isabet": round(float((tr.net > 0).mean()), 3), "sure": round(float(tr.hold.mean()), 2),
        "maliyet_ort": round(float((tr.gross - tr.net).mean()), 2), "P_net_poz": round(month_p(idx, tr.net.to_numpy(), rng), 3),
        "yari": [round(float(tr.net.iloc[:h].mean()), 2), round(float(tr.net.iloc[h:].mean()), 2)],
        "plasebo_net_ort": round(float(np.nanmean(pl)), 2), "plasebo_yuzdelik": round(float((pl < tr.net.mean()).mean()), 3),
        "sembol": tr.groupby("sym").net.agg(["size", "mean"]).round(2).to_dict("index"),
        "net_ss": round(float(tr.net.std()), 1),
    }


def yahoo() -> pd.DataFrame:
    d = {}
    for s in ("NDX", "GSPC", "DJI"):
        q = pd.read_parquet(ROOT / f"fitil_ret_20261106/data_d1_{s}.parquet")
        q.index = pd.DatetimeIndex(q.index).tz_localize(None).normalize()
        d[s] = np.log(q.Close)
    return pd.DataFrame(d).dropna()


def broker() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    meta = {}
    for f in ("meta.json", "meta2.json"):
        p = MT5 / f
        if p.exists():
            meta.update({k: v for k, v in json.loads(p.read_text()).items() if isinstance(v, dict)})
    S, E, C = {}, {}, {}
    for sym in ("NAS100", "US500", "US30", "US2000"):
        x = pd.read_csv(MT5 / f"{sym}_M30.csv.gz")
        x["ts_et"] = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7)
        x = x[x.ts_et.dt.dayofweek < 5].reset_index(drop=True)
        m = (x.ts_et.dt.hour * 60 + x.ts_et.dt.minute == 930) & (x.t.diff() <= 3 * 1800)
        d = x.ts_et.dt.normalize()[m].to_numpy()
        keep = ~pd.Index(d).duplicated()
        point = meta.get(sym, {}).get("point")
        if point is None:
            raise SystemExit(f"{sym} için point bilgisi yok (meta)")
        S[sym] = pd.Series(np.log(x.c.shift(1)[m].to_numpy()[keep]), index=d[keep])
        E[sym] = pd.Series(np.log(x.o[m].to_numpy()[keep]), index=d[keep])
        C[sym] = pd.Series((x.sp[m].to_numpy()[keep] * point) / x.o[m].to_numpy()[keep] * 1e4, index=d[keep])
    S, E, C = pd.DataFrame(S).dropna(), pd.DataFrame(E), pd.DataFrame(C)
    E, C = E.reindex(S.index), C.reindex(S.index)
    return S, E, C


def main() -> None:
    rng = np.random.default_rng(23)
    res = {}
    lp = yahoo()
    for label, a, b in (("KESIF_1999_2009", "1999-01-01", "2010-01-01"), ("TEST_2010_2018", "2010-01-01", "2018-05-01")):
        seg = lp[(lp.index >= a) & (lp.index < b)]
        X = rel(seg)
        cost = pd.DataFrame(COST_YAHOO_BP, index=X.index, columns=X.columns)
        res[label] = {"uzun_geride_kalan": run(X, X, cost, +1, rng, label), "ayna_kisa_one_gecen": run(X, X, cost, -1, rng, label)}
    S, E, C = broker()
    XS, XE = rel(S), rel(E)
    n = C.shape[1]
    tot = C.sum(axis=1)
    cost = C.apply(lambda c: (c + (tot - c) / (n - 1)) * SPREAD_STRESS)   # bacak başına tam spread (gidiş-dönüş) × stres
    res["KOR_BROKER_2018_2026"] = {
        "donem": [str(S.index[0].date()), str(S.index[-1].date())], "gun": int(len(S)), "medyan_maliyet_bp": round(float(cost.median().mean()), 2),
        "uzun_geride_kalan": run(XS, XE, cost, +1, rng, "KOR"), "ayna_kisa_one_gecen": run(XS, XE, cost, -1, rng, "KOR"),
    }
    (OUT / "ma02.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for k, v in res.items():
        for kk in ("uzun_geride_kalan", "ayna_kisa_one_gecen"):
            r = v[kk]
            print(k, kk, {x: r[x] for x in ("n", "brut_ort", "net_ort", "isabet", "sure", "maliyet_ort", "P_net_poz", "yari", "plasebo_net_ort", "plasebo_yuzdelik", "net_ss") if x in r})
            print("   ", r.get("sembol"))


if __name__ == "__main__":
    main()
