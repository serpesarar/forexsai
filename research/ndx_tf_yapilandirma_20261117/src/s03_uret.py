"""Adım 3 — 2, 3, 90, 210 dk mumları üret (besleme başına, karıştırmadan).

DUKA       : Dukascopy 1m (2018-01 → 2026-11-12) → dört zaman dilimi de 1m'den.
MT5        : Pepperstone NAS100 (bugünkü broker). 2/3 dk M1'den: terminal M1 dosyaları + kutudan taze çekim
             (`out/kutu_taze`) + s05'te MT5'in yerli M5'iyle gün gün birebir doğrulanmış kopya günleri
             (`kaynak_tf = M1_kopya`). 90/210 dk her kova için onu TAMAMEN kapsayan en ince kaynaktan:
             M1 > M5 > M15 > M30 (M30 2018-05'ten). Kaynakların ortak kovalarda birebir aynı çıktığı s04'te sınanır.
USTEC      : önceki broker hesabının USTEC 1m beslemesi (2026-02-10 → 06-12; s05: NAS100'den ayrı fiyat, saat
             ekseni Dukascopy'ye karşı gecikme 0). Dört zaman dilimi 1m'den.
Aynı beslemenin üst üste binen dosyaları birleştirilirken ortak barların birebir aynı olması DAYATILIR.

DUKA mumlarına fitil denetimi sütunları eklenir (`fitil_durumu`): eksik dakikası olan mumun fitili, aynı
penceredeki MT5 (yoksa USTEC) mumuyla seviye farkı düzeltilerek kıyaslanır (s06 bulgusu: Dukascopy hızlı
haber anlarında dakika kaçırıp fitili kesebiliyor — ör. 2026-03-23 11:05 UTC).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import kaynak as K  # noqa: E402
import tf_motor as M  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "out"
TFS = (2, 3, 90, 210)
MT5_COARSE = (("M1", 1), ("M5", 5), ("M15", 15), ("M30", 30))
EXTRA_FEEDS = (("EET30", 30), ("NQ", 5))  # s08 çıktısı: (besleme, kaynak TF dk)
EXT_M1 = OUT / "ek/mt5_m1_ek_gunler.parquet"
DAY_END_SLACK_MIN = 10  # veri günün son 10 dk'sında bitiyorsa (Cuma kapanışı) gün tamamdır
WICK_SUSPECT_RATIO = 0.20  # fitil sapması > karşı mumun aralığının %20'si → şüpheli (yalnız eksik dakikalı mumda)


def union(frames: list[pd.DataFrame], name: str = "") -> pd.DataFrame:
    """Aynı beslemenin üst üste binen dosyaları: ortak barlar birebir aynı olmalı."""
    x = pd.concat([f for f in frames if f is not None and len(f)], ignore_index=True)
    d = x.groupby("t")[["open", "high", "low", "close"]].agg(lambda s: s.max() - s.min())
    if float(d.to_numpy().max(initial=0)) > 1e-9:
        bad = d[d.max(axis=1) > 1e-9]
        raise AssertionError(f"{name}: aynı beslemenin dosyaları {len(bad)} ortak barda ayrışıyor "
                             f"(ilk {pd.to_datetime(bad.index[0], unit='s')})")
    return x.drop_duplicates("t").sort_values("t").reset_index(drop=True)


def _fresh(tf: str) -> pd.DataFrame | None:
    p = K.KUTU_TAZE / f"NAS100_{tf}.csv.gz"
    return K.load_mt5_native(tf, K.KUTU_TAZE) if p.exists() else None


def mt5_sources() -> dict[str, pd.DataFrame]:
    return {
        "M1": union([K.load_mt5_native("M1", K.MT5_DIR_A), K.load_mt5_native("M1", K.MT5_DIR_B),
                     K.load_mt5_utc_csv(K.MT5_UTC_CSV[0]), K.load_mt5_utc_csv(K.MT5_UTC_CSV[1]), _fresh("M1")], "MT5 M1"),
        "M5": union([K.load_mt5_native("M5", K.MT5_DIR_A), K.load_mt5_native("M5", K.MT5_DIR_B), _fresh("M5")], "MT5 M5"),
        "M15": union([K.load_mt5_native("M15", K.MT5_DIR_A), _fresh("M15")], "MT5 M15"),
        "M30": union([K.load_mt5_native("M30", K.MT5_DIR_A), _fresh("M30")], "MT5 M30"),
    }


HCC_M1 = OUT / "ek/mt5_hcc_m1.parquet"  # s12: kutudaki MT5 yıl dosyalarından, yerli M30'la gün gün doğrulanmış M1


def mt5_m1_with_copies(m1: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Terminal M1 + MT5 geçmiş dosyaları (s12) + doğrulanmış kopya günleri. Ortak barlar birebir olmak zorunda.
    Dönüş: birleşik M1 ve 'terminalin copy_rates'inde yok' maskesi."""
    parts = [m1]
    for p in (HCC_M1, EXT_M1):
        if p.exists():
            parts.append(pd.read_parquet(p)[K.COLS])
    if len(parts) == 1:
        return m1, np.zeros(len(m1), bool)
    merged = union(parts, "MT5 M1 + geçmiş dosyaları + kopya günleri")
    return merged, ~merged["t"].isin(m1["t"]).to_numpy()


