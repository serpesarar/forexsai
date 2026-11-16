"""Faz 8 mezuniyet ölçütünün GEÇMİŞ mumlarda yeniden oynatılması (destek kanıtı; canlı mezuniyetin YERİNE GEÇMEZ).

Etkin paket (2021-11 → 2026-11 ile eğitildi) modelin HİÇ görmediği 2018-01 → 2021-10 Dukascopy 1m mumlarında, gölge modun
hedefleriyle (NOM_SHADOW_TARGETS) 15 dk ızgarada tahmin üretir; sonuç eğitimdeki etiket koduyla çözülür. Sonra canlı raporun
AYNI fonksiyonu (`services.nom.calibration.side_report`, aynı WF bantları) uygulanır:
  (a) tüm eski dönem tek blok;
  (b) ardışık, örtüşmeyen 28 günlük pencereler — canlı mezuniyetin tam boyu: kaç pencere "mezun" olurdu?
(c) güç kontrolü: aynı pencerelerde bilerek bozulmuş iki tahmin — "kaydir" (P(TP)+0,08, kalibrasyonu bozuk) ve
    "karistir" (P(TP) pencere içinde karıştırılmış, bilgisiz) — ölçüt bunları ELEMELİ.
Eşik/ayar YOK. python src/faz8_eski_donem_mezuniyet.py → results/faz8_eski_donem_mezuniyet.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(H / 'src'))
sys.path.insert(0, str(REPO / 'backend'))
import faz12_build as B12  # noqa: E402
from services.nom import calibration as CB  # noqa: E402
from services.nom import features as FE  # noqa: E402
from services.nom import labels as LB  # noqa: E402
from services.nom import model_store as MS  # noqa: E402

OLD = ('2018-01-01', '2021-11-01')
GRID_S = 900
TARGETS = [('15m', '1x1'), ('1h', '1x1'), ('1h', '1.5x1'), ('4h', '1x1'), ('4h', '1.5x1.5'), ('session', '1x1')]
WIN_D = CB.GRAD_MIN_DAYS


def windows(df: pd.DataFrame, d: str, bins: list) -> list[dict]:
    wins, t0, span = [], df.t_dec.min(), pd.Timedelta(days=WIN_D + 1)   # +1 g: ilk-son tahmin arası ≥ 28 g olabilsin
    while t0 + span <= df.t_dec.max():
        w = df[(df.t_dec >= t0) & (df.t_dec < t0 + span)]
        r = CB.side_report(w, d, bins)
        if r.get('n'):
            g = r['mezuniyet']
            wins.append({'bas': str(t0.date()), 'n': r['n'], 'bagimsiz': g['bagimsiz_n'], 'beceri': g['brier_beceri'],
                         'egim': g['kalibrasyon_egimi'], 'bant_disi': g['bant_disi_kova'], 'mezun': g['mezun']})
        t0 += span
    return wins


def corrupt(df: pd.DataFrame, d: str, kind: str, seed: int = 7) -> pd.DataFrame:
    x = df.copy()
    col = f'p_{d}_tp'
    if kind == 'kaydir':
        x[col] = np.clip(x[col] + 0.08, 0.001, 0.999)
    else:
        rng = np.random.default_rng(seed)
        blk = x.t_dec.dt.floor(f'{WIN_D}D')
        x[col] = x.groupby(blk)[col].transform(lambda v: rng.permutation(v.to_numpy()))
    return x


def main() -> None:
    m = pd.read_parquet(H / 'data/ndx_1m_v3_duka.parquet')
    mac = pd.read_parquet(H / 'data/macro/macro_daily.parquet')
    cal = pd.read_parquet(H / 'data/macro/calendar.parquet')
    a, b = (int(pd.Timestamp(x, tz='UTC').timestamp()) for x in OLD)
    sub = m[(m.t >= a - 60 * 86400) & (m.t < b + 2 * 86400)].reset_index(drop=True)
    td, i0 = B12.decision_grid(sub)
    keep = (td >= a + 30 * 86400) & (td < b) & (td % GRID_S == 0)
    td, i0 = td[keep], i0[keep]
    F = FE.compute_features(sub, td, mac, cal)
    bundle = MS.load_bundle()
    cols = bundle.meta['feature_columns']
    path = LB.Path1m(t=sub.t.to_numpy(), o=sub.open.to_numpy(), h=sub.high.to_numpy(), l=sub.low.to_numpy(),
                     c=sub.close.to_numpy(), spr=sub.spr.to_numpy())
    out = {'donem': OLD, 'kaynak': 'Dukascopy bi5 (ndx_1m_v3_duka)', 'paket': bundle.version, 'olcut': {
        'gun': WIN_D, 'bagimsiz': CB.GRAD_MIN_INDEP, 'egim': CB.SLOPE_BAND}, 'hedefler': {}}
    labels_cache: dict[str, tuple] = {}
    for hz, gk in TARGETS:
        spec = LB.HORIZONS[hz]
        if hz not in labels_cache:
            te = B12.session_end(td) if hz == 'session' else td + spec['minutes'] * 60
            idx = np.where(te > 0)[0]
            atr = F[f"_atr_{spec['atr_tf']}"].to_numpy()[idx]
            L = LB.label_frame(path, i0[idx], atr, te[idx], expected_min=B12.expected_open_minutes(td[idx], te[idx]))
            labels_cache[hz] = (idx, L)
        idx, L = labels_cache[hz]
        X = F[cols].iloc[idx]
        df = pd.DataFrame({'t_dec': pd.to_datetime(td[idx], unit='s', utc=True)})
        for d in ('long', 'short'):
            booster, calb, _ = bundle.target(hz, d, gk)
            df[f'p_{d}_tp'] = calb.apply(booster.predict(X))[:, 0]
            df[f'outcome_{d}_cls'] = L[f'{d}_{gk}_cls'].to_numpy()
            df[f'outcome_{d}_r'] = L[f'{d}_{gk}_r'].to_numpy()
        res = {}
        for d in ('long', 'short'):
            bins = bundle.meta['targets'][f'{hz}_{d}_{gk}']['p_tp_bins']
            tum = CB.side_report(df, d, bins)
            wins = windows(df, d, bins)
            wdf = pd.DataFrame(wins)
            guc = {k: int(pd.DataFrame(windows(corrupt(df, d, k), d, bins)).mezun.sum()) for k in ('kaydir', 'karistir')}
            res[d] = {'tum_donem': {k: tum[k] for k in ('n', 'tp_orani', 'ort_p_tp', 'brier_beceri', 'ort_R', 'mezuniyet')},
                      'pencere_28g': {'adet': int(len(wdf)), 'mezun': int(wdf.mezun.sum()) if len(wdf) else 0,
                                      'beceri_medyan': float(wdf.beceri.median()) if len(wdf) else None,
                                      'beceri_pozitif_pay': float((wdf.beceri > 0).mean()) if len(wdf) else None,
                                      'egim_bantta_pay': float(wdf.egim.between(*CB.SLOPE_BAND).mean()) if len(wdf) else None,
                                      'bant_disi_sifir_pay': float((wdf.bant_disi == 0).mean()) if len(wdf) else None,
                                      'pencereler': wins},
                      'guc_kontrolu_mezun_pencere': guc}
            print(hz, gk, d, json.dumps(res[d]['tum_donem']['mezuniyet'], default=float),
                  {k: v for k, v in res[d]['pencere_28g'].items() if k != 'pencereler'}, 'guc', guc, flush=True)
        out['hedefler'][f'{hz}_{gk}'] = res
    (H / 'results/faz8_eski_donem_mezuniyet.json').write_text(json.dumps(out, indent=1, default=float))


if __name__ == '__main__':
    main()
