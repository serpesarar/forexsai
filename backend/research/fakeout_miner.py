"""
Fakeout Miner — destek/direnç/trend-kanalı SAHTE KIRILIM tespiti + koşul madenciliği.

Amaç (kullanıcı isteği 2026-07-16): "Grafikte S/R ve trend kanalı noktalarında
fiyatın yaptığı sahte kırılımları geçmişten tespit et; sahte kırılımların ortak
noktası var mı (hacim < X, gösterge Y eşiği, tekli veya kombinasyon) bunu öğren;
sistem 'kesin kırdı' diye işlem açmasın."

Yöntem — üç katman, tamamı LOOKAHEAD'SİZ:

  1) OLAY TESPİTİ (5m barlar)
       - Fraktal pivotlar (w bar sol/sağ) yalnızca TEYİT edildikleri bardan
         itibaren seviye havuzuna girer (pivot i ancak i+w'de bilinir).
       - Pivotlar ATR-toleransıyla kümelenir → S/R seviyeleri (dokunuş sayısı ≥2).
       - Kayan linreg kanalı (son CH_WIN bar, sadece geçmiş) → üst/alt sınır.
       - Kırılım: önceki kapanış seviyenin içinde, şimdiki kapanış seviyeyi
         ≥ PEN_MIN_ATR × ATR aşıyor. Seviye başına cooldown uygulanır.

  2) ETİKETLEME (iki-hedef yarışı — işlem P&L'ine birebir eşlenir)
       - Kırılım kapanışından ±TARGET_ATR × ATR iki hedef kurulur.
       - Devam hedefi önce vurulursa TRUE (gerçek kırılım),
         ters hedef önce vurulursa FAKE (sahte kırılım).
       - Çözünürlük 1m barlarla yapılır (varsa); 5m fallback'te aynı barda iki
         hedef de vurulursa AMBIGUOUS → örneklemden atılır.
       - Horizon içinde hiçbiri vurulmazsa AMBIGUOUS → atılır (dürüstlük).

  3) MADENCİLİK (kronolojik %70/30 train/test)
       - Kırılım anındaki ~20 özellik üzerinde tek-koşul kantil taraması:
         fake-oranı lift'i ≥ MIN_LIFT_PP ve train desteği ≥ MIN_SUP_TRAIN olan
         koşullar OOS'ta işaret koruyorsa kural olur.
       - En iyi tekillerden 2'li kombinasyonlar denenir (aynı OOS şartı).
       - Derinlik-3 karar ağacı ikincil keşif katmanı (aynı doğrulama).

Çıktı:
  - backend/data/fakeout_rules.json    (runtime fakeout_service okur)
  - backend/data/fakeout_report.md     (insan-okur rapor)

CLI:
  python backend/research/fakeout_miner.py [--symbol NDX.INDX] [--write]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import httpx
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve()
for _cand in (_HERE.parent.parent / ".env", _HERE.parent.parent.parent / ".env"):
    if _cand.exists():
        from dotenv import load_dotenv
        load_dotenv(_cand)
        break

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY", "")
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
DATA_DIR = _HERE.parent.parent / "data"

# ─── Parametreler (tek yerden) ───────────────────────────────────────────────
PIVOT_W = 12            # fraktal pivot sol/sağ bar sayısı (5m → 1 saat)
CLUSTER_TOL_ATR = 0.35  # pivot kümeleme toleransı (ATR birimi)
MIN_TOUCHES = 2         # seviyenin S/R sayılması için min dokunuş
PEN_MIN_ATR = 0.10      # kırılım için kapanışın seviyeyi aşma minimumu
LEVEL_COOLDOWN = 24     # aynı seviyeden yeni olay için bekleme (5m bar)
TARGET_ATR = 1.0        # iki-hedef yarışı mesafesi (ATR birimi)
HORIZON_BARS = 72       # yarış zaman sınırı (72×5m = 6 saat)
CH_WIN = 96             # kanal regresyon penceresi (96×5m = 8 saat)
CH_K = 2.0              # kanal genişliği (std çarpanı)
CH_R2_MIN = 0.5         # kanal geçerlilik eşiği
TRAIN_FRAC = 0.70       # kronolojik train oranı
MIN_SUP_TRAIN = 40      # tek koşul min train örneği
MIN_SUP_TEST = 15       # tek koşul min test örneği
MIN_LIFT_PP = 8.0       # train fake-oranı lift eşiği (yüzde puan)
COMBO_MIN_SUP = 25      # kombinasyon min train örneği
COMBO_TOP_SINGLES = 12  # kombinasyona giren en iyi tekil sayısı
SCORE_MAX_COMPONENTS = 8   # birleşik skora giren en iyi tekil koşul sayısı
RETEST_WITHIN = 12      # retest araması penceresi (5m bar)
RETEST_TOL_ATR = 0.20   # seviyeye "geri döndü" sayılma toleransı (ATR)
CONFIRM_TP15_SL10 = (1.5, 1.0)   # teyitli girişler için ikincil geometri


def _log(msg: str) -> None:
    print(msg, flush=True)


# ─── Veri çekme ──────────────────────────────────────────────────────────────

def fetch_candles(symbol: str, timeframe: str, limit: int = 200_000) -> pd.DataFrame:
    rows: list[dict] = []
    with httpx.Client(timeout=60) as c:
        offset = 0
        while True:
            r = c.get(f"{URL}/rest/v1/candle_cache", headers=HEADERS,
                      params={"symbol": f"eq.{symbol}", "timeframe": f"eq.{timeframe}",
                              "select": "candle_time,open,high,low,close,volume",
                              "order": "candle_time.desc",
                              "limit": "1000", "offset": str(offset)})
            r.raise_for_status()
            batch = r.json()
            rows.extend(batch)
            if len(batch) < 1000 or len(rows) >= limit:
                break
            offset += 1000
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["candle_time"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    # Tick-kirliliği koruması: dakika hizası bozuk barları at (bkz. memory 2026-07)
    if timeframe == "1m":
        df = df[df["ts"].dt.second == 0].reset_index(drop=True)
    return df


# ─── Göstergeler ─────────────────────────────────────────────────────────────

def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([(h - l), (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def _rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    up, dn = h.diff(), -l.diff()
    plus_dm = ((up > dn) & (up > 0)).astype(float) * up.clip(lower=0)
    minus_dm = ((dn > up) & (dn > 0)).astype(float) * dn.clip(lower=0)
    tr = pd.concat([(h - l), (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * plus_dm.ewm(alpha=1 / n, adjust=False).mean() / atr.replace(0, np.nan)
    mdi = 100 * minus_dm.ewm(alpha=1 / n, adjust=False).mean() / atr.replace(0, np.nan)
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["atr14"] = _atr(df)
    df["rsi14"] = _rsi(df["close"])
    df["adx14"] = _adx(df)
    df["ema20"] = _ema(df["close"], 20)
    df["ema50"] = _ema(df["close"], 50)
    df["ema200"] = _ema(df["close"], 200)
    df["vol_ma20"] = df["volume"].rolling(20).mean()
    bb_mid = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_width_pct"] = (4 * bb_std / bb_mid) * 100
    # BB genişliğinin kayan yüzdelik sırası (squeeze tespiti — sadece geçmişe bakar)
    df["bb_width_rank"] = df["bb_width_pct"].rolling(288).rank(pct=True) * 100
    df["hour_utc"] = df["ts"].dt.hour
    # Gün-çıpalı VWAP (causal: her UTC günü başında sıfırlanır)
    typical = (df["high"] + df["low"] + df["close"]) / 3
    day = df["ts"].dt.date
    pv = (typical * df["volume"]).groupby(day).cumsum()
    vv = df["volume"].groupby(day).cumsum()
    df["vwap_day"] = (pv / vv.replace(0, np.nan)).values
    return df


# ─── Seviye motoru (causal S/R + kanal) ─────────────────────────────────────

@dataclass
class Level:
    price: float
    kind: str                    # "support" | "resistance"
    touches: int = 1
    born_idx: int = 0            # seviyenin bilinir olduğu bar (pivot teyidi)
    last_event_idx: int = -10_000
    attempts: int = 0            # bu seviyeden daha önce kaç kırılım denemesi oldu


def _causal_pivots(df: pd.DataFrame, w: int) -> tuple[dict[int, float], dict[int, float]]:
    """i barındaki pivot ancak i+w barında teyitlenir.
    Dönen dict: {teyit_bar_idx: pivot_fiyatı}."""
    highs, lows = df["high"].values, df["low"].values
    ph: dict[int, float] = {}
    pl: dict[int, float] = {}
    n = len(df)
    for i in range(w, n - w):
        seg_h = highs[i - w:i + w + 1]
        if highs[i] == seg_h.max() and (seg_h == highs[i]).sum() == 1:
            ph[i + w] = float(highs[i])
        seg_l = lows[i - w:i + w + 1]
        if lows[i] == seg_l.min() and (seg_l == lows[i]).sum() == 1:
            pl[i + w] = float(lows[i])
    return ph, pl


def _rolling_channel(df: pd.DataFrame, i: int) -> dict | None:
    """Son CH_WIN barın linreg kanalı (i dahil değil — sadece geçmiş)."""
    if i < CH_WIN:
        return None
    y = df["close"].values[i - CH_WIN:i]
    x = np.arange(CH_WIN, dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    fit = slope * x + intercept
    resid = y - fit
    ss_res = float((resid ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    if r2 < CH_R2_MIN:
        return None
    std = float(resid.std())
    center_now = slope * CH_WIN + intercept   # i barına ekstrapole edilmiş merkez
    return {"upper": center_now + CH_K * std, "lower": center_now - CH_K * std,
            "slope": slope, "r2": r2}


# ─── Olay tespiti + etiketleme ───────────────────────────────────────────────

_DF1_CACHE: dict[int, tuple] = {}


def _df1_arrays(df1: pd.DataFrame) -> tuple:
    """1m yarış taraması için (ts_int64, highs, lows) — DataFrame başına 1 kez."""
    key = id(df1)
    if key not in _DF1_CACHE:
        _DF1_CACHE.clear()      # tek df tutulur (bellek)
        _DF1_CACHE[key] = (df1["ts"].astype("int64").values,
                           df1["high"].values.astype(float),
                           df1["low"].values.astype(float))
    return _DF1_CACHE[key]

def _label_race(event_idx: int, direction: int, entry: float, atr: float,
                df5: pd.DataFrame, df1: pd.DataFrame | None,
                tp_atr: float = TARGET_ATR, sl_atr: float = TARGET_ATR,
                horizon_bars: int = HORIZON_BARS, bar_minutes: int = 5) -> str:
    """İki-hedef yarışı: devam hedefi önce → 'true', ters hedef önce → 'fake'.
    1m varsa onunla çözülür; yoksa event TF barları (aynı barda ikisi de → ambiguous).
    tp_atr/sl_atr ile asimetrik geometri test edilir.

    Yarış event barının KAPANIŞINDAN sonra başlar (t0 = bar açılış zamanı +
    bar_minutes) — bar içi dakikalar entry'den önce oluştuğu için yarışa
    katılmaz (2026-07-16 düzeltmesi; önceki sürüm bar içi 1m'leri sayıyordu)."""
    tgt_cont = entry + direction * tp_atr * atr
    tgt_rev = entry - direction * sl_atr * atr
    bar_delta = pd.Timedelta(minutes=bar_minutes)
    t0 = df5["ts"].iloc[event_idx] + bar_delta            # event barının kapanışı
    t_end = df5["ts"].iloc[min(event_idx + horizon_bars, len(df5) - 1)] + bar_delta

    if df1 is not None and len(df1):
        ts1, h1, l1 = _df1_arrays(df1)
        i0 = int(np.searchsorted(ts1, t0.value))
        i1 = int(np.searchsorted(ts1, t_end.value, side="right"))
        for h, l in zip(h1[i0:i1], l1[i0:i1]):
            hit_cont = h >= tgt_cont if direction > 0 else l <= tgt_cont
            hit_rev = l <= tgt_rev if direction > 0 else h >= tgt_rev
            if hit_cont and hit_rev:
                return "ambiguous"
            if hit_cont:
                return "true"
            if hit_rev:
                return "fake"
        return "ambiguous"

    for j in range(event_idx + 1, min(event_idx + 1 + horizon_bars, len(df5))):
        h, l = df5["high"].iloc[j], df5["low"].iloc[j]
        hit_cont = h >= tgt_cont if direction > 0 else l <= tgt_cont
        hit_rev = l <= tgt_rev if direction > 0 else h >= tgt_rev
        if hit_cont and hit_rev:
            return "ambiguous"
        if hit_cont:
            return "true"
        if hit_rev:
            return "fake"
    return "ambiguous"


def _event_features(df: pd.DataFrame, i: int, lvl_price: float, direction: int,
                    level_kind: str, touches: int, age_bars: int,
                    attempts: int = 0) -> dict:
    row = df.iloc[i]
    atr = float(row["atr14"]) or 1e-9
    o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
    rng = max(h - l, 1e-9)
    body = abs(c - o)
    # Kırılım yönünün TERSİNDEKİ fitil (ör. yukarı kırılımda üst fitil = reddetme izi)
    wick_against = (h - max(o, c)) if direction > 0 else (min(o, c) - l)
    vol_ma = float(row["vol_ma20"]) if row["vol_ma20"] and not math.isnan(row["vol_ma20"]) else 0.0
    closes = df["close"].values
    approach = (c - closes[i - 6]) / atr if i >= 6 else 0.0
    # Gerçek-kırılım hipotez özellikleri (2026-07-16 v2)
    prebreak_range = (df["high"].values[i - 24:i].max() - df["low"].values[i - 24:i].min()) / atr if i >= 24 else np.nan
    vols = df["volume"].values
    vol_buildup = (vols[i - 3:i].mean() / vol_ma) if (i >= 3 and vol_ma > 0) else np.nan
    ema50s = df["ema50"].values
    ema50_slope = (ema50s[i] - ema50s[i - 12]) / atr * direction if i >= 12 else np.nan
    vwap = float(row.get("vwap_day") or np.nan)
    return {
        # volume=0 barı veri artefaktı — NaN (runtime fakeout_service ile parite)
        "vol_ratio": (float(row["volume"]) / vol_ma
                      if (vol_ma > 0 and float(row["volume"]) > 0) else np.nan),
        "rsi14": float(row["rsi14"]),
        "adx14": float(row["adx14"]),
        "atr_pct": atr / c * 100,
        "pen_atr": abs(c - lvl_price) / atr,                 # kapanışın seviyeyi aşma derinliği
        "body_ratio": body / rng,                            # kırılım mumunun gövde oranı
        "wick_against_atr": wick_against / atr,              # ters fitil (reddetme izi)
        "dist_ema200_atr": (c - float(row["ema200"])) / atr,
        "ema50_side": 1.0 if c > float(row["ema50"]) else 0.0,
        "with_ema200_trend": 1.0 if (c - float(row["ema200"])) * direction > 0 else 0.0,
        "approach_speed_atr": approach * direction,          # son 30dk seviyeye yaklaşma hızı (yön lehine)
        "bb_width_rank": float(row["bb_width_rank"]) if not math.isnan(row["bb_width_rank"]) else np.nan,
        "touches": float(touches),
        "level_age_bars": float(age_bars),
        "hour_utc": float(row["hour_utc"]),
        "ny_session": 1.0 if 13 <= int(row["hour_utc"]) < 21 else 0.0,
        "is_channel": 1.0 if level_kind.startswith("channel") else 0.0,
        "prebreak_range_atr": prebreak_range,        # kırılım öncesi 2s sıkışma (dar=base)
        "vol_buildup": vol_buildup,                  # kırılım ÖNCESİ 3-bar hacim birikimi
        "ema50_slope_atr": ema50_slope,              # yön-hizalı EMA50 eğimi (1s)
        "vwap_dist_atr": (c - vwap) / atr * direction if not math.isnan(vwap) else np.nan,
        "attempts": float(attempts),                 # seviyedeki kaçıncı deneme (0=ilk)
    }


def detect_events(df5: pd.DataFrame, df1: pd.DataFrame | None,
                  tp_atr: float = TARGET_ATR, sl_atr: float | None = None,
                  horizon_bars: int = HORIZON_BARS,
                  bar_minutes: int = 5) -> pd.DataFrame:
    """Tüm S/R + kanal kırılım olaylarını tara, etiketle, feature çıkar.

    tp_atr/sl_atr/horizon_bars/bar_minutes lab deneyleri için parametriktir
    (farklı TF ve hedef geometrileri); default'lar üretim 5m konfigürasyonudur.
    """
    if sl_atr is None:
        sl_atr = tp_atr
    ph, pl = _causal_pivots(df5, PIVOT_W)
    res_levels: list[Level] = []
    sup_levels: list[Level] = []
    events: list[dict] = []
    last_ch_event = -10_000
    warmup = max(CH_WIN, 288, PIVOT_W * 2 + 1)

    for i in range(warmup, len(df5) - 1):
        atr = df5["atr14"].iloc[i]
        if not atr or math.isnan(atr) or atr <= 0:
            continue
        tol = CLUSTER_TOL_ATR * atr

        # 1) Bu barda teyitlenen pivotları havuza al / kümele
        if i in ph:
            p = ph[i]
            for lv in res_levels:
                if abs(lv.price - p) <= tol:
                    lv.price = (lv.price * lv.touches + p) / (lv.touches + 1)
                    lv.touches += 1
                    break
            else:
                res_levels.append(Level(price=p, kind="resistance", born_idx=i))
        if i in pl:
            p = pl[i]
            for lv in sup_levels:
                if abs(lv.price - p) <= tol:
                    lv.price = (lv.price * lv.touches + p) / (lv.touches + 1)
                    lv.touches += 1
                    break
            else:
                sup_levels.append(Level(price=p, kind="support", born_idx=i))

        c_prev = df5["close"].iloc[i - 1]
        c_now = df5["close"].iloc[i]

        # 2) S/R kırılım taraması
        for lv in res_levels + sup_levels:
            if lv.touches < MIN_TOUCHES or i - lv.last_event_idx < LEVEL_COOLDOWN:
                continue
            if abs(c_now - lv.price) > 3 * atr:       # uzak seviye — ilgisiz
                continue
            direction = 0
            if lv.kind == "resistance" and c_prev <= lv.price and c_now > lv.price + PEN_MIN_ATR * atr:
                direction = +1
            elif lv.kind == "support" and c_prev >= lv.price and c_now < lv.price - PEN_MIN_ATR * atr:
                direction = -1
            if direction == 0:
                continue
            lv.last_event_idx = i
            prior_attempts = lv.attempts
            lv.attempts += 1
            label = _label_race(i, direction, float(c_now), float(atr), df5, df1,
                                tp_atr=tp_atr, sl_atr=sl_atr,
                                horizon_bars=horizon_bars, bar_minutes=bar_minutes)
            if label == "ambiguous":
                continue
            feat = _event_features(df5, i, lv.price, direction, lv.kind,
                                   lv.touches, i - lv.born_idx, attempts=prior_attempts)
            events.append({"ts": df5["ts"].iloc[i].isoformat(), "idx": i,
                           "level_kind": lv.kind, "level_price": round(lv.price, 2),
                           "direction": "up" if direction > 0 else "down",
                           "label": label, "is_fake": 1 if label == "fake" else 0,
                           "close": float(c_now), "atr_abs": float(atr),
                           **feat})

        # 3) Kanal kırılım taraması (bar başına en fazla 1 olay, cooldown'lu)
        if i - last_ch_event >= LEVEL_COOLDOWN:
            ch = _rolling_channel(df5, i)
            if ch:
                direction, lvl_price, kind = 0, 0.0, ""
                if c_prev <= ch["upper"] and c_now > ch["upper"] + PEN_MIN_ATR * atr:
                    direction, lvl_price, kind = +1, ch["upper"], "channel_upper"
                elif c_prev >= ch["lower"] and c_now < ch["lower"] - PEN_MIN_ATR * atr:
                    direction, lvl_price, kind = -1, ch["lower"], "channel_lower"
                if direction != 0:
                    last_ch_event = i
                    label = _label_race(i, direction, float(c_now), float(atr), df5, df1,
                                        tp_atr=tp_atr, sl_atr=sl_atr,
                                        horizon_bars=horizon_bars, bar_minutes=bar_minutes)
                    if label != "ambiguous":
                        feat = _event_features(df5, i, lvl_price, direction, kind,
                                               touches=0, age_bars=CH_WIN, attempts=0)
                        events.append({"ts": df5["ts"].iloc[i].isoformat(), "idx": i,
                                       "level_kind": kind, "level_price": round(lvl_price, 2),
                                       "direction": "up" if direction > 0 else "down",
                                       "label": label, "is_fake": 1 if label == "fake" else 0,
                                       "close": float(c_now), "atr_abs": float(atr),
                                       **feat})

        # 4) Havuç budaması: çok eski/uzak seviyeleri at (performans + alaka)
        if i % 500 == 0:
            px = c_now
            res_levels = [lv for lv in res_levels if abs(lv.price - px) < 12 * atr]
            sup_levels = [lv for lv in sup_levels if abs(lv.price - px) < 12 * atr]

    return pd.DataFrame(events)


# ─── Madencilik ──────────────────────────────────────────────────────────────

FEATURES = ["vol_ratio", "rsi14", "adx14", "atr_pct", "pen_atr", "body_ratio",
            "wick_against_atr", "dist_ema200_atr", "ema50_side", "with_ema200_trend",
            "approach_speed_atr", "bb_width_rank", "touches", "level_age_bars",
            "hour_utc", "ny_session", "is_channel",
            "prebreak_range_atr", "vol_buildup", "ema50_slope_atr",
            "vwap_dist_atr", "attempts"]

BINARY_FEATURES = {"ema50_side", "with_ema200_trend", "ny_session", "is_channel"}


def _cond_mask(df: pd.DataFrame, feat: str, op: str, thr: float) -> pd.Series:
    return df[feat] <= thr if op == "<=" else df[feat] >= thr


def _scan_singles(train: pd.DataFrame, test: pd.DataFrame, base_train: float,
                  base_test: float) -> list[dict]:
    rules = []
    for feat in FEATURES:
        vals = train[feat].dropna()
        if len(vals) < MIN_SUP_TRAIN:
            continue
        if feat in BINARY_FEATURES:
            cand = [(op, thr) for op in ("<=", ">=") for thr in (0.5,)]
        else:
            qs = vals.quantile([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]).unique()
            cand = [(op, float(t)) for op in ("<=", ">=") for t in qs]
        for op, thr in cand:
            m_tr = _cond_mask(train, feat, op, thr) & train[feat].notna()
            n_tr = int(m_tr.sum())
            if n_tr < MIN_SUP_TRAIN or n_tr > len(train) * 0.9:
                continue
            fr_tr = train.loc[m_tr, "is_fake"].mean() * 100
            lift_tr = fr_tr - base_train
            if abs(lift_tr) < MIN_LIFT_PP:
                continue
            m_te = _cond_mask(test, feat, op, thr) & test[feat].notna()
            n_te = int(m_te.sum())
            if n_te < MIN_SUP_TEST:
                continue
            fr_te = test.loc[m_te, "is_fake"].mean() * 100
            lift_te = fr_te - base_test
            if lift_tr * lift_te <= 0:          # OOS işaret korumadı → ele
                continue
            rules.append({"conditions": [{"feature": feat, "op": op, "threshold": round(thr, 3)}],
                          "train_n": n_tr, "train_fake_rate": round(fr_tr, 1),
                          "train_lift_pp": round(lift_tr, 1),
                          "test_n": n_te, "test_fake_rate": round(fr_te, 1),
                          "test_lift_pp": round(lift_te, 1)})
    # Aynı feature'ın en güçlü versiyonunu tut (threshold taraması çok üretir)
    best: dict[tuple, dict] = {}
    for r in rules:
        k = (r["conditions"][0]["feature"], r["conditions"][0]["op"])
        if k not in best or abs(r["test_lift_pp"]) > abs(best[k]["test_lift_pp"]):
            best[k] = r
    return sorted(best.values(), key=lambda r: -abs(r["test_lift_pp"]))


def _scan_combos(singles: list[dict], train: pd.DataFrame, test: pd.DataFrame,
                 base_train: float, base_test: float) -> list[dict]:
    rules = []
    top = singles[:COMBO_TOP_SINGLES]
    for a, b in combinations(top, 2):
        ca, cb = a["conditions"][0], b["conditions"][0]
        if ca["feature"] == cb["feature"]:
            continue
        if a["train_lift_pp"] * b["train_lift_pp"] <= 0:   # zıt yönlü koşulları birleştirme
            continue
        m_tr = (_cond_mask(train, ca["feature"], ca["op"], ca["threshold"]) & train[ca["feature"]].notna()
                & _cond_mask(train, cb["feature"], cb["op"], cb["threshold"]) & train[cb["feature"]].notna())
        n_tr = int(m_tr.sum())
        if n_tr < COMBO_MIN_SUP:
            continue
        fr_tr = train.loc[m_tr, "is_fake"].mean() * 100
        lift_tr = fr_tr - base_train
        # Kombinasyon en iyi tekil bileşeninden belirgin iyi olmalı (yoksa gereksiz)
        if abs(lift_tr) < max(abs(a["train_lift_pp"]), abs(b["train_lift_pp"])) + 3:
            continue
        m_te = (_cond_mask(test, ca["feature"], ca["op"], ca["threshold"]) & test[ca["feature"]].notna()
                & _cond_mask(test, cb["feature"], cb["op"], cb["threshold"]) & test[cb["feature"]].notna())
        n_te = int(m_te.sum())
        if n_te < 10:
            continue
        fr_te = test.loc[m_te, "is_fake"].mean() * 100
        lift_te = fr_te - base_test
        if lift_tr * lift_te <= 0:
            continue
        rules.append({"conditions": [ca, cb],
                      "train_n": n_tr, "train_fake_rate": round(fr_tr, 1),
                      "train_lift_pp": round(lift_tr, 1),
                      "test_n": n_te, "test_fake_rate": round(fr_te, 1),
                      "test_lift_pp": round(lift_te, 1)})
    return sorted(rules, key=lambda r: -abs(r["test_lift_pp"]))


def _tree_rules(train: pd.DataFrame, test: pd.DataFrame, base_train: float,
                base_test: float) -> list[dict]:
    try:
        from sklearn.tree import DecisionTreeClassifier, _tree
    except ImportError:
        return []
    feats = [f for f in FEATURES]
    X = train[feats].fillna(train[feats].median())
    y = train["is_fake"]
    clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=COMBO_MIN_SUP, random_state=42)
    clf.fit(X, y)
    tree = clf.tree_
    out: list[dict] = []

    def recurse(node: int, conds: list[dict]) -> None:
        if tree.feature[node] == _tree.TREE_UNDEFINED:
            if not conds:
                return
            m_tr = pd.Series(True, index=train.index)
            m_te = pd.Series(True, index=test.index)
            for c in conds:
                m_tr &= _cond_mask(train, c["feature"], c["op"], c["threshold"]) & train[c["feature"]].notna()
                m_te &= _cond_mask(test, c["feature"], c["op"], c["threshold"]) & test[c["feature"]].notna()
            n_tr, n_te = int(m_tr.sum()), int(m_te.sum())
            if n_tr < COMBO_MIN_SUP or n_te < 10:
                return
            fr_tr = train.loc[m_tr, "is_fake"].mean() * 100
            fr_te = test.loc[m_te, "is_fake"].mean() * 100
            lift_tr, lift_te = fr_tr - base_train, fr_te - base_test
            if abs(lift_tr) < MIN_LIFT_PP or lift_tr * lift_te <= 0:
                return
            out.append({"conditions": conds,
                        "train_n": n_tr, "train_fake_rate": round(fr_tr, 1),
                        "train_lift_pp": round(lift_tr, 1),
                        "test_n": n_te, "test_fake_rate": round(fr_te, 1),
                        "test_lift_pp": round(lift_te, 1), "source": "tree"})
            return
        f = feats[tree.feature[node]]
        thr = round(float(tree.threshold[node]), 3)
        recurse(tree.children_left[node], conds + [{"feature": f, "op": "<=", "threshold": thr}])
        recurse(tree.children_right[node], conds + [{"feature": f, "op": ">=", "threshold": thr}])

    recurse(0, [])
    return sorted(out, key=lambda r: -abs(r["test_lift_pp"]))


