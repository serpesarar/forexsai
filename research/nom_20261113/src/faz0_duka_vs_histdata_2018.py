"""Eski dönem iki besleme kıyası: Dukascopy USATECHIDXUSD 1m (2018-01 → 2018-05, indirilebilen kısım) vs HistData NSXUSD (eğitim dışı
eski dönemin tek kaynağı). Gecikme (±120 dk), 1m getiri korelasyonu, kapanış farkı (bp), günlük aralık oranı; ve aynı günlerde etkin
NOM paketinin 15 dk / 1 s Brier becerisinin iki beslemede farkı (besleme hassasiyeti). python src/faz0_duka_vs_histdata_2018.py"""
from __future__ import annotations

import datetime as D
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H / 'src'))
import data_layer as DL  # noqa: E402

START, END = D.date(2018, 1, 1), D.date(2018, 5, 23)


def main() -> None:
    du, st = DL.load_bi5_range(DL.RAW_NEW, START, END, 'duka_2018')
    hd = pd.read_parquet(H / 'data/histdata_ndx_1m.parquet')
    a, b = int(pd.Timestamp(START, tz='UTC').timestamp()), int(pd.Timestamp(END, tz='UTC').timestamp()) + 86400
    hd = hd[(hd.t >= a) & (hd.t < b)]
    du = du[(du.t >= a) & (du.t < b)]
    out = {'duka_bar': int(len(du)), 'histdata_bar': int(len(hd)),
           'duka_gun': int(pd.to_datetime(du.t, unit='s').dt.date.nunique()),
           'histdata_gun': int(pd.to_datetime(hd.t, unit='s').dt.date.nunique())}
    d = du.set_index('t').close
    h = hd.set_index('t').close
    lag = {}
    rd = np.log(d).diff()
    for L in range(-120, 121):
        hh = np.log(h).diff()
        hh.index = hh.index + 60 * L
        j = pd.concat([rd.rename('d'), hh.rename('h')], axis=1, join='inner').dropna()
        if len(j) > 1000:
            lag[L] = float(j.d.corr(j.h))
    best = max(lag, key=lag.get)
    out['en_iyi_gecikme_dk'] = int(best)
    out['getiri_korelasyonu_gecikme0'] = lag.get(0)
    out['getiri_korelasyonu_en_iyi'] = lag[best]
    j = pd.concat([d.rename('d'), h.rename('h')], axis=1, join='inner').dropna()
    diff_bp = (j.h / j.d - 1) * 1e4
    out['ortak_bar'] = int(len(j))
    out['kapanis_farki_bp_medyan'] = float(diff_bp.median())
    out['kapanis_farki_bp_mutlak_p50_p95'] = [float(diff_bp.abs().quantile(.5)), float(diff_bp.abs().quantile(.95))]
    # günlük aralık oranı (NY günü)
    ny = lambda s: pd.to_datetime(s.index, unit='s', utc=True).tz_convert('America/New_York').date
    dh = du.set_index('t'); hh_ = hd.set_index('t')
    rng_d = (dh.high.groupby(ny(dh)).max() - dh.low.groupby(ny(dh)).min())
    rng_h = (hh_.high.groupby(ny(hh_)).max() - hh_.low.groupby(ny(hh_)).min())
    r = (rng_h / rng_d).dropna()
    out['gunluk_aralik_orani_histdata_bolu_duka_medyan'] = float(r.median())
    out['gunluk_aralik_orani_p10_p90'] = [float(r.quantile(.1)), float(r.quantile(.9))]
    # 1m bar başına mutlak getiri oranı (mikro oynaklık / gürültü farkı)
    jr = pd.concat([rd.rename('d'), np.log(h).diff().rename('h')], axis=1, join='inner').dropna()
    out['abs_1m_getiri_orani_h_bolu_d'] = float(jr.h.abs().mean() / jr.d.abs().mean())
    print(json.dumps(out, indent=1))
    (H / 'results/faz0_duka_vs_histdata_2018.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
