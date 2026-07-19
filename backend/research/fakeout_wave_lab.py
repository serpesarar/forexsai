"""
Fakeout Wave Lab — dalga-verdikt modu (kullanıcı hipotezi, 2026-07-16).

Hipotez: kırılım tek mumla değil DALGA ile gerçekleşir (kır → ters toparlanma →
devam). Kırılımdan K bar sonra, YALNIZCA yarışı henüz bitmemiş olaylarda
(aksiyon alınabilir küme), dalga-yapısı + gösterge-oranı özellikleriyle karar
vermek +1-bar dedektöründen daha isabetli/kapsamlı mı?

Özellikler (bar idx+1..idx+K penceresi):
  - mfe/mae (ATR), pullback_ratio (geri çekilme / impuls), close_k konumları
  - vol_with/vol_against ORANI (gerçek kırılımda pullback düşük hacimli tezi)
  - seviye ötesi kapanış oranı, ters bar oranı, retest-tut, RSI delta, EMA20 eğimi

Protokol: lab v2 ile aynı (kronolojik train/val/test, eşik VAL'de, purge).
Karşılaştırma: aynı yarışı-bitmemiş test kümesinde +1-bar özellik seti (baseline).
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

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TP, SL, HORIZON, BAR_MIN = 1.0, 1.0, 72, 5
K_GRID = [2, 3, 4, 6]

WAVE_COLS = ["w_mfe_atr", "w_mae_atr", "w_close_beyond_atr", "w_move_atr",
             "w_pullback_ratio", "w_frac_beyond", "w_frac_adverse",
             "w_vol_ratio_with_against", "w_vol_last_over_ma", "w_rsi_delta",
             "w_ema20_slope_atr", "w_retest_hold"]


def resolution_offsets(ev: pd.DataFrame, df1: pd.DataFrame) -> np.ndarray:
    """Her olay için yarışın bittiği ana kadar geçen DAKİKA (1m çözünürlük)."""
    ts1, h1, l1 = fm._df1_arrays(df1)
    out = np.full(len(ev), 1e9)
    for r, (_, e) in enumerate(ev.iterrows()):
        dirn = 1 if e["direction"] == "up" else -1
        entry, atr = float(e["close"]), float(e["atr_abs"])
        tgt_c = entry + dirn * TP * atr
        tgt_r = entry - dirn * SL * atr
        t0 = pd.Timestamp(e["ts"]).value + BAR_MIN * 60_000_000_000
        i0 = int(np.searchsorted(ts1, t0))
        for i in range(i0, min(i0 + HORIZON * BAR_MIN + 60, len(ts1))):
            h, l = h1[i], l1[i]
            hit_c = h >= tgt_c if dirn > 0 else l <= tgt_c
            hit_r = l <= tgt_r if dirn > 0 else h >= tgt_r
            if hit_c or hit_r:
                out[r] = (ts1[i] - t0) / 60_000_000_000 + 1
                break
    return out


def wave_features(ev: pd.DataFrame, df: pd.DataFrame, K: int) -> pd.DataFrame:
    rows = []
    H, Lo, C, O, V = (df[x].values for x in ("high", "low", "close", "open", "volume"))
    vol_ma = df["vol_ma20"].values
    rsi = df["rsi14"].values
    ema20 = df["ema20"].values
    for _, e in ev.iterrows():
        i = int(e["idx"])
        dirn = 1 if e["direction"] == "up" else -1
        atr = float(e["atr_abs"]) or 1e-9
        entry, lvl = float(e["close"]), float(e["level_price"])
        j0, j1 = i + 1, min(i + K, len(df) - 1)
        if j1 < j0:
            rows.append({c: np.nan for c in WAVE_COLS})
            continue
        hh = H[j0:j1 + 1]; ll = Lo[j0:j1 + 1]; cc = C[j0:j1 + 1]
        oo = O[j0:j1 + 1]; vv = V[j0:j1 + 1]
        mfe = (hh.max() - entry) / atr if dirn > 0 else (entry - ll.min()) / atr
        mae = (entry - ll.min()) / atr if dirn > 0 else (hh.max() - entry) / atr
        bar_dir = np.sign(cc - oo) * dirn                 # +1 yönlü, −1 ters bar
        v_with = vv[bar_dir > 0].mean() if (bar_dir > 0).any() else np.nan
        v_agn = vv[bar_dir < 0].mean() if (bar_dir < 0).any() else np.nan
        # retest-tut: seviyeye ±0.2 ATR dönüş + doğru tarafta kapanış
        retest = 0.0
        for k in range(len(cc)):
            near = (ll[k] <= lvl + 0.2 * atr) if dirn > 0 else (hh[k] >= lvl - 0.2 * atr)
            if near:
                retest = 1.0 if (cc[k] - lvl) * dirn >= 0 else -1.0
                break
        rows.append({
            "w_mfe_atr": mfe, "w_mae_atr": mae,
            "w_close_beyond_atr": (cc[-1] - lvl) / atr * dirn,
            "w_move_atr": (cc[-1] - entry) / atr * dirn,
            "w_pullback_ratio": mae / max(mfe, 0.05),
            "w_frac_beyond": float(((cc - lvl) * dirn > 0).mean()),
            "w_frac_adverse": float((bar_dir < 0).mean()),
            "w_vol_ratio_with_against": (v_with / v_agn) if (v_agn and v_agn > 0) else np.nan,
            "w_vol_last_over_ma": (vv[-1] / vol_ma[j1]) if (vol_ma[j1] and vv[-1] > 0) else np.nan,
            "w_rsi_delta": (rsi[j1] - rsi[i]) * dirn,
            "w_ema20_slope_atr": (ema20[j1] - ema20[i]) / atr * dirn,
            "w_retest_hold": retest,
        })
    return pd.concat([ev.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def main() -> None:
    data = lab.assemble()
    df = fm.add_indicators(data["frames"]["5m"])
    print("[wave] olay tespiti...", flush=True)
    ev = fm.detect_events(df, data["df1"], tp_atr=TP, sl_atr=SL,
                          horizon_bars=HORIZON, bar_minutes=BAR_MIN)
    ev = lab.add_stage2(ev, df).dropna(subset=["is_fake"]).reset_index(drop=True)
    print(f"  olay={len(ev)}")
    res_min = resolution_offsets(ev, data["df1"])

    results = []
    for K in K_GRID:
        alive = res_min > K * BAR_MIN          # K bar sonunda yarış hâlâ açık
        evK = wave_features(ev[alive].reset_index(drop=True), df, K)
        base = evK["is_fake"].mean() * 100
        print(f"\n[wave] K={K}: aksiyon-alınabilir {alive.sum()}/{len(ev)} "
              f"(%{alive.mean()*100:.0f}), taban sahte %{base:.1f}", flush=True)
        feats_wave = fm.FEATURES + lab.STAGE2_COLS + WAVE_COLS
        r = lab.eval_config(evK, feats_wave, HORIZON, BAR_MIN, f"wave_K{K}")
        r_base = lab.eval_config(evK, fm.FEATURES + lab.STAGE2_COLS, HORIZON,
                                 BAR_MIN, f"1bar_on_aliveK{K}")
        for tag, rr in (("WAVE", r), ("1bar-baseline", r_base)):
            fk, gn = rr.get("fake", {}), rr.get("genuine", {})
            print(f"  {tag:14s} → SAHTE %{fk.get('precision')} (n={fk.get('test_n')}, "
                  f"kaps %{fk.get('coverage')}) | GERÇEK %{gn.get('precision')} "
                  f"(n={gn.get('test_n')}, kaps %{gn.get('coverage')}) | "
                  f"{'✅' if rr.get('pass') else '—'} {rr.get('reason','')}", flush=True)
            sw = rr.get("sweep")
            if sw:
                print("     sweep FAKE  " + " ".join(f"{int(x['cov']*100)}%→{x['prec']}" for x in sw["fake"])
                      + " | GERÇEK " + " ".join(f"{int(x['cov']*100)}%→{x['prec']}" for x in sw["genuine"]), flush=True)
        results.append({"K": K, "alive": int(alive.sum()), "base_fake": round(base, 1),
                        "wave": r, "baseline_1bar": r_base})

    (DATA_DIR / "fakeout_wave_report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str))
    print("\nrapor: data/fakeout_wave_report.json")


if __name__ == "__main__":
    main()
