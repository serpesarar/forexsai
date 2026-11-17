"""report_tables.py — EK-3 rapor tabloları (results/<sym>/ → markdown, stdout)."""
import json
import sys

import fblib as F

sym = sys.argv[1].lower()
d = json.load(open(F.HERE / "results" / sym / "birincil.json"))
c = {x["hucre"]: x for x in d["hucreler"]}
f = lambda v: "" if v is None else f"{v:+.3f}".replace(".", ",")
print("| TF | UZUN tüm (n) | KEŞİF | TEST | KÖR | KISA tüm (n) | KEŞİF | TEST | KÖR | Plasebo farkı U / K |")
print("|---|---|---|---|---|---|---|---|---|---|")
for tf in F.TFS_NDX:
    u, k = c.get(f"{tf}|UZUN"), c.get(f"{tf}|KISA")
    row = [tf]
    for x in (u, k):
        b = x["birincil"]
        row += [f"{f(b['TUM'].get('ortR'))} ({b['TUM'].get('n')})"] + [f(b[p].get("ortR")) for p in ["KESIF", "TEST", "KOR"]]
    row.append(f"{f(u.get('K4_fark'))} / {f(k.get('K4_fark'))}")
    print("| " + " | ".join(row) + " |")
print("Holm en iyi:", d["holm"][0])
print(json.dumps(json.load(open(F.HERE / "results" / sym / "grid_ozet.json")), indent=0))