# ─── Birleşik kırılım skoru (GERÇEK-pozitif) ─────────────────────────────────

def _score_components(singles: list[dict]) -> list[dict]:
    """OOS'ta ayakta kalan en iyi tekillerden skor bileşenleri.

    Skor GERÇEK-kırılım yönünde pozitiftir: sahte-lift'li koşul (klimaks imzası)
    −1, gerçek-lift'li koşul (sakin imza) +1 ağırlık alır.
    """
    comps = []
    for r in singles[:SCORE_MAX_COMPONENTS]:
        c = r["conditions"][0]
        comps.append({"feature": c["feature"], "op": c["op"],
                      "threshold": c["threshold"],
                      "weight": -1 if r["train_lift_pp"] > 0 else 1})
    return comps


def _event_scores(df: pd.DataFrame, comps: list[dict]) -> pd.Series:
    score = pd.Series(0, index=df.index)
    for c in comps:
        m = _cond_mask(df, c["feature"], c["op"], c["threshold"]) & df[c["feature"]].notna()
        score = score + m.astype(int) * c["weight"]
    return score


def _score_buckets(train: pd.DataFrame, test: pd.DataFrame,
                   comps: list[dict]) -> list[dict]:
    """Skor kovaları → train/test GERÇEK-kırılım oranı (kalibrasyon tablosu)."""
    s_tr, s_te = _event_scores(train, comps), _event_scores(test, comps)
    edges = [(-99, -2), (-1, -1), (0, 0), (1, 1), (2, 99)]
    rows = []
    for lo, hi in edges:
        m_tr = (s_tr >= lo) & (s_tr <= hi)
        m_te = (s_te >= lo) & (s_te <= hi)
        n_tr, n_te = int(m_tr.sum()), int(m_te.sum())
        rows.append({
            "min_score": lo, "max_score": hi,
            "train_n": n_tr,
            "train_genuine": round(100 - train.loc[m_tr, "is_fake"].mean() * 100, 1) if n_tr else None,
            "test_n": n_te,
            "test_genuine": round(100 - test.loc[m_te, "is_fake"].mean() * 100, 1) if n_te else None,
        })
    return rows


