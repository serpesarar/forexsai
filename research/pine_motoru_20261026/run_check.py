"""Örneklem scriptlerini çalıştırıp durum dağılımı + hata sınıfları raporla.
Kullanım: python run_check.py [n_scripts] [n_bars] [top_err]
"""
import collections
import gzip
import json
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "gosterge_cakisma_20261025"))
import data  # noqa: E402  (GÇM veri katmanı)

import pine_run  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
BARS = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
TOP = int(sys.argv[3]) if len(sys.argv) > 3 else 25

import pine_src  # noqa: E402
SKIP = int(sys.argv[4]) if len(sys.argv) > 4 else 0
rows = list(pine_src.iter_sources(True, N + SKIP))[SKIP:]
df = data.load("NDX", "1h").iloc[-BARS:].reset_index(drop=True)
st, errs, ex, secs = collections.Counter(), collections.Counter(), {}, []
nout = collections.Counter()
t0 = time.time()
for r in rows:
    res = pine_run.run_script(r["source"], df, "1h", "NDX", timeout_s=60)
    st[res["status"]] += 1
    if res["status"] == "ok":
        secs.append(res["seconds"])
        for o in res["outputs"].values():
            nout[o["kind"]] += 1
    else:
        msg = res["error"] or ""
        key = res["status"] + ": " + " ".join(msg.split("@")[0].split()[:5])
        errs[key] += 1
        ex.setdefault(key, (r["name"], msg))
print(f"{len(rows)} script, {BARS} bar, {time.time() - t0:.0f}s | {dict(st)} | ok oranı {st['ok'] / len(rows):.3f}")
if secs:
    secs.sort()
    print(f"süre/script medyan {secs[len(secs) // 2]:.2f}s p90 {secs[int(len(secs) * .9)]:.2f}s | çıktılar {dict(nout)}")
for k, n in errs.most_common(TOP):
    print(n, k[:90], "|", ex[k][0][:35], "|", ex[k][1][:110])
