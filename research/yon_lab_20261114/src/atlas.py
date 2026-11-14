"""Faz 4 (şans haritası) + Faz 5 (kombinatoryal tarama) — gerçek ve martingal koşulara AYNI kod.

python src/atlas.py <etiket>   → results/atlas_<etiket>/*.parquet + özet json (max |t| dahil)
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

import core as C
import refs as R

RES = C.H / 'results'
LABELS = ['dir_15m', 'dir_1h', 'dir_4h', 'dir_sess', 'sym_1']
NEAR_ATR = 0.25
REACT_ATR = 0.5
REACT_WIN = 240
TOUCH_WIN = 240
TOP_SINGLES = 40
TOP_PAIRS = 10
TOP_TRIPLE_SINGLES = 20
MIN_N = 300                      # hücre en az bu kadar satır (≈ 75 bağımsız saat)


# ───────────────────────────── yardımcılar ─────────────────────────────

def cluster_t(r: np.ndarray, day: np.ndarray) -> tuple[float, float, int]:
    """Gün-kümeli ortalama ve t (oran tahmincisi)."""
    if len(r) < 2:
        return np.nan, np.nan, len(r)
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=r)
    n = np.bincount(inv).astype(float)
    m = S.sum() / n.sum()
    D = len(u)
    if D < 3:
        return m, np.nan, len(r)
    var = ((S - m * n) ** 2).sum() * D / (D - 1) / n.sum() ** 2
    return m, m / np.sqrt(var) if var > 0 else np.nan, len(r)


def indep(t: np.ndarray, gap: int = 3600) -> int:
    t = np.sort(t)
    return int(1 + (np.diff(t) >= gap).sum()) if len(t) else 0


def stat_row(r, day, t, halfmask) -> dict:
    m, tt, n = cluster_t(r, day)
    m1, _, _ = cluster_t(r[halfmask], day[halfmask])
    m2, _, _ = cluster_t(r[~halfmask], day[~halfmask])
    return {'n': n, 'n_indep': indep(t), 'fazla': m, 't': tt, 'h1': m1, 'h2': m2,
            'same_sign': bool(np.sign(m1) == np.sign(m2) and np.sign(m1) == np.sign(m))}


class Run:
    def __init__(self, tag: str):
        d = C.H / 'data' / f'run_{tag}'
        self.tag = tag
        self.lab = pd.read_parquet(d / 'labels.parquet')
        self.F = pd.read_parquet(d / 'features.parquet')
        self.R = pd.read_parquet(d / 'refs.parquet')
        self.X = pd.read_parquet(d / 'extras.parquet')
        z = np.load(d / 'fh.npz')
        self.FU, self.FD = z['FU'], z['FD']
        L = self.lab
        self.td = L.t.to_numpy()
        self.per = L.period.to_numpy()
        self.K = self.per == 'K'
        kmask = self.K & np.isfinite(L.volr.to_numpy())
        self.edges = np.nanquantile(L.volr.to_numpy()[kmask], np.linspace(0.1, 0.9, 9))
        self.strat = C.strata(self.td, L.volr.to_numpy(), self.edges)
        self.sidx = pd.factorize(self.strat)[0]
        self.day = L.day.to_numpy()
        self.price = L.price.to_numpy()
        self.a1 = L.atr1.to_numpy()
        kt = self.td[self.K]
        self.kmid = np.median(kt) if len(kt) else 0
        self._ghost = None

    def sameday_sums(self, rows: np.ndarray, ub: np.ndarray, db: np.ndarray):
        """Satır başına: aynı (kova, gün) grubundaki noktaların (ub, db) yarışında yukarı-önce ve çözülme toplamları."""
        if not hasattr(self, '_grp'):
            key = self.sidx.astype(np.int64) * 100000 + (self.day - self.day.min())
            order = np.argsort(key, kind='stable')
            ks = key[order]
            start = np.r_[0, np.flatnonzero(np.diff(ks)) + 1]
            gid = np.empty(len(key), dtype=np.int64)
            gid[order] = np.repeat(np.arange(len(start)), np.diff(np.r_[start, len(ks)]))
            self._grp = (order, start, gid, np.diff(np.r_[start, len(ks)]))
        order, start, gid, size = self._grp
        g = gid[rows]
        su = np.zeros(len(rows))
        sr = np.zeros(len(rows))
        maxk = int(size.max())
        for k in range(maxk):
            has = size[g] > k
            j = order[start[g[has]] + k]
            r = C.race_from_tables(self.FU, self.FD, ub[has], db[has], j)
            su[has] += (r == 1)
            sr[has] += np.isin(r, (1, -1))
        return su, sr

    def half(self, m):
        return self.td[m] < self.kmid

    # ── hayalet tablosu: G[s, ub, db] = (yukarı önce sayısı, çözülen sayısı)
    def ghost(self):
        if self._ghost is not None:
            return self._ghost
        S = self.sidx.max() + 1
        Gu = np.zeros((S, C.NK, C.NK), dtype=np.float32)
        Gr = np.zeros((S, C.NK, C.NK), dtype=np.float32)
        FU, FD = self.FU.astype(np.int32), self.FD.astype(np.int32)
        for ub in range(C.NK):
            fu = FU[:, ub][:, None]
            up = (fu < FD) & (fu < C.NOHIT)
            dn = (FD < fu) & (FD < C.NOHIT)
            for db in range(C.NK):
                Gu[:, ub, db] = np.bincount(self.sidx, weights=up[:, db], minlength=S)
                Gr[:, ub, db] = np.bincount(self.sidx, weights=(up[:, db] | dn[:, db]), minlength=S)
        self._ghost = (Gu, Gr)
        return self._ghost


def binidx(dist: np.ndarray) -> np.ndarray:
    """Uzaklık (ATR) → yukarı yuvarlanmış kova indeksi (0 … NK−1); seviye = (idx+1)·0,05."""
    return np.clip(np.ceil(dist / C.STEP_ATR - 1e-9).astype(int) - 1, 0, C.NK - 1)


def race_eval(run: Run, rows: np.ndarray, ub: np.ndarray, db: np.ndarray) -> pd.DataFrame:
    Gu, Gr = run.ghost()
    r = C.race_from_tables(run.FU, run.FD, ub, db, rows)
    up = (r == 1).astype(float)
    res = np.isin(r, (1, -1))
    s = run.sidx[rows]
    # aynı (kova, gün) grubundaki TÜM noktalar (kendisi dahil) hayalet havuzundan çıkarılır: aynı yolu paylaşırlar
    su, sr = run.sameday_sums(rows, ub, db)
    gu = Gu[s, ub, db] - su
    gr = Gr[s, ub, db] - sr
    pg = np.where(gr > 20, gu / np.maximum(gr, 1), np.nan)
    p0 = (db + 1) / ((ub + 1) + (db + 1))
    return pd.DataFrame({'row': rows, 'up': up, 'res': res, 'pg': pg, 'p0': p0})


# ───────────────────────────── Faz 4A: aile yarışı ─────────────────────────────

def family_levels(run: Run) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    cols = list(run.R.columns)
    fams = R.member_groups(cols)
    out = {}
    for f, cs in fams.items():
        U, D, _, _ = R.nearest(run.R, cs, run.price, run.a1)
        out[f] = (U, D)
    # CLU: ≥ 2 farklı ailenin en yakın üst (alt) seviyesi ±0,3 ATR içinde → en yakın böyle bölge
    base = dict(out)
    clu = []
    for side in (0, 1):
        M = np.column_stack([v[side] for v in base.values()])
        Ms = np.sort(np.where(np.isnan(M), np.inf, M), axis=1)
        close = np.diff(Ms, axis=1) <= 0.3
        first = np.where(close.any(1), Ms[np.arange(len(Ms)), close.argmax(1)], np.inf)
        clu.append(np.where(np.isfinite(first), first, np.nan))
    out['CLU'] = tuple(clu)
    return out


def atlas_family(run: Run, fl: dict) -> pd.DataFrame:
    rows = []
    for f, (U, D) in fl.items():
        m = np.isfinite(U) & np.isfinite(D)
        for per in ('K', 'D', 'T'):
            pm = m & (run.per == per)
            idx = np.where(pm)[0]
            if len(idx) < MIN_N:
                continue
            ev = race_eval(run, idx, binidx(U[idx]), binidx(D[idx]))
            ok = ev.res.to_numpy() & np.isfinite(ev.pg.to_numpy())
            e = ev[ok]
            rr = e.up.to_numpy() - e.pg.to_numpy()
            st = stat_row(rr, run.day[e.row], run.td[e.row], run.half(e.row.to_numpy()) if per == 'K' else run.td[e.row] < np.median(run.td[e.row]))
            rows.append({'aile': f, 'donem': per, 'olcu': 'yaris_hayalet', **st,
                         'p_gozlenen': e.up.mean(), 'p_hayalet': e.pg.mean(), 'p_analitik': e.p0.mean(),
                         'fazla_analitik': (e.up - e.p0).mean(), 'cozulme': ev.res.mean()})
    return pd.DataFrame(rows)


def calib_curve(run: Run, fl: dict, fam: str = 'PIV') -> pd.DataFrame:
    U, D = fl[fam]
    m = np.isfinite(U) & np.isfinite(D) & run.K
    idx = np.where(m)[0]
    ev = race_eval(run, idx, binidx(U[idx]), binidx(D[idx]))
    ev = ev[ev.res & np.isfinite(ev.pg)]
    q = pd.cut(ev.p0, np.linspace(0, 1, 11))
    return ev.groupby(q, observed=True).agg(n=('up', 'size'), gozlenen=('up', 'mean'), analitik=('p0', 'mean'),
                                            hayalet=('pg', 'mean')).reset_index().assign(aile=fam)


# ───────────────────────────── Faz 4B: üye "mıknatıs / duvar" ─────────────────────────────

def member_series(run: Run) -> dict[str, np.ndarray]:
    out = {c: run.R[c].to_numpy(dtype=float) for c in R.single_members(list(run.R.columns))}
    for tf in ('M15', 'H1', 'H4'):
        for k in R.PIV_K:
            cs = [c for c in run.R.columns if c.startswith(f'PIV_{tf}_k{k}_')]
            U, D, _, _ = R.nearest(run.R, cs, run.price, run.a1, hi=1.5)
            out[f'PIVNEAR_{tf}_k{k}_U'] = run.price + U * run.a1
            out[f'PIVNEAR_{tf}_k{k}_D'] = run.price - D * run.a1
    return out


def atlas_members(run: Run, ms: dict) -> pd.DataFrame:
    """Üye seviye p'nin üstünde (altında) d ∈ [0,05; 1,5] ATR iken: o seviyeye, aynı uzaklıktaki karşı (sahte) seviyeden
    önce değme oranı − hayalet (aynı kova, aynı d her iki tarafta). >0 mıknatıs, <0 duvar."""
    rows = []
    for name, L in ms.items():
        d = (L - run.price) / run.a1
        for per in ('K', 'D', 'T'):
            for side, sel in ((1, (d >= 0.05) & (d <= 1.5)), (-1, (-d >= 0.05) & (-d <= 1.5))):
                pm = sel & (run.per == per)
                idx = np.where(pm)[0]
                if len(idx) < MIN_N:
                    continue
                b_ = binidx(np.abs(d[idx]))
                ev = race_eval(run, idx, b_, b_)
                ok = ev.res.to_numpy() & np.isfinite(ev.pg.to_numpy())
                e = ev[ok]
                touch = e.up.to_numpy() if side == 1 else 1 - e.up.to_numpy()
                pgt = e.pg.to_numpy() if side == 1 else 1 - e.pg.to_numpy()
                rr = touch - pgt
                hm = run.half(e.row.to_numpy()) if per == 'K' else run.td[e.row] < np.median(run.td[e.row])
                st = stat_row(rr, run.day[e.row], run.td[e.row], hm)
                rows.append({'uye': name, 'aile': R.family(name.replace('PIVNEAR', 'PIV')), 'taraf': 'ust' if side == 1 else 'alt',
                             'donem': per, 'olcu': 'once_degme_hayalet', **st, 'p_gozlenen': touch.mean(), 'p_hayalet': pgt.mean()})
    return pd.DataFrame(rows)


# ───────────────────────────── Faz 4C: değdikten sonra ret / kırılım ─────────────────────────────

def reaction_events(b: pd.DataFrame, run: Run, L: np.ndarray, side: int, rows: np.ndarray) -> np.ndarray:
    """rows: seviyeye ≤0,25 ATR uzak ızgara noktaları. Dönen: +1 kırılım, −1 ret, 0 çözülmedi/değmedi, nan belirsiz."""
    t, hi, lo = b.t.to_numpy(), b.high.to_numpy(), b.low.to_numpy()
    n = len(t)
    out = np.full(len(rows), np.nan)
    i1 = run.lab.i1.to_numpy()
    for s in range(0, len(rows), 4000):
        r = rows[s:s + 4000]
        lv, A = L[r], run.a1[r]
        J = i1[r][:, None] + 1 + np.arange(TOUCH_WIN + REACT_WIN)[None, :]
        inb = J < n
        Jc = np.where(inb, J, n - 1)
        ok = inb & (t[Jc] < run.td[r][:, None] + (TOUCH_WIN + REACT_WIN) * 60)
        gap = np.zeros_like(ok)
        gap[:, 1:] = np.diff(t[Jc], axis=1) > C.GAP_S
        ok &= ~np.maximum.accumulate(gap, axis=1)
        H_, L_ = hi[Jc], lo[Jc]
        touch = ok & ((H_ >= lv[:, None]) if side == 1 else (L_ <= lv[:, None]))
        touch[:, TOUCH_WIN:] = False
        has = touch.any(1)
        tau = touch.argmax(1)
        k = np.arange(J.shape[1])[None, :]
        after = ok & (k > tau[:, None]) & (k <= tau[:, None] + REACT_WIN)
        brk = after & ((H_ >= (lv + REACT_ATR * A)[:, None]) if side == 1 else (L_ <= (lv - REACT_ATR * A)[:, None]))
        rej = after & ((L_ <= (lv - REACT_ATR * A)[:, None]) if side == 1 else (H_ >= (lv + REACT_ATR * A)[:, None]))
        big = 10**6
        fb = np.where(brk.any(1), brk.argmax(1), big)
        fr = np.where(rej.any(1), rej.argmax(1), big)
        o = np.where(fb < fr, 1.0, np.where(fr < fb, -1.0, 0.0))
        o[(fb == fr) & (fb < big)] = np.nan
        o[~has] = 0.0
        out[s:s + 4000] = o
    return out


def ghost_reaction_table(run: Run) -> dict:
    """Hayalet ret/kırılım: aynı kova × yaklaşma kovası (ret15) × taraf; p_j'den ±0,5 ATR, yaklaşma yönünde devam = kırılım."""
    k = int(round(REACT_ATR / C.STEP_ATR)) - 1
    r = C.race_from_tables(run.FU, run.FD, np.full(len(run.td), k), np.full(len(run.td), k))
    ab = np.digitize(np.nan_to_num(run.lab.ret15.to_numpy()), [-1.0, -0.3, 0.0, 0.3, 1.0])
    df = pd.DataFrame({'s': run.sidx, 'a': ab, 'up': (r == 1).astype(float), 'res': np.isin(r, (1, -1)).astype(float)})
    g = df.groupby(['s', 'a']).agg(up=('up', 'sum'), res=('res', 'sum'))
    return {'tab': g, 'ab': ab}


