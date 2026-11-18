"""korku.py — gün sonu korku göstergeleri (K1–K6) → gece / ertesi gün (PROTOCOL). gece.py motorunu kullanır.

Kullanım: python korku.py kesif | dogrula | ayna
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/fitil_gece_20261118/src"))
import gece as G  # noqa: E402
import gece_run as GR  # noqa: E402

RES = ROOT / "research/korku_gece_20261118/results"
TZ = "America/New_York"
KS_ = {"K1": (0.5, 1.0), "K2": (0.20, 0.10), "K3": (0.3, 0.6), "K4": (2.0, 3.0), "K5": (0.5, 1.0), "K6": (3, 2)}
N_MIN, N_PL, MAX_FROZEN, MAX_PER = 25, 20, 5, 2
P_YENI = 1 - 0.10 / MAX_FROZEN


def features(d: pd.DataFrame, entry: int, step: int) -> pd.DataFrame:
    """Gün başına, girişe kadarki RTH (09:30 →) barlarından: TWAP, tepe, dip, 09:30 açılışı."""
    x = G._local(d, TZ)
    r = x[(x.mn >= 570) & (x.mn < entry)]
    g = r.groupby("day")
    f = pd.DataFrame({"twap": g.c.mean(), "hi": g.h.max(), "lo": g.l.min(), "o930": g.o.first(), "nb": g.size()})
    return f


def triggers(nt: pd.DataFrame, f: pd.DataFrame, dp: pd.DataFrame, entry: int) -> dict:
    """(K, eşik) → gün maskesi (nt sırasıyla)."""
    ff = f.reindex(nt.d.values)
    p = dp.reindex(nt.d.values)
    pe = p[f"o{entry}"].values
    pm60 = p[f"o{entry - 60}"].values if f"o{entry - 60}" in p else np.full(len(nt), np.nan)
    days = list(dp.index)
    pos = {d: i for i, d in enumerate(days)}
    o16 = dp["o960"].values
    prev16 = np.array([o16[pos[d] - 1] if pos[d] > 0 else np.nan for d in nt.d])
    dret = pd.Series(o16, index=days).pct_change()

    def downs(d, k):
        i = pos[d]
        return i > k and all(dret.iloc[i - j] < 0 for j in range(1, k + 1))

    hi, lo, o930, tw = ff.hi.values, ff.lo.values, ff.o930.values, ff.twap.values
    rng = (hi - lo) / o930
    out = {}
    for thr in KS_["K1"]:
        out[("K1", thr)] = (pe / tw - 1) * 100 <= -thr
    for thr in KS_["K2"]:
        out[("K2", thr)] = ((pe - lo) / (hi - lo) <= thr) & (rng >= 0.015)
    for thr in KS_["K3"]:
        out[("K3", thr)] = (pe / pm60 - 1) * 100 <= -thr
    for thr in KS_["K4"]:
        out[("K4", thr)] = (rng * 100 >= thr) & (pe < o930)
    for thr in KS_["K5"]:
        out[("K5", thr)] = ((o930 / prev16 - 1) * 100 <= -thr) & (pe < o930)
    for k in KS_["K6"]:
        out[("K6", k)] = np.array([downs(d, k) for d in nt.d]) & (pe / prev16 - 1 < 0)
    return {k: np.nan_to_num(v.astype(float), nan=0).astype(bool) for k, v in out.items()}


def build(d: pd.DataFrame, step: int) -> dict:
    mins = sorted({570, 870, 900, 930, 960, 240})
    dp = G.day_prices(d, TZ, mins, step)
    out = {}
    for en, emin in G.ENTRIES.items():
        f = features(d, emin, step)
        for ex in ("09:30", "16:00"):
            nt = G.nights(dp, emin, G.EXITS[ex], G.KSG_REF, G.nyse_ok)
            out[(en, ex)] = (nt, triggers(nt, f, dp, emin))
    return out


def cell(nt: pd.DataFrame, m: np.ndarray, ksg: bool, n_boot: int = 4000, excl: np.ndarray | None = None) -> dict:
    mk = (nt.ksg_ret < 0).values if ksg else np.ones(len(nt), bool)
    keep = ~excl if excl is not None else np.ones(len(nt), bool)
    a, b = nt[m & mk & keep], nt[~m & mk & keep]
    if len(a) < 3 or len(b) < 3:
        return {"n": int(len(a))}
    diff = a.net_bp.mean() - b.net_bp.mean()
    se = np.sqrt(a.net_bp.var(ddof=1) / len(a) + b.net_bp.var(ddof=1) / len(b))
    return {"n": int(len(a)), "tetik": float(a.net_bp.mean()), "taban": float(b.net_bp.mean()), "fark": float(diff),
            "t": float(diff / se) if se > 0 else np.nan, "s15": float(a.net_bp_s15.mean()),
            "P": G.KS.diff_p(a.net_bp.values, a.d.astype(str).values, b.net_bp.values, b.d.astype(str).values, n=n_boot)}


def grid(B: dict, era: str | None, n_boot: int, shift: dict | None = None) -> pd.DataFrame:
    rows = []
    for (en, ex), (nt, trig) in B.items():
        sel = (nt.era == era).values if era else np.ones(len(nt), bool)
        for (k, thr), m in trig.items():
            mm = np.roll(m, shift[(en, ex)]) if shift else m
            for ksg in (True, False):
                r = cell(nt[sel].reset_index(drop=True), mm[sel], ksg, n_boot)
                rows.append({"K": k, "esik": thr, "entry": en, "exit": ex, "ksg": ksg, **r})
    return pd.DataFrame(rows)


def passing(g: pd.DataFrame) -> pd.DataFrame:
    return g[(g.n >= N_MIN) & (g.tetik > 0) & (g.fark > 0) & (g.P >= 0.90)]


def kesif() -> None:
    RES.mkdir(exist_ok=True)
    B = build(G.ndx_bars(), 60)
    gr = grid(B, "ESKI", 4000)
    gr.to_csv(RES / "kesif_izgara.csv", index=False)
    real = passing(gr)
    print(f"ESKİ: {len(gr)} hücre, aday {len(real)}", flush=True)
    pc = []
    for r in range(N_PL):
        rng = np.random.default_rng(1100 + r)
        sh = {k: int(rng.integers(1, 11) * rng.choice([-1, 1])) for k in B}
        pc.append(int(len(passing(grid(B, "ESKI", 300, sh)))))
    frozen, per = [], {}
    for r in real.sort_values("t", ascending=False).itertuples():
        if per.get(r.K, 0) >= MAX_PER:
            continue
        frozen.append({k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in r._asdict().items() if k != "Index"})
        per[r.K] = per.get(r.K, 0) + 1
        if len(frozen) == MAX_FROZEN:
            break
    oz = {"hucre": len(gr), "aday": len(real), "plasebo": sorted(pc), "plasebo_p95": float(np.percentile(pc, 95)),
          "sans_ustu": bool(len(real) > np.percentile(pc, 95)), "donmus": frozen,
          "aday_listesi": real.sort_values("t", ascending=False).head(20).to_dict("records")}
    (RES / "kesif_ozet.json").write_text(json.dumps(oz, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: oz[k] for k in ("hucre", "aday", "plasebo", "plasebo_p95", "sans_ustu")}, ensure_ascii=False))
    for c in real.sort_values("t", ascending=False).head(12).itertuples():
        print(f"  {c.K} {c.esik} {c.entry}→{c.exit} KSG={c.ksg} n {c.n} tetik {c.tetik:+.1f} taban {c.taban:+.1f} P {c.P:.3f} t {c.t:.2f}")


def dogrula() -> None:
    frozen = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    d = G.ndx_bars()
    B = build(d, 60)
    fd = {nm: build(b, st) for nm, (b, st) in GR.feeds().items()}
    wide = G.wick_ends(d, TZ, 7200, 0.50, 60)
    out = []
    for c in frozen:
        key, tk = (c["entry"], c["exit"]), (c["K"], c["esik"])
        nt, trig = B[key]
        y = cell(nt[nt.era == "YENI"].reset_index(drop=True), trig[tk][(nt.era == "YENI").values], c["ksg"])
        tot = cell(nt, trig[tk], c["ksg"])
        exw = G.tag(nt.t_in.values, wide, 12 * 3600)
        ind = cell(nt, trig[tk], c["ksg"], excl=exw)
        fr = {nm: cell(fb[key][0], fb[key][1][tk], c["ksg"]) for nm, fb in fd.items()}
        ok = {"1_yeni": bool(y.get("tetik", -1) > 0 and y.get("P", 0) >= P_YENI),
              "2_beslemeler": all(f.get("tetik", -1) > 0 and f.get("tetik", -1) > f.get("taban", 9e9) for f in fr.values()),
              "3_fitilden_bagimsiz": bool(ind.get("tetik", -1) > 0 and ind.get("fark", -1) > 0 and ind.get("P", 0) >= 0.90),
              "4_surtunme": bool(y.get("s15", -1) > 0), "5_hacim": bool(tot.get("n", 0) >= 150)}
        hk = "B" if all(ok.values()) else ("C (fitilin başka ölçüsü)" if ok["1_yeni"] and ok["2_beslemeler"] else "X")
        out.append({"hucre": {k: c[k] for k in ("K", "esik", "entry", "exit", "ksg")}, "ESKI": {k: c[k] for k in ("n", "tetik", "taban", "P")},
                    "YENI": y, "TUM": tot, "fitilsiz_geceler": ind, "beslemeler": fr, "olcut": ok, "hukum": hk})
        print(f"{c['K']} {c['esik']} {c['entry']}→{c['exit']} KSG={c['ksg']} | YENİ {y.get('tetik', float('nan')):+.1f} vs {y.get('taban', float('nan')):+.1f} "
              f"(n {y.get('n')}, P {y.get('P', 0):.3f}) | fitilsiz gecelerde {ind.get('tetik', float('nan')):+.1f} vs {ind.get('taban', float('nan')):+.1f} "
              f"(n {ind.get('n')}, P {ind.get('P', 0):.3f}) | " + " ".join(f"{nm} {f.get('tetik', float('nan')):+.1f}/{f.get('taban', float('nan')):+.1f}"
                                                                          for nm, f in fr.items()) + f" | n {tot.get('n')} | {hk}", flush=True)
    (RES / "dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def ayna() -> None:
    """Coşku aynası: 6 sa içinde 2h büyük ÜST fitil ∧ 15:00→15:30 yukarı → 15:30 SAT, ertesi 16:00 al-kapat."""
    d = G.ndx_bars()
    x = G._local(d, TZ)
    key = x["loc"].values - x["loc"].values % 7200
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    en = np.r_[st[1:], len(key)] - 1
    o, c = x.o.values[st], x.c.values[en]
    h, l = np.maximum.reduceat(x.h.values, st), np.minimum.reduceat(x.l.values, st)
    bb, tt = np.minimum(o, c), np.maximum(o, c)
    uw, lw = (h - tt) / tt * 100, (bb - l) / bb * 100
    ends = np.sort(x.t.values[en][(uw >= 0.5) & (lw <= 0.5 * uw)] + 60)
    dp = G.day_prices(d, TZ, [900, 930, 960], 60)
    days = [dd for dd in dp.index if dd.weekday() < 5 and G.nyse_ok(dd)]
    rows = []
    for i, dd in enumerate(days[:-1]):
        r, nx = dp.loc[dd], dp.loc[days[i + 1]]
        if not (np.isfinite(r.o930) and np.isfinite(r.o900) and np.isfinite(nx.o960)):
            continue
        up = r.o930 / r.o900 - 1 > 0
        net = -((nx.o960 + nx.s960) / r.o930 - 1) * 1e4
        rows.append({"d": dd, "t_in": int(r.t930), "up": up, "net": net})
    nt = pd.DataFrame(rows)
    m = G.tag(nt.t_in.values, ends, 6 * 3600) & nt.up.values
    a, b = nt[m], nt[~m & nt.up.values]
    res = {"n": int(len(a)), "SAT_ort_bp": round(float(a.net.mean()), 1), "taban_SAT_bp": round(float(b.net.mean()), 1)}
    print("coşku aynası:", res)
    (RES / "ayna.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula, "ayna": ayna}[sys.argv[1]]()
