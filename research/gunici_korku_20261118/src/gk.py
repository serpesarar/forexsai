"""gk.py — gün içi korku zaman ekseni (PROTOCOL §1–2) + K1 taşıması (§3). Kullanım: python gk.py kesif | dogrula | tasima"""
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

RES = ROOT / "research/gunici_korku_20261118/results"
TZ = K.TZ
TS = {"10:30": 630, "12:00": 720, "14:00": 840}
EXITS = {"ayni_15:30": ("same", 930), "ertesi_16:00": ("next", 960)}
FEAR = {("K1", 0.5), ("K1", 1.0), ("K2", 0.20), ("K2", 0.10), ("K7", 0.75), ("K7", 1.5)}
N_MIN, N_PL, MAX_FROZEN = 25, 20, 4
P_YENI = 1 - 0.10 / MAX_FROZEN


def trades(d: pd.DataFrame, step: int) -> dict:
    dp = G.day_prices(d, TZ, sorted({570, 630, 720, 840, 930, 960}), step)
    days = [x for x in dp.index if x.weekday() < 5 and G.nyse_ok(x)]
    out = {}
    for tn, tm in TS.items():
        f = K.features(d, tm, step).reindex(days)
        for en, (kind, xm) in EXITS.items():
            rows = []
            for i, dd in enumerate(days[:-1] if kind == "next" else days):
                r = dp.loc[dd]
                xr = dp.loc[days[i + 1]] if kind == "next" else r
                pe, px = r.get(f"o{tm}"), xr.get(f"o{xm}")
                if not (np.isfinite(pe) and np.isfinite(px)):
                    continue
                pin = pe + r[f"s{tm}"]
                nights = (days[i + 1] - dd).days if kind == "next" else 0
                net = (px / pin - 1) * 1e4 - G.lib.FIN_BP_PER_DAY * nights
                extra = 0.5 * (r[f"s{tm}"] + xr[f"s{xm}"]) / pin * 1e4
                ff = f.loc[dd]
                rng = (ff.hi - ff.lo) / ff.o930 if np.isfinite(ff.o930) else np.nan
                rows.append({"d": dd, "t_in": int(r[f"t{tm}"]), "net_bp": net, "net_bp_s15": net - extra,
                             "k1": (pe / ff.twap - 1) * 100, "k2": (pe - ff.lo) / (ff.hi - ff.lo) if ff.hi > ff.lo else np.nan,
                             "rng": rng, "k7": (pe / ff.o930 - 1) * 100})
            df = pd.DataFrame(rows)
            df["era"] = np.where(df.d <= G.ESKI_END, "ESKI", "YENI")
            out[(tn, en)] = df
    return out


def mask(df: pd.DataFrame, k: str, thr: float) -> np.ndarray:
    if k == "K1":
        m = df.k1 <= -thr
    elif k == "K2":
        m = (df.k2 <= thr) & (df.rng >= 0.015)
    else:
        m = df.k7 <= -thr
    return m.fillna(False).values


def cell(df: pd.DataFrame, m: np.ndarray, n_boot: int = 4000) -> dict:
    a, b = df[m], df[~m]
    if len(a) < 3 or len(b) < 3:
        return {"n": int(len(a))}
    diff = a.net_bp.mean() - b.net_bp.mean()
    se = np.sqrt(a.net_bp.var(ddof=1) / len(a) + b.net_bp.var(ddof=1) / len(b))
    return {"n": int(len(a)), "tetik": float(a.net_bp.mean()), "taban": float(b.net_bp.mean()), "fark": float(diff), "t": float(diff / se),
            "s15": float(a.net_bp_s15.mean()), "P": G.KS.diff_p(a.net_bp.values, a.d.astype(str).values, b.net_bp.values, b.d.astype(str).values, n=n_boot)}


def grid(T: dict, era: str | None, n_boot: int, shift: int = 0) -> pd.DataFrame:
    rows = []
    for (tn, en), df0 in T.items():
        df = df0[df0.era == era].reset_index(drop=True) if era else df0
        for k, thr in sorted(FEAR):
            m = mask(df, k, thr)
            if shift:
                m = np.roll(m, shift)
            rows.append({"T": tn, "cikis": en, "K": k, "esik": thr, **cell(df, m, n_boot)})
    return pd.DataFrame(rows)


def passing(g):
    return g[(g.n >= N_MIN) & (g.tetik > 0) & (g.fark > 0) & (g.P >= 0.90)]


def kesif() -> None:
    RES.mkdir(exist_ok=True)
    T = trades(G.ndx_bars(), 60)
    gr = grid(T, "ESKI", 4000)
    gr.to_csv(RES / "kesif_izgara.csv", index=False)
    real = passing(gr)
    rng = np.random.default_rng(77)
    pc = [int(len(passing(grid(T, "ESKI", 300, int(rng.integers(1, 11) * rng.choice([-1, 1])))))) for _ in range(N_PL)]
    frozen = real.sort_values("t", ascending=False).head(MAX_FROZEN).to_dict("records")
    oz = {"hucre": len(gr), "aday": len(real), "plasebo": sorted(pc), "plasebo_p95": float(np.percentile(pc, 95)),
          "sans_ustu": bool(len(real) > np.percentile(pc, 95)), "donmus": frozen}
    (RES / "kesif_ozet.json").write_text(json.dumps(oz, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: oz[k] for k in ("hucre", "aday", "plasebo", "plasebo_p95", "sans_ustu")}, ensure_ascii=False))
    print(gr.sort_values("t", ascending=False).head(10)[["T", "cikis", "K", "esik", "n", "tetik", "taban", "P", "t"]].round(3).to_string(index=False))


