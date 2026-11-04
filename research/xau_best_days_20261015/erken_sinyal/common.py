"""Ortak yükleyici: mekanik/ SALT-OKUNUR import; load_main ile aynı kesim + hacim sütunu."""
import os, sys
import numpy as np, pandas as pd
sys.dont_write_bytecode = True
MK = "/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik"
sys.path.insert(0, MK)
from mech import prep_h1, path_sim, one_position, day_boot_p  # noqa
from run_main import sim_cell  # noqa
from rules import events, GEOM  # noqa
END_MAIN = pd.Timestamp("2026-06-17", tz="UTC")
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def raw_duka(end=END_MAIN) -> pd.DataFrame:
    d = pd.read_parquet(os.path.join(MK, "data", "duka_h1.parquet"))
    d["ts"] = pd.to_datetime(d.ts, utc=True)
    return d[d.ts < end][["ts", "o", "h", "l", "c", "spr", "v"]]


def load_d(end=END_MAIN) -> pd.DataFrame:
    return prep_h1(raw_duka(end))
