"""seq_engine.py — değişken uzunluklu MUM DİZİSİ motifleri (mum-mum sapma payıyla).

Kullanıcı tanımı (2026-10-02): "100 mumun hepsi benzer olsun demedim; 100 mumluk alan
içinden herhangi sayıda mumun benzer olması — her mumun belirli sapma payı
büyüklük/küçüklüğü ile". Buna göre:

Mum özellikleri (% , mumun KENDİ açılışına göre):
    h = 100·(High/Open − 1)   l = 100·(Low/Open − 1)   c = 100·(Close/Open − 1)
İki mum benzer  ⇔  |Δh|, |Δl|, |Δc| ≤ tol   (gövde + iki fitil aynı payda)
Model (motif)  = ardışık k mumluk dizi; başka bir yerdeki k mumun HER BİRİ eşleşirse
                 bir tekrar sayılır. k serbest (3 … 100) → "100 mumluk alan" üst sınır.

Hesap: tüm mum çiftleri (s, t) için köşegen boyunca "s ve t'den başlayan eşleşen
mum koşusu" R(s,t) bir kez hesaplanır (n²/2 hücre, numba paralel). Her başlangıç s
ve uzunluk k için C_k(s) = #{t : min(R, |t−s|) ≥ k} (kendi kaydırmasıyla çakışan
önemsiz eşleşmeler hariç). Motif seçimi: C_k sıralı adaylar → kesin çakışmasız
örnek listesi → tembel-açgözlü (CELF).

Uygunluk: motifin mumlarının medyan aralığı ≥ ELIG_RATIO·tol — yoksa en çok "tekrar
eden" şey sessiz dönemlerin minik mumları olur (pay mumdan büyükse her şey eşleşir).

Plasebo: her mum %50 olasılıkla aynalanır (h,l,c) → (−l,−h,−c): mum boyları aynen
korunur, yön dizilimi rastgele olur. Gerçek tekrar sayısı plaseboyu geçmiyorsa
"model" tesadüf geometrisidir.
"""
from __future__ import annotations

import heapq

import numba as nb
import numpy as np

KS = np.array([3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 75, 100], dtype=np.int64)
ELIG_RATIO = 3.0
N_CHUNK = 8


def candle_features(o: np.ndarray, h: np.ndarray, l: np.ndarray, c: np.ndarray) -> np.ndarray:
    """[n×3] float32: tepe/dip/kapanış, açılışa göre %."""
    return np.stack([100 * (h / o - 1), 100 * (l / o - 1), 100 * (c / o - 1)], 1).astype(np.float32)


def breaks(seg: np.ndarray) -> np.ndarray:
    """brk[i]=1 → i ile i+1 arasında veri boşluğu (dizi bunun üstünden geçemez)."""
    b = np.zeros(len(seg), np.uint8)
    b[:-1] = seg[:-1] != seg[1:]
    b[-1] = 1
    return b


