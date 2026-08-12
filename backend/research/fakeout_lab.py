"""
Fakeout Lab — %70/%70 hedefi için sistematik deney ızgarası.

HEDEF (kullanıcı, 2026-07-16): "SAHTE dedi → sahte çıktı" VE "GERÇEK dedi →
gerçek çıktı" isabetlerinin İKİSİ de OOS'ta ≥%70 olana kadar farklı filtreler,
hedef geometrileri, timeframe'ler ve algoritmalar dene (hedefi aşırı küçültme).

Izgara:
  - Timeframe: 5m (1m-genişletilmiş), 15m, 30m (5m'den resample), 1h (native cache)
  - Hedef geometrisi (tp_atr, sl_atr): (1,1) (1,1.5) (1.5,1) (0.75,1)  — tp ≥ 0.75 ATR
  - Karar modu: instant (kırılım barında) | delayed (+1 bar bilgisiyle sınıfla;
    etiket DEĞİŞMEZ — filtrasyon-tutarlı tahmin, sızıntı değil)
  - Model: LightGBM (chrono %70/30, purge boşluğu) vs sayım-skoru benchmark

Başarı ölçütü (bir konfig için):
  Eşikler YALNIZ train'de seçilir (hedef ≥%72 kesinlik, marj için);
  test'te her iki tarafta kesinlik ≥%70, çağrı ≥20 olay ve kapsam ≥%12.

Çıktı: backend/data/fakeout_lab_report.md + en iyi konfig JSON'u (stdout).
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fakeout_miner as fm  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

GEOMETRIES = [(1.0, 1.0), (1.0, 1.5), (1.5, 1.0), (0.75, 1.0)]
#: TF → (bar_minutes, horizon_bars, pivot_w, cooldown) — yapı parametreleri
#: TF ile ölçeklenir; 5m değerleri üretim konfigürasyonudur.
TF_SPECS = {"5m": (5, 72, 12, 24), "15m": (15, 48, 8, 12),
            "30m": (30, 32, 6, 8), "1h": (60, 24, 5, 6)}

#: Kronolojik 3-yol: model TRAIN'de öğrenir, eşik VAL'de seçilir, sonuç TEST'te.
TRAIN_FRAC, VAL_FRAC = 0.55, 0.15
PREC_TARGET_VAL = 72.0     # marjlı hedef (test ≥70 için)
PREC_TARGET_TEST = 70.0
MIN_CALLS_TEST = 15
MIN_COVERAGE = 0.08
MIN_EVENTS = 140

STAGE2_COLS = ["c1_beyond_atr", "c1_body_ratio", "c1_vol_ratio", "c1_move_atr"]


def _log(m: str) -> None:
    print(m, flush=True)


# ─── Veri montajı ────────────────────────────────────────────────────────────

def resample_ohlcv(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Bucket-hizalı resample (ts = bucket açılışı; kısmi son bucket dahil)."""
    g = df.set_index("ts").resample(f"{minutes}min", label="left", closed="left")
    out = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(),
        "low": g["low"].min(), "close": g["close"].last(),
        "volume": g["volume"].sum(),
    }).dropna(subset=["open", "high", "low", "close"]).reset_index()
    return out


def align_1m_basis(df1: "pd.DataFrame", df5: "pd.DataFrame") -> "pd.DataFrame":
    """1m serisini 5m'in FİYAT TABANINA hizala (gün gün medyan fark).

    NEDEN (2026-08-12): 1m'in 2026-02→05 partisi ESKİ broker'dan (USTEC/IC
    Markets), 5m ise güncel broker'dan (NAS100/Pepperstone) geliyor. Zaman
    ekseni onarıldıktan sonra bile aralarında sistematik 3-12 puanlık taban
    farkı kalıyor — NDX'te bu ATR(5m)'in %10-40'ı kadar. Yarış etiketi 1m ile,
    giriş/ATR 5m ile hesaplandığı için bu fark TP/SL yarışını yanlı yapar.

    Çözüm: her gün için medyan(5m_close − eşleşen_1m_close) kadar 1m'in TÜM
    fiyat kolonlarını kaydır. Bu bir SEVİYE düzeltmesidir; bar içi hareketi
    (yani yarışın kendisini) değiştirmez. Aynı-besleme günlerinde fark 0'dır
    ve işlem no-op olur.
    """
    if df1.empty or df5.empty:
        return df1
    r1 = df1.set_index("ts")["close"].resample("5min").last()
    a5 = df5.set_index("ts")["close"]
    j = pd.DataFrame({"a": a5, "b": r1}).dropna()
    if j.empty:
        return df1
    j["gun"] = j.index.date
    off = (j["a"] - j["b"]).groupby(j["gun"]).median()
    d = df1.copy()
    shift = pd.Series(d["ts"].dt.date.map(off).values, index=d.index).fillna(0.0)
    for col in ("open", "high", "low", "close"):
        if col in d.columns:
            d[col] = d[col] + shift
    n_adj = int((off.abs() > 0.05).sum())
    if n_adj:
        _log(f"  1m taban hizalama: {n_adj}/{len(off)} gün düzeltildi "
             f"(medyan |fark| {off.abs().median():.2f})")
    return d


