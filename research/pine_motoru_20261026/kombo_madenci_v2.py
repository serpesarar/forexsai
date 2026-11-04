"""Kombinasyon Madencisi v2 (PROTOCOL EK-P9): tüm tarih + yön isabeti puanı + ikili etkileşim taraması.

v1'den (kombo_madenci.py) farklar:
  - etiket artığı e = 1[r>0] − p_up (bölme × saat) → z yön isabetinin t'si (getiri büyüklüğü değil)
  - saf etkileşim: popüler, birbirinden farklı K özelliğin TÜM çiftleri, h-adımlı ızgarada (matris çarpımıyla)
  - model girdisi: tekli ilk 3.000 ∪ çift kümesi
Işın araması, aday seçimi, doğrulama/kasa ölçütleri v1 ile aynı fonksiyonlardır.

Kullanım: python kombo_madenci_v2.py <pencere: full_1h_NDX|recent|...> [SYM,...]
Çıktı: results_kombo_v2/<pencere>/<SYM>/{adaylar.csv, ciftler.csv, model.csv, meta.json}
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kombo_madenci as KM  # noqa: E402

E, EV, GC, data = KM.E, KM.EV, KM.GC, KM.data
HS = KM.HS
PAIR_K = 3000
PAIR_FREQ = (0.08, 0.50)
PAIR_CORR_MAX = 0.9
PAIR_TOP = 100
CORR_SAMPLE = 6000
CORR_BATCH = 2000
OUT = HERE / "results_kombo_v2"


# ── etiket: yön isabeti artığı ───────────────────────────────────────────────
def hit_labels(d, tf, h, cost):
    L = E.labels(d, data.bucket(d, tf), h, cost)
    L["e"] = np.where(L["valid"], (L["r"] > 0).astype(np.float64) - L["pu"], 0.0)
    return L


def label_pack(d, tf, sym, rng):
    """KM.label_pack'in aynısı; tek fark e = isabet artığı."""
    disc = np.flatnonzero(d.split.values == 0)
    nd = len(disc)
    offs = rng.integers(int(nd * GC.NULL_MIN_OFFSET), nd - int(nd * GC.NULL_MIN_OFFSET), KM.N_SHIFT)
    out = {}
    for h in HS:
        L = hit_labels(d, tf, h, GC.SPREAD[sym])
        W = E.weights(L)
        v, e = L["valid"][disc].astype(np.float64), L["e"][disc]
        Wsh = np.zeros((len(d), 3 * KM.N_SHIFT))
        for k, o in enumerate(offs):
            vs, es = np.roll(v, o), np.roll(e, o)
            Wsh[disc, 3 * k:3 * k + 3] = np.column_stack([vs, es * vs, es ** 2 * vs])
        out[h] = (L, np.hstack([W, Wsh]).astype(np.float32))
    return out


# ── çift kümesi seçimi ───────────────────────────────────────────────────────
def pair_set(fs: KM.Feats, boosts: np.ndarray, disc: np.ndarray, force=()) -> list[int]:
    """Popülerlik sırasıyla, sıklık bandında ve birbirine |r| < PAIR_CORR_MAX olan en çok PAIR_K özellik."""
    rng = np.random.default_rng(GC.SEED)
    samp = np.sort(rng.choice(disc, min(CORR_SAMPLE, len(disc)), replace=False))
    fset = set(int(i) for i in force)
    order = list(fset) + [int(i) for i in np.argsort(-boosts, kind="stable") if int(i) not in fset]
    acc, accZ = [], np.zeros((0, len(samp)), np.float32)
    for a in range(0, len(order), CORR_BATCH):
        idx = order[a:a + CORR_BATCH]
        X = fs.mat(idx)
        fr = X[disc].mean(axis=0)
        ok = ((fr >= PAIR_FREQ[0]) & (fr <= PAIR_FREQ[1])) | np.isin(idx, list(fset))
        if not ok.any():
            continue
        idx = [i for i, k in zip(idx, ok) if k]
        Z = X[samp][:, ok].astype(np.float32).T
        Z = (Z - Z.mean(axis=1, keepdims=True)) / np.maximum(Z.std(axis=1, keepdims=True), 1e-6) / np.sqrt(len(samp))
        Cprev = np.abs(Z @ accZ.T).max(axis=1) if len(acc) else np.zeros(len(idx))
        Cself = np.abs(Z @ Z.T)
        taken = []
        for j, i in enumerate(idx):
            if Cprev[j] >= PAIR_CORR_MAX or any(Cself[j, t] >= PAIR_CORR_MAX for t in taken):
                continue
            taken.append(j)
            acc.append(i)
            if len(acc) >= PAIR_K:
                break
        accZ = np.vstack([accZ, Z[taken]])
        if len(acc) >= PAIR_K:
            break
    return acc


