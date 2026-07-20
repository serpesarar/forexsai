"""Fakeout Service — sahte kırılım radarı (runtime).

fakeout_miner.py'ın (backend/research/) ürettiği OOS-doğrulanmış kuralları
(backend/data/fakeout_rules.json) canlıda uygular:

  1. Son 5m barlarda TAZE bir S/R veya kanal kırılımı var mı? (madenci ile aynı
     causal seviye mantığı — pivot ancak w bar sonra teyitlenir, lookahead yok)
  2. Varsa kırılım anı özellikleri hesaplanır ve kalite filtresinden geçen
     kurallarla eşlenir → sahte-kırılım olasılığı + karar ("likely_fake" /
     "lean_genuine" / "uncertain").

Tüketiciler:
  - signal_gates.fakeout_gate  → NDX pulse/smc kırılım-yönlü sinyal kapısı
  - routers/fakeout_router.py  → GET /api/fakeout/assess/{symbol}
  - claude_decider/run_decider → situation["fakeout"] enjeksiyonu (saf çekirdek)

Saf çekirdek (assess_bars) FastAPI'ye bağımlı DEĞİLDİR — claude_decider kendi
MT5 barlarıyla doğrudan çağırır. Barlarda "open" yoksa önceki kapanış kullanılır
(5m endeks barlarında open ≈ prev close). Tüm hata yolları fail-open: değerlendirme
yapılamazsa {"status": "unavailable"} döner, asla exception sızdırmaz.

Kanıt (v2, 2026-07-16, NDX 5m, 1005 olay, kronolojik %70/30):
  - Taban: kırılımların %65-69'u SAHTE (±1×ATR iki-hedef yarışı, 1m çözünürlük).
  - Birleşik skor (GERÇEK-pozitif, 8 bileşen) OOS kalibrasyonu:
      skor ≤ −2 → %87.2 sahte (n=86)  ← FADE (ters işlem) kanıtı, en güçlü hücre
      skor ≥ +2 → %55.6 gerçek (n=45) ← zayıf; TEK BAŞINA edge DEĞİL
  - Teyit protokolü backtest'i: kırılım-yönlü TÜM giriş varyantları −EV
    (breakout bar −0.29R, sonraki-bar teyidi −0.07R, retest-tut −0.10R OOS).
    Teyit yalnızca ELEME filtresi: teyit gelmezse orijinal gerçeklik %13'e düşer.
  → Profesyonel sonuç: NDX 5m'de edge kırılımı ALMAKTA değil, klimaks kırılımı
    SÖNDÜRMEKTE (fade) ve kırılım-yönlü sinyali FRENLEMEKTEDİR.
"""
from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "fakeout_rules.json"
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "model_fakeout_ndx_5m.joblib"
MODEL_WAVE_PATH = Path(__file__).resolve().parent.parent / "models" / "model_fakeout_ndx_5m_wave.joblib"

# ─── Madenci ile BİREBİR aynı olay parametreleri (senkron tutulmalı) ─────────
PIVOT_W = 12
CLUSTER_TOL_ATR = 0.35
MIN_TOUCHES = 2
PEN_MIN_ATR = 0.10
LEVEL_COOLDOWN = 24
CH_WIN = 96
CH_K = 2.0
CH_R2_MIN = 0.5

#: Kırılım kaç bar içindeyse "taze" sayılır. 5 = dalga-verdikti (K=2) canlıda
#: görülebilsin diye 3'ten genişletildi (aşama-2 kararı bars_ago≥2'de gelir).
FRESH_BARS = 5

#: Runtime'da kullanılacak kuralların kalite tabanı (rapor "Dürüstlük Notları").
RULE_MIN_TRAIN_N = 25
RULE_MIN_TEST_N = 10
RULE_MIN_TRAIN_LIFT = 8.0
RULE_MIN_TEST_LIFT = 5.0

_CACHE_TTL_SECONDS = 60   # sembol bazlı assess cache'i (5m bar hızında yeterli)

_rules_cache: Dict[str, Dict[str, Any]] = {}


def _rules_path_for(symbol: str) -> Path:
    """NDX legacy adı korunur; diğer semboller fakeout_rules_<BASE>.json."""
    if symbol == "NDX.INDX":
        return RULES_PATH
    return RULES_PATH.parent / f"fakeout_rules_{symbol.split('.')[0]}.json"
_assess_cache: Dict[str, tuple] = {}
_model_cache: Dict[str, Dict[str, Any]] = {}
_wave_model_cache: Dict[str, Dict[str, Any]] = {}


def _load_model_cached(path: Path, cache: Dict[str, Any]) -> Optional[dict]:
    """Doğrulanmış LGBM dedektör paketini yükle (mtime izlemeli, fail-open)."""
    try:
        if not path.exists():
            return None
        mtime = path.stat().st_mtime
        if cache["mtime"] != mtime:
            import joblib
            cache["bundle"] = joblib.load(path)
            cache["mtime"] = mtime
            logger.info("[fakeout] dedektör modeli yüklendi (%s)", path.name)
        return cache["bundle"]
    except Exception as exc:
        logger.warning("[fakeout] dedektör yüklenemedi (fail-open, %s): %s", path.name, exc)
        return None