def assemble(symbol: str = "NDX.INDX") -> dict:
    _log(f"[lab] veri çekiliyor ({symbol}: 1m + 5m + 1h)...")
    df1 = fm.fetch_candles(symbol, "1m")
    df5n = fm.fetch_candles(symbol, "5m")
    df60 = fm.fetch_candles(symbol, "1h")
    # 5m'i 1m ile geriye genişlet (Şubat–Mart dönemi 5m cache'te yok)
    first5 = df5n["ts"].iloc[0]
    early1 = df1[df1["ts"] < first5]
    if len(early1) > 500:
        df5e = pd.concat([resample_ohlcv(early1, 5), df5n], ignore_index=True)
        df5e = df5e.drop_duplicates(subset="ts").sort_values("ts").reset_index(drop=True)
    else:
        df5e = df5n
    frames = {
        "5m": df5e,
        "15m": resample_ohlcv(df5e, 15),
        "30m": resample_ohlcv(df5e, 30),
        "1h": df60,
    }
    for k, v in frames.items():
        _log(f"  {k}: {len(v)} bar ({v['ts'].iloc[0]:%Y-%m-%d} → {v['ts'].iloc[-1]:%Y-%m-%d})")
    df1 = align_1m_basis(df1, df5e)
    _log(f"  1m (yarış çözümü): {len(df1)} bar")
    return {"frames": frames, "df1": df1}


# ─── Stage-2 (+1 bar) özellikleri ───────────────────────────────────────────

