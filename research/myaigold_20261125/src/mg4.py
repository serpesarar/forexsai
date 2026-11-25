"""MG-4 — My AI Gold kuralının geliştirilmesi (PROTOCOL MG-4). Kullanım: python src/mg4.py ASAMA1 | ASAMA2 | TEST ad1,ad2,ad3"""
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
R = KOK / "results"
TOHUM = 20261125
DONEM = {"KESIF": ("2018-01-01", "2022-01-01"), "TEST": ("2022-01-01", "2026-05-18"), "KOR": ("2026-05-18", "2026-11-25")}
BP_GEOM = {"tp": 59.2, "sl": 94.7, "L": 38.2, "ks": 37.9}
YOGUN_SAAT = (7, 8, 12, 15, 20, 22)
T_DK = 4000.0
_CACHE: dict = {}


def hazirla() -> dict:
    if _CACHE:
        return _CACHE
    B = V.xau_1m()
    H = A.h1(B)
    saat = H.kova.to_numpy()[300:] + 1
    F = A.karar_ozellik(H, saat)
    F["u"] = saat * 3600
    F["ema200_y"] = np.sign(F.c - F.ema200)
    F["yil"] = pd.to_datetime(F.u, unit="s").dt.year
    F = F[F.gecerli & (F.gun < 5)].reset_index(drop=True)
    t = B.t.to_numpy()
    F["ii"] = np.searchsorted(t, F.u.to_numpy())
    F = F[F.ii < len(t) - 2].reset_index(drop=True)
    _CACHE.update({"B": B, "F": F, "t": t, "o": B.open.to_numpy(), "h": B.high.to_numpy(), "l": B.low.to_numpy(), "sp": B.sp.to_numpy()})
    return _CACHE


def sinyal(F: pd.DataFrame, c: dict) -> tuple[np.ndarray, np.ndarray]:
    d12, d24 = np.sign(F.r12_atr.to_numpy()), np.sign(F.r24_atr.to_numpy())
    d = d12.copy()
    ok = np.ones(len(F), bool)
    if c["mod"] == "T12T24":
        ok &= d12 == d24
    elif c["mod"] == "AL":
        ok &= d12 > 0
    elif c["mod"] == "D200":
        ok &= F.ema200_y.to_numpy() == d12
    uz = d * F.fiyat_ema50_atr.to_numpy()
    kz = np.where(d > 0, F.konum24, 1 - F.konum24)
    ok &= (d * F.r12_atr.to_numpy() >= c["a"]) & (np.abs(F.r4_atr.to_numpy()) <= c["b"]) & (uz >= 1.0) & (uz <= c["uz"])
    ok &= (kz >= 0.55) & (kz <= c["kz"])
    if c["saat"] == "yogun":
        ok &= np.isin(F.saat_utc.to_numpy(), YOGUN_SAAT)
    return ok, d


@njit(cache=True)
def _sim(t, o, h, l, sp, ii, yy, tp, sl, L, ks, T, spk, kom, tek):
    n, m = len(t), len(ii)
    Rr = np.full(m, np.nan)
    t0 = np.zeros(m, np.int64)
    serbest = -1
    for k in range(m):
        e = ii[k]
        if e >= n - 1 or (tek and e <= serbest):
            continue
        y = yy[k]
        E = o[e] + sp[e] * spk if y > 0 else o[e]
        TP, S = E + y * tp[k], E - y * sl[k]
        kilitli = not np.isfinite(L[k])
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
            if (not kilitli) and fav >= L[k]:
                S = E + y * ks[k]
                kilitli = True
            j += 1
        if np.isnan(px):
            continue
        Rr[k] = (y * (px - E) - kom) / sl[k]
        t0[k] = t[e]
        serbest = j
    return Rr, t0


def geometri(D: dict, idx: np.ndarray, c: dict) -> tuple[np.ndarray, ...]:
    F = D["F"]
    px = D["o"][F.ii.to_numpy()[idx]]
    if c.get("cikis", "bp") == "bp":
        g = BP_GEOM
        return px * g["tp"] / 1e4, px * g["sl"] / 1e4, px * g["L"] / 1e4, px * g["ks"] / 1e4
    atr = F.atr.to_numpy()[idx]
    tp, sl = c["tp"] * atr, c["sl"] * atr
    if c["kilit"]:
        return tp, sl, 0.6 * tp, 0.5 * tp
    return tp, sl, np.full(len(idx), np.inf), np.zeros(len(idx))