# ── çift taraması ────────────────────────────────────────────────────────────
def _pair_z(Xg, w):
    """Xg: ızgara × K (float32), w: ızgara × 3 (v, e, e²) → n, z (K × K)."""
    S = [Xg.T @ (Xg * w[:, c:c + 1]) for c in range(3)]
    return S[0], EV.z_of(S[0], S[1], S[2])


def pair_scan(fs, K: list[int], lp, n_min, disc_end):
    X = fs.mat(K)
    iu = np.triu_indices(len(K), 1)
    res = {}
    for h in HS:
        L, Wh = lp[h]
        g = np.arange(0, disc_end, h)
        Xg = X[g].astype(np.float32)
        n_, z_ = _pair_z(Xg, Wh[g][:, [0, 1, 2]].astype(np.float32))
        n_, z_ = n_[iu], np.where(n_[iu] >= n_min, z_[iu], 0.0)
        smax = []
        for k in range(KM.N_SHIFT):
            ns, zs = _pair_z(Xg, Wh[g][:, 24 + 3 * k:27 + 3 * k].astype(np.float32))
            smax.append(float(np.abs(np.where(ns[iu] >= n_min, zs[iu], 0.0)).max()))
        thr = float(np.quantile(smax, 0.95))
        top = np.argsort(-np.abs(z_))[:PAIR_TOP * 5]
        res[h] = dict(thr=thr, cands=[(K[iu[0][t]], K[iu[1][t]], float(n_[t]), float(z_[t])) for t in top])
    return res


def grid_events(x: np.ndarray, h: int) -> np.ndarray:
    g = np.zeros(len(x), bool)
    g[::h] = True
    return np.flatnonzero(x & g)


def pair_rows(fs, sym, window, scan, lp, n_min, disc_end, sname):
    rows = []
    for h in HS:
        L, Wh = lp[h]
        sets = []
        for a, b, _, z in scan[h]["cands"]:
            ev = grid_events(fs.vec(a) & fs.vec(b), h)
            evd = set(ev[ev < disc_end].tolist())
            if not evd or any(len(evd & s) / min(len(evd), len(s)) >= GC.DEDUP_OVERLAP for s in sets):
                continue
            sets.append(evd)
            r = KM.split_rows(ev, Wh, L, 1.0 if z > 0 else -1.0, n_min)
            rows.append(dict(kombo_id=f"{sym}-P-h{h}-{len(rows)}", sym=sym, window=window, h=h, derece=2,
                             dir="BUY" if z > 0 else "SELL", kosullar=f"{fs.names[a]} & {fs.names[b]}",
                             kosullar_ad=f"{KM._readable(fs.names[a], sname)} & {KM._readable(fs.names[b], sname)}",
                             idx_a=a, idx_b=b, kesif_esik_ustu=abs(z) >= scan[h]["thr"], esik=scan[h]["thr"], **r))
            if len(sets) >= PAIR_TOP:
                break
    return rows


