"""Düzeltme turu eşitlik testi (EK-P1 §4): önceki koşuda `ok` olan scriptlerden rastgele örneklemi verilen motorla
yeniden koştur, 4 sembolün tepki durumlarını bayt bayt karşılaştır.

Kodu değişen scriptler (iki derleme taramasının özetleri farklı) ve strateji scriptleri (broker emülatörü) beklenen
değişiklik sınıfıdır; örneklem onların DIŞINDAN çekilir ve tek fark bile raporlanır.
Kullanım: python equiv_check.py <motor_dizini> <n> <eski_tarama.json> <yeni_tarama.json>
"""
from __future__ import annotations

import gzip
import json
import pickle
import random
import re
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(HERE.parent / "gosterge_cakisma_20261025"))
sys.path.insert(0, str(ENGINE))
SEED = 20261026
STRAT_RE = re.compile(r"^\s*strategy\s*\(", re.M)


def _rerun(rec):
    import batch                                      # motor dizinindeki batch: _DF + _run_one
    return batch._run_one(rec)


def main(n: int, old_scan: str, new_scan: str):
    import batch
    import pine_src
    old, new = json.load(open(old_scan)), json.load(open(new_scan))
    prev = {}
    for p in sorted((HERE / "data/runs/recent").glob("part_*.pkl.gz")):
        with gzip.open(p, "rb") as f:
            for r in pickle.load(f):
                if all(v["status"] == "ok" for v in r["per_sym"].values()):
                    prev[r["sid"]] = r
    src = {r["sid"]: r for r in pine_src.iter_sources(True) if r["sid"] in prev}
    pool_ids = sorted(s for s in prev if s in src and old.get(s, [None, None, ""])[2] == new.get(s, [None, None, "x"])[2]
                      and not STRAT_RE.search(src[s]["source"]))
    random.Random(SEED).shuffle(pool_ids)
    pick = [src[s] for s in pool_ids[:n]]
    print(f"havuz {len(pool_ids)} (kodu aynı, strateji değil, 4 sembolde ok); örneklem {len(pick)}", flush=True)
    diff = []
    with Pool(7, initializer=batch._init, initargs=("recent",)) as pool:
        for r in pool.imap_unordered(_rerun, pick, chunksize=2):
            a = prev[r["sid"]]["per_sym"]
            for s, v in r["per_sym"].items():
                if v["status"] != a[s]["status"] or v["states"] != a[s]["states"]:
                    diff.append((r["sid"], r["name"], s, a[s]["status"], v["status"], (v.get("error") or "")[:80]))
                    break
    for d in diff:
        print("FARK", *d)
    print(f"sonuç: {len(diff)} fark / {len(pick)}")
    return len(diff)


if __name__ == "__main__":
    sys.exit(1 if main(int(sys.argv[2]), sys.argv[3], sys.argv[4]) else 0)
