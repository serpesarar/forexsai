"""engine.py — sızıntısız özellik + replay çekirdeği (NDX BUY araştırması).

DÜRÜSTLÜK SÖZLEŞMESİ (bu dosyadaki her fonksiyon buna uyar)
-----------------------------------------------------------
1. Mum zaman damgası = mumun AÇILIŞ zamanı (MT5/candle_cache konvansiyonu).
   Karar anı t'de KAPANMIŞ sayılan son mum: candle_time + tf_süresi <= t.
   `asof_features` bunu zorlar — açık mum ASLA özelliğe girmez.
2. Giriş: sinyal anından SONRA açılan ilk 1m mumun AÇILIŞ fiyatı (+ sürtünme).
   Sinyal barının kendisi kullanılamaz (o bar karar anında henüz kapanmamıştır).
3. Çözüm: giriş barı DAHİL, girişten sonraki barların high/low'u ile. Aynı barda
   TP ve SL birlikte dokunulduysa → SL önce (konservatif, her varyantta aynı).
4. Sürtünme: spread + kayma, girişte ve çıkışta fiyata aleyhte uygulanır.
5. Hiçbir özellik geleceğe bakmaz; makro günlük veriler 1 gün kaydırılır.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"

TF_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}


# ─────────────────────────── gösterge matematiği ────────────────────────────
def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def atr(h, l, c, n: int = 14) -> pd.Series:
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def macd(c: pd.Series):
    line = ema(c, 12) - ema(c, 26)
    sig = ema(line, 9)
    return line, sig, line - sig


def adx(h, l, c, n: int = 14):
    up, dn = h.diff(), -l.diff()
    plus_dm = ((up > dn) & (up > 0)).astype(float) * up
    minus_dm = ((dn > up) & (dn > 0)).astype(float) * dn
    a = atr(h, l, c, n)
    pdi = 100 * plus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    mdi = 100 * minus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean(), pdi, mdi


def stoch(h, l, c, n: int = 14, d_n: int = 3):
    ll, hh = l.rolling(n).min(), h.rolling(n).max()
    k = 100 * (c - ll) / (hh - ll).replace(0, np.nan)
    return k, k.rolling(d_n).mean()


def parabolic_sar(high: pd.Series, low: pd.Series) -> pd.Series:
    """backend/services/signal_feature_snapshot.py ile aynı uygulama."""
    n = len(high)
    out = np.full(n, np.nan)
    if n < 3:
        return pd.Series(out, index=high.index)
    h, l = high.values, low.values
    af_init, af_step, af_max = 0.02, 0.02, 0.2
    is_long, out[0], ep, af = True, l[0], h[0], af_init
    for i in range(1, n):
        prev = out[i - 1] if not np.isnan(out[i - 1]) else l[i - 1]
        if is_long:
            s = prev + af * (ep - prev)
            s = min(s, l[i - 1], l[i - 2] if i >= 2 else l[i - 1])
            if l[i] < s:
                is_long, s, ep, af = False, ep, l[i], af_init
            elif h[i] > ep:
                ep, af = h[i], min(af + af_step, af_max)
        else:
            s = prev + af * (ep - prev)
            s = max(s, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if h[i] > s:
                is_long, s, ep, af = True, ep, h[i], af_init
            elif l[i] < ep:
                ep, af = l[i], min(af + af_step, af_max)
        out[i] = s
    return pd.Series(out, index=high.index)


# ─────────────────────────── veri yükleme ────────────────────────────────────
def load_bars(tf: str) -> pd.DataFrame:
    df = pd.read_csv(DATA / f"bars_{tf}.csv", parse_dates=["ts"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    return df


def resample_from(df1m: pd.DataFrame, tf: str) -> pd.DataFrame:
    """1m'den üst TF türet (boşluklu candle_cache yerine tutarlı ızgara)."""
    rule = {"5m": "5min", "15m": "15min", "30m": "30min",
            "1h": "1h", "4h": "4h", "1d": "1D"}[tf]
    g = (df1m.set_index("ts")
         .resample(rule, label="left", closed="left")
         .agg({"open": "first", "high": "max", "low": "min",
               "close": "last", "volume": "sum"})
         .dropna(subset=["open"]))
    return g.reset_index()


