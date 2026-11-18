"""Adım 12 — kutudaki MT5 geçmiş dosyaları (bases/Pepperstone-Demo/history/NAS100/<YIL>.hcc) → NAS100 M1.

Terminal 'grafikteki azami bar' (100.000) yüzünden copy_rates_* yalnız son ~100 günün M1'ini veriyor; diskteki yıl dosyaları
2017'den beri M1 tutuyor. Kullanıcı ayar değişikliği yerine SALT OKUMA'yı seçti (2026-11-17): dosyalar
calistir/arac_mt5_gecmis_liste.py --yukle ile alındı (out/hcc/, git dışı; 2026.hcc terminal kilidinde, okunamadı).

Biçim (ölçüldü): kayıtlar sıkıştırılmamış MqlRates (60 bayt: time i64, open/high/low/close f64, tick_volume i64,
spread i32, real_volume i64) blok blok, blok başlıkları yüzünden değişken hizada. Ayrıştırıcı her bayt hizasında
geçerli kayıt arar: time dosyanın yılında ve dakika katı; high ≥ max(open, close) ≥ min(open, close) ≥ low > 0;
spread 0..10.000; tick_volume ≥ 0. `t` sunucu duvar saati (NY+7) → UTC'ye çevrilir.
UYARI (ölçüldü): 2009–2016 ve 2017'nin bir kısmında dosya M1 değil H1/D1 kaydı tutuyor → gün ancak M1 ise kabul
(medyan aralık 60 sn ve dakika sayısı ≥ yerli kapsamın %80'i).
DOĞRULUK s04'te sınanmaz, burada: ayrıştırılan M1'den kurulan M5/M15/M30, MT5'in KENDİ yerli M5/M15/M30 barlarıyla
gün gün birebir kıyaslanır; yalnız bütün yerli barları birebir tutan günler `out/ek/mt5_hcc_m1.parquet`'e yazılır.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import kaynak as K  # noqa: E402
import s03_uret as U  # noqa: E402
import s05_ek_kaynak as S  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
HCC_DIR = BASE / "out/hcc"
REC = 60
M1_MIN_SHARE = 0.80  # gün M1 sayılması için: dakika sayısı ≥ yerli barların kapsadığı dakikaların %80'i, medyan aralık 60 sn


def parse_hcc(path: Path, year: int) -> pd.DataFrame:
    b = np.frombuffer(path.read_bytes(), dtype=np.uint8)
    lo = int(pd.Timestamp(f"{year}-01-01").value // 10**9) - 86400
    hi = int(pd.Timestamp(f"{year + 1}-01-01").value // 10**9) + 86400
    out = []
    for a in range(8):  # her bayt hizası
        n = (len(b) - a - REC) // 1
        if n <= 0:
            continue
        # aday konumlar: bu hizada 8-bayt i64 zaman alanı
        view = b[a:a + (len(b) - a) // 8 * 8].view("<i8")
        cand = np.flatnonzero((view >= lo) & (view < hi) & (view % 60 == 0))
        pos = a + cand * 8
        pos = pos[pos + REC <= len(b)]
        if not len(pos):
            continue
        raw = np.stack([b[p:p + REC] for p in pos]) if len(pos) < 50_000 else None
        if raw is None:  # bellek dostu vektörleştirme
            idx = pos[:, None] + np.arange(REC)[None, :]
            raw = b[idx]
        f = raw[:, 8:40].copy().view("<f8")
        o, h, l, c = f[:, 0], f[:, 1], f[:, 2], f[:, 3]
        tv = raw[:, 40:48].copy().view("<i8")[:, 0]
        sp = raw[:, 48:52].copy().view("<i4")[:, 0]
        ok = (h >= np.maximum(o, c)) & (np.minimum(o, c) >= l) & (l > 0) & (h < 1e6) & (sp >= 0) & (sp <= 10_000) & (tv >= 0)
        ok &= np.isfinite(o) & np.isfinite(c)
        t = raw[:, :8].copy().view("<i8")[:, 0]
        out.append(pd.DataFrame({"t_srv": t[ok], "open": o[ok], "high": h[ok], "low": l[ok], "close": c[ok],
                                 "vol": tv[ok].astype(float), "sp": sp[ok]}))
    d = pd.concat(out) if out else pd.DataFrame()
    return d.drop_duplicates("t_srv").sort_values("t_srv").reset_index(drop=True)


def finest_verdicts(df: pd.DataFrame, natives: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Her gün, o gün için mevcut EN İNCE yerli MT5 barına (M5 → M15 → M30 → H1) karşı birebir sınanır."""
    out = None
    for tf in sorted(natives):
        v = S.day_verdicts(df, 1, {tf: natives[tf], **{k: natives[k].iloc[:0] for k in (5, 15, 30) if k != tf}})
        if not len(v) or int(v["ref_tf"].iloc[0]) != tf:
            continue
        v = v[v["yerli"] > 0]
        out = v if out is None else pd.concat([out, v[~v.index.isin(out.index)]])
    return out.sort_index() if out is not None else pd.DataFrame()


