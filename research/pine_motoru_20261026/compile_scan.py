"""Kapsama tanısı: tüm scriptleri yalnız ayrıştır + çevir (çalıştırmadan) → derleme-zamanı başarısızlık sınıfları.

Her script için çevrilmiş kodun özeti (sha1) de yazılır: düzeltme turunda (EK-P1 §4) kodu değişen scriptleri bulmak için
iki motor sürümünün taraması karşılaştırılır.
Kullanım: python compile_scan.py [motor_dizini=bu dizin] [çıktı=data/compile_scan.json]
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "data/compile_scan.json"
sys.path.insert(0, str(ENGINE))
import pine_parser as P  # noqa: E402
import pine_runtime as R  # noqa: E402
import pine_src  # noqa: E402
import pine_transpile as TR  # noqa: E402


def main():
    out = {}
    for i, r in enumerate(pine_src.iter_sources(True)):
        if r.get("type") == "library":
            continue
        try:
            prog = P.parse(r["source"])
        except Exception as e:
            out[r["sid"]] = ["parse_error", f"{type(e).__name__}: {e}"[:160], ""]
            continue
        try:
            code, _ = TR.transpile(prog, P.version_of(r["source"]))
            out[r["sid"]] = ["ok", "", hashlib.sha1(code.encode()).hexdigest()[:16]]
        except R.Unsupported as e:
            out[r["sid"]] = ["unsupported", str(e)[:160], ""]
        except Exception as e:
            out[r["sid"]] = ["transpile_error", f"{type(e).__name__}: {e}"[:160], ""]
        if i % 4000 == 0:
            print(i, flush=True)
    json.dump(out, open(OUT, "w"))
    print(dict(Counter(v[0] for v in out.values())))
    cls = Counter(v[0] + " | " + re.sub(r"\d+", "#", v[1])[:80] for v in out.values() if v[0] != "ok")
    for k, n in cls.most_common(40):
        print(n, k)


if __name__ == "__main__":
    main()