def add_indicators(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Bar bazlı göstergeler. Satır i = i'inci barın KAPANIŞINDA bilinen değerler."""
    o, h, l, c, v = (df[x] for x in ("open", "high", "low", "close", "volume"))
    out = pd.DataFrame({"ts": df["ts"]})
    a = atr(h, l, c, 14)
    out[f"{prefix}_close"] = c
    out[f"{prefix}_atr"] = a
    out[f"{prefix}_atr_pct"] = a / c * 100
    out[f"{prefix}_atr_ratio"] = a / a.rolling(50).mean()
    for n in (20, 50, 200):
        e = ema(c, n)
        out[f"{prefix}_ema{n}"] = e
        out[f"{prefix}_dist_ema{n}_atr"] = (c - e) / a
    out[f"{prefix}_ema20_slope_atr"] = (ema(c, 20).diff(5)) / a
    out[f"{prefix}_ema50_slope_atr"] = (ema(c, 50).diff(10)) / a
    out[f"{prefix}_rsi"] = rsi(c, 14)
    k, d = stoch(h, l, c, 14, 3)
    out[f"{prefix}_stoch_k"] = k
    out[f"{prefix}_stoch_d"] = d
    ml, ms, mh = macd(c)
    out[f"{prefix}_macd_hist"] = mh
    out[f"{prefix}_macd_hist_atr"] = mh / a
    ax, pdi, mdi = adx(h, l, c, 14)
    out[f"{prefix}_adx"] = ax
    out[f"{prefix}_di_diff"] = pdi - mdi
    sar = parabolic_sar(h, l)
    out[f"{prefix}_sar_dist_atr"] = (c - sar) / a
    bb_m = c.rolling(20).mean()
    bb_s = c.rolling(20).std()
    out[f"{prefix}_bb_pos"] = (c - (bb_m - 2 * bb_s)) / (4 * bb_s).replace(0, np.nan)
    out[f"{prefix}_bb_width_atr"] = (4 * bb_s) / a
    out[f"{prefix}_ret1_atr"] = c.diff(1) / a
    out[f"{prefix}_ret5_atr"] = c.diff(5) / a
    out[f"{prefix}_ret20_atr"] = c.diff(20) / a
    out[f"{prefix}_range_atr"] = (h - l) / a
    out[f"{prefix}_body_frac"] = (c - o).abs() / (h - l).replace(0, np.nan)
    out[f"{prefix}_up_frac20"] = (c.diff() > 0).rolling(20).mean()
    hh = h.rolling(50).max()
    ll = l.rolling(50).min()
    out[f"{prefix}_pos_in_range50"] = (c - ll) / (hh - ll).replace(0, np.nan)
    out[f"{prefix}_dist_hh50_atr"] = (hh - c) / a
    out[f"{prefix}_dist_ll50_atr"] = (c - ll) / a
    out[f"{prefix}_vol_ratio"] = v / v.rolling(50).mean()
    # kapanış zamanı: bu satırdaki değerler bu andan İTİBAREN bilinir
    out["known_at"] = df["ts"] + pd.Timedelta(minutes=TF_MINUTES[prefix_to_tf(prefix)])
    return out


PREFIX_TF = {"M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
             "H1": "1h", "H4": "4h", "D1": "1d"}


def prefix_to_tf(prefix: str) -> str:
    return PREFIX_TF[prefix]


def asof_features(events: pd.DataFrame, feat: pd.DataFrame,
                  event_col: str = "ts") -> pd.DataFrame:
    """Her olay için, olaydan ÖNCE kapanmış son barın özelliklerini iliştir.

    feat['known_at'] barın kapanış anıdır; merge_asof `<=` semantiğiyle
    known_at <= event zamanı olan son satırı seçer → açık bar sızmaz.
    """
    f = feat.sort_values("known_at").drop(columns=["ts"])
    e = events.sort_values(event_col)
    return pd.merge_asof(e, f, left_on=event_col, right_on="known_at",
                         direction="backward")


# ─────────────────────────── replay ──────────────────────────────────────────
@dataclass
class Geometry:
    tp: float = 80.0       # puan (NDX)
    sl: float = 110.0
    friction: float = 1.0  # spread+kayma (fiyat birimi), giriş VE çıkışta aleyhte
    max_hold_min: int = 1440


def replay_one(bars1m: np.ndarray, ts1m: np.ndarray, t_signal: np.datetime64,
               direction: str, g: Geometry) -> dict | None:
    """Tek girişi 1m barlarla çöz. bars1m: (n,4) open,high,low,close."""
    i = np.searchsorted(ts1m, t_signal, side="right")   # sinyalden SONRAKİ ilk bar
    if i >= len(ts1m):
        return None
    entry_raw = bars1m[i, 0]
    sgn = 1.0 if direction == "BUY" else -1.0
    entry = entry_raw + sgn * g.friction          # aleyhte spread
    tp_px = entry + sgn * g.tp
    sl_px = entry - sgn * g.sl
    end = min(len(ts1m), i + g.max_hold_min + 5)
    mfe = mae = 0.0
    for j in range(i, end):
        # j-i = PİYASA dakikası (bar yoksa zaman da akmaz — hafta sonu atlanır)
        hi, lo = bars1m[j, 1], bars1m[j, 2]
        fav = sgn * (hi - entry) if direction == "BUY" else sgn * (lo - entry)
        adv = sgn * (lo - entry) if direction == "BUY" else sgn * (hi - entry)
        mfe = max(mfe, fav)
        mae = min(mae, adv)
        extra = dict(mfe_r=mfe / g.sl, mae_r=mae / g.sl, entry_px=entry)
        hit_sl = (lo <= sl_px) if direction == "BUY" else (hi >= sl_px)
        hit_tp = (hi >= tp_px) if direction == "BUY" else (lo <= tp_px)
        if hit_sl and hit_tp:
            pnl = -g.sl - g.friction
            return dict(outcome=0, exit_i=j, r=pnl / g.sl, pnl=pnl,
                        ambiguous=True, bars_held=j - i, **extra)
        if hit_sl:
            pnl = -g.sl - g.friction
            return dict(outcome=0, exit_i=j, r=pnl / g.sl, pnl=pnl,
                        ambiguous=False, bars_held=j - i, **extra)
        if hit_tp:
            pnl = g.tp - g.friction
            return dict(outcome=1, exit_i=j, r=pnl / g.sl, pnl=pnl,
                        ambiguous=False, bars_held=j - i, **extra)
        if (j - i) >= g.max_hold_min:
            px = bars1m[j, 3]
            pnl = sgn * (px - entry) - g.friction
            return dict(outcome=int(pnl > 0), exit_i=j, r=pnl / g.sl, pnl=pnl,
                        ambiguous=False, bars_held=j - i, timeout=True, **extra)
    return None