def atlas_reaction(b: pd.DataFrame, run: Run, ms: dict) -> pd.DataFrame:
    gt = ghost_reaction_table(run)
    tab, ab = gt['tab'], gt['ab']
    key = pd.MultiIndex.from_arrays([run.sidx, ab])
    gu = tab.up.reindex(key).to_numpy()
    gr = tab.res.reindex(key).to_numpy()
    rows = []
    for name, L in ms.items():
        d = (L - run.price) / run.a1
        for side, sel in ((1, (d > 0) & (d <= NEAR_ATR)), (-1, (d < 0) & (-d <= NEAR_ATR))):
            for per in ('K', 'D', 'T'):
                idx = np.where(sel & (run.per == per))[0]
                if len(idx) < MIN_N:
                    continue
                # aynı üye için 60 dk refrakter
                tt = run.td[idx]
                keep = np.r_[True, np.diff(tt) >= 3600]
                idx = idx[keep]
                if len(idx) < MIN_N // 3:
                    continue
                o = reaction_events(b, run, L, side, idx)
                ok = np.isin(o, (1, -1))
                pg_up = gu[idx] / np.maximum(gr[idx], 1)
                pg_brk = pg_up if side == 1 else 1 - pg_up
                brk = (o == 1).astype(float)
                rr = (brk - pg_brk)[ok]
                ii = idx[ok]
                hm = run.half(ii) if per == 'K' else run.td[ii] < np.median(run.td[ii])
                st = stat_row(rr, run.day[ii], run.td[ii], hm)
                rows.append({'uye': name, 'aile': R.family(name.replace('PIVNEAR', 'PIV')), 'taraf': 'direnc' if side == 1 else 'destek',
                             'donem': per, 'olcu': 'kirilim_hayalet', **st, 'p_kirilim': brk[ok].mean(),
                             'p_hayalet': pg_brk[ok].mean(), 'cozulme_orani': float(ok.mean())})
    return pd.DataFrame(rows)


