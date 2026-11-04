"""Kombinasyon Madencisi (PROTOCOL EK-P8): her türlü tepki karışımı + 1–4'lü çakışmalar, ufuk 1…15 ayrı ayrı.

Özellikler: script durumları *aktif* ve *taze* (≤3 bar) biçimde + "kaç script AL / kaç script SAT" karışım kovaları.
Yön verinin işaretinden okunur (scriptin AL/SAT etiketine bakılmaz). Arama yalnız keşif diliminde; doğrulama ve kasa
dokunulmadan okunur.

Kullanım: python kombo_madenci.py <pencere: recent|tf_15m> [SYM,...]
Çıktı: results_kombo/<pencere>/<SYM>/{adaylar.csv, profil.csv, model.csv, meta.json}
"""
from __future__ import annotations

import gzip
import hashlib
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gosterge_cakisma_20261025"))
sys.path.insert(0, str(HERE))
import config as GC  # noqa: E402
import data  # noqa: E402
import engine as E  # noqa: E402
import eval_scripts as EV  # noqa: E402
from pine_inceleme import _sign  # noqa: E402

HS = tuple(range(1, 16))            # kullanıcı isteği: önündeki 15 mumun her biri ayrı
FRESH_W = 3                         # "taze" = durum başlangıcı son 3 bar içinde
FREQ_MIN, FREQ_MAX = 0.01, 0.60     # keşifte özellik sıklığı aralığı
POOL = 1000                         # ışın havuzu (tekli |z| sırası)
BEAM = 100                          # her seviyede genişletilen kombinasyon sayısı
MAX_ORDER = 4
TOP_CANDS = 100
N_SHIFT = 10
MIX_BINS = 5
MODEL_FEATS = 3000
CHUNK = 15000
OUT = HERE / "results_kombo"


# ── özellik evreni ───────────────────────────────────────────────────────────
def _fresh(S: np.ndarray) -> np.ndarray:
    on = EV.onsets(S)
    R = on.copy()
    for k in range(1, FRESH_W):
        R[k:] |= on[:-k]
    return R


def build_features(sym: str, window: str, d: pd.DataFrame, excl: set):
    """→ (packed özellikler, adlar, karışım dizileri). Sıklık süzgeci + birebir kopya ayıklaması."""
    n, disc = len(d), d.split.values == 0
    names, sids, packed, meta = EV.load_states(sym, window, excl)
    feats, fnames, seen = [], [], set()
    bull = np.zeros(n, np.int32)
    bear = np.zeros(n, np.int32)
    order = np.argsort(np.array(sids, dtype=object), kind="stable")
    for idx in _script_chunks(order, sids):
        S = EV.unpack([packed[i] for i in idx], n)
        R = _fresh(S)
        _mix_counts(R, [sids[i] for i in idx], [names[i] for i in idx], bull, bear)
        for X, tag in ((S, "A"), (R, "T")):
            fr = X[disc].mean(axis=0)
            for j in np.flatnonzero((fr >= FREQ_MIN) & (fr <= FREQ_MAX)):
                b = np.packbits(X[:, j]).tobytes()
                hsh = hashlib.blake2b(b, digest_size=12).digest()
                if hsh in seen:
                    continue
                seen.add(hsh)
                feats.append(b)
                fnames.append(f"{tag}:{sids[idx[j]]}|{names[idx[j]]}")
    nsc = max(len(set(sids)), 1)
    return feats, fnames, bull / nsc, bear / nsc, {s: m[0] for s, m in meta.items()}


def _script_chunks(order, sids):
    """~CHUNK'lık parçalar; bir scriptin durumları iki parçaya bölünmez (karışım sayımı script başına)."""
    a = 0
    while a < len(order):
        b = min(a + CHUNK, len(order))
        while b < len(order) and sids[order[b]] == sids[order[b - 1]]:
            b += 1
        yield order[a:b]
        a = b


def _mix_counts(R, sids, names, bull, bear):
    """Script başına: herhangi bir taze boğa (ayı) tepkisi varsa o barda 1 sayılır."""
    sg = np.array([_sign(k) for k in names])
    sids = np.array(sids, dtype=object)
    for sid in pd.unique(sids):
        m = sids == sid
        for sgn, acc in ((1, bull), (-1, bear)):
            mm = m & (sg == sgn)
            if mm.any():
                acc += R[:, mm].any(axis=1)


