"""İndirilen kaynakların ayrıştırma oranı + hata sınıfları."""
import collections
import gzip
import json
import sys

import pine_parser as P

rows = [json.loads(l) for l in gzip.open("data/src/sources.jsonl.gz", "rt")]
ok = [r for r in rows if r["ok"]]
res, errs, ex = collections.Counter(), collections.Counter(), {}
for r in ok:
    try:
        P.parse(r["source"])
        res["ok"] += 1
    except Exception as e:
        res["err"] += 1
        key = type(e).__name__ + ": " + " ".join(str(e).split()[:4])
        errs[key] += 1
        ex.setdefault(key, (r["name"], str(e)))
print(len(ok), dict(res), f"oran {res['ok'] / max(len(ok), 1):.3f}")
for k, n in errs.most_common(int(sys.argv[1]) if len(sys.argv) > 1 else 15):
    print(n, k, "|", ex[k][0][:40], "|", ex[k][1][:90])
