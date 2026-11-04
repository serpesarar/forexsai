"""Tüm geçmiş penceresi (v2 madenci için): seçili scriptleri TEK sembolün tüm 1h tarihinde koştur.

Pencere adı full_<tf>_<SYM> (ör. full_1h_NDX). Script listesi: data/full_sids_<sym>.txt (recent koşusunda o sembolde
çalışıp benzersiz durum katan scriptler, popülerlik sırasıyla). Devam ettirilebilir.
Kullanım: python run_full.py NDX [1h] [workers]
"""
from __future__ import annotations

import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import batch  # noqa: E402

TIMEOUT_MULT = 5          # ~5 kat bar → orantılı süre
FLUSH_EVERY = 200


def _init(sym: str, tf: str):
    import data
    batch.SYMS, batch.TF = (sym,), tf
    batch.TIMEOUT_S = batch.TIMEOUT_S * TIMEOUT_MULT
    batch._DF[sym] = data.load(sym, tf).reset_index(drop=True)


def main(sym: str = "NDX", tf: str = "1h", workers: int = 6):
    import pine_src
    window = f"full_{tf}_{sym}"
    run_dir = HERE / "data/runs" / window
    run_dir.mkdir(parents=True, exist_ok=True)
    order = (HERE / f"data/full_sids_{sym.lower()}.txt").read_text().split()
    want, done = set(order), batch.done_sids(run_dir)
    pos = {s: i for i, s in enumerate(order)}
    recs = sorted((r for r in pine_src.iter_sources(True) if r["sid"] in want and r["sid"] not in done),
                  key=lambda r: pos[r["sid"]])
    print(f"{window}: {len(recs)} script (atlanan {len(done)}), {workers} süreç", flush=True)
    k, out, t0 = batch.k0_start(run_dir), [], time.time()
    with Pool(workers, initializer=_init, initargs=(sym, tf), maxtasksperchild=100) as pool:
        for i, res in enumerate(pool.imap(batch._run_one, recs, chunksize=1), 1):
            out.append(res)
            if len(out) == FLUSH_EVERY:
                batch._flush(run_dir, k, out)
                k, out = k + 1, []
                print(f"{i}/{len(recs)} {time.time() - t0:.0f}s", flush=True)
    if out:
        batch._flush(run_dir, k, out)
    print(f"bitti {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else "NDX", a[1] if len(a) > 1 else "1h", int(a[2]) if len(a) > 2 else 6)
