"""Tanılar (hüküm dışı; run.py'den SONRA yazıldı, post-hoc olduğu raporda belirtilir).

T1 Fitil-ucu stop tabanı karışıklığı: ızgara yalnız ATR stoplarıyla (a0.5/a1.0/a1.5) yeniden + seçim düzeltmesi.
T2 Mutlak beklenti: KEŞİF'te ort.R > 0 ve P ≥ 0,90 olan hücreler TEST'te ne yapıyor.
T3 Gecikme eğrisi: birincil tanım, ATR 1,0 stop, TP 1R, D = 0…20.
T4 H3 (4h üst fitil SAT) bağımsız: 2016-06 → 2023-12 1h arşivinden 17:00 ET 4h mumları, giriş sonraki 1h açılışı.
T5 H3 / H1 yıl ve seans kırılımı; en iyi 5 gün çıkınca.
T6 Teyit: girişte fiyat sinyal kapanışının ret yönünde mi (D = 15).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine as E  # noqa: E402
import run as RN  # noqa: E402

OUT = {}


def grid_atr(F, Rm, side, sel, perm=None):
    t, mu, n, keys, cols = RN.grid_t(F, Rm, side, sel, perm)
    keep = np.array([c[1] != 0 for c in cols])
    return t[:, keep], mu[:, keep], n[:, keep], keys, [c for c in cols if c[1] != 0]


def abs_grid(F, Rm, side, flag):
    """Her hücrenin mutlak ort.R ve n'i (dönem flag)."""
    sel = ((F.kesif == flag) & F.full).to_numpy()
    cols = RN.grid_cols()
    X = np.stack([Rm[:, side, di, si, ti] for di, si, ti in cols], 1)[sel]
    V = np.isfinite(X)
    X0 = np.where(V, X, 0)
    Fs = F[sel].reset_index(drop=True)
    res = {}
    for s in RN.S_GRID:
        for w in RN.W_GRID:
            for k in RN.K_GRID:
                m = E.event_mask(Fs, side, s, w, k).astype(float)
                n = m @ V
                with np.errstate(invalid="ignore"):
                    res[(s, w, k)] = ((m @ X0) / n, n)
    return res, cols


