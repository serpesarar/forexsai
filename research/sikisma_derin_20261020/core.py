"""Sıkışma araştırması — ortak çekirdek: 1m özellikleri (A1–A9), simülasyon, istatistik. Bkz. PROTOCOL.md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import data  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402
from scripts.islem_otopsi.placebo import simulate  # noqa: E402

RATIO_FEATS = ("atr_14_100", "atr_5_60", "atr_30_240", "rv_14_100", "atr14_seas", "vol_14_100")
RATIO_TH = (0.8, 0.9, 1.0, 1.1)
QUANT_FEATS = ("rng15_atr100", "bbw5_pct")
QUANT_TH = (0.2, 0.3, 0.4)
BIN_FEATS = ("ttm_sqz",)
ALL_FEATS = RATIO_FEATS + QUANT_FEATS + BIN_FEATS
STALE_MIN = 10
SEAS_DAYS = 20
RR, NDX_RISK_FRAC = 0.73, 0.00373
SPREAD = {"NDX.INDX": 1.5, "GDAXI.INDX": 1.5, "USOIL.FOREX": 0.03, "XAUUSD": 0.25}
SL_FRAC = {"NDX.INDX": NDX_RISK_FRAC}            # diğer semboller: bot medyanından (runner hesaplar)
N_BOOT, N_PLAC = 1000, 1000
RNG = np.random.default_rng(20261020)


# ── çubuklar ─────────────────────────────────────────────────────────────────

def bars_snapshots(sym: str, start: str) -> pd.DataFrame:
    raw = data.load_bars_raw(sym, pd.Timestamp(start, tz="UTC"), data.utc_now())
    return data.normalize_snapshot_clock(raw)


def bars_ndx_long() -> pd.DataFrame:
    raw = pd.read_parquet(ROOT / "research" / "ndx_gate_forge" / "data" / "bars_1m_all.parquet")
    return raw.set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float).sort_index()


# ── özellikler: satır i = bar i KAPANDIĞINDA bilinen değer ───────────────────

def _five_min(df: pd.DataFrame) -> pd.DataFrame:
    g = df.resample("5min", label="left", closed="left")
    b = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(),
                      "close": g.close.last()}).dropna()
    c = b.close
    sma, sd = c.rolling(20).mean(), c.rolling(20).std()
    bbw = 4 * sd / sma
    pc = c.shift()
    tr = np.maximum.reduce([b.high - b.low, (b.high - pc).abs(), (b.low - pc).abs()])
    atr20 = pd.Series(tr, index=b.index).rolling(20).mean()
    ema = c.ewm(span=20, adjust=False).mean()
    ttm = ((sma + 2 * sd) < (ema + 1.5 * atr20)) & ((sma - 2 * sd) > (ema - 1.5 * atr20))
    pct = bbw.rolling(288, min_periods=100).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    out = pd.DataFrame({"bbw5_pct": pct, "ttm_sqz": ttm.astype(float).where(atr20.notna())})
    out.index = out.index + pd.Timedelta(minutes=5)         # bilinme anı = 5m bar sonu
    return out


def _seasonal(atr14: pd.Series) -> pd.Series:
    df = pd.DataFrame({"a": atr14})
    df["date"] = df.index.normalize()
    df["mod"] = df.index.hour * 60 + df.index.minute
    piv = df.pivot_table(index="date", columns="mod", values="a", aggfunc="last")
    med = piv.rolling(SEAS_DAYS, min_periods=8).median().shift(1)
    m = med.stack().rename("m").reset_index()
    j = df.reset_index().merge(m, on=["date", "mod"], how="left").set_index(df.index.name or "index")
    return pd.Series(j["a"].to_numpy() / j["m"].to_numpy(), index=atr14.index)


def compute_feats(df: pd.DataFrame) -> pd.DataFrame:
    h, l, c, v = df.high, df.low, df.close, df.volume
    pc = c.shift()
    tr = pd.Series(np.maximum.reduce([h - l, (h - pc).abs(), (l - pc).abs()]), index=df.index)
    a = {n: tr.rolling(n).mean() for n in (5, 14, 30, 60, 100, 240)}
    r = np.log(c).diff()
    f = pd.DataFrame(index=df.index)
    f["atr_14_100"] = a[14] / a[100]
    f["atr_5_60"] = a[5] / a[60]
    f["atr_30_240"] = a[30] / a[240]
    f["rv_14_100"] = r.rolling(14).std() / r.rolling(100).std()
    f["rng15_atr100"] = (h.rolling(15).max() - l.rolling(15).min()) / a[100]
    f["atr14_seas"] = _seasonal(a[14])
    f["vol_14_100"] = v.rolling(14).mean() / v.rolling(100).mean()
    f.index = f.index + pd.Timedelta(minutes=1)              # bilinme anı = 1m bar sonu
    f5 = _five_min(df)
    f = pd.merge_asof(f.sort_index(), f5.sort_index(), left_index=True, right_index=True, direction="backward")
    f["_known"] = f.index
    return f.replace([np.inf, -np.inf], np.nan)


def feats_at(F: pd.DataFrame, ts: pd.Series) -> pd.DataFrame:
    """Karar anı t için t'den ÖNCE/AN bilinen son satır (bayatsa NaN)."""
    q = pd.DataFrame({"t": pd.to_datetime(pd.Series(ts).reset_index(drop=True), utc=True)}).sort_values("t").reset_index()
    j = pd.merge_asof(q, F.reset_index(drop=True).sort_values("_known"), left_on="t", right_on="_known",
                      direction="backward")
    stale = (j.t - j._known) > pd.Timedelta(minutes=STALE_MIN)
    j.loc[stale, list(ALL_FEATS)] = np.nan
    return j.sort_values("index").set_index("index")[list(ALL_FEATS)]


