"""TS — saniye ölçeğinde XAU strateji motoru (PROTOCOL.md). Kullanım: python src/ts.py KESIF | TEST ad1,ad2"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK.parents[1] / "yeni deneme"))
import broker_time as bt  # noqa: E402

VERI = KOK / "data" / "XAUUSD"
DONEM = {"KESIF": ("2026-09-01", "2026-10-21"), "TEST": ("2026-10-21", "2026-11-26")}
KOM = 0.07
LAT_MS = 1000
TOHUM = 20261125


def gun_yukle(f: Path) -> dict | None:
    d = pd.read_csv(f, usecols=[0, 1, 2])
    if len(d) < 1000:
        return None
    s = d.time_msc.to_numpy(np.int64)
    h = s // 3_600_000
    u, inv = np.unique(h, return_inverse=True)
    off = np.array([bt.rule_offset_sec(int(x) * 3600) for x in u], np.int64) * 1000
    t = s - off[inv]
    o = np.argsort(t, kind="stable")
    t, bid, ask = t[o], d.bid.to_numpy()[o], d.ask.to_numpy()[o]
    ok = (bid > 0) & (ask >= bid)
    t, bid, ask = t[ok], bid[ok], ask[ok]
    return {"gun": f.name[:10], "t": t, "bid": bid, "ask": ask, "mid": (bid + ask) / 2}


def gunler(a: str, b: str) -> list[dict]:
    out = []
    for f in sorted(VERI.glob("*.csv.gz")):
        if a <= f.name[:10] < b:
            g = gun_yukle(f)
            if g:
                out.append(g)
    return out


def gecmis(t: np.ndarray, x: np.ndarray, ms: int) -> np.ndarray:
    j = np.searchsorted(t, t - ms, "left")
    return x[j]


@njit(cache=True)
def _sim(t, bid, ask, ii, yy, tp, sl, T_ms, lat_ms, kom):
    n, m = len(t), len(ii)
    pnl = np.full(m, np.nan)
    serbest = -1
    for k in range(m):
        i = ii[k]
        if t[i] <= serbest:
            continue
        e = i
        while e < n and t[e] < t[i] + lat_ms:
            e += 1
        if e >= n - 1:
            break
        y = yy[k]
        E = ask[e] if y > 0 else bid[e]
        j = e + 1
        px = np.nan
        while j < n:
            c = bid[j] if y > 0 else ask[j]
            g = y * (c - E)
            if g >= tp or g <= -sl or t[j] - t[e] >= T_ms:
                px = c
                break
            j += 1
        if np.isnan(px):
            break
        pnl[k] = y * (px - E) - kom
        serbest = t[j]
    return pnl


def tetik(g: dict, c: dict) -> tuple[np.ndarray, np.ndarray]:
    t, mid = g["t"], g["mid"]
    if c["aile"] in ("A", "B"):
        dW = mid - gecmis(t, mid, c["W"] * 1000)
        d180 = mid - gecmis(t, mid, 180_000)
        y = np.sign(dW)
        ok = (np.abs(dW) >= c["k"]) & (t - t[0] >= 180_000) & (y * d180 >= c["trend"])
        if c["aile"] == "B":
            y = -y
    else:
        n = np.arange(len(t))
        n10 = n - np.searchsorted(t, t - 10_000, "left")
        n600 = n - np.searchsorted(t, t - 600_000, "left")
        oran = n10 / np.maximum((n600 - n10) / 59.0, 1e-9)
        j5 = np.searchsorted(t, t - 300_000, "left")
        hh = _pencere_uc(mid, j5, n, 1)                    # [t−5 dk, şimdiki tick) — şimdiki hariç
        ll = _pencere_uc(mid, j5, n, -1)
        y = np.where(mid > hh, 1, np.where(mid < ll, -1, 0))
        ok = (oran >= c["m"]) & (y != 0) & (t - t[0] >= 600_000)
    i = np.flatnonzero(ok)
    return i, y[i].astype(np.int64)


@njit(cache=True)
def _pencere_uc(x, a, b, isaret):
    """[a_i, b_i) penceresinin en büyük (isaret=1) / en küçük (−1) değeri — monoton deque, O(n)."""
    n = len(x)
    out = np.full(n, np.nan)
    dq = np.empty(n, np.int64)
    bas, son = 0, 0
    sag = 0
    for i in range(n):
        while sag < b[i]:
            v = x[sag] * isaret
            while son > bas and x[dq[son - 1]] * isaret <= v:
                son -= 1
            dq[son] = sag
            son += 1
            sag += 1
        while son > bas and dq[bas] < a[i]:
            bas += 1
        if son > bas:
            out[i] = x[dq[bas]]
    return out


def hucreler() -> list[dict]:
    H = []
    for aile in ("A", "B"):
        for W in (2, 5, 10):
            for k in (1.0, 1.5, 2.0):
                for tr in (0.0, 4.0):
                    for tp in (0.5, 1.0, 2.0):
                        for sl in (1.5, 3.0):
                            for T in (15, 60):
                                H.append({"ad": f"{aile}_W{W}_k{k}_tr{tr}_tp{tp}_sl{sl}_T{T}", "aile": aile, "W": W, "k": k, "trend": tr,
                                          "tp": tp, "sl": sl, "T": T})
    for m in (3, 5):
        for tp in (0.5, 1.0, 2.0):
            for sl in (1.5, 3.0):
                for T in (15, 60):
                    H.append({"ad": f"C_m{m}_tp{tp}_sl{sl}_T{T}", "aile": "C", "m": m, "tp": tp, "sl": sl, "T": T})
    return H


def kos(G: list[dict], c: dict, lat: int = LAT_MS, cache: dict | None = None) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(TOHUM)
    for g in G:
        key = (g["gun"], c["aile"], c.get("W"), c.get("k"), c.get("trend"), c.get("m"))
        if cache is not None and key in cache:
            i, y = cache[key]
        else:
            i, y = tetik(g, c)
            if cache is not None:
                cache[key] = (i, y)
        if not len(i):
            continue
        p = _sim(g["t"], g["bid"], g["ask"], i, y, c["tp"], c["sl"], c["T"] * 1000, lat, KOM)
        m = np.isfinite(p)
        if not m.any():
            continue
        # plasebo: aynı UTC saatinde rastgele tick, aynı yön (işlem başına bir)
        saat = (g["t"] // 3_600_000)
        si = i[m]
        lo = np.searchsorted(saat, saat[si], "left")              # t sıralı → saat dilimleri bitişik
        hi = np.searchsorted(saat, saat[si], "right")
        pl_i = lo + (rng.random(len(si)) * (hi - lo)).astype(np.int64)
        o = np.argsort(pl_i)
        pp = _sim(g["t"], g["bid"], g["ask"], pl_i[o].astype(np.int64), y[m][o], c["tp"], c["sl"], c["T"] * 1000, lat, KOM)
        plv = np.full(len(si), np.nan)
        plv[o] = pp
        rows.append(pd.DataFrame({"gun": g["gun"], "t": g["t"][si], "pnl": p[m], "plasebo": plv}))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["gun", "t", "pnl", "plasebo"])


def gun_P(x, gun, n=3000):
    if len(x) < 3:
        return float("nan")
    kod, ters = np.unique(gun, return_inverse=True)
    top, ad = np.bincount(ters, weights=x), np.bincount(ters).astype(float)
    sc = np.random.default_rng(TOHUM).integers(0, len(kod), (n, len(kod)))
    return float((top[sc].sum(1) / ad[sc].sum(1) > 0).mean())


def ozet(r: pd.DataFrame, n_gun: int) -> dict:
    if len(r) < 5:
        return {"n": len(r)}
    x, gun = r.pnl.to_numpy(), r.gun.to_numpy()
    f = x - np.nan_to_num(r.plasebo.to_numpy())
    yari = len(x) // 2
    return {"n": len(x), "gunde": round(len(x) / max(n_gun, 1), 1), "ort_$": round(float(x.mean()), 4), "isabet": round(float((x > 0).mean()), 3),
            "P": round(gun_P(x, gun), 4), "yari1": round(float(x[:yari].mean()), 4), "yari2": round(float(x[yari:].mean()), 4),
            "plasebo_$": round(float(np.nanmean(r.plasebo)), 4), "fark_$": round(float(np.nanmean(f)), 4), "fark_P": round(gun_P(f, gun), 4),
            "gunluk_$": round(float(x.sum() / max(n_gun, 1)), 3)}


def gecer(h: dict) -> bool:
    return (h.get("n", 0) >= 200 and h["ort_$"] > 0 and h["P"] >= 0.95 and h["yari1"] > 0 and h["yari2"] > 0 and h["fark_$"] > 0
            and h["fark_P"] >= 0.95)


def kesif() -> None:
    G = gunler(*DONEM["KESIF"])
    print("KEŞİF gün", len(G), "tick", sum(len(g["t"]) for g in G), flush=True)
    cache: dict = {}
    out = {}
    for c in hucreler():
        h = ozet(kos(G, c, cache=cache), len(G))
        out[c["ad"]] = {"tanim": c, **h}
    df = pd.DataFrame([{"ad": k, **{x: v.get(x) for x in ("n", "gunde", "ort_$", "isabet", "P", "yari1", "yari2", "plasebo_$", "fark_$", "fark_P",
                                                          "gunluk_$")}} for k, v in out.items()])
    df.to_csv(KOK / "results/ts_kesif.csv", index=False)
    aday = {}
    for aile in ("A", "B", "C"):
        g = [k for k, v in out.items() if v["tanim"]["aile"] == aile and gecer(v)]
        g.sort(key=lambda k: -out[k]["gunluk_$"])
        aday[aile] = g[:1]
        print(aile, "geçen", len(g), g[:5], flush=True)
    out["_aday"] = aday
    (KOK / "results/ts_kesif.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for aile in ("A", "B", "C"):
        s = df[df.ad.str.startswith(aile)].sort_values("ort_$", ascending=False).head(4)
        print(s.to_string(index=False), flush=True)


def test(adlar: list[str]) -> None:
    G = gunler(*DONEM["TEST"])
    j = json.loads((KOK / "results/ts_kesif.json").read_text())
    out = {}
    for ad in adlar:
        c = j[ad]["tanim"]
        h = ozet(kos(G, c), len(G))
        h["gecikme_500"] = ozet(kos(G, c, 500), len(G))["ort_$"]
        h["gecikme_2000"] = ozet(kos(G, c, 2000), len(G))["ort_$"]
        h["hukum"] = "GÖLGE adayı" if (h["ort_$"] > 0 and h["P"] >= 0.90 and h["fark_$"] > 0 and h["gecikme_2000"] > 0) else "X"
        out[ad] = h
        print(ad, h, flush=True)
    (KOK / "results/ts_test.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    kesif() if sys.argv[1] == "KESIF" else test(sys.argv[2].split(","))
