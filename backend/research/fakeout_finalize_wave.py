"""Dalga-verdikt (K=2) modelini üretime kilitle — fakeout_wave_lab kazananı.

OOS (yarışı-açık popülasyon, taban ~%52): SAHTE çağrısı %71.4 (n=42),
GERÇEK çağrısı %73.5 (n=49). Deploy edilen artefakt test edilenin aynısı.
Çıktı: models/model_fakeout_ndx_5m_wave.joblib + fakeout_rules.json.detector_wave
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fakeout_miner as fm  # noqa: E402
import fakeout_lab as lab  # noqa: E402
import fakeout_wave_lab as wl  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
K = 2
FEATS = fm.FEATURES + lab.STAGE2_COLS + wl.WAVE_COLS


def main(symbol: str = "NDX.INDX", TP: float = 1.0, SL: float = 1.0) -> None:
    base_name = "ndx" if symbol == "NDX.INDX" else symbol.split(".")[0].lower()
    MODEL_PATH = MODELS_DIR / f"model_fakeout_{base_name}_5m_wave.joblib"
    suffix = "" if symbol == "NDX.INDX" else f"_{symbol.split('.')[0]}"
    wl.TP, wl.SL = TP, SL
    data = lab.assemble(symbol)
    df = fm.add_indicators(data["frames"]["5m"])
    ev = fm.detect_events(df, data["df1"], tp_atr=TP, sl_atr=SL,
                          horizon_bars=wl.HORIZON, bar_minutes=wl.BAR_MIN)
    ev = lab.add_stage2(ev, df).dropna(subset=["is_fake"]).reset_index(drop=True)
    alive = wl.resolution_offsets(ev, data["df1"]) > K * wl.BAR_MIN
    evK = wl.wave_features(ev[alive].reset_index(drop=True), df, K)
    print(f"[wave-finalize] olay={len(ev)}, K={K} yarışı-açık={len(evK)}")

    train, val, test = lab._split3_purged(evK, wl.HORIZON, wl.BAR_MIN)
    med = train[FEATS].median(numeric_only=True)
    model = lab._fit_lgbm(train[FEATS].fillna(med), train["is_fake"].values)
    p_va = model.predict_proba(val[FEATS].fillna(med))[:, 1]
    p_te = model.predict_proba(test[FEATS].fillna(med))[:, 1]
    y_va, y_te = val["is_fake"].values, test["is_fake"].values
    thr_f = lab._pick_threshold(p_va, y_va, "fake")
    thr_g = lab._pick_threshold(p_va, y_va, "genuine")
    assert thr_f is not None and thr_g is not None

    def _side(m, pos):
        n = int(m.sum())
        prec = ((y_te[m] == (1 if pos else 0)).mean() * 100) if n else 0.0
        return {"test_n": n, "coverage": round(n / len(y_te) * 100, 1),
                "precision": round(prec, 1)}

    oos = {"fake_call": _side(p_te >= thr_f, True),
           "genuine_call": _side(p_te <= thr_g, False),
           "test_n": len(y_te), "base_fake_test": round(y_te.mean() * 100, 1)}
    print("  OOS:", json.dumps(oos, ensure_ascii=False))
    assert oos["fake_call"]["precision"] >= 70 and oos["genuine_call"]["precision"] >= 70

    joblib.dump({"model": model, "features": FEATS, "medians": med.to_dict(),
                 "config": {"tf": "5m", "symbol": symbol, "K": K, "tp_atr": TP, "sl_atr": SL,
                            "mode": "wave_verdict_k2"}}, MODEL_PATH)
    rules_path = DATA_DIR / f"fakeout_rules{suffix}.json"
    rules = json.loads(rules_path.read_text())
    rules["detector_wave"] = {
        "model_file": MODEL_PATH.name, "K": K, "features": FEATS,
        "thresholds": {"fake": round(float(thr_f), 4), "genuine": round(float(thr_g), 4)},
        "oos": oos, "generated_at": pd.Timestamp.utcnow().isoformat(),
        "note": ("Aşama-2: kırılımdan K=2 bar sonra, ±1ATR yarışı HÂLÂ AÇIKSA "
                 "dalga-yapısı özellikleriyle karar (kullanıcı dalga hipotezi)."),
    }
    rules_path.write_text(
        json.dumps(rules, indent=2, ensure_ascii=False, default=str))
    print(f"  yazıldı: {MODEL_PATH.name} + detector_wave bölümü")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="NDX.INDX")
    ap.add_argument("--tp", type=float, default=1.0)
    ap.add_argument("--sl", type=float, default=1.0)
    a = ap.parse_args()
    main(symbol=a.symbol, TP=a.tp, SL=a.sl)
