"""v2 çapraz-pencere tekrar sınaması (PN-07).

Aynı koşul kümesi (script|plot|durum) farklı sembol/TF penceresinde de aday çıktıysa: yön AYNI mı TERS mi?
Kenar varsa aynı-yön, ters-yöne baskın gelmeli; tesadüfte ikisi eşit (binom 0,5). Ayrıca h-esnek (|Δh|≤2) ve
yalnız kanıtlı alt kümesi raporlanır.
Kullanım: python capraz_tekrar_v2.py   → results_kombo_v2/capraz_tekrar.json
"""
import itertools, json
from math import comb
from pathlib import Path
import pandas as pd

R = Path(__file__).resolve().parent / "results_kombo_v2"
rows = []
for p in sorted(R.glob("full_*_*/*/adaylar.csv")) + sorted(R.glob("full_*_*/*/ciftler.csv")):
    d = pd.read_csv(p, usecols=["window", "h", "dir", "kosullar", "KASA_lift", "kanitli"])
    rows.append(d)
D = pd.concat(rows, ignore_index=True)
D["key"] = D.kosullar.map(lambda s: frozenset(s.split(" & ")))
wins = sorted(D.window.unique())

def binom_p(k, n):
    return sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n if n else float("nan")

out = {"pencere": wins, "aday": len(D)}
for name, sub in (("tum", D), ("kanitli", D[D.kanitli == True])):
    same = opp = 0
    ex = []
    g = {}
    for r in sub.itertuples():
        g.setdefault(r.key, []).append(r)
    for k, rs in g.items():
        for a, b in itertools.combinations(rs, 2):
            if a.window == b.window or abs(a.h - b.h) > 2:
                continue
            if a.dir == b.dir:
                same += 1
                if len(ex) < 5:
                    ex.append([a.window, b.window, a.dir, a.h, b.h])
            else:
                opp += 1
    n = same + opp
    out[name] = dict(ayni_yon=same, ters_yon=opp, binom_p_ayni_fazla=binom_p(same, n), ornek=ex)
(R / "capraz_tekrar.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps(out, indent=1, ensure_ascii=False)[:1500])
