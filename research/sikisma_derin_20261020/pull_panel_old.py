"""Bot ÖNCESİ panel sinyalleri (NDX, 2026-02-01 → 06-15) — yeni bağımsız örneklem → results/panel_old.parquet."""
from __future__ import annotations

import pandas as pd

import core as C

MODELS = ["pulse1", "pulse2", "pulse3", "emel", "smc", "ml:main", "meta"]

if __name__ == "__main__":
    rows = C.data.fetch_table(C.data.get_client(), "prediction_logs", "created_at,model_type,ml_direction",
                              [("created_at", "gte", "2026-02-01"), ("created_at", "lt", "2026-06-15"),
                               ("symbol", "eq", "NDX.INDX"), ("model_type", "in_", MODELS)], "created_at")
    d = pd.DataFrame(rows)
    d["ts"] = pd.to_datetime(d.created_at, utc=True, format="ISO8601")
    d = d[d.ml_direction.isin(["BUY", "SELL"])][["ts", "model_type", "ml_direction"]]
    d.to_parquet(C.HERE / "results" / "panel_old.parquet", index=False)
    print(len(d), d.ts.min(), d.ts.max())
    print(d.groupby(["model_type", "ml_direction"]).size())
