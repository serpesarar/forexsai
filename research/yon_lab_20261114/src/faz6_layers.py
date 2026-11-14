"""Faz 6 — fiyat dışı bilgi katmanları (PROTOCOL EK-1). Her katman: KEŞİF beşte birlik hücreleri, eşlenmiş taban artığı,
dairesel kaydırma max-|t| eşiği (200 tekrar, q95), iki yarı tutarlılığı, DOĞRULAMA. KÖR burada AÇILMAZ (Faz 8).

python src/faz6_layers.py → results/faz6_<katman>.csv + results/faz6_ozet.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import atlas as A
import core as C

RES = C.H / 'results'
XA = C.H / 'data/xasset'
NREP = 200
NY = C.NY
RNG = np.random.default_rng(20261114)


def qcells(X: pd.DataFrame, kmask: np.ndarray) -> dict[str, np.ndarray]:
    out = {}
    for c in X.columns:
        x = X[c].to_numpy(dtype=float)
        if c.startswith('bin:'):
            out[c[4:]] = x == 1
            continue
        xk = x[kmask & np.isfinite(x)]
        if len(xk) < 50 or len(np.unique(xk)) < 5:
            continue
        q = np.nanquantile(xk, [0.2, 0.4, 0.6, 0.8])
        b = np.digitize(x, q)
        for i in range(5):
            out[f'{c}#Q{i + 1}'] = (b == i) & np.isfinite(x)
    return out


def tstat(r, day, m):
    idx = np.where(m)[0]
    mm, t, n = A.cluster_t(r[idx], day[idx])
    return mm, t, n


def evaluate(name: str, X: pd.DataFrame, labels: dict, per: np.ndarray, day: np.ndarray, tt: np.ndarray,
             shift_min: int, indep_gap: int = 3600) -> dict:
    """X: özellikler (satır = karar anı); labels: ad → (artık, geçerli); per: 'K'/'D'/'T'/'X'."""
    K = per == 'K'
    cells = qcells(X, K)
    kmid = np.median(tt[K])
    rows = []
    for lab, (r, v) in labels.items():
        for c, m in cells.items():
            for p in ('K', 'D'):
                mm = m & v & (per == p)
                if mm.sum() < 50:
                    continue
                idx = np.where(mm)[0]
                f, t, n = A.cluster_t(r[idx], day[idx])
                h = tt[idx] < (kmid if p == 'K' else np.median(tt[idx]))
                f1, _, _ = A.cluster_t(r[idx[h]], day[idx[h]])
                f2, _, _ = A.cluster_t(r[idx[~h]], day[idx[~h]])
                rows.append({'katman': name, 'kosul': c, 'etiket': lab, 'donem': p, 'n': n,
                             'n_indep': A.indep(tt[idx], indep_gap), 'fazla': f, 't': t, 'h1': f1, 'h2': f2,
                             'same_sign': bool(np.sign(f1) == np.sign(f2) == np.sign(f))})
    df = pd.DataFrame(rows)
    # dairesel kaydırma sıfırı: özellik satırları etiketlere göre kaydırılır (yalnız KEŞİF)
    mx = []
    kidx = np.where(K)[0]
    for _ in range(NREP):
        sh = int(RNG.integers(shift_min, max(shift_min + 1, len(kidx) - shift_min)))
        perm = np.roll(kidx, sh)
        best = 0.0
        for lab, (r, v) in labels.items():
            for c, m in cells.items():
                mm = m[perm] & v[kidx]
                if mm.sum() < 50:
                    continue
                idx = kidx[mm]
                _, t, _ = A.cluster_t(r[idx], day[idx])
                if np.isfinite(t):
                    best = max(best, abs(t))
        mx.append(best)
    T = float(np.quantile(mx, 0.95))
    k = df[df.donem == 'K']
    sel = k[(k.t.abs() > T) & k.same_sign & (k.n_indep >= 100)]
    val = []
    for _, s in sel.iterrows():
        d = df[(df.donem == 'D') & (df.kosul == s.kosul) & (df.etiket == s.etiket)]
        if len(d):
            d = d.iloc[0]
            val.append({**s.to_dict(), 'fazla_D': d.fazla, 't_D': d.t, 'n_D': d.n,
                        'gecti': bool(np.sign(d.fazla) == np.sign(s.fazla) and abs(d.t) >= 2 and abs(d.fazla) >= 0.5 * abs(s.fazla))})
    df.to_csv(RES / f'faz6_{name}.csv', index=False)
    return {'katman': name, 'hucre': int(len(k)), 'T_star_q95': T, 'max_abs_t_K': float(k.t.abs().max()) if len(k) else None,
            'secilen': int(len(sel)), 'dogrulama': val}


# ───────────────────────── L1 DIX / GEX → NDX günlük ─────────────────────────

def layer_dix() -> dict:
    d = pd.read_csv(C.H / 'data/DIX.csv', parse_dates=['date']).set_index('date')
    n = pd.read_parquet(XA / 'NDX_1d.parquet')
    if isinstance(n.columns, pd.MultiIndex):
        n.columns = n.columns.get_level_values(0)
    n.index = pd.to_datetime(n.index).tz_localize(None).normalize()
    n = n[['Open', 'Close']].dropna()
    n['sess'] = np.sign(n.Close - n.Open)
    n['night'] = np.sign(n.Open.shift(-1) - n.Close)
    n['nextcc'] = np.sign(n.Close.shift(-1) - n.Close)
    # D günü kararları: koşul = önceki işlem gününün DIX/GEX'i (yayın kapanış sonrası)
    f = pd.DataFrame(index=n.index)
    dd = d.reindex(n.index).ffill()
    prev = dd.shift(1)
    f['gex'] = prev.gex
    f['dix'] = prev.dix
    f['dix_z'] = (prev.dix - prev.dix.rolling(60).mean()) / prev.dix.rolling(60).std()
    f['gex_z'] = (prev.gex - prev.gex.rolling(60).mean()) / prev.gex.rolling(60).std()
    f['ddix5'] = prev.dix - prev.dix.shift(5)
    f['bin:gex_neg'] = (prev.gex < 0).astype(float)
    f['bin:dix_z_hi'] = (f.dix_z > 1).astype(float)
    f['bin:dix_z_lo'] = (f.dix_z < -1).astype(float)
    f['bin:gex_z_hi'] = (f.gex_z > 1).astype(float)
    f['bin:gex_z_lo'] = (f.gex_z < -1).astype(float)
    ok = f.gex.notna() & (f.index >= '2011-06-01')
    f, n = f[ok], n[ok]
    idx = f.index
    per = np.where(idx < '2021-11-01', 'K', np.where(idx < '2026-01-01', 'D', 'T'))
    yr = idx.year.to_numpy()
    labels = {}
    for lab in ('sess', 'night', 'nextcc'):
        y = n[lab].to_numpy()
        v = np.isfinite(y) & (y != 0)
        up = (y > 0).astype(float)
        base = pd.Series(up[v]).groupby(yr[v]).mean().reindex(yr).to_numpy()   # aynı yıl tabanı
        labels[lab] = (np.where(v, up - base, np.nan), v)
    day = (idx.asi8 // 86400 // 10**9).astype(np.int64)
    tt = (idx.asi8 // 10**9).astype(np.int64)
    return evaluate('L1_dix_gex', f, labels, per, day, tt, shift_min=60, indep_gap=86400)


# ───────────────────────── ortak: ana ızgara artıkları ─────────────────────────

def grid_ctx():
    run = A.Run('real')
    res = A.label_residuals(run)
    return run, res


def subset_labels(res, rows, names):
    return {k: (res[k][0][rows], res[k][1][rows]) for k in names}


# ───────────────────────── L2 saatlik çapraz varlık ─────────────────────────

def layer_hourly(run, res) -> dict:
    syms = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'AVGO']
    def load(k):
        d = pd.read_parquet(XA / f'{k}_1h.parquet')
        d.index = pd.to_datetime(d.index, utc=True)
        return d.Close
    eq = pd.concat({k: load(k) for k in syms + ['SOXX', 'QQQ', 'SPY', 'IWM']}, axis=1)
    eq = eq[eq.index.tz_convert(NY).minute == 30]
    end = eq.index + pd.Timedelta(hours=1)                 # yfinance saat barı = başlangıç; karar = bar kapanışı
    r = np.log(eq).diff()
    r.index = end
    F = pd.DataFrame(index=end)
    F['breadth8'] = (r[syms] > 0).mean(axis=1)
    F['disp8'] = r[syms].std(axis=1)
    for k in ('NVDA', 'SOXX', 'IWM', 'SPY'):
        F[f'{k.lower()}_rel'] = r[k] - r['QQQ']
    for k, col in (('VIX', 'vix_chg'), ('DXY', 'dxy_chg'), ('TNX', 'tnx_chg')):
        d = pd.read_parquet(XA / f'{k}_1h.parquet').Close
        d.index = pd.to_datetime(d.index, utc=True) + pd.Timedelta(hours=1)     # bar kapanışı
        d = d[~d.index.duplicated()].sort_index().diff()
        F[col] = d.reindex(F.index, method='ffill').to_numpy()
    F = F[(F.index.tz_convert(NY).hour >= 10) & (F.index.tz_convert(NY).hour <= 15)]
    tsec = (F.index.asi8 // 10**9).astype(np.int64)
    pos = pd.Series(np.arange(len(run.td)), index=run.td)
    rows = pos.reindex(tsec).to_numpy()
    ok = np.isfinite(rows)
    F = F[ok]
    rows = rows[ok].astype(int)
    tt = run.td[rows]
    per = np.where(tt < C.ts('2023-12-18'), 'X', np.where(tt < C.ts('2024-07-01'), 'K', np.where(tt < C.ts('2026-01-01'), 'D', 'T')))
    labels = subset_labels(res, rows, ['dir_15m', 'dir_1h', 'dir_sess'])
    out = evaluate('L2_saatlik_capraz', F.reset_index(drop=True), labels, per, run.day[rows], tt, shift_min=5 * 7)
    out['_rows'] = rows
    return out


# ───────────────────────── L3 M5 çapraz endeks (MT5) ─────────────────────────

def load_mt5(sym: str, tf: str = 'M5') -> pd.DataFrame:
    d = pd.read_csv(C.H / f'data/mt5/{sym}_{tf}.csv.gz')
    ny = (pd.to_datetime(d.t, unit='s') - pd.Timedelta(hours=7)).dt.tz_localize(NY, ambiguous='NaT', nonexistent='shift_forward')
    d['ts'] = ny.dt.tz_convert('UTC')
    d = d.dropna(subset=['ts'])
    d['tu'] = (d.ts.astype('int64') // 10**9).astype(np.int64)
    return d.set_index('tu').sort_index()


def layer_m5(run, res) -> dict:
    px = {s: load_mt5(s).c for s in ('NAS100', 'US500', 'US30', 'US2000')}
    P = pd.concat(px, axis=1).dropna()
    P.index = P.index + 300                                 # bar kapanışı
    lp = np.log(P)
    F = pd.DataFrame(index=P.index)
    for s in ('US500', 'US30', 'US2000'):
        for k, lab in ((3, '15'), (12, '60')):
            F[f'{s}_rel{lab}'] = (lp[s] - lp[s].shift(k) - (lp.NAS100 - lp.NAS100.shift(k))) * 1e4
    F['agree15'] = sum(np.sign(lp[s] - lp[s].shift(3)) for s in ('US500', 'US30', 'US2000'))
    pos = pd.Series(np.arange(len(run.td)), index=run.td)
    rows = pos.reindex(F.index.to_numpy()).to_numpy()
    ok = np.isfinite(rows)
    F = F[ok]
    rows = rows[ok].astype(int)
    tt = run.td[rows]
    per = np.where(tt < C.ts('2025-06-20'), 'X', np.where(tt < C.ts('2025-11-01'), 'K', np.where(tt < C.ts('2026-01-01'), 'D', 'T')))
    labels = subset_labels(res, rows, ['dir_15m', 'dir_1h'])
    out = evaluate('L3_m5_capraz_endeks', F.reset_index(drop=True), labels, per, run.day[rows], tt, shift_min=5 * 92)
    out['_rows'] = rows
    return out


# ───────────────────────── L4 tick mikroyapısı (2025) ─────────────────────────

def layer_tick(run, res) -> dict:
    m = pd.read_parquet(C.H / 'data/tick_micro_2025.parquet').set_index('t').sort_index()
    m.index = m.index + 60                                   # dakika kapanışı
    full = m.reindex(np.arange(m.index.min(), m.index.max() + 60, 60))
    up, dn = full.up.fillna(0), full.dn.fillna(0)
    F = pd.DataFrame(index=full.index)
    for w in (5, 15, 60):
        u, d_ = up.rolling(w).sum(), dn.rolling(w).sum()
        F[f'imb{w}'] = (u - d_) / (u + d_).replace(0, np.nan)
    nq = full.nq.fillna(0)
    mod = (pd.to_datetime(full.index, unit='s', utc=True).tz_convert(NY).hour * 60 + pd.to_datetime(full.index, unit='s', utc=True).tz_convert(NY).minute)
    nq15 = nq.rolling(15).sum()
    base = nq15.groupby(mod.to_numpy()).transform(lambda s: s.rolling(20, min_periods=5).median().shift(1))
    F['qrate'] = nq15 / base
    sp = full.spr
    F['spr_ratio'] = sp.rolling(15, min_periods=5).mean() / sp.rolling(1440 * 5, min_periods=1000).median()
    pos = pd.Series(np.arange(len(run.td)), index=run.td)
    rows = pos.reindex(F.index.to_numpy()).to_numpy()
    ok = np.isfinite(rows)
    F = F[ok]
    rows = rows[ok].astype(int)
    tt = run.td[rows]
    per = np.where(tt < C.ts('2025-01-15'), 'X', np.where(tt < C.ts('2025-07-01'), 'K', np.where(tt < C.ts('2026-01-01'), 'D', 'T')))
    labels = subset_labels(res, rows, ['dir_15m', 'dir_1h'])
    out = evaluate('L4_tick_mikroyapi', F.reset_index(drop=True), labels, per, run.day[rows], tt,
                   shift_min=5 * 92)
    return out


def main() -> None:
    out = [layer_dix()]
    print(json.dumps({k: v for k, v in out[-1].items() if not k.startswith('_')}, default=float)[:1500], flush=True)
    run, res = grid_ctx()
    for fn in (layer_hourly, layer_m5, layer_tick):
        o = fn(run, res)
        o.pop('_rows', None)
        out.append(o)
        print(json.dumps(o, default=float)[:1500], flush=True)
    (RES / 'faz6_ozet.json').write_text(json.dumps(out, indent=1, default=float))


if __name__ == '__main__':
    main()
