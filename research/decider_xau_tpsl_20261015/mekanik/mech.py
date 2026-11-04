"""XAU mekanik kurallar — çekirdek (PROTOCOL.md ön kaydına göre). Sızıntısız: karar = sinyal barı KAPANIŞI,
yalnız kapanmış D1/H4 barları, giriş = sonraki barın açılışı (+spread), yol yalnız giriş barından itibaren."""
from __future__ import annotations
import numpy as np, pandas as pd

NY, LDN = "America/New_York", "Europe/London"
GAP_H = 3  # saat: daha büyük boşluk = segment sonu (hafta sonu/tatil)


# ───────────────────────── bar hazırlığı ─────────────────────────
def prep_h1(d: pd.DataFrame) -> pd.DataFrame:
    """d: ts(UTC başlangıç), o,h,l,c (+spr). Türetilmiş zaman alanları + segment + ATR + D1/H4 durumları."""
    d = d.sort_values("ts").reset_index(drop=True).copy()
    ts = pd.to_datetime(d.ts, utc=True)
    d["ts"] = ts
    gap = ts.diff().dt.total_seconds().div(3600).fillna(99)
    d["seg"] = (gap > GAP_H).cumsum()
    ny = ts.dt.tz_convert(NY)
    d["ny_h"] = ny.dt.hour
    d["ldn_h"] = ts.dt.tz_convert(LDN).dt.hour
    d["day"] = (ny + pd.Timedelta(hours=7)).dt.strftime("%Y-%m-%d")   # NY 17:00 gün sınırı
    d["h4k"] = d["day"] + "_" + ((ny + pd.Timedelta(hours=7)).dt.hour // 4).astype(str)
    d["utc_h"] = ts.dt.hour
    d["year"] = ts.dt.year
    pc = d.c.shift(1)
    tr = np.maximum(d.h - d.l, np.maximum((d.h - pc).abs(), (d.l - pc).abs()))
    tr[d.seg != d.seg.shift(1)] = (d.h - d.l)[d.seg != d.seg.shift(1)]
    d["atr"] = tr.rolling(14).mean()
    # D1 (kapanmış) — her H1 karar anına son kapanmış günü eşle
    end = d.ts + pd.Timedelta(hours=1)
    D = d.groupby("day").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"),
                             end=("ts", "last"), n=("ts", "size"))
    D["end"] = D["end"] + pd.Timedelta(hours=1)
    D = D[D.n >= 4]
    D["ema200"] = D.c.ewm(span=200, adjust=False, min_periods=200).mean()
    D = D.sort_values("end")
    k = np.searchsorted(D["end"].values, end.values, side="right") - 1
    ok = k >= 0
    d["d1_c"] = np.where(ok, D.c.values[np.clip(k, 0, None)], np.nan)
    d["d1_ema200"] = np.where(ok, D.ema200.values[np.clip(k, 0, None)], np.nan)
    d["day_open"] = d.groupby("day").o.transform("first")
    d["trend_up"] = d.d1_c > d.d1_ema200
    d["trend_dn"] = d.d1_c < d.d1_ema200
    # H4 (kapanmış)
    H4 = d.groupby("h4k").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"),
                              end=("ts", "last"), i_last=("ts", lambda s: s.index[-1]))
    H4["end"] = H4["end"] + pd.Timedelta(hours=1)
    H4 = H4.sort_values("end").reset_index()
    H4["ema50"] = H4.c.ewm(span=50, adjust=False, min_periods=50).mean()
    k4 = np.searchsorted(H4["end"].values, end.values, side="right") - 1
    ok4 = k4 >= 0
    d["h4_c"] = np.where(ok4, H4.c.values[np.clip(k4, 0, None)], np.nan)
    d["h4_ema50"] = np.where(ok4, H4.ema50.values[np.clip(k4, 0, None)], np.nan)
    d.attrs["H4"] = H4
    return d


def h4_frame(d: pd.DataFrame) -> pd.DataFrame:
    """H4 barları (kapanış zamanı end) + H4 ATR + D1 trend durumu (H4 kapanış anında kapanmış gün)."""
    H4 = d.attrs["H4"].copy()
    pc = H4.c.shift(1)
    tr = np.maximum(H4.h - H4.l, np.maximum((H4.h - pc).abs(), (H4.l - pc).abs()))
    H4["atr"] = tr.rolling(14).mean()
    # H4 kapanışındaki trend = o H4'ün son H1 barının trend_up değeri
    H4["trend_up"] = d.trend_up.values[H4.i_last.values]
    H4["trend_dn"] = d.trend_dn.values[H4.i_last.values]
    return H4


