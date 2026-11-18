"""gece_run.py — kesif (ESKİ seçim + ızgara plasebosu) · dogrula (YENİ + MT5/EET30/NQ) · dax (G7)."""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import gece as G

RES = G.ROOT / "research/fitil_gece_20261118/results"
N_MIN, P_MIN, N_PL, MAX_FROZEN = 25, 0.90, 20, 5
REF = {"tf": "1h", "thr": 0.50, "w": "6h", "ksg": True, "entry": "16:00", "exit": "09:30"}


def build(d: pd.DataFrame, tz: str, step: int) -> dict:
    mins = sorted(set(list(G.ENTRIES.values()) + list(G.EXITS.values()) + [G.KSG_REF]))
    dp = G.day_prices(d, tz, mins, step)
    return {(en, ex): G.nights(dp, G.ENTRIES[en], G.EXITS[ex], G.KSG_REF, G.nyse_ok) for en in G.ENTRIES for ex in G.EXITS}


def cell(df: pd.DataFrame, ends: np.ndarray, w: int, ksg: bool, n_boot: int = 4000) -> dict:
    m_k = (df.ksg_ret < 0).values if ksg else np.ones(len(df), bool)
    tg = G.tag(df.t_in.values, ends, w)
    a, b = df[tg & m_k], df[~tg & m_k]
    if len(a) < 3 or len(b) < 3:
        return {"n": int(len(a))}
    diff = a.net_bp.mean() - b.net_bp.mean()
    se = np.sqrt(a.net_bp.var(ddof=1) / len(a) + b.net_bp.var(ddof=1) / len(b))
    return {"n": int(len(a)), "n_taban": int(len(b)), "fitil": float(a.net_bp.mean()), "taban": float(b.net_bp.mean()),
            "fark": float(diff), "t": float(diff / se) if se > 0 else np.nan, "s15": float(a.net_bp_s15.mean()),
            "P": KS.diff_p(a.net_bp.values, a.d.astype(str).values, b.net_bp.values, b.d.astype(str).values, n=n_boot),
            "yil_basi": float(len(a) / max(1e-9, (a.d.max() - a.d.min()).days / 365.25)) if len(a) > 1 else None,
            "yil": {int(y): round(float(g.net_bp.mean()), 1) for y, g in a.groupby(pd.to_datetime(a.d).dt.year)}}


KS = G.KS


def grid(nts: dict, ends: dict, era: str | None, n_boot: int) -> pd.DataFrame:
    rows = []
    for (en, ex), df0 in nts.items():
        df = df0[df0.era == era] if era else df0
        for (tfn, thr), e in ends.items():
            for wn, ws in G.WS.items():
                for ksg in (True, False):
                    r = cell(df, e, ws, ksg, n_boot)
                    rows.append({"tf": tfn, "thr": thr, "w": wn, "ksg": ksg, "entry": en, "exit": ex, **r})
    return pd.DataFrame(rows)


def passing(g: pd.DataFrame) -> pd.DataFrame:
    return g[(g.n >= N_MIN) & (g.fitil > 0) & (g.fark > 0) & (g.P >= P_MIN)]


def kesif() -> None:
    RES.mkdir(exist_ok=True)
    d = G.ndx_bars()
    nts = build(d, "America/New_York", 60)
    ends = G.all_ends(d, "America/New_York", 60)
    gr = grid(nts, ends, "ESKI", 4000)
    gr.drop(columns=["yil"]).to_csv(RES / "kesif_izgara.csv", index=False)
    real = passing(gr)
    print(f"ESKİ: {len(gr)} hücre, aday {len(real)}", flush=True)
    ref = gr[(gr.tf == "1h") & (gr.thr == 0.5) & (gr.w == "6h") & gr.ksg & (gr.entry == "16:00") & (gr.exit == "09:30")].iloc[0]
    print("referans (fitilli KSG) ESKİ:", {k: ref[k] for k in ("n", "fitil", "taban", "P")}, flush=True)
    pc = []
    for r in range(N_PL):
        ep = G.all_ends(d, "America/New_York", 60, rng=np.random.default_rng(900 + r))
        pc.append(int(len(passing(grid(nts, ep, "ESKI", 300)))))
        print(f"  plasebo {r}: {pc[-1]}", flush=True)
    frozen = real.sort_values("t", ascending=False).head(MAX_FROZEN)
    oz = {"hucre": len(gr), "aday": len(real), "plasebo": pc, "plasebo_p95": float(np.percentile(pc, 95)),
          "sans_ustu": bool(len(real) > np.percentile(pc, 95)),
          "donmus": frozen.drop(columns=["yil"]).to_dict("records"), "aday_listesi": real.drop(columns=["yil"]).sort_values("t", ascending=False).head(25).to_dict("records")}
    (RES / "kesif_ozet.json").write_text(json.dumps(oz, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: oz[k] for k in ("hucre", "aday", "plasebo_p95", "sans_ustu")}, ensure_ascii=False))
    for c in oz["donmus"]:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in c.items()})