# ── ışın araması (v1 akışı, yeni puanla) ─────────────────────────────────────
def beam_rows(fs, sym, window, lp, nz, smax, n_min, disc_end, sname):
    rows = []
    for h in HS:
        found = KM.beam(fs, h, lp[h][1], nz[h][:, 1], nz[h][:, 0], smax[h], n_min)
        thr = float(np.quantile(smax[h], 0.95))
        for tup, z, ev in KM.select(fs, found, h, disc_end):
            dsg = 1.0 if z > 0 else -1.0
            r = KM.split_rows(ev, lp[h][1], lp[h][0], dsg, n_min)
            rows.append(dict(kombo_id=f"{sym}-B-h{h}-{len(rows)}", sym=sym, window=window, h=h, derece=len(tup),
                             dir="BUY" if dsg > 0 else "SELL", kosullar=" & ".join(fs.names[i] for i in tup),
                             kosullar_ad=" & ".join(KM._readable(fs.names[i], sname) for i in tup),
                             tup=tup, kesif_esik_ustu=abs(z) >= thr, esik=thr, **r))
    return rows


def model(fs, nz, lp, K, bull_f, bear_f, sp, n_min):
    """KM.model'in aynısı; girdi = tekli ilk MODEL_FEATS ∪ çift kümesi K."""
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score
    rows = []
    for h in HS:
        L, Wh = lp[h]
        idx = np.union1d(np.argsort(-np.abs(nz[h][:, 1]))[:KM.MODEL_FEATS], np.array(K, int))
        X = np.column_stack([fs.mat(idx).astype(np.float32), bull_f, bear_f])
        y, v = (L["r"] > 0).astype(int), L["valid"]
        tr, va, te = (sp == 0) & v, (sp == 1) & v, (sp == 2) & v
        m = lgb.LGBMClassifier(n_estimators=600, learning_rate=0.03, num_leaves=15, min_child_samples=100,
                               subsample=0.8, subsample_freq=1, colsample_bytree=0.5, n_jobs=2, verbose=-1)
        m.fit(X[tr], y[tr], eval_set=[(X[va], y[va])], callbacks=[lgb.early_stopping(50, verbose=False)])
        p = m.predict_proba(X)[:, 1]
        lo, hi = np.quantile(p[sp == 1], [0.10, 0.90])
        r = dict(h=h, iters=int(m.best_iteration_ or 0), kasa_auc=float(roc_auc_score(y[te], p[te])),
                 dogr_auc=float(roc_auc_score(y[va], p[va])))
        for dr, mask, dsg in (("BUY", p >= hi, 1.0), ("SELL", p <= lo, -1.0)):
            ev = np.flatnonzero(EV.thin(mask[:, None], h)[:, 0])
            s = KM.split_rows(ev, Wh, L, dsg, n_min)
            r.update({f"{dr}_{k}": s[k] for k in ("DOGRULAMA_n", "DOGRULAMA_z", "KASA_n", "KASA_z", "KASA_hit",
                                                     "KASA_base", "KASA_lift", "KASA_ret_bp", "KASA_cost_bp")})
        rows.append(r)
        print(f"    model h={h}: kasa AUC {r['kasa_auc']:.4f}, AL kasa z {r['BUY_KASA_z']:.2f}, "
              f"SAT kasa z {r['SELL_KASA_z']:.2f}", flush=True)
    return rows


# ── hazırlık (enjeksiyon sınaması da kullanır) ───────────────────────────────
def prepare(sym: str, window: str, excl: set, extra=()):
    """→ bağlam sözlüğü. extra: [(ad, bool dizi)] gerçek özelliklere eklenir (enjeksiyon)."""
    t0 = time.time()
    d = EV.window_frame(sym, window)
    tf, n, sp = EV.window_tf(window), len(d), d.split.values
    cap = {}
    orig = EV.load_states

    def _cap(*a, **k):
        r = orig(*a, **k)
        cap["meta"] = r[3]
        return r
    EV.load_states = _cap
    try:
        packed, names, bull_f, bear_f, sname = KM.build_features(sym, window, d, excl)
    finally:
        EV.load_states = orig
    p0 = len(packed)
    for nm, x in extra:
        packed.append(np.packbits(x).tobytes())
        names.append(nm)
    mix, mix_names = KM.mix_features(bull_f, bear_f, sp == 0)
    fs = KM.Feats(packed, names, mix, mix_names, n)
    meta = cap["meta"]
    boosts = np.array([float((meta.get(nm.split(":", 1)[1].split("|", 1)[0]) or (0, 0, 0))[2] or 0)
                       if i < p0 else 0.0 for i, nm in enumerate(names)])
    print(f"  {sym} {window}: {len(fs)} özellik, {n} bar ({time.time() - t0:.0f}s)", flush=True)
    return dict(d=d, tf=tf, n=n, sp=sp, fs=fs, p0=p0, bull_f=bull_f, bear_f=bear_f, sname=sname, boosts=boosts,
                n_min=GC.N_MIN[tf], disc_end=int(np.flatnonzero(sp == 0).max()) + 1, t0=t0)


