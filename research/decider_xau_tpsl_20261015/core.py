"""Ortak çekirdek: broker 1m bar yükleme, kapalı-bar ATR, yol çıkarma ve vektörel TP/SL simülasyonu.

FİYAT KONVANSİYONU: barlar MT5 BID barlarıdır.
  BUY : giriş = ask = bid_open + spread ; çıkışlar bid'de → TP: high ≥ E+tp ; SL: low ≤ E−sl.
  SELL: giriş = bid_open            ; çıkışlar ask'te → TP: low+s ≤ E−tp ; SL: high+s ≥ E+sl.
Aynı barda TP ve SL → LOSS (konservatif). Giriş barı DAHİL (giriş o barın AÇILIŞINDA, barın
high/low'u girişten sonra oluşur). Ufuk dolarsa son barın kapanışında (yöne göre bid/ask) çıkılır.
Tüm fonksiyonlar yalnız giriş anından SONRAKİ veriyi çıkış için, ÖNCEKİ (kapalı) veriyi ATR için kullanır."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OZ_PER_LOT = 100.0           # XAUUSD 1 lot = 100 ons → 1$ fiyat hareketi × 0.01 lot = 1$
MAX_HOLD_MIN = 48 * 60        # decider outcomes.py MAX_HORIZON_H=48 ile aynı
SESSION_BREAK_HOUR_UTC = 21   # broker günlük kapanış 00:00 sunucu = 21:00 UTC (ABD yaz saati boyunca)


def to64(ts: pd.Timestamp) -> np.datetime64:
    """tz-aware Timestamp → naive UTC datetime64[ns] (numpy dizileriyle kıyas için)."""
    ts = pd.Timestamp(ts)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return np.datetime64(ts.to_datetime64(), "ns")


def load_1m() -> pd.DataFrame:
    b = pd.read_csv(HERE / "data" / "xau_1m_utc.csv.gz")
    b["t_utc"] = pd.to_datetime(b.t_utc, utc=True, format="ISO8601")
    return b.sort_values("t_utc").reset_index(drop=True)


def resample(b1: pd.DataFrame, rule: str) -> pd.DataFrame:
    r = (b1.set_index("t_utc").resample(rule, label="left", closed="left")
         .agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna())
    r["t_end"] = r.index + pd.Timedelta(rule)
    return r.reset_index()


def atr_closed(bars: pd.DataFrame, t: pd.Timestamp, n: int = 14) -> float | None:
    """t anında KAPANMIŞ barlardan (t_end ≤ t) basit ortalama ATR(n) — decider ile aynı tanım."""
    ends = bars.t_end.dt.tz_convert("UTC").dt.tz_localize(None).values.astype("datetime64[ns]")
    idx = int(np.searchsorted(ends, to64(t), side="right"))
    if idx < n + 1:
        return None
    w = bars.iloc[idx - n - 1: idx]
    h, l, c = w.high.values[1:], w.low.values[1:], w.close.values[:-1]
    tr = np.maximum(h - l, np.maximum(abs(h - c), abs(l - c)))
    return float(tr.mean())


class Paths:
    """1m dizilerini numpy'da tutar; giriş zamanından itibaren yol dilimi verir."""

    def __init__(self, b1: pd.DataFrame):
        self.t = b1.t_utc.dt.tz_convert("UTC").dt.tz_localize(None).values.astype("datetime64[ns]")
        self.o, self.h, self.l, self.c = (b1[k].values.astype(float) for k in ("open", "high", "low", "close"))

    def first_idx_at_or_after(self, ts: pd.Timestamp) -> int:
        return int(np.searchsorted(self.t, to64(ts), side="left"))

    def window(self, i0: int, minutes: int) -> slice:
        t_end = self.t[i0] + np.timedelta64(minutes, "m")
        i1 = int(np.searchsorted(self.t, t_end, side="left"))
        return slice(i0, max(i1, i0 + 1))


