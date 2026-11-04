"""Kırılım / TSMOM NDX — PROTOCOL.md'ye birebir (2026-10-13).

python3.13 bm.py grid      # keşif ızgarası + plasebo + H-S seçimi  → results/grid_*.csv, results/secim.json
python3.13 bm.py kasa      # kasa + DAX + kartlar (bir kez)          → results/kart_*.json, results/kasa.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "research/ndx_gate_forge"))

CUT = pd.Timestamp("2026-07-01", tz="UTC")
END = pd.Timestamp("2026-10-03", tz="UTC")
SPR = 1.5
NS, HS, STOPS = (10, 20, 40, 60), (10, 20, 40), (0.0, 1.5, 2.0)
FAMS = ("F1", "F2", "F3", "F4")
TFS = ("30m", "1h", "4h", "D")
ATR_N, WARM = 14, 250
PLACEBO_REPS = 50
RNG = np.random.default_rng(20261013)


# ───────────────────────── veri ─────────────────────────
def _seg(d: pd.DataFrame) -> pd.DataFrame:
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    d["seg"] = (d.ts.diff() > pd.Timedelta(days=4)).cumsum()
    return d


def _agg(d: pd.DataFrame, key: pd.Series) -> pd.DataFrame:
    g = d.groupby(key.values)
    x = pd.DataFrame({"ts": g.ts.first(), "open": g.open.first(), "high": g.high.max(),
                      "low": g.low.min(), "close": g.close.last()})
    return _seg(x.dropna()).iloc[:-1].reset_index(drop=True)  # son (yarım) kova atılır


def _ny_shift(ts: pd.Series) -> pd.Series:
    """NY saati +7 sa: 17:00 NY → ertesi gün 00:00 (vadeli işlem günü sınırı)."""
    return ts.dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)


def ndx_sets() -> dict[str, pd.DataFrame]:
    from long_data import load_long
    b30 = pd.read_parquet(ROOT / "research/ndx_pattern_motifs/data/bars_30m.parquet")[["ts", "open", "high", "low", "close"]]
    l30 = load_long("30m")[["ts", "open", "high", "low", "close"]]
    d30 = _seg(pd.concat([l30[l30.ts < CUT], b30[b30.ts >= CUT]]))
    l1 = load_long("1h")[["ts", "open", "high", "low", "close"]]
    r1 = b30[b30.ts >= CUT].copy()
    r1 = _agg(r1, r1.ts.dt.floor("1h"))[["ts", "open", "high", "low", "close"]]
    d1 = _seg(pd.concat([l1[l1.ts < CUT], r1]))
    sh = _ny_shift(d1.ts)
    d4 = _agg(d1, sh.dt.floor("4h"))
    dd = _agg(d1, sh.dt.floor("1D"))
    return {"30m": d30, "1h": d1, "4h": d4, "D": dd}


def dax_sets() -> dict[str, pd.DataFrame]:
    G = ROOT / "research/ndx_gate_forge/data"
    d30 = _seg(pd.read_parquet(G / "dax_30m.parquet")[["ts", "open", "high", "low", "close"]])
    h = pd.read_parquet(G / "dax_1h.parquet")[["ts", "open", "high", "low", "close"]]
    h = _seg(h)
    d1 = _seg(h[h.ts >= "2019-01-01"])
    ber = d1.ts.dt.tz_convert("Europe/Berlin").dt.tz_localize(None)
    d4 = _agg(d1, ber.dt.floor("4h"))
    hall = h[h.ts >= "2008-01-01"]
    dd = _agg(hall, hall.ts.dt.tz_convert("Europe/Berlin").dt.tz_localize(None).dt.floor("1D"))
    return {"30m": d30, "1h": d1, "4h": d4, "D": dd}


# ───────────────────────── özellikler / sonuçlar ─────────────────────────
def features(d: pd.DataFrame, tf: str) -> dict:
    o, h, l, c = (d[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    seg = d.seg.to_numpy()
    n = len(c)
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    cs = np.r_[0, np.cumsum(tr)]
    atr = np.full(n, np.nan)
    atr[ATR_N:] = (cs[ATR_N:n] - cs[:n - ATR_N]) / ATR_N          # önceki 14 mum, i hariç
    ema = pd.Series(c).ewm(span=200, adjust=False).mean().to_numpy()
    ts = d.ts.reset_index(drop=True)
    if tf == "D":
        hour = np.zeros(n, int)
    elif tf == "4h":
        hour = _ny_shift(ts).dt.hour.to_numpy()
    else:
        hour = ts.dt.hour.to_numpy()
    return dict(o=o, h=h, l=l, c=c, seg=seg, atr=atr, ema=ema, ts=ts, n=n, hour=hour,
                year=ts.dt.year.to_numpy(), ym=(ts.dt.year * 100 + ts.dt.month).to_numpy(),
                date=ts.dt.strftime("%Y-%m-%d").to_numpy(), tsn=ts.dt.tz_convert(None).to_numpy())


def mask(F: dict, fam: str, N: int, side: int) -> np.ndarray:
    h, l, c = F["h"], F["l"], F["c"]
    hiN = pd.Series(h).shift(1).rolling(N).max().to_numpy()
    loN = pd.Series(l).shift(1).rolling(N).min().to_numpy()
    with np.errstate(invalid="ignore"):
        if fam == "F1":
            m = h >= hiN if side > 0 else l <= loN
        elif fam == "F2":
            m = c > hiN if side > 0 else c < loN
        elif fam == "F3":
            m = (c > hiN) & (c > F["ema"]) if side > 0 else (c < loN) & (c < F["ema"])
        else:
            cN = np.r_[np.full(N, np.nan), c[:-N]]
            m = c > cN if side > 0 else c < cN
    return np.nan_to_num(m, nan=0).astype(bool)


def outcome(F: dict, H: int, k: float, side: int, spr: float = SPR, optimistic: bool = False):
    """Her mum i için: i+1 açılışında giriş, H mum zaman çıkışı, k×ATR stop. → (R_atr, çıkış indeksi, geçerli)."""
    o, h, l, c, atr, seg, n = F["o"], F["h"], F["l"], F["c"], F["atr"], F["seg"], F["n"]
    R = np.full(n, np.nan)
    X = np.full(n, -1)
    i = np.arange(n - H - 1)
    e = i + 1
    ok = (i >= WARM) & np.isfinite(atr[i]) & (atr[i] > 0) & (seg[e + H - 1] == seg[i]) & (seg[np.maximum(i - 60, 0)] == seg[i])
    i, e = i[ok], e[ok]
    A = atr[i]
    if optimistic:
        ent = c[i]
        cost = 0.0
    else:
        ent = o[e] + (spr if side > 0 else 0.0)
        cost = 0.0 if side > 0 else spr
    ex = c[e + H - 1].astype(float)
    xi = e + H - 1
    if k > 0:
        stop = ent - side * k * A
        W = (swv(l, H) if side > 0 else swv(h, H))[e]                # (m, H): mum e..e+H-1
        hit = (W <= stop[:, None]) if side > 0 else (W >= stop[:, None])
        any_ = hit.any(1)
        j = hit.argmax(1)
        oj = o[e + j]
        fill = np.where(j == 0, stop, np.minimum(oj, stop) if side > 0 else np.maximum(oj, stop))
        ex = np.where(any_, fill, ex)
        xi = np.where(any_, e + j, xi)
    R[i] = (side * (ex - ent) - cost) / A
    X[i] = xi
    return R, X


def base_map(F: dict, R: np.ndarray, region: np.ndarray, key: str) -> np.ndarray:
    """Her mum için aynı (yıl×saat) veya (yıl-ay) hücresindeki rastgele-işlem ortalaması (bölge içinde)."""
    v = region & np.isfinite(R)
    if key == "yh":
        kk = F["year"] * 100 + F["hour"]
    elif key == "ym":
        kk = F["ym"]
    else:
        kk = np.zeros(F["n"], int)
    s = pd.Series(R[v]).groupby(kk[v]).mean()
    return pd.Series(kk).map(s).to_numpy(float)


def regions(F: dict, H: int) -> dict[str, np.ndarray]:
    ts = F["tsn"]
    n = F["n"]
    exu = ts[np.minimum(np.arange(n) + H, n - 1)]
    cut, end = np.datetime64(CUT.tz_convert(None)), np.datetime64(END.tz_convert(None))
    return {"kesif": (ts < cut) & (exu < cut), "kasa": (ts >= cut) & (ts < end), "tum": ts < end}


def nonoverlap(idx: np.ndarray, X: np.ndarray) -> np.ndarray:
    keep, busy = [], -1
    for i in idx:
        if i > busy:
            keep.append(i)
            busy = X[i]
    return np.array(keep, int)


def day_boot(vals: np.ndarray, days: np.ndarray, reps: int = 4000, seed: int = 1) -> float:
    if len(vals) < 5:
        return float("nan")
    u, inv = np.unique(days, return_inverse=True)
    s, k = np.bincount(inv, weights=vals), np.bincount(inv)
    r = np.random.default_rng(seed).integers(0, len(u), (reps, len(u)))
    m = s[r].sum(1) / k[r].sum(1)
    return float((m > 0).mean())


# ───────────────────────── ızgara ─────────────────────────
def tf_cache(F: dict) -> dict:
    """(H, k, side) → R, X ve taban haritaları (bölge başına)."""
    C = {}
    for H in HS:
        rg = regions(F, H)
        for k in STOPS:
            for side in (1, -1):
                R, X = outcome(F, H, k, side)
                C[(H, k, side)] = dict(R=R, X=X, rg=rg,
                                       b={(r, key): base_map(F, R, rg[r], key) for r in rg for key in ("yh", "ym", "all")})
    return C


def cell(F: dict, C: dict, m: np.ndarray, H: int, k: float, side: int, region: str) -> dict:
    z = C[(H, k, side)]
    idx = np.where(m & z["rg"][region] & np.isfinite(z["R"]))[0]
    if len(idx) < 30:
        return {"n": len(idx)}
    R = z["R"][idx]
    ex = R - z["b"][(region, "yh")][idx]
    h2 = len(idx) // 2
    return {"n": len(idx), "R": R.mean(), "taban_all": z["b"][(region, "all")][idx].mean(), "fazla": ex.mean(),
            "fazla_ym": (R - z["b"][(region, "ym")][idx]).mean(), "y1": ex[:h2].mean(), "y2": ex[h2:].mean()}


def run_grid(sets: dict, region: str, tag: str, placebo: bool) -> pd.DataFrame:
    rows, prow = [], []
    for tf in TFS:
        F = features(sets[tf], tf)
        C = tf_cache(F)
        M = {(fam, N, side): mask(F, fam, N, side) for fam in FAMS for N in NS for side in (1, -1)}
        for (fam, N, side), m in M.items():
            for H in HS:
                for k in STOPS:
                    r = cell(F, C, m, H, k, side, region)
                    r.update(tf=tf, fam=fam, N=N, H=H, stop=k, yon="BUY" if side > 0 else "SELL")
                    rows.append(r)
        if placebo:
            for rep in range(PLACEBO_REPS):
                off = int(RNG.integers(F["n"] // 10, F["n"] - F["n"] // 10))
                for (fam, N, side), m in M.items():
                    ms = np.roll(m, off)
                    for H in HS:
                        for k in STOPS:
                            r = cell(F, C, ms, H, k, side, region)
                            prow.append(dict(rep=rep, tf=tf, fam=fam, N=N, H=H, stop=k, yon="BUY" if side > 0 else "SELL",
                                             fazla=r.get("fazla", np.nan)))
        print(f"  {tag} {tf}: n_mum={F['n']} tamam", flush=True)
    g = pd.DataFrame(rows)
    g.to_csv(OUT / f"grid_{tag}.csv", index=False)
    if placebo:
        pd.DataFrame(prow).to_csv(OUT / f"placebo_{tag}.csv", index=False)
    return g


def year_grid(sets: dict, years: tuple, tag: str) -> pd.DataFrame:
    """Tek takvim yılı (ör. 2022 ayı) — bölge = o yıl, taban o yılın kendisi."""
    rows = []
    for tf in ("30m", "1h", "4h", "D"):
        F = features(sets[tf], tf)
        for y in years:
            for H in HS:
                for k in STOPS:
                    for side in (1, -1):
                        R, X = outcome(F, H, k, side)
                        reg = (F["year"] == y) & np.isfinite(R)
                        if reg.sum() < 50:
                            continue
                        b = base_map(F, R, reg, "yh")
                        for fam in FAMS:
                            for N in NS:
                                idx = np.where(mask(F, fam, N, side) & reg)[0]
                                if len(idx) < 20:
                                    continue
                                rows.append(dict(tf=tf, yil=y, fam=fam, N=N, H=H, stop=k, yon="BUY" if side > 0 else "SELL",
                                                 n=len(idx), R=R[idx].mean(), taban=R[reg].mean(), fazla=(R[idx] - b[idx]).mean()))
    g = pd.DataFrame(rows)
    g.to_csv(OUT / f"yil_{tag}.csv", index=False)
    return g


# ───────────────────────── kart ─────────────────────────
def card(F: dict, fam: str, N: int, H: int, k: float, region: str, label: str, random_ctrl: bool = False) -> dict:
    side = 1
    R, X = outcome(F, H, k, side)
    R15, _ = outcome(F, H, k, side, spr=SPR * 1.5)
    Ro, _ = outcome(F, H, k, side, optimistic=True)
    rg = regions(F, H)[region]
    m = np.ones(F["n"], bool) if random_ctrl else mask(F, fam, N, side)
    valid = rg & np.isfinite(R)
    allidx = np.where(m & valid)[0]
    idx = nonoverlap(allidx, X)
    unit = k if k > 0 else 1.0
    r, r15, ro = R[idx] / unit, R15[idx] / unit, Ro[idx] / unit
    b = base_map(F, R, valid, "yh")[idx] / unit
    ex = r - b
    days = F["date"][idx + 1]
    h2 = len(r) // 2
    dsum = pd.Series(r).groupby(days).sum().sort_values(ascending=False)
    esum = pd.Series(ex).groupby(days).sum().sort_values(ascending=False)
    yrs = pd.Series(ex).groupby(F["year"][idx]).agg(["mean", "size"]).round(3)
    rr = pd.Series(r).groupby(F["year"][idx]).mean().round(3)
    P = day_boot(r, days)
    Pex = day_boot(ex, days)
    allR = R[allidx] / unit
    chk = {
        "1_hacim": (int(len(r)), len(r) >= 150),
        "2_beklenti": (f"ortR {r.mean():+.3f} P %{100 * P:.1f}", r.mean() > 0 and P >= 0.9),
        "3_kararlilik": (f"{r[:h2].mean():+.3f}/{r[h2:].mean():+.3f}", r[:h2].mean() >= 0 and r[h2:].mean() >= 0),
        "4_surtunme": (f"spread×1,5 {r15.mean():+.3f}", r15.mean() > 0),
        "5_icra": (f"iyimser {ro.mean():+.3f} vs gerçek {r.mean():+.3f} fark {ro.mean() - r.mean():+.3f}",
                   abs(ro.mean() - r.mean()) < 0.5 * abs(r.mean()) and r.mean() > 0),
        "6_tek_poz": (f"tek-poz {r.mean():+.3f} (tüm sinyal n={len(allR)} {allR.mean():+.3f})", r.mean() > 0),
        "7_taban": (f"fazla {ex.mean():+.3f} P %{100 * Pex:.1f} (taban {b.mean():+.3f})", ex.mean() > 0 and Pex >= 0.9),
    }
    out = {"etiket": label, "bolge": region, "kural": f"{fam} N={N} H={H} stop={k}", "n": int(len(r)),
           "WR": round(float((r > 0).mean()), 3), "ortR": round(float(r.mean()), 4), "fazla": round(float(ex.mean()), 4),
           "en_kotu": round(float(r.min()), 2), "toplam": round(float(r.sum()), 1),
           "top5_haric": round(float(dsum.sum() - dsum.head(5).sum()), 1),
           "top10_haric": round(float(dsum.sum() - dsum.head(10).sum()), 1),
           "fazla_top5_haric": round(float(esum.sum() - esum.head(5).sum()), 1),
           "fazla_top10_haric": round(float(esum.sum() - esum.head(10).sum()), 1),
           "yil_fazla": {int(a): [float(b_["mean"]), int(b_["size"])] for a, b_ in yrs.iterrows()},
           "yil_R": {int(a): float(v) for a, v in rr.items()},
           "checks": {kk: {"deger": str(v), "gecti": bool(okk)} for kk, (v, okk) in chk.items()}}
    return out


def pr_card(c: dict) -> None:
    print(f"\n[{c['etiket']}] {c['bolge']} {c['kural']}  n={c['n']} WR %{100 * c['WR']:.1f} ortR {c['ortR']:+.3f} "
          f"fazla {c['fazla']:+.3f} en kötü {c['en_kotu']} toplam {c['toplam']} (top5 hariç {c['top5_haric']}, top10 hariç "
          f"{c['top10_haric']}; fazla top5 hariç {c['fazla_top5_haric']})")
    for kk, v in c["checks"].items():
        print(f"    {kk:13} {'✓' if v['gecti'] else '✗'} {v['deger']}")
    print("    yıl fazla:", {y: v[0] for y, v in c["yil_fazla"].items()})
    print("    yıl ortR :", c["yil_R"])


# ───────────────────────── ana akışlar ─────────────────────────
def summarize(g: pd.DataFrame, p: pd.DataFrame | None, title: str) -> dict:
    s = {}
    print(f"\n=== {title} ===")
    for yon in ("BUY", "SELL"):
        for k in STOPS:
            x = g[(g.yon == yon) & (g.stop == k) & g.fazla.notna()]
            frac = float((x.fazla > 0).mean())
            line = f"{yon:4} stop {k}: hücre {len(x)}  fazla>0 oranı %{100 * frac:.0f}  medyan fazla {x.fazla.median():+.3f}  " \
                   f"(yıl-ay eşli >0 %{100 * (x.fazla_ym > 0).mean():.0f}, medyan {x.fazla_ym.median():+.3f})"
            if p is not None:
                pp = p[(p.yon == yon) & (p.stop == k)].groupby("rep").fazla.apply(lambda v: (v > 0).mean())
                line += f"  | plasebo oran ort %{100 * pp.mean():.0f} %95 %{100 * pp.quantile(.95):.0f}"
                s[f"{yon}_{k}_plasebo95"] = float(pp.quantile(.95))
            print(line)
            s[f"{yon}_{k}"] = frac
            bytf = x.groupby(["tf", "fam"]).fazla.apply(lambda v: int((v > 0).sum())).unstack()
            print("     TF×aile pozitif hücre (/12):\n" + "\n".join("       " + l for l in bytf.to_string().splitlines()))
    return s


def main_grid() -> None:
    print("NDX keşif ızgarası + plasebo")
    g = run_grid(ndx_sets(), "kesif", "ndx_kesif", placebo=True)
    p = pd.read_csv(OUT / "placebo_ndx_kesif.csv")
    s = summarize(g, p, "NDX KEŞİF")
    # H-S seçimi: komşuluk-yumuşatılmış fazla, BUY, stop∈{1.5,2}, F1-F3
    cand = []
    x = g[(g.yon == "BUY") & g.stop.isin([1.5, 2.0]) & g.fam.isin(["F1", "F2", "F3"])].copy()
    for r in x.itertuples():
        ni, hi = NS.index(r.N), HS.index(r.H)
        nb = x[(x.tf == r.tf) & (x.fam == r.fam) & (x.stop == r.stop) &
               x.N.isin([NS[j] for j in range(max(0, ni - 1), min(len(NS), ni + 2))]) &
               x.H.isin([HS[j] for j in range(max(0, hi - 1), min(len(HS), hi + 2))])]
        cand.append(dict(tf=r.tf, fam=r.fam, N=r.N, H=r.H, stop=r.stop, fazla=r.fazla, y1=r.y1, y2=r.y2,
                         yumusak=nb.fazla.mean(), n=r.n))
    cd = pd.DataFrame(cand).sort_values("yumusak", ascending=False)
    sets = ndx_sets()
    chosen = None
    for r in cd.itertuples():
        if not (r.y1 > 0 and r.y2 > 0):
            continue
        F = features(sets[r.tf], r.tf)
        R, X = outcome(F, r.H, r.stop, 1)
        rg = regions(F, r.H)["kesif"]
        idx = nonoverlap(np.where(mask(F, r.fam, r.N, 1) & rg & np.isfinite(R))[0], X)
        if len(idx) >= 150:
            chosen = dict(tf=r.tf, fam=r.fam, N=int(r.N), H=int(r.H), stop=float(r.stop), yumusak=float(r.yumusak),
                          fazla=float(r.fazla), n_tekpoz_kesif=int(len(idx)))
            break
    print("\nKomşuluk-yumuşatılmış ilk 10 (BUY, stoplu, F1-F3):\n", cd.head(10).round(3).to_string(index=False))
    print("\nH-S seçimi:", chosen)
    (OUT / "secim.json").write_text(json.dumps({"ozet": s, "H_S": chosen}, ensure_ascii=False, indent=1))
    print("\n2022 ayı + yıllar (NDX)")
    yg = year_grid(sets, (2018, 2020, 2022), "ndx")
    for y in (2018, 2020, 2022):
        for yon in ("BUY", "SELL"):
            z = yg[(yg.yil == y) & (yg.yon == yon)]
            print(f"  {y} {yon}: hücre {len(z)} fazla>0 %{100 * (z.fazla > 0).mean():.0f} medyan fazla {z.fazla.median():+.3f} "
                  f"| ham ortR medyan {z.R.median():+.3f} vs taban {z.taban.median():+.3f}")


def main_kasa() -> None:
    sel = json.loads((OUT / "secim.json").read_text())["H_S"]
    sets = ndx_sets()
    res = {}
    print("NDX KASA ızgarası (bir kez)")
    gk = run_grid(sets, "kasa", "ndx_kasa", placebo=False)
    res["kasa_ozet"] = summarize(gk, None, "NDX KASA 2026-07-01→10-02")
    print("\nDAX ızgarası (tüm dönem, ayar yok)")
    dsets = dax_sets()
    gd = run_grid(dsets, "tum", "dax", placebo=False)
    res["dax_ozet"] = summarize(gd, None, "DAX TÜM")
    # DAX günlük 2008-2018 (görülmemiş) ayrıca
    dd = dsets["D"]
    FD = features(dd[dd.ts < "2019-01-01"].reset_index(drop=True), "D")
    CD = tf_cache(FD)
    rows = []
    for fam in FAMS:
        for N in NS:
            for side in (1, -1):
                m = mask(FD, fam, N, side)
                for H in HS:
                    for k in STOPS:
                        r = cell(FD, CD, m, H, k, side, "tum")
                        r.update(fam=fam, N=N, H=H, stop=k, yon="BUY" if side > 0 else "SELL")
                        rows.append(r)
    g08 = pd.DataFrame(rows)
    g08.to_csv(OUT / "grid_dax_D_2008_2018.csv", index=False)
    print("\n=== DAX GÜNLÜK 2008-2018 (görülmemiş) ===")
    for yon in ("BUY", "SELL"):
        for k in STOPS:
            z = g08[(g08.yon == yon) & (g08.stop == k) & g08.fazla.notna()]
            print(f"  {yon} stop {k}: hücre {len(z)} fazla>0 %{100 * (z.fazla > 0).mean():.0f} medyan {z.fazla.median():+.3f} "
                  f"(yıl-ay eşli >0 %{100 * (z.fazla_ym > 0).mean():.0f}); ham ortR medyan {z.R.median():+.3f} taban {z.taban_all.median():+.3f}")
    # kartlar
    cards = []
    variants = [("H-A ipucu stop2", "30m", "F1", 20, 20, 2.0), ("H-A ipucu stopsuz", "30m", "F1", 20, 20, 0.0)]
    if sel:
        variants.append(("H-S seçilen", sel["tf"], sel["fam"], sel["N"], sel["H"], sel["stop"]))
    for lab, tf, fam, N, H, k in variants:
        F = features(sets[tf], tf)
        for reg in ("tum", "kesif", "kasa"):
            cards.append(card(F, fam, N, H, k, reg, f"NDX {lab}"))
        cards.append(card(F, fam, N, H, k, "tum", f"NDX {lab} — KONTROL rastgele BUY", random_ctrl=True))
        FDx = features(dsets[tf], tf)
        cards.append(card(FDx, fam, N, H, k, "tum", f"DAX {lab}"))
        if tf == "D":
            dd0 = dsets["D"][dsets["D"].ts < "2019-01-01"].reset_index(drop=True)
            cards.append(card(features(dd0, "D"), fam, N, H, k, "tum", f"DAX {lab} 2008-2018 (görülmemiş)"))
    for c in cards:
        pr_card(c)
    res["kartlar"] = cards
    (OUT / "kasa.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    {"grid": main_grid, "kasa": main_kasa}[sys.argv[1]]()