def mix_features(bull_f, bear_f, disc):
    out, names = [], []
    for arr, tag in ((bull_f, "boga"), (bear_f, "ayi")):
        edges = np.unique(np.quantile(arr[disc], np.linspace(0, 1, MIX_BINS + 1)[1:-1]))
        k = np.searchsorted(edges, arr, side="right")
        for b in range(len(edges) + 1):
            out.append(k == b)
            names.append(f"MIX:{tag}_kova{b + 1}/{len(edges) + 1}")
    return np.column_stack(out), names


# ── etiket ağırlıkları (gerçek + kaydırmalar) ────────────────────────────────
def label_pack(d, tf, sym, rng):
    disc = np.flatnonzero(d.split.values == 0)
    nd = len(disc)
    offs = rng.integers(int(nd * GC.NULL_MIN_OFFSET), nd - int(nd * GC.NULL_MIN_OFFSET), N_SHIFT)
    out = {}
    for h in HS:
        L = E.labels(d, data.bucket(d, tf), h, GC.SPREAD[sym])
        W = E.weights(L)
        v, e = L["valid"][disc].astype(np.float64), L["e"][disc]
        Wsh = np.zeros((len(d), 3 * N_SHIFT))
        for k, o in enumerate(offs):
            vs, es = np.roll(v, o), np.roll(e, o)
            Wsh[disc, 3 * k:3 * k + 3] = np.column_stack([vs, es * vs, es ** 2 * vs])
        out[h] = (L, np.hstack([W, Wsh]).astype(np.float32))
    return out


def kz(A):
    """A: (m, 24 + 3·N_SHIFT) → keşif n, z (gerçek) ve kaydırma |z| maksimumu (n ≥ N_MIN olanlarda)."""
    g = E.split_stats(A[:, :24], 0)
    sh = A[:, 24:].reshape(len(A), N_SHIFT, 3)
    zs = EV.z_of(sh[..., 0], sh[..., 1], sh[..., 2])
    return g["n"], g["z"], zs


# ── arama ────────────────────────────────────────────────────────────────────
class Feats:
    """Paketli özellikler + karışım sütunları; indeksle aktif vektör (önbellekli)."""

    def __init__(self, packed, names, mix, mix_names, n):
        self.packed, self.n, self.mix = packed, n, mix
        self.names = names + mix_names
        self.F = len(packed)
        self._cache = {}

    def __len__(self):
        return len(self.names)

    def vec(self, i: int) -> np.ndarray:
        if i >= self.F:
            return self.mix[:, i - self.F]
        if i not in self._cache:
            self._cache[i] = np.unpackbits(np.frombuffer(self.packed[i], np.uint8))[:self.n].astype(bool)
        return self._cache[i]

    def mat(self, idx) -> np.ndarray:
        return np.column_stack([self.vec(int(i)) for i in idx])

    def chunks(self):
        for a in range(0, self.F, CHUNK):
            yield a, EV.unpack(self.packed[a:a + CHUNK], self.n)
        yield self.F, self.mix


def events(X: np.ndarray, h: int) -> np.ndarray:
    """Kombinasyon doğru olmaya başladığı bar (onset), ardından h bar susturma."""
    return EV.thin(EV.onsets(X), h)


def univariate(fs: Feats, lp: dict, n_min: int):
    nz = {h: np.zeros((len(fs), 2)) for h in HS}
    smax = {h: np.zeros(N_SHIFT) for h in HS}
    for a, X in fs.chunks():
        for h in HS:
            A = events(X, h).astype(np.float32).T @ lp[h][1]
            n_, z_, zs = kz(A.astype(np.float64))
            nz[h][a:a + X.shape[1]] = np.column_stack([n_, np.where(n_ >= n_min, z_, 0.0)])
            ok = n_ >= n_min
            if ok.any():
                smax[h] = np.maximum(smax[h], np.abs(zs[ok]).max(axis=0))
    return nz, smax