def dogrula() -> None:
    frozen = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    if not frozen:
        print("dondurulan yok")
        return
    T = trades(G.ndx_bars(), 60)
    FD = {nm: trades(b, st) for nm, (b, st) in GR.feeds().items()}
    # akşam K1 günleri (artımsallık)
    d = G.ndx_bars()
    dp = G.day_prices(d, TZ, [900, 960], 60)
    f16 = K.features(d, 960, 60)
    ev = set(dd for dd in dp.index if dd in f16.index and np.isfinite(dp.loc[dd, "o960"]) and np.isfinite(dp.loc[dd, "o900"])
             and dp.loc[dd, "o960"] / f16.loc[dd, "twap"] - 1 <= -0.005 and dp.loc[dd, "o960"] < dp.loc[dd, "o900"])
    out = []
    for c in frozen:
        key = (c["T"], c["cikis"])
        df = T[key]
        m = mask(df, c["K"], c["esik"])
        y = cell(df[df.era == "YENI"].reset_index(drop=True), m[(df.era == "YENI").values])
        tot = cell(df, m)
        fr = {nm: cell(F[key], mask(F[key], c["K"], c["esik"])) for nm, F in FD.items()}
        ort = float(np.mean([dd in ev for dd in df.d[m]]))
        noev = ~df.d.isin(ev).values
        inc = cell(df[noev].reset_index(drop=True), m[noev])
        ok = {"1_yeni": bool(y.get("tetik", -1) > 0 and y.get("P", 0) >= P_YENI),
              "2_beslemeler": all(f.get("tetik", -1) > 0 and f.get("tetik", -1) > f.get("taban", 9e9) for f in fr.values()),
              "3_surtunme": bool(y.get("s15", -1) > 0), "4_hacim": bool(tot.get("n", 0) >= 150)}
        hk = "B" if all(ok.values()) else ("C+" if ok["1_yeni"] else "X")
        out.append({"hucre": {k: c[k] for k in ("T", "cikis", "K", "esik")}, "YENI": y, "TUM": tot, "beslemeler": fr,
                    "aksam_K1_ortusme": round(ort, 3), "aksam_K1_disi": inc, "olcut": ok, "hukum": hk})
        print(f"{c['T']} {c['cikis']} {c['K']} {c['esik']} | ESKİ {c['tetik']:+.1f} vs {c['taban']:+.1f} | YENİ {y.get('tetik', float('nan')):+.1f} vs "
              f"{y.get('taban', float('nan')):+.1f} (n {y.get('n')}, P {y.get('P', 0):.3f}) | " + " ".join(
                  f"{nm} {f.get('tetik', float('nan')):+.1f}/{f.get('taban', float('nan')):+.1f}" for nm, f in fr.items())
              + f" | akşam-K1 örtüşme {ort:.2f}, dışında {inc.get('tetik', float('nan')):+.1f} vs {inc.get('taban', float('nan')):+.1f} | n {tot.get('n')} | {hk}", flush=True)
    (RES / "dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def tasima() -> None:
    import ksg_dogrulama as KD
    res = {}
    for sym, since in (("US30", None), ("US2000", None), ("US500", "2021-01-01"), ("XAUUSD", None)):
        b = KD.mt5_m30(sym, since)
        if sym == "XAUUSD":
            b = b.assign(sp=b.sp / 10)                              # XAU point 0,01
        dp = G.day_prices(b, TZ, [570, 900, 960], 1800)
        nt = G.nights(dp, 960, 960, G.KSG_REF, G.nyse_ok)
        f = K.features(b, 960, 1800).reindex(nt.d.values)
        m = ((dp.reindex(nt.d.values).o960.values / f.twap.values - 1) <= -0.005) & (nt.ksg_ret.values < 0)
        m = np.nan_to_num(m.astype(float)).astype(bool)
        a, bb = nt[m], nt[~m]
        res[sym] = {"n": int(len(a)), "tetik": round(float(a.net_bp.mean()), 1), "taban": round(float(bb.net_bp.mean()), 1),
                    "P": round(G.KS.diff_p(a.net_bp.values, a.d.astype(str).values, bb.net_bp.values, bb.d.astype(str).values), 3),
                    "ESKI": round(float(a[a.era == "ESKI"].net_bp.mean()), 1), "YENI": round(float(a[a.era == "YENI"].net_bp.mean()), 1)}
        print(sym, res[sym], flush=True)
    (RES / "tasima.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula, "tasima": tasima}[sys.argv[1]]()
