"""GER40 broker M30 yükleyici: sunucu saati (New York + 7) → UTC → Berlin. Eksen denetimi: Xetra 09:00 açılış hacim tepesi."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path("yeni deneme").resolve()))
from broker_time import rule_offset_sec

SRC = Path("research/c1_turev_20261105/data/mt5")
BER = "Europe/Berlin"

def load(sym: str = "GER40", tf: str = "M30") -> pd.DataFrame:
    d = pd.read_csv(SRC / f"{sym}_{tf}.csv.gz")
    off = np.array([rule_offset_sec(int(t)) for t in d["t"]])
    d["utc"] = pd.to_datetime(d["t"] - off, unit="s", utc=True)
    d["ber"] = d["utc"].dt.tz_convert(BER)
    d = d[d["utc"] >= "2018-06-01"].reset_index(drop=True)
    return d

def axis_audit(d: pd.DataFrame) -> pd.DataFrame:
    """Her ay: en yüksek ortalama hacimli Berlin yarım saati (beklenen 09:00 Xetra açılışı veya 15:30 ABD açılışı)."""
    x = d.assign(m=d["ber"].dt.strftime("%Y-%m"), hm=d["ber"].dt.strftime("%H:%M"))
    g = x.groupby(["m", "hm"])["v"].mean().reset_index()
    top = g.sort_values("v").groupby("m").tail(3).groupby("m")["hm"].apply(lambda s: ",".join(sorted(s)))
    return top

if __name__ == "__main__":
    d = load()
    print(d["ber"].min(), d["ber"].max(), len(d))
    a = axis_audit(d)
    ok = a.str.contains("09:00")
    print("09:00 en yoğun 3 yarım saat içinde olan ay:", ok.sum(), "/", len(ok))
    print(a[~ok].to_string())