def mirror_placebo(X: np.ndarray, seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    flip = rng.random(len(X)) < 0.5
    Y = X.copy()
    Y[flip, 0] = -X[flip, 1]
    Y[flip, 1] = -X[flip, 0]
    Y[flip, 2] = -X[flip, 2]
    return Y


@nb.njit(parallel=True, fastmath=True, cache=True)
def diag_counts(X, brk, tol, Ks, nchunk):
    """C[s, kk] = s'den başlayan Ks[kk] uzunluklu diziyle eşleşen (çakışmasız) konum sayısı.

    Ayrıca en uzun tekrar eden dizi (uzunluk, s, t).
    """
    n = X.shape[0]
    nk = Ks.shape[0]
    kmin = Ks[0]
    C = np.zeros((nchunk, n, nk), np.int32)
    best = np.zeros((nchunk, 3), np.int64)
    for c in nb.prange(nchunk):
        for d in range(1 + c, n, nchunk):
            r = 0
            for i in range(n - d - 1, -1, -1):
                t = i + d
                x0 = X[i, 0] - X[t, 0]
                x1 = X[i, 1] - X[t, 1]
                x2 = X[i, 2] - X[t, 2]
                if x0 <= tol and x0 >= -tol and x1 <= tol and x1 >= -tol and x2 <= tol and x2 >= -tol:
                    if brk[i] == 0 and brk[t] == 0:
                        r = r + 1
                    else:
                        r = 1
                else:
                    r = 0
                    continue
                e = r if r < d else d
                if e > best[c, 0]:
                    best[c, 0] = e
                    best[c, 1] = i
                    best[c, 2] = t
                if e >= kmin:
                    for kk in range(nk):
                        if e >= Ks[kk]:
                            C[c, i, kk] += 1
                            C[c, t, kk] += 1
                        else:
                            break
    out = np.zeros((n, nk), np.int32)
    for c in range(nchunk):
        out += C[c]
    bi = 0
    for c in range(nchunk):
        if best[c, 0] > best[bi, 0]:
            bi = c
    return out, best[bi]


@nb.njit(fastmath=True, cache=True)
def seq_matches(X, brk, s, k, tol):
    """s'den başlayan k mumlu diziyle HER mumu eşleşen tüm t (|t−s| ≥ k) + RMS sapma."""
    n = X.shape[0]
    ts = np.empty(n, np.int64)
    rm = np.empty(n, np.float32)
    m = 0
    for t in range(0, n - k + 1):
        if t > s - k and t < s + k:
            continue
        ok = True
        ss = 0.0
        for j in range(k):
            for f in range(3):
                x = X[s + j, f] - X[t + j, f]
                if x > tol or x < -tol:
                    ok = False
                    break
                ss += x * x
            if not ok:
                break
            if j < k - 1 and brk[t + j] == 1:
                ok = False
                break
        if ok:
            ts[m] = t
            rm[m] = np.sqrt(ss / (3 * k))
            m += 1
    return ts[:m], rm[:m]


@nb.njit(fastmath=True, cache=True)
def template_counts(X, brk, T, tol):
    """Şablonun (k mum) her konumdaki eşleşen mum sayısı (kısmi benzerlik) — tam eşleşme = k."""
    n = X.shape[0]
    k = T.shape[0]
    out = np.full(n, -1, np.int32)
    for t in range(0, n - k + 1):
        okseg = True
        for j in range(k - 1):
            if brk[t + j] == 1:
                okseg = False
                break
        if not okseg:
            continue
        cnt = 0
        for j in range(k):
            good = True
            for f in range(3):
                x = T[j, f] - X[t + j, f]
                if x > tol or x < -tol:
                    good = False
                    break
            if good:
                cnt += 1
        out[t] = cnt
    return out


def greedy_spaced(ts: np.ndarray, key: np.ndarray, k: int, taken: np.ndarray) -> list[int]:
    """En iyi anahtardan başlayarak birbirine ve 'taken'a ≥ k uzak başlangıçlar."""
    tk = np.sort(taken.astype(np.int64))
    picked: list[int] = []
    for idx in np.argsort(key, kind="stable"):
        t = int(ts[idx])
        pos = np.searchsorted(tk, t)
        if pos > 0 and t - tk[pos - 1] < k:
            continue
        if pos < tk.size and tk[pos] - t < k:
            continue
        picked.append(t)
        tk = np.insert(tk, pos, t)
    return picked


def eligible_starts(X: np.ndarray, brk: np.ndarray, k: int, tol: float) -> np.ndarray:
    """Dizi içinde boşluk yok + medyan mum aralığı ≥ ELIG_RATIO·tol."""
    n = len(X)
    rng = X[:, 0] - X[:, 1]
    if n < k:
        return np.zeros(n, bool)
    win = np.lib.stride_tricks.sliding_window_view(rng, k)
    med = np.median(win, axis=1)
    cb = np.concatenate([[0], np.cumsum(brk[:-1])])          # i..i+k−1 arası kırılma sayısı
    nb_ = cb[k - 1:] - cb[: n - k + 1]
    ok = (med >= ELIG_RATIO * tol) & (nb_ == 0)
    out = np.zeros(n, bool)
    out[: n - k + 1] = ok
    return out


def select_motifs(X: np.ndarray, brk: np.ndarray, Ck: np.ndarray, k: int, tol: float,
                  elig: np.ndarray, k_top: int = 3, n_cand: int = 400) -> list[dict]:
    """C_k ile sıralı adaylardan çakışmasız tekrar sayısı en yüksek k_top motif."""
    cand = np.where(elig & (Ck > 0))[0]
    cand = cand[np.argsort(-Ck[cand], kind="stable")[:n_cand]]
    cache: dict[int, tuple] = {}

    def exact(s: int, used: np.ndarray):
        if s not in cache:
            ts, rm = seq_matches(X, brk, s, k, np.float32(tol))
            keep = elig[ts]
            cache[s] = (ts[keep], rm[keep])
        ts, rm = cache[s]
        picked = greedy_spaced(ts, rm, k, np.concatenate([used, [s]]))
        return len(picked) + 1, picked

    heap = [(-(int(Ck[s]) + 1), -1, int(s)) for s in cand]
    heapq.heapify(heap)
    used = np.empty(0, np.int64)
    fam: set[int] = set()
    motifs: list[dict] = []
    for rnd in range(k_top):
        chosen = None
        while heap:
            negc, stamp, s = heapq.heappop(heap)
            if s in fam or (used.size and np.min(np.abs(used - s)) < k):
                continue
            if stamp == rnd:
                chosen = s
                break
            c, _ = exact(s, used)
            heapq.heappush(heap, (-c, rnd, s))
        if chosen is None:
            break
        c, picked = exact(chosen, used)
        if c < 2:
            break
        ts, rm = cache[chosen]
        lut = dict(zip(ts.tolist(), rm.tolist()))
        motifs.append({"start": int(chosen), "k": k, "count": int(c),
                       "occ": [int(chosen)] + [int(t) for t in picked],
                       "rms": [0.0] + [round(float(lut[t]), 4) for t in picked]})
        used = np.concatenate([used, [chosen], np.array(picked, np.int64)])
        fam.update(int(t) for t in ts)
        fam.add(int(chosen))
    return motifs


def max_in_window(occ: list[int], span: int = 100) -> int:
    """Aynı 'span' mumluk alanda en fazla kaç örnek (iç içe tekrar yoğunluğu)."""
    o = np.sort(np.array(occ))
    best, j = 1, 0
    for i in range(len(o)):
        while o[i] - o[j] >= span:
            j += 1
        best = max(best, i - j + 1)
    return int(best)


# ─── Kısmi eşleşme: k mumun en az q'su pay içinde (uzun diziler için) ─────────
KS_PARTIAL = np.array([10, 15, 20, 30, 50, 75, 100], dtype=np.int64)
QS_PARTIAL = (0.9, 0.8, 0.7)
ELIG_RATIO_PARTIAL = 1.5      # pay ≤ mum medyan boyunun 2/3'ü (kısmi modda biraz gevşek)


def run_lengths(brk: np.ndarray) -> np.ndarray:
    """run[i] = i'den başlayıp veri boşluğu geçmeyen en uzun dizi uzunluğu."""
    n = len(brk)
    run = np.ones(n, np.int64)
    for i in range(n - 2, -1, -1):
        run[i] = 1 if brk[i] else run[i + 1] + 1
    return run


def need_table(Ks: np.ndarray, Qs: tuple[float, ...]) -> np.ndarray:
    """need[kk, qq] = k mumdan en az kaçının tutması gerektiği (Qs azalan sırada)."""
    return np.array([[int(np.ceil(q * k - 1e-9)) for q in Qs] for k in Ks], dtype=np.int64)


@nb.njit(parallel=True, fastmath=True, cache=True)
def diag_counts_partial(X, run, E, tol, Ks, need, nchunk):
    """C[s, kk, qq] = s'den başlayan Ks[kk] mumluk dizinin, mumlarının ≥ need[kk,qq]'si
    tutan (ilk mumu tutan, çakışmasız) eşleşme sayısı.

    E[i, kk] = i'den başlayan Ks[kk] mumluk dizi uygun mu (pay ≤ medyan mum boyu oranı).
    Yalnız iki ucu da uygun çiftler sayılır — motif seçimi zaten uygunları kullanır; geniş
    payda (mumların çoğu eşleşirken) sayımı uygun dizilere indirip hesabı kısaltır.
    """
    n = X.shape[0]
    nk = Ks.shape[0]
    nq = need.shape[1]
    kmin = Ks[0]
    C = np.zeros((nchunk, n, nk, nq), np.int32)
    for c in nb.prange(nchunk):
        pref = np.zeros(n + 1, np.int32)
        for d in range(kmin + c, n, nchunk):
            L = n - d
            s = 0
            for i in range(L):
                t = i + d
                x0 = X[i, 0] - X[t, 0]
                x1 = X[i, 1] - X[t, 1]
                x2 = X[i, 2] - X[t, 2]
                if x0 <= tol and x0 >= -tol and x1 <= tol and x1 >= -tol and x2 <= tol and x2 >= -tol:
                    s += 1
                pref[i + 1] = s
            if s < need[0, nq - 1]:
                continue
            for i in range(L - kmin + 1):
                if pref[i + 1] == pref[i]:
                    continue
                ri = run[i]
                rt = run[i + d]
                for kk in range(nk):
                    k = Ks[kk]
                    if k > d or i + k > L or ri < k or rt < k:
                        break
                    if E[i, kk] == 0 or E[i + d, kk] == 0:
                        continue
                    S = pref[i + k] - pref[i]
                    if S < need[kk, nq - 1]:
                        continue
                    for qq in range(nq):
                        if S >= need[kk, qq]:
                            C[c, i, kk, qq] += 1
                            C[c, i + d, kk, qq] += 1
    out = np.zeros((n, nk, nq), np.int32)
    for c in range(nchunk):
        out += C[c]
    return out


@nb.njit(fastmath=True, cache=True)
def seq_matches_partial(X, run, s, k, tol, need):
    """s'den başlayan k mumla ≥ need mumu tutan tüm t (ilk mum tutmalı, |t−s| ≥ k)."""
    n = X.shape[0]
    ts = np.empty(n, np.int64)
    ms = np.empty(n, np.int32)
    rm = np.empty(n, np.float32)
    m = 0
    allow = k - need
    for t in range(0, n - k + 1):
        if t > s - k and t < s + k:
            continue
        if run[t] < k:
            continue
        miss = 0
        ss = 0.0
        ok = True
        for j in range(k):
            good = True
            for f in range(3):
                x = X[s + j, f] - X[t + j, f]
                ss += x * x
                if x > tol or x < -tol:
                    good = False
            if not good:
                if j == 0:
                    ok = False
                    break
                miss += 1
                if miss > allow:
                    ok = False
                    break
        if ok:
            ts[m] = t
            ms[m] = k - miss
            rm[m] = np.sqrt(ss / (3 * k))
            m += 1
    return ts[:m], ms[:m], rm[:m]


_MED_CACHE: dict[tuple, tuple[np.ndarray, np.ndarray]] = {}


def _window_median(X: np.ndarray, brk: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """(k mumluk kayan medyan aralık, pencere içi kırılma yok) — paydan bağımsız, önbellekli."""
    key = (id(X), X.shape[0], k)
    if key not in _MED_CACHE:
        n = len(X)
        rng = np.abs(X[:, 0] - X[:, 1])      # aynalı plaseboda da aynı boy
        med = np.median(np.lib.stride_tricks.sliding_window_view(rng, k), axis=1)
        cb = np.concatenate([[0], np.cumsum(brk[:-1])])
        clean = (cb[k - 1:] - cb[: n - k + 1]) == 0
        _MED_CACHE[key] = (med, clean)
    return _MED_CACHE[key]


def eligible_ratio(X: np.ndarray, brk: np.ndarray, k: int, tol: float, ratio: float) -> np.ndarray:
    """eligible_starts'ın oran parametreli hâli."""
    n = len(X)
    out = np.zeros(n, bool)
    if n < k:
        return out
    med, clean = _window_median(X, brk, k)
    out[: n - k + 1] = (med >= ratio * tol) & clean
    return out


def eligibility_matrix(X: np.ndarray, brk: np.ndarray, Ks: np.ndarray, tol: float, ratio: float) -> np.ndarray:
    """E[i, kk] (uint8) — diag_counts_partial için."""
    return np.ascontiguousarray(np.stack([eligible_ratio(X, brk, int(k), tol, ratio) for k in Ks], 1)
                                .astype(np.uint8))


def select_partial(X: np.ndarray, run: np.ndarray, Ck: np.ndarray, k: int, tol: float, need: int,
                   elig: np.ndarray, k_top: int = 6, n_cand: int = 400) -> list[dict]:
    """select_motifs'in kısmi-eşleşme hâli (need=k → birebir)."""
    cand = np.where(elig & (Ck > 0))[0]
    cand = cand[np.argsort(-Ck[cand], kind="stable")[:n_cand]]
    cache: dict[int, tuple] = {}

    def exact(s: int, used: np.ndarray):
        if s not in cache:
            ts, ms, rm = seq_matches_partial(X, run, s, k, np.float32(tol), need)
            keep = elig[ts]
            cache[s] = (ts[keep], ms[keep], rm[keep])
        ts, ms, rm = cache[s]
        picked = greedy_spaced(ts, -ms * 10.0 + rm, k, np.concatenate([used, [s]]))
        return len(picked) + 1, picked

    heap = [(-(int(Ck[s]) + 1), -1, int(s)) for s in cand]
    heapq.heapify(heap)
    used = np.empty(0, np.int64)
    fam: set[int] = set()
    motifs: list[dict] = []
    for rnd in range(k_top):
        chosen = None
        while heap:
            negc, stamp, s = heapq.heappop(heap)
            if s in fam or (used.size and np.min(np.abs(used - s)) < k):
                continue
            if stamp == rnd:
                chosen = s
                break
            c, _ = exact(s, used)
            heapq.heappush(heap, (-c, rnd, s))
        if chosen is None:
            break
        c, picked = exact(chosen, used)
        if c < 2:
            break
        ts, ms, rm = cache[chosen]
        lut = {int(t): (int(a), float(b)) for t, a, b in zip(ts, ms, rm)}
        motifs.append({"start": int(chosen), "k": k, "count": int(c), "need": need,
                       "occ": [int(chosen)] + [int(t) for t in picked],
                       "matched": [k] + [lut[t][0] for t in picked],
                       "rms": [0.0] + [round(lut[t][1], 4) for t in picked]})
        used = np.concatenate([used, [chosen], np.array(picked, np.int64)])
        fam.update(int(t) for t in ts)
        fam.add(int(chosen))
    return motifs