def mine(c: dict, sym: str, window: str, force=(), with_model=True):
    fs, sp, n_min, disc_end = c["fs"], c["sp"], c["n_min"], c["disc_end"]
    lp = label_pack(c["d"], c["tf"], sym, np.random.default_rng(GC.SEED))
    nz, smax = KM.univariate(fs, lp, n_min)
    K = pair_set(fs, c["boosts"], np.flatnonzero(sp == 0), force)
    print(f"  çift kümesi K={len(K)} ({time.time() - c['t0']:.0f}s)", flush=True)
    scan = pair_scan(fs, K, lp, n_min, disc_end)
    prs = pair_rows(fs, sym, window, scan, lp, n_min, disc_end, c["sname"])
    bms = beam_rows(fs, sym, window, lp, nz, smax, n_min, disc_end, c["sname"])
    for h in HS:
        hp = [r for r in prs if r["h"] == h]
        hb = [r for r in bms if r["h"] == h]
        print(f"  {sym} h={h}: çift eşik {scan[h]['thr']:.2f} kanıtlı {sum(r['kanitli'] for r in hp)} "
              f"doğr {sum(r['val_ok'] for r in hp)}/{sum(r['val_wrong'] for r in hp)} | ışın kanıtlı "
              f"{sum(r['kanitli'] for r in hb)} doğr {sum(r['val_ok'] for r in hb)}/{sum(r['val_wrong'] for r in hb)}"
              f" ({time.time() - c['t0']:.0f}s)", flush=True)
    mod = model(fs, nz, lp, K, c["bull_f"], c["bear_f"], sp, n_min) if with_model else []
    return dict(lp=lp, nz=nz, K=K, scan=scan, pairs=prs, beam=bms, model=mod)


def run(sym: str, window: str, excl: set):
    c = prepare(sym, window, excl)
    m = mine(c, sym, window)
    out = OUT / window / sym
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{k: v for k, v in r.items() if k != "tup"} for r in m["beam"]]).to_csv(out / "adaylar.csv",
                                                                                         index=False)
    pd.DataFrame(m["pairs"]).to_csv(out / "ciftler.csv", index=False)
    pd.DataFrame(m["model"]).to_csv(out / "model.csv", index=False)
    d = c["d"]
    json.dump(dict(sym=sym, window=window, bars=c["n"], features=len(c["fs"]), pair_k=len(m["K"]),
                   pair_thresholds={h: m["scan"][h]["thr"] for h in HS}, excluded_lookahead=len(excl),
                   start=str(d.ts.iloc[0]), end=str(d.ts.iloc[-1]), seconds=round(time.time() - c["t0"])),
              open(out / "meta.json", "w"), indent=1)


if __name__ == "__main__":
    win = sys.argv[1] if len(sys.argv) > 1 else "full_1h_NDX"
    syms = sys.argv[2].split(",") if len(sys.argv) > 2 else [win.split("_")[-1]]
    excl = EV.lookahead_sids()
    print(f"EK-P9 kombinasyon madencisi v2: pencere {win}, {len(excl)} lookahead_on script hariç", flush=True)
    for s in syms:
        run(s, win, excl)
