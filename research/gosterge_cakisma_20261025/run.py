"""GÇM çalıştırıcı. Kullanım: python run.py NDX [1h,4h] | python run.py ALL"""
import sys
import time

import config as C
import miner
import model


def main(argv: list[str]) -> None:
    syms = list(C.SOURCES) if argv[0] == "ALL" else [argv[0]]
    for sym in syms:
        tfs = argv[1].split(",") if len(argv) > 1 else list(C.SOURCES[sym])
        for tf in tfs:
            t = time.time()
            print(f"== {sym} {tf}", flush=True)
            miner.run_cell(sym, tf)
            if "--no-model" not in argv:
                model.run_cell(sym, tf)
            print(f"== {sym} {tf} bitti ({time.time() - t:.0f}s)", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
