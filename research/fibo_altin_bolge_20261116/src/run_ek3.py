"""run_ek3.py — EK-3 §3–§7 (FB_SYM=DAX | XAU): aday dondurma → bağımsız sınav, Fib katkısı, NDX C1–C3 uzun sınavı, VIX.

Kullanım: FB_SYM=DAX python src/run_ek3.py   (önce run_primary + run_grid aynı FB_SYM ile koşulmuş olmalı)
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

import fblib as F
from run_ek1 import CANDS as NDX_CANDS, PRIM, YON_MT5, _load, diff_p, full_criteria

KEYS = ["tf", "side", "pattern", "zone", "sl", "tp", "hold", "smin", "spmin", "filt"]
TF_MIN = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240}
BROKER_FILES = {  # en ince mevcut çözünürlük (dakika) → dosya
    "SpotCrude": {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1"},
    "GER40": {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1"},
    "XAUUSD": {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1"},
    "NAS100": {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1"},
    "US500": {5: "M5y", 30: "M30"},
}
OTHERS = {"DAX": ["NDX", "XAU"], "XAU": ["NDX", "DAX"]}
FEED = {"DAX": "GER40", "XAU": "XAUUSD"}


def filt_mask(tr: pd.DataFrame, filt: str) -> np.ndarray:
    if filt == "tum" or tr.empty:
        return np.ones(len(tr), bool)
    k, v = filt.split(":")
    return (tr.session.values == v) if k == "ses" else (tr.dow.values == int(v))


def run_c(bars, p, c: dict) -> pd.DataFrame:
    cand = F.detect(bars, int(c["side"]))
    s = F.signals(cand, c["pattern"], c["zone"], float(c["smin"]), float(c["spmin"]))
    tr = F.resolve(F.setup_trades(s, bars, p, c["sl"], c["tp"], int(c["hold"]), c["zone"]), p)
    return tr[filt_mask(tr, c["filt"])]


# ───────────────────────── §3 dondurma ─────────────────────────

def freeze() -> list[dict]:
    g = pd.concat([pd.read_parquet(F.RESULTS / f"grid_{tf}.parquet") for tf in F.TFS_NDX], ignore_index=True)
    ok = (g.n_KESIF >= 60) & (g.n_TEST >= 30) & (g.n_KOR >= 30)
    for per in ["KESIF", "TEST", "KOR"]:
        ok &= (g[f"R_{per}"] > 0) & (g[f"R_{per}"] > g[f"pR_{per}"])
    e = g[ok].copy()
    e["min_t"] = e[["t_KESIF", "t_TEST", "t_KOR"]].min(axis=1)
    e = e.sort_values("min_t", ascending=False)
    out, seen = [], set()
    for _, r in e.iterrows():
        fam = (r.tf, r.pattern)
        if fam in seen:
            continue
        seen.add(fam)
        out.append({k: (r[k].item() if hasattr(r[k], "item") else r[k]) for k in KEYS}
                   | {"min_t": round(float(r.min_t), 2), "R_KESIF": round(float(r.R_KESIF), 4),
                      "R_TEST": round(float(r.R_TEST), 4), "R_KOR": round(float(r.R_KOR), 4)})
        if len(out) == 3:
            break
    plac = (g.n_KESIF >= 60) & (g.n_TEST >= 30) & (g.n_KOR >= 30)
    for per in ["KESIF", "TEST", "KOR"]:
        plac &= g[f"pR_{per}"] > 0
    meta = {"uygun_hucre": int(ok.sum()), "plasebo_uc_donem_arti": int(plac.sum()),
            "gercek_uc_donem_arti": int(((g.n_KESIF >= 60) & (g.n_TEST >= 30) & (g.n_KOR >= 30) & (g.R_KESIF > 0)
                                         & (g.R_TEST > 0) & (g.R_KOR > 0)).sum())}
    (F.RESULTS / "ek3_adaylar.json").write_text(json.dumps({"meta": meta, "adaylar": out}, indent=1))
    print("dondurma", meta, *out, sep="\n", flush=True)
    return out


# ───────────────────────── yollar ─────────────────────────

_PATHS: dict[str, F.Path1] = {}


def duka(sym: str) -> F.Path1:
    if sym not in _PATHS:
        _PATHS[sym] = F.load_ndx_1m() if sym == "NDX" else F.load_duka(sym)
    return _PATHS[sym]


def broker_bars(sym: str, tf: str) -> tuple[F.Bars, F.Path1, str] | None:
    want = TF_MIN[tf]
    avail = {m: f for m, f in BROKER_FILES[sym].items() if m <= want and want % m == 0}
    if not avail:
        return None
    m = max(avail)
    f = avail[m]
    bp = _load(YON_MT5 / f"{sym}_M5.csv.gz", sym) if f == "M5y" else F.load_broker(sym, f)
    return _agg(bp, want, m, tf), bp, f


def _agg(bp: F.Path1, want: int, have: int, tf: str) -> F.Bars:
    if want == have:
        return F.build_bars(bp, 1, 0, tf)
    return F.build_bars(bp, want, 120 if want == 240 else 0, tf)


def market_eval(c: dict, bars, p, placebo: bool = True) -> dict:
    tr = run_c(bars, p, c)
    out = F.summarize(tr, boot=True)
    if placebo and len(tr):
        pl = F.placebo(tr, bars, p, int(c["hold"]), draws=5)
        pl = pl[filt_mask(pl, c["filt"])] if len(pl) else pl
        out["plasebo"] = F.summarize(pl).get("ortR")
        out["fark_P"] = diff_p(tr, pl) if len(pl) else None
    out["donem"] = {per: F.summarize(tr[tr.period == per]).get("ortR") for per in ["KESIF", "TEST", "KOR"]} if len(tr) else {}
    return out, tr


# ───────────────────────── §4 bağımsız sınav + §5 Fib katkısı ─────────────────────────

def impulse_now(bars, p, c: dict) -> pd.DataFrame:
    """Aynı itki (S ≥ smin, hız ≥ spmin), ilk görülebildiği bar (H+2) kapanışında giriş; aynı SL/TP/tutuş/filtre."""
    side = int(c["side"])
    Hh, Ll = (bars.h, bars.l) if side > 0 else (-bars.l, -bars.h)
    N, K, M = len(Hh), F.K_WIN, F.M_WIN
    am = sliding_window_view(Hh[:-1], K).argmax(axis=1)
    t = np.arange(K, N)
    hidx = am + (t - K)
    lw = np.full(N, -1)
    lw[M:] = sliding_window_view(Ll, M + 1).argmin(axis=1) + np.arange(N - M)
    ok = (am > 0) & (hidx <= t - 2) & (hidx >= M)
    t, hidx = t[ok], hidx[ok]
    df = pd.DataFrame({"t": t, "hidx": hidx, "lidx": lw[hidx]}).drop_duplicates(["lidx", "hidx"], keep="first")
    H, L = Hh[df.hidx.values], Ll[df.lidx.values]
    R = H - L
    S = R / bars.atr[df.lidx.values]
    df = df.assign(side=side, H=side * H, L=side * L, R=R, S=S, speed=S / np.maximum(df.hidx - df.lidx, 1),
                   plow=side * L, atr=bars.atr[df.t.values])
    df = df[(df.R > 0) & (df.S >= float(c["smin"])) & (df.speed >= float(c["spmin"]))]
    sl = c["sl"] if c["sl"] != "pat" else "L"
    tr = F.resolve(F.setup_trades(df, bars, p, sl, c["tp"], int(c["hold"]), c["zone"]), p)
    return tr[filt_mask(tr, c["filt"])]


def indep(cands: list[dict]) -> dict:
    res = {}
    p0 = duka(F.SYM)
    for i, c in enumerate(cands, 1):
        code = f"{F.SYM}{i}"
        tf = c["tf"]
        bars = F.build_bars(p0, *F.TFS_NDX[tf], tf)
        own, tr = market_eval(c, bars, p0)
        pl = F.placebo(tr, bars, p0, int(c["hold"]), draws=5)
        pl = pl[filt_mask(pl, c["filt"])] if len(pl) else pl
        r = {"tanim": c, "kendi": full_criteria(tr, pl), "bagimsiz": {}}
        ctl = impulse_now(bars, p0, c)
        r["fib_katkisi"] = {}
        for per in ["KESIF", "TEST", "KOR", None]:
            a = tr if per is None else tr[tr.period == per]
            b = ctl if per is None else ctl[ctl.period == per]
            r["fib_katkisi"][per or "TUM"] = {"aday": F.summarize(a).get("ortR"), "itki_aninda": F.summarize(b, boot=True),
                                              "fark": round(float(a.R.mean() - b.R.mean()), 4) if len(a) and len(b) else None,
                                              "fark_P": diff_p(a, b)}
        pooled = []
        for m in OTHERS[F.SYM]:
            if m != "NDX" and not (F.CACHE / f"{m}_1m_raw.parquet").exists():
                r["bagimsiz"][f"{m}_duka"] = {"n": 0, "not": "veri henüz yok"}
                continue
            pm = duka(m)
            bm = F.build_bars(pm, *F.TFS_NDX[tf], tf)
            ev, trm = market_eval(c, bm, pm)
            r["bagimsiz"][f"{m}_duka"] = ev
            if len(trm):
                pooled.append(trm.assign(sym=m))
        for bsym in ["SpotCrude", "US500", FEED[F.SYM]]:
            bb = broker_bars(bsym, tf)
            if bb is None:
                r["bagimsiz"][bsym] = {"n": 0, "not": "uygun TF yok"}
                continue
            bbars, bp, fname = bb
            ev, trb = market_eval(c, bbars, bp)
            ev["kaynak"] = fname
            ev["basla"] = str(pd.to_datetime(bp.local[0], unit="s").date())
            r["bagimsiz"][bsym if bsym != FEED[F.SYM] else f"{bsym}_besleme_kontrolu"] = ev
            if bsym != FEED[F.SYM] and len(trb):
                pooled.append(trb.assign(sym=bsym))
        if pooled:
            pdf = pd.concat(pooled)
            pdf = pdf.assign(date=pdf.sym + "|" + pdf.date.astype(str))
            r["bagimsiz_havuz"] = F.summarize(pdf, boot=True)
        r["bagimsiz_arti_sayi"] = int(sum(1 for k, v in r["bagimsiz"].items()
                                          if "besleme" not in k and (v.get("ortR") or -1) > 0))
        if F.SYM == "XAU":
            tk = tr[tr.period != "KESIF"]
            r["xau_2x_finansman_TK"] = round(float((tk.R - tk.rolls * F.FIN_PER_NIGHT * tk.entry / tk.risk).mean()), 4) \
                if len(tk) else None
        res[code] = r
        print(code, c, "\n  kendi TK", r["kendi"]["TK"], "\n  bağımsız", {k: v.get("ortR") for k, v in r["bagimsiz"].items()},
              "\n  havuz", r.get("bagimsiz_havuz"), "\n  fib katkı", r["fib_katkisi"]["TUM"]["fark"],
              r["fib_katkisi"]["TUM"]["fark_P"], flush=True)
    return res


# ───────────────────────── §6 NDX adayları burada ─────────────────────────

def ndx_cands_here() -> dict:
    p = duka(F.SYM)
    out = {}
    for code, c in NDX_CANDS.items():
        cc = {**c, "side": 1, "spmin": c["spmin"], "filt": "ses:NY"}
        bars = F.build_bars(p, *F.TFS_NDX[c["tf"]], c["tf"])
        ev, tr = market_eval(cc, bars, p)
        ev["NY_disi_tum"] = F.summarize(run_c(bars, p, {**cc, "filt": "tum"})).get("ortR")
        out[code] = ev
        print("NDX", code, "→", F.SYM, ev.get("n"), ev.get("ortR"), ev.get("P"), ev.get("donem"), flush=True)
    return out


# ───────────────────────── §7 VIX ─────────────────────────

def vix_split() -> dict:
    mac = pd.read_parquet(F.ROOT / "research/nom_20261113/data/macro/macro_daily.parquet")
    vd = pd.to_datetime(mac.date).values.astype("datetime64[D]")
    vv = mac.VIX_close.values
    k = ~np.isnan(vv)
    vd, vv = vd[k], vv[k]

    def prior(d):
        i = np.searchsorted(vd, d.astype("datetime64[D]"), side="left") - 1
        return np.where(i >= 0, vv[np.maximum(i, 0)], np.nan)

    p = duka(F.SYM)
    res = {}
    for tf in F.TFS_NDX:
        bars = F.build_bars(p, *F.TFS_NDX[tf], tf)
        for side in (1, -1):
            c = {**PRIM, "side": side, "filt": "tum", "tf": tf}
            tr = run_c(bars, p, c)
            if len(tr) < 10:
                continue
            pl = F.placebo(tr, bars, p, 100, draws=5)
            tr, pl = tr.assign(vix=prior(tr.date.values)), pl.assign(vix=prior(pl.date.values))
            o = {}
            for reg, f in [("VIX>=18.4", lambda x: x.vix >= 18.4), ("VIX<18.4", lambda x: x.vix < 18.4)]:
                g, gp = tr[f(tr)], pl[f(pl)]
                o[reg] = {"TUM": F.summarize(g, boot=True), "plasebo": F.summarize(gp).get("ortR"), "fark_P": diff_p(g, gp),
                          **{per: F.summarize(g[g.period == per]).get("ortR") for per in ["KESIF", "TEST", "KOR"]}}
            lab = f"{tf}|{'UZUN' if side > 0 else 'KISA'}"
            res[lab] = o
            print("VIX", lab, o["VIX>=18.4"]["TUM"].get("ortR"), o["VIX>=18.4"]["KESIF"], o["VIX>=18.4"]["TEST"],
                  o["VIX>=18.4"]["KOR"], "| düşük", o["VIX<18.4"]["TUM"].get("ortR"), flush=True)
    return res


def main() -> None:
    cands = freeze()
    out = {"adaylar": cands, "bagimsiz": indep(cands) if cands else {}, "ndx_adaylari": ndx_cands_here(),
           "vix": vix_split()}
    (F.RESULTS / "ek3.json").write_text(json.dumps(out, indent=1, default=lambda o: None if o != o else str(o)))


if __name__ == "__main__":
    main()