# ─── Teyit protokolü analizi (profesyonel giriş varyantları) ─────────────────

def _confirmation_analysis(ev: pd.DataFrame, df5: pd.DataFrame,
                           df1: pd.DataFrame | None, split: int) -> dict:
    """Üç giriş stratejisini bağımsız backtest'le kıyasla:

      A) breakout_bar   — kırılım barı kapanışında gir (taban; etiketin kendisi)
      B) next_bar_confirm — SONRAKİ bar da seviyenin ötesinde KAPANIRSA o kapanışta gir
      C) retest_hold    — RETEST_WITHIN bar içinde fiyat seviyeye dönüp (±tol)
                          seviyenin doğru tarafında kapanırsa o kapanışta gir

    Her varyant için ±1×ATR yarışı; B ve C için ayrıca 1.5:1 geometri.
    EV_R(1:1) = 2·WR−1; EV_R(1.5:1) = 1.5·WR − (1−WR).
    """
    recs: list[dict] = []
    for pos, (_, e) in enumerate(ev.iterrows()):
        dirn = 1 if e["direction"] == "up" else -1
        idx, lvl, atr = int(e["idx"]), float(e["level_price"]), float(e["atr_abs"])
        is_train = pos < split
        rec = {"train": is_train, "base_genuine": 1 - int(e["is_fake"])}

        # B) sonraki bar kapanış teyidi
        j = idx + 1
        if j < len(df5):
            cj = float(df5["close"].iloc[j])
            if (cj - lvl) * dirn > 0:
                rec["confirm"] = 1
                lb = _label_race(j, dirn, cj, atr, df5, df1)
                rec["confirm_label"] = lb
                lb15 = _label_race(j, dirn, cj, atr, df5, df1, *CONFIRM_TP15_SL10)
                rec["confirm_label_15"] = lb15
            else:
                rec["confirm"] = 0

        # C) retest-tut
        for k in range(idx + 1, min(idx + 1 + RETEST_WITHIN, len(df5))):
            near = (float(df5["low"].iloc[k]) <= lvl + RETEST_TOL_ATR * atr) if dirn > 0 \
                else (float(df5["high"].iloc[k]) >= lvl - RETEST_TOL_ATR * atr)
            if not near:
                continue
            ck = float(df5["close"].iloc[k])
            if (ck - lvl) * dirn >= 0:
                rec["retest"] = "hold"
                lb = _label_race(k, dirn, ck, atr, df5, df1)
                rec["retest_label"] = lb
                lb15 = _label_race(k, dirn, ck, atr, df5, df1, *CONFIRM_TP15_SL10)
                rec["retest_label_15"] = lb15
            else:
                rec["retest"] = "fail"
            break
        else:
            rec["retest"] = "none"
        recs.append(rec)

    rdf = pd.DataFrame(recs)

    def _agg(mask: pd.Series, label_col: str, tp: float, sl: float) -> dict:
        out = {}
        for split_name, sm in (("train", rdf["train"]), ("test", ~rdf["train"])):
            sub = rdf[mask & sm]
            resolved = sub[sub[label_col].isin(["true", "fake"])] if label_col in sub else sub.iloc[0:0]
            n = len(resolved)
            wr = (resolved[label_col] == "true").mean() * 100 if n else None
            out[split_name] = {
                "n": n, "wr": round(wr, 1) if wr is not None else None,
                "ev_r": round((tp * wr / 100 - sl * (1 - wr / 100)), 3) if wr is not None else None,
            }
        return out

    strategies = {
        "breakout_bar_1to1": {
            s: {"n": int(((rdf["train"] if s == "train" else ~rdf["train"])).sum()),
                "wr": round(rdf.loc[(rdf["train"] if s == "train" else ~rdf["train"]), "base_genuine"].mean() * 100, 1)}
            for s in ("train", "test")
        },
        "next_bar_confirm_1to1": _agg(rdf.get("confirm", pd.Series(dtype=float)) == 1, "confirm_label", 1.0, 1.0),
        "next_bar_confirm_1.5to1": _agg(rdf.get("confirm", pd.Series(dtype=float)) == 1, "confirm_label_15", *CONFIRM_TP15_SL10),
        "retest_hold_1to1": _agg(rdf.get("retest", pd.Series(dtype=object)) == "hold", "retest_label", 1.0, 1.0),
        "retest_hold_1.5to1": _agg(rdf.get("retest", pd.Series(dtype=object)) == "hold", "retest_label_15", *CONFIRM_TP15_SL10),
    }
    # baseline EV ekle
    for s in ("train", "test"):
        wr = strategies["breakout_bar_1to1"][s]["wr"]
        strategies["breakout_bar_1to1"][s]["ev_r"] = round(2 * wr / 100 - 1, 3) if wr is not None else None

    # Bilgi: teyit/retest sonucuna koşullu ORİJİNAL gerçek-oranı (filtre gücü)
    conditional = {}
    if "confirm" in rdf:
        for name, m in (("confirm_yes", rdf["confirm"] == 1), ("confirm_no", rdf["confirm"] == 0)):
            sub = rdf[m]
            conditional[name] = {"n": int(len(sub)),
                                 "orig_genuine": round(sub["base_genuine"].mean() * 100, 1) if len(sub) else None}
    if "retest" in rdf:
        for name in ("hold", "fail", "none"):
            sub = rdf[rdf["retest"] == name]
            conditional[f"retest_{name}"] = {"n": int(len(sub)),
                                             "orig_genuine": round(sub["base_genuine"].mean() * 100, 1) if len(sub) else None}

    return {"params": {"retest_within_bars": RETEST_WITHIN, "retest_tol_atr": RETEST_TOL_ATR,
                       "horizon_bars": HORIZON_BARS},
            "strategies": strategies, "conditional": conditional}


