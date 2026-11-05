"""HB-03 ortak: bar yükleme, başlık ayrıştırma, sürpriz z, icra, plasebo, bootstrap."""
from __future__ import annotations
import json, re
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
KESIF_END = pd.Timestamp("2025-01-01", tz="UTC")
DOGRULAMA_END = pd.Timestamp("2026-01-01", tz="UTC")
HORIZONS = (5, 15, 60, 240)
MIN_HIST = 12
_NUM = r"(-?\d[\d,]*\.?\d*)\s*([%KMBT]?)"
ACT = re.compile(rf"^(?:[^A-Za-z]*)(?:BREAKING:\s*)?(.+?)\s+ACTUAL\s+{_NUM}\s*\(FORECAST\s+(-|{_NUM}),\s*PREVIOUS\s+(-|-?[\d.,]+\s*[%KMBT]?)\)", re.I)
_MULT = {"": 1.0, "%": 1.0, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}

# (aile, başlık deseni, öncelik, tür). tür: infl|grow|oil|cb. Önceden sabit (PROTOCOL).
FAMILIES: tuple[tuple[str, str, int, str], ...] = (
    ("US_CORE_CPI_MOM", r"^US CORE CPI (?:MOM|MM)", 1, "infl"), ("US_CORE_CPI_YOY", r"^US CORE CPI (?:YOY|YY)", 2, "infl"),
    ("US_CPI_MOM", r"^US CPI (?:MOM|MM)", 3, "infl"), ("US_CPI_YOY", r"^US CPI (?:YOY|YY)", 4, "infl"),
    ("US_NFP", r"^US (?:NON-?FARM PAYROLLS?|NFP)$", 5, "grow"), ("US_UNEMP", r"^US UNEMPLOYMENT RATE", 6, "grow_inv"),
    ("US_CORE_PCE", r"^US CORE PCE (?:PRICE INDEX )?(?:MOM|MM|YOY|YY)", 7, "infl"), ("US_PPI", r"^US (?:CORE )?PPI (?:MOM|MM)", 8, "infl"),
    ("US_ISM_MFG", r"^US ISM MANUFACTURING PMI", 9, "grow"), ("US_ISM_SVC", r"^US ISM (?:SERVICES|NON-MANUFACTURING) PMI", 10, "grow"),
    ("US_RETAIL", r"^US RETAIL SALES (?:MOM|MM)", 11, "grow"), ("US_GDP", r"^US (?:GDP|ADVANCE GDP)", 12, "grow"),
    ("US_CLAIMS", r"^US (?:INITIAL )?JOBLESS CLAIMS", 13, "grow_inv"), ("US_ADP", r"^US ADP", 14, "grow"),
    ("FOMC_RATE", r"^US INTEREST RATE DECISION|^(?:US )?(?:FED|FOMC).*(?:RATE|FUNDS)", 0, "cb"), ("ECB_RATE", r"^ECB.*RATE", 0, "cb"),
    ("DE_CPI", r"^GERMAN CPI", 15, "infl"), ("DE_IFO", r"^GERMAN IFO", 16, "grow"), ("DE_ZEW", r"^GERMAN ZEW", 17, "grow"),
    ("EZ_CPI", r"^EUROZONE (?:CORE )?CPI", 18, "infl"),
    ("EIA_CRUDE", r"^EIA CRUDE OIL INVENTOR", 19, "oil"), ("API_CRUDE", r"^US API CRUDE", 20, "oil"),
)
_FAM = [(n, re.compile(p, re.I), o, k) for n, p, o, k in FAMILIES]


def _val(num: str | None, unit: str | None) -> float | None:
    if num is None:
        return None
    return float(num.replace(",", "")) * _MULT.get((unit or "").upper(), 1.0)


def parse_macro(text: str) -> dict | None:
    """'X ACTUAL a (FORECAST f, PREVIOUS p)' satırı; öngörü yoksa None."""
    t = text.split("| FJ")[0].replace("$MACRO", "").strip()
    m = ACT.search(t)
    if not m or m.group(4) == "-":
        return None
    name = re.sub(r"\s+", " ", m.group(1)).strip().upper()
    a, f = _val(m.group(2), m.group(3)), _val(m.group(5), m.group(6))
    if a is None or f is None:
        return None
    for fam, rx, order, kind in _FAM:
        if rx.search(name):
            return {"family": fam, "name": name, "actual": a, "forecast": f, "order": order, "kind": kind}
    return None


