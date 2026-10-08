"""decider_journal → düz özellik tablosu (data/decisions.parquet). Salt-okuma."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi.data import fetch_table, get_client  # noqa: E402

TFS = ("1m", "5m", "30m", "1h", "4h")
TREND = {"yukari": 1, "yukarı": 1, "asagi": -1, "aşağı": -1}
SELECT = ("id,ts,symbol,decision,raw->trade,raw->path,raw->cf_path,raw->forensics,raw->dirs_live,raw->vix,"
          "raw->pnl_r,raw->cf_pnl_r,raw->outcome,raw->cf_outcome,raw->outcome_at,raw->model,raw->batch_eval,raw->counterfactual")


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def flatten(r: dict) -> dict | None:
    import json
    d = r.get("decision")
    d = json.loads(d) if isinstance(d, str) else (d or {})
    act = d.get("action")
    reason = str(d.get("reason", ""))
    if reason.startswith(("claude exit", "claude spawn")) or r.get("batch_eval"):
        return None
    tr = r.get("trade") or {}
    if act == "OPEN":
        s_dir, pnl, path, out = d.get("direction"), _f(r.get("pnl_r")), r.get("path") or {}, r.get("outcome")
    else:
        cf = r.get("counterfactual") or {}
        s_dir = (cf.get("dir") or cf.get("direction")) if isinstance(cf, dict) else None
        tr = cf if isinstance(cf, dict) else tr
        pnl, path, out = _f(r.get("cf_pnl_r")), r.get("cf_path") or {}, r.get("cf_outcome")
    if s_dir not in ("BUY", "SELL") or not np.isfinite(pnl):
        return None
    s = 1 if s_dir == "BUY" else -1
    rec = {"id": r["id"], "ts": r["ts"], "symbol": r["symbol"], "act": act, "dir": s_dir, "pnl_r": pnl,
           "outcome": out, "outcome_at": r.get("outcome_at"), "model": r.get("model"),
           "size_factor": _f(d.get("size_factor")), "rr": _f(tr.get("rr")), "spread_atr": _f(tr.get("spread_atr")),
           "mae_r": _f(path.get("mae_r")), "mfe_r": _f(path.get("mfe_r")), "tp_progress": _f(path.get("tp_progress")),
           "sl_recovered_entry": _f(path.get("sl_recovered_entry")), "bars_to_outcome": _f(path.get("bars_to_outcome"))}
    rec.update(_forensics(r.get("forensics") or {}, s))
    live = (r.get("dirs_live") or {}).get(s_dir) or (tr.get("live") if isinstance(tr, dict) else None) or {}
    rec.update({"rev_chan": _f(live.get("rev_chan")), "rev_vwap": _f(live.get("rev_vwap")),
                "gate_fired": float(bool(live.get("gate_fired"))) if live else np.nan, "session": live.get("session")})
    vix = r.get("vix") or {}
    fav = vix.get("favored_ndx") if isinstance(vix, dict) else None
    rec["vix_favors_dir"] = float(fav == s_dir) if fav in ("BUY", "SELL") else np.nan
    return rec


def _forensics(f: dict, s: int) -> dict:
    out, agree = {}, 0
    tfs = f.get("tfs") or {}
    for tf in TFS:
        x = tfs.get(tf) or {}
        tr = TREND.get(str(x.get("trend", "")).lower(), 0) * s
        agree += tr > 0
        sr = x.get("sr") or {}
        opp, sup = (sr.get("res"), sr.get("sup")) if s > 0 else (sr.get("sup"), sr.get("res"))
        out.update({f"{tf}_trend": float(tr) if x else np.nan, f"{tf}_adx": _f(x.get("adx")),
                    f"{tf}_vwap_z": s * _f(x.get("vwap_z")), f"{tf}_channel_z": s * _f(x.get("channel_z")),
                    f"{tf}_vol_ratio": _f(x.get("vol_ratio")),
                    f"{tf}_opp_dist": _f((opp or {}).get("dist_atr")), f"{tf}_opp_touch": _f((opp or {}).get("touches")),
                    f"{tf}_sup_dist": _f((sup or {}).get("dist_atr"))})
    out["mtf_agree"] = float(agree) if tfs else np.nan
    m = f.get("macro") or {}
    out["vix"], out["dxy"] = _f(m.get("vix")), _f(m.get("dxy"))
    return out


def main() -> None:
    (HERE / "data").mkdir(exist_ok=True)
    rows = fetch_table(get_client(), "decider_journal", SELECT, [], "ts")
    print("ham satır:", len(rows))
    df = pd.DataFrame([x for x in (flatten(r) for r in rows) if x])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["outcome_at"] = pd.to_datetime(df["outcome_at"], utc=True, errors="coerce")
    df["hour"] = df["ts"].dt.hour.astype(float)
    df["dow"] = df["ts"].dt.dayofweek.astype(float)
    df.to_parquet(HERE / "data" / "decisions.parquet", index=False)
    print(df.groupby(["symbol", "act"]).size())


if __name__ == "__main__":
    main()