def kos(D: dict, idx: np.ndarray, yy: np.ndarray, c: dict, spk: float = 1.0, tek: bool = True, kom: float = 0.08) -> pd.DataFrame:
    tp, sl, L, ks = geometri(D, idx, c)
    ii = D["F"].ii.to_numpy()[idx]
    Rr, t0 = _sim(D["t"], D["o"], D["h"], D["l"], D["sp"], ii.astype(np.int64), yy.astype(np.int64), tp, sl, L, ks, T_DK, spk, kom, tek)
    m = t0 > 0
    assert np.isfinite(Rr[m]).all(), "NaN (E154)"
    F = D["F"]
    return pd.DataFrame({"t0": t0[m], "R": Rr[m], "y": yy[m], "yil": F.yil.to_numpy()[idx][m], "saat": F.saat_utc.to_numpy()[idx][m]})


def gun_P(x, gun, n=3000):
    if len(x) < 3:
        return float("nan")
    kod, ters = np.unique(gun, return_inverse=True)
    top, ad = np.bincount(ters, weights=x), np.bincount(ters).astype(float)
    sec = np.random.default_rng(TOHUM).integers(0, len(kod), (n, len(kod)))
    return float((top[sec].sum(1) / ad[sec].sum(1) > 0).mean())


def olc(D: dict, c: dict, a: str, b: str, ek: bool = False) -> dict:
    F = D["F"]
    ok, d = sinyal(F, c)
    don = ((F.u >= pd.Timestamp(a, tz="UTC").timestamp()) & (F.u < pd.Timestamp(b, tz="UTC").timestamp())).to_numpy()
    idx = np.flatnonzero(ok & don)
    r = kos(D, idx, d[idx], c)
    if len(r) < 10:
        return {"n": len(r)}
    s = kos(D, idx, d[idx], c, spk=1.5)
    # plasebo: aynı yıl × UTC saati, aynı yön, aynı geometri tanımı (×5), dönem içi tüm geçerli saat başları
    pool = np.flatnonzero(don)
    anah = F.yil.to_numpy()[pool] * 100 + F.saat_utc.to_numpy()[pool]
    sira = np.argsort(anah, kind="stable")
    sk = anah[sira]
    q = r.yil.to_numpy() * 100 + r.saat.to_numpy()
    lo, hi = np.searchsorted(sk, q, "left"), np.searchsorted(sk, q, "right")
    rng = np.random.default_rng(TOHUM)
    pl = []
    for _ in range(5):
        jj = pool[sira[lo + (rng.random(len(r)) * np.maximum(hi - lo, 1)).astype(int)]]
        pl.append(np.resize(kos(D, jj, r.y.to_numpy(), c, tek=False).R.to_numpy(), len(r)))
    x, gun = r.R.to_numpy(), r.t0.to_numpy() // 86400
    f = x - np.mean(pl, axis=0)
    gt = pd.Series(x).groupby(gun).sum()
    yari = len(x) // 2
    ay = (pd.Timestamp(b) - pd.Timestamp(a)).days / 30.44
    bd = pd.bdate_range(pd.Timestamp(a), pd.Timestamp(b))
    g = pd.Series(x).groupby(gun).sum().reindex(bd.asi8 // 10**9 // 86400, fill_value=0.0)
    out = {"n": len(x), "ayda": round(len(x) / ay, 1), "ort_R": round(float(x.mean()), 4), "aylik_R": round(float(x.sum() / ay), 3),
           "isabet": round(float((x > 0).mean()), 3), "P_EV": round(gun_P(x, gun), 4), "yari1": round(float(x[:yari].mean()), 4),
           "yari2": round(float(x[yari:].mean()), 4), "stres_R": round(float(s.R.mean()), 4), "plasebo_R": round(float(np.mean(pl)), 4),
           "fark_R": round(float(f.mean()), 4), "fark_P": round(gun_P(f, gun), 4),
           "en_iyi10_haric": round(float((gt.sum() - gt.nlargest(10).sum()) / len(x)), 4),
           "sharpe": round(float(g.mean() / g.std() * np.sqrt(252)), 3) if g.std() > 0 else 0.0,
           "AL_R": round(float(r.R[r.y > 0].mean()), 4) if (r.y > 0).any() else None,
           "SAT_R": round(float(r.R[r.y < 0].mean()), 4) if (r.y < 0).any() else None,
           "yillik_R": {int(k): round(float(v), 4) for k, v in r.groupby("yil").R.mean().items()}}
    if ek:
        out["iyimser_R"] = round(float(kos(D, idx, d[idx], c, spk=0.0, kom=0.0).R.mean()), 4)
    return out


def gecer(h: dict) -> bool:
    return (h.get("n", 0) >= 150 and h["ort_R"] > 0 and h["P_EV"] >= 0.95 and h["yari1"] > 0 and h["yari2"] > 0 and h["stres_R"] > 0
            and h["fark_R"] > 0 and h["fark_P"] >= 0.95 and h["en_iyi10_haric"] > 0)


def asama1_hucre() -> list[dict]:
    H = [{"ad": "TABAN", "mod": "T12", "a": 2.0, "b": 0.5, "uz": np.inf, "kz": 0.95, "saat": "tum"}]
    for mod in ("T12", "T12T24", "AL", "D200"):
        for a in (1.0, 1.5, 2.0):
            for b in (0.5, 1.0):
                for uz in (np.inf, 2.0):
                    for kz in (0.95, 0.80):
                        for saat in ("tum", "yogun"):
                            H.append({"ad": f"{mod}_a{a}_b{b}_uz{'inf' if uz == np.inf else uz}_kz{kz}_{saat}", "mod": mod, "a": a, "b": b,
                                      "uz": uz, "kz": kz, "saat": saat})
    return H


def asama2_hucre(girisler: list[dict]) -> list[dict]:
    out = []
    for g in girisler:
        for tp in (1.0, 1.5, 2.0):
            for sl in (1.5, 2.2, 3.0):
                for kil in (False, True):
                    out.append({**g, "ad": f"{g['ad']}__tp{tp}_sl{sl}_{'kilit' if kil else 'yok'}", "cikis": "atr", "tp": tp, "sl": sl,
                                "kilit": kil})
    return out


KOL = ("n", "ayda", "ort_R", "aylik_R", "isabet", "P_EV", "yari1", "yari2", "stres_R", "plasebo_R", "fark_R", "fark_P", "en_iyi10_haric",
       "sharpe", "AL_R", "SAT_R")


def tara(hucreler: list[dict], dosya: str) -> dict:
    D = hazirla()
    out = {}
    for c in hucreler:
        h = olc(D, c, *DONEM["KESIF"])
        out[c["ad"]] = {"tanim": {k: (None if v == np.inf else v) for k, v in c.items()}, **h}
    gec = sorted([k for k, v in out.items() if gecer(v)], key=lambda k: (-out[k]["aylik_R"], -out[k]["sharpe"]))
    out["_gecen"] = gec
    (R / f"{dosya}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    pd.DataFrame([{"ad": k, **{x: v.get(x) for x in KOL}} for k, v in out.items() if not k.startswith("_")]).sort_values(
        "aylik_R", ascending=False).to_csv(R / f"{dosya}.csv", index=False)
    print(dosya, "geçen", len(gec), gec[:6], flush=True)
    return out


def tanim_bul(ad: str) -> dict:
    for dosya in ("mg4_asama1", "mg4_asama2"):
        p = R / f"{dosya}.json"
        if p.exists():
            j = json.loads(p.read_text())
            if ad in j:
                t = j[ad]["tanim"]
                t["uz"] = np.inf if t.get("uz") is None else t["uz"]
                return t
    raise KeyError(ad)


def test(adlar: list[str]) -> None:
    D = hazirla()
    out = {}
    for ad in adlar:
        c = tanim_bul(ad)
        h = olc(D, c, *DONEM["TEST"], ek=True)
        h["kontrol"] = {"kesif_olcutleri": gecer(h), "2022_25_her_yil": all(h["yillik_R"].get(y, -1) > 0 for y in (2022, 2023, 2024, 2025)),
                        "icra": h["iyimser_R"] - h["ort_R"] <= h["ort_R"] / 2}
        h["hukum"] = "B" if all(h["kontrol"].values()) else "X"
        h["kor_2026_05_11"] = olc(D, c, *DONEM["KOR"])
        h["kesif"] = olc(D, c, *DONEM["KESIF"])
        out[ad] = h
        print(ad, h["hukum"], h["kontrol"], {k: h.get(k) for k in KOL + ("yillik_R", "iyimser_R")}, flush=True)
        print("   KÖR", {k: h["kor_2026_05_11"].get(k) for k in ("n", "ort_R", "isabet", "aylik_R")}, flush=True)
    (R / "mg4_test.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    if sys.argv[1] == "ASAMA1":
        tara(asama1_hucre(), "mg4_asama1")
    elif sys.argv[1] == "ASAMA2":
        j = json.loads((R / "mg4_asama1.json").read_text())
        en = [j[k]["tanim"] for k in j["_gecen"][:3]]
        for g in en:
            g["uz"] = np.inf if g.get("uz") is None else g["uz"]
        tara(asama2_hucre(en), "mg4_asama2") if en else print("Aşama 1'de geçen yok → Aşama 2 yok")
    else:
        test(sys.argv[2].split(","))