def load_channel(chan: str) -> pd.DataFrame:
    rows = [json.loads(x) for p in sorted(DATA.glob(f"tg_{chan}*.jsonl")) for x in p.open(encoding="utf8")]
    d = pd.DataFrame(rows).drop_duplicates("id")
    d["ts"] = pd.to_datetime(d["ts"], utc=True, format="ISO8601")
    return d.sort_values("ts").reset_index(drop=True)


UNIT = {"US_CORE_CPI_MOM": .1, "US_CORE_CPI_YOY": .1, "US_CPI_MOM": .1, "US_CPI_YOY": .1, "US_NFP": 40e3, "US_UNEMP": .1, "US_CORE_PCE": .1, "US_PPI": .1, "US_ISM_MFG": 1.0, "US_ISM_SVC": 1.0, "US_RETAIL": .3, "US_GDP": .3, "US_CLAIMS": 10e3, "US_ADP": 30e3, "FOMC_RATE": .25, "ECB_RATE": .25, "DE_CPI": .1, "DE_IFO": .5, "DE_ZEW": 3.0, "EZ_CPI": .1, "EIA_CRUDE": 2e6, "API_CRUDE": 2e6}


def macro_events() -> pd.DataFrame:
    """Sürpriz tablosu: z yalnız geçmiş sürprizlerin std'si ile (sızıntısız), ilk MIN_HIST atılır."""
    fj = load_channel("FinancialJuice")
    rows = []
    for ts, text in zip(fj["ts"], fj["text"]):
        p = parse_macro(text)
        if p:
            p["ts"] = ts
            rows.append(p)
    e = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    e["surprise"] = e["actual"] - e["forecast"]
    e["z"] = e["surprise"] / e["family"].map(UNIT)
    return e


class Bars:
    """1m bid/ask dizileri; t saniye, bar başlangıcı."""

    def __init__(self, sym: str) -> None:
        d = pd.read_parquet(DATA / f"{sym}_1m.parquet")
        self.sym = sym
        self.t = d["t"].to_numpy("int64")
        self.o, self.h, self.l, self.c = (d[k].to_numpy("float64") for k in ("open", "high", "low", "close"))
        self.ao, self.ac = d["ask_open"].to_numpy("float64"), d["ask_close"].to_numpy("float64")
        self.med_spread = float(np.median(self.ao - self.o))
        self.ret = np.r_[0.0, np.log(self.c[1:] / self.c[:-1])]

    def idx_after(self, ts: float) -> int:
        """ts'ten SONRA açılan ilk bar."""
        return int(np.searchsorted(self.t, ts, side="right"))

    def trade(self, ts: float, side: int, h_min: int, stress: bool = False) -> float | None:
        """Net bp: side=+1 buy(ask_open→bid close), −1 sell(bid open→ask close). Boşluk varsa None."""
        i = self.idx_after(ts)
        if i >= len(self.t) or self.t[i] - ts > 180:
            return None
        j = int(np.searchsorted(self.t, self.t[i] + h_min * 60, side="left")) - 1
        if j <= i or self.t[i] + h_min * 60 - self.t[j] > 600 or j + 1 >= len(self.t):
            return None
        if side > 0:
            entry, exit_ = self.ao[i], self.c[j]
        else:
            entry, exit_ = self.o[i], self.ac[j]
        if stress:
            extra = 0.5 * ((self.ao[i] - self.o[i]) + (self.ac[j] - self.c[j])) + 2 * self.med_spread
        else:
            extra = 0.0
        return float(side * (exit_ - entry) / entry * 1e4 - extra / entry * 1e4)


