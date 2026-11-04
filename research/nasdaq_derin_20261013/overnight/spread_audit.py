"""İcra denetimi (post-hoc, ölçüt 5'in derinleştirmesi): Dukascopy 2025 bid/ask ile dakika-bazlı spread ve
18:00 yeniden açılış barının bid-artefaktı."""
import pandas as pd, numpy as np
d = pd.read_parquet('/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data/duka_1m_2025.parquet')
d = d[d.ts.dt.second == 0].drop_duplicates('ts').set_index('ts').sort_index()
d['sp'] = d.ask_open - d.open
ny = d.index.tz_convert('America/New_York'); d['hm'] = ny.hour * 60 + ny.minute
tbl = d.groupby('hm').sp.median()
for hm in [17*60+59, 18*60, 18*60+1, 18*60+2, 18*60+5, 18*60+10, 18*60+30, 19*60, 60, 61, 120, 180, 240, 241, 9*60+30, 9*60+31, 16*60, 16*60+1, 16*60+55]:
    print(f"{hm//60:02d}:{hm%60:02d} medyan spread {tbl.get(hm, np.nan):.2f}  ort {d[d.hm==hm].sp.mean():.2f}  n={int((d.hm==hm).sum())}")
print('gün geneli medyan spread:', round(d.sp.median(), 2))
# 18:00 → X: bid getirisi vs mid getirisi
d['mid'] = (d.open + d.ask_open) / 2
def ret(col, h0, h1):
    a = d[d.hm == h0][col]; a.index = a.index.tz_convert('America/New_York').normalize()
    b = d[d.hm == h1][col]; b.index = b.index.tz_convert('America/New_York').normalize()
    j = pd.concat([a, b], axis=1, keys=['a', 'b']).dropna()
    return (j.b - j.a).mean(), len(j)
for h0, h1 in [(18*60, 19*60), (18*60+1, 19*60), (18*60+5, 19*60), (18*60+30, 19*60+30), (60, 240), (120, 180)]:
    rb, n = ret('open', h0, h1); rm, _ = ret('mid', h0, h1); ra, _ = ret('ask_open', h0, h1)
    print(f"{h0//60:02d}:{h0%60:02d}→{h1//60:02d}:{h1%60:02d}  bid {rb:+.2f}p  mid {rm:+.2f}p  ask {ra:+.2f}p  n={n}")
# bars_1m 2025 = duka bid mi?
b = pd.read_parquet('/Users/melihcanodacioglu/Desktop/panel/research/ndx_pattern_motifs/data/bars_1m.parquet').set_index('ts')
j = b.join(d[['open', 'ask_open']], rsuffix='_d', how='inner')
print('bars_1m vs duka bid açılış fark medyanı:', (j.open - j.open_d).median(), 'n', len(j))
