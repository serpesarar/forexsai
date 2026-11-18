"""vr.py — rejime bağlı vurkaç (PROTOCOL). python vr.py kesif | dogrula"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/fitil_zamanlama_20261118/src"))
import fz  # noqa: E402
lib, veri, NY = fz.lib, fz.veri, fz.NY
sys.path.insert(0, str(ROOT / "research/vw_dip_20261117/src"))
import kesif as KS  # noqa: E402  (cluster_p)

RES = ROOT / "research/vurkac_rejim_20261118/results"
GEOMS = {"0.5/1": (0.5, 1.0), "1/1": (1.0, 1.0), "1/2": (1.0, 2.0)}
ZTS = (2.0, 2.5)
REGS = ("R0", "R1", "R2", "R3")
HOLD_S = 1800
N_MIN, N_PL, MAX_FROZEN = 100, 10, 4
ESKI_END = pd.Timestamp("2021-10-31").date()


def signals(p: veri.PathBars) -> pd.DataFrame:
    b = fz.agg(p, 300)
    ny = pd.to_datetime(b.t, unit="s", utc=True).dt.tz_convert(NY)
    b["mn"] = (ny.dt.hour * 60 + ny.dt.minute).values
    b["d"] = ny.dt.date.values
    mu = b.close.rolling(12).mean()
    sd = b.close.rolling(12).std()
    b["z"] = (b.close - mu) / sd
    b["sig"] = sd
    hl = (b.high - b.low).rolling(12).mean()
    b["r3"] = hl >= 2 * hl.rolling(1560, min_periods=500).median().shift(1)
    # 5m kapanışı (mn + 5) 09:45–15:30 arası
    cl = b.mn + 5
    b = b[(cl >= 585) & (cl <= 930) & b.z.notna() & (b.sig > 0)].copy()
    days = sorted(set(b.d))
    vix = lib.vix_prev_map(days)
    D = lib.daily_table(lib.load_m1())
    rng = dict(zip(D.d, (D.high930 - D.low930) / D.open930))
    dl = sorted(rng)
    prev = {dl[i]: dl[i - 1] for i in range(1, len(dl))}
    b["R1"] = b.d.map(lambda x: vix.get(x, np.nan) >= 25).fillna(False)
    b["R2"] = b.d.map(lambda x: rng.get(prev.get(x), np.nan) >= 0.02).fillna(False)
    b["R3"] = b.r3.fillna(False)
    b["R0"] = True
    b["era"] = np.where(b.d <= ESKI_END, "ESKI", "YENI")
    return b.reset_index(drop=True)


def evaluate(p: veri.PathBars, t_sig: np.ndarray, side: int, sig: np.ndarray) -> dict:
    """Her giriş için 3 geometrinin R, R15, çıkış zamanı."""
    n = len(t_sig)
    out = {g: (np.full(n, np.nan), np.full(n, np.nan), np.zeros(n, np.int64)) for g in GEOMS}
    T, O, H, L, SP = p.t, p.o, p.h, p.l, p.spr
    for k in range(n):
        i = int(np.searchsorted(T, t_sig[k]))
        if i >= len(T) or T[i] - t_sig[k] > 600:
            continue
        j = int(np.searchsorted(T, T[i] + HOLD_S))
        if j <= i:
            continue
        spi = SP[i]
        if side > 0:
            ent = O[i] + spi
            hh, ll, oo = H[i:j], L[i:j], O[i:j]
        else:
            ent = O[i]
            sp = SP[i:j]
            hh, ll, oo = H[i:j] + sp, L[i:j] + sp, O[i:j] + sp
        tx = j if j < len(T) else len(T) - 1
        xpx = (O[tx] if side > 0 else O[tx] + SP[tx])
        for g, (a, bm) in GEOMS.items():
            tp, sl = ent + side * a * sig[k], ent - side * bm * sig[k]
            hs = np.flatnonzero(ll <= sl) if side > 0 else np.flatnonzero(hh >= sl)
            ht = np.flatnonzero(hh >= tp) if side > 0 else np.flatnonzero(ll <= tp)
            js = hs[0] if hs.size else 10 ** 9
            jt = ht[0] if ht.size else 10 ** 9
            if js <= jt and js < 10 ** 9:
                px, jx = (min(sl, oo[js]) if side > 0 else max(sl, oo[js])), i + js
            elif jt < 10 ** 9:
                px, jx = (max(tp, oo[jt]) if side > 0 else min(tp, oo[jt])), i + jt
            else:
                px, jx = xpx, tx
            risk = bm * sig[k]
            r = side * (px - ent) / risk
            extra = 0.5 * (spi + SP[min(jx, len(T) - 1)]) / risk
            out[g][0][k], out[g][1][k], out[g][2][k] = r, r - extra, int(T[min(jx, len(T) - 1)])
    return out


def single(t_in: np.ndarray, t_out: np.ndarray) -> np.ndarray:
    keep = np.zeros(len(t_in), bool)
    busy = -1
    for k in np.argsort(t_in, kind="stable"):
        if t_in[k] >= busy:
            keep[k] = True
            busy = t_out[k]
    return keep


def build(p: veri.PathBars, b: pd.DataFrame, rng_seed: int | None = None) -> dict:
    """(yön, zt) → sinyal tablosu + geometri sonuçları. rng_seed: plasebo (aynı gün rastgele 5m kapanışı)."""
    res = {}
    byday = b.groupby("d").tend.apply(np.array).to_dict()
    rng = np.random.default_rng(rng_seed) if rng_seed is not None else None
    for side, nm in ((+1, "AL"), (-1, "SAT")):
        for zt in ZTS:
            m = (b.z <= -zt) if side > 0 else (b.z >= zt)
            s = b[m].reset_index(drop=True)
            ts = s.tend.values.astype(np.int64)
            if rng is not None:
                ts = np.array([rng.choice(byday[x]) for x in s.d]).astype(np.int64)
            ev = evaluate(p, ts, side, s.sig.values)
            res[(nm, zt)] = (s, ev, ts)
    return res


def cells(res: dict, era: str | None) -> list[dict]:
    rows = []
    for (nm, zt), (s, ev, ts) in res.items():
        for g in GEOMS:
            r, r15, to = ev[g]
            for R in REGS:
                m = s[R].values & np.isfinite(r)
                if era:
                    m &= (s.era == era).values
                idx = np.flatnonzero(m)
                if idx.size < 3:
                    rows.append({"yon": nm, "zt": zt, "geom": g, "rejim": R, "n": int(idx.size)})
                    continue
                keep = idx[single(ts[idx], to[idx])]
                v = r[keep]
                rows.append({"yon": nm, "zt": zt, "geom": g, "rejim": R, "n": int(len(v)), "ort": float(v.mean()), "s15": float(r15[keep].mean()),
                             "isabet": float((v > 0).mean()), "t": float(v.mean() / (v.std() / np.sqrt(len(v)))),
                             "P": KS.cluster_p(v, s.d.values[keep].astype(str), 2000), "_v": v, "_d": s.d.values[keep]})
    return rows


def kesif() -> None:
    RES.mkdir(exist_ok=True)
    m = lib.load_m1()
    p = veri.PathBars(m.t, m.o, m.h, m.l, m.c, m.spr, 60, "DUKA")
    b = signals(p)
    print("5m sinyal satırı", len(b), flush=True)
    real = cells(build(p, b), "ESKI")
    pls = [cells(build(p, b, 500 + r), "ESKI") for r in range(N_PL)]
    out = []
    for k, c in enumerate(real):
        if c.get("n", 0) < 3:
            out.append({kk: v for kk, v in c.items() if not kk.startswith("_")})
            continue
        pv = np.concatenate([pl[k]["_v"] for pl in pls if "_v" in pl[k]])
        c["plasebo"] = float(pv.mean())
        c["P_plasebo"] = float(np.mean([c["_v"].mean() - np.random.default_rng(q).choice(pv, len(c["_v"])).mean() > 0 for q in range(1000)]))
        out.append({kk: v for kk, v in c.items() if not kk.startswith("_")})
    g = pd.DataFrame(out)
    g.to_csv(RES / "kesif_izgara.csv", index=False)
    ok = g[(g.n >= N_MIN) & (g.ort > 0) & (g.P >= 0.90) & (g.P_plasebo >= 0.90) & (g.s15 > 0)]
    frozen = ok.sort_values("t", ascending=False).head(MAX_FROZEN).to_dict("records")
    (RES / "kesif_ozet.json").write_text(json.dumps({"hucre": len(g), "aday": len(ok), "donmus": frozen}, indent=1, ensure_ascii=False, default=str))
    print(f"ESKİ: {len(g)} hücre, aday {len(ok)}")
    print(g.sort_values("t", ascending=False).head(16)[["yon", "zt", "geom", "rejim", "n", "ort", "plasebo", "isabet", "P", "P_plasebo", "s15"]].round(3).to_string(index=False))


def dogrula() -> None:
    frozen = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    if not frozen:
        print("dondurulan aday yok")
        return
    m = lib.load_m1()
    p = veri.PathBars(m.t, m.o, m.h, m.l, m.c, m.spr, 60, "DUKA")
    b = signals(p)
    real, pl = cells(build(p, b), "YENI"), [cells(build(p, b, 900 + r), "YENI") for r in range(5)]
    pn = fz.path_nq()
    bn = signals(pn)
    nq = cells(build(pn, bn), None)
    key = lambda c: (c["yon"], c["zt"], c["geom"], c["rejim"])  # noqa: E731
    R = {key(c): (c, k) for k, c in enumerate(real)}
    Q = {key(c): c for c in nq}
    out = []
    for f in frozen:
        c, k = R[key(f)]
        pv = np.concatenate([x[k]["_v"] for x in pl if "_v" in x[k]])
        pp = float(np.mean([c["_v"].mean() - np.random.default_rng(q).choice(pv, len(c["_v"])).mean() > 0 for q in range(1000)])) if "_v" in c else None
        q = Q[key(f)]
        ok = {"1_yeni": bool(c.get("ort", -1) > 0 and c.get("P", 0) >= 0.975 and (pp or 0) >= 0.90), "2_nq": bool(q.get("ort", -1) > 0),
              "3_surtunme": bool(c.get("s15", -1) > 0)}
        rec = {"hucre": key(f), "ESKI": {k_: f[k_] for k_ in ("n", "ort", "plasebo", "P")},
               "YENI": {k_: c.get(k_) for k_ in ("n", "ort", "s15", "isabet", "P")}, "YENI_plasebo_P": pp,
               "NQ": {k_: q.get(k_) for k_ in ("n", "ort", "isabet", "P")}, "olcut": ok, "hukum": "B" if all(ok.values()) else "X"}
        out.append(rec)
        print(rec["hucre"], "| ESKİ", round(f["ort"], 3), "| YENİ", rec["YENI"], "plasebo P", pp, "| NQ", rec["NQ"], "|", rec["hukum"])
    (RES / "dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula}[sys.argv[1]]()
