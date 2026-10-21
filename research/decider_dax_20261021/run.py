"""Decider GDAXI analizi — bkz. PROTOCOL.md. python3 research/decider_dax_20261021/run.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "results"
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import data  # noqa: E402

SYM = "GDAXI.INDX"
TP_X, SL_X = 1.0, 1.5
HORIZON = 48 * 60
DUP_SEC = 10
CUT_MIN, CUT_R = 5, -0.5
MINS, THS = (3, 5, 7, 10, 15), (-0.3, -0.4, -0.5, -0.6, -0.7)
N_BOOT, N_PLAC = 3000, 200
RNG = np.random.default_rng(2110)
RECENT = pd.Timestamp("2026-10-07", tz="UTC")


def journal() -> pd.DataFrame:
    p = OUT / "journal.parquet"
    if p.exists():
        return pd.read_parquet(p)
    rows = data.fetch_table(data.get_client(), "decider_journal", "id,ts,raw", [("symbol", "eq", SYM)], "ts")
    recs = []
    for r in rows:
        raw = r.get("raw") or {}
        dec = raw.get("decision") or {}
        if str(dec.get("action", "")).upper() != "OPEN":
            continue
        tr = raw.get("trade") or {}
        recs.append({"id": r["id"], "ts": pd.Timestamp(r["ts"]), "dir": str(dec.get("direction") or "").upper(),
                     "size": dec.get("size_factor"), "atr": tr.get("atr"), "spread": tr.get("spread"),
                     "model": raw.get("model"), "live": bool(raw.get("live"))})
    d = pd.DataFrame(recs).sort_values("ts").reset_index(drop=True)
    keep, last = [], {}
    for i, r in d.iterrows():
        k = r.dir
        if k in last and (r.ts - last[k]).total_seconds() <= DUP_SEC:
            continue
        keep.append(i)
        last[k] = r.ts
    d = d.loc[keep].reset_index(drop=True)
    d.to_parquet(p)
    return d


def bars() -> tuple:
    raw = data.load_bars_raw(SYM, pd.Timestamp("2026-06-25", tz="UTC"), data.utc_now())
    b = data.normalize_snapshot_clock(raw).sort_index()
    return b.open.to_numpy(float), b.high.to_numpy(float), b.low.to_numpy(float), b.close.to_numpy(float), b.index


def sim(B, ts, atr, sp, s, cut_min=None, cut_r=CUT_R, next_open=False, path=False):
    op, hi, lo, cl, idx = B
    j = idx.searchsorted(ts, side="right")
    if j >= idx.size - 2 or not np.isfinite(atr) or atr <= 0 or (idx[j] - ts) > pd.Timedelta(minutes=5):
        return (np.nan, None) if path else np.nan
    e = op[j] + (sp if s > 0 else 0.0)
    risk = SL_X * atr
    sl, tp = e - s * risk, e + s * TP_X * atr
    adj = 0.0 if s > 0 else sp
    end = min(idx.size, j + HORIZON)
    out = None
    for k in range(j, end):
        adv = lo[k] if s > 0 else hi[k] + adj
        fav = hi[k] if s > 0 else lo[k] + adj
        if adv * s <= sl * s:
            out = (-1.0, k)
            break
        if fav * s >= tp * s:
            out = (TP_X / SL_X, k)
            break
        if cut_min is not None and k == j + cut_min - 1:
            r = s * (cl[k] + adj - e) / risk
            if r <= cut_r:
                if next_open and k + 1 < idx.size:
                    px = op[k + 1] + adj - (sp / 2 if s > 0 else -sp / 2)
                    out = (float(s * (px - e) / risk), k + 1)
                else:
                    out = (float(r), k)
                break
    if out is None:
        out = (float(s * (cl[end - 1] + adj - e) / risk), end - 1)
    if not path:
        return out[0]
    # SL anatomisi: 5. dk R ve stop sonrası 240 dk'da TP seviyesi görüldü mü
    r5 = s * (cl[min(j + 4, idx.size - 1)] + adj - e) / risk
    after = False
    if out[0] == -1.0:
        k2 = min(idx.size, out[1] + 240)
        seg = hi[out[1] + 1:k2] if s > 0 else lo[out[1] + 1:k2] + adj
        after = bool(seg.size and (seg * s >= tp * s).any())
    return out[0], {"r5": r5, "dk": out[1] - j + 1, "yon_dogru": after}


def boot_p(x: np.ndarray, days: np.ndarray) -> float:
    ud = np.unique(days)
    ix = {u: np.flatnonzero(days == u) for u in ud}
    return float(np.mean([x[np.concatenate([ix[u] for u in RNG.choice(ud, ud.size)])].mean() > 0 for _ in range(N_BOOT)]))


def auc(pos: np.ndarray, neg: np.ndarray) -> float:
    if not pos.size or not neg.size:
        return np.nan
    return float(np.mean([(p > neg).mean() + 0.5 * (p == neg).mean() for p in pos]))


def side_report(d: pd.DataFrame, B, side: str, L: list) -> None:
    s = 1 if side == "BUY" else -1
    D = d[d.dir == side].reset_index(drop=True)
    if len(D) < 15:
        L.append(f"\n## {side}: n={len(D)} — yetersiz")
        return
    sp = D.spread.fillna(D.spread.median() if D.spread.notna().any() else 1.0).astype(float).to_numpy()
    atr = D.atr.astype(float).to_numpy()
    res = [sim(B, t, a, p, s, path=True) for t, a, p in zip(D.ts, atr, sp)]
    base = np.array([r[0] for r in res])
    ok = np.isfinite(base)
    days = D.ts.dt.strftime("%Y-%m-%d").to_numpy()
    h = np.arange(ok.sum()) < ok.sum() // 2
    rec = (D.ts >= RECENT).to_numpy()
    L.append(f"\n## {side} — OPEN n={int(ok.sum())} ({D.ts.min():%m-%d} → {D.ts.max():%m-%d}) (gerçek MT5 icrası değil — icra yalnız 2, bkz. SONUC.md)")
    L.append(f"A. ortR {base[ok].mean():+.3f} · WR %{100 * (base[ok] > 0).mean():.1f} (başabaş %60) · P(EV>0) %{100 * boot_p(base[ok], days[ok]):.0f} "
             f"· yarılar {base[ok][h].mean():+.3f}/{base[ok][~h].mean():+.3f} · son 14 gün n={int((ok & rec).sum())} ortR "
             f"{np.nanmean(base[ok & rec]) if (ok & rec).any() else float('nan'):+.3f}")
    # B plasebo
    pl = []
    for _ in range(N_PLAC):
        sh = RNG.integers(-10, 11, len(D))
        sh[sh == 0] = 1
        ts2 = D.ts + pd.to_timedelta(sh, unit="D")
        pl.append(np.array([sim(B, t, a, p, s) for t, a, p in zip(ts2, atr, sp)]))
    P = np.vstack(pl)
    rnd_mean = np.nanmean(P, axis=0)
    m = ok & np.isfinite(rnd_mean)
    diff = base[m] - rnd_mean[m]
    L.append(f"B. giriş − rastgele gün (aynı dakika, aynı ATR/spread, ×{N_PLAC}): {diff.mean():+.3f} R/işlem, P(>0) %{100 * boot_p(diff, days[m]):.0f} "
             f"(rastgele ortR {rnd_mean[m].mean():+.3f})")
    # C anatomi
    sl = [r[1] for r in res if r[1] and r[0] == -1.0]
    tpx = [r[1] for r in res if r[1] and r[0] == TP_X / SL_X]
    if sl:
        L.append(f"C. SL n={len(sl)}: yön doğru (stop sonrası 240 dk'da TP seviyesi) %{100 * np.mean([x['yon_dogru'] for x in sl]):.0f} · "
                 f"≤10 dk %{100 * np.mean([x['dk'] <= 10 for x in sl]):.0f} · 5. dk R ile SL/TP ayrımı AUC "
                 f"{auc(np.array([x['r5'] for x in tpx]), np.array([x['r5'] for x in sl])):.2f}")
    # D erken kesme (dondurulmuş)
    rows = []
    for lab, kw, mult in (("5dk/−0,5 (kapanış)", {}, 1.0), ("sonraki açılışta çık", dict(next_open=True), 1.0),
                          ("spread ×1,5", {}, 1.5), ("sonraki açılış + spread ×1,5", dict(next_open=True), 1.5)):
        b0 = np.array([sim(B, t, a, p * mult, s) for t, a, p in zip(D.ts, atr, sp)])
        x = np.array([sim(B, t, a, p * mult, s, cut_min=CUT_MIN, **kw) for t, a, p in zip(D.ts, atr, sp)])
        mm = np.isfinite(b0) & np.isfinite(x)
        dd = x[mm] - b0[mm]
        hh = np.arange(mm.sum()) < mm.sum() // 2
        rows.append({"varyant": lab, "n": int(mm.sum()), "kesilen": int((x[mm] != b0[mm]).sum()), "fark": dd.mean(),
                     "P(fark>0)": boot_p(dd, days[mm]), "yarılar": f"{dd[hh].mean():+.4f}/{dd[~hh].mean():+.4f}",
                     "ortR kesmeli": x[mm].mean(), "ortR taban": b0[mm].mean()})
    L.append("D. erken kesme (XAU'dan DONDURULMUŞ 5 dk / −0,5R):")
    L.append(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:+.4f}"))
    xr = np.vstack([[sim(B, t, a, p, s, cut_min=CUT_MIN) for t, a, p in zip(ts2, atr, sp)] for ts2 in
                    [D.ts + pd.to_timedelta(np.where(q == 0, 1, q), unit="D") for q in RNG.integers(-10, 11, (60, len(D)))]])
    L.append(f"   rastgele-gün plasebo (×60): kuralın rastgele girişlerdeki kazancı medyan "
             f"{np.nanmedian(np.nanmean(xr - P[:60], axis=1)):+.4f} vs gerçek {rows[0]['fark']:+.4f}")
    # E plato
    pr = []
    for mn in MINS:
        row = {"dk": mn}
        for th in THS:
            x = np.array([sim(B, t, a, p, s, cut_min=mn, cut_r=th) for t, a, p in zip(D.ts, atr, sp)])
            mm = ok & np.isfinite(x)
            row[f"{th:+.1f}"] = (x[mm] - base[mm]).mean()
        pr.append(row)
    L.append("E. plato (fark R/işlem):")
    L.append(pd.DataFrame(pr).to_string(index=False, float_format=lambda v: f"{v:+.4f}"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = journal()
    B = bars()
    L = ["# Decider GDAXI — XAU ile aynı analiz (ön-kayıt PROTOCOL.md)",
         f"\nJournal OPEN (yinelenmeyen): {len(d)} · yön: {d.dir.value_counts().to_dict()} · modeller: {d.model.value_counts().head(4).to_dict()}"]
    for side in ("BUY", "SELL"):
        side_report(d, B, side, L)
    # bot DAX işlemleri (bilgi): 5. dk R'si ≤ −0,5 olanları o R'de kapatsaydık
    t = pd.read_csv(ROOT / "output" / "islem_otopsi" / "2026-10-20_1429_all" / "islemler.csv")
    g = t[(t.symbol == SYM) & t.family.isin(["MOMSR", "CHREV"]) & t.e5_close_r.notna()]
    cut = np.where(g.e5_close_r <= CUT_R, np.minimum(g.e5_close_r, 0), g.r_exit)
    L.append(f"\n## Bot DAX işlemleri (MOMSR/CHREV, bilgi; 5. dk kapanış R'si islem_otopsi `e5_close_r`): n={len(g)} · "
             f"kesilen {int((g.e5_close_r <= CUT_R).sum())} · ortR {g.r_exit.mean():+.3f} → kesmeli {np.mean(cut):+.3f} "
             f"(fark {np.mean(cut) - g.r_exit.mean():+.3f})")
    txt = "\n".join(L)
    (OUT / "rapor.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
