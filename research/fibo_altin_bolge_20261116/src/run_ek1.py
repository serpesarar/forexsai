"""run_ek1.py — EK-1: A dondurulmuş adaylar (NDX ölçütleri + bağımsız broker), B VIX rejimi, C günlük çok endeks."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import fblib as F

CANDS = {
    "C1": dict(tf="5m", pattern="none", zone="sig382", smin=6.0, spmin=0.0, sl="L", tp="x1618", hold=300),
    "C2": dict(tf="15m", pattern="engf", zone="derin", smin=3.0, spmin=0.0, sl="L", tp="x1272", hold=300),
    "C3": dict(tf="15m", pattern="eng", zone="altin", smin=3.0, spmin=0.0, sl="L", tp="2R", hold=100),
}
PRIM = dict(pattern="eng", zone="altin", smin=4.0, spmin=0.5, sl="L", tp="H", hold=100)
YON_MT5 = F.ROOT / "research/yon_lab_20261114/data/mt5"
IDX_DIR = F.ROOT / "research/geri_cekilme_20261106/data"
QS_DIR = F.ROOT / "research/qs03_akis_takvim_20261111/data"
KOR_IDX = ["AEX", "AXJO", "BSESN", "BVSP", "DJI", "FCHI", "GSPTSE", "IBEX", "JKSE", "KS11", "MXX", "RUT", "SSMI",
           "TWII", "GDAXI"]
EXTRA_IDX = ["N225", "FTSE", "STOXX50E"]
DAILY_COST = 0.0003


def run(bars, p, pattern, zone, smin, spmin, sl, tp, hold, side=1, ny_only=True):
    c = F.detect(bars, side)
    tr = F.resolve(F.setup_trades(F.signals(c, pattern, zone, smin, spmin), bars, p, sl, tp, hold, zone), p)
    return tr[tr.session == "NY"] if ny_only and len(tr) else tr


def diff_p(a: pd.DataFrame, b: pd.DataFrame, B: int = 2000, seed: int = 5) -> float:
    if len(a) < 5 or len(b) < 5:
        return np.nan
    rng = np.random.default_rng(seed)

    def bs(df):
        s = df.groupby("date").R.agg(["sum", "count"])
        sm, ct = s["sum"].values, s["count"].values
        ix = rng.integers(0, len(sm), (B, len(sm)))
        return sm[ix].sum(1) / ct[ix].sum(1)
    return float((bs(a) - bs(b) > 0).mean())


def full_criteria(tr, pl) -> dict:
    tk = tr[tr.period != "KESIF"]
    plk = pl[pl.period != "KESIF"] if len(pl) else pl
    out = {"TUM": F.summarize(tr, boot=True)}
    for per in ["KESIF", "TEST", "KOR"]:
        out[per] = F.summarize(tr[tr.period == per], boot=True)
    out["TK"] = F.summarize(tk, boot=True)
    out["TK_spread15"] = F.summarize(tk, "R15")
    out["TK_tek_poz"] = F.summarize(F.single_position(tk), boot=True)
    out["TK_top5_haric"] = F.summarize(tk.drop(tk.R.nlargest(5).index)) if len(tk) > 5 else {}
    out["TK_plasebo"] = F.summarize(plk)
    out["TK_fark"] = round(float(tk.R.mean() - plk.R.mean()), 4) if len(plk) else None
    out["TK_fark_P"] = diff_p(tk, plk) if len(plk) else None
    for k in ["hour", "dow"]:
        out[f"kirilim_{k}"] = {str(v): F.summarize(g) for v, g in tr.groupby(k)}
    out["kirilim_yil"] = {str(v): F.summarize(g).get("ortR") for v, g in tr.groupby("year")}
    return out


# ───────────────────────── A ─────────────────────────

def part_a(p) -> dict:
    res = {}
    bars_cache = {}
    for code, c in CANDS.items():
        m_, a_ = F.TFS_NDX[c["tf"]]
        bars = bars_cache.setdefault(c["tf"], F.build_bars(p, m_, a_, c["tf"]))
        kw = {k: v for k, v in c.items() if k != "tf"}
        tr = run(bars, p, **kw)
        pl = F.placebo(tr, bars, p, c["hold"], draws=5)
        pl = pl[pl.session == "NY"] if len(pl) else pl
        res[code] = {"NDX": full_criteria(tr, pl), "bagimsiz": {}}
        btf = "M5" if c["tf"] == "5m" else "M15"
        pooled = []
        for sym in ["GER40", "XAUUSD", "SpotCrude", "US500", "NAS100"]:
            tf_use = btf
            if sym == "US500":
                path = F.MT5_DIR / f"US500_{btf}.csv.gz"
                if btf == "M5":
                    bp = _load(YON_MT5 / "US500_M5.csv.gz", sym)
                else:
                    tf_use = "M30"
                    bp = F.load_broker(sym, "M30")
            else:
                bp = F.load_broker(sym, tf_use)
            bb = F.build_bars(bp, 1, 0, tf_use)
            hold = c["hold"] if tf_use != "M30" else c["hold"] // 2
            trb = run(bb, bp, **{**kw, "hold": hold})
            plb = F.placebo(trb, bb, bp, hold, draws=5) if len(trb) else trb
            plb = plb[plb.session == "NY"] if len(plb) else plb
            allb = run(bb, bp, **{**kw, "hold": hold}, ny_only=False)
            d0 = pd.to_datetime(bp.local[0], unit="s").date()
            res[code]["bagimsiz"][sym] = {"tf": tf_use, "basla": str(d0), **F.summarize(trb, boot=True),
                                         "plasebo": F.summarize(plb).get("ortR"),
                                         "fark_P": diff_p(trb, plb) if len(plb) else None,
                                         "tum_seanslar": F.summarize(allb).get("ortR"),
                                         "tum_seanslar_n": len(allb)}
            if sym != "NAS100" and len(trb):
                pooled.append(trb.assign(sym=sym))
        if pooled:
            pdf = pd.concat(pooled)
            pdf = pdf.assign(date=pdf.sym + "|" + pdf.date.astype(str))
            res[code]["bagimsiz_havuz"] = F.summarize(pdf, boot=True)
            res[code]["bagimsiz_arti_sayi"] = int(sum(1 for s, v in res[code]["bagimsiz"].items()
                                                      if s != "NAS100" and v.get("ortR", -1) > 0))
        print(code, res[code]["NDX"]["TK"], res[code].get("bagimsiz_havuz"), flush=True)
    return res


def _load(path: Path, sym: str) -> F.Path1:
    df = pd.read_csv(path).sort_values("t").drop_duplicates("t")
    local = df.t.values.astype(np.int64) - F.SERVER_OFFSET_S
    return F.make_path(df.o.values, df.h.values, df.l.values, df.c.values, np.full(len(df), F.BROKER_SPREAD[sym]),
                       local)


# ───────────────────────── B ─────────────────────────

def part_b(p) -> dict:
    mac = pd.read_parquet(F.ROOT / "research/nom_20261113/data/macro/macro_daily.parquet")
    vd = pd.to_datetime(mac.date).values.astype("datetime64[D]")
    vv = mac.VIX_close.values
    ok = ~np.isnan(vv)
    vd, vv = vd[ok], vv[ok]

    def prior_vix(dates):
        i = np.searchsorted(vd, dates.astype("datetime64[D]"), side="left") - 1
        return np.where(i >= 0, vv[np.maximum(i, 0)], np.nan)

    res = {}
    cache = {}
    cells = [(f"{tf}|{'UZUN' if s > 0 else 'KISA'}", tf, s, PRIM, False) for tf in F.TFS_NDX for s in (1, -1)]
    cells += [(code, c["tf"], 1, {k: v for k, v in c.items() if k != "tf"}, True) for code, c in CANDS.items()]
    for lab, tf, side, kw, ny in cells:
        m_, a_ = F.TFS_NDX[tf]
        bars = cache.setdefault(tf, F.build_bars(p, m_, a_, tf))
        tr = run(bars, p, **kw, side=side, ny_only=ny)
        if tr.empty:
            continue
        pl = F.placebo(tr, bars, p, kw["hold"], draws=5)
        tr = tr.assign(vix=prior_vix(tr.date.values))
        pl = pl.assign(vix=prior_vix(pl.date.values))
        out = {}
        for reg, f in [("VIX>=18.4", lambda x: x.vix >= 18.4), ("VIX<18.4", lambda x: x.vix < 18.4)]:
            g, gp = tr[f(tr)], pl[f(pl)]
            out[reg] = {per: F.summarize(g[g.period == per]).get("ortR") for per in ["KESIF", "TEST", "KOR"]}
            out[reg]["n"] = len(g)
            out[reg]["TUM"] = F.summarize(g, boot=True)
            out[reg]["plasebo"] = F.summarize(gp).get("ortR")
            out[reg]["fark_P"] = diff_p(g, gp)
        res[lab] = out
        print("B", lab, out["VIX>=18.4"]["TUM"].get("ortR"), out["VIX<18.4"]["TUM"].get("ortR"), flush=True)
    return res


# ───────────────────────── C ─────────────────────────

def load_daily(name: str) -> F.Path1 | None:
    f = IDX_DIR / f"{name}.csv"
    if f.exists():
        df = pd.read_csv(f)
        d = pd.to_datetime(df.Date.str[:10])
    else:
        q = QS_DIR / f"{name}.parquet"
        if not q.exists():
            return None
        df = pd.read_parquet(q).reset_index()
        d = pd.to_datetime(df.iloc[:, 0]).dt.tz_localize(None).dt.normalize()
    df = df.assign(d=d.values)
    df = df[(df.d >= "1990-01-01") & (df.Open > 0) & (df.High >= df.Low) & ~((df.High == df.Low))]
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).drop_duplicates("d").sort_values("d")
    local = df.d.values.astype("datetime64[s]").astype(np.int64) + 10 * 3600
    o, h, l, c = df.Open.values, df.High.values, df.Low.values, df.Close.values
    h = np.maximum.reduce([h, o, c])
    l = np.minimum.reduce([l, o, c])
    return F.make_path(o, h, l, c, DAILY_COST * o, local)


def part_c() -> dict:
    res = {}
    rows = []
    for name in ["IXIC", "GSPC"] + KOR_IDX + EXTRA_IDX:
        p = load_daily(name)
        if p is None or p.n < 500:
            continue
        bars = F.build_bars(p, 1, 0, "1d")
        for side in (1, -1):
            for hold in (20, 60):
                tr = run(bars, p, **{**PRIM, "hold": hold}, side=side, ny_only=False)
                if tr.empty:
                    continue
                pl = F.placebo(tr, bars, p, hold, draws=5)
                if name in ("IXIC", "GSPC"):
                    per = np.where(tr.date.values <= np.datetime64("2009-12-31"), "KESIF", "TEST")
                    perp = np.where(pl.date.values <= np.datetime64("2009-12-31"), "KESIF", "TEST")
                else:
                    per = np.where(np.isin(name, EXTRA_IDX), "EK", "KOR")
                    per = np.full(len(tr), per)
                    perp = np.full(len(pl), per[0] if len(per) else "KOR")
                tr = tr.assign(period=per, idx=name)
                pl = pl.assign(period=perp, idx=name)
                rows.append((name, side, hold, tr, pl))
    for side in (1, -1):
        for hold in (20, 60):
            key = f"{'UZUN' if side > 0 else 'KISA'}|{hold}g"
            sel = [(n, t, pp) for n, s, h, t, pp in rows if s == side and h == hold]
            out = {"endeks": {}}
            for n, t, pp in sel:
                out["endeks"][n] = {"n": len(t), "ortR": F.summarize(t).get("ortR"), "plasebo": F.summarize(pp).get("ortR")}
            us = pd.concat([t for n, t, _ in sel if n in ("IXIC", "GSPC")])
            usp = pd.concat([pp for n, _, pp in sel if n in ("IXIC", "GSPC")])
            for per in ["KESIF", "TEST"]:
                a = us[us.period == per].assign(date=lambda x: x.idx + x.date.astype(str))
                b = usp[usp.period == per].assign(date=lambda x: x.idx + x.date.astype(str))
                out[per] = {**F.summarize(a, boot=True), "plasebo": F.summarize(b).get("ortR"), "fark_P": diff_p(a, b)}
            kor = pd.concat([t for n, t, _ in sel if n in KOR_IDX]).assign(date=lambda x: x.idx + x.date.astype(str))
            korp = pd.concat([pp for n, _, pp in sel if n in KOR_IDX]).assign(date=lambda x: x.idx + x.date.astype(str))
            out["KOR"] = {**F.summarize(kor, boot=True), "plasebo": F.summarize(korp).get("ortR"),
                          "fark_P": diff_p(kor, korp),
                          "arti_endeks": int(sum(1 for n in KOR_IDX if out["endeks"].get(n, {}).get("ortR", -1) > 0)),
                          "endeks_sayi": int(sum(1 for n in KOR_IDX if n in out["endeks"]))}
            res[key] = out
            print("C", key, out["KESIF"].get("ortR"), out["TEST"].get("ortR"), out["KOR"].get("ortR"),
                  out["KOR"]["plasebo"], out["KOR"]["arti_endeks"], flush=True)
    return res


def main() -> None:
    p = F.load_ndx_1m()
    out = {"A": part_a(p), "B": part_b(p), "C": part_c()}
    (F.RESULTS / "ek1.json").write_text(json.dumps(out, indent=1, default=lambda o: None if o != o else str(o)))


if __name__ == "__main__":
    main()
