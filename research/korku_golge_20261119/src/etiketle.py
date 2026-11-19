"""etiketle.py — K1 sinyallerine dondurulmuş kanal ∪ GBM vetosu etiketini yazar (veto UYGULANMAZ, emir yok).

python etiketle.py dogrula   # ham barlardan tüm tarihsel işlemleri yeniden etiketle, araştırma tablosuyla birebir kıyasla
python etiketle.py kos       # ileri sinyalleri (d ≥ ileri_baslangic) deftere ekle, belli olan sonuçları doldur
python etiketle.py rapor     # defterin ön kayıtlı ölçütlere göre durumu

Özellikler `xp_kaybeden_20261119/src/ozellik.py` ve `xp_gelistir_20261119/src/veri.py` ile AYNI kodla hesaplanır.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
for p in ("research/xp_kaybeden_20261119/src", "research/xp_gelistir_20261119/src"):
    sys.path.insert(0, str(ROOT / p))
import importlib.util  # noqa: E402

import ozellik as O  # noqa: E402

# "veri" adı başka araştırma klasörlerinde de var → dosya yoluyla yükle
_spec = importlib.util.spec_from_file_location("xp_veri", ROOT / "research/xp_gelistir_20261119/src/veri.py")
VR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(VR)

MODEL, RES = HERE / "model", HERE / "results"
DEFTER = RES / "golge_defter.csv"
META = json.loads((MODEL / "dondurulmus.json").read_text())
FEATS: list[str] = META["ozellikler"]
GBM = joblib.load(MODEL / "gbm_kesif.joblib")
PRIM = ["MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]
ETIKET = ["p_gbm", "z80", "veto_gbm", "veto_kanal", "veto"]
SONUC = ["cikis", "tutus_gun", "net"]


def forward_events() -> tuple[set, pd.Timestamp]:
    c = pd.read_csv(HERE / "olay_takvimi.csv", comment="#")
    end = pd.Timestamp(c[c.olay == "kapsam_sonu"].tarih.iloc[0])
    ev = set(pd.to_datetime(c[c.olay != "kapsam_sonu"].tarih))
    return ev | VR.R.event_days(), end


def load_bars() -> dict[str, pd.DataFrame]:
    return {s: O.load_market(s) for s in O.MARKETS}


def signal_features(bars: dict[str, pd.DataFrame], ev: set | None) -> pd.DataFrame:
    """Her MT5 piyasası için K1 günlerinin giriş anı özellik satırları (çıkış beklemeden)."""
    sret = {s: O.session_ret(b) for s, b in bars.items()}
    X = O.cross_market(sret)
    parts = []
    for s, b in bars.items():
        _, feats, k1 = VR.entry_features(b, 1800, ev)
        sig = feats[k1.fillna(False)].copy()
        sig.index.name = "d"
        sig = sig.reset_index()
        f = O.market_features(b, sig.d.tolist()).join(X[s], on="d")
        parts.append(sig.merge(f, on="d", how="inner").assign(besleme=f"MT5_{s}"))
    S = pd.concat(parts, ignore_index=True)
    S["X_k1_genislik"] = S.groupby("d").besleme.transform("nunique")
    return S


def apply_veto(S: pd.DataFrame) -> pd.DataFrame:
    out = []
    for f, z in S.groupby("besleme"):
        st = META["besleme_istatistik"][f]
        med, mu, sd = (pd.Series(st[k], index=FEATS) for k in ("med", "mu", "sd"))
        Xm = ((z.reindex(columns=FEATS).astype(float).fillna(med) - mu) / sd).fillna(0).values
        p = GBM.predict_proba(Xm)[:, 1]
        zz = z["T_1sa_z"].astype(float).values
        kan = np.isfinite(zz) & (zz <= st["kanal_esik"])
        out.append(z.assign(p_gbm=p, z80=zz, veto_gbm=p >= META["gbm_esik"], veto_kanal=kan, veto=(p >= META["gbm_esik"]) | kan))
    return pd.concat(out, ignore_index=True)


def outcomes(bars: dict[str, pd.DataFrame], ev: set | None) -> pd.DataFrame:
    return pd.concat([VR.build(b, 1800, f"MT5_{s}", ev)[["besleme", "d"] + SONUC] for s, b in bars.items()], ignore_index=True)


def dogrula() -> None:
    """Ham barlardan araştırma pipeline'ı yeniden: karar uyuşması %100, |Δp| < 1e-9 beklenir."""
    bars = load_bars()
    L = apply_veto(signal_features(bars, None))
    T = pd.read_csv(RES / "tarihsel_etiketler.csv", parse_dates=["d"])
    T = T[T.besleme.isin(PRIM)]
    j = T.merge(L[["besleme", "d"] + ETIKET], on=["besleme", "d"], how="left", suffixes=("_ar", ""))
    miss = int(j.p_gbm.isna().sum())
    ok = j.dropna(subset=["p_gbm"])
    dp = (ok.p_gbm_ar - ok.p_gbm).abs()
    res = {"arastirma_islem": len(T), "eslesen": len(ok), "eksik": miss,
           "karar_uyusma": float((ok.veto_ar == ok.veto).mean()), "maks_dp": float(dp.max()),
           "farkli_karar": ok[ok.veto_ar != ok.veto][["besleme", "d", "p_gbm_ar", "p_gbm", "veto_ar", "veto"]].astype(str).to_dict("records")[:20],
           "sinyal_ama_islem_yok": int(len(L) - len(ok))}
    # veri.py yeniden düzenlemesi işlem tablosunu değiştirmedi mi?
    o = outcomes(bars, None)
    I = pd.read_parquet(ROOT / "research/xp_gelistir_20261119/results/islemler.parquet")
    I = I[I.besleme.isin(PRIM)][["besleme", "d", "net"]]
    k = I.merge(o, on=["besleme", "d"], how="outer", indicator=True)
    res["islem_tablosu"] = {"ayni": int((k._merge == "both").sum()), "yalniz_eski": int((k._merge == "left_only").sum()),
                            "yalniz_yeni": int((k._merge == "right_only").sum()),
                            "maks_dnet": float((k.net_x - k.net_y).abs().max())}
    (RES / "dogrulama.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "farkli_karar"}, ensure_ascii=False, default=str))
    if res["farkli_karar"]:
        print("farklı kararlar:", res["farkli_karar"][:5])


def kos() -> None:
    ev, end = forward_events()
    start = pd.Timestamp(META["ileri_baslangic"])
    bars = load_bars()
    L = apply_veto(signal_features(bars, ev))
    L = L[(L.d >= start)]
    cov = L.d > end
    if cov.any():
        print("olay takvimi kapsamı dışında, etiketlenmedi:", sorted(L[cov].d.dt.date.unique()))
    L = L[~cov]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    D = pd.read_csv(DEFTER, parse_dates=["d", "cikis"]) if DEFTER.exists() else pd.DataFrame(columns=["besleme", "d", "etiket_zamani", "model_sha256"] + ETIKET + SONUC)
    have = set(zip(D.besleme, pd.to_datetime(D.d)))
    new = L[[(b, d) not in have for b, d in zip(L.besleme, L.d)]][["besleme", "d"] + ETIKET + ["twap_uz", "son_saat", "vix"]]
    new = new.assign(etiket_zamani=now, model_sha256=META["model_sha256"][:12])
    D = pd.concat([D, new], ignore_index=True) if len(new) else D
    o = outcomes(bars, ev).set_index(["besleme", "d"])
    for i, r in D.iterrows():
        key = (r.besleme, pd.Timestamp(r.d))
        if (pd.isna(r.get("net")) or r.get("net") == "") and key in o.index:
            for c in SONUC:
                D.at[i, c] = o.loc[key, c]
    D.sort_values(["d", "besleme"]).to_csv(DEFTER, index=False)
    last = {s: str(pd.to_datetime(b.t.max(), unit="s", utc=True).tz_convert(O.NY)) for s, b in bars.items()}
    print(f"yeni etiket {len(new)}, defter {len(D)} satır, sonuçlu {int(pd.to_numeric(D.net, errors='coerce').notna().sum())}; veri sonu {last}")
    rapor()


def rapor() -> dict:
    if not DEFTER.exists():
        print("defter yok")
        return {}
    D = pd.read_csv(DEFTER, parse_dates=["d"])
    D["net"] = pd.to_numeric(D.net, errors="coerce")
    for c in ("veto", "veto_gbm", "veto_kanal"):
        D[c] = D[c].astype(str).str.lower().eq("true")
    R_ = D.dropna(subset=["net"])
    net = R_.net.values

    def ev_(m: np.ndarray) -> dict:
        k = ~m
        loss = net[net < 0].sum()
        return {"veto_n": int(m.sum()), "veto_ort": round(float(net[m].mean()), 1) if m.any() else None,
                "kalan_ort": round(float(net[k].mean()), 1) if k.any() else None,
                "kar_x": round(float(net[k].sum() / net.sum()), 3) if net.sum() else None,
                "zarar_x": round(float(net[k][net[k] < 0].sum() / loss), 3) if loss else None}

    out = {"sonuclu": len(R_), "bekleyen": int(D.net.isna().sum()), "taban_ort": round(float(net.mean()), 1) if len(net) else None}
    for c in ("veto", "veto_kanal", "veto_gbm"):
        out[c] = ev_(R_[c].values) if len(R_) else {}
    piy = {}
    for f, g in R_.groupby("besleme"):
        m = g.veto.values
        if m.any() and (~m).any():
            piy[f] = bool(g.net[m].mean() < g.net[~m].mean())
    out["yon_tutan_piyasa"] = f"{sum(piy.values())}/{len(piy)}"
    v = out.get("veto", {})
    if len(R_) < 40 or v.get("veto_n", 0) < 8:
        out["hukum"] = "erken (≥40 sonuçlu ve ≥8 vetolu işlem gerekir)"
    elif v["veto_ort"] >= v["kalan_ort"]:
        out["hukum"] = "X"
    elif (v["veto_ort"] <= 20 and v["kalan_ort"] > out["taban_ort"] and v["kar_x"] >= 0.90 and v["zarar_x"] <= 0.70
          and sum(piy.values()) >= 3):
        out["hukum"] = "B önerisi (karar kullanıcıda)"
    else:
        out["hukum"] = "C"
    (RES / "golge_rapor.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out, ensure_ascii=False))
    return out


if __name__ == "__main__":
    {"dogrula": dogrula, "kos": kos, "rapor": rapor}[sys.argv[1]]()
