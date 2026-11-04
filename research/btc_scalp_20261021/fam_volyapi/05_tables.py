"""Rapor tabloları → results/summary.md"""
import numpy as np
import pandas as pd

import common as C

d = pd.read_csv(f"{C.RES}/cells.csv")
S = pd.read_csv(f"{C.RES}/selection_card.csv")
L = []


def f(x, k=3):
    return f"{x:+.{k}f}" if pd.notna(x) else "—"


def ysig(s):
    if not isinstance(s, str):
        return "—"
    out = []
    for tok in s.split():
        y, rest = tok.split(":")
        v = float(rest.split("(")[0])
        out.append(f"{y[2:]}{'+' if v > 0 else '−'}")
    return " ".join(out)


# 1) Aile başına DISC-seçilmiş hücre: bölme tablosu
L.append("## 1. Aile başına DISC'te seçilen hücre → POST kartı\n")
L.append("| aile | hücre | DISC n / ortR / P1% | OOS ortR | BLIND ortR | POST n | WR | ortR [%95 GA] | bp net | P(EV>0) | yarılar | stres | icra farkı | tek-poz | P1 ort / yüzd. | brüt kenar−P1 | aynı-bar | işlem/gün | yıl işaretleri (POST) | kart | p_sel | verdikt |")
L.append("|" + "---|" * 22)
for r in S.itertuples():
    post = d[(d.variant == r.variant) & (d.dir == r.dir) & (d.geom == r.geom) & (d.split == "POST")].iloc[0]
    L.append(f"| {r.family} | {r.variant} {r.dir} {r.geom} | {r.DISC_n} / {f(r.DISC_meanR)} / {r.DISC_pl_pct*100:.1f} | "
             f"{f(r.OOS_meanR)} | {f(r.BLIND_meanR)} | {r.POST_n} | {post.WR:.3f} | {f(r.POST_meanR)} {r.POST_ci} | "
             f"{r.POST_bp:+.2f} | {r.POST_P:.3f} | {r.POST_halves} | {f(r.POST_stress)} | {r.POST_exec_gap:.3f} | {f(r.POST_sp)} | "
             f"{f(r.POST_pl_mean)} / {r.POST_pl_pct*100:.1f} | {f(r.POST_edge_gross)} | {r.POST_same*100:.2f}% | {r.POST_tpd:.2f} | "
             f"{ysig(post.years)} | {r.card6}/6 | {r.p_sel:.2f} | {r.verdict} |")

# 2) Hipotez × yön: DISC-en iyi geometri, tüm bölmeler
L.append("\n## 2. Hipotez × yön (geometri DISC'te seçildi; POST istatistikleri)\n")
L.append("| varyant | yön | geo | DISC ortR (P1%) | OOS ortR (P1%) | BLIND ortR (P1%) | POST n | POST WR | POST ortR | POST bp | P(EV>0) | yarılar | stres | tek-poz | FIX15 | MAKER | TAKER | işlem/gün | yıllar + / toplam |")
L.append("|" + "---|" * 19)
for (v, dr), grp in d[d.split == "DISC"].groupby(["variant", "dir"], sort=False):
    b = grp.sort_values("meanR", ascending=False).iloc[0]
    row = {}
    for sp in ("DISC", "OOS", "BLIND", "POST", "ALL"):
        row[sp] = d[(d.variant == v) & (d.dir == dr) & (d.geom == b.geom) & (d.split == sp)].iloc[0]
    P = row["POST"]
    A = row["ALL"]
    L.append(f"| {v} | {dr} | {b.geom} | {f(row['DISC'].meanR)} ({row['DISC'].pl_pct*100:.0f}) | {f(row['OOS'].meanR)} ({row['OOS'].pl_pct*100:.0f}) | "
             f"{f(row['BLIND'].meanR)} ({row['BLIND'].pl_pct*100:.0f}) | {P.n} | {P.WR:.3f} | {f(P.meanR)} | {P.bp_net:+.2f} | {P.P:.2f} | "
             f"{P.half1:+.3f}/{P.half2:+.3f} | {f(P.STRESS)} | {f(P.sp)} | {f(P.FIX15)} | {f(P.MAKER)} | {f(P.TAKER)} | {P.tpd:.2f} | "
             f"{A.years_pos}/{A.years_n} |")

# 3) Plasebo simetrisi (E26/E28): aile × bölme, yüzdelik ≥95 ve ≤5 hücre sayısı
L.append("\n## 3. Plasebo simetrisi (hücre sayısı: P1 yüzdeliği ≥%95 / ≤%5; 4 geometri × yön)\n")
L.append("| aile | hücre | DISC ≥95 / ≤5 | OOS | BLIND | POST |")
L.append("|---|---|---|---|---|---|")
for fam, grp in d.groupby("family", sort=False):
    cells = grp[grp.split == "DISC"].shape[0]
    s = []
    for sp in ("DISC", "OOS", "BLIND", "POST"):
        x = grp[grp.split == sp]
        s.append(f"{(x.pl_pct >= .95).sum()} / {(x.pl_pct <= .05).sum()}")
    L.append(f"| {fam} | {cells} | " + " | ".join(s) + " |")
