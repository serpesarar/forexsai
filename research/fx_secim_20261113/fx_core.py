"""FX-01 ortak: veri indirme/yükleme, saat ekseni, maliyet, bootstrap. Ön kayıt: PROTOCOL.md."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
FX = DATA / "fx"
RES = HERE / "results"
RES.mkdir(exist_ok=True)
SPLIT = pd.Timestamp("2022-01-01")
SRV_MINUS_ET_H = 7
BUCKET = "research-xfer"


def _client():
    sp = importlib.util.spec_from_file_location("remote", ROOT / "scripts/remote.py")
    rm = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(rm)
    return rm._client()


def download(prefix: str = "fx") -> None:
    """Depodaki fx/ dosyalarını indir (zaten varsa ve boyutu aynıysa atla)."""
    c = _client()
    FX.mkdir(parents=True, exist_ok=True)
    for f in c.storage.from_(BUCKET).list(prefix, {"limit": 1000}):
        p = FX / f["name"]
        size = (f.get("metadata") or {}).get("size")
        if p.exists() and size and p.stat().st_size == size:
            continue
        p.write_bytes(c.storage.from_(BUCKET).download(f"{prefix}/{f['name']}"))
        print("indirildi", f["name"], flush=True)


def load(pair: str, tf: str) -> pd.DataFrame:
    """Bar tablosu: srv (sunucu), et (New York, naif), utc (naif), o,h,l,c,v,sp (puan)."""
    x = pd.read_csv(FX / f"{pair}_{tf}.csv.gz")
    x["srv"] = pd.to_datetime(x.t, unit="s")
    x["et"] = x.srv - pd.Timedelta(hours=SRV_MINUS_ET_H)
    x["utc"] = (x.et.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="shift_forward")
                .dt.tz_convert("UTC").dt.tz_localize(None))
    return x.dropna(subset=["utc"]).reset_index(drop=True)


def meta() -> dict:
    out: dict = {}
    pr = DATA / "probe.json"
    if pr.exists():
        out.update(json.loads(pr.read_text())["fx"])
    for f in sorted(DATA.glob("export_*.json")):
        for k, v in json.loads(f.read_text()).items():
            if isinstance(v, dict) and "meta" in v:
                out[k] = v["meta"]
    return out


def spread_bp(x: pd.DataFrame, point: float) -> pd.Series:
    """Bar spread'i bp; 0 olanlar o yıl × UTC saati medyanıyla doldurulur (E97 notu: devir dakikası ayrıca ele alınır)."""
    s = x.sp.astype(float) * point / x.o * 1e4
    s = s.where(x.sp > 0)
    key = [x.utc.dt.year, x.utc.dt.hour]
    fill = s.groupby(key).transform("median")
    return s.fillna(fill).fillna(s.median())


def boot_p(v: np.ndarray | pd.Series, groups: np.ndarray | None = None, n: int = 4000, seed: int = 7) -> float:
    """P(ort > 0), grup (gün/ay) kümeli bootstrap."""
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    if len(v) < 5:
        return float("nan")
    rng = np.random.default_rng(seed)
    if groups is None:
        m = np.array([rng.choice(v, len(v)).mean() for _ in range(n)])
    else:
        g = pd.Series(v).groupby(np.asarray(groups)[: len(v)]).agg(["sum", "count"])
        s, c = g["sum"].values, g["count"].values
        idx = rng.integers(0, len(g), (n, len(g)))
        m = s[idx].sum(1) / c[idx].sum(1)
    return float((m > 0).mean())


def summ(v: pd.Series, t: pd.Series | None = None) -> dict:
    """bp serisinin özeti; t verilirse KEŞİF/KÖR ve iki kronolojik yarı."""
    v = pd.Series(v, dtype=float).dropna()
    d = {"n": int(len(v)), "ort": round(v.mean(), 2) if len(v) else None,
         "t": round(v.mean() / (v.std(ddof=1) / np.sqrt(len(v))), 2) if len(v) > 2 and v.std() > 0 else None,
         "P": round(boot_p(v), 3) if len(v) >= 5 else None}
    if t is not None and len(v):
        t = pd.Series(pd.to_datetime(t)).loc[v.index] if len(t) != len(v) else pd.Series(pd.to_datetime(t).values, index=v.index)
        k, b = v[t < SPLIT], v[t >= SPLIT]
        h = len(v) // 2
        d.update({"kesif": [int(len(k)), round(k.mean(), 2) if len(k) else None],
                  "kor": [int(len(b)), round(b.mean(), 2) if len(b) else None],
                  "yari": [round(v.iloc[:h].mean(), 2), round(v.iloc[h:].mean(), 2)]})
    return d


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "indir":
        download()