# ── simülasyon ───────────────────────────────────────────────────────────────

def sim_events(sb: SymbolBars, ev: pd.DataFrame, risk_frac: float, spread: float) -> np.ndarray:
    """ev: t, s (+1/−1). Giriş = t'den sonraki ilk 1m açılış (+spread BUY)."""
    idx = sb.m1.index
    out = np.full(len(ev), np.nan)
    for k, (t, s) in enumerate(zip(pd.to_datetime(ev.t, utc=True), ev.s)):
        j = idx.searchsorted(t, side="left")
        if j >= idx.size - 30 or (idx[j] - t) > pd.Timedelta(minutes=5):
            continue
        e = float(sb.a["open"][j]) + (spread if s > 0 else 0.0)
        risk = e * risk_frac
        R, kk, _ = simulate(sb, int(s), e, j, risk, risk * RR, spread)
        out[k] = R if kk >= 0 else np.nan
    return out


# ── istatistik ───────────────────────────────────────────────────────────────

def rules() -> list[tuple[str, str, float, str]]:
    """(ad, özellik, eşik, tip) — tip: lt (özellik < eşik → engel), q (piyasa kantili), eq1."""
    out = [(f"{f}<{t:g}", f, t, "lt") for f in RATIO_FEATS for t in RATIO_TH]
    out += [(f"{f}<q{int(q * 100)}", f, q, "q") for f in QUANT_FEATS for q in QUANT_TH]
    out += [("ttm_sqz=1", "ttm_sqz", 1.0, "eq1")]
    return out


def block_mask(d: pd.DataFrame, rule: tuple, qref: dict) -> np.ndarray:
    _, f, th, typ = rule
    x = d[f].to_numpy(float)
    if typ == "lt":
        return x < th
    if typ == "q":
        return x < (th if f == "bbw5_pct" else qref[f][th])
    return x == 1.0


def day_ids(t: pd.Series) -> np.ndarray:
    return pd.to_datetime(t, utc=True).dt.tz_convert("America/New_York").dt.date.astype(str).to_numpy()


