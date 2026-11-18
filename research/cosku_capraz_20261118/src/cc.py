"""cc.py — A coşku gecesi (SAT) + B çapraz piyasa korkusu → NDX (PROTOCOL). Kullanım: python cc.py kesif | dogrula"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/korku_gece_20261118/src"))
import korku as K  # noqa: E402
import gece as G  # noqa: E402
import gece_run as GR  # noqa: E402

RES = ROOT / "research/cosku_capraz_20261118/results"
TZ = K.TZ
N_MIN, N_PL, MAX_FROZEN = 25, 20, 4
P_YENI = 1 - 0.10 / MAX_FROZEN


# ─────────── gece tabloları (uzun / kısa) ───────────

def night_table(d: pd.DataFrame, step: int, entry: int, exit_: int, side: int) -> pd.DataFrame:
    dp = G.day_prices(d, TZ, sorted({entry, exit_, 900, 570, entry - 60}), step)
    days = [x for x in dp.index if x.weekday() < 5 and G.nyse_ok(x)]
    rows = []
    for i, dd in enumerate(days[:-1]):
        r, nx = dp.loc[dd], dp.loc[days[i + 1]]
        oe, ox = r.get(f"o{entry}"), nx.get(f"o{exit_}")
        if not (np.isfinite(oe) and np.isfinite(ox)):
            continue
        se, sx = r[f"s{entry}"], nx[f"s{exit_}"]
        if side > 0:
            pin = oe + se
            net = (ox / pin - 1) * 1e4 - G.lib.FIN_BP_PER_DAY * (days[i + 1] - dd).days
        else:
            pin = oe
            net = -((ox + sx) / pin - 1) * 1e4
        rows.append({"d": dd, "t_in": int(r[f"t{entry}"]), "oe": oe, "o900": r.get("o900"), "om60": r.get(f"o{entry - 60}"),
                     "net_bp": net, "net_bp_s15": net - 0.5 * (se + sx) / pin * 1e4})
    df = pd.DataFrame(rows)
    df["era"] = np.where(df.d <= G.ESKI_END, "ESKI", "YENI")
    return df


def upper_wick_ends(d: pd.DataFrame, step: int) -> np.ndarray:
    x = G._local(d, TZ)
    key = x["loc"].values - x["loc"].values % 7200
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    en = np.r_[st[1:], len(key)] - 1
    o, c = x.o.values[st], x.c.values[en]
    h, l = np.maximum.reduceat(x.h.values, st), np.minimum.reduceat(x.l.values, st)
    bb, tt = np.minimum(o, c), np.maximum(o, c)
    uw, lw = (h - tt) / tt * 100, (bb - l) / bb * 100
    return np.sort(x.t.values[en][(uw >= 0.5) & (lw <= 0.5 * uw)] + step).astype(np.int64)


def cosku_tables(d: pd.DataFrame, step: int) -> dict:
    """(tetik, çıkış) → (gece tablosu, maske)."""
    out = {}
    ue = upper_wick_ends(d, step)
    for ex_n, ex in (("09:30", 570), ("16:00", 960)):
        nt = night_table(d, step, 960, ex, -1)
        f = K.features(d, 960, step).reindex(nt.d.values)
        pe = nt.oe.values
        up = (nt.oe.values / nt.o900.values - 1) > 0
        rng = (f.hi.values - f.lo.values) / f.o930.values
        pos = (pe - f.lo.values) / (f.hi.values - f.lo.values)
        for thr in (0.5, 1.0):
            out[(f"C1_{thr}", ex_n)] = (nt, ((pe / f.twap.values - 1) * 100 >= thr) & up)
        for thr in (0.80, 0.90):
            out[(f"C2_{thr}", ex_n)] = (nt, (pos >= thr) & (rng >= 0.015))
        for thr in (0.3, 0.6):
            out[(f"C3_{thr}", ex_n)] = (nt, (pe / nt.om60.values - 1) * 100 >= thr)
        nt15 = night_table(d, step, 930, ex, -1)
        up15 = (nt15.oe.values / nt15.o900.values - 1) > 0
        for wn, w in (("6h", 6 * 3600), ("12h", 12 * 3600)):
            out[(f"C4_{wn}", ex_n)] = (nt15, G.tag(nt15.t_in.values, ue, w) & up15)
    return {k: (nt, np.nan_to_num(np.asarray(m, float)).astype(bool)) for k, (nt, m) in out.items()}


# ─────────── çapraz piyasa ───────────

def ndx_k1_days(d: pd.DataFrame, step: int) -> set:
    nt = night_table(d, step, 960, 960, +1)
    f = K.features(d, 960, step).reindex(nt.d.values)
    m = ((nt.oe.values / f.twap.values - 1) <= -0.005) & ((nt.oe.values / nt.o900.values - 1) < 0)
    return set(nt.d.values[np.nan_to_num(m.astype(float)).astype(bool)])


def russell_days() -> set:
    import ksg_dogrulama as KD
    b = KD.mt5_m30("US2000")
    return ndx_k1_days(b, 1800)


def dax_triggers() -> pd.DataFrame:
    """DAX gün sonu korkusu: 17:30 Berlin, 09:00'dan beri TWAP'ın ≥%0,5 altı ∧ 16:30→17:30 aşağı. Döner: gün, UTC t."""
    src = ROOT / "research/fibo_altin_bolge_20261116/cache"
    raw = pd.read_parquet(src / "DAX_1m_raw.parquet", columns=["t"]).sort_values("t").drop_duplicates("t")
    z = np.load(src / "DAX_1m.npz")
    d = pd.DataFrame({"t": raw.t.values.astype(np.int64), "o": z["o"], "h": z["h"], "l": z["l"], "c": z["c"], "sp": z["spr"]})
    x = G._local(d, "Europe/Berlin")
    r = x[(x.mn >= 540) & (x.mn < 1050)].groupby("day").c.mean()
    dp = G.day_prices(d, "Europe/Berlin", [990, 1050], 60)
    dp = dp.join(r.rename("twap"), how="inner").dropna()
    trig = ((dp.o1050 / dp.twap - 1) <= -0.005) & (dp.o1050 < dp.o990)
    return pd.DataFrame({"d": dp.index, "t": dp.t1050.values.astype(np.int64), "trig": trig.values})


def dax_ndx_table(d: pd.DataFrame, step: int, dt: pd.DataFrame, exit_kind: str) -> tuple[pd.DataFrame, np.ndarray]:
    """NDX'i DAX kapanış anında AL; çıkış aynı NY günü 16:00 ya da ertesi işlem günü 16:00."""
    dp = G.day_prices(d, TZ, [960], step)
    t = d.t.values
    days = [x for x in dp.index if x.weekday() < 5 and G.nyse_ok(x)]
    pos = {x: i for i, x in enumerate(days)}
    rows, mk = [], []
    for r in dt.itertuples():
        if r.d not in pos:
            continue
        i = int(np.searchsorted(t, r.t))
        if i >= len(t) or t[i] - r.t > 600:
            continue
        j = pos[r.d] + (1 if exit_kind == "next" else 0)
        if j >= len(days):
            continue
        ox = dp.loc[days[j]].get("o960")
        if not np.isfinite(ox):
            continue
        pin = d.o.values[i] + d.sp.values[i]
        nights = (days[j] - r.d).days
        net = (ox / pin - 1) * 1e4 - G.lib.FIN_BP_PER_DAY * nights
        rows.append({"d": r.d, "t_in": int(t[i]), "net_bp": net,
                     "net_bp_s15": net - 0.5 * (d.sp.values[i] + dp.loc[days[j]].s960) / pin * 1e4})
        mk.append(bool(r.trig))
    df = pd.DataFrame(rows)
    df["era"] = np.where(df.d <= G.ESKI_END, "ESKI", "YENI")
    return df, np.array(mk)


