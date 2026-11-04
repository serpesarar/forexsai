"""Holm (7 hipotez, OOS∪BLIND tek-yönlü p) + özet tablo."""
import json, os
R = json.load(open("results/regime.json")); E = json.load(open("results/exits.json"))
rows = []
for h in ["C01_VIXREG_gunluk", "C03_QQQ_gun", "C04_QQQ_bosluk", "C05_QQQ_korelasyon", "C06_DXY", "C07_US10Y"]:
    H = R[h]; c = H["cells"][H["selected"]]
    rows.append(dict(h=h, sel=H["selected"], p=H["p_post"], card=c["card_POST"], blind=c["BLIND"].get("meanR"),
                     base_long=c["POST"]["base_long"], plc=H["placebo_pct"], psel=H["maxz_disc_psel"]))
C = E["C02_VIXREG_notr"]; c = C["cells"][C["selected"]]
rows.append(dict(h="C02_VIXREG_notr", sel=C["selected"], p=c["p_post"], card=c["card_POST"], blind=c["BLIND"]["meanR"],
                 base_long=c["POST"]["heplong"], plc=c["placebo_pct"], psel=C["maxz_disc_psel"]))
rows.sort(key=lambda r: r["p"]); m = len(rows); alive = True
for i, r in enumerate(rows):
    thr = 0.05 / (m - i); r["holm_thr"] = thr; r["holm_pass"] = bool(alive and r["p"] <= thr); alive = r["holm_pass"]
json.dump(rows, open("results/summary.json", "w"), indent=1, default=str)
for r in rows:
    k = r["card"]
    print(f"{r['h']:22s} {r['sel']:12s} n={k['n']:5d} R={k['meanR']:+.4f} [{k['lo']:+.3f},{k['hi']:+.3f}] P={k['P']:.3f} "
          f"h={k['h1']:+.3f}/{k['h2']:+.3f} st={k['stress']:+.4f} gap={k['gap']:.4f} single={k['single']:+.4f} pass={k['passed']} "
          f"plc={r['plc']:.2f} BLIND={r['blind']:+.4f} long={r['base_long']:+.4f} p={r['p']:.3f} holm={r['holm_pass']} psel={r['psel']:.3f} beWR={k['beWR']:.3f} WR={k['WR']:.3f}")
