"""İndirilen kaynakları oku (indirici hâlâ yazıyorsa yarım kalan son bloğu tolere eder)."""
import gzip
import json
from pathlib import Path

SRC = Path(__file__).resolve().parent / "data/src/sources.jsonl.gz"


def iter_sources(only_ok: bool = True, limit: int | None = None):
    n = 0
    try:
        with gzip.open(SRC, "rt") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    break
                if only_ok and not r.get("ok"):
                    continue
                yield r
                n += 1
                if limit and n >= limit:
                    return
    except (EOFError, OSError):
        return
