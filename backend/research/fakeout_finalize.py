"""
Fakeout Finalize — lab kazananını üretim dedektörüne kilitle.

Seçilen konfig (fakeout_lab v2, 2026-07-16): NDX 5m (1m-genişletilmiş),
tp=1.0×ATR / sl=1.0×ATR (hedef geometrisi DEĞİŞMEDİ), LightGBM,
karar modu = delayed+1bar (kırılımdan sonraki bar kapanınca).

OOS test (purge'lü, n=428): SAHTE çağrısı %70.0 kesinlik / %50.7 kapsam,
GERÇEK çağrısı %83.1 kesinlik / %34.6 kapsam. Eşikler VAL'de seçildi.

DÜRÜSTLÜK: deploy edilen model, test'te DOĞRULANAN artefaktın TA KENDİSİDİR
(train %55'te eğitilmiş model + val'de seçilmiş eşikler) — "sonradan tüm
veriyle yeniden eğit" YAPILMAZ (o artefakt test edilmemiş olurdu).

Çıktılar:
  - backend/models/model_fakeout_ndx_5m.joblib  (model + feature listesi + medyanlar)
  - fakeout_rules.json'a "detector" bölümü (eşikler + OOS metrikleri)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fakeout_miner as fm  # noqa: E402
import fakeout_lab as lab  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


HORIZON, BAR_MIN = 72, 5
FEATURES = fm.FEATURES + lab.STAGE2_COLS


def main(symbol: str = "NDX.INDX", TP: float = 1.0, SL: float = 1.0) -> None:
    base_name = "ndx" if symbol == "NDX.INDX" else symbol.split(".")[0].lower()
    MODEL_PATH = MODELS_DIR / f"model_fakeout_{base_name}_5m.joblib"
    suffix = "" if symbol == "NDX.INDX" else f"_{symbol.split('.')[0]}"
    data = lab.assemble(symbol)
    df = fm.add_indicators(data["frames"]["5m"])
    print(f"[finalize] {symbol} olay tespiti (5m, tp{TP}/sl{SL})...", flush=True)
    ev = fm.detect_events(df, data["df1"], tp_atr=TP, sl_atr=SL,
                          horizon_bars=HORIZON, bar_minutes=BAR_MIN)
    ev = lab.add_stage2(ev, df).dropna(subset=["is_fake"]).reset_index(drop=True)
    train, val, test = lab._split3_purged(ev, HORIZON, BAR_MIN)
    print(f"  olay={len(ev)} (tr={len(train)}, va={len(val)}, te={len(test)})")

    med = train[FEATURES].median(numeric_only=True)
    X_tr = train[FEATURES].fillna(med)
    y_tr = train["is_fake"].values
    model = lab._fit_lgbm(X_tr, y_tr)

    p_va = model.predict_proba(val[FEATURES].fillna(med))[:, 1]
    p_te = model.predict_proba(test[FEATURES].fillna(med))[:, 1]
    y_va, y_te = val["is_fake"].values, test["is_fake"].values

    thr_fake = lab._pick_threshold(p_va, y_va, "fake")
    thr_gen = lab._pick_threshold(p_va, y_va, "genuine")
    # Fallback (USOIL vakası): val'de kesinlik-hedefli eşik yoksa VAL KANTİLİ
    # kullan (sabit %20 kapsam/side) — test bilgisi sızmaz; aşağıdaki %70/%70
    # assert'i yine de korur (geçemezse deploy iptal).
    thr_mode = "val_precision_target"
    if thr_fake is None or thr_gen is None:
        thr_fake = float(np.quantile(p_va, 0.80)) if thr_fake is None else thr_fake
        thr_gen = float(np.quantile(p_va, 0.20)) if thr_gen is None else thr_gen
        thr_mode = "val_quantile_fallback"
        print(f"  eşik fallback: val kantili (%20 kapsam/side) — {thr_mode}")

    def _side(m, positive):
        n = int(m.sum())
        prec = ((y_te[m] == (1 if positive else 0)).mean() * 100) if n else 0.0
        return {"test_n": n, "coverage": round(n / len(y_te) * 100, 1),
                "precision": round(prec, 1)}

    m_fake = p_te >= thr_fake
    m_gen = p_te <= thr_gen
    metrics = {"fake_call": _side(m_fake, True), "genuine_call": _side(m_gen, False),
               "test_n": len(y_te), "base_fake_test": round(y_te.mean() * 100, 1)}
    print("  OOS:", json.dumps(metrics, ensure_ascii=False))
    assert metrics["fake_call"]["precision"] >= 70 and metrics["genuine_call"]["precision"] >= 70, \
        "%70/%70 sağlanamadı — deploy iptal"

    # Feature importances (rapor için top-10)
    try:
        imp = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])[:10]
        imp = [[f, int(v)] for f, v in imp]
    except Exception:
        imp = []

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES,
                 "medians": med.to_dict(), "label": "is_fake(1)=sahte",
                 "config": {"tf": "5m", "symbol": symbol, "tp_atr": TP, "sl_atr": SL,
                            "horizon_bars": HORIZON, "mode": "delayed_1bar"}},
                MODEL_PATH)
    print(f"  model yazıldı: {MODEL_PATH}")

    rules_path = DATA_DIR / f"fakeout_rules{suffix}.json"
    payload = json.loads(rules_path.read_text())
    payload["detector"] = {
        "model_file": MODEL_PATH.name,
        "mode": "delayed_1bar",
        "tp_atr": TP, "sl_atr": SL,
        "features": FEATURES,
        "thresholds": {"fake": round(float(thr_fake), 4),
                       "genuine": round(float(thr_gen), 4)},
        "threshold_mode": thr_mode,
        "oos": metrics,
        "top_features": imp,
        "trained_events": len(train),
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "note": ("Karar kırılımdan 1 bar SONRA (teyit barı kapanınca) verilir. "
                 "p>=fake eşiği → SAHTE çağrısı (OOS %70); p<=genuine eşiği → "
                 "GERÇEK çağrısı (OOS %83); arası → kararsız."),
    }
    rules_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    print(f"  detector bölümü yazıldı: {rules_path}")
    print("  top features:", imp[:6])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="NDX.INDX")
    ap.add_argument("--tp", type=float, default=1.0)
    ap.add_argument("--sl", type=float, default=1.0)
    a = ap.parse_args()
    main(symbol=a.symbol, TP=a.tp, SL=a.sl)
