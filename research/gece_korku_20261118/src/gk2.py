"""gk2.py — gece seansı (ETH) korkusu → sabah alımı (PROTOCOL). python gk2.py kesif | dogrula | ayna"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/fitil_gece_20261118/src"))
import gece as G  # noqa: E402
import gece_run as GR  # noqa: E402

RES = ROOT / "research/gece_korku_20261118/results"
GEC = ROOT / "research/korku_birlesik_20261118/results"
TZ = "America/New_York"
TS = {"03:00": (3, 0), "08:00": (8, 0), "09:30": (9, 30)}
EXITS = {"03:00": ("09:30", "16:00", "D1_16:00"), "08:00": ("09:30", "16:00", "D1_16:00"), "09:30": ("16:00", "D1_16:00")}
THR = {"G1": (0.5, 1.0), "G2": (0.3, 0.5), "G3": (0.10, 0.20)}
N_MIN, N_PL, MAX_FROZEN, MAX_PER = 25, 20, 4, 2
P_YENI = 1 - 0.10 / MAX_FROZEN
FIN = G.lib.FIN_BP_PER_DAY


def _u(d, hh: int, mm: int) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=TZ).timestamp())


def table(b: pd.DataFrame, step: int, feed: str) -> pd.DataFrame:
    """Gün D × karar saati: gece penceresi istatistikleri, giriş ve çıkış fiyatları."""
    t, o, h, l, c, sp = (b[k].values for k in ("t", "o", "h", "l", "c", "sp"))
    tol = 300 if step == 60 else 0
    dp = G.day_prices(b, TZ, [960], step)
    days = [x for x in dp.index if x.weekday() < 5 and G.nyse_ok(x) and np.isfinite(dp.loc[x, "o960"])]
    S = pd.read_parquet(GEC / f"geceler_{feed}.parquet").set_index("d").S if (GEC / f"geceler_{feed}.parquet").exists() else pd.Series(dtype=float)

    def at(u: int):
        i = int(np.searchsorted(t, u))
        if i < len(t) and t[i] - u <= tol:
            return o[i], sp[i]
        return np.nan, np.nan

    rows = []
    for k in range(1, len(days) - 1):
        D, Dp, Dn = days[k - 1 + 1], days[k - 1], days[k + 1]
        p0 = dp.loc[Dp, "o960"]
        u18 = _u(Dp, 18, 0)
        ex = {"09:30": at(_u(D, 9, 30)), "16:00": at(_u(D, 16, 0)), "D1_16:00": at(_u(Dn, 16, 0))}
        for tn, (hh, mm) in TS.items():
            uT = _u(D, hh, mm)
            pT, sT = at(uT)
            i0, i1 = int(np.searchsorted(t, u18)), int(np.searchsorted(t, uT))
            if not np.isfinite(pT) or i1 - i0 < 3:
                continue
            p60, _ = at(uT - 3600)
            hi, lo = h[i0:i1].max(), l[i0:i1].min()
            r = {"d": D, "T": tn, "p0": p0, "pT": pT, "sT": sT, "twap": c[i0:i1].mean(), "hi": hi, "lo": lo, "p60": p60,
                 "S_prev": float(S.get(Dp, np.nan)), "nts1": (Dn - D).days}
            for en, (px, s) in ex.items():
                r[f"x{en}"], r[f"s{en}"] = px, s
            rows.append(r)
    df = pd.DataFrame(rows)
    df["era"] = np.where(df.d <= G.ESKI_END, "ESKI", "YENI")
    return df


def masks(x: pd.DataFrame, side: int = 1) -> dict:
    r = x.pT / x.p0 - 1
    tw = x.pT / x.twap - 1
    l60 = x.pT / x.p60 - 1
    pos = (x.pT - x.lo) / (x.hi - x.lo)
    rng = (x.hi - x.lo) / x.p0
    out = {}
    for th in THR["G1"]:
        out[("G1", th)] = (side * r) <= -th / 100
    for th in THR["G2"]:
        out[("G2", th)] = ((side * tw) <= -th / 100) & ((side * l60) < 0)
    for th in THR["G3"]:
        out[("G3", th)] = ((pos <= th) if side > 0 else (pos >= 1 - th)) & (rng >= 0.01)
    return {k: np.nan_to_num(v.values.astype(float)).astype(bool) for k, v in out.items()}


def nets(x: pd.DataFrame, en: str, side: int = 1) -> tuple[np.ndarray, np.ndarray]:
    fin = FIN * (x.nts1.values if en == "D1_16:00" else 0)
    px, s = x[f"x{en}"].values, x[f"s{en}"].values
    if side > 0:
        pin = x.pT.values + x.sT.values
        net = (px / pin - 1) * 1e4 - fin
    else:
        pin = x.pT.values
        net = -((px + s) / pin - 1) * 1e4 - fin
    extra = 0.5 * (x.sT.values + s) / pin * 1e4
    return net, net - extra


def cell(x: pd.DataFrame, m: np.ndarray, en: str, side: int = 1, keep: np.ndarray | None = None, n_boot: int = 3000) -> dict:
    net, n15 = nets(x, en, side)
    ok = np.isfinite(net) & (keep if keep is not None else True)
    a, b = ok & m, ok & ~m
    if a.sum() < 3 or b.sum() < 3:
        return {"n": int(a.sum())}
    d = x.d.astype(str).values
    diff = net[a].mean() - net[b].mean()
    se = np.sqrt(net[a].var(ddof=1) / a.sum() + net[b].var(ddof=1) / b.sum())
    return {"n": int(a.sum()), "tetik": round(float(net[a].mean()), 1), "taban": round(float(net[b].mean()), 1),
            "fark": round(float(diff), 1), "t": round(float(diff / se), 2), "s15": round(float(n15[a].mean()), 1),
            "isabet": round(float((net[a] > 0).mean()), 3), "en_kotu": round(float(net[a].min()), 1),
            "P": round(float(G.KS.diff_p(net[a], d[a], net[b], d[b], n=n_boot)), 4)}


def grid(X: pd.DataFrame, era: str | None, n_boot: int, rng: np.random.Generator | None = None) -> pd.DataFrame:
    rows = []
    for tn in TS:
        x = X[X["T"] == tn].reset_index(drop=True)
        sel = (x.era == era).values if era else np.ones(len(x), bool)
        for key, m in masks(x).items():
            mm = np.roll(m, int(rng.integers(1, 11) * rng.choice([-1, 1]))) if rng is not None else m
            for en in EXITS[tn]:
                rows.append({"G": key[0], "esik": key[1], "T": tn, "cikis": en, **cell(x, mm, en, keep=sel, n_boot=n_boot)})
    return pd.DataFrame(rows)


def passing(g: pd.DataFrame) -> pd.DataFrame:
    return g[(g.n >= N_MIN) & (g.tetik > 0) & (g.fark > 0) & (g.P >= 0.90)]


def kesif() -> None:
    RES.mkdir(exist_ok=True)
    X = table(G.ndx_bars(), 60, "DUKA")
    X.to_parquet(RES / "tablo_DUKA.parquet")
    g = grid(X, "ESKI", 3000)
    g.to_csv(RES / "kesif_izgara.csv", index=False)
    real = passing(g)
    pc = [int(len(passing(grid(X, "ESKI", 300, np.random.default_rng(700 + r))))) for r in range(N_PL)]
    frozen, per = [], {}
    for r in real.sort_values("t", ascending=False).to_dict("records"):
        if per.get(r["G"], 0) >= MAX_PER:
            continue
        frozen.append(r)
        per[r["G"]] = per.get(r["G"], 0) + 1
        if len(frozen) == MAX_FROZEN:
            break
    oz = {"hucre": len(g), "aday": len(real), "plasebo": sorted(pc), "plasebo_p95": float(np.percentile(pc, 95)),
          "sans_ustu": bool(len(real) > np.percentile(pc, 95)), "donmus": frozen}
    (RES / "kesif_ozet.json").write_text(json.dumps(oz, indent=1, ensure_ascii=False, default=str))
    print({k: oz[k] for k in ("hucre", "aday", "plasebo_p95", "sans_ustu")}, sorted(pc))
    print(g.sort_values("t", ascending=False).head(15).to_string(index=False))
    print("dondurulan:", [(f["G"], f["esik"], f["T"], f["cikis"]) for f in frozen])


def dogrula() -> None:
    frozen = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    X = pd.read_parquet(RES / "tablo_DUKA.parquet")
    F = {nm: table(b, st, nm) for nm, (b, st) in GR.feeds().items()}
    out = []
    for f in frozen:
        key, tn, en = (f["G"], f["esik"]), f["T"], f["cikis"]
        x = X[X["T"] == tn].reset_index(drop=True)
        m = masks(x)[key]
        y = cell(x, m, en, keep=(x.era == "YENI").values)
        tot = cell(x, m, en)
        ind = cell(x, m, en, keep=(x.S_prev == 0).values)
        fr = {}
        for nm, Xf in F.items():
            xf = Xf[Xf["T"] == tn].reset_index(drop=True)
            fr[nm] = cell(xf, masks(xf)[key], en)
        ok = {"1_yeni": bool(y.get("tetik", -1) > 0 and y.get("P", 0) >= P_YENI),
              "2_beslemeler": all(v.get("tetik", -1) > 0 and v.get("tetik", -1) > v.get("taban", 9e9) for v in fr.values()),
              "3_korkudan_bagimsiz": bool(ind.get("tetik", -1) > 0 and ind.get("fark", -1) > 0 and ind.get("P", 0) >= 0.90),
              "4_surtunme": bool(y.get("s15", -1) > 0 and tot.get("s15", -1) > 0), "5_hacim": bool(tot.get("n", 0) >= 150)}
        hk = "B" if all(ok.values()) else ("C+" if ok["1_yeni"] and ok["2_beslemeler"] else "X")
        out.append({"hucre": {"G": key[0], "esik": key[1], "T": tn, "cikis": en}, "ESKI": {k: f[k] for k in ("n", "tetik", "taban", "P")},
                    "YENI": y, "TUM": tot, "S_prev_0": ind, "beslemeler": fr, "olcut": ok, "hukum": hk})
        print(f"\n{key} {tn}→{en}: {hk} {ok}\n  YENİ {y}\n  TÜM {tot}\n  korku gecesi dışı {ind}")
        for nm, v in fr.items():
            print(f"  {nm} {v}")
    (RES / "dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def ayna() -> None:
    frozen = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    X = pd.read_parquet(RES / "tablo_DUKA.parquet")
    out = []
    for f in frozen:
        key, tn, en = (f["G"], f["esik"]), f["T"], f["cikis"]
        x = X[X["T"] == tn].reset_index(drop=True)
        m = masks(x, -1)[key]
        r = {"hucre": [*key, tn, en], "ESKI": cell(x, m, en, -1, (x.era == "ESKI").values), "YENI": cell(x, m, en, -1, (x.era == "YENI").values)}
        out.append(r)
        print(r)
    (RES / "ayna.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula, "ayna": ayna}[sys.argv[1]]()
