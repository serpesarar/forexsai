"""Pine Motoru değerlendirmesi (PROTOCOL.md §4): A1 tek script tetikleri + A2 çakışmalar, sembol × ufuk.

Girdi : data/runs/recent/part_*.pkl.gz (batch.py)
Çıktı : results/<SYM>/cells.csv, results/<SYM>/meta.json
Kullanım: python eval_scripts.py [SYM,...]
"""
from __future__ import annotations

import gzip
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
GCM = HERE.parent / "gosterge_cakisma_20261025"
sys.path.insert(0, str(GCM))
import config as GC  # noqa: E402
import data  # noqa: E402
import engine as E  # noqa: E402
import indicators  # noqa: E402

N_BARS = 12000
TF = "1h"
TOP_K = 100
A2_TOP = 300
BATCH = 15000
RES = HERE / "results"


def window_tf(window: str) -> str:
    """'tf_15m' gibi zaman dilimi tekrar pencerelerinin TF'i (EK-P1); full_<tf>_<SYM> → tf; recent/past → 1h."""
    if window.startswith("full_"):
        return window.split("_")[1]
    return window[3:] if window.startswith("tf_") else TF


def window_frame(sym: str, window: str = "recent") -> pd.DataFrame:
    """Pencere + pencere İÇİNDE %60/20/20 bölme (PROTOCOL §2, EK-P1)."""
    d = data.load(sym, window_tf(window))
    if window == "past":
        d = d.iloc[max(0, len(d) - 2 * N_BARS):len(d) - N_BARS]
    elif window == "old":                                   # EK-P3: son pencereden önceki TÜM tarih
        d = d.iloc[:len(d) - N_BARS]
    elif window.startswith("full_"):                        # EK-P9: tüm tarih (v2 madenci)
        pass
    else:
        d = d.iloc[-N_BARS:]
    d = d.reset_index(drop=True)
    n = len(d)
    a, b = int(n * GC.SPLITS[0]), int(n * (GC.SPLITS[0] + GC.SPLITS[1]))
    d["split"] = np.where(np.arange(n) < a, 0, np.where(np.arange(n) < b, 1, 2)).astype(np.int8)
    return d


def lookahead_sids(window: str | None = None) -> set:
    """`lookahead_on` scriptleri (EK-P5: aramadan çıkarılır).

    E82: bayrak yalnız çalışan dalda düşer. 1h'te hata verip (ör. "HTF grafikten büyük olmalı") 15m'de
    çalışan script 1h bayrak listesine girmiyordu. Bu yüzden TÜM pencerelerin bayrakları + kaynakta
    `lookahead_on` geçen her script (statik tarama) birleşimi alınır. `window` verilirse yalnız o pencerenin
    bayrakları (tarihsel kayıt için).
    """
    import re
    import pine_src
    out = set()
    if window is None:
        out |= {r["sid"] for r in pine_src.iter_sources(True) if re.search(r"lookahead_on", r["source"] or "")}
        paths = sorted((HERE / "data/runs").glob("*/part_*.pkl.gz"))
    else:
        paths = sorted((HERE / "data/runs" / window).glob("part_*.pkl.gz"))
    for p in paths:
        with gzip.open(p, "rb") as f:
            for r in pickle.load(f):
                if any("lookahead_on" in (v.get("flags") or []) for v in r["per_sym"].values()):
                    out.add(r["sid"])
    return out


def load_states(sym: str, window: str = "recent", exclude: set | None = None):
    """→ names, script ids, packed bits listesi (yalnız ok koşular; `exclude` scriptleri atlanır)."""
    names, sids, packed = [], [], []
    meta = {}
    for p in sorted((HERE / "data/runs" / window).glob("part_*.pkl.gz")):
        with gzip.open(p, "rb") as f:
            for r in pickle.load(f):
                v = r["per_sym"].get(sym)
                meta[r["sid"]] = (r.get("name"), r.get("author"), r.get("boosts"), v["status"] if v else None,
                                  v.get("flags") if v else None)
                if not v or v["status"] != "ok" or (exclude and r["sid"] in exclude):
                    continue
                for k, b in v["states"].items():
                    names.append(k)
                    sids.append(r["sid"])
                    packed.append(b)
    return names, sids, packed, meta


