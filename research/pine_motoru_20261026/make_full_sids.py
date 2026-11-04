"""run_full.py için script listesi: recent koşusunda o sembolde çalışıp BENZERSİZ durum katan scriptler, popülerlik sırasıyla.

Kullanım: python make_full_sids.py NDX,DAX,XAU,USOIL   → data/full_sids_<sym>.txt
"""
from __future__ import annotations

import glob
import gzip
import hashlib
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import eval_scripts as EV  # noqa: E402


def make(syms: list[str]) -> None:
    excl = EV.lookahead_sids()
    recs: dict[str, list] = {s: [] for s in syms}
    for p in sorted(glob.glob(str(HERE / "data/runs/recent/part_*.pkl.gz"))):
        for r in pickle.load(gzip.open(p)):
            if r["sid"] in excl:
                continue
            for s in syms:
                v = r["per_sym"].get(s)
                if v and v["status"] == "ok" and v["states"]:
                    hs = [hashlib.blake2b(b, digest_size=12).digest() for b in v["states"].values()]
                    recs[s].append((r.get("boosts") or 0, r["sid"], v["seconds"] or 0, hs))
    for s in syms:
        rs = sorted(recs[s], key=lambda x: -x[0])
        seen, keep, t_keep = set(), [], 0.0
        for _, sid, sec, hs in rs:
            new = [h for h in hs if h not in seen]
            if new:
                keep.append(sid)
                t_keep += sec
                seen.update(new)
        (HERE / f"data/full_sids_{s.lower()}.txt").write_text("\n".join(keep))
        print(f"{s}: ok {len(rs)}, benzersiz {len(keep)}, recent süre {t_keep:.0f}s")


if __name__ == "__main__":
    make(sys.argv[1].split(",") if len(sys.argv) > 1 else ["DAX", "XAU", "USOIL"])
