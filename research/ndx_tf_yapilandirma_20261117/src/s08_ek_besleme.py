"""Adım 8 — ev dizinindeki (proje dışı) iki ayrı NASDAQ beslemesi: saat ekseni ay ay kalibre edilir.

EET30 : ~/Desktop/Trading Projeleri/nasdaq/nasdaq100_30min_full.csv — bir MT broker'ının 30 dk dışa aktarımı
        (2016-11 → 2025-10, tik hacimli). Damga Europe/Athens (UTC+2/+3, AB yaz saati) duvar saati, bar açılışı.
NQ    : ~/Desktop/Trading Projeleri/nasdaq/NQ_5Years_8_11_2024.csv — NQ vadeli 5 dk, geriye ayarlı sürekli seri
        (seviye CFD'den ~1.390 puan yukarıda). Damga bar KAPANIŞI; saat dilimi dosya içinde değişiyor.

Hafta kabul ölçütü (ÖN KAYIT, sonuçlara bakmadan): referansa (Dukascopy 1 dk→TF; 2018 öncesi Dukascopy M30 dışa
aktarımı) karşı getiri korelasyonu bar gecikmesi −3..+3'te taranır; KABUL = en iyi gecikme 0 VE r(0) ≥ 0,90 VE
r(0) − max(r(−1), r(+1)) ≥ 0,30. (+ sonradan: çevrilmiş saatte hafta sonuna düşen bar ≤ 3 ve onlar atılır; fazlası haftayı reddeder — bkz. out_of_session) NQ'da her hafta aday kurallar (New York / Berlin / sabit UTC+1 / UTC+2, kapanış
etiketi) içinden r(0)'ı en yüksek olan seçilir. Kabul edilen haftaların barları `out/ek/{EET30,NQ}_kalibre.parquet`
(t = gerçek UTC bar açılışı) olarak yazılır; s03 bunlardan 90/210 dk mum üretir (2/3 dk bu TF'lerden kurulamaz).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import dis_okuyucu as R  # noqa: E402
import kaynak as K  # noqa: E402
import s05_ek_kaynak as S  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
EET30_FILE = R.HOME / "Desktop/Trading Projeleri/nasdaq/nasdaq100_30min_full.csv"
NQ_FILE = R.HOME / "Desktop/Trading Projeleri/nasdaq/NQ_5Years_8_11_2024.csv"
DUKA_M30_EXPORT = R.HOME / "Downloads/USATECHIDXUSD30.csv"
R0_MIN, MARGIN_MIN, LAGS = 0.90, 0.30, range(-3, 4)
MIN_N = 60  # bir dönemde korelasyon için asgari ortak bar


def to_utc(wall: pd.Series, zone: str, close_label_min: int) -> np.ndarray:
    if zone.startswith("UTC+"):
        t = (wall.astype("int64") // 10**9).to_numpy(dtype=float) - int(zone[4:]) * 3600
    else:
        loc = wall.dt.tz_localize(zone, ambiguous="NaT", nonexistent="NaT")
        t = (loc.dt.tz_convert("UTC").astype("int64") // 10**9).to_numpy(dtype=float)
        t[loc.isna().to_numpy()] = np.nan
    return t - close_label_min * 60


MAX_STRAY = 3  # haftada en çok bu kadar seans dışı bar → yalnız onlar atılır; fazlası → hafta reddedilir


def session_mask(t: np.ndarray) -> np.ndarray:
    """True = seans içi (ya da NaN olmayan ve hafta sonuna düşmeyen)."""
    out = np.ones(len(t), bool)
    ok = ~np.isnan(t)
    ny = pd.to_datetime(t[ok].astype(np.int64), unit="s", utc=True).tz_convert("America/New_York")
    dow, hr = ny.dayofweek, ny.hour
    out[ok] = ~((dow == 4) & (hr >= 17) | (dow == 5) | (dow == 6) & (hr < 18))
    return out


def out_of_session(t: np.ndarray) -> int:
    """Çevrilmiş saatte hafta sonuna düşen bar sayısı (Cuma ≥17:00, Cumartesi, Pazar <18:00 NY). >0 → saat kayık.
    (Ölçüt sonradan eklendi: NQ 2021-10-31 ve 2022-03-13 AB/ABD ayrışma haftaları korelasyonda geçip 1 sa kayıktı.)"""
    tt = t[~np.isnan(t)].astype(np.int64)
    ny = pd.to_datetime(tt, unit="s", utc=True).tz_convert("America/New_York")
    dow, hr = ny.dayofweek, ny.hour
    return int(((dow == 4) & (hr >= 17) | (dow == 5) | (dow == 6) & (hr < 18)).sum())


def lag_curve(t: np.ndarray, close: np.ndarray, ref_ret: pd.Series, tf: int) -> dict[int, float]:
    s = pd.Series(close, index=t).dropna()
    s = s[~np.isnan(s.index)]
    s.index = s.index.astype(np.int64)
    s = s[~s.index.duplicated()].sort_index()
    out = {}
    for lag in LAGS:
        rc = pd.Series(s.to_numpy(), index=s.index + lag * tf * 60).pct_change()
        j = pd.concat([ref_ret, rc], axis=1, join="inner").dropna()
        out[lag] = float(j.corr().iloc[0, 1]) if len(j) > MIN_N else np.nan
    return out


def calibrate(df: pd.DataFrame, tf: int, ref: pd.DataFrame, rules: list[tuple[str, int]],
              period: str = "M", min_n: int = 100) -> tuple[pd.DataFrame, list[dict]]:
    """Dönem dönem (ay; reddedilen ay için hafta — kural ay ortasında değişebiliyor) saat kuralı + kabul."""
    ref_ret = ref.set_index("t")["close"].pct_change()
    # işlem haftası: Pazar akşamı açılan seans SONRAKİ haftaya aittir (dosya saati NY'den en çok ±7 sa farklı)
    df = df.assign(ay=(df["wall"] + pd.Timedelta(hours=12)).dt.to_period(period))
    keep, rows = [], []
    for ay, g in df.groupby("ay"):
        best = None
        for zone, lab in rules:
            t = to_utc(g["wall"], zone, lab)
            c = lag_curve(t, g["close"].to_numpy(), ref_ret, tf)
            if np.isnan(c[0]):
                continue
            if best is None or c[0] > best[2][0]:
                best = (zone, lab, c, t)
        if best is None:
            rows.append({"ay": str(ay), "kabul": False, "neden": "referansla çakışma yok"})
            continue
        zone, lab, c, t = best
        side = max(c[-1], c[1])
        arg = max(c, key=lambda k: -np.inf if np.isnan(c[k]) else c[k])
        off = out_of_session(t)
        ok = arg == 0 and c[0] >= R0_MIN and c[0] - side >= MARGIN_MIN and off <= MAX_STRAY
        rows.append({"ay": str(ay), "kural": f"{zone}{' kapanış' if lab else ''}", "r0": round(c[0], 3),
                     "r±1": round(side, 3), "en_iyi_gecikme": arg, "seans_disi_bar": off, "kabul": bool(ok)})
        if ok:
            if off:  # kaynakta başıboş seans dışı bar(lar): yalnız onlar atılır
                t = np.where(session_mask(t), t, np.nan)
            keep.append(pd.DataFrame({"t": t, "open": g["open"].to_numpy(), "high": g["high"].to_numpy(),
                                      "low": g["low"].to_numpy(), "close": g["close"].to_numpy(),
                                      "vol": g["vol"].to_numpy()}).dropna(subset=["t"]))
    out = pd.concat(keep) if keep else pd.DataFrame(columns=K.COLS)
    out["t"] = out["t"].astype(np.int64)
    out["spr"] = np.nan
    return out.drop_duplicates("t").sort_values("t").reset_index(drop=True)[K.COLS], rows


def duka_reference(tf: int) -> pd.DataFrame:
    d = S.regroup(K.load_duka_1m(), tf)
    if tf == 30:  # 2018 öncesi: Dukascopy'nin kendi M30 dışa aktarımı (1 dk'dan kurulanla %99,96 aynı)
        e = R.read_ohlc(DUKA_M30_EXPORT)
        e = pd.DataFrame({"t": e["wall"].astype("int64") // 10**9, "close": e["close"]})
        d = pd.concat([e[e["t"] < d["t"].min()], d[["t", "close"]]])
    return d.sort_values("t")


def main() -> None:
    rep = {}
    (BASE / "out/ek").mkdir(parents=True, exist_ok=True)
    jobs = [("EET30", EET30_FILE, 30, [("Europe/Athens", 0)]),
            ("NQ", NQ_FILE, 5, [("America/New_York", 5), ("Europe/Berlin", 5), ("UTC+1", 5), ("UTC+2", 5)])]
    for name, path, tf, rules in jobs:
        raw = R.read_ohlc(path)
        ref = duka_reference(tf)
        # HAFTALIK kalibrasyon: ABD/AB yaz saati ayrışma haftalarında (Mart/Ekim-Kasım 2-3 hafta) aylık kural bir saat
        # kayık kalabiliyordu (NQ 2022-03-13 Pazar 15:10 ET barı bunu gösterdi).
        cal, rows = calibrate(raw, tf, ref, rules, period="W")
        for r in rows:
            r["hafta"] = r.pop("ay")
        cal.to_parquet(BASE / f"out/ek/{name}_kalibre.parquet", index=False)
        weeks = rows
        rep[name] = {"dosya": str(path).replace(str(R.HOME), "~"), "tf_dk": tf, "ham_bar": len(raw),
                     "hafta": len(weeks), "kabul_hafta": sum(r["kabul"] for r in weeks),
                     "kurallar": pd.Series([r.get("kural") for r in weeks if r["kabul"]]).value_counts().to_dict(),
                     "kabul_bar": len(cal), "kabul_bar_%": round(100 * len(cal) / len(raw), 2), "donemler": rows}
        print(name, {k: v for k, v in rep[name].items() if k != "donemler"})
        for r in weeks:
            if not r["kabul"]:
                print("   red hafta", r)
    (BASE / "results/s08_ek_besleme.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
