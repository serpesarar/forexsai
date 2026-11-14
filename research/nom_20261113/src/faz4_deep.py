"""Faz 4 derin modeller (LSTM, TCN) — LightGBM/CatBoost YÜKLEMEYEN ayrı süreç (macOS OpenMP kilitlenmesi). Aynı WF katları
(2024H2, 2025H1, 2025H2), aynı etiket/özellik, isotonic, saat-iklimine göre Brier becerisi; karşılaştırma faz34_ek.json'daki LGB.
.venv_ext ile: python src/faz4_deep.py → results/faz4_deep.json"""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
import torch
torch.set_num_threads(6)
H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H / 'src'))
import validation as V  # noqa: E402  (lightgbm içermez)
from sklearn.isotonic import IsotonicRegression  # noqa: E402

GRID_S = 900
TARGETS = [('1h', 'long', '1x1'), ('4h', 'long', '1x1')]
FOLDS = ('2024H2', '2025H1', '2025H2')
KINDS = tuple(sys.argv[sys.argv.index('--kinds') + 1].split(',')) if '--kinds' in sys.argv else ('lstm', 'tcn')


def ny_hour(t):
    return pd.to_datetime(t, unit='s', utc=True).tz_convert('America/New_York').hour.to_numpy()


def climate(y_tr, k_tr, k_te, prior=50.0):
    glob = np.bincount(y_tr, minlength=3) / len(y_tr)
    df = pd.DataFrame({'k': k_tr, 'y': y_tr})
    cnt = df.groupby('k').y.value_counts().unstack(fill_value=0).reindex(columns=[0, 1, 2], fill_value=0)
    prob = (cnt.to_numpy() + prior * glob) / (cnt.sum(1).to_numpy()[:, None] + prior)
    m = dict(zip(cnt.index, prob))
    return np.array([m.get(k, glob) for k in k_te])


def brier(p, y):
    return float(((p - np.eye(3)[y]) ** 2).sum(1).mean())


def calibrate(pc, yc, pt):
    out = np.empty_like(pt)
    for k in range(3):
        out[:, k] = IsotonicRegression(out_of_bounds='clip', y_min=0, y_max=1).fit(pc[:, k], (yc == k).astype(float)).predict(pt[:, k])
    out = np.clip(out, 1e-6, None)
    return out / out.sum(1, keepdims=True)


def main():
    from deep_nets import seq_tensor, train_deep
    b = pd.read_parquet(H / 'data/ndx_1m_v1.parquet')
    b = b[b.t >= pd.Timestamp('2021-11-01', tz='UTC').timestamp()].reset_index(drop=True)
    F = pd.read_parquet(H / 'data/features_v1.parquet')
    cols = [c for c in F.columns if not c.startswith('_')]
    out = {}
    for hz, d, gk in TARGETS:
        t0 = time.time()
        L = pd.read_parquet(H / f'data/labels_{hz}.parquet')
        L = L[(L.t % GRID_S == 0) & (L[f'{d}_{gk}_cls'] >= 0)].reset_index(drop=True)
        y = L[f'{d}_{gk}_cls'].to_numpy().astype(int)
        t = L.t.to_numpy()
        Xt = F.iloc[L.row.to_numpy()][cols].to_numpy(np.float32)
        i0 = F._i0.to_numpy()[L.row.to_numpy()]
        a1 = F._atr_H1.to_numpy()[L.row.to_numpy()]
        hr = ny_hour(t)
        rows = []
        for fd in V.walk_forward(t, hz):
            if fd.name not in FOLDS:
                continue
            mu, sd = np.nanmean(Xt[fd.fit], 0), np.nanstd(Xt[fd.fit], 0) + 1e-6
            tab = lambda m: np.nan_to_num((Xt[m] - mu) / sd).astype(np.float32)
            S = {k: seq_tensor(i0[m] - 1, b, a1[m]) for k, m in (('fit', fd.fit), ('cal', fd.cal), ('test', fd.test))}
            c = climate(y[fd.fit | fd.cal], hr[fd.fit | fd.cal], hr[fd.test])
            row = {'kat': fd.name, 'n': int(fd.test.sum())}
            for kind in KINDS:
                pv, pt = train_deep(kind, S['fit'], tab(fd.fit), y[fd.fit], S['cal'], tab(fd.cal), y[fd.cal], S['test'], tab(fd.test))
                row[kind] = 1 - brier(calibrate(pv, y[fd.cal], pt), y[fd.test]) / brier(c, y[fd.test])
                print(hz, kind, fd.name, round(row[kind], 4), round(time.time() - t0), flush=True)
            rows.append(row)
        out[f'{hz}_{d}_{gk}'] = rows
    fp = H / 'results/faz4_deep.json'   # önceki türlerin sonuçlarıyla birleştir (kat başına)
    old = json.loads(fp.read_text()) if fp.exists() else {}
    for k, rows in out.items():
        prev = {r['kat']: r for r in old.get(k, [])}
        for r in rows:
            prev.setdefault(r['kat'], {}).update(r)
        old[k] = list(prev.values())
    fp.write_text(json.dumps(old, indent=1))
    print(json.dumps(out))


if __name__ == '__main__':
    main()
