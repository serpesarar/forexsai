"""NDX 1m: üç Dukascopy parçasını `data/NDX_1m.parquet` şemasına birleştirir (t, open.., ask_open, ask_close, src)."""
import pandas as pd
from pathlib import Path
R = Path(__file__).resolve().parents[1]
a = pd.read_parquet(R / "ndx_seans_tasima_20261103/denetim/data/duka24.parquet")
b = pd.read_parquet(R / "ndx_gate_forge/data/duka_1m_2025.parquet")
c = pd.read_parquet(R / "ndx_seans_tasima_20261103/denetim/data/duka26.parquet")
for x in (a, c):
    x.rename(columns={"ao": "ask_open", "ac": "ask_close"}, inplace=True)
a["src"], b["src"], c["src"] = "duka24_bid", "duka25_ba", "duka26_bid"
k = ["t", "open", "high", "low", "close", "ask_open", "ask_close", "src"]
d = pd.concat([a[k], b[k], c[k]]).drop_duplicates("t").sort_values("t").reset_index(drop=True)
d["ts"] = pd.to_datetime(d.t, unit="s", utc=True)
d.to_parquet(Path(__file__).parent / "data/NDX_1m.parquet", index=False)
print(d.groupby("src").agg(n=("t", "size"), bas=("ts", "min"), son=("ts", "max")))
print("spread medyan", (d.ask_open - d.open).groupby(d.src).median().to_dict())
print("en büyük boşluk gün", d.t.diff().nlargest(6).div(86400).round(1).tolist())
