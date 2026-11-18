"""Adım 5 — diskteki TÜM diğer NASDAQ mum dosyalarının hükmü ve doğrulanmış günlerin eklenmesi.

Her dosya üç sınıftan birine girer:
  türetilemez : günlük / 1 sa / 4 sa — 2, 3, 90, 210 dk bunlardan matematiksel olarak kurulamaz
                (90 ve 210, 60'ın katı değil; 2/3 dk ancak 1 dk'dan)
  DUKA ailesi : Dukascopy kopyaları — ana dosyayla ortak barlarda birebir mi, ana dosyada olmayan gün var mı
  MT5 ailesi  : broker kökenli kopyalar (candle_cache, USTEC json, sim_bot…) — işlem günü başına MT5'in
                KENDİ yerli barlarıyla (M5 → M15 → M30) birebir sınanır. Bir günün bütün yerli barları,
                kopyadan kurulan karşılığıyla tam eşitse gün KABUL; tek bar farklıysa RED (kayık / karışık
                besleme / eksik). Epoch damgalı dosyalar hem UTC hem sunucu saati (NY+7) olarak denenir.
Kabul edilen 1 dk günleri `out/ek/mt5_m1_ek_gunler.parquet`'e yazılır; s03 bunları terminal M1 ile birleştirir
(ortak barlar birebir olmak zorunda) ve terminalde olmayan barlardan kurulan 2/3 dk mumlara `kaynak_tf = M1_kopya` der.
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
R = K.ROOT
TOL = 1e-6

UNDERIVABLE = {
    "research/fitil_ret_20261106/data_d1_NDX.parquet": "günlük (Yahoo ^NDX)",
    "research/ndx_kapi_20261110/data/NDX.parquet": "günlük (Yahoo ^NDX)",
    "research/pythia_20261111/data/NDX.parquet": "günlük (Yahoo ^NDX)",
    "research/kasa_trend_20261028/data/NDX.csv": "günlük (Yahoo ^NDX)",
    "research/geri_cekilme_20261106/data/now_NDX.csv": "günlük (Yahoo ^NDX)",
    "research/yon_lab_20261114/data/xasset/NDX_1d.parquet": "günlük (Yahoo ^NDX)",
    "research/yon_lab_20261114/data/xasset/NDXF_1h.parquet": "1 sa (NQ vadeli, Yahoo)",
    "research/cortex_confluence/data/NQ_1h.csv": "1 sa (NQ vadeli)",
    "research/cortex_confluence/intraday/NQ.csv": "1 sa yalnız kapanış (NQ vadeli)",
    "research/nasdaq_derin_20261013/caprev_dax_recheck/data_fixed/ndx_long_1h_fixa.parquet": "1 sa (panel)",
    "research/nasdaq_derin_20261013/caprev_dax_recheck/data_fixed/ndx_long_1h_fixb.parquet": "1 sa (panel)",
    "backend/data/candle_history/NDX_1h.npz": "1 sa (panel candle_history)",
    "backend/data/candle_history/NDX_4h.npz": "4 sa (panel candle_history)",
    "sr_rejection_research/data/NDX.INDX_1h.json": "1 sa (panel)",
    "research/sim_bot/sig_NDX_INDX.json": "mum değil (sinyal listesi)",
}
DUKA_FAMILY = {
    "research/nom_20261113/data/ndx_1m_v1.parquet": "t",
    "research/nom_20261113/data/ndx_1m_v3.parquet": "t",
    "research/yon_lab_20261114/data/ndx_1m_v2.parquet": "t",
    "research/haber_derin_20261105/data/NDX_1m.parquet": "t",
    "research/nom_20261113/data/histdata_ndx_1m.parquet": "t",
    "research/fibo_altin_bolge_20261116/cache/ndx_1m.npz": "npz_local",
}
# MT5 ailesi: (yol, tf_dk)
MT5_FAMILY = [
    ("nasdaq_1m_candle_cache_2026-02-10_2026-08-29/nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv", 1),
    ("backend/data/nom_cache/ndx_1m.parquet", 1),
    ("ndx_reflex_engine/data/ustec_1m_2026.parquet", 1),
    ("research/fcr_ilk_mum_20261027/data/cache_NDX_1m.parquet", 1),
    ("output/islem_otopsi/_cache/NDX_INDX_1m_raw.parquet", 1),
    ("research/tp_sonrasi_ters_20261109/data/ndx_1m.parquet", 1),
    ("research/next_candidates/bars_NDX_INDX_1m.csv", 1),
    ("research/sim_bot/bars_NDX_INDX_1m.json", 1),
    ("research/trade_mgmt_ndx/bars_NAS100.csv", 1),
    ("sr_rejection_research/data/NDX.INDX_1m.json", 1),
    ("1MDATA/mt5_islem_analizi/nasdaq_1m.csv", 1),
    ("analiz_paketi_2026-07-09/prices/NDX_INDX_1m_son_14gun.csv", 1),
    ("bot_live_audit/bars/NDX.INDX_5m.json", 5),
    ("research/sim_bot/bars_NDX_INDX_5m.json", 5),
    ("research/dts_uyarlama_20261104/data/cc_NDX_5m.csv", 5),
    ("sr_rejection_research/data/NDX.INDX_5m.json", 5),
    ("backend/data/candle_history/NDX_5m.npz", 5),
    ("research/dts_uyarlama_20261104/data/cc_NDX_15m.csv", 15),
    ("backend/data/candle_history/NDX_15m.npz", 15),
    ("sr_rejection_research/data/NDX.INDX_30m.json", 30),
    ("backend/data/candle_history/NDX_30m.npz", 30),
]


# ── genel okuyucu ──────────────────────────────────────────────────────────────
def _to_epoch(x: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(x):
        return x.to_numpy().astype(np.int64)
    return (pd.to_datetime(x, utc=True).astype("int64") // 10**9).to_numpy()


def read_any(path: Path) -> tuple[pd.DataFrame, bool]:
    """→ (t,open,high,low,close,vol) ve 'epoch mu' (damga hem UTC hem sunucu olabilir)."""
    s = path.suffix
    if s == ".npz":
        z = np.load(path, allow_pickle=True)
        d = pd.DataFrame({k: z[k] for k in z.files})
    elif s == ".json":
        j = json.loads(path.read_text())
        d = pd.DataFrame(j["bars"] if isinstance(j, dict) else j)
    elif s == ".parquet":
        d = pd.read_parquet(path)
        if isinstance(d.index, pd.DatetimeIndex):
            d = d.reset_index().rename(columns={d.index.name or "index": "ts"})
    else:
        d = pd.read_csv(path)
    ren = {"o": "open", "h": "high", "l": "low", "c": "close", "v": "vol", "volume": "vol", "tick_volume": "vol"}
    d = d.rename(columns=ren)
    tcol = next(c for c in ("t", "ts", "time_utc", "candle_time", "index") if c in d.columns)
    epoch = pd.api.types.is_numeric_dtype(d[tcol])
    out = pd.DataFrame({"t": _to_epoch(d[tcol]), **{k: d[k].astype(float) for k in ("open", "high", "low", "close")}})
    out["vol"] = d["vol"].astype(float) if "vol" in d else np.nan
    out["spr"] = np.nan
    out = out.dropna(subset=["open", "high", "low", "close"]).drop_duplicates("t").sort_values("t")
    return out.reset_index(drop=True), epoch


def trading_day(t: np.ndarray) -> np.ndarray:
    return M.day_minute(t)[0]


def regroup(df: pd.DataFrame, tf: int) -> pd.DataFrame:
    day0, mins = M.day_minute(df["t"].to_numpy())
    key = df["t"].to_numpy() - (mins - (mins // tf) * tf) * 60
    g = df.assign(k=key).groupby("k", sort=True)
    return g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                 close=("close", "last")).reset_index().rename(columns={"k": "t"})


# ── MT5 ailesi gün sınaması ────────────────────────────────────────────────────
def day_verdicts(cand: pd.DataFrame, tf: int, natives: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Gün başına: hangi yerli TF'ye karşı, kaç bar, hepsi birebir mi."""
    ref_tf = next((r for r in (5, 15, 30, 60) if r in natives and len(natives[r]) and r >= tf and r % tf == 0
                   and natives[r]["t"].min() <= cand["t"].max() and natives[r]["t"].max() >= cand["t"].min()), None)
    if ref_tf is None:
        return pd.DataFrame()
    nat = natives[ref_tf]
    nat = nat[(nat["t"] >= cand["t"].min() - 86400) & (nat["t"] <= cand["t"].max() + 86400)]
    built = regroup(cand, ref_tf) if ref_tf != tf else cand[["t", "open", "high", "low", "close"]]
    nd = pd.Series(trading_day(nat["t"].to_numpy()), index=nat.index)
    bd = trading_day(built["t"].to_numpy())
    m = nat.merge(built, on="t", how="outer", suffixes=("_n", "_c"), indicator=True)
    m["gun"] = trading_day(m["t"].to_numpy())
    eq = np.ones(len(m), bool)
    for k in ("open", "high", "low", "close"):
        eq &= (np.abs(m[f"{k}_n"] - m[f"{k}_c"]) <= TOL).fillna(False).to_numpy()
    m["esit"] = eq
    g = m.groupby("gun").agg(yerli=("_merge", lambda s: int((s != "right_only").sum())),
                             kopya=("_merge", lambda s: int((s != "left_only").sum())),
                             esit=("esit", "sum"))
    g["kabul"] = (g["yerli"] > 0) & (g["yerli"] == g["kopya"]) & (g["esit"] == g["yerli"])
    g["ref_tf"] = ref_tf
    # yalnız kopyanın kendi kapsadığı günler
    days_c = set(np.unique(bd))
    return g[g.index.isin(days_c) & g.index.isin(set(nd.unique()))]


