"""NOM — reliability (kalibrasyon) diyagramları, SVG (matplotlib ortamda yok).

python src/plots.py dev|final → results/plots/<faz>_reliability_<ufuk>.svg
Her grafik: x = tahmin P(TP) kova ortalaması, y = gerçekleşen TP oranı (%95 Wilson), model (turuncu) ve saat-iklimi
tabanı (gri); köşegen = mükemmel kalibrasyon.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

H = Path(__file__).resolve().parents[1]
RES = H / 'results'
OUT = RES / 'plots'
W, HH, PAD = 300, 300, 40
COLORS = {'model': '#f97316', 'clim': '#94a3b8'}


def panel(ax0: int, title: str, series: dict, vmax: float) -> str:
    sx = lambda v: ax0 + PAD + v / vmax * (W - PAD - 10)
    sy = lambda v: HH - PAD - v / vmax * (HH - PAD - 30)
    s = [f'<text x="{ax0 + W / 2}" y="18" text-anchor="middle" font-size="12" fill="#e2e8f0">{title}</text>',
         f'<line x1="{sx(0)}" y1="{sy(0)}" x2="{sx(vmax)}" y2="{sy(vmax)}" stroke="#475569" stroke-dasharray="4 3"/>',
         f'<line x1="{sx(0)}" y1="{sy(0)}" x2="{sx(vmax)}" y2="{sy(0)}" stroke="#64748b"/>',
         f'<line x1="{sx(0)}" y1="{sy(0)}" x2="{sx(0)}" y2="{sy(vmax)}" stroke="#64748b"/>']
    for k in range(0, 6):
        v = vmax * k / 5
        s.append(f'<text x="{sx(v)}" y="{HH - PAD + 14}" font-size="9" text-anchor="middle" fill="#94a3b8">{v:.2f}</text>')
        s.append(f'<text x="{ax0 + PAD - 4}" y="{sy(v) + 3}" font-size="9" text-anchor="end" fill="#94a3b8">{v:.2f}</text>')
    for name, rows in series.items():
        pts = ' '.join(f'{sx(r["pred"]):.1f},{sy(r["obs"]):.1f}' for r in rows)
        s.append(f'<polyline points="{pts}" fill="none" stroke="{COLORS[name]}" stroke-width="1.5"/>')
        for r in rows:
            s.append(f'<line x1="{sx(r["pred"]):.1f}" x2="{sx(r["pred"]):.1f}" y1="{sy(r["ci_lo"]):.1f}" y2="{sy(r["ci_hi"]):.1f}" stroke="{COLORS[name]}"/>')
            s.append(f'<circle cx="{sx(r["pred"]):.1f}" cy="{sy(r["obs"]):.1f}" r="2.5" fill="{COLORS[name]}"/>')
    s.append(f'<text x="{ax0 + W / 2}" y="{HH - 6}" text-anchor="middle" font-size="10" fill="#94a3b8">tahmin P(TP önce)</text>')
    return '\n'.join(s)


def main(phase: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((RES / f'faz5_{phase}.json').read_text())
    by = {r['target']: r for r in data}
    for hz in ('15m', '1h', '4h', 'session'):
        parts, x = [], 0
        for d in ('long', 'short'):
            r = by.get(f'{hz}_{d}_1x1')
            if not r:
                continue
            ser = {'model': r['calibration_p_tp'], 'clim': r['calibration_p_tp_clim']}
            vmax = max(0.1, max(max(q['ci_hi'], q['pred']) for v in ser.values() for q in v)) * 1.05
            parts.append(panel(x, f'{hz} {d.upper()} 1/1 ATR ({phase})', ser, min(vmax, 1.0)))
            x += W
        legend = (f'<text x="10" y="{HH + 14}" font-size="10" fill="{COLORS["model"]}">● model (isotonic)</text>'
                  f'<text x="130" y="{HH + 14}" font-size="10" fill="{COLORS["clim"]}">● NY saati iklim tabanı</text>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x} {HH + 22}" width="{x}" height="{HH + 22}">'
               f'<rect width="100%" height="100%" fill="#0f172a"/>{"".join(parts)}{legend}</svg>')
        (OUT / f'{phase}_reliability_{hz}.svg').write_text(svg)
    print('ok', list(OUT.iterdir()))


if __name__ == '__main__':
    main(sys.argv[1])