def _stage2_features(df: pd.DataFrame, idx: int, level: float, dirn: int,
                     entry_close: float, atr: float) -> Dict[str, float]:
    """Teyit barı (+1) özellikleri — lab.add_stage2 ile birebir aynı formüller."""
    j = idx + 1
    o, h, l, c = (float(df[x].iloc[j]) for x in ("open", "high", "low", "close"))
    v = float(df["volume"].iloc[j])
    vol_ma = float(df["vol_ma20"].iloc[j]) if not math.isnan(float(df["vol_ma20"].iloc[j] or np.nan)) else 0.0
    rng = max(h - l, 1e-9)
    return {
        "c1_beyond_atr": (c - level) / atr * dirn,
        "c1_body_ratio": abs(c - o) / rng,
        "c1_vol_ratio": v / vol_ma if (vol_ma > 0 and v > 0) else float("nan"),
        "c1_move_atr": (c - entry_close) / atr * dirn,
    }


def _race_state(df: pd.DataFrame, idx: int, dirn: int, entry: float,
                atr: float, tp_atr: float = 1.0, sl_atr: float = 1.0) -> str:
    """İki-hedef yarışının 5m barlarla mevcut durumu: open | genuine | fake | ambiguous.
    tp/sl sembolün dedektör geometrisinden gelir (örn. XAU tp0.75/sl1.0)."""
    tgt_c = entry + dirn * tp_atr * atr
    tgt_r = entry - dirn * sl_atr * atr
    for j in range(idx + 1, len(df)):
        h, l = float(df["high"].iloc[j]), float(df["low"].iloc[j])
        hit_c = h >= tgt_c if dirn > 0 else l <= tgt_c
        hit_r = l <= tgt_r if dirn > 0 else h >= tgt_r
        if hit_c and hit_r:
            return "ambiguous"
        if hit_c:
            return "genuine"
        if hit_r:
            return "fake"
    return "open"


def _wave_features_runtime(df: pd.DataFrame, idx: int, dirn: int, entry: float,
                           lvl: float, atr: float, K: int) -> Dict[str, float]:
    """fakeout_wave_lab.wave_features ile birebir aynı formüller (tek olay)."""
    j0, j1 = idx + 1, min(idx + K, len(df) - 1)
    hh = df["high"].values[j0:j1 + 1]; ll = df["low"].values[j0:j1 + 1]
    cc = df["close"].values[j0:j1 + 1]; oo = df["open"].values[j0:j1 + 1]
    vv = df["volume"].values[j0:j1 + 1]
    mfe = (hh.max() - entry) / atr if dirn > 0 else (entry - ll.min()) / atr
    mae = (entry - ll.min()) / atr if dirn > 0 else (hh.max() - entry) / atr
    bar_dir = np.sign(cc - oo) * dirn
    v_with = vv[bar_dir > 0].mean() if (bar_dir > 0).any() else float("nan")
    v_agn = vv[bar_dir < 0].mean() if (bar_dir < 0).any() else float("nan")
    retest = 0.0
    for k in range(len(cc)):
        near = (ll[k] <= lvl + 0.2 * atr) if dirn > 0 else (hh[k] >= lvl - 0.2 * atr)
        if near:
            retest = 1.0 if (cc[k] - lvl) * dirn >= 0 else -1.0
            break
    vol_ma_j1 = float(df["vol_ma20"].iloc[j1] or np.nan)
    return {
        "w_mfe_atr": mfe, "w_mae_atr": mae,
        "w_close_beyond_atr": (cc[-1] - lvl) / atr * dirn,
        "w_move_atr": (cc[-1] - entry) / atr * dirn,
        "w_pullback_ratio": mae / max(mfe, 0.05),
        "w_frac_beyond": float(((cc - lvl) * dirn > 0).mean()),
        "w_frac_adverse": float((bar_dir < 0).mean()),
        "w_vol_ratio_with_against": (v_with / v_agn) if (v_agn and v_agn > 0) else float("nan"),
        "w_vol_last_over_ma": (vv[-1] / vol_ma_j1) if (vol_ma_j1 and not math.isnan(vol_ma_j1) and vv[-1] > 0) else float("nan"),
        "w_rsi_delta": (float(df["rsi14"].iloc[j1]) - float(df["rsi14"].iloc[idx])) * dirn,
        "w_ema20_slope_atr": (float(df["ema20"].iloc[j1]) - float(df["ema20"].iloc[idx])) / atr * dirn,
        "w_retest_hold": retest,
    }


