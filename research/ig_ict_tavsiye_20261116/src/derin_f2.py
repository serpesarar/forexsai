"""EK-1 F2 — günlük bias mı, son likiditeye tepki mi (madde 2). Olay: PDH/PDL/ONH/ONL'ye RTH'de ilk dokunuş."""
from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd

from derin_lib import CLOSE, OPEN, OUT, RNG, load_mat, passes, prev_rth_close, price_close_before, price_open

WS = (5, 15, 30)
EXITS = {"+60": 60, "+120": 120, "1600": None}
TAU_SLICES = {"AM": (570, 720), "ogle": (720, 810), "PM": (810, 930)}
SIGNALS = ("tepki", "b1", "b2", "b3", "b4", "uyum")
N_NULL = 200
MIN_N_K = 15


def day_levels(m) -> dict[str, np.ndarray]:
    rth_h = np.nanmax(m.H[:, OPEN:CLOSE], 1)
    rth_l = np.nanmin(m.L[:, OPEN:CLOSE], 1)
    pdh, pdl = np.r_[np.nan, rth_h[:-1]], np.r_[np.nan, rth_l[:-1]]
    on_h = np.fmax(np.nanmax(m.prevH[:, 1080:], 1), np.nanmax(m.H[:, :OPEN], 1))
    on_l = np.fmin(np.nanmin(m.prevL[:, 1080:], 1), np.nanmin(m.L[:, :OPEN], 1))
    return {"PDH": pdh, "PDL": pdl, "ONH": on_h, "ONL": on_l}


def biases(m) -> dict[str, np.ndarray]:
    c = price_close_before(m, CLOSE)
    o = price_open(m, OPEN)
    prev_ret = np.r_[np.nan, (c / o - 1)[:-1]]
    sma = pd.Series(c).rolling(20).mean().to_numpy()
    b2 = np.r_[np.nan, np.sign(c - sma)[:-1]]
    rh, rl = np.nanmax(m.H[:, OPEN:CLOSE], 1), np.nanmin(m.L[:, OPEN:CLOSE], 1)
    pos = (c - rl) / (rh - rl)
    b3 = np.where(pos >= 2 / 3, 1.0, np.where(pos <= 1 / 3, -1.0, 0.0))
    b3 = np.r_[np.nan, b3[:-1]]
    p18 = np.array([row[np.isfinite(row)][0] if np.isfinite(row).any() else np.nan for row in m.prevO[:, 1080:1095]])
    return {"b1": np.sign(prev_ret), "b2": b2, "b3": b3, "b4": np.sign(o - p18)}


def events(m) -> pd.DataFrame:
    lv, bs = day_levels(m), biases(m)
    rows = []
    for i in range(len(m.days)):
        for name, arr in lv.items():
            L = arr[i]
            if not np.isfinite(L):
                continue
            is_h = name.endswith("H")
            seg = m.H[i, OPEN:CLOSE] if is_h else m.L[i, OPEN:CLOSE]
            hit = seg >= L if is_h else seg <= L
            if not hit.any():
                continue
            tau = OPEN + int(np.argmax(hit))
            if tau == OPEN:  # açılışta seviyenin ötesinde — dokunuş değil boşluk
                continue
            for w in WS:
                k = tau + w
                if k + 1 >= CLOSE - 5 or not np.isfinite(m.C[i, k]) or not np.isfinite(m.O[i, k + 1]):
                    continue
                inside = m.C[i, k] < L if is_h else m.C[i, k] > L
                tep = (-1.0 if is_h else 1.0) * (1 if inside else -1)
                e = m.O[i, k + 1]
                cost = m.S[i, k + 1] / e * 1e4
                for ex, dm in EXITS.items():
                    j = CLOSE if dm is None else min(CLOSE, k + 1 + dm)
                    blk = m.C[i, max(k + 1, j - 5):j]
                    if not np.isfinite(blk).any():
                        continue
                    ret = (blk[np.isfinite(blk)][-1] / e - 1) * 1e4
                    rows.append(dict(i=i, level=name, w=w, exit=ex, tau=tau, tepki=tep, ret=ret, cost=cost,
                                     **{b: bs[b][i] for b in bs}))
    return pd.DataFrame(rows)


def tau_slice(tau: np.ndarray) -> np.ndarray:
    out = np.full(len(tau), "", dtype=object)
    for k, (a, b) in TAU_SLICES.items():
        out[(tau >= a) & (tau < b)] = k
    return out