# ───────────────────────────── Faz 4D + 5: durumlar ─────────────────────────────

def conditions(run: Run, fl: dict) -> pd.DataFrame:
    cols = {}
    F = run.F
    for c in F.columns:
        x = F[c].to_numpy(dtype=float)
        xk = x[run.K & np.isfinite(x)]
        if len(np.unique(xk)) < 5:
            for v in np.unique(xk)[:6]:
                cols[f'{c}=={v:g}'] = (x == v)
            continue
        q = np.nanquantile(xk, [0.2, 0.4, 0.6, 0.8])
        bins = np.digitize(x, q)
        for bq in range(5):
            cols[f'{c}#Q{bq + 1}'] = (bins == bq) & np.isfinite(x)
    for c in run.X.columns:
        if c.startswith('_'):
            continue
        x = run.X[c].to_numpy(dtype=float)
        cols[c] = x == 1
    for f, (U, D) in fl.items():
        cols[f'near_{f}_ust'] = np.nan_to_num(U, nan=9) <= NEAR_ATR
        cols[f'near_{f}_alt'] = np.nan_to_num(D, nan=9) <= NEAR_ATR
    return pd.DataFrame(cols)


def label_residuals(run: Run) -> dict:
    out = {}
    for lab in LABELS:
        y = run.lab[lab].to_numpy()
        valid = np.isfinite(y) & (y != 0)
        up = (y > 0).astype(float)
        df = pd.DataFrame({'s': run.strat, 'up': up, 'v': valid})
        base = df[df.v].groupby('s').up.mean()
        b = base.reindex(run.strat).to_numpy()
        out[lab] = (np.where(valid, up - b, np.nan), valid & np.isfinite(b))
    return out