def best_interpretation(path: Path, tf: int, natives: dict[int, pd.DataFrame],
                        alt: dict[int, pd.DataFrame] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Damga yorumu (UTC / sunucu) iki beslemeden (NAS100 yerli + USTEC) toplam kabul günü en çok olanla seçilir."""
    raw, _ = read_any(path)
    # Sütun adı ('time_utc') yanıltabilir: analiz_paketi dosyası UTC etiketli ama sunucu saatinde. Her ikisi denenir.
    options = [("utc", raw)]
    try:
        options.append(("sunucu(NY+7)", raw.assign(t=K.server_to_utc(raw["t"].to_numpy()))))
    except ValueError:
        pass  # DST geçiş saatine düşen bar → bu yorum imkânsız
    best = None
    for name, df in options:
        try:
            _, mins = M.day_minute(df["t"].to_numpy())
            if np.any(mins % tf):
                continue
            v = day_verdicts(df, tf, natives)
        except Exception:  # noqa: BLE001 — yorum tutmuyorsa sıradakine geç
            continue
        score = int(v["kabul"].sum()) if len(v) else -1
        if alt is not None:
            vu = day_verdicts(df, tf, alt)
            score += int(vu["kabul"].sum()) if len(vu) else 0
        if best is None or score > best[3]:
            best = (df, v, name, score)
    if best is None:
        return raw, pd.DataFrame(), "ızgara dışı"
    return best[0], best[1], best[2]


def main() -> None:
    rep: dict = {"turetilemez": {}, "duka_ailesi": {}, "mt5_ailesi": {}}
    for p, why in UNDERIVABLE.items():
        rep["turetilemez"][p] = why

    duka = K.load_duka_1m()
    duka_days = set(np.unique(trading_day(duka["t"].to_numpy())))
    for p, kind in DUKA_FAMILY.items():
        if kind == "npz_local":
            z = np.load(R / p)
            c = pd.DataFrame({"open": z["o"], "high": z["h"], "low": z["l"], "close": z["c"]})
            same_len = len(c) == len(duka)
            eq = same_len and all(np.allclose(c[k].to_numpy(), duka[k].to_numpy(), atol=TOL) for k in ("open", "high", "low", "close"))
            rep["duka_ailesi"][p] = {"n": len(c), "ana_dosyayla_satir_satir_ayni": bool(eq)}
            continue
        c, _ = read_any(R / p)
        mm = c.merge(duka, on="t", suffixes=("_c", "_d"))
        d = np.abs(mm[["open_c", "high_c", "low_c", "close_c"]].to_numpy() - mm[["open_d", "high_d", "low_d", "close_d"]].to_numpy()).max(1)
        cd = pd.Series(trading_day(c["t"].to_numpy()))
        extra = sorted(set(cd.unique()) - duka_days)
        extra_bars = int(cd.isin(extra).sum())
        y = pd.to_datetime(mm["t"], unit="s").dt.year
        rep["duka_ailesi"][p] = {
            "n": len(c), "ortak": len(mm), "birebir_%": round(100 * float((d <= TOL).mean()), 3) if len(mm) else None,
            "yila_gore_birebir_%": (pd.Series(d <= TOL).groupby(y.to_numpy()).mean() * 100).round(2).to_dict(),
            "ana_dosyada_olmayan_gun": len(extra), "o_gunlerde_bar": extra_bars,
            "ornek_gunler": [str(pd.Timestamp(x).date()) for x in extra[:10]],
        }

    natives = {5: pd.concat([K.load_mt5_native("M5", K.MT5_DIR_A), K.load_mt5_native("M5", K.MT5_DIR_B)]).drop_duplicates("t").sort_values("t"),
               15: K.load_mt5_native("M15", K.MT5_DIR_A), 30: K.load_mt5_native("M30", K.MT5_DIR_A)}
    for extra in sorted((BASE / "out/kutu_taze").glob("NAS100_M5.csv.gz")):
        natives[5] = pd.concat([natives[5], K.load_mt5_native("M5", extra.parent)]).drop_duplicates("t").sort_values("t")
    term_m1 = pd.concat([K.load_mt5_native("M1", K.MT5_DIR_A), K.load_mt5_native("M1", K.MT5_DIR_B),
                         K.load_mt5_utc_csv(K.MT5_UTC_CSV[0])])
    if (BASE / "out/kutu_taze/NAS100_M1.csv.gz").exists():
        term_m1 = pd.concat([term_m1, K.load_mt5_native("M1", BASE / "out/kutu_taze")])
    # terminal yalnız TAM kapsadığı günleri sayar (ilk/son gün yarım olabilir)
    tdays = trading_day(term_m1.drop_duplicates("t")["t"].to_numpy())
    term_days = set(np.unique(tdays)) - {tdays.min(), tdays.max()}

    us1 = pd.concat([K.load_ustec_json(p) for p in K.USTEC_JSON]).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    ustec_ref = {b: regroup(us1, b) for b in (5, 15, 30)}
    add: dict[np.datetime64, pd.DataFrame] = {}
    day_rows: list[pd.DataFrame] = []
    for p, tf in MT5_FAMILY:
        df, v, interp = best_interpretation(R / p, tf, natives, ustec_ref)
        r = {"tf_dk": tf, "n": len(df), "damga": interp,
             "bas": str(pd.to_datetime(df["t"].min(), unit="s")), "bit": str(pd.to_datetime(df["t"].max(), unit="s"))}
        if len(v):
            r |= {"ref": f"yerli M{int(v['ref_tf'].iloc[0])}", "sinanan_gun": int(len(v)), "kabul_gun": int(v["kabul"].sum()),
                  "red_gun": int((~v["kabul"]).sum()),
                  "red_ornek": [str(pd.Timestamp(x).date()) for x in v.index[~v["kabul"]][:8]]}
            if tf == 1:
                ok = list(v.index[v["kabul"]])
                r["terminalde_olmayan_kabul_gun"] = sum(d not in term_days for d in ok)
                cd = trading_day(df["t"].to_numpy())
                for d in ok:  # terminalle çakışan kabul günleri de eklenir: s03 birleşimi ortak barların
                    add.setdefault(d, df[cd == d].assign(kaynak=p))  # birebir aynı olduğunu ayrıca dayatır
        else:
            r["ref"] = "yerli MT5 barıyla çakışma yok — sınanamadı, kullanılmadı"
        if len(v):  # gün gün hüküm kaydı (s09 her reddedilen günü son çıktıların kapsamına bağlar)
            vu_all = day_verdicts(df, tf, ustec_ref)
            day_rows.append(pd.DataFrame({"dosya": p, "tf": tf, "gun": v.index, "nas100_kabul": v["kabul"].to_numpy(),
                                          "ustec_kabul": v.index.isin(vu_all.index[vu_all["kabul"]]) if len(vu_all) else False}))
        # reddedilen günler önceki broker (USTEC) beslemesinin kopyası mı?
        if len(v) and (~v["kabul"]).any():
            vu = day_verdicts(df, tf, ustec_ref)
            vu = vu[vu.index.isin(v.index[~v["kabul"]])]
            r["red_gunlerden_USTEC_birebir"] = int(vu["kabul"].sum()) if len(vu) else 0
            us_end = trading_day(us1["t"].to_numpy()[-1:])[0]
            r["red_gun_USTEC_bitisinden_sonra"] = int(((~v["kabul"]) & (v.index > us_end)).sum())
        rep["mt5_ailesi"][p] = r
        print(p, r)

    if add:
        ext = pd.concat(add.values()).drop_duplicates("t").sort_values("t").reset_index(drop=True)
        (BASE / "out/ek").mkdir(parents=True, exist_ok=True)
        ext.to_parquet(BASE / "out/ek/mt5_m1_ek_gunler.parquet", index=False)
        days = sorted(add)
        rep["mt5_m1_eklenen"] = {"gun": len(days), "bar": len(ext), "ilk": str(pd.Timestamp(days[0]).date()),
                                 "son": str(pd.Timestamp(days[-1]).date()),
                                 "kaynak_dagilimi": ext["kaynak"].value_counts().to_dict()}
    pd.concat(day_rows).to_csv(BASE / "results/s05_gun_hukumleri.csv", index=False)
    (BASE / "results/s05_ek_kaynak.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: rep[k] for k in ("duka_ailesi",) + (("mt5_m1_eklenen",) if add else ())}, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