tot = []
for sp in ("DISC", "OOS", "BLIND", "POST"):
    x = d[d.split == sp]
    tot.append(f"{(x.pl_pct >= .95).sum()} / {(x.pl_pct <= .05).sum()}")
L.append(f"| **toplam** | {d[d.split=='DISC'].shape[0]} | " + " | ".join(tot) + " |")

# 4) Sıkışmanın katkısı: VS vs kontrol
L.append("\n## 4. Sıkışma koşulunun katkısı (aynı kırılım, sıkışmalı − sıkışmasız; ortR, G1–G4 ortalaması)\n")
L.append("| TF | yön | DISC | OOS | BLIND | POST |")
L.append("|---|---|---|---|---|---|")
for a, b in (("VS1", "VS1-C"), ("VS2", "VS2-C")):
    for dr in ("L", "S"):
        s = []
        for sp in ("DISC", "OOS", "BLIND", "POST"):
            x = d[(d.variant == a) & (d.dir == dr) & (d.split == sp)].meanR.mean()
            y = d[(d.variant == b) & (d.dir == dr) & (d.split == sp)].meanR.mean()
            s.append(f"{x:+.3f} − {y:+.3f} = {x-y:+.3f}")
        L.append(f"| {a} | {dr} | " + " | ".join(s) + " |")

# 5) ST-S (L+S)/2
L.append("\n## 5. ST-S scalp straddle: (L+S)/2 ortR ve P1 ortalaması\n")
L.append("| çapa | geo | DISC | OOS | BLIND | POST | POST P1 (L+S)/2 |")
L.append("|---|---|---|---|---|---|---|")
for v in ("ST-S-0930", "ST-S-1000"):
    for gname in C.GEOMS:
        s = []
        for sp in ("DISC", "OOS", "BLIND", "POST"):
            x = d[(d.variant == v) & (d.geom == gname) & (d.split == sp)]
            s.append(f"{x.meanR.mean():+.3f}")
        x = d[(d.variant == v) & (d.geom == gname) & (d.split == "POST")]
        L.append(f"| {v[-4:]} | {gname} | " + " | ".join(s) + f" | {x.pl_mean.mean():+.3f} |")

# 6) ST-H teşhisi
sr = pd.read_csv(f"{C.RES}/st_h_real.csv")
hr = pd.read_csv(f"{C.RES}/st_h_hours.csv")
sy = pd.read_csv(f"{C.RES}/st_h_synth.csv")
import json
vr = json.load(open(f"{C.RES}/st_h_vr.json"))
L.append("\n## 6. ST-H (NY 10:00→16:00, SL 1×ATR14(1h), PEP) teşhisi\n")
L.append("| bölme | n | L ortR | S ortR | (L+S)/2 [%95 GA] | P>0 | stop payı L/S | stop sonrası kalan L/S (R) | SL medyan bp | saat-plasebo sırası (24) | sentetik (L+S)/2 ort [min, maks] (20) | VR 10→16 [%95] |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in sr.itertuples():
    sp = r.split
    h = hr[hr.split == sp].sort_values("LS_avg", ascending=False).reset_index(drop=True)
    rk = int(np.where(h.hour == 10)[0][0]) + 1
    s = sy[sy.split == sp]
    v = vr["10:00"].get(sp)
    vs = f"{v['VR']:.3f} [{v['lo']:.2f}, {v['hi']:.2f}]" if v else "—"
    L.append(f"| {sp} | {r.n} | {r.R_L:+.3f} | {r.R_S:+.3f} | {r.LS_avg:+.3f} [{r.LS_ci_lo:+.3f}, {r.LS_ci_hi:+.3f}] | {r.P_LS_gt0:.3f} | "
             f"{r.stop_L:.2f}/{r.stop_S:.2f} | {r.rem_L:+.3f}/{r.rem_S:+.3f} | {r.s_bp_med:.0f} | {rk} | "
             f"{s.LS_avg.mean():+.3f} [{s.LS_avg.min():+.3f}, {s.LS_avg.max():+.3f}] | {vs} |")
L.append("\nSaat plasebosu (POST, (L+S)/2, NY çapa saati): " + ", ".join(
    f"{int(r.hour):02d}:{r.LS_avg:+.3f}" for r in hr[hr.split == "POST"].sort_values("hour").itertuples()))
L.append("\nSaat plasebosu (DISC): " + ", ".join(
    f"{int(r.hour):02d}:{r.LS_avg:+.3f}" for r in hr[hr.split == "DISC"].sort_values("hour").itertuples()))
L.append("\nVR (NY çapa → +6 s), DISC / POST: " + ", ".join(
    f"{k}: {vr[k]['DISC']['VR']:.2f}/{vr[k]['POST']['VR']:.2f}" for k in sorted(vr)))

open(f"{C.RES}/summary.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