def scan_cells(run: Run, Cm: pd.DataFrame, res: dict, per: str = 'K', names=None) -> pd.DataFrame:
    rows = []
    pm = run.per == per
    names = names or list(Cm.columns)
    for lab, (r, v) in res.items():
        base_m = pm & v
        for c in names:
            m = base_m & Cm[c].to_numpy()
            if m.sum() < MIN_N:
                continue
            idx = np.where(m)[0]
            hm = run.half(idx) if per == 'K' else run.td[idx] < np.median(run.td[idx])
            st = stat_row(r[idx], run.day[idx], run.td[idx], hm)
            rows.append({'kosul': c, 'etiket': lab, 'donem': per, **st})
    return pd.DataFrame(rows)


def combos(run: Run, Cm: pd.DataFrame, res: dict, singles: pd.DataFrame) -> pd.DataFrame:
    out = []
    for lab in LABELS:
        s = singles[(singles.etiket == lab)].dropna(subset=['t']).copy()
        s['at'] = s.t.abs()
        top = s.sort_values('at', ascending=False).kosul.head(TOP_SINGLES).tolist()
        pairs = {}
        for i in range(len(top)):
            for j in range(i + 1, len(top)):
                pairs[f'{top[i]} & {top[j]}'] = Cm[top[i]].to_numpy() & Cm[top[j]].to_numpy()
        P = pd.DataFrame(pairs)
        pr = scan_cells(run, P, {lab: res[lab]}) if len(P.columns) else pd.DataFrame()
        if len(pr):
            pr['duzey'] = 2
            out.append(pr)
            tp = pr.assign(at=pr.t.abs()).sort_values('at', ascending=False).kosul.head(TOP_PAIRS).tolist()
            trip = {}
            for p in tp:
                for sg in top[:TOP_TRIPLE_SINGLES]:
                    if sg in p.split(' & '):
                        continue
                    trip[f'{p} & {sg}'] = P[p].to_numpy() & Cm[sg].to_numpy()
            T3 = pd.DataFrame(trip)
            tr = scan_cells(run, T3, {lab: res[lab]}) if len(T3.columns) else pd.DataFrame()
            if len(tr):
                tr['duzey'] = 3
                out.append(tr)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def maxabs(df: pd.DataFrame, per: str = 'K', min_indep: int = 0) -> float:
    if df is None or not len(df):
        return np.nan
    d = df[(df.donem == per) & (df.n_indep >= min_indep)]
    return float(d.t.abs().max()) if len(d) else np.nan


