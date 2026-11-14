"""NOM Faz 1 — aynı-bar (TP+SL) belirsizliğinin tick verisiyle çözümü (2025-01 → 06, Dukascopy bid/ask tick).

Belirsiz etiketlerde (amb=1) çözüm barının tick'lerinde hangi bariyer önce? Muhafazakâr SL kuralının
EV'ye etkisi = (belirsiz payı) × (TP-önce oranı) × (TP R + 1).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
REPO = H.parents[1]
sys.path.insert(0, str(REPO / 'backend'))
from services.nom import labels as LB  # noqa: E402

TICKS = REPO / 'ndx_reflex_engine/data/ticks'


def main() -> None:
    m = pd.read_parquet(H / 'data/ndx_1m_v1.parquet')
    F = pd.read_parquet(H / 'data/features_v1.parquet', columns=['_i0', '_atr_M5', '_atr_M15', '_atr_H1'])
    t_lo = pd.Timestamp('2025-01-02', tz='UTC').timestamp()
    t_hi = pd.Timestamp('2025-06-19', tz='UTC').timestamp()
    out = []
    for hz in ('15m', '1h', '4h'):
        L = pd.read_parquet(H / f'data/labels_{hz}.parquet')
        atr_col = '_atr_' + LB.HORIZONS[hz]['atr_tf']
        L = L[(L.t >= t_lo) & (L.t < t_hi)]
        for d in ('long', 'short'):
            for tp, sl in LB.GEOMETRIES:
                gk = LB.geom_key(tp, sl)
                amb = L[L[f'{d}_{gk}_amb'] == 1]
                n_res = int((L[f'{d}_{gk}_cls'].isin([0, 1])).sum())
                first_tp = first_sl = unk = 0
                for _, r in amb.iterrows():
                    i0 = int(F._i0.iloc[int(r.row)])
                    A = float(F[atr_col].iloc[int(r.row)])
                    k = i0 + int(r[f'{d}_{gk}_tbar'])
                    t_bar = int(m.t.iloc[k])
                    day = pd.to_datetime(t_bar, unit='s', utc=True).strftime('%Y-%m-%d')
                    f = TICKS / f'{day}.parquet'
                    if not f.exists():
                        unk += 1
                        continue
                    tk = pd.read_parquet(f)
                    tk = tk[(tk.ts_ms >= t_bar * 1000) & (tk.ts_ms < (t_bar + 60) * 1000)]
                    o, s = float(m.open.iloc[i0]), float(m.spr.iloc[i0])
                    if d == 'long':
                        e = o + s + LB.SLIP_PTS
                        hit_tp = tk.bid >= e + tp * A
                        hit_sl = tk.bid <= e - sl * A
                    else:
                        e = o - LB.SLIP_PTS
                        hit_tp = tk.ask <= e - tp * A
                        hit_sl = tk.ask >= e + sl * A
                    a = np.argmax(hit_tp.to_numpy()) if hit_tp.any() else 10**9
                    b = np.argmax(hit_sl.to_numpy()) if hit_sl.any() else 10**9
                    if a == b == 10**9:
                        unk += 1
                    elif a < b:
                        first_tp += 1
                    else:
                        first_sl += 1
                out.append({'horizon': hz, 'dir': d, 'geom': gk, 'resolved': n_res, 'ambiguous': len(amb),
                            'tick_tp_first': first_tp, 'tick_sl_first': first_sl, 'tick_unknown': unk,
                            'ev_bias_r': (first_tp * (tp / sl + 1)) / max(1, n_res)})
    df = pd.DataFrame(out)
    df.to_csv(H / 'results/faz1_tick_ambiguity.csv', index=False)
    print(df.to_string())
    tot = df[['ambiguous', 'tick_tp_first', 'tick_sl_first', 'tick_unknown']].sum().to_dict()
    tot['max_ev_bias_r'] = float(df.ev_bias_r.max())
    (H / 'results/faz1_tick_ambiguity.json').write_text(json.dumps(tot, indent=1))
    print(tot)


if __name__ == '__main__':
    main()
