"""DTS-07 — Zaman Makinesi seans/saat/gün kırılımı (ön-kayıt: PROTOCOL.md Ek-3).

Yoğun ızgara: temiz aylarda her 15m bar. Havuz time_machine_service ile aynı tanım (son 60 dolu seans, aynı slot,
±2 slot jitter, boş slotta en yakın dolu slot); 300 tekrar vektörleştirilmiş.
"""
import json, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from services import time_machine_service as tm
from common import load, month_boot, SPREAD

BM, HS, R, WARM, TAU = 15, (4, 16), 300, 65, 0.05
SYMS = ("NDX", "GDAXI")
SESS = [("Asya", 0, 7), ("Avrupa", 7, 13), ("ABD", 13, 20), ("Geç", 20, 24)]
DOW = ["Pzt", "Sal", "Çrş", "Per", "Cum"]


def clean_months(sym):
    e = pd.read_csv("eksen_denetimi.csv")
    return set(e[(e.sym == sym) & e.temiz].ay)


def run(sym):
    d = load(sym, "15m")
    ts = (d.ts.astype("int64") // 10**9).to_numpy(); c = d.close.to_numpy(); hi = d.high.to_numpy(); lo = d.low.to_numpy()
    days, slots = tm.day_and_slot(ts, BM)
    m = tm.n_slots(BM)
    gap = max(tm.PREV_GAP_S, 2 * BM * 60)
    lr = np.full(len(c), np.nan)
    ok = np.r_[False, (np.diff(ts) > 0) & (np.diff(ts) <= gap)]
    lr[1:] = np.where(ok[1:], np.log(c[1:] / c[:-1]), np.nan)
    order = np.unique(days)
    cnt = {x: int((days == x).sum()) for x in order}
    typical = float(np.median(list(cnt.values())))
    full = [x for x in order if cnt[x] >= tm.MIN_DAY_FRACTION * typical]
    dayrow = {}
    for x in full:
        row = np.full(m, np.nan); idx = np.where(days == x)[0]
        row[slots[idx]] = lr[idx]; dayrow[x] = row
    good = clean_months(sym)
    tz = "America/New_York" if sym == "NDX" else "Europe/Berlin"
    mon_local = d.ts.dt.tz_convert(tz).dt.strftime("%Y-%m").to_numpy()
    rng = np.random.default_rng(19)
    out = []
    full_arr = np.array(full)
    for x in order[WARM:]:
        qi = np.where(days == x)[0]
        qi = qi[[mon_local[q] in good for q in qi]]
        qi = qi[qi + max(HS) < len(c)]
        if len(qi) == 0:
            continue
        prev = full_arr[full_arr < x][-tm.POOL_SESSIONS:]
        if len(prev) < tm.MIN_SESSIONS:
            continue
        P = np.stack([dayrow[p] for p in prev]).T            # m × n_sess
        srt = np.sort(np.where(np.isnan(P), np.inf, P), axis=1)   # geçerliler başta
        n = np.isfinite(srt).sum(1)
        srt = np.where(np.isfinite(srt), srt, 0.0)
        mp = np.arange(m)
        for j in range(m):
            if n[j] == 0:
                mp[j] = next(((j + s * w) % m for w in range(1, tm.MAX_WINDOW + 1) for s in (-1, 1) if n[(j + s * w) % m] > 0), j)
        k = slots[qi]
        steps = k[:, None, None] + np.arange(1, max(HS) + 1)[None, None, :] + rng.integers(-tm.WINDOW, tm.WINDOW + 1, size=(len(qi), R, max(HS)))
        jj = mp[steps % m]
        nn = n[jj]
        pick = np.where(nn > 0, (rng.random(jj.shape) * np.maximum(nn, 1)).astype(int), 0)
        path = np.cumsum(np.where(nn > 0, srt[jj, pick], 0.0), axis=2)
        for h in HS:
            end = path[:, :, h - 1]
            qs = np.quantile(end, [0.05, 0.25, 0.75, 0.95], axis=1)
            pup = (end > 0).mean(1)
            for t, q in enumerate(qi):
                if ts[q + h] - ts[q] > 3 * h * BM * 60:
                    continue
                e = c[q]; real = np.log(c[q + h] / e)
                hmax = np.log(hi[q + 1:q + h + 1].max() / e); lmin = np.log(lo[q + 1:q + h + 1].min() / e)
                out.append({"sym": sym, "h": h, "t": int(ts[q] + BM * 60), "e": e, "real": real, "pup": pup[t],
                            "p5": qs[0, t], "p25": qs[1, t], "p75": qs[2, t], "p95": qs[3, t], "hmax": hmax, "lmin": lmin})
    return out


def segs(df):
    dt = pd.to_datetime(df.t, unit="s", utc=True)
    hr = dt.dt.hour; dw = dt.dt.dayofweek
    sess = pd.Series("", index=df.index)
    for nm, a, b in SESS:
        sess[(hr >= a) & (hr < b)] = nm
    out = {}
    for nm, _, _ in SESS:
        out[("seans", nm)] = sess == nm
    for h in range(24):
        out[("saat", f"{h:02d}")] = hr == h
    for i, nm in enumerate(DOW):
        out[("gün", nm)] = dw == i
    for s, _, _ in SESS:
        for i, nm in enumerate(DOW):
            out[("seans×gün", f"{s}-{nm}")] = (sess == s) & (dw == i)
    return out, dt


def evaluate(df):
    rows = []
    for (sym, h), g in df.groupby(["sym", "h"]):
        g = g.sort_values("t").reset_index(drop=True)
        masks, dt = segs(g)
        cost = np.log(1 + SPREAD[sym] / g.e)
        side = np.where(g.pup >= 0.5 + TAU, 1, np.where(g.pup <= 0.5 - TAU, -1, 0))
        net = side * g.real - (side != 0) * cost
        mon = dt.dt.strftime("%Y-%m").to_numpy(); day = dt.dt.strftime("%Y-%m-%d").to_numpy()
        half = np.arange(len(g)) >= len(g) // 2
        for (fam, nm), mk in masks.items():
            mk = mk.to_numpy()
            if mk.sum() < 50:
                continue
            gs = g[mk]
            in90 = ((gs.real >= gs.p5) & (gs.real <= gs.p95)).mean() * 100
            touch_up = (gs.hmax >= gs.p95).mean() * 100; touch_dn = (gs.lmin <= gs.p5).mean() * 100
            both = ((gs.hmax >= gs.p95) & (gs.lmin <= gs.p5)).mean() * 100
            tr = mk & (side != 0)
            x = net[tr] * 1e4
            ntr, nday = int(tr.sum()), len(set(day[tr]))
            P = month_boot(x, mon[tr]) if ntr >= 10 else np.nan
            y1 = x[~half[tr]].mean() if (~half[tr]).any() else np.nan
            y2 = x[half[tr]].mean() if half[tr].any() else np.nan
            # drift tabanı: 1. yarı kesim ortalama işaretiyle hep aynı yön, 2. yarıda
            r1 = g.real[mk & ~half]; r2 = g.real[mk & half]
            sgn = np.sign(r1.mean()) if len(r1) else 0
            base2 = (sgn * r2 - np.log(1 + SPREAD[sym] / g.e[mk & half])).mean() * 1e4 if len(r2) else np.nan
            up1 = (r1 > 0).mean() if len(r1) else np.nan
            b2 = mk & half
            brier = ((g.pup[b2] - (g.real[b2] > 0)) ** 2).mean() if b2.any() else np.nan
            brier_b = ((up1 - (g.real[b2] > 0)) ** 2).mean() if b2.any() else np.nan
            rows.append({"sym": sym, "h_dk": h * BM, "aile": fam, "kesim": nm, "n": int(mk.sum()), "kapsama90": in90,
                         "p95_dokun": touch_up, "p5_dokun": touch_dn, "iki_uc": both, "islem": ntr, "gun": nday,
                         "ort_bp": x.mean() if ntr else np.nan, "P": P, "y1_bp": y1, "y2_bp": y2, "taban2_bp": base2,
                         "brier2": brier, "brier2_taban": brier_b})
    r = pd.DataFrame(rows)
    r["p_tek"] = 1 - r.P
    r["aralik_ok"] = r.kapsama90.between(85, 95)
    pre = (r.islem >= 150) & (r.gun >= 100) & (r.ort_bp > 0) & (r.P >= 0.95) & (r.y1_bp > 0) & (r.y2_bp > 0) & \
          (r.y2_bp > r.taban2_bp) & (r.brier2 <= r.brier2_taban)
    # Holm (tüm kesimler)
    p = r.p_tek.fillna(1).to_numpy(); o = np.argsort(p); mtot = len(p); holm = np.zeros(mtot, bool)
    for rank, i in enumerate(o):
        if p[i] <= 0.05 / (mtot - rank):
            holm[i] = True
        else:
            break
    r["holm"] = holm
    r["yon_gecti"] = pre & r.holm
    r["on_olcut_holm_haric"] = pre
    return r


def main():
    with Pool(2) as pool:
        rows = sum(pool.map(run, SYMS), [])
    df = pd.DataFrame(rows)
    r = evaluate(df)
    r.to_csv("dts07_kesimler.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    cols = ["sym", "h_dk", "aile", "kesim", "n", "kapsama90", "p95_dokun", "p5_dokun", "iki_uc", "islem", "ort_bp", "P", "y1_bp", "y2_bp", "taban2_bp", "brier2", "brier2_taban", "on_olcut_holm_haric", "yon_gecti"]
    print(r[r.aile.isin(["seans", "gün"])][cols].round(3).to_string(index=False))
    ozet = {"sorgu": len(df), "kesim": len(r), "aralik_ok": int(r.aralik_ok.sum()),
            "kapsama90_min": float(r.kapsama90.min()), "kapsama90_max": float(r.kapsama90.max()),
            "on_olcut_holm_haric": int(r.on_olcut_holm_haric.sum()), "yon_gecti": int(r.yon_gecti.sum()),
            "P_ge_095": int((r.P >= 0.95).sum()), "P_le_005": int((r.P <= 0.05).sum()),
            "uc_senaryo": {f"{s}_{h}": {"p95_dokun": float(g.p95_dokun.mean()), "p5_dokun": float(g.p5_dokun.mean()),
                                         "iki_uc": float(g.iki_uc.mean()), "kapsama90": float(g.kapsama90.mean())}
                           for (s, h), g in r[r.aile == "seans"].groupby(["sym", "h_dk"])},
            "gecen_kesimler": r[r.on_olcut_holm_haric][["sym", "h_dk", "aile", "kesim", "islem", "ort_bp", "P", "y1_bp", "y2_bp"]].to_dict("records")}
    json.dump(ozet, open("dts07_ozet.json", "w"), indent=1, ensure_ascii=False, default=float)
    print(json.dumps({k: v for k, v in ozet.items() if k != "gecen_kesimler"}, ensure_ascii=False, default=float))
    print("Holm hariç ön-ölçütü geçen:", ozet["gecen_kesimler"])


if __name__ == "__main__":
    main()
