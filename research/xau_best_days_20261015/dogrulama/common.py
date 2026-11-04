"""Ortak yükleyiciler. mekanik/, anatomi/, makro/, erken_sinyal/ klasörleri SALT-OKUNUR kullanılır (yalnız import /
okuma; hiçbir dosyaları yazılmaz). Bayrak tanımları PROTOCOL.md §2 ile birebir."""
from __future__ import annotations
import importlib.util, os, sys
import numpy as np, pandas as pd
sys.dont_write_bytecode = True
BASE = "/Users/melihcanodacioglu/Desktop/panel/research"
MK = f"{BASE}/decider_xau_tpsl_20261015/mekanik"
ANA = f"{BASE}/xau_best_days_20261015/anatomi"
MAK = f"{BASE}/xau_best_days_20261015/makro"
ERK = f"{BASE}/xau_best_days_20261015/erken_sinyal"
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
sys.path.insert(0, MK)
import run_main  # noqa: E402
from mech import prep_h1, path_sim, one_position, day_boot_p  # noqa: E402,F401
from run_main import sim_cell  # noqa: E402
from rules import events  # noqa: E402

SPREAD = 0.12
CUT = pd.Timestamp("2026-06-17", tz="UTC")
ERAS = [("2008-12", 2008, 2012), ("2013-16", 2013, 2016), ("2017-20", 2017, 2020), ("2021-26", 2021, 2026)]
# ileri dönem FOMC (2026 Fed takvimi; 14:00 ET = 18:00 UTC yaz saati) — makro calendar.csv 2026-06-17'de bitiyor
EXTRA_FOMC = ["2026-07-29 18:00:00+00:00", "2026-09-16 18:00:00+00:00"]


def _load_mod(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


mak_feat = _load_mod("mak04", f"{MAK}/04_features.py")   # add_feats, daily_gold (yalnız tanımlar; main korunuyor)


def macro_inputs():
    M = pd.read_csv(f"{MAK}/out/macro_daily.csv", index_col=0, parse_dates=True)
    cal = pd.read_csv(f"{MAK}/out/calendar.csv")
    extra = pd.DataFrame({"event": "FOMC", "date": [x[:10] for x in EXTRA_FOMC], "et": "14:00", "ts_utc": EXTRA_FOMC})
    cal = pd.concat([cal, extra], ignore_index=True)
    return M, cal


def load_d(end: str | None = None) -> pd.DataFrame:
    """run_main.load_main() — END_MAIN geçici olarak değiştirilebilir (uzatma)."""
    old = run_main.END_MAIN
    if end:
        run_main.END_MAIN = pd.Timestamp(end, tz="UTC")
    try:
        return run_main.load_main()
    finally:
        run_main.END_MAIN = old


def event_window(ent_ts: pd.Series, cal: pd.DataFrame, ev: str, hours: int = 20) -> np.ndarray:
    """07_event_windows.win ile aynı: açıklama anı ∈ [giriş, giriş+hours)."""
    t = np.sort(pd.to_datetime(cal[cal.event == ev].ts_utc, utc=True).dt.tz_localize(None).values.astype("datetime64[ns]"))
    e = pd.to_datetime(ent_ts, utc=True).dt.tz_localize(None).values.astype("datetime64[ns]")
    j = np.searchsorted(t, e); nx = t[np.clip(j, 0, len(t) - 1)]
    return (j < len(t)) & ((nx - e) < np.timedelta64(hours, "h")) & ((nx - e) >= np.timedelta64(0, "h"))


def brk_density(d: pd.DataFrame, n_bars: int = 24) -> np.ndarray:
    """S1: her bar s için [s−24, s−1] içindeki R0 olay barı sayısı (anatomi build.py xa_brk_density24 ile aynı)."""
    ev = events(d, "R0", +1)
    isev = np.zeros(len(d), bool); isev[ev.sig.to_numpy()] = True
    cs = np.concatenate([[0], np.cumsum(isev)])
    s = np.arange(len(d))
    return cs[s] - cs[np.maximum(s - n_bars, 0)]


def gprev_for(d: pd.DataFrame, ent_idx: np.ndarray) -> np.ndarray:
    """S2: makro 04_features.add_feats'teki gprev — giriş UTC gününden önceki son Duka UTC-gün kapanışı / bir önceki − 1."""
    G = mak_feat.daily_gold(d)
    ent = d.ts.to_numpy()[ent_idx]
    eday = pd.to_datetime(ent).tz_localize(None).normalize().values if pd.to_datetime(ent).tz is not None \
        else pd.to_datetime(ent).normalize().values
    gi = G.index.values; kg = np.searchsorted(gi, eday, side="left") - 1
    gc = G.values; g1 = gc[np.clip(kg, 0, None)]; g2 = gc[np.clip(kg - 1, 0, None)]
    out = g1 / g2 - 1
    out[kg < 1] = np.nan
    return out


def run_rule(d: pd.DataFrame) -> pd.DataFrame:
    """Tüm R0B_G1 olayları (R, xi, dur) + S bayrakları için ham değerler."""
    ev = events(d, "R0", +1)
    R, xi, code, hl = sim_cell(d, ev, None, 1.5, 20, +1, SPREAD)
    m = np.isfinite(R)
    e = ev[m].reset_index(drop=True)
    e["R"] = R[m]; e["xi"] = xi[m]; e["code"] = code[m]; e["dur"] = e.xi - e.ent
    e["ent_ts"] = d.ts.to_numpy()[e.ent]
    e["ent_day"] = d.ts.dt.strftime("%Y-%m-%d").to_numpy()[e.ent]
    e["week"] = d.ts.dt.tz_convert(None).dt.to_period("W").astype(str).to_numpy()[e.ent]
    dens = brk_density(d)
    e["dens24"] = dens[e.sig]
    e["gprev"] = gprev_for(d, e.ent.to_numpy())
    return e


def add_flags(e: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    e = e.copy()
    for k in (1, 2, 3):
        e[f"S1_ge{k}"] = e.dens24 >= k
    for thr, nm in ((0.0075, "075"), (0.01, "100"), (0.0125, "125")):
        e[f"S2_gt{nm}"] = e.gprev > thr
    e["S3_fomcwin"] = event_window(e.ent_ts, cal, "FOMC")
    e["S1"] = e.S1_ge2; e["S2"] = e.S2_gt100; e["S12"] = e.S1 | e.S2
    return e


def circ_shift(year: np.ndarray, rng) -> np.ndarray:
    """erken_sinyal 01_main.circ_shift ile aynı: yıl içinde dairesel kaydırma (dizi giriş sırasında)."""
    perm = np.arange(len(year))
    for y in np.unique(year):
        g = np.where(year == y)[0]
        if len(g) > 1:
            perm[g] = np.roll(g, rng.integers(1, len(g)))
    return perm
