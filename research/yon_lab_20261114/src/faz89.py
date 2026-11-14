"""Faz 8 (DOĞRULAMA → KÖR TEST tek açılış → KÖR TAŞIMA) + Faz 9 (işlem çevrimi, PROTOCOL §12 + EK-2).

python src/faz89.py → results/faz8_*.csv, results/faz9_*.csv, results/faz89_ozet.json, results/FINAL_OPENED.json
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

import atlas as A
import core as C
import extras as XT
import faz7_model as M7

RES = C.H / 'results'
SLIP = 1.0
HOLD = 15
NREP = 1000
LOCK = RES / 'FINAL_OPENED.json'


# ───────────────────────── işlem simülasyonu ─────────────────────────

def trade_time_exit(b: pd.DataFrame, spr: np.ndarray, i1: np.ndarray, td: np.ndarray, side: np.ndarray, atr: np.ndarray,
                    extra_cost: float = 0.0) -> np.ndarray:
    """Giriş: t'den sonraki 1m açılışı. LONG: ask + kayma; SHORT: bid − kayma. Çıkış HOLD dk sonra kapanış (karşı taraf ± kayma).
    Dönen R = pnl / ATR(M15). extra_cost: 2× stres için ek (spread + 2 kayma) çarpanı (0 veya 1)."""
    t, o, c = b.t.to_numpy(), b.open.to_numpy(), b.close.to_numpy()
    e = i1 + 1
    ok = (e < len(t)) & (t[np.clip(e, 0, len(t) - 1)] == td)
    j = np.searchsorted(t, td + HOLD * 60 - 60, side='right') - 1
    ok &= (j >= e) & (t[np.clip(j, 0, None)] >= td + HOLD * 60 - 60 - 300)
    e = np.clip(e, 0, len(t) - 1)
    j = np.clip(j, 0, len(t) - 1)
    se, sx = spr[e], spr[j]
    long_pnl = (c[j] - SLIP) - (o[e] + se + SLIP)
    short_pnl = (o[e] - SLIP) - (c[j] + sx + SLIP)
    pnl = np.where(side > 0, long_pnl, short_pnl) - extra_cost * (se + 2 * SLIP)
    return np.where(ok, pnl / atr, np.nan)


def day_boot(r: np.ndarray, day: np.ndarray, n: int = 2000) -> tuple[float, float, float]:
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=r)
    N = np.bincount(inv)
    rng = np.random.default_rng(3)
    ix = rng.integers(0, len(u), (n, len(u)))
    m = S[ix].sum(1) / N[ix].sum(1)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975)), float((m > 0).mean())


def placebo(sel_idx: np.ndarray, pool_r: np.ndarray, hours: np.ndarray, pool_mask: np.ndarray, n: int = NREP) -> float:
    rng = np.random.default_rng(5)
    by = {h: np.where(pool_mask & (hours == h) & np.isfinite(pool_r))[0] for h in np.unique(hours[sel_idx])}
    need = pd.Series(hours[sel_idx]).value_counts()
    ev = []
    for _ in range(n):
        pick = np.concatenate([rng.choice(by[h], k) for h, k in need.items() if len(by[h])])
        ev.append(np.nanmean(pool_r[pick]))
    return float(np.quantile(ev, 0.95))


def stats(r, day, td, mask, pool_r=None, hours=None, pool_mask=None) -> dict:
    idx = np.where(mask & np.isfinite(r))[0]
    if len(idx) < 10:
        return {'n': int(len(idx))}
    rr = r[idx]
    lo, hi, pp = day_boot(rr, day[idx])
    h = td[idx] < np.median(td[idx])
    out = {'n': int(len(idx)), 'n_indep': A.indep(td[idx]), 'ev_r': float(rr.mean()), 'lo95': lo, 'hi95': hi, 'p_ev_pos': pp,
           'yari1': float(rr[h].mean()), 'yari2': float(rr[~h].mean()), 'isabet': float((rr > 0).mean())}
    if pool_r is not None:
        out['plasebo_p95'] = placebo(idx, pool_r, hours, pool_mask)
    return out


def cell_mask(Cm: pd.DataFrame, k: str) -> np.ndarray:
    m = np.ones(len(Cm), bool)
    for p in k.split(' & '):
        m &= Cm[p].to_numpy()
    return m


# ───────────────────────── KÖR TAŞIMA ─────────────────────────

def load_m1(sym: str) -> pd.DataFrame:
    d = pd.read_csv(C.H / f'data/mt5/{sym}_M1.csv.gz')
    ny = (pd.to_datetime(d.t, unit='s') - pd.Timedelta(hours=7)).dt.tz_localize(C.NY, ambiguous='NaT', nonexistent='shift_forward')
    d['ts'] = ny.dt.tz_convert('UTC')
    d = d.dropna(subset=['ts'])
    b = pd.DataFrame({'t': (d.ts.astype('int64') // 10**9).astype(np.int64), 'open': d.o, 'high': d.h, 'low': d.l, 'close': d.c,
                      'spr': d.sp * 0.1})
    tsu = pd.to_datetime(b.t, unit='s', utc=True)
    import data_layer_proxy as DLP  # noqa: F401  (yalnız kapalı-saat maskesi)
    b = b[~DLP.closed(tsu)].drop_duplicates('t').sort_values('t').reset_index(drop=True)
    return b


def transfer_eval(sym: str, ndx_run: A.Run, cells: list[str]) -> dict:
    b = load_m1(sym)
    mac, cal = C.load_macro()
    td, i1 = C.grid(b)
    F = C.nom_features(b[['t', 'open', 'high', 'low', 'close']], td, mac, cal)
    Xx = XT.build_extras(b[['t', 'open', 'high', 'low', 'close']], td)
    # koşullar: NDX KEŞİF beşte birlik eşikleri (sıfır ayar)
    cols = {}
    for k in cells:
        for p in k.split(' & '):
            if p in cols:
                continue
            if '#Q' in p:
                f, q = p.split('#Q')
                xk = ndx_run.F[f].to_numpy(dtype=float)[ndx_run.K]
                e = np.nanquantile(xk[np.isfinite(xk)], [0.2, 0.4, 0.6, 0.8])
                x = F[f].to_numpy(dtype=float)
                cols[p] = (np.digitize(x, e) == int(q) - 1) & np.isfinite(x)
            else:
                cols[p] = Xx[p].to_numpy() == 1
    Cm = pd.DataFrame(cols)
    lab = C.dir_labels(b, td, i1)
    y = lab['dir_15m']
    valid = np.isfinite(y) & (y != 0)
    up = (y > 0).astype(float)
    volr = F.H1_atr_ratio.to_numpy()
    ed = np.nanquantile(volr, np.linspace(0.1, 0.9, 9))
    key = C.ny_hour(td) * 10 + np.searchsorted(ed, np.nan_to_num(volr, nan=1.0))
    base = pd.Series(up[valid]).groupby(key[valid]).mean().reindex(key).to_numpy()
    resid = np.where(valid, up - base, np.nan)
    day = td // 86400
    spr = np.fmax(b.spr.to_numpy(), pd.Series(b.spr.to_numpy()).rolling(1440, min_periods=60).median().bfill().to_numpy())
    a15 = F._atr_M15.to_numpy()
    rshort = trade_time_exit(b, spr, i1, td, -np.ones(len(td)), a15)
    union = np.zeros(len(td), bool)
    out = {'sembol': sym, 'baslangic': str(pd.to_datetime(td.min(), unit='s')), 'bitis': str(pd.to_datetime(td.max(), unit='s')),
           'n_izgara': int(len(td))}
    per_cell = []
    for k in cells:
        m = cell_mask(Cm, k)
        union |= m
        idx = np.where(m & valid)[0]
        f, t, n = A.cluster_t(resid[idx], day[idx]) if len(idx) > 5 else (np.nan, np.nan, len(idx))
        per_cell.append({'kosul': k, 'n': int(n), 'fazla': f, 't': t, 'ev_r_short': float(np.nanmean(rshort[m])) if m.any() else np.nan})
    idx = np.where(union & valid)[0]
    f, t, n = A.cluster_t(resid[idx], day[idx])
    out.update({'birlik_n': int(n), 'birlik_fazla_15m': f, 'birlik_t': t,
                'birlik_ev_r_short': float(np.nanmean(rshort[union])), 'hucreler': per_cell})
    return out


def main() -> None:
    if LOCK.exists() and (RES / 'faz89_ozet.json').exists():
        raise SystemExit('KÖR TEST zaten açıldı ve sonuç yazıldı — FINAL_OPENED.json; yeniden ayar yasak')
    prev = json.loads(LOCK.read_text()) if LOCK.exists() else None
    t0 = time.time()
    run = A.Run('real')
    b = pd.read_parquet(C.H / 'data/ndx_1m_v2.parquet')
    spr = b.spr.to_numpy()
    fl = A.family_levels(run)
    Cm = A.conditions(run, fl)
    res = A.label_residuals(run)
    val = pd.read_csv(RES / 'faz5_dogrulama.csv')
    cells = val[val.gecti].kosul.tolist()
    LOCK.write_text(json.dumps({'opened_at': time.time(), 'what': 'Yön Lab KÖR TEST 2026 + KÖR TAŞIMA, tek açılış',
                                'onceki_deneme': prev}))
    i1, td, a15 = run.lab.i1.to_numpy(), run.td, run.lab.atr15.to_numpy()
    hours = C.ny_hour(td)
    r1 = trade_time_exit(b, spr, i1, td, -np.ones(len(td)), a15)
    r2 = trade_time_exit(b, spr, i1, td, -np.ones(len(td)), a15, extra_cost=1.0)
    rlong = trade_time_exit(b, spr, i1, td, np.ones(len(td)), a15)
    # Faz 8: hücreler — DOĞRULAMA + KÖR TEST (yön artığı)
    r_dir, v_dir = res['dir_15m']
    rows = []
    union = np.zeros(len(td), bool)
    for k in cells:
        m = cell_mask(Cm, k)
        union |= m
        for per in ('K', 'D', 'T'):
            idx = np.where(m & v_dir & (run.per == per))[0]
            f, t, n = A.cluster_t(r_dir[idx], run.day[idx])
            rows.append({'kosul': k, 'donem': per, 'n': n, 'fazla_15m': f, 't': t,
                         'ev_r_short': float(np.nanmean(r1[m & (run.per == per)]))})
    f8 = pd.DataFrame(rows)
    f8.to_csv(RES / 'faz8_hucreler.csv', index=False)
    # Faz 9: R-H birlik kuralı
    rh = {}
    for per in ('K', 'D', 'T'):
        pm = run.per == per
        s1 = stats(r1, run.day, td, union & pm, r1, hours, pm)
        s2 = stats(r2, run.day, td, union & pm)
        idx = np.where(union & v_dir & pm)[0]
        f, t, n = A.cluster_t(r_dir[idx], run.day[idx])
        rh[per] = {'ev': s1, 'ev_2x': s2, 'yon_fazla_15m': f, 'yon_t': t}
    print('R-H', json.dumps(rh, default=float)[:2500], flush=True)
    # R-M: model — X seçimi KEŞİF içi WF bloklarında
    o = pd.read_parquet(RES / 'faz7_oos_dir_15m.parquet')
    pos = pd.Series(np.arange(len(td)), index=td)
    oi = pos.reindex(o.t).to_numpy().astype(int)
    side_o = np.where(o.p > 0.5, 1, -1)
    ro = np.where(side_o > 0, rlong[oi], r1[oi])
    kb = o.blok.isin(['2023H1', '2023H2', '2024H1']).to_numpy()
    bestX, bestev = None, -9
    for X_ in M7.XS:
        m = kb & ((o.p - 0.5).abs() >= X_).to_numpy()
        ev = np.nanmean(ro[m]) if m.sum() > 50 else -9
        if ev > bestev:
            bestX, bestev = X_, ev
    # final model: ≤ 2025-12 ile eğit, 2026 tahmin (tek açılış)
    Xd, _ = M7.design(run)
    M7.BLOCKS = [('KOR', '2026-01-01', '2027-01-01')]
    of = M7.run_wf(run, Xd, 'dir_15m')
    of_i = pos.reindex(of.t).to_numpy().astype(int)
    rm = {}
    for name, d, ii in (('D', o[o.blok.isin(['2024H2', '2025H1', '2025H2'])], None), ('T', of, of_i)):
        ii = pos.reindex(d.t).to_numpy().astype(int)
        sd = np.where(d.p.to_numpy() > 0.5, 1, -1)
        m = ((d.p - 0.5).abs() >= bestX).to_numpy()
        rr = np.where(sd > 0, rlong[ii], r1[ii])
        rr2 = np.where(sd > 0, trade_time_exit(b, spr, i1[ii], td[ii], np.ones(len(ii)), a15[ii], 1.0),
                       trade_time_exit(b, spr, i1[ii], td[ii], -np.ones(len(ii)), a15[ii], 1.0))
        full = np.full(len(td), np.nan)
        full[ii[m]] = rr[m]
        msk = np.isfinite(full)
        rm[name] = {'X': bestX, 'ev': stats(full, run.day, td, msk), 'ev_2x': float(np.nanmean(rr2[m])),
                    'isabet_yon': float(((d.p.to_numpy()[m] > 0.5) == (d.y.to_numpy()[m] == 1)).mean()) if m.any() else None}
    print('R-M', json.dumps(rm, default=float)[:2000], flush=True)
    # KÖR TAŞIMA
    tr = []
    for sym in ('US500', 'US30', 'US2000', 'GER40'):
        try:
            tr.append(transfer_eval(sym, run, cells))
            print('TAŞIMA', sym, {k: v for k, v in tr[-1].items() if k != 'hucreler'}, flush=True)
        except Exception as ex:  # noqa: BLE001
            tr.append({'sembol': sym, 'hata': str(ex)})
            print('TAŞIMA hata', sym, ex, flush=True)
    out = {'R_H': rh, 'R_M': rm, 'tasima': tr, 'hucre_sayisi': len(cells), 'secs': round(time.time() - t0)}
    (RES / 'faz89_ozet.json').write_text(json.dumps(out, indent=1, default=float))


if __name__ == '__main__':
    main()