def main(tag: str) -> None:
    t0 = time.time()
    out = RES / f'atlas_{tag}'
    out.mkdir(parents=True, exist_ok=True)
    run = Run(tag)
    b = C.load_ndx() if tag == 'real' else C.martingale_path(C.load_ndx(), int(tag.replace('mart', '')))
    fl = family_levels(run)
    fam = atlas_family(run, fl)
    fam.to_parquet(out / 'family.parquet')
    if tag == 'real':
        pd.concat([calib_curve(run, fl, f) for f in fl]).to_csv(out / 'calib_curve.csv', index=False)
    print(tag, 'family', round(time.time() - t0), flush=True)
    ms = member_series(run)
    mem = atlas_members(run, ms)
    mem.to_parquet(out / 'members.parquet')
    print(tag, 'members', round(time.time() - t0), flush=True)
    rea = atlas_reaction(b, run, ms)
    rea.to_parquet(out / 'reaction.parquet')
    print(tag, 'reaction', round(time.time() - t0), flush=True)
    Cm = conditions(run, fl)
    res = label_residuals(run)
    sing = scan_cells(run, Cm, res, 'K')
    sing['duzey'] = 1
    sing.to_parquet(out / 'singles.parquet')
    print(tag, 'singles', len(sing), round(time.time() - t0), flush=True)
    cmb = combos(run, Cm, res, sing)
    cmb.to_parquet(out / 'combos.parquet')
    print(tag, 'combos', len(cmb), round(time.time() - t0), flush=True)
    summ = {'tag': tag, 'n_cells': {'family': len(fam), 'members': len(mem), 'reaction': len(rea), 'singles': len(sing),
                                    'combos': len(cmb)},
            'max_abs_t_K': {'family': maxabs(fam), 'members': maxabs(mem), 'reaction': maxabs(rea), 'singles': maxabs(sing),
                            'combos': maxabs(cmb), 'singles_indep100': maxabs(sing, min_indep=100),
                            'combos_indep100': maxabs(cmb, min_indep=100)},
            'secs': round(time.time() - t0)}
    (out / 'summary.json').write_text(json.dumps(summ, indent=1, default=float))
    print(json.dumps(summ, default=float), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