def capraz_tables(d: pd.DataFrame, step: int, rus: set, dax: pd.DataFrame) -> dict:
    out = {}
    k1 = ndx_k1_days(d, step)
    for ex_n, ex in (("09:30", 570), ("16:00", 960)):
        nt = night_table(d, step, 960, ex, +1)
        keep = ~nt.d.isin(k1).values
        nt = nt[keep].reset_index(drop=True)
        out[("X1_russell", ex_n)] = (nt, nt.d.isin(rus).values)
    for ek in ("same", "next"):
        df, m = dax_ndx_table(d, step, dax, ek)
        out[("X2_dax", f"{'ayni' if ek == 'same' else 'ertesi'}_16:00")] = (df, m)
    return out


# ─────────── ızgara ───────────

def cell(nt, m, n_boot=4000):
    a, b = nt[m], nt[~m]
    if len(a) < 3 or len(b) < 3:
        return {"n": int(len(a))}
    diff = a.net_bp.mean() - b.net_bp.mean()
    se = np.sqrt(a.net_bp.var(ddof=1) / len(a) + b.net_bp.var(ddof=1) / len(b))
    return {"n": int(len(a)), "tetik": float(a.net_bp.mean()), "taban": float(b.net_bp.mean()), "fark": float(diff), "t": float(diff / se),
            "s15": float(a.net_bp_s15.mean()),
            "P": G.KS.diff_p(a.net_bp.values, a.d.astype(str).values, b.net_bp.values, b.d.astype(str).values, n=n_boot)}