def hcc_keys(tf: int) -> pd.Series:
    if not HCC_M1.exists():
        return pd.Series(dtype=np.int64)
    h, _ = drop_closed_hour(pd.read_parquet(HCC_M1)[K.COLS])
    return M.aggregate(h, 1, tf)["t"]


def ustec_1m() -> pd.DataFrame:
    return union([K.load_ustec_json(p) for p in K.USTEC_JSON], "USTEC")


def full_days(src: pd.DataFrame, src_tf: int) -> set:
    """Kaynağın baştan sona kapsadığı işlem günleri (verinin ilk/son günü yarımsa hariç)."""
    d0, mins = M.day_minute(src["t"].to_numpy())
    g = pd.DataFrame({"d": d0, "m": mins}).groupby("d")["m"].agg(["min", "max"])
    days = set(g.index)
    first, last = g.index.min(), g.index.max()
    if g.loc[first, "min"] > M.CLOSED_UNTIL_MIN:  # ilk gün 18:00 açılışından sonra başlıyorsa yarım
        days.discard(first)
    if g.loc[last, "max"] + src_tf < M.DAY_MIN - DAY_END_SLACK_MIN:
        days.discard(last)
    return days


def assign_days(srcs: dict[str, pd.DataFrame], order) -> dict:
    """Gün → kaynak adı: sıradaki (en ince) kaynak o günü tam kapsıyorsa o."""
    out: dict = {}
    for name, stf in order:
        for d in full_days(srcs[name], stf):
            out.setdefault(d, name)
    return out