def feeds() -> dict:
    import ksg_dogrulama as KD
    import ksg_ek2 as E
    out = {"MT5": (KD.mt5_m30("NAS100"), 1800)}
    for nm in ("EET30", "NQ"):
        out[nm] = E.bars(nm)
    return out


def dogrula() -> None:
    oz = json.loads((RES / "kesif_ozet.json").read_text())
    cells = oz["donmus"] + [dict(REF, ref=True)]
    d = G.ndx_bars()
    nts = build(d, "America/New_York", 60)
    ends = G.all_ends(d, "America/New_York", 60)
    fd = {nm: (build(b, "America/New_York", st), G.all_ends(b, "America/New_York", st)) for nm, (b, st) in feeds().items()}
    out = []
    for c in cells:
        key = (c["entry"], c["exit"])
        e = ends[(c["tf"], c["thr"])]
        y = cell(nts[key][nts[key].era == "YENI"], e, G.WS[c["w"]], c["ksg"])
        tot = cell(nts[key], e, G.WS[c["w"]], c["ksg"])
        fr = {nm: cell(fnts[key], fends[(c["tf"], c["thr"])], G.WS[c["w"]], c["ksg"]) for nm, (fnts, fends) in fd.items()}
        ok = {"1_yeni": bool(y.get("fitil", -1) > 0 and y.get("P", 0) >= 0.98),
              "2_beslemeler": all(f.get("fitil", -1) > 0 and f.get("fitil", -1) > f.get("taban", 9e9) for f in fr.values()),
              "3_surtunme": bool(y.get("s15", -1) > 0),
              "4_hacim": bool(tot.get("n", 0) >= 150)}
        nf = sum(f.get("fitil", -1) > 0 and f.get("fitil", -1) > f.get("taban", 9e9) for f in fr.values())
        hk = "B" if all(ok.values()) else ("C+" if ok["1_yeni"] and nf >= 2 else "X")
        rec = {"hucre": {k: c[k] for k in ("tf", "thr", "w", "ksg", "entry", "exit")}, "referans": bool(c.get("ref")),
               "ESKI": {k: c.get(k) for k in ("n", "fitil", "taban", "P")}, "YENI": y, "TUM": tot, "beslemeler": fr, "olcut": ok, "hukum": hk}
        out.append(rec)
        print(f"{'REF ' if c.get('ref') else ''}{c['tf']} %{c['thr']} W{c['w']} KSG={c['ksg']} {c['entry']}→{c['exit']} | YENİ "
              f"{y.get('fitil', float('nan')):+.1f} vs {y.get('taban', float('nan')):+.1f} (n {y.get('n')}, P {y.get('P', 0):.3f}) | "
              + " ".join(f"{nm} {f.get('fitil', float('nan')):+.1f}/{f.get('taban', float('nan')):+.1f}(n{f.get('n')})" for nm, f in fr.items())
              + f" | toplam n {tot.get('n')} yılda {tot.get('yil_basi') or 0:.0f} | {hk}", flush=True)
    (RES / "dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def dax() -> None:
    src = G.ROOT / "research/fibo_altin_bolge_20261116/cache"
    raw = pd.read_parquet(src / "DAX_1m_raw.parquet", columns=["t"]).sort_values("t").drop_duplicates("t")
    z = np.load(src / "DAX_1m.npz")
    d = pd.DataFrame({"t": raw.t.values.astype(np.int64), "o": z["o"], "h": z["h"], "l": z["l"], "c": z["c"], "sp": z["spr"]})
    tz = "Europe/Berlin"
    dp = G.day_prices(d, tz, [990, 1050, 540], 60)
    ok_day = set(dp.index[dp["o540"].notna()])
    nt = G.nights(dp, 1050, 540, 990, lambda x: x in ok_day)
    e = G.wick_ends(d, tz, 3600, 0.50, 60)
    res = {"TUM": cell(nt, e, 6 * 3600, True), "ESKI": cell(nt[nt.era == "ESKI"], e, 6 * 3600, True),
           "YENI": cell(nt[nt.era == "YENI"], e, 6 * 3600, True)}
    ok = all(res[x].get("fitil", -1) > 0 and res[x].get("fark", -1) > 0 for x in ("ESKI", "YENI")) and res["TUM"].get("P", 0) >= 0.90
    res["gecti"] = bool(ok)
    for k in ("TUM", "ESKI", "YENI"):
        r = res[k]
        print(f"DAX {k}: fitilli {r.get('fitil', float('nan')):+.1f} (n {r.get('n')}) vs taban {r.get('taban', float('nan')):+.1f} P {r.get('P', 0):.3f}")
    print("G7 DAX", "GEÇTİ" if ok else "geçmedi")
    (RES / "dax_g7.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula, "dax": dax}[sys.argv[1]]()
