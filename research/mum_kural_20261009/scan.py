"""Mum formasyonu kural taraması — PROTOCOL.md'ye birebir. Aşama: keşif + plasebo; kasa ayrı çağrılır (--kasa).

python3 scan.py           # keşif (NDX ≤ 2026-06-30) + 20 plasebo → results/kesif.json
python3 scan.py --kasa    # keşfi geçenleri kasa 1 (NDX 2026-07→10) ve kasa 2 (DAX) üzerinde bir kez sına
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/ndx_pattern_motifs"))
from trade_eval import trade_R  # noqa: E402

NDX = ROOT / "research/ndx_pattern_motifs/data"
DAX = ROOT / "research/ndx_gate_forge/data"
CUT = pd.Timestamp("2026-07-01", tz="UTC")
SPREAD, ATR_N, LOOK, MAX_HOLD = 1.5, 14, 20, 60
HOLDS = {"T5": 5, "T10": 10, "T20": 20}
BRK = {"B11": (1.0, 1.0), "B21": (2.0, 1.0)}
MIN_N, MIN_PF, REPS = 100, 1.05, 20
TUR2 = "--tur2" in sys.argv
TFS_NDX = ("5m", "15m", "30m") if TUR2 else ("1m", "5m", "15m", "30m")
_BASE: dict = {}


def baseline(tf_key: str, F: dict, side: int, ex: str) -> float:
    """Taban: aynı TF/yön/çıkışla tüm geçerli mumlarda giriş (her 3. mum — hız; yansız örnek)."""
    k = (tf_key, side, ex, id(F))
    if k not in _BASE:
        idx = np.where(F["ok"])[0][::3]
        _BASE[k] = float(np.nanmean(outcomes(F, idx, side)[ex]))
    return _BASE[k]
RNG = np.random.default_rng(2026)


def load(path: Path, segs: bool = True) -> pd.DataFrame:
    d = pd.read_parquet(path).sort_values("ts").reset_index(drop=True)
    if "seg" not in d:
        d["seg"] = (d.ts.diff() > pd.Timedelta(days=4)).cumsum()
    return d


def features(d: pd.DataFrame) -> dict:
    o, h, l, c = (d[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    seg = d.seg.to_numpy()
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
    cs = np.r_[0, np.cumsum(tr)]
    n = len(c)
    i = np.arange(n)
    atr = np.full(n, np.nan)
    atr[ATR_N:] = (cs[ATR_N:n] - cs[:n - ATR_N]) / ATR_N            # önceki 14 mum (i hariç)
    s = pd.Series
    lo20 = s(l).shift(1).rolling(LOOK).min().to_numpy()
    hi20 = s(h).shift(1).rolling(LOOK).max().to_numpy()
    ema = s(c).ewm(span=50, adjust=False).mean().to_numpy()
    ok = np.zeros(n, bool)
    ok[LOOK + 2:] = seg[LOOK + 2:] == seg[:n - LOOK - 2]
    ok &= np.isfinite(atr) & (atr > 0)
    return dict(o=o, h=h, l=l, c=c, seg=seg, atr=atr, lo20=lo20, hi20=hi20, ema=ema, ok=ok, ts=d.ts)


def rules(F: dict) -> dict[str, tuple[np.ndarray, int]]:
    """kural → (maske, TAKİP yönü +1/−1). Hepsi yalnız i ve öncesini kullanır."""
    o, h, l, c, atr = F["o"], F["h"], F["l"], F["c"], F["atr"]
    sh = lambda x, k=1: np.r_[np.full(k, np.nan), x[:-k]]
    B, R = np.abs(c - o), h - l
    up, lw = h - np.maximum(o, c), np.minimum(o, c) - l
    g, r = c > o, c < o
    o1, c1, h1, l1, B1 = sh(o), sh(c), sh(h), sh(l), sh(B)
    g1, r1 = c1 > o1, c1 < o1
    o2, c2 = sh(o, 2), sh(c, 2)
    dip, tepe, yuk = l <= F["lo20"], h >= F["hi20"], c > F["ema"]
    inside1 = (h1 <= sh(h, 2)) & (l1 >= sh(l, 2))
    R1 = sh(R)
    nr7 = sh(pd.Series(R).rolling(7).apply(lambda x: x[-1] == x.min(), raw=True).to_numpy().astype(float)) == 1
    pos = np.where(R > 0, (c - l) / np.where(R > 0, R, 1), 0.5)
    return {
        "01 yutan boğa": (r1 & g & (c >= o1) & (o <= c1), 1),
        "02 yutan ayı": (g1 & r & (c <= o1) & (o >= c1), -1),
        "03 çekiç @dip": (dip & (lw >= 2 * B) & (up <= B), 1),
        "04 kayan yıldız @tepe": (tepe & (up >= 2 * B) & (lw <= B), -1),
        "05 kapitülasyon kırmızı @dip": (dip & r & (R >= 2 * atr) & (pos <= 0.25), 1),
        "06 coşku yeşil @tepe": (tepe & g & (R >= 2 * atr) & (pos >= 0.75), 1),
        "07 iç bar ↑ kırılım": (inside1 & (c > sh(h, 2)), 1),
        "08 iç bar ↓ kırılım": (inside1 & (c < sh(l, 2)), -1),
        "09 üç beyaz asker": (g & g1 & (c2 > o2) & (c > c1) & (c1 > c2) & (B >= 0.5 * R) & (B1 >= 0.5 * R1), 1),
        "10 üç kara karga": (r & r1 & (c2 < o2) & (c < c1) & (c1 < c2) & (B >= 0.5 * R) & (B1 >= 0.5 * R1), -1),
        "11 sabah yıldızı": ((c2 < o2) & (np.abs(c1 - o1) < 0.5 * np.abs(c2 - o2)) & g & (c > (o2 + c2) / 2), 1),
        "12 akşam yıldızı": ((c2 > o2) & (np.abs(c1 - o1) < 0.5 * np.abs(c2 - o2)) & r & (c < (o2 + c2) / 2), -1),
        "13 pin bar @dip": (dip & (lw >= 2 / 3 * R) & (R > 0), 1),
        "14 pin bar @tepe": (tepe & (up >= 2 / 3 * R) & (R > 0), -1),
        "15 dış bar yeşil": ((h > h1) & (l < l1) & g, 1),
        "16 dış bar kırmızı": ((h > h1) & (l < l1) & r, -1),
        "17 yükselişte 3 düşen kapanış": (yuk & (c < c1) & (c1 < c2) & (c2 < sh(c, 3)), 1),
        "18 düşüşte 3 yükselen kapanış": (~yuk & (c > c1) & (c1 > c2) & (c2 > sh(c, 3)), -1),
        "19 NR7 → yukarı kapanış": (nr7 & (c > h1), 1),
        "20 NR7 → aşağı kapanış": (nr7 & (c < l1), -1),
    }


def outcomes(F: dict, idx: np.ndarray, side: int) -> dict[str, np.ndarray]:
    """Olay i → giriş i+1 açılışı; her çıkış için net R (ATR birimi). Geçersiz → atılır (ortak maske)."""
    o, c, seg, atr = F["o"], F["c"], F["seg"], F["atr"]
    n = len(o)
    e = idx + 1
    valid = (e + 20 < n)
    e, idx = e[valid], idx[valid]
    valid = (seg[e] == seg[idx]) & (seg[np.minimum(e + 19, n - 1)] == seg[idx])
    e, idx = e[valid], idx[valid]
    A = atr[idx]
    cost = SPREAD / A
    out = {}
    for k, H in HOLDS.items():
        out[k] = side * (c[e + H - 1] - o[e]) / A - cost
    br = trade_R(o, F["h"], F["l"], c, seg, e.astype(np.int64), A, np.array([1.0, 2.0]), np.array([1.0]),
                 MAX_HOLD, SPREAD)
    d = 0 if side == 1 else 1
    out["B11"], out["B21"] = br[:, d, 0, 0], br[:, d, 1, 0]
    out["_t"] = F["ts"].to_numpy()[idx]
    return out


def stats(v: np.ndarray) -> dict:
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return {"n": 0, "R": np.nan, "pf": np.nan}
    pos, neg = v[v > 0].sum(), -v[v < 0].sum()
    return {"n": int(len(v)), "R": float(v.mean()), "pf": float(pos / neg) if neg > 0 else np.inf}


def evaluate(Fs: dict, events: dict) -> dict:
    """events[tf][(kural, yön)] = olay indeksleri → yapılandırma başına TF istatistikleri + yarılar + geçti mi."""
    res = {}
    for key in events[next(iter(events))]:
        rule, yon = key
        for ex in list(HOLDS) + list(BRK):
            per, halves = {}, []
            for tf, F in Fs.items():
                idx, side = events[tf][key]
                if len(idx) == 0:
                    per[tf] = {"n": 0, "R": np.nan, "pf": np.nan}; continue
                oc = outcomes(F, idx, side)
                v = oc[ex]
                per[tf] = stats(v)
                if TUR2:
                    per[tf]["taban"] = baseline(tf, F, side, ex)
                    per[tf]["fark"] = per[tf]["R"] - per[tf]["taban"]
                h = len(v) // 2
                halves.append((np.nanmean(v[:h]) if h else np.nan, np.nanmean(v[h:]) if h else np.nan))
            hv = np.array(halves, float)
            ok = all(p["n"] >= MIN_N and p["R"] > 0 and p["pf"] >= MIN_PF and (not TUR2 or p["fark"] > 0)
                     for p in per.values()) and \
                len(hv) == len(Fs) and np.nanmean(hv[:, 0]) > 0 and np.nanmean(hv[:, 1]) > 0
            res[f"{rule} | {yon} | {ex}"] = {"tf": per, "yarilar": [float(np.nanmean(hv[:, 0])), float(np.nanmean(hv[:, 1]))]
                                            if len(hv) else None, "gecti": bool(ok)}
    return res


def build_events(Fs: dict, shift: bool = False) -> dict:
    ev = {}
    for tf, F in Fs.items():
        ev[tf] = {}
        n = len(F["c"])
        for rule, (mask, follow) in rules(F).items():
            idx = np.where(np.nan_to_num(mask, nan=0).astype(bool) & F["ok"])[0]
            if shift and len(idx):
                idx = np.sort((idx + RNG.integers(1000, n - 1000)) % n)
                idx = idx[F["ok"][idx]]
            for yon, side in (("TAKİP", follow), ("TERS", -follow)):
                ev[tf][(rule, yon)] = (idx, side)
    return ev


def ndx_sets(lockbox: bool) -> dict:
    Fs = {}
    for tf in TFS_NDX:
        d = load(NDX / f"bars_{tf}.parquet")
        d = d[(d.ts >= CUT)] if lockbox else d[d.ts < CUT]
        Fs[tf] = features(d.reset_index(drop=True))
    return Fs


def dax_sets() -> dict:
    return {tf: features(load(DAX / f"dax_{tf}.parquet")[lambda x: x.ts >= "2019-01-01"].reset_index(drop=True))
            for tf in ("15m", "30m", "1h")}


def kesif() -> None:
    Fs = ndx_sets(False)
    real = evaluate(Fs, build_events(Fs))
    passed = [k for k, v in real.items() if v["gecti"]]
    null = []
    for rep in range(REPS):
        p = evaluate(Fs, build_events(Fs, shift=True))
        null.append(sum(v["gecti"] for v in p.values()))
    nv = np.array(null)
    print(f"KEŞİF: {len(real)} yapılandırma, 4 TF'nin hepsinde pozitif+PF≥1,05+iki yarı: {len(passed)}")
    print(f"PLASEBO (dairesel kaydırma, {REPS} tekrar): geçen sayısı ort {nv.mean():.1f}, %95 {np.percentile(nv, 95):.1f}, max {nv.max()}")
    for k in passed:
        v = real[k]
        print("  ✓", k, {tf: (p["n"], round(p["R"], 3), round(p["pf"], 2), round(p.get("fark", np.nan), 3)) for tf, p in v["tf"].items()}, "yarılar", [round(x, 3) for x in v["yarilar"]])
    # en yakın adaylar (hangi TF'de düştüğünü görmek için)
    kk = "fark" if TUR2 else "R"
    near = sorted(real.items(), key=lambda kv: -min((p[kk] if np.isfinite(p[kk]) else -9) for p in kv[1]["tf"].values()))[:12]
    print("\nEn zayıf TF'si en iyi olan 12 yapılandırma (min TF ort. R):")
    for k, v in near:
        print(f"  {k:48}", {tf: (p['n'], round(p['R'], 3), round(p['pf'], 2), round(p.get('fark', np.nan), 3)) for tf, p in v['tf'].items()})
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / ("kesif_tur2.json" if TUR2 else "kesif.json")).write_text(json.dumps({"gecen": passed, "plasebo": null, "sonuc": real},
                                                            ensure_ascii=False, default=float))


def kasa() -> None:
    k = json.loads((HERE / "results" / ("kesif_tur2.json" if TUR2 else "kesif.json")).read_text())
    if not k["gecen"]:
        print("Keşfi geçen yapılandırma yok — kasa açılmadı.")
        return
    for name, Fs, need in (("KASA-1 NDX 2026-07→10", ndx_sets(True), "4tf"), ("KASA-2 DAX", dax_sets(), "3tf")):
        r = evaluate(Fs, build_events(Fs))
        print(f"\n{name}:")
        for key in k["gecen"]:
            v = r[key]
            ok = all(np.isfinite(p["R"]) and p["R"] > 0 for p in v["tf"].values())
            print(f"  {'✓' if ok else '✗'} {key:48}", {tf: (p['n'], round(p['R'], 3), round(p['pf'], 2)) for tf, p in v['tf'].items()})


if __name__ == "__main__":
    kasa() if "--kasa" in sys.argv else kesif()
