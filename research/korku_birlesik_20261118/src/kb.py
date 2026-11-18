"""kb.py — birleşik korku gecesi (skor, doz, felaket stopu), kesişimler, canlı portföy (PROTOCOL). python kb.py bolum1 | bolum2 | bolum3"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/vix_egri_20261118/src", "research/korku_gece_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import ve  # noqa: E402
import korku as K  # noqa: E402
G, GR, cc = ve.G, ve.GR, ve.cc
import rules  # noqa: E402

RES = ROOT / "research/korku_birlesik_20261118/results"
TZ = "America/New_York"
STOPS = (None, 0.02, 0.03, 0.04)


def nights_scored(d: pd.DataFrame, step: int) -> pd.DataFrame:
    """16:00 → ertesi 16:00 geceleri + tetikler + skor + stop sonuçları."""
    dp = G.day_prices(d, TZ, [570, 900, 960], step)
    days = [x for x in dp.index if x.weekday() < 5 and G.nyse_ok(x)]
    f = K.features(d, 960, step)
    wf = G.wick_ends(d, TZ, 7200, 0.50, step)
    t, lo, op = d.t.values, d.l.values, d.o.values
    rows = []
    for i, dd in enumerate(days[:-1]):
        r, nx = dp.loc[dd], dp.loc[days[i + 1]]
        oe, ox = r.get("o960"), nx.get("o960")
        if not (np.isfinite(oe) and np.isfinite(ox) and dd in f.index):
            continue
        ff = f.loc[dd]
        ksg = np.isfinite(r.o900) and oe < r.o900
        rng = (ff.hi - ff.lo) / ff.o930 if np.isfinite(ff.o930) else np.nan
        tin, tout = int(r.t960), int(nx.t960)
        trig = {"T_f": bool(G.tag(np.array([tin]), wf, 12 * 3600)[0] and ksg),
                "T_k1": bool(np.isfinite(ff.twap) and oe / ff.twap - 1 <= -0.005 and ksg),
                "T_k3": bool(np.isfinite(r.o900) and (oe / r.o900 - 1) * 100 <= -0.3),
                "T_k4": bool(np.isfinite(rng) and rng >= 0.02 and oe < ff.o930 and ksg)}
        pin = oe + r.s960
        nights = (days[i + 1] - dd).days
        fin = G.lib.FIN_BP_PER_DAY * nights
        i0, i1 = int(np.searchsorted(t, tin)), int(np.searchsorted(t, tout))
        seg = lo[i0:i1]
        res = {}
        for s in STOPS:
            if s is None or seg.size == 0:
                px = ox
            else:
                st = pin * (1 - s)
                h = np.flatnonzero(seg <= st)
                px = min(st, op[i0 + h[0]]) if h.size else ox
            res[f"bp_{'yok' if s is None else int(s * 100)}"] = (px / pin - 1) * 1e4 - fin
        rows.append({"d": dd, "t_in": tin, "t_out": tout, **trig, "S": sum(trig.values()), **res,
                     "s15_extra": 0.5 * (r.s960 + nx.s960) / pin * 1e4})
    df = pd.DataFrame(rows)
    df["era"] = np.where(df.d <= G.ESKI_END, "ESKI", "YENI")
    return df


def st(v: np.ndarray) -> dict:
    v = np.asarray(v, float)
    if len(v) < 3:
        return {"n": int(len(v))}
    return {"n": int(len(v)), "ort": round(float(v.mean()), 1), "sd": round(float(v.std()), 1), "sharpe_islem": round(float(v.mean() / v.std()), 3),
            "en_kotu": round(float(v.min()), 1), "isabet": round(float((v > 0).mean()), 3)}


def bolum1() -> None:
    RES.mkdir(exist_ok=True)
    feeds = {"DUKA": (G.ndx_bars(), 60), **GR.feeds()}
    out = {}
    for nm, (b, step) in feeds.items():
        df = nights_scored(b, step)
        df.to_parquet(RES / f"geceler_{nm}.parquet")
        u = df[df.S >= 1]
        r = {"U": {e: st(u[u.era == e].bp_yok) for e in ("ESKI", "YENI")} | {"TUM": st(u.bp_yok), "taban_S0": st(df[df.S == 0].bp_yok)}}
        r["doz"] = {e: {f"S{k}": st(df[(df.era == e) & (df.S == k if k < 3 else df.S >= 3)].bp_yok) for k in (1, 2, 3)} for e in ("ESKI", "YENI")}
        r["stop"] = {e: {c: st(u[u.era == e][c]) for c in ("bp_yok", "bp_2", "bp_3", "bp_4")} for e in ("ESKI", "YENI")}
        out[nm] = r
        print(f"\n== {nm} ==  U: {r['U']['TUM']}  | S=0 taban {r['U']['taban_S0'].get('ort')}")
        for e in ("ESKI", "YENI"):
            print(f"  {e} doz: " + "  ".join(f"{k} {v.get('ort')} (n {v.get('n')})" for k, v in r["doz"][e].items()))
            print(f"  {e} stop: " + "  ".join(f"{k} ort {v.get('ort')} sh {v.get('sharpe_islem')} kötü {v.get('en_kotu')}" for k, v in r["stop"][e].items()))
    d = out["DUKA"]
    mono = all(d["doz"][e]["S3"].get("ort", -1e9) > d["doz"][e]["S2"].get("ort", -1e9) > d["doz"][e]["S1"].get("ort", -1e9) for e in ("ESKI", "YENI"))
    s3gt1 = all(d["doz"][e]["S3"].get("ort", -1e9) > d["doz"][e]["S1"].get("ort", -1e9) for e in ("ESKI", "YENI"))
    stops_ok = [c for c in ("bp_2", "bp_3", "bp_4") if all(d["stop"][e][c]["ort"] > 0 and d["stop"][e][c]["sharpe_islem"] > d["stop"][e]["bp_yok"]["sharpe_islem"] for e in ("ESKI", "YENI"))]
    best = min(stops_ok, key=lambda c: min(d["stop"][e][c]["en_kotu"] * -1 for e in ("ESKI", "YENI"))) if stops_ok else "bp_yok"
    out["hukum"] = {"doz_tekduze": mono, "doz_S3>S1": s3gt1, "doz_sinif": "B" if mono else ("C+" if s3gt1 else "X"),
                    "stop_gecen": stops_ok, "onerilen_stop": best,
                    "beslemeler_U_arti": {k: out[k]["U"]["TUM"].get("ort", -1) > 0 for k in ("MT5", "EET30", "NQ")}}
    print("\nhüküm:", out["hukum"])
    (RES / "bolum1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def bolum2() -> None:
    df = pd.read_parquet(RES / "geceler_DUKA.parquet")
    u = df[df.S >= 1].reset_index(drop=True)
    days = list(df.d)
    vs = ve.lagged(days, ve.vix_signals()).set_index("d")
    vp = G.lib.vix_prev_map(days)
    m1 = G.lib.load_m1()
    D = G.lib.daily_table(m1)
    s = D[D.S.notna()].reset_index(drop=True)
    r2 = dict(zip(s.d, rules.rsi2(s.S.values)))
    months = pd.Series(days, index=pd.to_datetime(days)).groupby(pd.to_datetime(days).to_period("M"))
    last3 = set(x for _, g in months for x in list(g.values)[-3:])
    H = {"H1_ters_egri": u.d.map(lambda x: vs.r3.get(x, np.nan) >= 1.0).fillna(False).values,
         "H2_vix18": u.d.map(lambda x: vp.get(x, np.nan) >= 18.4).fillna(False).values,
         "H3_c3b": u.d.map(lambda x: r2.get(x, np.nan) < 10).fillna(False).values,
         "H4_cuma": np.array([x.weekday() == 4 for x in u.d]),
         "H5_ay_sonu": u.d.isin(last3).values}
    out = {}
    for k, m in H.items():
        a, b = u[m], u[~m]
        r = {"n": int(m.sum()), "ile": round(float(a.bp_yok.mean()), 1), "olmadan": round(float(b.bp_yok.mean()), 1),
             "P": round(G.KS.diff_p(a.bp_yok.values, a.d.astype(str).values, b.bp_yok.values, b.d.astype(str).values), 3)}
        for e in ("ESKI", "YENI"):
            ae, be = a[a.era == e], b[b.era == e]
            r[e] = {"n": int(len(ae)), "ile": round(float(ae.bp_yok.mean()), 1) if len(ae) else None, "olmadan": round(float(be.bp_yok.mean()), 1)}
        both = all(r[e]["ile"] is not None and r[e]["ile"] > r[e]["olmadan"] for e in ("ESKI", "YENI"))
        r["sinif"] = "B" if both and r["P"] >= 0.98 else ("C+" if both and r["P"] >= 0.90 else "X")
        out[k] = r
        print(k, r)
    (RES / "bolum2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def bolum3() -> None:
    hk = json.loads((RES / "bolum1.json").read_text())["hukum"]
    col = hk["onerilen_stop"]
    m1 = G.lib.load_m1()
    D = G.lib.daily_table(m1)
    vixp = G.lib.vix_prev_map(D.d.tolist())
    arms = {"C3b": G.lib.to_frame(rules.c3b(m1, D)), "ORBxVIX": G.lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0)),
            "KSG": G.lib.to_frame(rules.ksg(m1, D)), "CAPREV": G.lib.to_frame(rules.caprev(m1, D, vixp))}
    df = pd.read_parquet(RES / "geceler_DUKA.parquet")
    u = df[df.S >= 1]
    arms["U"] = pd.DataFrame({"d": u.d.values, "t_out": u.t_out.values, "net_bp": u[col].values})
    udays = set(u.d)
    allday = pd.to_datetime(sorted(set(D.d)))

    def daily(frames: dict) -> pd.DataFrame:
        cols = {}
        for k, f in frames.items():
            f = f.dropna(subset=["net_bp"])
            sc = 100.0 / f.net_bp.std()
            ex = pd.to_datetime(pd.to_datetime(f.t_out, unit="s", utc=True).dt.tz_convert(TZ).dt.date)
            cols[k] = (f.net_bp * sc).groupby(ex.values).sum().reindex(allday, fill_value=0.0)
        return pd.DataFrame(cols)

    def met(s: pd.Series) -> dict:
        cs = s.cumsum()
        return {"yillik_risk_birimi": round(float(s.mean() * 252), 1), "sharpe": round(float(s.mean() / s.std() * np.sqrt(252)), 2),
                "maxDD": round(float((cs - cs.cummax()).min()), 1)}

    base = {k: v for k, v in arms.items() if k != "U"}
    ksg_wo = arms["KSG"][~arms["KSG"].d.isin(udays)]
    with_u = {**{k: v for k, v in base.items() if k != "KSG"}, "KSG": ksg_wo, "U": arms["U"]}
    out = {}
    for nm, fr in (("canli_4_kol", base), ("canli_+_U", with_u)):
        P = daily(fr)
        tot = P.sum(1)
        out[nm] = {"TUM": met(tot), "ESKI": met(tot[tot.index <= pd.Timestamp(G.ESKI_END)]), "YENI": met(tot[tot.index > pd.Timestamp(G.ESKI_END)])}
        act = P.replace(0, np.nan)
        out[nm]["korelasyon_ortak_gun"] = act.corr(min_periods=10).round(2).to_dict()
        print(nm, {k: out[nm][k] for k in ("TUM", "ESKI", "YENI")})
    a, b = out["canli_4_kol"], out["canli_+_U"]
    ok = all(b[e]["sharpe"] > a[e]["sharpe"] for e in ("ESKI", "YENI")) and b["TUM"]["maxDD"] >= 1.2 * a["TUM"]["maxDD"]
    out["oneri"] = {"U_eklenmeli": bool(ok), "stop": col}
    print("korelasyon (canlı + U):", out["canli_+_U"]["korelasyon_ortak_gun"].get("U"))
    print("öneri:", out["oneri"])
    (RES / "bolum3.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"bolum1": bolum1, "bolum2": bolum2, "bolum3": bolum3}[sys.argv[1]]()