def beam(fs: Feats, h: int, Wh: np.ndarray, z1: np.ndarray, n1: np.ndarray, smax: np.ndarray, n_min: int):
    """Işın araması 2…MAX_ORDER; → değerlendirilen kombinasyonlar [(tuple, n, z)]."""
    ok = n1 >= n_min
    order = np.argsort(-np.abs(np.where(ok, z1, 0)))
    pool = list(order[:POOL]) + [i for i in range(fs.F, len(fs)) if i not in order[:POOL]]
    P = fs.mat(pool)
    found = [((int(i),), float(n1[i]), float(z1[i])) for i in order[:TOP_CANDS * 5] if ok[i]]
    level = [((int(i),), fs.vec(int(i))) for i in order[:BEAM] if ok[i]]
    for _ in range(2, MAX_ORDER + 1):
        nxt = {}
        for tup, v in level:
            C = v[:, None] & P
            keep = C.sum(axis=0) < v.sum()                     # yeni koşul gerçekten daraltmalı
            keep &= ~np.isin(pool, tup)
            if not keep.any():
                continue
            cols = np.flatnonzero(keep)
            A = events(C[:, cols], h).astype(np.float32).T @ Wh
            n_, z_, zs = kz(A.astype(np.float64))
            good = n_ >= n_min
            if good.any():
                smax[:] = np.maximum(smax, np.abs(zs[good]).max(axis=0))
            for c, nn, zz in zip(cols[good], n_[good], z_[good]):
                key = tuple(sorted(tup + (int(pool[c]),)))
                if key not in nxt or abs(zz) > abs(nxt[key][1]):
                    nxt[key] = (float(nn), float(zz))
        found += [(k, v[0], v[1]) for k, v in nxt.items()]
        best = sorted(nxt.items(), key=lambda kv: -abs(kv[1][1]))[:BEAM]
        level = [(k, np.logical_and.reduce([fs.vec(i) for i in k])) for k, _ in best]
    return found


def split_rows(ev_idx, Wh, L, dsg, n_min):
    vec = Wh[ev_idx, :24].astype(np.float64).sum(axis=0)
    r = {}
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
    return r


def select(fs: Feats, found, h, disc_end):
    """Keşif |z| sırası + %80 olay örtüşmesi ayıklaması → en çok TOP_CANDS aday (tuple, z, olaylar)."""
    chosen, sets = [], []
    for tup, _, z in sorted(found, key=lambda f: -abs(f[2])):
        ev = np.flatnonzero(events(np.logical_and.reduce([fs.vec(i) for i in tup])[:, None], h)[:, 0])
        evd = set(ev[ev < disc_end].tolist())
        if not evd or any(len(evd & s) / min(len(evd), len(s)) >= GC.DEDUP_OVERLAP for s in sets):
            continue
        chosen.append((tup, z, ev))
        sets.append(evd)
        if len(chosen) >= TOP_CANDS:
            break
    return chosen


# ── ufuk profili + tüm-özellik modeli ────────────────────────────────────────
def profile(fs: Feats, cands: list, lp: dict, n_min: int):
    """Her aday kombinasyonun BÜTÜN örnekleri, h = 1…15'in her birinde ayrı (yön adayın seçildiği h'den)."""
    rows = []
    for c in cands:
        X = np.logical_and.reduce([fs.vec(i) for i in c["tup"]])[:, None]
        for h in HS:
            L, Wh = lp[h]
            ev = np.flatnonzero(events(X, h)[:, 0])
            r = split_rows(ev, Wh, L, 1.0 if c["dir"] == "BUY" else -1.0, n_min)
            rows.append(dict(kombo_id=c["kombo_id"], secim_h=c["h"], dir=c["dir"], h=h, **r))
    return rows


def model(fs: Feats, nz: dict, lp: dict, bull_f, bear_f, sp, n_min):
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score
    rows = []
    for h in HS:
        L, Wh = lp[h]
        z = np.abs(nz[h][:, 1])
        idx = np.argsort(-z)[:MODEL_FEATS]
        X = np.column_stack([fs.mat(idx).astype(np.float32), bull_f, bear_f])
        y, v = (L["r"] > 0).astype(int), L["valid"]
        tr, va, te = (sp == 0) & v, (sp == 1) & v, (sp == 2) & v
        m = lgb.LGBMClassifier(n_estimators=600, learning_rate=0.03, num_leaves=15, min_child_samples=100,
                               subsample=0.8, subsample_freq=1, colsample_bytree=0.5, n_jobs=2, verbose=-1)
        m.fit(X[tr], y[tr], eval_set=[(X[va], y[va])], callbacks=[lgb.early_stopping(50, verbose=False)])
        p = m.predict_proba(X)[:, 1]
        lo, hi = np.quantile(p[sp == 1], [0.10, 0.90])            # eşik doğrulamadan (kasaya bakmadan)
        r = dict(h=h, iters=int(m.best_iteration_ or 0), kasa_auc=float(roc_auc_score(y[te], p[te])),
                 dogr_auc=float(roc_auc_score(y[va], p[va])))
        for dr, mask, dsg in (("BUY", p >= hi, 1.0), ("SELL", p <= lo, -1.0)):
            ev = np.flatnonzero(EV.thin(mask[:, None], h)[:, 0])
            s = split_rows(ev, Wh, L, dsg, n_min)
            r.update({f"{dr}_{k}": s[k] for k in ("DOGRULAMA_n", "DOGRULAMA_z", "DOGRULAMA_lift", "KASA_n", "KASA_z",
                                                     "KASA_hit", "KASA_base", "KASA_lift", "KASA_ret_bp", "KASA_cost_bp")})
        rows.append(r)
        print(f"    model h={h}: kasa AUC {r['kasa_auc']:.4f}, AL kasa z {r['BUY_KASA_z']:.2f}, "
              f"SAT kasa z {r['SELL_KASA_z']:.2f}", flush=True)
    return rows