def _run_detector(df: pd.DataFrame, bo: dict, feat: Dict[str, float],
                  payload: dict) -> Optional[dict]:
    """Doğrulanmış +1-bar dedektörü: SAHTE / GERÇEK / kararsız çağrısı.

    Karar kırılımdan 1 bar sonra verilir (OOS: SAHTE çağrısı %70, GERÇEK %83).
    Teyit barı henüz kapanmadıysa 'pending_next_bar' döner.
    """
    det_cfg = payload.get("detector") or {}
    if not det_cfg:
        return None
    idx = int(bo["idx"])
    bars_ago = int(bo.get("bars_ago", 0))
    if bars_ago < 1 or idx + 1 >= len(df):
        return {"call": "pending_next_bar", "stage": "pending",
                "note": "Teyit barı kapanınca kesin karar (~5dk)",
                "oos": det_cfg.get("oos")}
    try:
        dirn = 1 if bo["direction"] in (1, "up") else -1
        atr = float(df["atr14"].iloc[idx]) or 1e-9
        entry = float(df["close"].iloc[idx])
        lvl = float(bo["level_price"])

        # 0) Yarış zaten sonuçlandıysa gözlemlenen GERÇEĞİ raporla (model gerekmez)
        race = _race_state(df, idx, dirn, entry, atr,
                           tp_atr=float(det_cfg.get("tp_atr", 1.0)),
                           sl_atr=float(det_cfg.get("sl_atr", 1.0)))
        if race in ("genuine", "fake"):
            return {"call": race, "stage": "resolved_observed", "p_fake": None,
                    "note": "±1ATR yarışı sonuçlandı — bu model tahmini değil, gözlemlenen sonuç"}

        # 2) Aşama-2: dalga-verdikti (K=2) — yarış açık ve 2 bar kapanmışsa
        wave_cfg = payload.get("detector_wave") or {}
        if wave_cfg and bars_ago >= 2 and idx + 2 < len(df) and race == "open":
            wave_path = MODEL_WAVE_PATH.parent / (wave_cfg.get("model_file") or MODEL_WAVE_PATH.name)
            wb = _load_model_cached(wave_path, _wave_model_cache.setdefault(str(wave_path), {"mtime": None, "bundle": None}))
            if wb:
                c1 = _stage2_features(df, idx, lvl, dirn, entry, atr)
                wf = _wave_features_runtime(df, idx, dirn, entry, lvl, atr,
                                            int(wave_cfg.get("K", 2)))
                row = {**feat, **c1, **wf}
                X = pd.DataFrame([row]).reindex(columns=wb["features"])
                X = X.fillna(pd.Series(wb.get("medians") or {}))
                p = float(wb["model"].predict_proba(X)[0, 1])
                thr = wave_cfg.get("thresholds") or {}
                call = ("fake" if p >= float(thr.get("fake", 2))
                        else "genuine" if p <= float(thr.get("genuine", -1))
                        else "abstain")
                return {"call": call, "p_fake": round(p * 100, 1), "stage": "wave_k2",
                        "thresholds": thr, "oos": wave_cfg.get("oos"),
                        "note": "Dalga-verdikti: yarışı hâlâ açık kırılımda pullback yapısından karar"}

        # 1) Aşama-1: teyit barı (+1) dedektörü
        det_path = MODEL_PATH.parent / Path(det_cfg.get("model_file") or MODEL_PATH.name).name
        bundle = _load_model_cached(det_path, _model_cache.setdefault(str(det_path), {"mtime": None, "bundle": None}))
        if not bundle:
            return None
        c1 = _stage2_features(df, idx, lvl, dirn, entry, atr)
        row = {**feat, **c1}
        X = pd.DataFrame([row]).reindex(columns=bundle["features"])
        X = X.fillna(pd.Series(bundle.get("medians") or {}))
        p = float(bundle["model"].predict_proba(X)[0, 1])
        thr = det_cfg.get("thresholds") or {}
        if p >= float(thr.get("fake", 2)):
            call = "fake"
        elif p <= float(thr.get("genuine", -1)):
            call = "genuine"
        else:
            call = "abstain"
        return {"call": call, "p_fake": round(p * 100, 1), "stage": "confirm_bar",
                "thresholds": thr, "oos": det_cfg.get("oos"),
                "confirm_bar_features": {k: round(v, 3) if not math.isnan(v) else None
                                         for k, v in c1.items()}}
    except Exception as exc:
        logger.warning("[fakeout] dedektör inference hatası (fail-open): %s", exc)
        return None


# ─── Kural yükleme (mtime izlemeli) ──────────────────────────────────────────

def load_rules(symbol: str = "NDX.INDX") -> Optional[dict]:
    """Sembolün kural dosyasını yükle; dosya değiştiyse yeniden oku."""
    try:
        path = _rules_path_for(symbol)
        if not path.exists():
            return None
        mtime = path.stat().st_mtime
        entry = _rules_cache.setdefault(symbol, {"mtime": None, "payload": None})
        if entry["mtime"] != mtime:
            entry["payload"] = json.loads(path.read_text())
            entry["mtime"] = mtime
            logger.info("[fakeout] kurallar yüklendi (%s, %s)", symbol,
                        entry["payload"].get("generated_at"))
        return entry["payload"]
    except Exception as exc:
        logger.warning("[fakeout] kural yükleme hatası (%s): %s", symbol, exc)
        return None


def _quality_rules(payload: dict) -> List[dict]:
    """Kalite tabanını geçen kuralları düzleştir (singles + combos + tree)."""
    out: List[dict] = []
    rules = payload.get("rules") or {}
    for group in ("combos", "tree", "singles"):
        for r in rules.get(group) or []:
            if (r.get("train_n", 0) >= RULE_MIN_TRAIN_N
                    and r.get("test_n", 0) >= RULE_MIN_TEST_N
                    and abs(r.get("train_lift_pp", 0)) >= RULE_MIN_TRAIN_LIFT
                    and abs(r.get("test_lift_pp", 0)) >= RULE_MIN_TEST_LIFT
                    and r.get("train_lift_pp", 0) * r.get("test_lift_pp", 0) > 0):
                out.append({**r, "group": group})
    return out


# ─── Göstergeler (madenci ile aynı formüller) ────────────────────────────────