def first_hit(cum: np.ndarray, levels: np.ndarray, increasing: bool) -> np.ndarray:
    """cum monoton (cummax ↑ / cummin ↓). Seviyeye ilk ulaşılan indeks; ulaşılmazsa len(cum)."""
    if increasing:
        return np.searchsorted(cum, levels, side="left")
    return np.searchsorted(-cum, -levels, side="left")


def sim_grid(direction: str, entry: float, spread: float, h: np.ndarray, l: np.ndarray, c: np.ndarray,
             tp_d: np.ndarray, sl_d: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sabit TP/SL ızgarası (tp_d × sl_d, fiyat birimi). Dönüş: pnl ($/ons, fiyat birimi) matrisi,
    sonuç kodu (1 TP, −1 SL, 0 süre), çıkış bar indeksi. Yol = h,l,c (giriş barından ufuk sonuna)."""
    n = len(h)
    if direction == "BUY":
        cmax, cmin = np.maximum.accumulate(h), np.minimum.accumulate(l)
        i_tp = first_hit(cmax, entry + tp_d, True)
        i_sl = first_hit(cmin, entry - sl_d, False)
        exit_te = c[-1] - entry
    else:
        cmax, cmin = np.maximum.accumulate(h + spread), np.minimum.accumulate(l + spread)
        i_tp = first_hit(cmin, entry - tp_d, False)
        i_sl = first_hit(cmax, entry + sl_d, True)
        exit_te = entry - (c[-1] + spread)
    TP, SL = np.meshgrid(i_tp, i_sl, indexing="ij")
    tpv, slv = np.meshgrid(tp_d, sl_d, indexing="ij")
    loss = (SL <= TP) & (SL < n)
    win = (TP < SL) & (TP < n)
    pnl = np.where(loss, -slv, np.where(win, tpv, exit_te))
    code = np.where(loss, -1, np.where(win, 1, 0))
    ex = np.where(loss, SL, np.where(win, TP, n - 1))
    return pnl, code, ex


def fav_adv(direction: str, entry: float, spread: float, h: np.ndarray, l: np.ndarray, c: np.ndarray):
    """Bar bazında lehte/aleyhte hareket (fiyat birimi; çıkış tarafı fiyatıyla)."""
    if direction == "BUY":
        return h - entry, entry - l, c - entry
    return entry - (l + spread), (h + spread) - entry, entry - (c + spread)


def sim_path_rule(direction: str, entry: float, spread: float, h, l, c, tp: float, sl: float,
                  be_trig: float | None = None, trail_d: float | None = None, trail_act: float = 0.0,
                  partial_tp: float | None = None, partial_frac: float = 0.5) -> float:
    """Yol-bağımlı kurallar (BE / iz-süren stop / kısmi TP). Konservatif sıra: bir barda stop ve
    hedef birlikte → stop; stop seviyesi yalnız ÖNCEKİ barların ekstremumlarıyla güncellenir.
    Dönüş: pnl (fiyat birimi, tam pozisyon başına)."""
    fav, adv, cl = fav_adv(direction, entry, spread, h, l, c)
    stop = -sl                      # lehte-mesafe ekseninde stop seviyesi (negatif = zarar)
    best_prev = -np.inf
    open_frac, realized = 1.0, 0.0
    for k in range(len(fav)):
        # bu barda stop vuruldu mu? (aleyhte hareket ≥ −stop)
        if -adv[k] <= stop:
            return realized + open_frac * stop
        if partial_tp is not None and open_frac == 1.0 and fav[k] >= partial_tp:
            realized += partial_frac * partial_tp
            open_frac -= partial_frac
            if be_trig is not None and be_trig <= 0:      # kısmi sonrası BE
                stop = max(stop, 0.0)
        if fav[k] >= tp:
            return realized + open_frac * tp
        best_prev = max(best_prev, fav[k])
        if be_trig is not None and be_trig > 0 and best_prev >= be_trig:
            stop = max(stop, 0.0)
        if trail_d is not None and best_prev >= trail_act:
            stop = max(stop, best_prev - trail_d)
    return realized + open_frac * cl[-1]
