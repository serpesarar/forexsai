"""results/tables.md — notlar için tablolar (analysis.json + cells.csv)."""
import json
from pathlib import Path
import pandas as pd
OUT = Path(__file__).resolve().parent / "results"
A = json.loads((OUT / "analysis.json").read_text())
C = pd.read_csv(OUT / "cells.csv")
f = lambda x: "—" if x is None or (isinstance(x, float) and pd.isna(x)) else (f"{x:+.3f}" if isinstance(x, float) else str(x))
L = ["| grup | seçilen hücre (KEŞİF) | n onay | WR / başabaş | ortR | %95 GA | P(EV>0) | yarılar | ×1,5 spread | iyimser (fark) | 15$ | tek-poz | plasebo ort / yüzdelik | OOS | KÖR | kart | Holm p |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for g, v in A["kart_onay"].items():
    s = v["stats"]; holm = A["holm_onay_4"].get(g, "—")
    L.append(f"| {g} | `{v['hucre']}` | {s['n']} ({s['gun']} gün) | %{s['wr']} / %{s['basabas_wr']} | {s['ortR']:+.3f} | "
             f"[{s['ci95'][0]:+.3f}, {s['ci95'][1]:+.3f}] | %{100*s['P_EV']:.1f} | {s['yari1']:+.3f} / {s['yari2']:+.3f} | "
             f"{v['ortR_spread_x1.5']:+.3f} | {v['ortR_iyimser']:+.3f} ({abs(v['ortR_iyimser']-s['ortR']):.3f}) | {v['ortR_sabit15usd']:+.3f} | "
             f"{v['tek_poz_ortR']:+.3f} | {v.get('plasebo_ort', 0):+.3f} / %{100*v.get('plasebo_yuzdelik', 0):.0f} | "
             f"{v['OOS']['ortR']:+.3f} (n {v['OOS']['n']}) | {v['KOR']['ortR']:+.3f} (n {v['KOR']['n']}) | "
             f"{v['kart_gecen']}/6 {v['kart_verdikt']} | {holm} |")
L += ["", "| hücre | KEŞİF n / ortR / plasebo% | OOS n / ortR | KÖR n / ortR | ONAY ortR / P(EV>0) / plasebo% | TÜM n / ortR |", "|---|---|---|---|---|---|"]
for r in C.itertuples():
    L.append(f"| `{r.cell}` | {r.KESIF_n} / {f(r.KESIF_ortR)} / {f(r.KESIF_plasebo_yuzdelik)} | {r.OOS_n} / {f(r.OOS_ortR)} | "
             f"{r.KOR_n} / {f(r.KOR_ortR)} | {f(r.ONAY_ortR)} / {f(r.ONAY_P_EV)} / {f(r.ONAY_plasebo_yuzdelik)} | {r.TUM_n} / {f(r.TUM_ortR)} |")
(OUT / "tables.md").write_text("\n".join(L))
print("\n".join(L[:8]))
