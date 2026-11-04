"""Uygulanan göstergelerin topluluk scriptlerini kapsama oranı (PROTOCOL §1)."""
import json
from collections import Counter

import config as C
import data
import indicators

UNIQUE = C.ROOT / "research/indicator_atlas_20261025/topluluk_taramasi/data/unique_scripts.jsonl"
NOT_INDICATOR = {"automation_tools"}


def main() -> dict:
    book = indicators.compute(data.load("NDX", "1h"), "1h")        # hacimli TF → tüm aileler görünür
    fams = sorted({fam for _, fam in book.meta.values()})
    inds = sorted({ind for ind, _ in book.meta.values()})
    rows = [json.loads(line) for line in UNIQUE.open()]
    classified = [r for r in rows if r["families"] and set(r["families"]) - NOT_INDICATOR]
    covered = [r for r in classified if set(r["families"]) & set(fams)]
    boost_all = sum(r.get("boosts") or 0 for r in classified)
    boost_cov = sum(r.get("boosts") or 0 for r in covered)
    per_fam = Counter(f for r in classified for f in r["families"])
    missing = sorted(((f, n) for f, n in per_fam.items() if f not in fams and f not in NOT_INDICATOR), key=lambda x: -x[1])
    out = dict(indicators=len(inds), states=len(book.states), families_implemented=fams, n_families=len(fams),
               scripts_total=len(rows), scripts_classified=len(classified), scripts_covered=len(covered),
               share_scripts=round(len(covered) / len(classified), 4), share_boost=round(boost_cov / boost_all, 4),
               missing_families=missing)
    C.RES.mkdir(exist_ok=True)
    json.dump(out, open(C.RES / "coverage.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k != "families_implemented"}, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    main()
