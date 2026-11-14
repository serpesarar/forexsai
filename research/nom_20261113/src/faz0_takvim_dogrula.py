"""Faz 0.3 — statik NYSE takvimi (backend/services/nom/nyse_calendar.py) ile pandas_market_calendars (XNYS) karşılaştırması
2018–2026: tatiller ve yarım günler birebir mi? Ayrıca 1MDATA/mt5_ustec_1m_bars.json'un saat ekseni denetimi.
.venv_ext ile çalıştırılır. Çıktı: results/faz0_takvim_1mdata.json"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import pandas_market_calendars as pmc
H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(REPO / 'backend'))
sys.path.insert(0, str(H / 'src'))
from services.nom import nyse_calendar as CAL  # noqa: E402
import faz0_build as F0  # noqa: E402

nyse = pmc.get_calendar('XNYS')
sch = nyse.schedule(start_date='2018-01-01', end_date='2026-12-31')
open_days = set(sch.index.date)
wd = [d.date() for d in pd.bdate_range('2018-01-01', '2026-12-31')]
pmc_hol = {d for d in wd if d not in open_days}
close_et = sch.market_close.dt.tz_convert('America/New_York')
pmc_early = {d.date() for d, c in zip(sch.index, close_et) if c.hour < 16}
st_hol = set(CAL.HOLIDAYS)
st_early = set(CAL.EARLY_CLOSE)
out = {'tatil_pmc': len(pmc_hol), 'tatil_statik': len(st_hol), 'tatil_yalniz_pmc': sorted(map(str, pmc_hol - st_hol)),
       'tatil_yalniz_statik': sorted(map(str, st_hol - pmc_hol)), 'yarim_pmc': len(pmc_early), 'yarim_statik': len(st_early),
       'yarim_yalniz_pmc': sorted(map(str, pmc_early - st_early)), 'yarim_yalniz_statik': sorted(map(str, st_early - pmc_early))}
# 1MDATA json
j = json.load(open(REPO / '1MDATA/mt5_ustec_1m_bars.json'))
r = pd.DataFrame(j.get('bars') or []).rename(columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close'})
gold = pd.read_csv(REPO / 'nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv')
gold['t'] = (pd.to_datetime(gold.time_utc, utc=True).astype('int64') // 10**9)
duka = pd.read_parquet(H.parent / 'yon_lab_20261114/data/ndx_1m_v2.parquet')
for name, ref in (('mt5_gold', gold), ('dukascopy', duka)):
    for shift_min in (0, -180, -120):
        rr = r.assign(t=r.t + shift_min * 60)
        c = F0.compare(rr[['t', 'open', 'high', 'low', 'close']], ref[['t', 'open', 'high', 'low', 'close']], f'1mdata{shift_min}', name)
        out[f'1mdata_vs_{name}_kaydirma{shift_min}'] = {k: c.get(k) for k in ('overlap_bars', 'best_lag_min', 'ret_corr_lag0', 'agree_within_tol_frac')}
out['1mdata_kapsam'] = [str(pd.to_datetime(r.t.min(), unit='s')), str(pd.to_datetime(r.t.max(), unit='s')), len(r)]
(H / 'results/faz0_takvim_1mdata.json').write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