def boot_saved(R: np.ndarray, blk: np.ndarray, days: np.ndarray) -> float:
    """P(kurtarılan R > 0), gün-blok bootstrap."""
    ud, inv = np.unique(days, return_inverse=True)
    s = np.bincount(inv, weights=np.where(blk, -R, 0.0), minlength=ud.size)
    picks = RNG.integers(0, ud.size, (N_BOOT, ud.size))
    return float((s[picks].sum(axis=1) > 0).mean())


def hour_placebo(R: np.ndarray, blk: np.ndarray, hours: np.ndarray) -> float:
    """Aynı UTC saatinden aynı sayıda rastgele olay engellense kurtarılan R; gerçek kaçıncı yüzdelik."""
    real = -R[blk].sum()
    need = {h: int((blk & (hours == h)).sum()) for h in np.unique(hours[blk])}
    pools = {h: np.flatnonzero(hours == h) for h in need}
    sims = np.empty(N_PLAC)
    for k in range(N_PLAC):
        tot = 0.0
        for h, n in need.items():
            tot += -R[RNG.choice(pools[h], n, replace=False)].sum()
        sims[k] = tot
    return float((sims < real).mean())


def quarters(R: np.ndarray, blk: np.ndarray) -> list[float]:
    q = np.array_split(np.arange(R.size), 4)
    return [float(-R[i][blk[i]].sum()) for i in q]


def evaluate(d: pd.DataFrame, qref: dict, label: str, full: bool = True) -> pd.DataFrame:
    """d: t, R, özellikler (zaman sıralı). Her kural için bir satır."""
    d = d[np.isfinite(d.R)].sort_values("t").reset_index(drop=True)
    R = d.R.to_numpy(float)
    days, hours = day_ids(d.t), pd.to_datetime(d.t, utc=True).dt.hour.to_numpy()
    rows = []
    for rule in rules():
        blk = block_mask(d, rule, qref) & np.isfinite(d[rule[1]].to_numpy(float))
        nb = int(blk.sum())
        if nb < 5 or nb > R.size - 5:
            continue
        qs = quarters(R, blk)
        row = {"kaynak": label, "kural": rule[0], "n": R.size, "engel": nb,
               "ortR_engel": R[blk].mean(), "ortR_kalan": R[~blk].mean(), "kurt_R": -R[blk].sum(),
               "Ç+": sum(x >= 0 for x in qs), "çeyrekler": "/".join(f"{x:+.1f}" for x in qs)}
        if full:
            row["P(kurt>0)"] = boot_saved(R, blk, days)
            row["saat_plasebo"] = hour_placebo(R, blk, hours)
        rows.append(row)
    return pd.DataFrame(rows)


def max_stat(d: pd.DataFrame, qref: dict, n_shift: int = 1000) -> tuple[float, np.ndarray]:
    """Tüm kurallar içinde en büyük kurtarılan R; boş = R dizisini dairesel kaydır."""
    d = d[np.isfinite(d.R)].sort_values("t").reset_index(drop=True)
    masks = []
    for rule in rules():
        m = block_mask(d, rule, qref) & np.isfinite(d[rule[1]].to_numpy(float))
        if 5 <= m.sum() <= len(d) - 5:
            masks.append(m)
    M = np.array(masks, float)
    R = d.R.to_numpy(float)
    obs = float((-(M @ R)).max())
    shifts = RNG.integers(10, R.size - 10, n_shift)
    null = np.array([(-(M @ np.roll(R, int(s)))).max() for s in shifts])
    return obs, null


def md(df: pd.DataFrame, floatfmt: str = "{:+.3f}") -> str:
    def f(v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else floatfmt.format(v)
        return str(v)
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    return "\n".join([head, sep] + ["| " + " | ".join(f(v) for v in r) + " |" for r in df.itertuples(index=False)])
