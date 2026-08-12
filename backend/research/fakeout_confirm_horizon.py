"""Kırılım dedektörü — TEYİT UFKU taraması: +1 bar yerine +K bar (K≤20).

Kullanıcı sorusu (2026-08-12): "dedektör bir sonraki muma bakarak teyit almasın,
sonraki 20 muma bakarak alsa sonuçlar nasıl değişir?"

Üretimdeki akış: pending → confirm_bar (+1) → wave_k2 (+2) → resolved_observed.
Dalga lab'ı K=2,3,4,6'yı denemişti; bu betik K'yı 20'ye kadar uzatır ve iki şeyi
birlikte raporlar:

  1) AKSİYON PAYI — K bar beklerken ±1×ATR yarışının ne kadarı zaten bitmiş olur.
     (K büyüdükçe "hâlâ açık" küme küçülür; kalan küme de giderek daha kararsız
      /choppy bir alt kümedir — isabet artsa bile kapsam çöker.)
  2) İSABET — hâlâ açık olaylarda, K barlık dalga özellikleriyle kronolojik
     train/val/test (eşik VAL'de) SAHTE/GERÇEK kesinliği; karşılaştırma olarak
     aynı kümede +1-bar özellik seti.

⚠️ VERİ ONARIMI: candle_cache 1m serisi 2026-05-07 ÖNCESİNDE broker saatinde
(UTC+3) etiketlenmiş; 5m serisi gerçek UTC. Yarış çözümü 1m ile yapıldığı için
onarılmadan çalıştırılırsa ETİKETLER BOZUK olur (bkz. memory
candle-cache-broker-time-offset). Burada 1m −3 saat kaydırılır ve gün bazında
5m ile tutarlılık kontrolünden geçmeyen günler ATILIR.

Çalıştırma: python backend/research/fakeout_confirm_horizon.py [SEMBOL]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fakeout_lab as lab  # noqa: E402
import fakeout_miner as fm  # noqa: E402
import fakeout_wave_lab as wave  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TP, SL, HORIZON, BAR_MIN = 1.0, 1.0, 72, 5
K_GRID = [1, 2, 3, 4, 6, 8, 12, 20]
SHIFT_UNTIL = pd.Timestamp("2026-05-07", tz="UTC")   # bu tarihten önce 1m = UTC+3
MAX_DAY_ERR = 0.6                                     # gün bazında |5m−1m| eşiği


def repair_1m(df1: pd.DataFrame, df5: pd.DataFrame) -> pd.DataFrame:
    """1m serisini 5m ile hizala: eski dönemi −3 saat kaydır, kirli günleri at."""
    d = df1.copy()
    mask = d["ts"] < SHIFT_UNTIL
    d.loc[mask, "ts"] = d.loc[mask, "ts"] - pd.Timedelta(hours=3)
    d = d.drop_duplicates(subset="ts").sort_values("ts").reset_index(drop=True)

    r1 = d.set_index("ts").close.resample("5min").last()
    a5 = df5.set_index("ts").close
    j = pd.DataFrame({"a": a5, "b": r1}).dropna()
    if j.empty:
        return d
    j["gun"] = j.index.date
    err = j.groupby("gun").apply(lambda x: (x.a - x.b).abs().mean(), include_groups=False)
    cov = j.groupby("gun").size()
    good = set(err[(err <= MAX_DAY_ERR) & (cov >= 100)].index)
    print(f"  1m onarımı: {len(good)}/{len(err)} gün temiz "
          f"(eşik |fark| ≤ {MAX_DAY_ERR}), atılan gün {len(err) - len(good)}")
    d = d[[t.date() in good for t in d["ts"]]].reset_index(drop=True)
    return d


def main() -> None:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "NDX.INDX"
    print(f"=== TEYİT UFKU TARAMASI — {symbol} ===", flush=True)
    data = lab.assemble(symbol)
    df5 = data["frames"]["5m"]
    df1 = repair_1m(data["df1"], df5)
    if df1.empty:
        raise SystemExit("temiz 1m verisi kalmadı")
    print(f"  temiz 1m: {len(df1)} bar ({df1.ts.iloc[0]:%Y-%m-%d} → {df1.ts.iloc[-1]:%Y-%m-%d})")

    df = fm.add_indicators(df5)
    print("[ufuk] olay tespiti...", flush=True)
    ev = fm.detect_events(df, df1, tp_atr=TP, sl_atr=SL,
                          horizon_bars=HORIZON, bar_minutes=BAR_MIN)
    ev = lab.add_stage2(ev, df).dropna(subset=["is_fake"]).reset_index(drop=True)
    print(f"  etiketlenen olay: {len(ev)}  "
          f"({pd.Timestamp(ev['ts'].iloc[0]):%Y-%m-%d} → {pd.Timestamp(ev['ts'].iloc[-1]):%Y-%m-%d})"
          f"  taban sahte %{ev['is_fake'].mean()*100:.1f}", flush=True)

    res_min = wave.resolution_offsets(ev, df1)
    print("\n[1] YARIŞ NE ZAMAN BİTİYOR — K bar beklemenin bedeli")
    print(f"  {'K':>3}{'dakika':>8}{'hâlâ açık':>11}{'kapsam':>9}{'o kümede taban sahte':>22}")
    for K in K_GRID:
        alive = res_min > K * BAR_MIN
        base = ev.loc[alive, "is_fake"].mean() * 100 if alive.sum() else float("nan")
        print(f"  {K:>3}{K*BAR_MIN:>8}{alive.sum():>11}{100*alive.mean():>8.1f}%{base:>21.1f}%")

    print("\n[2] İSABET — hâlâ açık kümede K barlık dalga özellikleriyle", flush=True)
    results = []
    for K in K_GRID:
        alive = res_min > K * BAR_MIN
        if alive.sum() < 200:
            print(f"\n  K={K}: aksiyon kümesi {alive.sum()} — train/val/test için yetersiz, atlandı")
            results.append({"K": K, "alive": int(alive.sum()), "skip": True})
            continue
        sub = ev[alive].reset_index(drop=True)
        evK = wave.wave_features(sub, df, K) if K >= 2 else sub
        feats = fm.FEATURES + lab.STAGE2_COLS + (wave.WAVE_COLS if K >= 2 else [])
        r = lab.eval_config(evK, feats, HORIZON, BAR_MIN, f"K{K}")
        r_base = lab.eval_config(evK, fm.FEATURES + lab.STAGE2_COLS, HORIZON,
                                 BAR_MIN, f"1bar_on_aliveK{K}")
        print(f"\n  K={K:<3} aksiyon={alive.sum():<5} (kapsam %{100*alive.mean():.0f}, "
              f"taban sahte %{sub['is_fake'].mean()*100:.1f})")
        for tag, rr in ((f"K={K} dalga", r), ("+1bar (aynı küme)", r_base)):
            if not rr.get("fake") and not rr.get("genuine"):
                print(f"    {tag:<20} → {rr.get('reason', 'sonuç yok')}")
                continue
            fk, gn = rr.get("fake", {}) or {}, rr.get("genuine", {}) or {}
            print(f"    {tag:<20} → SAHTE %{fk.get('precision')} "
                  f"(n={fk.get('test_n')}, kaps %{fk.get('coverage')}) | "
                  f"GERÇEK %{gn.get('precision')} (n={gn.get('test_n')}, "
                  f"kaps %{gn.get('coverage')}) {'✅' if rr.get('pass') else ''}")
        results.append({"K": K, "alive": int(alive.sum()),
                        "coverage_pct": round(100 * float(alive.mean()), 1),
                        "base_fake": round(float(sub["is_fake"].mean() * 100), 1),
                        "wave": r, "baseline_1bar": r_base})

    out = DATA_DIR / f"fakeout_confirm_horizon_{symbol.split('.')[0]}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1, default=str))
    print(f"\nrapor: {out}")


if __name__ == "__main__":
    main()