def trades(B: "Bars", ts: np.ndarray, side: np.ndarray, h_min: int, extra_bp: float = 0.0) -> np.ndarray:
    """B.trade'in vektör hâli; boşlukta NaN. side +1/−1, h_min dk."""
    i = np.searchsorted(B.t, ts, side="right")
    ok = i < len(B.t)
    ii = np.where(ok, i, 0)
    ok &= B.t[ii] - ts <= 180
    j = np.searchsorted(B.t, B.t[ii] + h_min * 60, side="left") - 1
    ok &= (j > ii) & (j + 1 < len(B.t))
    jj = np.where(ok, j, ii)
    ok &= (B.t[ii] + h_min * 60 - B.t[jj]) <= 600
    entry = np.where(side > 0, B.ao[ii], B.o[ii])
    exit_ = np.where(side > 0, B.c[jj], B.ac[jj])
    out = side * (exit_ - entry) / entry * 1e4 - extra_bp
    out[~ok] = np.nan
    return out


def tstat(v: np.ndarray) -> float:
    m = np.isfinite(v)
    if m.sum() < 5:
        return -9.0
    return float(np.nanmean(v) / (np.nanstd(v[m]) / np.sqrt(m.sum()) + 1e-9))


def family(B: "Bars", cells: list[dict], N: int = 2000, seed: int = 21, extra_bp: float = 0.0) -> "pd.DataFrame":
    """Her hücre {name, ts, side, h}. Aynı hafta-dakika kaydırma ile plasebo p + aile maxT p (hücre başına aynı ofset dizisi)."""
    rng = np.random.default_rng(seed)
    obs = [trades(B, c["ts"], c["side"], c["h"], extra_bp) for c in cells]
    t_obs = np.array([tstat(v) for v in obs])
    pool = {}
    def off(n):  # olay başına rastgele ±1..8 hafta
        return rng.integers(1, 9, n) * rng.choice([-1, 1], n) * 7 * 86400
    maxt, pl = np.full(N, -9.0), np.zeros((N, len(cells)))
    for k in range(N):
        for ci, c in enumerate(cells):
            v = trades(B, c["ts"] + off(len(c["ts"])), c["side"], c["h"], extra_bp)
            pl[k, ci] = np.nanmean(v) if np.isfinite(v).sum() >= 5 else np.nan
            maxt[k] = max(maxt[k], tstat(v))
    rows = []
    for ci, (c, v) in enumerate(zip(cells, obs)):
        m = np.isfinite(v); vv, tt = v[m], c["ts"][m]
        if len(vv) < 5:
            rows.append({"hücre": c["name"], "n": int(m.sum())}); continue
        o = np.argsort(tt); vs = vv[o]; h = len(vs) // 2
        st = trades(B, c["ts"], c["side"], c["h"], extra_bp + 2 * B.med_spread / np.nanmedian(B.c) * 1e4)
        rows.append({"hücre": c["name"], "n": len(vv), "ort": round(vv.mean(), 2), "med": round(float(np.median(vv)), 2), "isabet": round(float((vv > 0).mean()), 3),
                     "P": round(boot_p(vv, tt // 86400), 3), "y1": round(vs[:h].mean(), 2), "y2": round(vs[h:].mean(), 2), "stres": round(float(np.nanmean(st)), 2),
                     "plc_p": round(float(np.nanmean(pl[:, ci] >= vv.mean())), 3), "t": round(t_obs[ci], 2), "maxT_p": round(float((maxt >= t_obs[ci]).mean()), 3)})
    return pd.DataFrame(rows)


def boot_p(values: np.ndarray, days: np.ndarray, n: int = 2000, seed: int = 7) -> float:
    """Gün-blok bootstrap P(EV>0)."""
    rng = np.random.default_rng(seed)
    u, inv = np.unique(days, return_inverse=True)
    s, c = np.bincount(inv, values), np.bincount(inv)
    idx = rng.integers(0, len(u), size=(n, len(u)))
    return float(((s[idx].sum(1) / c[idx].sum(1)) > 0).mean())


def placebo_times(ts: pd.Series, bars: Bars, n: int, seed: int = 11) -> np.ndarray:
    """Her olay için aynı hafta-günü + aynı UTC dakika, ±8 hafta rastgele hafta, olay dışı: n çekiliş × len(ts) matrisi."""
    rng = np.random.default_rng(seed)
    base = ts.astype("int64").to_numpy() // 10**9
    offs = rng.integers(1, 9, size=(n, len(base))) * rng.choice([-1, 1], size=(n, len(base))) * 7 * 86400
    return base[None, :] + offs