def grid(T: dict, era, n_boot, shift=0):
    rows = []
    for (k, ex), (nt, m) in T.items():
        sel = (nt.era == era).values if era else np.ones(len(nt), bool)
        mm = np.roll(m, shift) if shift else m
        rows.append({"hucre": k, "cikis": ex, **cell(nt[sel].reset_index(drop=True), mm[sel], n_boot)})
    return pd.DataFrame(rows)


def passing(g):
    return g[(g.n >= N_MIN) & (g.tetik > 0) & (g.fark > 0) & (g.P >= 0.90)]


def all_tables(d, step, rus, dax):
    return {**cosku_tables(d, step), **capraz_tables(d, step, rus, dax)}


def kesif():
    RES.mkdir(exist_ok=True)
    d = G.ndx_bars()
    T = all_tables(d, 60, russell_days(), dax_triggers())
    gr = grid(T, "ESKI", 4000)
    gr.to_csv(RES / "kesif_izgara.csv", index=False)
    real = passing(gr)
    rng = np.random.default_rng(55)
    pc = [int(len(passing(grid(T, "ESKI", 300, int(rng.integers(1, 11) * rng.choice([-1, 1])))))) for _ in range(N_PL)]
    frozen = real.sort_values("t", ascending=False).head(MAX_FROZEN).to_dict("records")
    oz = {"hucre": len(gr), "aday": len(real), "plasebo": sorted(pc), "plasebo_p95": float(np.percentile(pc, 95)),
          "sans_ustu": bool(len(real) > np.percentile(pc, 95)), "donmus": frozen}
    (RES / "kesif_ozet.json").write_text(json.dumps(oz, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: oz[k] for k in ("hucre", "aday", "plasebo", "plasebo_p95", "sans_ustu")}, ensure_ascii=False))
    print(gr.sort_values("t", ascending=False)[["hucre", "cikis", "n", "tetik", "taban", "P", "t"]].round(3).to_string(index=False))


def dogrula():
    frozen = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    if not frozen:
        print("dondurulan yok")
        return
    rus, dax = russell_days(), dax_triggers()
    d = G.ndx_bars()
    T = all_tables(d, 60, rus, dax)
    FD = {nm: all_tables(b, st, rus, dax) for nm, (b, st) in GR.feeds().items()}
    out = []
    for c in frozen:
        key = (c["hucre"], c["cikis"])
        nt, m = T[key]
        y = cell(nt[nt.era == "YENI"].reset_index(drop=True), m[(nt.era == "YENI").values])
        tot = cell(nt, m)
        fr = {nm: cell(*F[key]) for nm, F in FD.items()}
        ok = {"1_yeni": bool(y.get("tetik", -1) > 0 and y.get("P", 0) >= P_YENI),
              "2_beslemeler": all(f.get("tetik", -1) > 0 and f.get("tetik", -1) > f.get("taban", 9e9) for f in fr.values()),
              "3_surtunme": bool(y.get("s15", -1) > 0), "4_hacim": bool(tot.get("n", 0) >= 150)}
        hk = "B" if all(ok.values()) else ("C+" if ok["1_yeni"] else "X")
        out.append({"hucre": key, "ESKI": {k: c[k] for k in ("n", "tetik", "taban", "P")}, "YENI": y, "TUM": tot, "beslemeler": fr, "olcut": ok, "hukum": hk})
        print(f"{key} | ESKİ {c['tetik']:+.1f} vs {c['taban']:+.1f} | YENİ {y.get('tetik', float('nan')):+.1f} vs {y.get('taban', float('nan')):+.1f} "
              f"(n {y.get('n')}, P {y.get('P', 0):.3f}) | " + " ".join(f"{nm} {f.get('tetik', float('nan')):+.1f}/{f.get('taban', float('nan')):+.1f}(n{f.get('n')})"
                                                                          for nm, f in fr.items()) + f" | n {tot.get('n')} | {hk}", flush=True)
    (RES / "dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula}[sys.argv[1]]()