def main() -> None:
    srcs = U.mt5_sources()
    h1 = U.union([K.load_mt5_native("H1", K.MT5_DIR_A), U._fresh("H1")], "MT5 H1")
    natives = {5: srcs["M5"], 15: srcs["M15"], 30: srcs["M30"], 60: h1}
    rep, keep = {}, []
    for p in sorted(HCC_DIR.glob("*.hcc")):
        y = int(p.stem)
        d = parse_hcc(p, y)
        if d.empty:
            rep[y] = {"bar": 0}
            continue
        # aynı zamanda iki farklı değerli kayıt (bozuk ayrıştırma işareti) var mı?
        df = pd.DataFrame({"t": K.server_to_utc(d["t_srv"].to_numpy()), "open": d["open"], "high": d["high"],
                           "low": d["low"], "close": d["close"], "vol": d["vol"], "spr": d["sp"] * K.MT5_POINT})
        df, n_closed = U.drop_closed_hour(K._finish(df))  # sunucu 00:00 = NY 17:00: günlük özet kaydı, M1 değil
        v = finest_verdicts(df, natives)
        if len(v):  # M1 olma koşulu: eski yıllarda dosya H1/D1 kaydı tutuyor; bunlar yerli H1 ile kendiliğinden eşleşir
            day_all = pd.Series(S.trading_day(df["t"].to_numpy()))
            st = pd.DataFrame({"gun": day_all, "t": df["t"].to_numpy()}).groupby("gun")["t"].agg(
                n="size", gap=lambda x: float(np.median(np.diff(np.sort(x.to_numpy())))) if len(x) > 1 else 0.0)
            v = v.join(st, how="left")
            v["m1_mi"] = (v["gap"] == 60) & (v["n"] >= M1_MIN_SHARE * v["yerli"] * v["ref_tf"])
            v["kabul"] = v["kabul"] & v["m1_mi"]
        acc = v.index[v["kabul"]] if len(v) else []
        day = S.trading_day(df["t"].to_numpy())
        kept = df[np.isin(day, np.array(acc, dtype="datetime64[ns]"))]
        keep.append(kept)
        rep[y] = {"bar": int(len(df)), "bas": str(pd.to_datetime(df.t.min(), unit="s")), "bit": str(pd.to_datetime(df.t.max(), unit="s")),
                  "sinanan_gun": int(len(v)), "kabul_gun": int(len(acc)), "ref": v["ref_tf"].value_counts().to_dict() if len(v) else None,
                  "kabul_bar": int(len(kept)), "atilan_kapali_saat_kaydi": n_closed,
                  "m1_olmayan_gun": int((~v["m1_mi"]).sum()) if len(v) else 0}
        print(y, rep[y], flush=True)
    out = pd.concat(keep).drop_duplicates("t").sort_values("t").reset_index(drop=True) if keep else pd.DataFrame(columns=K.COLS)
    (BASE / "out/ek").mkdir(parents=True, exist_ok=True)
    out.to_parquet(BASE / "out/ek/mt5_hcc_m1.parquet", index=False)
    rep["toplam_kabul_bar"] = int(len(out))
    (BASE / "results/s12_hcc.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
