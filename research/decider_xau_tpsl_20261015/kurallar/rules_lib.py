"""Decider XAU giriş-kuralı araştırması — ortak kütüphane (özellikler + simülasyon).

SIZINTI KURALI: karar anı T = journal ts (Claude çağrısı bittikten SONRA yazılır). Bar-tabanlı her özellik
yalnız t_end ≤ T olan KAPANMIŞ barlardan hesaplanır (`asof_closed`). Journal'daki multi_tf/forensics alanları
kutu tarafından karar ÖNCESİ hesaplanmış anlık görüntülerdir. Giriş = T'den sonraki ilk 1m barın açılışı
(+ spread, BUY'da ask); +1 dk gecikme testinde bir sonraki barın açılışı. Çıkış yalnız giriş barından itibaren
(giriş barı dahil; giriş barın AÇILIŞINDA) — üst klasördeki core.py simülatörü (aynı bar TP+SL = LOSS)."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parents[1] / "claude_decider"))
import core  # noqa: E402
import entry_quality as EQ  # noqa: E402  (decider'ın kendi D2 tanımı — birebir)

DEFAULT_SPREAD = 0.14
GEOMS = {  # ön-kayıtlı üç geometri (ATR = kapalı-bar 5m ATR14)
    "G1_tp1.0_sl1.5": dict(tp=1.0, sl=1.5, time_min=None),
    "G2_tp1.25_sl0.75": dict(tp=1.25, sl=0.75, time_min=None),
    "G3_tp3.0_sl1.5_t120": dict(tp=3.0, sl=1.5, time_min=120),
}
EMA_H1 = 50
D1_SMA = 10
HI20 = 20
ATR_RATIO_LOOKBACK = 288       # 24 saat × 12 adet 5m bar


# ---------------------------------------------------------------- bar serileri (kapalı-bar asof)
class BarFeatures:
    """1m barlardan türetilen TF serileri; her özellik 'karar anında kapanmış son bar' ile okunur."""

    def __init__(self, b1: pd.DataFrame):
        self.b1 = b1
        self.t1 = b1.t_utc.dt.tz_convert("UTC").dt.tz_localize(None).values.astype("datetime64[ns]")
        self.c1 = b1.close.values.astype(float)
        r5 = core.resample(b1, "5min")
        r60 = core.resample(b1, "60min")
        d1 = (b1.set_index("t_utc").resample("1D", offset="21h", label="left", closed="left")
              .agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna())
        d1["t_end"] = d1.index + pd.Timedelta("1D")
        d1 = d1.reset_index()
        self.tf = {}
        for name, r in (("5m", r5), ("1h", r60), ("1d", d1)):
            te = r.t_end.dt.tz_convert("UTC").dt.tz_localize(None).values.astype("datetime64[ns]")
            h, l, c = r.high.values, r.low.values, r.close.values
            pc = np.r_[np.nan, c[:-1]]
            tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
            atr14 = pd.Series(tr).rolling(14).mean().values          # decider: basit ortalama ATR14
            self.tf[name] = dict(te=te, h=h, l=l, c=c, atr14=atr14,
                                 ema50=pd.Series(c).ewm(span=EMA_H1, adjust=False).mean().values,
                                 sma10=pd.Series(c).rolling(D1_SMA).mean().values,
                                 hi20=pd.Series(h).rolling(HI20).max().values,
                                 lo20=pd.Series(l).rolling(HI20).min().values,
                                 n_avail=np.arange(1, len(c) + 1))
        a5 = self.tf["5m"]["atr14"]
        self.tf["5m"]["atr_med24h"] = pd.Series(a5).rolling(ATR_RATIO_LOOKBACK, min_periods=200).median().values

    def asof_closed(self, tfname: str, T: np.datetime64) -> int:
        """t_end ≤ T olan son barın indeksi (yoksa −1)."""
        return int(np.searchsorted(self.tf[tfname]["te"], T, side="right")) - 1

    def last_close_1m(self, T: np.datetime64) -> float:
        """T anında KAPANMIŞ son 1m barın kapanışı (1m bar t_utc = başlangıç, bitiş = +1 dk)."""
        i = int(np.searchsorted(self.t1 + np.timedelta64(1, "m"), T, side="right")) - 1
        return float(self.c1[i]) if i >= 0 else np.nan

    def features(self, T: np.datetime64) -> dict:
        f = {}
        px = self.last_close_1m(T)
        i = self.asof_closed("1h", T); H = self.tf["1h"]
        if i >= EMA_H1:
            f["h1_close"], f["h1_ema50"] = H["c"][i], H["ema50"][i]
            f["h1_above_ema50"] = bool(H["c"][i] > H["ema50"][i])
            f["dist_hi20_h1_atr"] = (H["hi20"][i] - px) / H["atr14"][i]
            f["dist_lo20_h1_atr"] = (px - H["lo20"][i]) / H["atr14"][i]
        j = self.asof_closed("1d", T); D = self.tf["1d"]
        if j >= D1_SMA - 1:
            f["d1_up"] = bool(D["c"][j] > D["sma10"][j])
        k = self.asof_closed("5m", T); F = self.tf["5m"]
        if k >= 14:
            f["atr5_closed"] = F["atr14"][k]
            med = F["atr_med24h"][k]
            f["atr5_ratio"] = F["atr14"][k] / med if med and med > 0 else np.nan
        f["px_closed_1m"] = px
        return f


# ---------------------------------------------------------------- journal kayıtları
def load_journal() -> pd.DataFrame:
    rows = []
    for ln in open(ROOT / "data" / "journal_xau_raw.jsonl"):
        r = json.loads(ln); raw = r["raw"]; dec = raw.get("decision") or {}
        mode = raw.get("mode") or "evidence"
        if mode == "gold_brain":
            continue
        reason = str(dec.get("reason") or "")
        m5 = (raw.get("multi_tf") or {}).get("5m") or {}
        fz = raw.get("forensics")
        tr = raw.get("trade") or {}
        cz, vz = m5.get("channel_z"), m5.get("vwap_z")
        ext = np.nan; tsign = np.nan
        if cz is not None and vz is not None:
            ext = max(abs(cz), abs(vz))
            dom = cz if abs(cz) >= abs(vz) else vz
            tsign = float(np.sign(dom))
        q_buy = EQ.assess(fz, "BUY"); q_sell = EQ.assess(fz, "SELL")
        rows.append(dict(
            id=r["id"], ts=pd.Timestamp(r["ts"]), mode=mode, action=dec.get("action"),
            direction=dec.get("direction"), size_factor=dec.get("size_factor"),
            fake_wait=reason.startswith(("claude exit", "claude spawn")), model=raw.get("model"),
            cz5=cz, vz5=vz, extremity=ext, trig_sign=tsign,
            eq_block_buy=q_buy["blocked"] if q_buy["score"] is not None else np.nan,
            eq_block_sell=q_sell["blocked"] if q_sell["score"] is not None else np.nan,
            chz_dir_buy=q_buy["chz_dir"], vol5=q_buy["vol"],
            spread=tr.get("spread") if tr.get("spread") is not None else np.nan,
        ))
    d = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    return d


def add_bar_features(d: pd.DataFrame, BF: BarFeatures) -> pd.DataFrame:
    feats = [BF.features(core.to64(t)) for t in d.ts]
    F = pd.DataFrame(feats, index=d.index)
    out = pd.concat([d, F], axis=1)
    out["hour_utc"] = out.ts.dt.tz_convert("UTC").dt.hour
    out["sess_ldn_ny"] = out.hour_utc.between(7, 16)          # 07:00–16:59 UTC
    return out


# ---------------------------------------------------------------- simülasyon
def sim_one(P: core.Paths, direction: str, i0: int, spread: float, atr: float) -> dict[str, float]:
    """i0 = giriş barı indeksi. Dönüş: {geom: R} (R = pnl / SL mesafesi). Spread BUY girişinde (ask)."""
    out = {}
    if i0 >= len(P.t) or not np.isfinite(atr) or atr <= 0:
        return {g: np.nan for g in GEOMS}
    e = P.o[i0] + (spread if direction == "BUY" else 0.0)
    w = P.window(i0, core.MAX_HOLD_MIN)
    h, l, c, t = P.h[w], P.l[w], P.c[w], P.t[w]
    for g, G in GEOMS.items():
        hh, ll, cc = h, l, c
        if G["time_min"]:
            j = max(int(np.searchsorted(t, t[0] + np.timedelta64(G["time_min"], "m"))), 1)
            hh, ll, cc = h[:j], l[:j], c[:j]
        pnl_m, _, ex = core.sim_grid(direction, e, spread, hh, ll, cc, np.array([G["tp"] * atr]), np.array([G["sl"] * atr]))
        pnl = pnl_m[0, 0]
        out[g] = pnl / (G["sl"] * atr)
        out[g + "_exit"] = pd.Timestamp(t[int(ex[0, 0])], tz="UTC") + pd.Timedelta(minutes=1)
        out[g + "_usd_oz"] = pnl
    return out


def entry_index(P: core.Paths, T: pd.Timestamp, delay_min: int = 0) -> tuple[int, float]:
    """T'den sonraki ilk 1m barın indeksi (+delay bar). Dönüş (i0, gecikme dk)."""
    i0 = P.first_idx_at_or_after(pd.Timestamp(T).floor("min") + pd.Timedelta(minutes=1)) + delay_min
    if i0 >= len(P.t):
        return i0, np.inf
    return i0, (P.t[i0] - core.to64(T)) / np.timedelta64(1, "m")


def gap_in_window(P: core.Paths, i0: int, minutes: int = 240) -> bool:
    w = P.window(i0, minutes)
    tt = P.t[w]
    if len(tt) < 2:
        return True
    gaps = np.diff(tt).astype("timedelta64[m]").astype(int)
    hrs = pd.DatetimeIndex(tt[:-1]).hour
    return bool(np.any((gaps > 5) & (np.asarray(hrs) != 20)))


def lot_from_size(sf: float) -> float:
    """execute_mt5: lot = 0.10 × min(size_factor, 0.3), 0.01 adıma AŞAĞI yuvarla, ≥0.01."""
    if sf is None or not np.isfinite(sf) or sf <= 0:
        return 0.01
    lot = np.floor(0.10 * min(sf, 0.3) / 0.01 + 1e-9) * 0.01
    return max(lot, 0.01)
