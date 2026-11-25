"""MG-2 kopya/plasebo + kilit tetiği ölçümü; MG-3 kural çözümü ve bağımsız dönem (PROTOCOL.md)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anatomi as A  # noqa: E402
import veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
TOHUM = 20261125
REF_PX = None


def gun_P(x, gun, n=4000):
    kod, ters = np.unique(gun, return_inverse=True)
    top, ad = np.bincount(ters, weights=x), np.bincount(ters).astype(float)
    sec = np.random.default_rng(TOHUM).integers(0, len(kod), (n, len(kod)))
    return float((top[sec].sum(1) / ad[sec].sum(1) > 0).mean())


def kilit_tetigi(x: pd.DataFrame, B: pd.DataFrame) -> dict:
    """Kazananlar: girişten çıkışa MFE ($); kaybedenler (tam −40): girişten stopa kadar MFE — kilit tetiği L, kaybedenlerin MFE'sinin
    üstünde, kilitli kazananların MFE'sinin altında olmalı."""
    t = B.t.to_numpy()
    o, h, l = B.open.to_numpy(), B.high.to_numpy(), B.low.to_numpy()
    mfe = []
    for _, r in x.iterrows():
        i, j = np.searchsorted(t, r.u // 60 * 60), np.searchsorted(t, r.u_kap // 60 * 60)
        if j <= i:
            mfe.append(np.nan)
            continue
        hi, lo = h[i:j + 1].max(), l[i:j + 1].min()
        mfe.append((hi - r.px_ac) if r.yon > 0 else (r.px_ac - lo))
    x = x.assign(mfe=mfe)
    kil = x[(x.net > 0) & (x.yorum == "[sl]")]
    tam = x[x.hareket < -35]
    return {"kilitli_kazanan_MFE_$": kil.mfe.quantile([0, .05, .25, .5]).round(2).tolist(),
            "tam_kayip_MFE_$": tam.mfe.quantile([.5, .75, .95, 1]).round(2).tolist(),
            "TP_vuran_n": int((x.hareket > 23).sum())}, x


def kopya(x: pd.DataFrame, B: pd.DataFrame) -> dict:
    t, o, sp = B.t.to_numpy(), B.open.to_numpy(), B.sp.to_numpy()

    def ret(u0, u1, y):
        i = np.searchsorted(t, u0 // 60 * 60 + 60)
        j = np.maximum(np.searchsorted(t, u1 // 60 * 60 + 60), i + 1)
        i, j = np.minimum(i, len(t) - 1), np.minimum(j, len(t) - 1)
        e = np.where(y > 0, o[i] + sp[i], o[i])
        c = np.where(y > 0, o[j], o[j] + sp[j])
        return y * (c - e) / o[i] * 1e4
    y = x.yon.to_numpy()
    u0, u1 = x.u.to_numpy(), x.u_kap.to_numpy()
    k = ret(u0, u1, y)
    rng = np.random.default_rng(TOHUM)
    z = pd.to_datetime(u0, unit="s", utc=True)
    pzt = (z.normalize() - pd.to_timedelta(z.weekday, unit="D")).astype("int64").to_numpy() // 10**9
    pl = np.mean([ret(pzt + rng.integers(0, 5, len(u0)) * 86400 + z.hour.to_numpy() * 3600,
                      pzt + rng.integers(0, 5, len(u0)) * 86400 + z.hour.to_numpy() * 3600 + (u1 - u0), y, ) for _ in range(5)], axis=0)
    gun = u0 // 86400
    kendi = y * (x.px_kap - x.px_ac).to_numpy() / x.px_ac.to_numpy() * 1e4
    return {"n": len(k), "saglayici_bp": round(float(kendi.mean()), 2), "kopya_bp": round(float(k.mean()), 2),
            "plasebo_bp": round(float(pl.mean()), 2), "fark_bp": round(float((k - pl).mean()), 2), "fark_P": round(gun_P(k - pl, gun), 4),
            "kopya_P": round(gun_P(k, gun), 4), "ters_bp": round(float(ret(u0, u1, -y).mean()), 2)}


# ───────────── MG-3 ─────────────
def kural_ates(F: pd.DataFrame, a: float, b: float, c: float) -> tuple[np.ndarray, np.ndarray]:
    d = np.sign(F.r12_atr.to_numpy())
    kz = np.where(d > 0, F.konum24, 1 - F.konum24)
    ok = (F.gecerli.to_numpy() & (F.gun.to_numpy() < 5) & (d * F.r12_atr >= a).to_numpy() & (F.r4_atr.abs() <= b).to_numpy()
          & (d * F.fiyat_ema50_atr >= c).to_numpy() & (kz >= 0.55) & (kz <= 0.95))
    return ok, d


@njit(cache=True)
def _sim(t, o, h, l, sp, ii, yy, tp_bp, sl_bp, kilit_L, kilit_s, T, spk):
    n, m = len(t), len(ii)
    R = np.full(m, np.nan)
    t0 = np.zeros(m, np.int64)
    serbest = -1
    for k in range(m):
        e = ii[k]
        if e >= n - 1 or e <= serbest:
            continue
        y = yy[k]
        E = o[e] + sp[e] * spk if y > 0 else o[e]
        tp, sl = E * tp_bp / 1e4, E * sl_bp / 1e4
        L, ks = E * kilit_L / 1e4, E * kilit_s / 1e4
        TP, S = E + y * tp, E - y * sl
        kilitli = False
        px, j = np.nan, e
        while j < n - 1:
            sj = sp[j] * spk
            if j > e and t[j] - t[e] >= T * 60:
                px = o[j] if y > 0 else o[j] + sj
                break
            if y > 0:
                if l[j] <= S:
                    px = min(o[j], S)
                    break
                if h[j] >= TP:
                    px = TP
                    break
                fav = h[j] - E
            else:
                if h[j] + sj >= S:
                    px = max(o[j] + sj, S)
                    break
                if l[j] + sj <= TP:
                    px = TP
                    break
                fav = E - (l[j] + sj)
            if (not kilitli) and fav >= L:                     # kilit sonraki bardan geçerli
                S = E + y * ks
                kilitli = True
            j += 1
        if np.isnan(px):
            continue
        R[k] = y * (px - E) / sl
        t0[k] = t[e]
        serbest = j
    return R, t0


def main() -> None:
    x = V.islemler()
    B = V.xau_1m()
    sys.path.insert(0, str(KOK.parents[1] / "yeni deneme"))
    import broker_time as bt
    srv = (x.t_ac.astype("int64") // 10**9).to_numpy()
    x["u"] = srv - np.array([bt.rule_offset_sec(int(s)) for s in srv])
    sk = (x.t_kap.astype("int64") // 10**9).to_numpy()
    x["u_kap"] = sk - np.array([bt.rule_offset_sec(int(s)) for s in sk])
    out = {}
    out["kilit"], x = kilit_tetigi(x, B)
    print("KİLİT", out["kilit"])
    out["kopya"] = kopya(x, B)
    print("KOPYA", out["kopya"])
    H = A.h1(B)
    saat = H.kova.to_numpy()[300:] + 1
    F = A.karar_ozellik(H, saat)
    F["u"] = saat * 3600
    hesap_d = (F.u >= x.u.min() - 3600) & (F.u <= x.u.max() + 3600)
    giris = set((x.u // 3600).tolist())
    yon = dict(zip((x.u // 3600).tolist(), x.yon.tolist()))
    en = None
    izg = []
    for a in (1.0, 1.5, 2.0):
        for b in (0.5, 1.0):
            for c in (0.5, 1.0):
                ok, d = kural_ates(F, a, b, c)
                at = set((F.u[ok & hesap_d.to_numpy()] // 3600).tolist())
                es = {s for s in giris if any(abs(s - q) <= 1 for q in (s - 1, s, s + 1) if q in at)}
                yon_ok = np.mean([d[np.flatnonzero((F.u // 3600).to_numpy() == s)[0]] == yon[s] for s in es]) if es else 0
                kesin = len(es) / max(len(at), 1)
                duy = len(es) / len(giris)
                f1 = 2 * kesin * duy / max(kesin + duy, 1e-9)
                izg.append({"a": a, "b": b, "c": c, "ates_hesap_donemi": len(at), "duyarlilik": round(duy, 3), "kesinlik": round(kesin, 3),
                            "F1": round(f1, 3), "yon_uyumu": round(float(yon_ok), 3)})
                if en is None or f1 > en["F1"]:
                    en = izg[-1]
    out["izgara"], out["secilen"] = izg, en
    print("SEÇİLEN", en)
    # kilit tetiği L: kilitli kazananların MFE'sinin 5. yüzdeliği (bp) — kilit eşiği bunun altında
    L_dolar = out["kilit"]["kilitli_kazanan_MFE_$"][1]
    px_ref = float(x.px_ac.median())
    tp_bp, sl_bp, ks_bp, L_bp = 25 / px_ref * 1e4, 40 / px_ref * 1e4, 16 / px_ref * 1e4, L_dolar / px_ref * 1e4
    out["geometri_bp"] = {"tp": round(tp_bp, 1), "sl": round(sl_bp, 1), "kilit_tetik": round(L_bp, 1), "kilit_stop": round(ks_bp, 1)}
    print("GEOMETRİ", out["geometri_bp"])
    t, o, h, l, sp = (B[k].to_numpy() for k in ("t", "open", "high", "low", "sp"))
    ok, d = kural_ates(F, en["a"], en["b"], en["c"])

    def kos(maske, dd, spk=1.0, ii=None):
        if ii is None:
            ii = np.searchsorted(t, F.u.to_numpy()[maske])
        R, t0 = _sim(t, o, h, l, sp, ii.astype(np.int64), dd.astype(np.int64), tp_bp, sl_bp, L_bp, ks_bp, 4000.0, spk)
        m = t0 > 0
        return pd.DataFrame({"t0": t0[m], "R": R[m], "y": dd[m]})
    for ad, (a_, b_) in {"BAGIMSIZ_2018_2026-05": ("2018-01-01", "2026-05-18"), "HESAP_DONEMI": ("2026-05-18", "2026-11-25")}.items():
        donem = ((F.u >= pd.Timestamp(a_, tz="UTC").timestamp()) & (F.u < pd.Timestamp(b_, tz="UTC").timestamp())).to_numpy()
        m = ok & donem
        r = kos(m, d[m])
        s = kos(m, d[m], 1.5)
        # plasebo: aynı yıl × UTC saati, aynı yön
        rng = np.random.default_rng(TOHUM)
        Fd = F[donem & F.gecerli.to_numpy() & (F.gun.to_numpy() < 5)]
        anah = pd.to_datetime(Fd.u, unit="s").dt.year.to_numpy() * 100 + Fd.saat_utc.to_numpy()
        q = pd.to_datetime(r.t0, unit="s").dt.year.to_numpy() * 100 + pd.to_datetime(r.t0, unit="s").dt.hour.to_numpy()
        pl = []
        for _ in range(5):
            jj = np.array([rng.choice(np.flatnonzero(anah == k)) if (anah == k).any() else 0 for k in q])
            ii = np.searchsorted(t, Fd.u.to_numpy()[jj])
            pr, pt = _sim(t, o, h, l, sp, ii.astype(np.int64), r.y.to_numpy().astype(np.int64), tp_bp, sl_bp, L_bp, ks_bp, 4000.0, 1.0)
            pl.append(np.resize(pr[pt > 0], len(r)))
        x_, gun = r.R.to_numpy(), r.t0.to_numpy() // 86400
        f = x_ - np.mean(pl, axis=0)
        gt = pd.Series(x_).groupby(gun).sum()
        yari = len(x_) // 2
        res = {"n": len(x_), "ayda": round(len(x_) / max(1, (pd.Timestamp(b_) - pd.Timestamp(a_)).days / 30.44), 1),
               "ort_R": round(float(x_.mean()), 4), "isabet": round(float((x_ > 0).mean()), 3), "P_EV": round(gun_P(x_, gun), 4),
               "yarilar": [round(float(x_[:yari].mean()), 4), round(float(x_[yari:].mean()), 4)], "stres_R": round(float(s.R.mean()), 4),
               "plasebo_R": round(float(np.mean(pl)), 4), "fark_R": round(float(f.mean()), 4), "fark_P": round(gun_P(f, gun), 4),
               "en_iyi10_haric": round(float((gt.sum() - gt.nlargest(10).sum()) / len(x_)), 4),
               "yillik_R": {int(k): round(float(v), 4) for k, v in r.groupby(pd.to_datetime(r.t0, unit="s").dt.year).R.mean().items()},
               "AL_R": round(float(r.R[r.y > 0].mean()), 4), "SAT_R": round(float(r.R[r.y < 0].mean()), 4)}
        if ad.startswith("BAGIMSIZ"):
            res["hukum"] = "B" if (res["n"] >= 150 and res["ort_R"] > 0 and res["P_EV"] >= 0.95 and min(res["yarilar"]) > 0 and res["stres_R"] > 0
                                   and res["fark_R"] > 0 and res["fark_P"] >= 0.95 and res["en_iyi10_haric"] > 0
                                   and all(res["yillik_R"].get(yy, -1) > 0 for yy in (2022, 2023, 2024, 2025))) else "X"
        out[ad] = res
        print(ad, res)
    (KOK / "results/mg23.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