# ───────────────────────── simülasyon ─────────────────────────
def path_sim(O, H, L, C, seg, sig, ent, atr, hold, tp, sl, side, spread, optimistic=False, same_bar="loss"):
    """Vektörel TP/SL/zaman yarışı.
    sig: sinyal barı indeksi, ent: giriş barı indeksi (= sig+1 H1'de), hold: tutulacak bar sayısı (giriş barı dahil).
    tp=None → TP yok. side +1 BUY / −1 SELL. spread $ (skaler veya dizi). Dönüş: R, çıkış indeksi, sonuç kodu."""
    sig, ent, hold = np.asarray(sig), np.asarray(ent), np.asarray(hold)
    n = len(O)
    Hmax = int(hold.max()) if len(hold) else 1
    J = ent[:, None] + np.arange(Hmax)[None, :]
    Jc = np.clip(J, 0, n - 1)
    valid = (np.arange(Hmax)[None, :] < hold[:, None]) & (J < n) & (seg[Jc] == seg[ent][:, None])
    sp = np.broadcast_to(np.asarray(spread, float), ent.shape) if np.ndim(spread) else np.full(len(ent), float(spread))
    if optimistic:
        entry = C[sig]
        sp_eff = np.zeros(len(ent))
    else:
        entry = O[ent] + (sp if side > 0 else 0.0)
        sp_eff = sp
    unit = sl * atr
    if side > 0:
        SL, TP = entry - unit, (entry + tp * atr if tp is not None else np.full(len(ent), np.inf))
        hs, ht = (L[Jc] <= SL[:, None]), (H[Jc] >= TP[:, None])
    else:
        SL, TP = entry + unit, (entry - tp * atr if tp is not None else np.full(len(ent), -np.inf))
        hs = (H[Jc] + (sp_eff[:, None] if not optimistic else 0) >= SL[:, None])
        ht = (L[Jc] + (sp_eff[:, None] if not optimistic else 0) <= TP[:, None])
    hs &= valid; ht &= valid
    BIG = 10 ** 6
    fs = np.where(hs.any(1), hs.argmax(1), BIG)
    ft = np.where(ht.any(1), ht.argmax(1), BIG)
    last = valid.sum(1) - 1
    R = np.empty(len(ent)); code = np.empty(len(ent), dtype="<U4"); xi = np.empty(len(ent), dtype=int)
    loss_first = (fs < ft) | ((fs == ft) & (fs < BIG) & (same_bar == "loss"))
    win_first = (ft < fs) | ((fs == ft) & (ft < BIG) & (same_bar == "win"))
    # SL: boşlukla (j>0 açılışı SL'nin ötesinde) daha kötü fiyattan
    jS = np.clip(fs, 0, Hmax - 1)
    oS = O[Jc[np.arange(len(ent)), jS]]
    if side > 0:
        px_sl = np.where((fs > 0) & (oS < SL), oS, SL)
        pnl_sl = px_sl - entry
        pnl_tp = TP - entry
        px_t = C[Jc[np.arange(len(ent)), np.clip(last, 0, None)]]
        pnl_t = px_t - entry
    else:
        oSa = oS + (sp_eff if not optimistic else 0)
        px_sl = np.where((fs > 0) & (oSa > SL), oSa, SL)
        pnl_sl = entry - px_sl
        pnl_tp = entry - TP
        px_t = C[Jc[np.arange(len(ent)), np.clip(last, 0, None)]] + (sp_eff if not optimistic else 0)
        pnl_t = entry - px_t
    R = np.where(loss_first, pnl_sl, np.where(win_first, pnl_tp, pnl_t)) / unit
    code = np.where(loss_first, "SL", np.where(win_first, "TP", "TIME"))
    xi = ent + np.where(loss_first, fs, np.where(win_first, ft, last))
    bad = last < 0
    R[bad] = np.nan
    return R, xi, code


def one_position(ent, xi):
    """Aynı anda tek pozisyon: giriş sırasına göre, önceki çıkış barından SONRA başlayanlar alınır."""
    order = np.argsort(ent, kind="stable")
    keep = np.zeros(len(ent), bool); busy = -1
    for i in order:
        if ent[i] > busy:
            keep[i] = True; busy = xi[i]
    return keep


def day_boot_p(R, days, n=4000, seed=7):
    """Gün-blok bootstrap: P(ortR>0) ve %95 CI."""
    R = np.asarray(R, float); m = ~np.isnan(R); R, days = R[m], np.asarray(days)[m]
    if len(R) < 10:
        return np.nan, (np.nan, np.nan)
    u, inv = np.unique(days, return_inverse=True)
    s, k = np.bincount(inv, weights=R), np.bincount(inv)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(u), (n, len(u)))
    mm = s[idx].sum(1) / k[idx].sum(1)
    return float((mm > 0).mean()), (float(np.percentile(mm, 2.5)), float(np.percentile(mm, 97.5)))


def day_t(R, days):
    """Gün-kümeli t istatistiği."""
    R = np.asarray(R, float); m = ~np.isnan(R); R, days = R[m], np.asarray(days)[m]
    df = pd.DataFrame({"R": R, "d": days}).groupby("d").R.agg(["sum", "size"])
    mu = R.mean()
    G = len(df)
    if G < 3:
        return np.nan
    resid = df["sum"] - mu * df["size"]
    se = np.sqrt((resid ** 2).sum() * G / (G - 1)) / len(R)
    return mu / se if se > 0 else np.nan