def table(ev: pd.DataFrame, kesif: np.ndarray, flip: np.ndarray | None = None) -> pd.DataFrame:
    ev = ev.copy()
    f = 1.0 if flip is None else flip[ev.i.to_numpy()]
    ev["uyum"] = np.where(ev.tepki == ev.b1, ev.tepki, np.nan)
    ev["K"] = kesif[ev.i.to_numpy()]
    rows = []
    for (lvl, w, ex, sl), g in ev.groupby(["level", "w", "exit", "sl"]):
        for sig in SIGNALS:
            s = g[sig].to_numpy()
            r = s * g.ret.to_numpy() * (f if np.isscalar(f) else f[g.index.to_numpy()]) - g.cost.to_numpy()
            r[(s == 0) | ~np.isfinite(s)] = np.nan
            out = dict(level=lvl, w=w, exit=ex, sl=sl, sinyal=sig)
            for per, pm in (("K", g.K.to_numpy()), ("T", ~g.K.to_numpy())):
                x = r[pm]
                x = x[np.isfinite(x)]
                n = len(x)
                mu = x.mean() if n > 2 else np.nan
                sd = x.std(ddof=1) if n > 2 else np.nan
                out.update({f"n{per}": n, f"m{per}": mu,
                            f"t{per}": mu / sd * np.sqrt(n) if n > 2 and sd > 0 else np.nan})
            rows.append(out)
    t = pd.DataFrame(rows)
    t["gecer"] = [passes(a, b, int(n)) and nk >= MIN_N_K for a, b, n, nk in zip(t.tK, t.tT, t.nT, t.nK)]
    return t


def paired(ev: pd.DataFrame, kesif: np.ndarray) -> dict:
    """Aynı girişlerde tepki-yönü − bias(b1)-yönü farkı (tavsiyenin doğrudan iddiası)."""
    out = {}
    for ex in EXITS:
        g = ev[(ev.exit == ex) & (ev.b1 != 0) & np.isfinite(ev.b1)]
        d = (g.tepki - g.b1).to_numpy() * g.ret.to_numpy()
        day = g.i.to_numpy()
        for per, pm in (("K", kesif[day]), ("T", ~kesif[day])):
            x = pd.Series(d[pm]).groupby(day[pm]).mean().to_numpy()
            out[f"{ex}|{per}"] = dict(n_gun=len(x), fark_bp=float(x.mean()), t=float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))))
    return out


def main() -> None:
    m = load_mat()
    ev = events(m)
    ev["sl"] = tau_slice(ev.tau.to_numpy())
    ev = ev[ev.sl != ""].reset_index(drop=True)
    ev.to_parquet(OUT / "f2_olaylar.parquet")
    t = table(ev, m.kesif)
    t.to_csv(OUT / "f2_hucreler.csv", index=False)
    null = [int(table(ev, m.kesif, RNG.choice([-1.0, 1.0], size=len(m.days))).gecer.sum()) for _ in range(N_NULL)]
    elig = t[(t.nK >= MIN_N_K) & (t.nT >= 30)]
    top = elig.reindex(elig.tK.abs().sort_values(ascending=False).index).head(20)
    sig_summary = elig.groupby("sinyal").apply(lambda g: pd.Series(dict(
        hucre=len(g), K_ort=g.mK.mean(), T_ort=g.mT.mean(), K_t2=(g.tK.abs() >= 2).sum(),
        ayni_isaret=(np.sign(g.tK) == np.sign(g.tT)).mean()))).round(3)
    res = dict(olay=len(ev), hucre=len(t), uygun=len(elig), gecen=int(t.gecer.sum()),
               null_ort=float(np.mean(null)), null_p95=float(np.percentile(null, 95)),
               gecenler=t[t.gecer].to_dict("records"), ilk20=top.to_dict("records"),
               ilk20_TEST_ayni_isaret=float((np.sign(top.tK) == np.sign(top.tT)).mean()),
               ilk20_TEST_ort_isaretli=float((np.sign(top.tK) * top.mT).mean()),
               sinyal_ozet=sig_summary.to_dict("index"), tepki_eksi_bias=paired(ev, m.kesif))
    (OUT / "derin_f2.json").write_text(json.dumps(res, indent=1, default=float, ensure_ascii=False))
    print({k: res[k] for k in ("olay", "hucre", "uygun", "gecen", "null_ort", "null_p95")})
    print(sig_summary.to_string())
    print(json.dumps(res["tepki_eksi_bias"], indent=1))


if __name__ == "__main__":
    main()