def main() -> None:
    B = E.load_1m()
    data = {tf: E.build(tf, B) for tf in (60, 240)}
    rng = np.random.default_rng(5)

    # ---- T1 + T2
    for tf in (60, 240):
        F, Rm, T = data[tf]
        sel = (F.kesif & F.full).to_numpy()
        selT = (~F.kesif & F.full).to_numpy()
        hours = F.hour.to_numpy()[sel]
        for side in (0, 1):
            t, mu, n, keys, cols = grid_atr(F, Rm, side, sel)
            tT, muT, nT, *_ = grid_atr(F, Rm, side, selT)
            null = [np.nanmax(grid_atr(F, Rm, side, sel, RN.perm_within_hour(hours, rng))[0]) for _ in range(200)]
            i, j = np.unravel_index(np.nanargmax(t), t.shape)
            order = np.argsort(-np.nan_to_num(t, nan=-99), axis=None)[:20]
            top = [muT[np.unravel_index(o, t.shape)] for o in order]
            # mutlak
            aK, acols = abs_grid(F, Rm, side, True)
            aT, _ = abs_grid(F, Rm, side, False)
            win = []
            for key in aK:
                mK, nK = aK[key]
                mT, nTT = aT[key]
                for c in range(len(acols)):
                    if nK[c] >= RN.N_MIN and mK[c] > 0.10:
                        win.append((key, acols[c], mK[c], nK[c], mT[c], nTT[c]))
            ws = pd.DataFrame(win, columns=["key", "col", "kesif_R", "kesif_n", "test_R", "test_n"])
            di, si, ti = cols[j]
            OUT[f"T1_{tf}_{side}"] = {
                "t_max": round(float(np.nanmax(t)), 2), "null_p95": round(float(np.percentile(null, 95)), 2),
                "p_sel": round(float((np.array(null) >= np.nanmax(t)).mean()), 3),
                "en_iyi": {"swk": keys[i], "D": E.DELAYS[di], "SL": E.SL_MODES[si], "TP": E.TPS[ti],
                           "kesif_fark": round(float(mu[i, j]), 4), "test_fark": round(float(muT[i, j]), 4),
                           "test_n": int(nT[i, j])},
                "ilk20_test_fark_ort": round(float(np.nanmean(top)), 4), "ilk20_test_pozitif": int(np.nansum(np.array(top) > 0)),
                "test_fark_medyan_tum": round(float(np.nanmedian(np.where(nT >= RN.N_MIN, muT, np.nan))), 4),
                "T2_kesif_R>0.10_hucre": len(ws),
                "T2_bunlarin_test_R_ort": round(float(ws.test_R.mean()), 4) if len(ws) else None,
                "T2_bunlarin_test_pozitif_orani": round(float((ws.test_R > 0).mean()), 3) if len(ws) else None,
            }
            print(f"T1/T2 tf={tf} side={side}", json.dumps(OUT[f"T1_{tf}_{side}"], default=str))

    # ---- T3 gecikme eğrisi
    for tf in (60, 240):
        F, Rm, T = data[tf]
        for side in (0, 1):
            m = E.event_mask(F, side, 0.5, 0.5, 0)
            row = {}
            for di, D in enumerate(E.DELAYS):
                for flag, nm in ((True, "K"), (False, "T")):
                    x = Rm[m & (F.kesif == flag).to_numpy() & F.full.to_numpy(), side, di, 2, 1]
                    row[f"D{D}_{nm}"] = round(float(np.nanmean(x)), 3)
            OUT[f"T3_{tf}_{side}"] = row
            print("T3", tf, side, row)

    # ---- T4 H3 bağımsız (1h arşivinden 4h)
    BL = E.load_long1h()
    FL = E.htf_bars(BL, 240)
    FL["full"] = FL.n >= 3
    RL, TL = E.outcomes(BL, FL, 240)
    for side in (0, 1):
        for k in (0, 2):
            m = E.event_mask(FL, side, 0.5, 0.5, k)
            for si, sl in ((0, "tip"), (2, "a1.0")):
                col = RL[:, side, 0, si, 1]
                base = RN.hour_base(col, FL.hour.to_numpy(), FL.full.to_numpy())
                x = RN.trades(BL, FL, TL, m, side, 0, si, 1, 240)
                s = RN.summarize(x, base)
                yr = x.groupby("year").R.mean().round(3).to_dict() if len(x) else {}
                OUT[f"T4_4h_bagimsiz_side{side}_k{k}_{sl}"] = {**s, "yil": yr}
                print("T4", side, k, sl, s, yr)

    # ---- T5 yıl/seans, en iyi 5 gün
    def sess(m):
        return np.select([(m >= 18 * 60) | (m < 2 * 60), m < 8 * 60 + 30, m < 11 * 60], ["Asya", "Londra", "NY_sabah"], "NY_oglen")
    for hid, tf, side, k in RN.PRIMARY[:4]:
        F, Rm, T = data[tf]
        m = E.event_mask(F, side, 0.5, 0.5, k)
        x = RN.trades(B, F, T, m, side, 1, 0, 1, tf)
        x["seans"] = sess(x.ny_min.to_numpy())
        g = x.groupby(x.day).R.sum().sort_values()
        OUT[f"T5_{hid}"] = {"yil": x.groupby("year").R.agg(["mean", "size"]).round(3).to_dict("index"),
                            "seans": x.groupby("seans").R.agg(["mean", "size"]).round(3).to_dict("index"),
                            "toplam": round(float(x.R.sum()), 2), "en_iyi5_gun_cikinca": round(float(g.iloc[:-5].sum()), 2)}
        print("T5", hid, OUT[f"T5_{hid}"])

    # ---- T6 teyit (D=15, ATR 1.0, TP 1)
    for tf in (60, 240):
        F, Rm, T = data[tf]
        for side in (0, 1):
            m = E.event_mask(F, side, 0.5, 0.5, 0) & F.full.to_numpy()
            e = T[:, 3]
            px = np.where(e >= 0, B.o[np.maximum(e, 0)], np.nan)
            conf = (px < F.c.to_numpy()) if side == 0 else (px > F.c.to_numpy())
            r = Rm[:, side, 3, 2, 1]
            row = {}
            for flag, nm in ((True, "K"), (False, "T")):
                p = (F.kesif == flag).to_numpy()
                row[f"teyitli_{nm}"] = (round(float(np.nanmean(r[m & p & conf])), 3), int(np.isfinite(r[m & p & conf]).sum()))
                row[f"teyitsiz_{nm}"] = (round(float(np.nanmean(r[m & p & ~conf])), 3), int(np.isfinite(r[m & p & ~conf]).sum()))
            OUT[f"T6_{tf}_{side}"] = row
            print("T6", tf, side, row)

    (E.OUT / "tani.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