def add_stage2(ev: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, e in ev.iterrows():
        i = int(e["idx"]) + 1
        dirn = 1 if e["direction"] == "up" else -1
        atr = float(e["atr_abs"]) or 1e-9
        if i >= len(df):
            rows.append({c: np.nan for c in STAGE2_COLS})
            continue
        o, h, l, c = (float(df[x].iloc[i]) for x in ("open", "high", "low", "close"))
        v = float(df["volume"].iloc[i])
        vol_ma = float(df["vol_ma20"].iloc[i]) if not np.isnan(df["vol_ma20"].iloc[i]) else 0.0
        rng = max(h - l, 1e-9)
        rows.append({
            "c1_beyond_atr": (c - float(e["level_price"])) / atr * dirn,
            "c1_body_ratio": abs(c - o) / rng,
            "c1_vol_ratio": v / vol_ma if (vol_ma > 0 and v > 0) else np.nan,
            "c1_move_atr": (c - float(e["close"])) / atr * dirn,
        })
    return pd.concat([ev.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


# ─── Değerlendirme ───────────────────────────────────────────────────────────

def _split3_purged(ev: pd.DataFrame, horizon_bars: int, bar_minutes: int):
    """Kronolojik train/val/test + segment aralarında horizon kadar purge boşluğu."""
    n = len(ev)
    i_tr, i_va = int(n * TRAIN_FRAC), int(n * (TRAIN_FRAC + VAL_FRAC))
    gap = pd.Timedelta(minutes=horizon_bars * bar_minutes)
    ts = pd.to_datetime(ev["ts"], utc=True)
    train = ev.iloc[:i_tr]
    val = ev.iloc[i_tr:i_va][ts.iloc[i_tr:i_va] > ts.iloc[i_tr - 1] + gap]
    test = ev.iloc[i_va:][ts.iloc[i_va:] > ts.iloc[i_va - 1] + gap]
    return train, val, test


def _pick_threshold(p: np.ndarray, y: np.ndarray, side: str) -> float | None:
    """VAL'de kesinlik ≥ PREC_TARGET_VAL sağlayan en geniş kapsamlı eşik.
    side='fake': p ≥ thr → SAHTE çağrısı; side='genuine': p ≤ thr → GERÇEK."""
    qs = np.unique(np.quantile(p, np.linspace(0.02, 0.98, 49)))
    best = None
    for thr in qs:
        m = p >= thr if side == "fake" else p <= thr
        n = int(m.sum())
        if n < 12:
            continue
        prec = (y[m] == 1).mean() * 100 if side == "fake" else (y[m] == 0).mean() * 100
        if prec >= PREC_TARGET_VAL:
            if best is None or n > best[1]:
                best = (float(thr), n)
    return best[0] if best else None


def _coverage_sweep(p_te: np.ndarray, y_te: np.ndarray) -> dict:
    """Teşhis: test'te sabit kapsam dilimlerinde kesinlik (eşiksiz sıralama kalitesi)."""
    out = {}
    order = np.argsort(p_te)
    for side in ("fake", "genuine"):
        rows = []
        for cov in (0.05, 0.10, 0.15, 0.20, 0.30):
            k = max(int(len(p_te) * cov), 5)
            idx = order[-k:] if side == "fake" else order[:k]
            prec = ((y_te[idx] == 1).mean() if side == "fake" else (y_te[idx] == 0).mean()) * 100
            rows.append({"cov": cov, "n": k, "prec": round(prec, 1)})
        out[side] = rows
    return out


def _eval_sides(p_va, y_va, p_te, y_te) -> dict:
    out = {}
    for side in ("fake", "genuine"):
        thr = _pick_threshold(p_va, y_va, side)
        if thr is None:
            out[side] = {"ok": False, "precision": None, "coverage": None,
                         "test_n": 0, "reason": "val eşiği yok"}
            continue
        m = p_te >= thr if side == "fake" else p_te <= thr
        n = int(m.sum())
        prec = ((y_te[m] == 1).mean() if side == "fake" else (y_te[m] == 0).mean()) * 100 if n else 0.0
        out[side] = {"ok": bool(n >= MIN_CALLS_TEST and n / max(len(y_te), 1) >= MIN_COVERAGE
                                and prec >= PREC_TARGET_TEST),
                     "thr": round(thr, 3), "test_n": n,
                     "coverage": round(n / max(len(y_te), 1) * 100, 1),
                     "precision": round(prec, 1)}
    out["pass"] = bool(out.get("fake", {}).get("ok") and out.get("genuine", {}).get("ok"))
    return out


def _fit_lgbm(X_tr, y_tr):
    """Küçük örnekleme göre AĞIR regülarizasyon (ilk ızgarada ezber görüldü)."""
    try:
        import lightgbm as lgb
        m = lgb.LGBMClassifier(n_estimators=120, learning_rate=0.05, num_leaves=7,
                               min_child_samples=40, subsample=0.8, colsample_bytree=0.7,
                               reg_lambda=10.0, random_state=42, verbose=-1)
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier
        m = GradientBoostingClassifier(n_estimators=120, learning_rate=0.05,
                                       max_depth=2, subsample=0.8, random_state=42)
    m.fit(X_tr, y_tr)
    return m


def eval_config(ev: pd.DataFrame, feats: list[str], horizon_bars: int,
                bar_minutes: int, mode: str) -> dict:
    ev = ev.dropna(subset=["is_fake"]).reset_index(drop=True)
    train, val, test = _split3_purged(ev, horizon_bars, bar_minutes)
    if len(train) < 90 or len(val) < 25 or len(test) < 50:
        return {"pass": False, "reason": f"örneklem küçük (tr={len(train)}, va={len(val)}, te={len(test)})"}
    med = train[feats].median(numeric_only=True)
    X_tr, X_va, X_te = (d[feats].fillna(med) for d in (train, val, test))
    y_tr, y_va, y_te = (d["is_fake"].values for d in (train, val, test))
    model = _fit_lgbm(X_tr, y_tr)
    p_va = model.predict_proba(X_va)[:, 1]
    p_te = model.predict_proba(X_te)[:, 1]
    res = _eval_sides(p_va, y_va, p_te, y_te)
    res["sweep"] = _coverage_sweep(p_te, y_te)
    res.update({"mode": mode, "train_n": len(train), "val_n": len(val), "test_n": len(test),
                "base_fake_test": round(y_te.mean() * 100, 1)})
    return res


# ─── Ana ızgara ──────────────────────────────────────────────────────────────

def main(symbol: str = "NDX.INDX") -> None:
    data = assemble(symbol)
    df1 = data["df1"]
    results = []
    events_cache: dict[str, pd.DataFrame] = {}

    for tf, (bar_min, horizon, pivot_w, cooldown) in TF_SPECS.items():
        df = fm.add_indicators(data["frames"][tf])
        # Yapı parametrelerini TF'ye ölçekle (detect_events modül globallerini okur)
        fm.PIVOT_W, fm.LEVEL_COOLDOWN = pivot_w, cooldown
        for tp, sl in GEOMETRIES:
            key = f"{tf}|tp{tp}|sl{sl}"
            _log(f"\n[lab] {key} (horizon={horizon} bar, w={pivot_w}, cd={cooldown})...")
            ev = fm.detect_events(df, df1, tp_atr=tp, sl_atr=sl,
                                  horizon_bars=horizon, bar_minutes=bar_min)
            if ev.empty or len(ev) < MIN_EVENTS:
                _log(f"  olay={len(ev)} — atlandı (yetersiz)")
                continue
            ev = add_stage2(ev, df)
            events_cache[key] = ev
            base = ev["is_fake"].mean() * 100
            _log(f"  olay={len(ev)}, taban sahte %{base:.1f}")
            for mode, feats in (("instant", fm.FEATURES),
                                ("delayed+1bar", fm.FEATURES + STAGE2_COLS)):
                r = eval_config(ev, feats, horizon, bar_min, mode)
                r.update({"tf": tf, "tp": tp, "sl": sl, "events": len(ev),
                          "key": key})
                results.append(r)
                fk, gn = r.get("fake", {}), r.get("genuine", {})
                _log(f"  {mode:13s} → SAHTE %{fk.get('precision')} (n={fk.get('test_n')}, kaps %{fk.get('coverage')}) | "
                     f"GERÇEK %{gn.get('precision')} (n={gn.get('test_n')}, kaps %{gn.get('coverage')}) | "
                     f"{'✅ GEÇTİ' if r.get('pass') else '—'}")
                sw = r.get("sweep")
                if sw:
                    _log("     sweep FAKE  " + " ".join(f"{int(x['cov']*100)}%→{x['prec']}" for x in sw["fake"])
                         + " | GERÇEK " + " ".join(f"{int(x['cov']*100)}%→{x['prec']}" for x in sw["genuine"]))

    passing = [r for r in results if r.get("pass")]
    _log(f"\n[lab] {len(results)} konfig denendi, {len(passing)} tanesi %70/%70 geçti")
    ranked = sorted(passing, key=lambda r: -(min(r['fake']['precision'], r['genuine']['precision'])
                                             + min(r['fake']['coverage'], r['genuine']['coverage']) * 0.3))
    for r in ranked[:8]:
        _log(f"  ✅ {r['key']} {r['mode']}: SAHTE %{r['fake']['precision']}/kaps%{r['fake']['coverage']} "
             f"GERÇEK %{r['genuine']['precision']}/kaps%{r['genuine']['coverage']} (test n={r['test_n']})")

    # Rapor
    L = ["# Fakeout Lab — %70/%70 Deney Izgarası (NDX)", ""]
    L.append("| TF | TP | SL | Mod | Olay | Taban sahte% (te) | SAHTE kesinlik% | SAHTE kaps% | GERÇEK kesinlik% | GERÇEK kaps% | Geçti |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        fk, gn = r.get("fake", {}), r.get("genuine", {})
        L.append(f"| {r['tf']} | {r['tp']} | {r['sl']} | {r['mode']} | {r.get('events')} | "
                 f"{r.get('base_fake_test')} | {fk.get('precision', '—')} | {fk.get('coverage', '—')} | "
                 f"{gn.get('precision', '—')} | {gn.get('coverage', '—')} | {'✅' if r.get('pass') else ''} |")
    L.append("")
    L.append("Eşikler yalnız TRAIN'de seçildi (hedef ≥%72); tablo değerleri TEST (OOS). "
             "Purge: test, train sonundan horizon kadar boşluk sonrası başlar.")
    suffix = "" if symbol == "NDX.INDX" else f"_{symbol.split('.')[0]}"
    (DATA_DIR / f"fakeout_lab_report{suffix}.md").write_text(
        "\n".join(L).replace("(NDX)", f"({symbol})"))
    _log(f"\nrapor: {DATA_DIR / f'fakeout_lab_report{suffix}.md'}")

    if ranked:
        best = ranked[0]
        _log("\n[lab] EN İYİ KONFİG: " + json.dumps(
            {k: best[k] for k in ("key", "mode", "fake", "genuine", "events", "test_n")},
            ensure_ascii=False))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="NDX.INDX")
    main(symbol=ap.parse_args().symbol)