def unpack(packed: list, n: int) -> np.ndarray:
    """Paketli durumlar → (n, S) bool; tek çağrıda (aynı pencerenin durumları aynı uzunlukta)."""
    if not packed:
        return np.zeros((n, 0), bool)
    buf = np.frombuffer(b"".join(packed), np.uint8).reshape(len(packed), -1)
    return np.ascontiguousarray(np.unpackbits(buf, axis=1)[:, :n].T).astype(bool)


def thin(T: np.ndarray, h: int) -> np.ndarray:
    """E.thin'in vektörel eşdeğeri: her sütun ateşledikten sonra h bar susar (açgözlü, aynı sonuç)."""
    if h <= 1:
        return T
    T = np.ascontiguousarray(T)
    out = np.zeros_like(T)
    last = np.full(T.shape[1], -10 ** 9, np.int64)
    for i in np.flatnonzero(T.any(axis=1)):
        k = T[i] & (i - last >= h)
        out[i] = k
        last[k] = i
    return out


def onsets(S: np.ndarray) -> np.ndarray:
    prev = np.vstack([np.zeros((1, S.shape[1]), bool), S[:-1]])
    return S & ~prev


def l1_stats(packed, n, h, W, L, rng_offsets):
    """Tüm tetiklerin L1 toplamları + her kaydırmada max|z| (KEŞİF)."""
    disc = np.flatnonzero(L["split"] == 0)
    v, e = L["valid"][disc].astype(np.float64), L["e"][disc]
    shiftW = [np.column_stack([np.roll(v, o), np.roll(e, o) * np.roll(v, o), np.roll(e, o) ** 2 * np.roll(v, o)])
              for o in rng_offsets]
    sums = np.zeros((len(packed), W.shape[1]))
    null_z = []
    for a in range(0, len(packed), BATCH):
        T = thin(onsets(unpack(packed[a:a + BATCH], n)), h).astype(np.float32)
        sums[a:a + T.shape[1]] = T.T @ W.astype(np.float32)
        Td = T[disc]
        nz = []
        for Ws in shiftW:
            A = Td.T @ Ws.astype(np.float32)
            nz.append(A)
        null_z.append(nz)
    return sums, null_z


def z_of(nsum, se, see):
    with np.errstate(divide="ignore", invalid="ignore"):
        m = se / nsum
        z = m / np.sqrt(np.maximum(see / nsum - m * m, 1e-18) / nsum)
    return np.where(nsum >= 2, np.nan_to_num(z), 0.0)


