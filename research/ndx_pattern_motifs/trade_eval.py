"""trade_eval.py — mum modellerini ATR TP/SL ile İŞLEM olarak ölç (2026-10-09, ön kayıt bu docstring).

Evren   : seq_scan.json'daki ≥30 tekrarlı modeller (birebir + kısmi), 4 TF. Tekrar listeleri model merkezinden
          aynı tanımla yeniden üretilir (seq_matches_partial + uygunluk + çakışmasız açgözlü).
İşlem   : giriş = modelin son mumundan SONRAKİ mumun açılışı; ATR = önceki 14 mumun ortalama gerçek aralığı.
          TP ∈ {0,5 1 1,5 2 3}×ATR, SL ∈ {0,5 1 1,5 2}×ATR, BUY ve SELL; en çok 60 mum, sonra kapanıştan çık;
          aynı mumda TP ve SL → SL. Maliyet: 1,5 puan spread / SL mesafesi (R'den düşülür). R = SL birimi.
Protokol: her model için tekrarlar kronolojik ikiye bölünür. İLK yarıda (seçim) en yüksek ort. R veren
          (yön, TP, SL) seçilir; İKİNCİ yarıda (sınama, hiç bakılmamış) aynı yapılandırma ölçülür.
Plasebo : her model için aynı sayıda RASTGELE giriş zamanı (aynı TF, aynı dönem aralığı) → aynı seç-sına.
Kenar   : modellerin sınama ortalaması plasebonun sınama dağılımının üstünde ve > 0 olmalı.
Çıktı   : results/trade_eval.json + konsol tabloları.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_seq import TF  # noqa: E402
from seq_engine import (ELIG_RATIO, ELIG_RATIO_PARTIAL, eligible_ratio, greedy_spaced,  # noqa: E402
                        run_lengths, seq_matches_partial)

TPS = np.array([0.5, 1.0, 1.5, 2.0, 3.0])
SLS = np.array([0.5, 1.0, 1.5, 2.0])
MAX_HOLD, ATR_N, SPREAD, MIN_OCC = 60, 14, 1.5, 30
RNG = np.random.default_rng(42)


@nb.njit(cache=True)
def trade_R(o, h, l, c, seg, entries, atr, tps, sls, max_hold, spread):
    """R[i, dir(0=BUY,1=SELL), tp, sl] — dürüst ilk-geçiş, aynı mumda ikisi → SL."""
    n = entries.shape[0]
    out = np.full((n, 2, tps.shape[0], sls.shape[0]), np.nan)
    N = o.shape[0]
    for a in range(n):
        i = entries[a]
        A = atr[a]
        if i < 0 or i >= N or not (A > 0):
            continue
        e = o[i]
        for d in range(2):
            s = 1.0 if d == 0 else -1.0
            for ti in range(tps.shape[0]):
                for si in range(sls.shape[0]):
                    tp = tps[ti] * A
                    sl = sls[si] * A
                    R = np.nan
                    last = i
                    for j in range(i, min(N, i + max_hold)):
                        if seg[j] != seg[i]:
                            break
                        last = j
                        fav = (h[j] - e) if d == 0 else (e - l[j])
                        adv = (e - l[j]) if d == 0 else (h[j] - e)
                        if adv >= sl:
                            R = -1.0
                            break
                        if fav >= tp:
                            R = tps[ti] / sls[si]
                            break
                    if np.isnan(R):
                        R = s * (c[last] - e) / sl
                    out[a, d, ti, si] = R - spread / sl
    return out


def atr_at(T: TF, idx: np.ndarray) -> np.ndarray:
    tr = np.maximum(T.h - T.l, np.maximum(np.abs(T.h - np.r_[T.c[0], T.c[:-1]]), np.abs(T.l - np.r_[T.c[0], T.c[:-1]])))
    cs = np.r_[0.0, np.cumsum(tr)]
    a = np.full(len(idx), np.nan)
    ok = idx >= ATR_N
    a[ok] = (cs[idx[ok]] - cs[idx[ok] - ATR_N]) / ATR_N            # yalnız girişten ÖNCEKİ 14 mum
    same = ok.copy()
    same[ok] = T.seg[idx[ok] - ATR_N] == T.seg[idx[ok]]
    a[~same] = np.nan
    return a


def occurrences(T: TF, run: np.ndarray, m: dict) -> np.ndarray:
    k, tol, q = m["k"], m["tol"], m.get("q", 1.0)
    s = int(np.where(T.srv == m["show"][0]["start"])[0][0])
    need = int(np.ceil(q * k - 1e-9))
    ts, ms, rm = seq_matches_partial(T.X, run, s, k, np.float32(tol), need)
    el = eligible_ratio(T.X, T.brk, k, tol, ELIG_RATIO if q == 1.0 else ELIG_RATIO_PARTIAL)
    keep = el[ts]
    picked = greedy_spaced(ts[keep], -ms[keep] * 10.0 + rm[keep], k, np.array([s]))
    return np.sort(np.array([s] + picked, dtype=np.int64))


def select_and_test(R: np.ndarray, t_order: np.ndarray) -> dict | None:
    """R: [n,2,5,4]; ilk yarıda en iyi yapılandırma → ikinci yarıda ölç."""
    o = np.argsort(t_order)
    R = R[o]
    R = R[~np.isnan(R).any(axis=(1, 2, 3))]
    if len(R) < MIN_OCC:
        return None
    h = len(R) // 2
    is_m = R[:h].mean(axis=0)
    d, ti, si = np.unravel_index(np.nanargmax(is_m), is_m.shape)
    oos = R[h:, d, ti, si]
    return {"n_is": h, "n_oos": len(oos), "dir": "BUY" if d == 0 else "SELL", "tp": float(TPS[ti]), "sl": float(SLS[si]),
            "is_R": float(is_m[d, ti, si]), "oos_R": float(oos.mean()), "oos_wr": float((oos > 0).mean()),
            "oos_sum": float(oos.sum()), "grid_is": is_m, "R_all": R}


def eval_tf(tf: str, motifs: list[dict]) -> tuple[list, list, dict]:
    T = TF(tf)
    run = run_lengths(T.brk)
    o, h, l, c, seg = T.o, T.h, T.l, T.c, T.seg
    real, plac = [], []
    pooled = {"real": np.zeros((2, 5, 4)), "n": 0}
    valid_idx = np.where(np.r_[T.seg[1:] == T.seg[:-1], False])[0]
    for m in motifs:
        occ = occurrences(T, run, m)
        ent = occ + m["k"]
        ent = ent[ent < len(o)]
        ent = ent[seg[ent] == seg[ent - 1]]
        a = atr_at(T, ent)
        R = trade_R(o, h, l, c, seg, ent, a, TPS, SLS, MAX_HOLD, SPREAD)
        r = select_and_test(R, ent)
        if r is None:
            continue
        good = R[~np.isnan(R).any(axis=(1, 2, 3))]
        pooled["real"] += good.sum(axis=0)
        pooled["n"] += len(good)
        r.update(tf=tf, name=m["name"], k=m["k"], tol=m["tol"], q=m.get("q", 1.0), start=m["show"][0]["start"],
                 n=len(r["R_all"]))
        real.append(r)
        # plasebo: aynı dönem aralığında rastgele girişler (aynı sayı)
        lo, hi = ent.min(), ent.max()
        pool = valid_idx[(valid_idx >= lo) & (valid_idx <= hi)]
        pe = np.sort(RNG.choice(pool, size=min(len(ent), len(pool)), replace=False))
        Rp = trade_R(o, h, l, c, seg, pe, atr_at(T, pe), TPS, SLS, MAX_HOLD, SPREAD)
        rp = select_and_test(Rp, pe)
        if rp is not None:
            plac.append({k: v for k, v in rp.items() if k not in ("grid_is", "R_all")})
    return real, plac, pooled


def summarize(tf: str, real: list, plac: list, pooled: dict) -> dict:
    ro = np.array([r["oos_R"] for r in real])
    po = np.array([p["oos_R"] for p in plac])
    ri = np.array([r["is_R"] for r in real])
    grid = pooled["real"] / max(pooled["n"], 1)
    d, ti, si = np.unravel_index(np.argmax(grid), grid.shape)
    out = {"tf": tf, "modeller": len(real), "is_secilen_ortR": round(float(ri.mean()), 3),
           "oos_ortR_model": round(float(ro.mean()), 4), "oos_pozitif_oran": round(float((ro > 0).mean()), 3),
           "plasebo_oos_ortR": round(float(po.mean()), 4), "plasebo_pozitif_oran": round(float((po > 0).mean()), 3),
           "havuz_en_iyi_sabit": {"dir": "BUY" if d == 0 else "SELL", "tp": float(TPS[ti]), "sl": float(SLS[si]),
                                  "ortR": round(float(grid[d, ti, si]), 4)},
           "havuz_izgara": {f"{'BUY' if dd == 0 else 'SELL'} TP{TPS[a]}/SL{SLS[b]}": round(float(grid[dd, a, b]), 4)
                            for dd in range(2) for a in range(5) for b in range(4)}}
    return out


def main() -> None:
    o = json.loads((HERE / "results" / "seq_scan.json").read_text())
    res, all_real = {}, []
    for t in o["tfs"]:
        ms = [m for m in t["exact"]["motifs"] + t.get("partial", {}).get("motifs", []) if m["fwd"]["n"] >= MIN_OCC]
        t0 = time.time()
        real, plac, pooled = eval_tf(t["tf"], ms)
        s = summarize(t["tf"], real, plac, pooled)
        res[t["tf"]] = s
        all_real += real
        print(f"{t['tf']:>4}: {s['modeller']} model | seçimde ortR {s['is_secilen_ortR']:+.3f} → sınamada {s['oos_ortR_model']:+.4f} "
              f"(pozitif %{100 * s['oos_pozitif_oran']:.0f}) | plasebo sınama {s['plasebo_oos_ortR']:+.4f} "
              f"(pozitif %{100 * s['plasebo_pozitif_oran']:.0f}) | havuz en iyi sabit {s['havuz_en_iyi_sabit']}  ({time.time() - t0:.0f}s)",
              flush=True)
    # en iyi adaylar: SEÇİM yarısına göre ilk 20 → sınama sonuçları (sınamaya göre seçmek sınamayı bozar)
    top = sorted(all_real, key=lambda r: -r["is_R"])[:20]
    res["secimde_ilk20"] = [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()
                             if k not in ("grid_is", "R_all")} for r in top]
    print("\nSEÇİM yarısında en iyi 20 model → SINAMA yarısındaki sonuçları:")
    for r in top:
        print(f"  {r['tf']:>3} k{r['k']:<3} q{r['q']} pay{r['tol']:<6} {r['dir']:4} TP{r['tp']}/SL{r['sl']}  "
              f"seçim {r['is_R']:+.3f} (n={r['n_is']}) → sınama {r['oos_R']:+.3f} (n={r['n_oos']}, WR %{100 * r['oos_wr']:.0f})  {r['name']}")
    oos_all = np.concatenate([r["R_all"][r["n_is"]:, 0 if r["dir"] == "BUY" else 1,
                                         int(np.where(TPS == r["tp"])[0][0]), int(np.where(SLS == r["sl"])[0][0])]
                              for r in all_real])
    res["toplam_sinama"] = {"islem": int(len(oos_all)), "ortR": round(float(oos_all.mean()), 4),
                            "toplamR": round(float(oos_all.sum()), 1)}
    print(f"\nTÜM modellerin sınama işlemleri birlikte: {len(oos_all)} işlem, ortR {oos_all.mean():+.4f}, toplam {oos_all.sum():+.1f}R")
    (HERE / "results" / "trade_eval.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()