def _readable(fname: str, sname: dict) -> str:
    """'A:<sid>|plot7|Histo|z+' → '[aktif] <script adı> · plot7|Histo|z+'."""
    if fname.startswith("MIX:"):
        return fname
    tag, rest = fname.split(":", 1)
    sid, st = rest.split("|", 1)
    return f"[{'aktif' if tag == 'A' else 'taze'}] {str(sname.get(sid, sid))[:40]} · {st}"


# ── ana akış ─────────────────────────────────────────────────────────────────
def run(sym: str, window: str, excl: set):
    t0 = time.time()
    d = EV.window_frame(sym, window)
    tf, n, sp = EV.window_tf(window), len(d), d.split.values
    n_min = GC.N_MIN[tf]
    packed, names, bull_f, bear_f, sname = build_features(sym, window, d, excl)
    mix, mix_names = mix_features(bull_f, bear_f, sp == 0)
    fs = Feats(packed, names, mix, mix_names, n)
    print(f"  {sym} {window}: {len(fs)} özellik ({time.time() - t0:.0f}s)", flush=True)
    lp = label_pack(d, tf, sym, np.random.default_rng(GC.SEED))
    nz, smax = univariate(fs, lp, n_min)
    disc_end = int(np.flatnonzero(sp == 0).max()) + 1
    cands, thr, n_eval = [], {}, {}
    for h in HS:
        found = beam(fs, h, lp[h][1], nz[h][:, 1], nz[h][:, 0], smax[h], n_min)
        n_eval[h] = len(fs) + len(found)
        thr[h] = float(np.quantile(smax[h], 0.95))
        for tup, z, ev in select(fs, found, h, disc_end):
            dsg = 1.0 if z > 0 else -1.0
            r = split_rows(ev, lp[h][1], lp[h][0], dsg, n_min)
            cands.append(dict(kombo_id=f"{sym}-h{h}-{len(cands)}", sym=sym, window=window, h=h, derece=len(tup),
                              dir="BUY" if dsg > 0 else "SELL", kosullar=" & ".join(fs.names[i] for i in tup),
                              kosullar_ad=" & ".join(_readable(fs.names[i], sname) for i in tup),
                              tup=tup, kesif_esik_ustu=abs(z) >= thr[h], **r))
        hc = [c for c in cands if c["h"] == h]
        print(f"  {sym} h={h}: {n_eval[h]} kombinasyon, eşik {thr[h]:.2f}, eşik üstü "
              f"{sum(c['kesif_esik_ustu'] for c in hc)}, kanıtlı {sum(c['kanitli'] for c in hc)}, doğr {sum(c['val_ok'] for c in hc)}"
              f"/{sum(c['val_wrong'] for c in hc)} ({time.time() - t0:.0f}s)", flush=True)
    prof = profile(fs, [c for c in cands if c["val_ok"]], lp, n_min)
    mod = model(fs, nz, lp, bull_f, bear_f, sp, n_min)
    out = OUT / window / sym
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{k: v for k, v in c.items() if k != "tup"} for c in cands]).to_csv(out / "adaylar.csv", index=False)
    pd.DataFrame(prof).to_csv(out / "profil.csv", index=False)
    pd.DataFrame(mod).to_csv(out / "model.csv", index=False)
    json.dump(dict(sym=sym, window=window, bars=n, features=len(fs), thresholds=thr, evaluated=n_eval,
                   excluded_lookahead=len(excl), start=str(d.ts.iloc[0]), end=str(d.ts.iloc[-1]),
                   seconds=round(time.time() - t0)), open(out / "meta.json", "w"), indent=1)


if __name__ == "__main__":
    win = sys.argv[1] if len(sys.argv) > 1 else "recent"
    syms = sys.argv[2].split(",") if len(sys.argv) > 2 else ["NDX", "DAX", "XAU", "USOIL"]
    excl = EV.lookahead_sids()
    print(f"EK-P8 kombinasyon madencisi: pencere {win}, {len(excl)} lookahead_on script hariç", flush=True)
    for s in syms:
        run(s, win, excl)
