"""
Fakeout MTF Lab — üst zaman dilimi (1h/30m) bağlam katmanı deneyi.

Kullanıcı hipotezi (2026-07-17): farklı TF'lerin KOMBİNASYONU alt-derecelendirme
olarak eklenirse dedektör güçlenir — "5m kırılımı 1h yapısıyla hizalıysa gerçek,
1h seviyesinin/aralığının içine kırıyorsa sahte".

Yöntem: mevcut kazanan dedektörlerin (confirm_bar +1bar ve wave_k2) AYNI olay
kümesi + AYNI protokolüne (kronolojik train/val/test, eşik VAL'de, purge)
YALNIZCA üst-TF bağlam özellikleri eklenir; OOS kesinlik/kapsam karşılaştırılır.
Üst-TF verisi: gerçek 1h cache (2025-09'dan beri) + 30m (5m'den resample).
Tüm özellikler CAUSAL: yalnız olay anından önce KAPANMIŞ üst-TF barları.

MTF özellikleri (yön-hizalı):
  - m1h_ema50_side_dir, m1h_ema200_side_dir, m30_ema50_side_dir (trend hizası)
  - m1h_rsi_dir ((RSI-50)×yön), m1h_ema20_slope_atr
  - m1h_range_pos_dir (son 24×1h aralığında pozisyon ×yön — tepeye mi kırıyor?)
  - m1h_level_confl_atr (5m seviyesi 1h fraktal pivotlarına ne kadar yakın —
    seviye üst-TF'te de seviye mi?)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fakeout_miner as fm  # noqa: E402
import fakeout_lab as lab  # noqa: E402
import fakeout_wave_lab as wl  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TP, SL, HORIZON, BAR_MIN = 1.0, 1.0, 72, 5

MTF_COLS = ["m1h_ema50_side_dir", "m1h_ema200_side_dir", "m30_ema50_side_dir",
            "m1h_rsi_dir", "m1h_ema20_slope_atr", "m1h_range_pos_dir",
            "m1h_level_confl_atr"]


def _pivot_levels_1h(df1h: pd.DataFrame, w: int = 5) -> list[tuple[int, float]]:
    """(teyit_bar_idx, fiyat) — 1h fraktal pivotlar (causal kullanılacak)."""
    ph, pl = fm._causal_pivots(df1h, w)
    return sorted([(i, p) for i, p in ph.items()] + [(i, p) for i, p in pl.items()])


def add_mtf(ev: pd.DataFrame, df1h: pd.DataFrame, df30: pd.DataFrame) -> pd.DataFrame:
    ts1h = df1h["ts"].astype("int64").values
    ts30 = df30["ts"].astype("int64").values
    HOUR = 3_600_000_000_000
    piv = _pivot_levels_1h(df1h)
    piv_idx = np.array([i for i, _ in piv])
    piv_px = np.array([p for _, p in piv])
    rows = []
    for _, e in ev.iterrows():
        t = pd.Timestamp(e["ts"]).value
        dirn = 1 if e["direction"] == "up" else -1
        i1 = int(np.searchsorted(ts1h, t - HOUR, side="right")) - 1      # son KAPANMIŞ 1h
        i3 = int(np.searchsorted(ts30, t - HOUR // 2, side="right")) - 1
        if i1 < 210 or i3 < 60:
            rows.append({c: np.nan for c in MTF_COLS})
            continue
        c1 = float(df1h["close"].iloc[i1])
        atr1 = float(df1h["atr14"].iloc[i1]) or 1e-9
        hh = df1h["high"].values[i1 - 23:i1 + 1].max()
        ll = df1h["low"].values[i1 - 23:i1 + 1].min()
        entry = float(e["close"])
        # 1h seviye-çakışması: olaydan önce teyitli pivotlara min mesafe
        m = piv_idx <= i1
        confl = (np.abs(piv_px[m] - float(e["level_price"])).min() / atr1) if m.any() else np.nan
        rows.append({
            "m1h_ema50_side_dir": np.sign(c1 - float(df1h["ema50"].iloc[i1])) * dirn,
            "m1h_ema200_side_dir": np.sign(c1 - float(df1h["ema200"].iloc[i1])) * dirn,
            "m30_ema50_side_dir": np.sign(float(df30["close"].iloc[i3]) - float(df30["ema50"].iloc[i3])) * dirn,
            "m1h_rsi_dir": (float(df1h["rsi14"].iloc[i1]) - 50.0) * dirn,
            "m1h_ema20_slope_atr": (float(df1h["ema20"].iloc[i1]) - float(df1h["ema20"].iloc[i1 - 6])) / atr1 * dirn,
            "m1h_range_pos_dir": ((entry - ll) / max(hh - ll, 1e-9) - 0.5) * 2 * dirn,
            "m1h_level_confl_atr": confl,
        })
    return pd.concat([ev.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def _report(tag: str, r: dict) -> None:
    fk, gn = r.get("fake", {}), r.get("genuine", {})
    print(f"  {tag:22s} → SAHTE %{fk.get('precision')} (n={fk.get('test_n')}, kaps %{fk.get('coverage')}) | "
          f"GERÇEK %{gn.get('precision')} (n={gn.get('test_n')}, kaps %{gn.get('coverage')}) | "
          f"{'✅' if r.get('pass') else '—'}", flush=True)
    sw = r.get("sweep")
    if sw:
        print("     sweep FAKE  " + " ".join(f"{int(x['cov']*100)}%→{x['prec']}" for x in sw["fake"])
              + " | GERÇEK " + " ".join(f"{int(x['cov']*100)}%→{x['prec']}" for x in sw["genuine"]), flush=True)


def main() -> None:
    data = lab.assemble()
    df = fm.add_indicators(data["frames"]["5m"])
    df1h = fm.add_indicators(data["frames"]["1h"])
    df30 = fm.add_indicators(data["frames"]["30m"])
    ev = fm.detect_events(df, data["df1"], tp_atr=TP, sl_atr=SL,
                          horizon_bars=HORIZON, bar_minutes=BAR_MIN)
    ev = lab.add_stage2(ev, df).dropna(subset=["is_fake"]).reset_index(drop=True)
    ev = add_mtf(ev, df1h, df30)
    n_mtf = ev["m1h_ema50_side_dir"].notna().sum()
    print(f"[mtf] olay={len(ev)}, MTF bağlamı olan={n_mtf}", flush=True)

    base_feats = fm.FEATURES + lab.STAGE2_COLS
    print("\n=== AŞAMA-1 (confirm_bar, +1 bar) ===")
    r0 = lab.eval_config(ev, base_feats, HORIZON, BAR_MIN, "base")
    _report("BASE (mevcut prod)", r0)
    r1 = lab.eval_config(ev, base_feats + MTF_COLS, HORIZON, BAR_MIN, "mtf")
    _report("BASE + MTF", r1)

    print("\n=== AŞAMA-2 (wave_k2, yarışı açık) ===")
    alive = wl.resolution_offsets(ev, data["df1"]) > 2 * BAR_MIN
    evK = wl.wave_features(ev[alive].reset_index(drop=True), df, 2)
    print(f"  yarışı-açık={len(evK)}")
    w0 = lab.eval_config(evK, base_feats + wl.WAVE_COLS, HORIZON, BAR_MIN, "wave_base")
    _report("WAVE (mevcut prod)", w0)
    w1 = lab.eval_config(evK, base_feats + wl.WAVE_COLS + MTF_COLS, HORIZON, BAR_MIN, "wave_mtf")
    _report("WAVE + MTF", w1)

    (DATA_DIR / "fakeout_mtf_report.json").write_text(json.dumps(
        {"stage1": {"base": r0, "mtf": r1}, "stage2": {"base": w0, "mtf": w1},
         "mtf_coverage_events": int(n_mtf)}, ensure_ascii=False, indent=1, default=str))
    print("\nrapor: data/fakeout_mtf_report.json")


if __name__ == "__main__":
    main()
