"""Pin bar @tepe → TERS (BUY), 20 mum tut — derin sınama (2026-10-10). ÖN KAYIT (sonuçlara bakmadan):

Kural (MK-01): mumun yükseği önceki 20 mumun en yükseğine ≥, üst fitil ≥ 2/3 aralık → sonraki mum açılışında BUY,
20 mum sonra kapanışta çık. Maliyet: sembol spread'i / ATR. Birim: ATR (R).
Testler (hepsi raporlanır, hiçbiri sonuca göre seçilmez):
  T1 Taban farkı: her veri setinde ort.R − (aynı TF'de tüm mumlarda BUY T20) ve PF. Bağımsız ek set: NDX 1h 2016→2026-07.
  T2 Tek pozisyon: TF içinde çakışan işlemler atlanır (20 mum meşgul).
  T3 Yıl yıl (havuz), en iyi 5 / 10 gün çıkınca toplam.
  T4 Parametre komşuluğu: fitil {0,5 0,6 0,67 0,75} × pencere {10 20 40} × tutma {10 15 20 30 40} — NDX 15m/30m/1h, DAX 30m.
     Gerçek kenar komşulukta düzgün olmalı (tek tepe değil).
  T5 Mekanizma: (a) 20 mumluk yeni tepe yapan TÜM mumlar BUY T20, (b) yeni tepe + üst fitil < 1/3 (güçlü kapanış),
     (c) pin bar. Pin bar (a)/(b)'den belirgin iyi değilse kenar "tepede al" (momentum), pin bar değil.
  T6 M1 katı icra (NDX 5m/15m/30m, M1 olan dönem): giriş = TF mumu kapanışından sonraki ilk M1 açılışı + spread,
     çıkış = 20 TF-mumu sonraki M1 kapanışı; bar-bazlı sonuçla fark.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/ndx_gate_forge"))
import importlib.util as _u  # noqa: E402
_spec = _u.spec_from_file_location("mum_scan", ROOT / "research/mum_kural_20261009/scan.py")
S = _u.module_from_spec(_spec)
_spec.loader.exec_module(S)          # gate_forge/scan.py ile ad çakışmasın

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)


def ndx_1h() -> pd.DataFrame:
    from long_data import load_long
    d = load_long("1h")[["ts", "open", "high", "low", "close"]].copy()
    d["seg"] = (d.ts.diff() > pd.Timedelta(days=4)).cumsum()
    return d.reset_index(drop=True)


def datasets() -> dict[str, tuple[dict, float]]:
    """ad → (özellikler, spread). NDX keşif+kasa birlikte (tam dönem) + NDX 1h + DAX."""
    ds = {}
    for tf in ("5m", "15m", "30m"):
        ds[f"NDX {tf}"] = (S.features(S.load(S.NDX / f"bars_{tf}.parquet")), 1.5)
    ds["NDX 1h (10y)"] = (S.features(ndx_1h()), 1.5)
    for tf, F in S.dax_sets().items():
        ds[f"DAX {tf}"] = (F, 1.5)
    return ds


def pin_mask(F: dict, wick: float = 2 / 3, look: int = 20, kind: str = "pin") -> np.ndarray:
    h, l, o, c = F["h"], F["l"], F["o"], F["c"]
    hi = pd.Series(h).shift(1).rolling(look).max().to_numpy()
    R = h - l
    up = h - np.maximum(o, c)
    tepe = h >= hi
    if kind == "pin":
        m = tepe & (R > 0) & (up >= wick * R)
    elif kind == "hepsi":
        m = tepe
    elif kind == "guclu":
        m = tepe & (R > 0) & (up < R / 3)
    return np.nan_to_num(m, nan=0).astype(bool) & F["ok"]


def time_exit(F: dict, idx: np.ndarray, hold: int, spread: float) -> tuple[np.ndarray, np.ndarray]:
    o, c, seg, atr = F["o"], F["c"], F["seg"], F["atr"]
    n = len(o)
    e = idx + 1
    ok = (e + hold - 1 < n)
    e, idx = e[ok], idx[ok]
    ok = (seg[e] == seg[idx]) & (seg[e + hold - 1] == seg[idx])
    e, idx = e[ok], idx[ok]
    R = (c[e + hold - 1] - o[e]) / atr[idx] - spread / atr[idx]
    return R, idx


def stats(R: np.ndarray) -> dict:
    if len(R) == 0:
        return {"n": 0}
    pos, neg = R[R > 0].sum(), -R[R < 0].sum()
    return {"n": int(len(R)), "R": round(float(R.mean()), 4), "pf": round(float(pos / neg), 3) if neg else None}


def nonoverlap(idx: np.ndarray, hold: int) -> np.ndarray:
    keep, busy = [], -1
    for k, i in enumerate(idx):
        if i > busy:
            keep.append(k)
            busy = i + hold
    return np.array(keep, int)


def t1_t2_t3(ds: dict) -> dict:
    out, pooled = {}, []
    for name, (F, spr) in ds.items():
        idx = np.where(pin_mask(F))[0]
        R, ii = time_exit(F, idx, 20, spr)
        base, _ = time_exit(F, np.where(F["ok"])[0][::3], 20, spr)
        no = nonoverlap(ii, 20)
        st = stats(R)
        st.update(taban=round(float(base.mean()), 4), fark=round(float(R.mean() - base.mean()), 4),
                  tek_poz=stats(R[no]))
        ts = F["ts"].to_numpy()[ii]
        h = len(R) // 2
        st["yarilar"] = [round(float(R[:h].mean()), 3), round(float(R[h:].mean()), 3)]
        out[name] = st
        pooled.append(pd.DataFrame({"t": ts, "R": R, "set": name, "fark": R - base.mean()}))
        print(f"T1/T2 {name:14} n={st['n']:5} ortR {st['R']:+.3f} PF {st['pf']} taban {st['taban']:+.3f} → fark {st['fark']:+.3f} "
              f"| yarılar {st['yarilar']} | tek-poz n={st['tek_poz']['n']} ortR {st['tek_poz'].get('R')}")
    x = pd.concat(pooled)
    x["y"] = pd.to_datetime(x.t, utc=True).dt.year
    yr = x.groupby(["set", "y"]).fark.mean().unstack(0).round(3)
    print("\nT3 yıl yıl (taban farkı, set başına):\n", yr.to_string())
    for name, g in x.groupby("set"):
        day = g.groupby(pd.to_datetime(g.t, utc=True).dt.date).fark.sum().sort_values(ascending=False)
        out[name]["en_iyi_5_gun_haric_fark_toplam"] = round(float(day.sum() - day.head(5).sum()), 1)
        out[name]["en_iyi_10_gun_haric_fark_toplam"] = round(float(day.sum() - day.head(10).sum()), 1)
        out[name]["fark_toplam"] = round(float(day.sum()), 1)
    print("\nT3 en iyi günler çıkınca (taban farkı toplamı):",
          {k: (v["fark_toplam"], v["en_iyi_5_gun_haric_fark_toplam"], v["en_iyi_10_gun_haric_fark_toplam"]) for k, v in out.items()})
    out["_yillar"] = yr.to_dict()
    return out


def t4(ds: dict) -> dict:
    res = {}
    for name in ("NDX 15m", "NDX 30m", "NDX 1h (10y)", "DAX 30m"):
        F, spr = ds[name]
        base = {hd: time_exit(F, np.where(F["ok"])[0][::3], hd, spr)[0].mean() for hd in (10, 15, 20, 30, 40)}
        grid = {}
        for w in (0.5, 0.6, 2 / 3, 0.75):
            for lk in (10, 20, 40):
                idx = np.where(pin_mask(F, w, lk))[0]
                for hd in (10, 15, 20, 30, 40):
                    R, _ = time_exit(F, idx, hd, spr)
                    grid[(round(w, 2), lk, hd)] = float(R.mean() - base[hd]) if len(R) >= 50 else np.nan
        g = pd.Series(grid)
        res[name] = {"pozitif_oran": round(float((g > 0).mean()), 3), "medyan_fark": round(float(g.median()), 4),
                     "min": round(float(g.min()), 4), "max": round(float(g.max()), 4)}
        print(f"T4 {name:14} 60 komşu: taban farkı >0 oranı %{100 * res[name]['pozitif_oran']:.0f}, medyan {res[name]['medyan_fark']:+.3f}, "
              f"aralık [{res[name]['min']:+.3f}, {res[name]['max']:+.3f}]")
    return res


def t5(ds: dict) -> dict:
    res = {}
    for name, (F, spr) in ds.items():
        base = time_exit(F, np.where(F["ok"])[0][::3], 20, spr)[0].mean()
        row = {}
        for kind in ("hepsi", "guclu", "pin"):
            R, _ = time_exit(F, np.where(pin_mask(F, kind=kind))[0], 20, spr)
            row[kind] = (len(R), round(float(R.mean() - base), 4))
        res[name] = row
        print(f"T5 {name:14} yeni-tepe tümü {row['hepsi']} | güçlü kapanış {row['guclu']} | pin bar {row['pin']}   (n, taban farkı)")
    return res


def t6() -> dict:
    """M1 katı icra — NDX 5m/15m/30m'de M1 olan dönem."""
    b1 = S.load(S.NDX / "bars_1m.parquet")
    t1 = b1.ts.dt.tz_convert(None).to_numpy().astype("datetime64[ns]")
    o1, c1 = b1.open.to_numpy(), b1.close.to_numpy()
    res = {}
    for tf, mins in (("5m", 5), ("15m", 15), ("30m", 30)):
        F = S.features(S.load(S.NDX / f"bars_{tf}.parquet"))
        idx = np.where(pin_mask(F))[0]
        R_bar, ii = time_exit(F, idx, 20, 1.5)
        ts = F["ts"].dt.tz_convert(None).to_numpy().astype("datetime64[ns]")
        rows = []
        for k, i in enumerate(ii):
            t_dec = ts[i] + np.timedelta64(mins, "m")                 # TF mumu kapanışı
            t_out = ts[i] + np.timedelta64(mins * 21, "m")            # 20 TF-mumu sonra (yaklaşık; seans boşluğu atlanır)
            a = np.searchsorted(t1, t_dec)
            b = np.searchsorted(t1, t_out) - 1
            if a >= len(t1) or b <= a or t1[a] - t_dec > np.timedelta64(3, "m") or t_out - t1[b] > np.timedelta64(3, "m"):
                continue
            entry = o1[a] + 1.5
            rows.append(((c1[b] - entry) / F["atr"][i], R_bar[k]))
        if rows:
            r = np.array(rows)
            res[tf] = {"n": len(r), "M1_katı": round(float(r[:, 0].mean()), 4), "bar": round(float(r[:, 1].mean()), 4)}
            print(f"T6 NDX {tf}: M1 katı icra n={len(r)} ortR {r[:, 0].mean():+.3f} vs bar-bazlı {r[:, 1].mean():+.3f}")
    return res


if __name__ == "__main__":
    ds = datasets()
    out = {"T1_T2_T3": t1_t2_t3(ds), "T4": t4(ds), "T5": t5(ds), "T6": t6()}
    (OUT / "deep.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