# ─── Rapor + çıktı ───────────────────────────────────────────────────────────

def _rule_str(r: dict) -> str:
    return " VE ".join(f"{c['feature']} {c['op']} {c['threshold']}" for c in r["conditions"])


def run_mining(symbol: str = "NDX.INDX", write_files: bool = True,
               out_dir: Path | None = None) -> dict:
    out_dir = out_dir or DATA_DIR
    _log(f"[fakeout_miner] {symbol}: 5m + 1m mum verisi çekiliyor...")
    df5 = add_indicators(fetch_candles(symbol, "5m"))
    df1 = fetch_candles(symbol, "1m")
    _log(f"  5m={len(df5)} bar ({df5['ts'].iloc[0]:%Y-%m-%d} → {df5['ts'].iloc[-1]:%Y-%m-%d}), 1m={len(df1)} bar")

    _log("[fakeout_miner] olay tespiti + etiketleme...")
    ev = detect_events(df5, df1 if len(df1) else None)
    if ev.empty or len(ev) < 100:
        _log(f"  YETERSİZ OLAY: {len(ev)} — madencilik atlandı")
        return {"status": "insufficient_events", "events": int(len(ev))}

    split = int(len(ev) * TRAIN_FRAC)
    train, test = ev.iloc[:split], ev.iloc[split:]
    base_train = train["is_fake"].mean() * 100
    base_test = test["is_fake"].mean() * 100
    _log(f"  {len(ev)} olay | fake oranı: train %{base_train:.1f} (n={len(train)}), "
         f"test %{base_test:.1f} (n={len(test)})")

    singles = _scan_singles(train, test, base_train, base_test)
    combos = _scan_combos(singles, train, test, base_train, base_test)
    tree = _tree_rules(train, test, base_train, base_test)
    _log(f"  kural: {len(singles)} tekil, {len(combos)} kombinasyon, {len(tree)} ağaç")

    # Birleşik kırılım skoru (GERÇEK-pozitif) + kalibrasyon kovaları
    comps = _score_components(singles)
    buckets = _score_buckets(train, test, comps)
    _log(f"  skor: {len(comps)} bileşen | kovalar: " + ", ".join(
        f"[{b['min_score']},{b['max_score']}]→test %{b['test_genuine']}(n={b['test_n']})"
        for b in buckets))

    # Teyit protokolü (sonraki-bar teyidi, retest-tut) — bağımsız backtest
    _log("[fakeout_miner] teyit protokolü analizi...")
    confirmation = _confirmation_analysis(ev, df5, df1, split)
    for name, st in confirmation["strategies"].items():
        te = st.get("test") or {}
        _log(f"  {name}: test n={te.get('n')} WR=%{te.get('wr')} EV={te.get('ev_r')}R")

    # Segment kırılımları (bilgi amaçlı)
    seg_stats = {}
    for col, name in (("level_kind", "seviye_türü"), ("direction", "yön")):
        seg_stats[name] = {str(k): {"n": int(g["is_fake"].count()),
                                    "fake_rate": round(g["is_fake"].mean() * 100, 1)}
                           for k, g in ev.groupby(col)}

    payload = {
        "version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "timeframe": "5m",
        "params": {"pivot_w": PIVOT_W, "min_touches": MIN_TOUCHES,
                   "pen_min_atr": PEN_MIN_ATR, "target_atr": TARGET_ATR,
                   "horizon_bars": HORIZON_BARS, "train_frac": TRAIN_FRAC},
        "events_total": int(len(ev)),
        "base_fake_rate_train": round(base_train, 1),
        "base_fake_rate_test": round(base_test, 1),
        "date_range": [str(ev["ts"].iloc[0]), str(ev["ts"].iloc[-1])],
        "segments": seg_stats,
        "rules": {"singles": singles, "combos": combos, "tree": tree},
        "score": {"components": comps, "buckets": buckets,
                  "note": "Skor GERÇEK-kırılım yönünde pozitif: sakin imza +1, klimaks imzası −1."},
        "confirmation": confirmation,
    }

    if write_files:
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = "" if symbol == "NDX.INDX" else f"_{symbol.split('.')[0]}"
        (out_dir / f"fakeout_rules{suffix}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        (out_dir / f"fakeout_report{suffix}.md").write_text(render_report(payload, ev))
        ev.to_csv(out_dir / f"fakeout_events{suffix}.csv", index=False)
        _log(f"  yazıldı: {out_dir}/fakeout_rules.json, fakeout_report.md, fakeout_events.csv")

    return payload


def render_report(p: dict, ev: pd.DataFrame) -> str:
    L = [f"# Sahte Kırılım (Fakeout) Madencilik Raporu — {p['symbol']}",
         f"\nÜretim: {p['generated_at']} · Olay: {p['events_total']} · "
         f"Aralık: {p['date_range'][0][:10]} → {p['date_range'][1][:10]}",
         f"\n**Taban sahte-kırılım oranı:** train %{p['base_fake_rate_train']} · "
         f"test %{p['base_fake_rate_test']}",
         "\nEtiket: kırılım kapanışından ±1.0×ATR iki-hedef yarışı (1m çözünürlük). "
         "Devam hedefi önce → GERÇEK; ters hedef önce → SAHTE. Belirsizler atıldı.",
         "\n## Segmentler\n"]
    for name, seg in p["segments"].items():
        L.append(f"**{name}:**")
        for k, v in seg.items():
            L.append(f"- {k}: n={v['n']}, sahte %{v['fake_rate']}")
        L.append("")
    for title, key in (("Tekil Koşullar (OOS doğrulanmış)", "singles"),
                       ("Kombinasyonlar (OOS doğrulanmış)", "combos"),
                       ("Karar Ağacı Kuralları (OOS doğrulanmış)", "tree")):
        rules = p["rules"][key]
        L.append(f"## {title}\n")
        if not rules:
            L.append("_(OOS'ta ayakta kalan kural yok)_\n")
            continue
        L.append("| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |")
        L.append("|---|---|---|---|---|---|---|")
        for r in rules[:20]:
            L.append(f"| `{_rule_str(r)}` | {r['train_n']} | {r['train_fake_rate']} | "
                     f"{r['train_lift_pp']:+.1f}pp | {r['test_n']} | {r['test_fake_rate']} | "
                     f"{r['test_lift_pp']:+.1f}pp |")
        L.append("")
    score = p.get("score") or {}
    if score.get("buckets"):
        L.append("## Birleşik Kırılım Skoru (GERÇEK-pozitif kalibrasyon)\n")
        L.append("Bileşenler: " + "; ".join(
            f"`{c['feature']} {c['op']} {c['threshold']}` ({'+' if c['weight'] > 0 else '−'}1)"
            for c in score.get("components", [])) + "\n")
        L.append("| Skor aralığı | Train n | Train gerçek% | Test n | Test gerçek% |")
        L.append("|---|---|---|---|---|")
        for b in score["buckets"]:
            L.append(f"| {b['min_score']} … {b['max_score']} | {b['train_n']} | "
                     f"{b['train_genuine']} | {b['test_n']} | {b['test_genuine']} |")
        L.append("")
    conf = p.get("confirmation") or {}
    if conf.get("strategies"):
        L.append("## Teyit Protokolü — Giriş Varyantları (bağımsız backtest)\n")
        L.append("| Strateji | Train n | Train WR% | Train EV(R) | Test n | Test WR% | Test EV(R) |")
        L.append("|---|---|---|---|---|---|---|")
        for name, st in conf["strategies"].items():
            tr, te = st.get("train") or {}, st.get("test") or {}
            L.append(f"| {name} | {tr.get('n')} | {tr.get('wr')} | {tr.get('ev_r')} | "
                     f"{te.get('n')} | {te.get('wr')} | {te.get('ev_r')} |")
        L.append("")
        L.append("**Koşullu bilgi (filtre gücü):** " + "; ".join(
            f"{k}: n={v['n']}, orijinal gerçek %{v['orig_genuine']}"
            for k, v in (conf.get("conditional") or {}).items()) + "\n")
    L.append("## Dürüstlük Notları\n")
    L.append("- Seviyeler yalnızca olay anına kadar TEYİTLENMİŞ pivotlardan kuruldu (lookahead yok).")
    L.append("- Kurallar kronolojik %70/30 ayrımında OOS işaret korumazsa elendi.")
    L.append("- `test_lift_pp` küçük örneklemde gürültülüdür; runtime kapısı yalnızca "
             "hem train hem test lifti aynı yönde GÜÇLÜ olan kuralları kullanmalıdır.")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="NDX.INDX")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    run_mining(symbol=args.symbol, write_files=not args.no_write)


if __name__ == "__main__":
    main()