def evaluate(sym: str, exclude: set | None = None):
    t0 = time.time()
    d = window_frame(sym)
    n = len(d)
    names, sids, packed, meta = load_states(sym, exclude=exclude)
    book = indicators.compute(d, TF)
    gn, gS, gT, gR, gind = E.matrices(book)
    rng = np.random.default_rng(GC.SEED)
    n_min = GC.N_MIN[TF]
    rows, nulls = [], []
    for h in GC.HORIZONS:
        L = E.labels(d, data.bucket(d, TF), h, GC.SPREAD[sym])
        W = E.weights(L)
        nd = int((L["split"] == 0).sum())
        offs = [int(rng.integers(int(nd * GC.NULL_MIN_OFFSET), nd - int(nd * GC.NULL_MIN_OFFSET)))
                for _ in range(GC.NULL_SHIFTS)]
        sums, null_parts = l1_stats(packed, n, h, W, L, offs)
        g0 = E.split_stats(sums, 0)
        z0 = np.where(g0["n"] >= n_min, g0["z"], 0)
        # plasebo: L1 max + (her kaydırmada) A2 yeniden
        null_l1 = []
        for k in range(GC.NULL_SHIFTS):
            A = np.vstack([np.asarray(p[k]) for p in null_parts])
            zz = z_of(A[:, 0], A[:, 1], A[:, 2])
            zz[A[:, 0] < n_min] = 0
            null_l1.append(zz)
        # A2: en iyi 300 tetik × (GÇM 353 durum + 300 tetiğin yakın hâli)
        top = np.argsort(-np.abs(z0))[:A2_TOP]
        Ttop = thin(onsets(unpack([packed[i] for i in top], n)), h)
        Rtop = onsets(unpack([packed[i] for i in top], n))
        for k in range(1, GC.RECENT_W):
            Rtop[k:] |= onsets(unpack([packed[i] for i in top], n))[:-k]
        X = np.hstack([gS, Rtop])
        A2 = E.pair_sums(Ttop, X, W).transpose(0, 2, 1)
        g2 = E.split_stats(A2, 0)
        same = np.array([[sids[top[i]] == (sids[top[j - gS.shape[1]]] if j >= gS.shape[1] else None)
                          for j in range(X.shape[1])] for i in range(len(top))])
        z2 = np.where((g2["n"] >= n_min) & ~same, g2["z"], 0)
        # tam arama plasebosu: her kaydırmada o kaydırmanın en iyi 300'ü ile A2
        disc = np.flatnonzero(L["split"] == 0)
        v, e = L["valid"][disc].astype(np.float64), L["e"][disc]
        maxes = []
        for k, o in enumerate(offs):
            zz = null_l1[k]
            best = float(np.abs(zz).max())
            topk = np.argsort(-np.abs(zz))[:A2_TOP]
            Tk = thin(onsets(unpack([packed[i] for i in topk], n)), h)[disc]
            Rk = onsets(unpack([packed[i] for i in topk], n))
            for kk in range(1, GC.RECENT_W):
                Rk[kk:] |= onsets(unpack([packed[i] for i in topk], n))[:-kk]
            Xk = np.hstack([gS, Rk])[disc]
            vs, es = np.roll(v, o), np.roll(e, o)
            Ws = np.column_stack([vs, es * vs, es ** 2 * vs])
            Ak = E.pair_sums(Tk, Xk, Ws)
            zk = z_of(Ak[:, 0], Ak[:, 1], Ak[:, 2])
            samek = np.array([[sids[topk[i]] == (sids[topk[j - gS.shape[1]]] if j >= gS.shape[1] else None)
                               for j in range(Xk.shape[1])] for i in range(len(topk))])
            zk[(Ak[:, 0] < n_min) | samek] = 0
            maxes.append(max(best, float(np.abs(zk).max())))
        thr = float(np.quantile(maxes, 0.95)) if max(maxes) > 0 else float("nan")   # havuz boş → ölçülemez
        # aday havuzu: L1 + A2, keşif |z| sırası, %80 örtüşme ayıklaması
        cands = [("L1", int(i), None, float(z0[i])) for i in np.argsort(-np.abs(z0))[:2000] if z0[i] != 0]
        for flat in np.argsort(-np.abs(z2), axis=None)[:2000]:
            i, j = np.unravel_index(flat, z2.shape)
            if z2[i, j] != 0:
                cands.append(("L2", int(top[i]), int(j), float(z2[i, j]), int(i)))
        cands.sort(key=lambda c: -abs(c[3]))
        chosen, sets = [], []
        disc_end = int(disc.max()) + 1
        Tall_cache = {}
        for c in cands:
            ev = _events(c, packed, n, h, X, Ttop, Tall_cache)
            evd = set(ev[ev < disc_end].tolist())
            if not evd or any(len(evd & s) / min(len(evd), len(s)) >= GC.DEDUP_OVERLAP for s in sets):
                continue
            chosen.append((c, ev))
            sets.append(evd)
            if len(chosen) >= TOP_K:
                break
        for c, ev in chosen:
            vec = W[ev].sum(axis=0)
            dsg = np.sign(c[3])
            r = dict(sym=sym, h=h, level=c[0], sid=sids[c[1]], script=meta[sids[c[1]]][0], author=meta[sids[c[1]]][1],
                     state=names[c[1]], partner=(None if c[0] == "L1" else (f"GCM:{gn[c[2]]}" if c[2] < gS.shape[1]
                                                                             else f"R:{sids[top[c[2] - gS.shape[1]]]}|{names[top[c[2] - gS.shape[1]]]}")),
                     dir="BUY" if dsg > 0 else "SELL", kesif_secimden_sag=bool(np.isfinite(thr) and abs(c[3]) >= thr),
                     lookahead_on="lookahead_on" in (meta[sids[c[1]]][4] or []))
            for s, sn in enumerate(("KESIF", "DOGRULAMA", "KASA")):
                out = E.directional(E.split_stats(vec, s), np.array(dsg), L["cost"][s])
                for key in ("n", "z", "hit", "base", "lift", "ret_bp", "cost_bp"):
                    r[f"{sn}_{key}"] = float(np.asarray(out[key]).ravel()[0])
            r["val_ok"] = r["DOGRULAMA_z"] >= GC.Z_PASS and r["DOGRULAMA_n"] >= n_min / 4
            r["test_ok"] = (r["KASA_z"] >= GC.Z_PASS and r["KASA_n"] >= n_min / 4 and r["KASA_lift"] >= GC.LIFT_MIN
                            and r["KASA_ret_bp"] > r["KASA_cost_bp"])
            r["kanitli"] = bool(r["val_ok"] and r["test_ok"])
            r["val_wrong"] = r["DOGRULAMA_z"] <= -GC.Z_PASS and r["DOGRULAMA_n"] >= n_min / 4
            r["test_wrong"] = r["KASA_z"] <= -GC.Z_PASS and r["KASA_n"] >= n_min / 4
            rows.append(r)
        nulls.append(dict(h=h, thr95=thr, null_max=maxes, n_states=len(packed),
                          l1_over=int((np.abs(z0) >= thr).sum()) if np.isfinite(thr) else 0,
                          l2_over=int((np.abs(z2) >= thr).sum()) if np.isfinite(thr) else 0))
        print(f"  {sym} h={h}: {len(packed)} durum, eşik {thr:.2f}, L1 eşik üstü {nulls[-1]['l1_over']}, "
              f"L2 eşik üstü {nulls[-1]['l2_over']}, kanıtlı {sum(r['kanitli'] for r in rows if r['h'] == h)} "
              f"({time.time() - t0:.0f}s)", flush=True)
    out = RES / sym
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "cells.csv", index=False)
    st = pd.Series([m[3] for m in meta.values()]).value_counts().to_dict()
    json.dump(dict(sym=sym, bars=n, excluded_lookahead=len(exclude or ()), start=str(d.ts.iloc[0]), end=str(d.ts.iloc[-1]), scripts=len(meta),
                   status=st, n_states=len(packed), n_scripts_with_states=len(set(sids)), nulls=nulls,
                   seconds=round(time.time() - t0)), open(out / "meta.json", "w"), indent=1, default=str)


def _events(c, packed, n, h, X, Ttop, cache):
    if c[0] == "L1":
        i = c[1]
        if i not in cache:
            cache[i] = np.flatnonzero(thin(onsets(unpack([packed[i]], n)), h)[:, 0])
        return cache[i]
    i_local, j = c[4], c[2]
    return np.flatnonzero(Ttop[:, i_local] & X[:, j])


if __name__ == "__main__":
    syms = sys.argv[1].split(",") if len(sys.argv) > 1 else ["NDX", "DAX", "XAU", "USOIL"]
    excl = lookahead_sids()
    print(f"EK-P5: {len(excl)} lookahead_on script aramadan çıkarıldı", flush=True)
    for s in syms:
        evaluate(s, excl)
