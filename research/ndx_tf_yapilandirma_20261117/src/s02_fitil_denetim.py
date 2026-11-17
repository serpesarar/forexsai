"""Adım 2 — kaynak 1m barlarda yalıtık fitil sıçraması (bad tick) denetimi.

Bir 1m barın fitili üst zaman dilimlerine birebir taşınır; yanlış bir tik 90/210 dk mumun
tepesini/dibini de bozar. Aday tanımı (sonuca bakmadan sabit):
    üst fitil u = high − max(open, close),   alt fitil d = min(open, close) − low
    ölçek s = o NY işlem gününün 1m aralık (high−low) medyanı
    aday: u > K·s VE high, komşu iki barın high'larının en büyüğünü K·s'den fazla aşıyor
          (alt fitil için simetrik). K = 12.
İki beslemenin ortak dakikalarında aday diğer beslemede de varsa (aynı dakikada diğer
beslemenin fitili ≥ K/3·s) → GERÇEK hareket; yoksa → şüpheli tik.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import kaynak as K  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
K_SPIKE = 12.0


def trading_day(t: np.ndarray) -> np.ndarray:
    ny = pd.to_datetime(t, unit="s", utc=True).tz_convert(K.NY).tz_localize(None)
    return (ny - pd.Timedelta(hours=17)).normalize().to_numpy()


def spike_candidates(df: pd.DataFrame) -> pd.DataFrame:
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    rng = h - l
    day = trading_day(df["t"].to_numpy())
    s = pd.Series(rng).groupby(day).transform("median").to_numpy()
    s = np.where(s > 0, s, np.nan)
    hp, hn = np.r_[np.nan, h[:-1]], np.r_[h[1:], np.nan]
    lp, ln = np.r_[np.nan, l[:-1]], np.r_[l[1:], np.nan]
    up = (h - np.maximum(o, c) > K_SPIKE * s) & (h - np.fmax(hp, hn) > K_SPIKE * s)
    dn = (np.minimum(o, c) - l > K_SPIKE * s) & (np.fmin(lp, ln) - l > K_SPIKE * s)
    out = df.loc[up | dn, ["t", "open", "high", "low", "close"]].copy()
    out["yon"] = np.where(up[up | dn], "ust", "alt")
    out["olcek"] = s[up | dn]
    out["ts_utc"] = pd.to_datetime(out["t"], unit="s")
    return out


def confirm(cands: pd.DataFrame, other: pd.DataFrame) -> pd.DataFrame:
    m = cands.merge(other[["t", "open", "high", "low", "close"]], on="t", how="left", suffixes=("", "_d"))
    u_d = m["high_d"] - np.maximum(m["open_d"], m["close_d"])
    d_d = np.minimum(m["open_d"], m["close_d"]) - m["low_d"]
    wick_d = np.where(m["yon"] == "ust", u_d, d_d)
    m["diger_besleme"] = np.where(m["high_d"].isna(), "yok",
                                  np.where(wick_d >= K_SPIKE / 3 * m["olcek"], "teyit", "teyitsiz"))
    return m


def main() -> None:
    duka = K.load_duka_1m()
    import s03_uret as U  # yükleyici/birleşim (taze kutu çekimi dahil)
    mt5 = U.mt5_sources()["M1"]
    ustec = U.ustec_1m()
    rep = {}
    keep = {}
    # her besleme, diğer bağımsız beslemeyle aynı dakikada teyit edilir
    for name, a, b in (("DUKA", duka, mt5), ("MT5", mt5, duka), ("USTEC", ustec, duka)):
        cd = confirm(spike_candidates(a), b)
        keep[name] = cd
        rep[name] = {"aday": int(len(cd)), **cd["diger_besleme"].value_counts().to_dict(),
                     "yila_gore": cd["ts_utc"].dt.year.value_counts().sort_index().to_dict()}
        cd.to_csv(OUT / f"s02_fitil_adaylari_{name}.csv", index=False)
    (OUT / "s02_fitil_denetim.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(rep, indent=1, ensure_ascii=False, default=str))
    for name, cd in keep.items():
        print("==", name)
        print(cd[["ts_utc", "yon", "open", "high", "low", "close", "olcek", "high_d", "low_d", "diger_besleme"]]
              .head(40).to_string())


if __name__ == "__main__" and "--m30" not in sys.argv:
    main()


def confirm_with_mt5_bar(cands: pd.DataFrame, duka: pd.DataFrame) -> pd.DataFrame:
    """Ortak 1m yoksa: adayı içeren MT5 M30 (yoksa H1) barında aynı uç var mı?

    Ölçü: fitilin bar gövdesinin ötesine taşan kısmı (ust: high − max(o,c)) Dukascopy'nin aynı
    30 dk penceresinde ve MT5 M30 barında; MT5 aynı pencerede ≥ yarısı kadar uzanıyorsa teyit.
    """
    m30 = K.load_mt5_native("M30", K.MT5_DIR_A).set_index("t")
    rows = []
    for _, r in cands.iterrows():
        w0 = int(r.t) - int(r.t) % 1800
        win = duka[(duka.t >= w0) & (duka.t < w0 + 1800)]
        if w0 not in m30.index or win.empty:
            rows.append("mt5_yok")
            continue
        b = m30.loc[w0]
        if r.yon == "ust":
            ext_d = win.high.max() - max(win.open.iloc[0], win.close.iloc[-1])
            ext_m = b.high - max(b.open, b.close)
        else:
            ext_d = min(win.open.iloc[0], win.close.iloc[-1]) - win.low.min()
            ext_m = min(b.open, b.close) - b.low
        rows.append("teyit" if ext_m >= 0.5 * ext_d else f"teyitsiz({ext_m:.0f}/{ext_d:.0f})")
    cands = cands.copy()
    cands["mt5_m30"] = rows
    return cands


if __name__ == "__main__" and "--m30" in sys.argv:
    d = K.load_duka_1m()
    c = pd.read_csv(OUT / "s02_fitil_adaylari_DUKA.csv")
    c = confirm_with_mt5_bar(c, d)
    c.to_csv(OUT / "s02_fitil_adaylari_DUKA.csv", index=False)
    print(c[["ts_utc", "yon", "olcek", "mt5_m30"]].to_string())
    print(c["mt5_m30"].str.split("(").str[0].value_counts().to_dict())
