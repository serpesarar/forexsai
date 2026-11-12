"""`yeni deneme/xau_r0b_live.py` (CANLI kural) ↔ araştırma R0B_G1 + S2 (tek pozisyon) uçtan uca parite.

Duka H1 (2008-01 → 2026-06) bar bar, canlıdaki gibi 200 barlık pencere: her bar kapanışında önce açık pozisyon (stop → çıkış
nedeni, xau_r0b_live.exit_reason), sonra xau_r0b_live.evaluate. Giriş sonraki bar açılışı + 0,12 (araştırma kuralı), sonraki bar
> 3 saat sonraysa giriş yok (canlıda bayat tick). Hedef: araştırma c5_practical "ATLA S2_gt100" n 3.259, ort +0,109R.
Çalıştır: .venv/bin/python research/xau_best_days_20261015/golge_parite/live_parity.py
"""
from __future__ import annotations
import json, os, sys
sys.dont_write_bytecode = True
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "yeni deneme"))
import xau_r0b_live as xl  # noqa: E402

SPREAD, WIN = 0.12, 200


def main() -> None:
    d = pd.read_parquet(os.path.join(ROOT, "research/decider_xau_tpsl_20261015/mekanik/data/duka_h1.parquet"))
    t = (pd.to_datetime(d.ts).astype("int64") // 10 ** 9).to_numpy()
    o, h, l, c = (d[k].to_numpy(float) for k in "ohlc")
    bars = [{"t": int(t[k]), "open": o[k], "high": h[k], "low": l[k], "close": c[k]} for k in range(len(d))]
    pos, out = None, []
    for k in range(WIN, len(bars) - 1):
        b = bars[k]; now = b["t"] + 3600
        if pos is not None and b["t"] >= pos["entry_bar_t"]:
            px, how = None, None
            if b["low"] <= pos["stop"]:
                px, how = (pos["stop"] if b["t"] == pos["entry_bar_t"] else min(b["open"], pos["stop"])), "stop"
            else:
                why = xl.exit_reason(bars[k - 40:k + 1], pos["entry_bar_t"], now)
                if why:
                    px, how = b["close"], why.split(" ")[0]
            if px is not None:
                out.append({"sig_t": pos["sig_t"], "R": (px - pos["entry"]) / pos["sd"], "how": how})
                pos = None
        if pos is None:
            sig, _ = xl.evaluate(bars[k - WIN + 1:k + 1])
            if sig and bars[k + 1]["t"] - b["t"] <= xl.GAP_S:
                e = bars[k + 1]["open"] + SPREAD
                pos = {"sig_t": b["t"], "entry_bar_t": bars[k + 1]["t"], "entry": e, "sd": sig["stop_dist"], "stop": e - sig["stop_dist"]}
    r = pd.DataFrame(out); R = r.R.to_numpy()
    yrs = pd.to_datetime(r.sig_t, unit="s").dt.year
    res = {"n": int(len(R)), "ort_R": round(float(R.mean()), 4), "isabet": round(float((R > 0).mean()), 4),
           "toplam_R": round(float(R.sum()), 1), "artı_yil": f"{int((r.groupby(yrs).R.sum() > 0).sum())}/{yrs.nunique()}",
           "cikis": r.how.value_counts().to_dict(), "arastirma_hedef": {"n": 3259, "ort_R": 0.1095, "isabet": 0.363, "toplam_R": 356.8}}
    print(json.dumps(res, indent=1, ensure_ascii=False))
    with open(os.path.join(os.path.dirname(__file__), "live_parity.json"), "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