def _prep_df(bars: Sequence[dict]) -> Optional[pd.DataFrame]:
    if not bars or len(bars) < CH_WIN + PIVOT_W * 2 + 5:
        return None
    df = pd.DataFrame(list(bars))
    for col in ("high", "low", "close"):
        if col not in df.columns:
            return None
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "open" not in df.columns or df["open"].isna().all():
        df["open"] = df["close"].shift(1)        # MT5 decider barları: open ≈ prev close
    else:
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
    df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0.0)
    df = df.dropna(subset=["high", "low", "close"]).reset_index(drop=True)

    # ── Zaman damgası (erken ayrıştırılır: forming-bar filtresi için) ──────
    if "time" in df.columns:      # decider/MT5 barları: epoch saniye
        ts = pd.to_datetime(df["time"], unit="s", utc=True, errors="coerce")
    elif "timestamp" in df.columns:
        tsv = pd.to_numeric(df["timestamp"], errors="coerce")
        if tsv.notna().any():     # DataHub: epoch (ms > 1e12, s > 1e9)
            unit = "ms" if float(tsv.dropna().iloc[-1]) > 1e12 else "s"
            ts = pd.to_datetime(tsv, unit=unit, utc=True, errors="coerce")
        else:                     # ISO string (candle_cache formatı)
            ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    else:
        ts = pd.Series([pd.NaT] * len(df))

    # ── FORMING-BAR FİLTRESİ (2026-07-20 denetim düzeltmesi) ───────────────
    # DataHub son bar(lar)ı henüz KAPANMAMIŞ olabilir (tek-tick embriyo bar,
    # sahte gap'ler, bar-içi spike'lar). Doğrulanmış lab protokolü yalnız
    # KAPANMIŞ barlarla karar verir — bucket'ı dolmamış kuyruk barları düşürülür.
    # Kural yalnız zaman damgaları UTC-senkron görünüyorsa uygulanır (son bar
    # now'a ≤10dk yakın): MT5 broker-saatli barlar (UTC+2/3) yanlışlıkla
    # düşmesin — o yollar forming barı KAYNAKTA atlar (copy_rates pos=1).
    # Zaman damgası yoksa fail-open (davranış değişmez).
    if ts.notna().any():
        now = pd.Timestamp.now(tz="UTC")
        bar_delta = pd.Timedelta(minutes=5)
        clock_ok = abs(ts.dropna().iloc[-1] - now) <= pd.Timedelta(minutes=10)
        if clock_ok:
            while len(df) and pd.notna(ts.iloc[-1]) and ts.iloc[-1] + bar_delta > now:
                df = df.iloc[:-1]
                ts = ts.iloc[:-1]
            df = df.reset_index(drop=True)
            ts = ts.reset_index(drop=True)
    if len(df) < CH_WIN + PIVOT_W * 2 + 5:
        return None

    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([(h - l), (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    df["atr14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()

    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    df["rsi14"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))

    hd, ld = h.diff(), -l.diff()
    plus_dm = ((hd > ld) & (hd > 0)).astype(float) * hd.clip(lower=0)
    minus_dm = ((ld > hd) & (ld > 0)).astype(float) * ld.clip(lower=0)
    atr_s = tr.ewm(alpha=1 / 14, adjust=False).mean()
    pdi = 100 * plus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr_s.replace(0, np.nan)
    mdi = 100 * minus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr_s.replace(0, np.nan)
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    df["adx14"] = dx.ewm(alpha=1 / 14, adjust=False).mean()

    df["ema20"] = c.ewm(span=20, adjust=False).mean()
    df["ema50"] = c.ewm(span=50, adjust=False).mean()
    df["ema200"] = c.ewm(span=200, adjust=False).mean() if len(df) >= 200 else np.nan
    df["vol_ma20"] = df["volume"].rolling(20).mean()
    bb_mid = c.rolling(20).mean()
    bb_std = c.rolling(20).std()
    df["bb_width_pct"] = (4 * bb_std / bb_mid) * 100
    df["bb_width_rank"] = df["bb_width_pct"].rolling(288).rank(pct=True) * 100

    df["hour_utc"] = ts.dt.hour.fillna(-1)
    # Gün-çıpalı VWAP (madenci ile aynı: UTC günü başında sıfırlanır)
    if ts.notna().any():
        typical = (df["high"] + df["low"] + df["close"]) / 3
        day = ts.dt.date
        pv = (typical * df["volume"]).groupby(day).cumsum()
        vv = df["volume"].groupby(day).cumsum()
        df["vwap_day"] = (pv / vv.replace(0, np.nan)).values
    else:
        df["vwap_day"] = np.nan
    return df


def _event_features(df: pd.DataFrame, i: int, lvl_price: float, direction: int,
                    level_kind: str, touches: int, age_bars: int,
                    attempts: int = 0) -> Dict[str, float]:
    row = df.iloc[i]
    atr = float(row["atr14"]) or 1e-9
    o = float(row["open"]) if not math.isnan(float(row["open"] or np.nan)) else float(row["close"])
    h, l, c = float(row["high"]), float(row["low"]), float(row["close"])
    rng = max(h - l, 1e-9)
    body = abs(c - o)
    wick_against = (h - max(o, c)) if direction > 0 else (min(o, c) - l)
    vol_ma = float(row["vol_ma20"]) if not math.isnan(float(row["vol_ma20"] or np.nan)) else 0.0
    closes = df["close"].values
    approach = (c - closes[i - 6]) / atr if i >= 6 else 0.0

    def _nz(v: float) -> float:
        return float(v) if v is not None and not math.isnan(float(v)) else float("nan")

    ema200 = _nz(row["ema200"])
    return {
        # volume=0 aktif piyasada veri artefaktıdır (oluşmakta olan bar) — NaN,
        # yoksa "sakin imza" (vol_ratio≤1) kuralları yanlış eşleşir.
        "vol_ratio": (float(row["volume"]) / vol_ma
                      if (vol_ma > 0 and float(row["volume"]) > 0) else float("nan")),
        "rsi14": _nz(row["rsi14"]),
        "adx14": _nz(row["adx14"]),
        "atr_pct": atr / c * 100,
        "pen_atr": abs(c - lvl_price) / atr,
        "body_ratio": body / rng,
        "wick_against_atr": wick_against / atr,
        "dist_ema200_atr": (c - ema200) / atr if not math.isnan(ema200) else float("nan"),
        "ema50_side": 1.0 if c > _nz(row["ema50"]) else 0.0,
        "with_ema200_trend": (1.0 if (c - ema200) * direction > 0 else 0.0) if not math.isnan(ema200) else float("nan"),
        "approach_speed_atr": approach * direction,
        "bb_width_rank": _nz(row["bb_width_rank"]),
        "touches": float(touches),
        "level_age_bars": float(age_bars),
        "hour_utc": float(row["hour_utc"]),
        "ny_session": 1.0 if 13 <= int(row["hour_utc"]) < 21 else 0.0,
        "is_channel": 1.0 if level_kind.startswith("channel") else 0.0,
        "prebreak_range_atr": ((df["high"].values[i - 24:i].max()
                                - df["low"].values[i - 24:i].min()) / atr) if i >= 24 else float("nan"),
        "vol_buildup": (float(df["volume"].values[i - 3:i].mean()) / vol_ma)
                       if (i >= 3 and vol_ma > 0) else float("nan"),
        "ema50_slope_atr": ((float(df["ema50"].iloc[i]) - float(df["ema50"].iloc[i - 12]))
                            / atr * direction) if i >= 12 else float("nan"),
        "vwap_dist_atr": ((c - float(row["vwap_day"])) / atr * direction)
                         if not math.isnan(float(row.get("vwap_day") or np.nan)) else float("nan"),
        "attempts": float(attempts),
    }


# ─── Taze kırılım tespiti (madenci ile aynı causal mantık) ───────────────────

def _detect_recent_breakout(df: pd.DataFrame) -> tuple:
    """Penceredeki seviyeleri kur; (en taze kırılım | None, seviye özeti) döndür.

    Seviye özeti panel için: fiyatın üstündeki en yakın direnç, altındaki en
    yakın destek (dokunuş/yaş bilgisiyle) + geçerliyse kanal sınırları.
    """
    highs, lows = df["high"].values, df["low"].values
    n = len(df)

    ph: Dict[int, float] = {}
    pl: Dict[int, float] = {}
    for i in range(PIVOT_W, n - PIVOT_W):
        seg_h = highs[i - PIVOT_W:i + PIVOT_W + 1]
        if highs[i] == seg_h.max() and (seg_h == highs[i]).sum() == 1:
            ph[i + PIVOT_W] = float(highs[i])
        seg_l = lows[i - PIVOT_W:i + PIVOT_W + 1]
        if lows[i] == seg_l.min() and (seg_l == lows[i]).sum() == 1:
            pl[i + PIVOT_W] = float(lows[i])

    res: List[dict] = []
    sup: List[dict] = []
    latest: Optional[dict] = None
    scan_from = max(CH_WIN, PIVOT_W * 2 + 1, 30)

    for i in range(scan_from, n):
        atr = df["atr14"].iloc[i]
        if not atr or math.isnan(atr) or atr <= 0:
            continue
        tol = CLUSTER_TOL_ATR * atr
        if i in ph:
            p = ph[i]
            for lv in res:
                if abs(lv["price"] - p) <= tol:
                    lv["price"] = (lv["price"] * lv["touches"] + p) / (lv["touches"] + 1)
                    lv["touches"] += 1
                    break
            else:
                res.append({"price": p, "kind": "resistance", "touches": 1,
                            "born": i, "last_ev": -10_000})
        if i in pl:
            p = pl[i]
            for lv in sup:
                if abs(lv["price"] - p) <= tol:
                    lv["price"] = (lv["price"] * lv["touches"] + p) / (lv["touches"] + 1)
                    lv["touches"] += 1
                    break
            else:
                sup.append({"price": p, "kind": "support", "touches": 1,
                            "born": i, "last_ev": -10_000})

        c_prev, c_now = df["close"].iloc[i - 1], df["close"].iloc[i]

        for lv in res + sup:
            if lv["touches"] < MIN_TOUCHES or i - lv["last_ev"] < LEVEL_COOLDOWN:
                continue
            if abs(c_now - lv["price"]) > 3 * atr:
                continue
            direction = 0
            if lv["kind"] == "resistance" and c_prev <= lv["price"] and c_now > lv["price"] + PEN_MIN_ATR * atr:
                direction = +1
            elif lv["kind"] == "support" and c_prev >= lv["price"] and c_now < lv["price"] - PEN_MIN_ATR * atr:
                direction = -1
            if direction == 0:
                continue
            lv["last_ev"] = i
            prior_attempts = lv.get("attempts", 0)
            lv["attempts"] = prior_attempts + 1
            if n - 1 - i < FRESH_BARS:
                latest = {"idx": i, "bars_ago": n - 1 - i, "direction": direction,
                          "level_kind": lv["kind"], "level_price": float(lv["price"]),
                          "touches": lv["touches"], "age_bars": i - lv["born"],
                          "attempts": prior_attempts}

        # Kanal kırılımı — yalnızca taze pencerede hesapla (maliyet)
        if n - 1 - i < FRESH_BARS and i >= CH_WIN:
            y = df["close"].values[i - CH_WIN:i]
            x = np.arange(CH_WIN, dtype=float)
            slope, intercept = np.polyfit(x, y, 1)
            fit = slope * x + intercept
            resid = y - fit
            ss_tot = float(((y - y.mean()) ** 2).sum())
            r2 = 1 - float((resid ** 2).sum()) / ss_tot if ss_tot > 0 else 0.0
            if r2 >= CH_R2_MIN:
                std = float(resid.std())
                center = slope * CH_WIN + intercept
                upper, lower = center + CH_K * std, center - CH_K * std
                if c_prev <= upper and c_now > upper + PEN_MIN_ATR * atr:
                    latest = {"idx": i, "bars_ago": n - 1 - i, "direction": +1,
                              "level_kind": "channel_upper", "level_price": float(upper),
                              "touches": 0, "age_bars": CH_WIN, "attempts": 0}
                elif c_prev >= lower and c_now < lower - PEN_MIN_ATR * atr:
                    latest = {"idx": i, "bars_ago": n - 1 - i, "direction": -1,
                              "level_kind": "channel_lower", "level_price": float(lower),
                              "touches": 0, "age_bars": CH_WIN, "attempts": 0}

    # ── Seviye özeti (panel): en yakın direnç/destek + kanal ────────────────
    last_close = float(df["close"].iloc[-1])
    last_atr = float(df["atr14"].iloc[-1]) or 1e-9
    snapshot: Dict[str, Any] = {"price": last_close, "atr": last_atr}

    def _nearest(pool: List[dict], above: bool) -> Optional[dict]:
        cands = [lv for lv in pool
                 if lv["touches"] >= MIN_TOUCHES
                 and ((lv["price"] > last_close) if above else (lv["price"] < last_close))
                 and abs(lv["price"] - last_close) < 12 * last_atr]
        if not cands:
            return None
        lv = min(cands, key=lambda x: abs(x["price"] - last_close))
        dist = lv["price"] - last_close
        return {"price": round(lv["price"], 2), "touches": lv["touches"],
                "age_bars": n - 1 - lv["born"], "attempts": lv.get("attempts", 0),
                "distance_points": round(dist, 2),
                "distance_atr": round(dist / last_atr, 2),
                "distance_pct": round(dist / last_close * 100, 3)}

    snapshot["resistance"] = _nearest(res, above=True)
    snapshot["support"] = _nearest(sup, above=False)

    if n - 1 >= CH_WIN:      # son bar için kanal sınırları
        y = df["close"].values[n - 1 - CH_WIN:n - 1]
        x = np.arange(CH_WIN, dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        resid = y - (slope * x + intercept)
        ss_tot = float(((y - y.mean()) ** 2).sum())
        r2 = 1 - float((resid ** 2).sum()) / ss_tot if ss_tot > 0 else 0.0
        if r2 >= CH_R2_MIN:
            std = float(resid.std())
            center = slope * CH_WIN + intercept
            snapshot["channel"] = {
                "upper": round(center + CH_K * std, 2),
                "lower": round(center - CH_K * std, 2),
                "slope_atr_per_bar": round(slope / last_atr, 4), "r2": round(r2, 3),
            }

    return latest, snapshot


def _tail_candles(df: pd.DataFrame, n: int = 48) -> List[dict]:
    """Panel grafiği için son n bar (dedektörle AYNI 5m veri — hizalama garantili)."""
    t = df.iloc[-n:]
    return [{"o": round(float(r.open), 2), "h": round(float(r.high), 2),
             "l": round(float(r.low), 2), "c": round(float(r.close), 2)}
            for r in t.itertuples()]


def _pre_breakout_forecast(df: pd.DataFrame, snapshot: dict,
                           payload: dict, base: float) -> Dict[str, Any]:
    """"ŞİMDİ kırılsa" ön-tahmini — iki yön için ayrı (panel göstergeleri).

    Hipotetik kırılım özellikleri: mevcut bağlam (hacim, RSI, VWAP mesafesi,
    yaklaşma hızı, EMA eğimi...) + minimal penetrasyon varsayımı. Kırılım mumu
    henüz yok — mum-karakteri özellikleri son bardan yaklaşıktır; UI bunu
    "yaklaşık ön-tahmin" olarak sunmalıdır.
    """
    out: Dict[str, Any] = {}
    n = len(df)
    for side, key, dirn in (("up", "resistance", 1), ("down", "support", -1)):
        lv = snapshot.get(key)
        kind = key
        if lv is None and snapshot.get("channel"):
            ch = snapshot["channel"]
            price = ch["upper"] if dirn > 0 else ch["lower"]
            lv = {"price": price, "touches": 0, "age_bars": CH_WIN, "attempts": 0,
                  "distance_points": round(price - snapshot["price"], 2),
                  "distance_atr": round((price - snapshot["price"]) / snapshot["atr"], 2),
                  "distance_pct": round((price - snapshot["price"]) / snapshot["price"] * 100, 3)}
            kind = "channel_upper" if dirn > 0 else "channel_lower"
        if lv is None:
            out[side] = None
            continue
        try:
            feat = _event_features(df, n - 1, float(lv["price"]), dirn, kind,
                                   lv.get("touches", 0), lv.get("age_bars", 0),
                                   attempts=lv.get("attempts", 0))
            feat["pen_atr"] = PEN_MIN_ATR          # hipotetik minimal kırılım
            score, genuine = _breakout_score(feat, payload)
            fake = round(100.0 - genuine, 1) if genuine is not None else round(base, 1)
            out[side] = {"level_kind": kind, "level_price": lv["price"],
                         "distance_points": lv.get("distance_points"),
                         "distance_atr": lv.get("distance_atr"),
                         "distance_pct": lv.get("distance_pct"),
                         "breakout_score": score,
                         "fake_probability": fake,
                         "genuine_probability": genuine if genuine is not None else round(100 - base, 1)}
        except Exception:
            out[side] = None
    return out


# ─── Kural eşleme + skorlama ─────────────────────────────────────────────────

def _rule_matches(rule: dict, feat: Dict[str, float]) -> bool:
    for cond in rule.get("conditions") or []:
        v = feat.get(cond["feature"])
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return False
        if cond["op"] == "<=" and not v <= cond["threshold"]:
            return False
        if cond["op"] == ">=" and not v >= cond["threshold"]:
            return False
    return True


def _pooled_rate(rule: dict) -> float:
    n = rule["train_n"] + rule["test_n"]
    return (rule["train_fake_rate"] * rule["train_n"]
            + rule["test_fake_rate"] * rule["test_n"]) / n if n else 0.0


def _breakout_score(feat: Dict[str, float], payload: dict) -> tuple[Optional[int], Optional[float]]:
    """Birleşik kırılım skoru + kova-kalibrasyonlu GERÇEK olasılığı (pooled).

    Returns:
        (score, genuine_probability) — skor konfigürasyonu yoksa (None, None).
    """
    cfg = payload.get("score") or {}
    comps = cfg.get("components") or []
    buckets = cfg.get("buckets") or []
    if not comps or not buckets:
        return None, None
    score = 0
    for c in comps:
        v = feat.get(c["feature"])
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        hit = v <= c["threshold"] if c["op"] == "<=" else v >= c["threshold"]
        if hit:
            score += int(c["weight"])
    for b in buckets:
        if b["min_score"] <= score <= b["max_score"]:
            n = (b.get("train_n") or 0) + (b.get("test_n") or 0)
            if n and b.get("train_genuine") is not None and b.get("test_genuine") is not None:
                pooled = (b["train_genuine"] * b["train_n"]
                          + b["test_genuine"] * b["test_n"]) / n
                return score, round(pooled, 1)
            return score, None
    return score, None


def _confirmation_status(df: pd.DataFrame, bo: dict, payload: dict) -> dict:
    """Taze kırılımın teyit durumu (sonraki-bar kapanışı + retest) + OOS bağlamı.

    NOT: madencilik teyitli girişlerin de −EV olduğunu gösterdi — teyit burada
    GİRİŞ sinyali değil, ELEME filtresidir (teyitsiz kırılımın gerçekliği %13).
    """
    idx = int(bo["idx"])
    dirn = 1 if bo["direction"] in (1, "up") else -1
    lvl = float(bo["level_price"])
    atr = float(df["atr14"].iloc[idx]) or 1e-9
    n = len(df)
    out: Dict[str, Any] = {}

    if idx + 1 < n:
        cj = float(df["close"].iloc[idx + 1])
        out["next_bar_confirm"] = bool((cj - lvl) * dirn > 0)
    else:
        out["next_bar_confirm"] = None   # sonraki bar henüz kapanmadı

    retest = "pending"
    for k in range(idx + 1, min(idx + 13, n)):
        near = (float(df["low"].iloc[k]) <= lvl + 0.20 * atr) if dirn > 0 \
            else (float(df["high"].iloc[k]) >= lvl - 0.20 * atr)
        if not near:
            continue
        retest = "hold" if (float(df["close"].iloc[k]) - lvl) * dirn >= 0 else "fail"
        break
    else:
        if n - 1 - idx >= 12:
            retest = "none"
    out["retest"] = retest

    cond = (payload.get("confirmation") or {}).get("conditional") or {}
    out["oos_context"] = {
        "confirm_no_genuine": (cond.get("confirm_no") or {}).get("orig_genuine"),
        "confirm_yes_genuine": (cond.get("confirm_yes") or {}).get("orig_genuine"),
        "retest_fail_genuine": (cond.get("retest_fail") or {}).get("orig_genuine"),
        "note": "Teyitli girişler dahi −EV (OOS) — teyit eleme filtresidir, giriş sinyali değil.",
    }
    return out


def _rule_str(rule: dict) -> str:
    return " VE ".join(f"{c['feature']} {c['op']} {c['threshold']}"
                       for c in rule.get("conditions") or [])


def assess_bars(bars: Sequence[dict], symbol: str = "NDX.INDX") -> Dict[str, Any]:
    """SAF ÇEKİRDEK: 5m barlardan taze kırılım + sahte-kırılım değerlendirmesi.

    Args:
        bars: 5m OHLCV dict listesi (open opsiyonel; time epoch-s veya timestamp ISO).
        symbol: Kural setinin sembol kontrolü için (kurallar sembole özgü).

    Returns:
        {"status": "no_breakout" | "assessed" | "no_rules" | "unavailable", ...}
        "assessed" ise: breakout{}, fake_probability, verdict, matched_rules[],
        base_fake_rate. Asla exception fırlatmaz (fail-open).
    """
    try:
        payload = load_rules(symbol)
        if not payload:
            return {"status": "no_rules"}
        if payload.get("symbol") != symbol:
            return {"status": "no_rules", "note": f"kurallar {payload.get('symbol')} için, {symbol} değil"}

        df = _prep_df(bars)
        if df is None:
            return {"status": "unavailable", "note": "yetersiz bar"}

        bo, levels = _detect_recent_breakout(df)
        base = float(payload.get("base_fake_rate_test") or payload.get("base_fake_rate_train") or 66.0)
        pre_forecast = _pre_breakout_forecast(df, levels, payload, base)
        if bo is None:
            return {"status": "no_breakout", "base_fake_rate": base,
                    "levels": levels, "pre_forecast": pre_forecast,
                    "candles": _tail_candles(df)}

        feat = _event_features(df, bo["idx"], bo["level_price"], bo["direction"],
                               bo["level_kind"], bo["touches"], bo["age_bars"],
                               attempts=bo.get("attempts", 0))
        matched = [r for r in _quality_rules(payload) if _rule_matches(r, feat)]

        # 1) Skor-kalibrasyonlu olasılık, 2) kural eşleşmesi, 3) v3: +1-bar LGBM dedektörü
        score, genuine_prob = _breakout_score(feat, payload)
        prob = base
        if genuine_prob is not None:
            prob = 100.0 - genuine_prob
        if matched:
            best = max(matched, key=lambda r: abs(r.get("test_lift_pp", 0)))
            rule_prob = _pooled_rate(best)
            # Konservatif birleşim: iki kanıt kanalından yüksek sahte-olasılığı
            prob = max(prob, rule_prob) if best.get("test_lift_pp", 0) > 0 else min(prob, rule_prob)

        detector = _run_detector(df, bo, feat, payload)
        det_call = (detector or {}).get("call")
        if detector and detector.get("p_fake") is not None:
            # Doğrulanmış dedektör konuştuysa olasılıkların birincil kaynağı odur
            prob = float(detector["p_fake"])
            genuine_prob = round(100.0 - prob, 1)

        if det_call == "fake" or (det_call not in ("genuine",) and prob >= 75.0):
            verdict = "likely_fake"
        elif det_call == "genuine" or prob <= 55.0:
            verdict = "lean_genuine"
        else:
            verdict = "uncertain"

        # Öneri (v3): dedektör çağrısı > skor/kural kanıtı
        if det_call == "fake" and score is not None and score <= -2:
            recommendation = "fade_candidate"        # iki kanal aynı yönde — en güçlü ters-yön kanıtı
        elif det_call == "fake":
            recommendation = "avoid_breakout_direction"
        elif det_call == "genuine":
            recommendation = "breakout_leaning_genuine"   # dedektör GERÇEK çağrısı (OOS %83)
        elif score is not None and score <= -2 and prob >= 80.0:
            recommendation = "fade_candidate"
        elif prob >= 75.0:
            recommendation = "avoid_breakout_direction"
        elif score is not None and score >= 2:
            recommendation = "breakout_leaning_genuine"
        else:
            recommendation = "neutral_no_trade"

        confirmation = _confirmation_status(df, {**bo}, payload)

        return {
            "status": "assessed",
            "engine_version": payload.get("version", 1),
            "levels": levels,
            "pre_forecast": pre_forecast,
            "candles": _tail_candles(df),
            "breakout": {**bo, "direction": "up" if bo["direction"] > 0 else "down",
                         "bar_offset_from_end": len(df) - 1 - int(bo["idx"])},
            "features": {k: (round(v, 3) if isinstance(v, float) and not math.isnan(v) else None)
                         for k, v in feat.items()},
            "base_fake_rate": round(base, 1),
            "breakout_score": score,
            "genuine_probability": genuine_prob,
            "fake_probability": round(prob, 1),
            "verdict": verdict,
            "recommendation": recommendation,
            "detector": detector,
            "confirmation": confirmation,
            "matched_rules": [{"rule": _rule_str(r), "group": r["group"],
                               "pooled_fake_rate": round(_pooled_rate(r), 1),
                               "test_lift_pp": r.get("test_lift_pp")}
                              for r in sorted(matched, key=lambda r: -abs(r.get("test_lift_pp", 0)))[:5]],
            "note": ("NDX 5m: kırılımların ~%66'sı sahte; kırılım-yönlü TÜM giriş varyantları −EV "
                     "(teyitli dahi). Edge fade tarafında (skor≤−2 → OOS %87 sahte)."),
        }
    except Exception as exc:
        logger.warning("[fakeout] assess_bars hata (fail-open): %s", exc)
        return {"status": "unavailable", "note": str(exc)[:200]}


# ─── Async sarmalayıcı (backend içi kullanım) ────────────────────────────────

async def assess_symbol(symbol: str) -> Dict[str, Any]:
    """DataHub'dan 5m mumları çekip assess_bars'ı çalıştırır (60s TTL cache)."""
    now = time.monotonic()
    cached = _assess_cache.get(symbol)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]
    try:
        # data_fetcher (DataHub ham) kullanılır — market_data_service timestamp'i
        # düşürüyor, o yolda saat/VWAP özellikleri hesaplanamıyordu (2026-07-16 fix).
        from services.data_fetcher import fetch_ohlc_data
        candles = await fetch_ohlc_data(symbol, timeframe="5m", limit=400)
        result = assess_bars(candles or [], symbol=symbol)
    except Exception as exc:
        logger.warning("[fakeout] assess_symbol hata (fail-open, %s): %s", symbol, exc)
        result = {"status": "unavailable", "note": str(exc)[:200]}
    _assess_cache[symbol] = (now, result)
    return result