def drop_closed_hour(src: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """NY 17:00–17:59 barı varsa (günlük ara) sayılır ve atılır — işlem yok, dolgu barıdır."""
    _, mins = M.day_minute(src["t"].to_numpy())
    bad = mins < M.CLOSED_UNTIL_MIN
    return src.loc[~bad].reset_index(drop=True), int(bad.sum())


def covered(out: pd.DataFrame, src: pd.DataFrame, src_tf: int) -> np.ndarray:
    """Kova kaynağın kapsadığı aralıkta mı? Verinin başı/sonundaki yarım kovaları eler."""
    lo, hi = int(src["t"].iloc[0]), int(src["t"].iloc[-1]) + src_tf * 60
    _, last_min = M.day_minute(src["t"].to_numpy()[-1:])
    if last_min[0] + src_tf >= M.DAY_MIN - DAY_END_SLACK_MIN:
        hi += (M.DAY_MIN - last_min[0] - src_tf) * 60
    start = out["t"].to_numpy()
    end = start + out["sure_dk"].to_numpy() * 60
    # açılış barı kapalı saatteyse (17:00) ilk işlem dakikası 18:00 olduğundan ona göre bakılır
    first_trade = start + np.where(out["zaman_ny"].dt.hour.to_numpy() == M.DAY_START_H,
                                   M.CLOSED_UNTIL_MIN * 60, 0)
    return (first_trade >= lo) & (end <= hi)


def build_1m_feed(src: pd.DataFrame, feed: str, closed: tuple, label: str) -> dict[int, pd.DataFrame]:
    out = {}
    for tf in TFS:
        a = M.aggregate(src, 1, tf, label, closed)
        out[tf] = a[covered(a, src, 1)].reset_index(drop=True)
    return out


def annotate_duka_wicks(d: pd.DataFrame, refs: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    """Eksik dakikalı DUKA mumunun fitilini başka beslemenin aynı penceredeki mumuyla kıyasla."""
    d = d.copy()
    d["karsi_besleme"] = pd.Series([None] * len(d), dtype=object)
    d["fitil_sapma_orani"] = np.nan
    for name, r in refs:
        x = d[["t", "open", "high", "low", "close"]].merge(r[["t", "open", "high", "low", "close"]], on="t",
                                                           suffixes=("", "_r"))
        x = x[~x["t"].isin(d.loc[d["karsi_besleme"].notna(), "t"])]
        off = ((x.open - x.open_r) + (x.close - x.close_r)) / 2  # beslemeler arası seviye farkı
        dev = np.maximum(np.abs(x.high - (x.high_r + off)), np.abs(x.low - (x.low_r + off)))
        rng = (x.high_r - x.low_r).replace(0, np.nan)
        idx = d.index[d["t"].isin(x["t"])]
        d.loc[idx, "karsi_besleme"] = name
        d.loc[idx, "fitil_sapma_orani"] = (dev / rng).round(4).to_numpy()
    suspicious = d["fitil_sapma_orani"] > WICK_SUSPECT_RATIO
    d["fitil_durumu"] = np.select(
        [d["tam"], d["karsi_besleme"].isna(), suspicious],
        ["tam", "eksik_dakika_teyitsiz", "eksik_dakika_supheli"], default="eksik_dakika_teyitli")
    return d


def save(df: pd.DataFrame, feed: str, tf: int) -> str:
    d = OUT / feed
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"NDX_{feed}_{tf}m.parquet"
    df.to_parquet(p, index=False)
    csv = df.assign(zaman_utc=df.zaman_utc.dt.strftime("%Y-%m-%d %H:%M"),
                    zaman_ny=df.zaman_ny.dt.strftime("%Y-%m-%d %H:%M%z"))
    csv.to_csv(d / f"NDX_{feed}_{tf}m.csv.gz", index=False, float_format="%.3f")
    return str(p.relative_to(BASE))


def summary(df: pd.DataFrame) -> dict:
    r = {"n": int(len(df)), "bas": str(df.zaman_utc.iloc[0]), "bit": str(df.zaman_utc.iloc[-1]),
         "tam_%": round(100 * float(df.tam.mean()), 2), "kaynak_tf": df.kaynak_tf.value_counts().to_dict()}
    if "fitil_durumu" in df:
        r["fitil_durumu"] = df.fitil_durumu.value_counts().to_dict()
    return r


def main() -> None:
    meta: dict = {"capa": "NY 17:00 işlem günü başı, günlük sıfırlama", "DUKA": {}, "MT5": {}, "USTEC": {}}

    # ── MT5 NAS100 ──
    srcs = mt5_sources()
    for k in list(srcs):
        srcs[k], n_closed = drop_closed_hour(srcs[k])
        meta["MT5"][f"atilan_kapali_saat_bari_{k}"] = n_closed
        meta["MT5"][f"kaynak_{k}"] = {"n": len(srcs[k]), "bas": str(pd.to_datetime(srcs[k].t.iloc[0], unit="s")),
                                      "bit": str(pd.to_datetime(srcs[k].t.iloc[-1], unit="s"))}
    m1_all, is_copy = mt5_m1_with_copies(srcs["M1"])
    meta["MT5"]["kopya_gun_bar"] = int(is_copy.sum())
    mt5_out: dict[int, pd.DataFrame] = {}
    for tf in (2, 3):
        a = M.aggregate(m1_all, 1, tf, "M1", M.CLOSED["MT5"])
        a = a[covered(a, m1_all, 1)].reset_index(drop=True)
        copy_keys = M.aggregate(m1_all[is_copy].reset_index(drop=True), 1, tf)["t"] if is_copy.any() else []
        a.loc[a["t"].isin(copy_keys), "kaynak_tf"] = "M1_kopya"
        a.loc[a["t"].isin(hcc_keys(tf)) & (a["kaynak_tf"] == "M1_kopya"), "kaynak_tf"] = "M1_gecmis"
        mt5_out[tf] = a
    coarse = dict(srcs)
    if HCC_M1.exists():  # en düşük öncelik: yerli M30'un başladığı 2018-05 öncesini (2017-06 →) doldurur
        coarse["M1_gecmis"], _ = drop_closed_hour(pd.read_parquet(HCC_M1)[K.COLS])
    order = MT5_COARSE + ((("M1_gecmis", 1),) if "M1_gecmis" in coarse else ())
    day_src = assign_days(coarse, order)  # her işlem günü TEK kaynaktan: o günü baştan sona kapsayan en ince
    for tf in (90, 210):
        parts = []
        for name, stf in order:
            a = M.aggregate(coarse[name], stf, tf, name, M.CLOSED["MT5"])
            a = a[covered(a, coarse[name], stf)]
            d0, _ = M.day_minute(a["t"].to_numpy())
            parts.append(a[pd.Series(d0).map(day_src).to_numpy() == name])
        mt5_out[tf] = pd.concat(parts).sort_values("t").reset_index(drop=True)
    for tf, a in mt5_out.items():
        meta["MT5"][f"{tf}m"] = summary(a) | {"dosya": save(a, "MT5", tf)}

    # ── USTEC (önceki broker) ──
    us, n_closed = drop_closed_hour(ustec_1m())
    meta["USTEC"]["atilan_kapali_saat_bari"] = n_closed
    us_out = build_1m_feed(us, "USTEC", M.CLOSED["MT5"], "1m")
    for tf, a in us_out.items():
        meta["USTEC"][f"{tf}m"] = summary(a) | {"dosya": save(a, "USTEC", tf)}

    # ── EET30 ve NQ (ev dizininden, s08'de ay/hafta kalibre) ──
    ext_out: dict[str, dict[int, pd.DataFrame]] = {}
    for feed, stf in EXTRA_FEEDS:
        p = OUT / f"ek/{feed}_kalibre.parquet"
        if not p.exists():
            continue
        src, n_closed = drop_closed_hour(pd.read_parquet(p)[K.COLS])
        meta[feed] = {"atilan_kapali_saat_bari": n_closed}
        ext_out[feed] = {}
        for tf in (90, 210):
            a = M.aggregate(src, stf, tf, f"{stf}m", M.CLOSED["MT5"])
            a = a[covered(a, src, stf)].reset_index(drop=True)
            ext_out[feed][tf] = a
            meta[feed][f"{tf}m"] = summary(a) | {"dosya": save(a, feed, tf)}

    # ── DUKA ──
    duka, n_closed = drop_closed_hour(K.load_duka_1m())
    meta["DUKA"]["atilan_kapali_saat_bari"] = n_closed
    m30x, _ = drop_closed_hour(K.load_duka_m30_export())
    for tf, a in build_1m_feed(duka, "DUKA", M.CLOSED["DUKA"], "1m").items():
        if tf in (90, 210):  # 1 dk'nın başlamadığı 2016-03 → 2018-01: Dukascopy'nin kendi M30 dışa aktarımından
            pre = M.aggregate(m30x, 30, tf, "M30_disaktarim", M.CLOSED["DUKA"])
            pre = pre[covered(pre, m30x, 30) & (pre["t"] + pre["sure_dk"] * 60 <= a["t"].iloc[0])]
            a = pd.concat([pre, a]).sort_values("t").reset_index(drop=True)
        refs = [("MT5_NAS100", mt5_out[tf]), ("MT5_USTEC", us_out[tf])]
        refs += [(f, ext_out[f][tf]) for f in ext_out if tf in ext_out[f]]
        a = annotate_duka_wicks(a, refs)
        meta["DUKA"][f"{tf}m"] = summary(a) | {"dosya": save(a, "DUKA", tf)}

    (BASE / "results/s03_uretim.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print(json.dumps(meta, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
