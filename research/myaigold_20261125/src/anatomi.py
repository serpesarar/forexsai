"""Giriş anı anatomisi + çıkış mekaniği. Karar anı = saat başı (UTC u); bilinen = u'dan önce KAPANMIŞ H1 barlar."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "yeni deneme"))
import broker_time as bt  # noqa: E402
import veri as V  # noqa: E402


def h1(B: pd.DataFrame) -> pd.DataFrame:
    kv = B.t.to_numpy() // 3600
    u, ilk = np.unique(kv, return_index=True)
    son = np.r_[ilk[1:], len(kv)] - 1
    H = pd.DataFrame({"kova": u, "o": B.open.to_numpy()[ilk], "h": np.maximum.reduceat(B.high.to_numpy(), ilk),
                      "l": np.minimum.reduceat(B.low.to_numpy(), ilk), "c": B.close.to_numpy()[son]})
    pc = H.c.shift(1)
    tr = np.maximum(H.h - H.l, np.maximum((H.h - pc).abs(), (H.l - pc).abs()))
    H["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    for n in (20, 50, 200):
        H[f"ema{n}"] = H.c.ewm(span=n, adjust=False).mean()
    d = H.c.diff()
    up, dn = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean(), (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    H["rsi"] = 100 - 100 / (1 + up / dn)
    H["renk"] = np.sign(H.c - H.o)
    H["govde"] = (H.c - H.o).abs() / (H.h - H.l).replace(0, np.nan)
    H["aralik_atr"] = (H.h - H.l) / H.atr
    H["kap_konum"] = (H.c - H.l) / (H.h - H.l).replace(0, np.nan)
    seri = [0]
    for k in range(1, len(H)):
        seri.append(seri[-1] + 1 if H.renk.iat[k] == H.renk.iat[k - 1] and H.renk.iat[k] != 0 else 1)
    H["ayni_renk_seri"] = seri
    for n in (4, 12, 24):
        H[f"r{n}_atr"] = (H.c - H.c.shift(n)) / H.atr
    H["hh24"], H["ll24"] = H.h.rolling(24).max(), H.l.rolling(24).min()
    H["konum24"] = (H.c - H.ll24) / (H.hh24 - H.ll24)
    H["kirilim20"] = np.where(H.c > H.h.shift(1).rolling(20).max(), 1, np.where(H.c < H.l.shift(1).rolling(20).min(), -1, 0))
    H["ema_dizilim"] = np.sign(H.ema20 - H.ema50) + np.sign(H.ema50 - H.ema200)
    H["fiyat_ema50_atr"] = (H.c - H.ema50) / H.atr
    return H


def karar_ozellik(H: pd.DataFrame, u_saat: np.ndarray) -> pd.DataFrame:
    """u_saat: karar saati kovası (UTC saat başı // 3600). Kullanılan bar = u_saat − 1 (kapanmış)."""
    idx = pd.Series(np.arange(len(H)), index=H.kova)
    j = idx.reindex(u_saat - 1).to_numpy()
    ok = ~np.isnan(j)
    j = np.nan_to_num(j).astype(int)
    F = H.iloc[j].reset_index(drop=True)
    F["gecerli"] = ok
    z = pd.to_datetime(u_saat * 3600, unit="s", utc=True)
    F["saat_utc"] = z.hour
    F["gun"] = z.weekday
    return F


def main() -> None:
    x = V.islemler()
    B = V.xau_1m()
    H = h1(B)
    srv = (x.t_ac.astype("int64") // 10**9).to_numpy()
    x["u"] = srv - np.array([bt.rule_offset_sec(int(s)) for s in srv])
    x["u_kap"] = (x.t_kap.astype("int64") // 10**9).to_numpy() - np.array([bt.rule_offset_sec(int(s)) for s in (x.t_kap.astype("int64") // 10**9)])
    F = karar_ozellik(H, (x.u // 3600).to_numpy())
    y = x.yon.to_numpy()
    print("== 1. PROFİL ==")
    tut = (x.u_kap - x.u) / 60
    print(f"işlem {len(x)}  AL {int((y > 0).sum())} / SAT {int((y < 0).sum())}  net {x.net.sum():.0f} $  isabet {(x.net > 0).mean():.3f}")
    print("tutuş dk medyan/p25/p75/maks", tut.median().round(0), tut.quantile(.25).round(0), tut.quantile(.75).round(0), tut.max().round(0))
    kaz = x[x.net > 0]
    kay = x[x.net <= 0]
    print(f"kazanç ort {kaz.net.mean():.1f} $ / kayıp ort {kay.net.mean():.1f} $ → başabaş isabet {(-kay.net.mean() / (kaz.net.mean() - kay.net.mean())):.3f}")
    atr = F.atr.to_numpy()
    print("TP mesafesi $ medyan", x.tp_mesafe.median().round(2), "| ATR_H1 cinsinden", np.nanmedian(x.tp_mesafe / atr).round(2), "geçersiz F", int((~F.gecerli).sum()))
    print("hareket $ (ons başı): kazananlar medyan", kaz.hareket.median().round(2), " kaybedenler", kay.hareket.round(1).tolist())
    print("son stop konumu (girişe göre $): kazananlarda medyan", kaz.sl_son_mesafe.median().round(2), " p10/p90",
          kaz.sl_son_mesafe.quantile([.1, .9]).round(1).tolist())
    print("kayıpların ATR_H1 cinsinden büyüklüğü", (kay.hareket / atr[kay.index]).round(2).tolist())
    print("lot ↔ zaman korelasyonu", round(np.corrcoef(x.u, x.lot)[0, 1], 3), " lot/kümülatif bakiye: ilk 10", x.lot.head(10).tolist(), "son 10", x.lot.tail(10).tolist())
    print("\n== 2. NE ZAMAN ==")
    print("UTC saat:", F.saat_utc.value_counts().sort_index().to_dict())
    print("gün:", F.gun.value_counts().sort_index().to_dict())
    tum = karar_ozellik(H, H.kova.to_numpy()[300:] + 1)
    tum = tum[tum.gecerli & (tum.gun < 5) & np.asarray(pd.to_datetime(H.kova.to_numpy()[300:] * 3600, unit="s") >= pd.Timestamp("2026-05-19"))]
    print("taban (aynı dönem tüm saat başları) UTC saat payı vs hesap payı (en farklı):")
    t_pay = tum.saat_utc.value_counts(normalize=True)
    h_pay = F.saat_utc.value_counts(normalize=True)
    lift = (h_pay / t_pay).dropna().sort_values(ascending=False)
    print("  ", {int(k): round(v, 2) for k, v in lift.head(6).items()}, "... en az:", {int(k): round(v, 2) for k, v in lift.tail(4).items()})
    print("\n== 3. NEREDE: yöne göre işaretlenmiş özellikler (hesap vs taban) ==")
    S = F.copy()
    S["yon"] = y
    for k, ad in (("renk", "son H1 mumu yönle aynı renk"), ("kirilim20", "20-bar kırılımı yönle aynı"), ("ema_dizilim", "EMA20/50/200 dizilimi yönle aynı")):
        hes = np.mean(np.sign(S[k]) == S.yon)
        tb = 0.5 * (np.mean(np.sign(tum[k]) == 1) + np.mean(np.sign(tum[k]) == -1))
        print(f"  {ad}: hesap {hes:.2f}  (rastgele yön tabanı ≈ {tb:.2f})")
    for k in ("r4_atr", "r12_atr", "r24_atr", "fiyat_ema50_atr"):
        v = S[k] * S.yon
        print(f"  {k} × yön: medyan {v.median():+.2f}  (pozitif = yönle aynı hareket sonrası giriş) pay>0 {np.mean(v > 0):.2f}")
    kz = np.where(S.yon > 0, S.konum24, 1 - S.konum24)
    print(f"  24 sa aralıkta yöne göre konum (1 = alışta tepe/satışta dip): medyan {np.nanmedian(kz):.2f}  dağılım {np.nanquantile(kz, [.1, .25, .5, .75, .9]).round(2).tolist()}")
    rs = np.where(S.yon > 0, S.rsi, 100 - S.rsi)
    print(f"  RSI14 (yöne göre): medyan {np.nanmedian(rs):.1f}  p10/p90 {np.nanquantile(rs, [.1, .9]).round(1).tolist()}")
    print(f"  son H1 aralığı / ATR medyan {S.aralik_atr.median():.2f} (taban {tum.aralik_atr.median():.2f}); gövde payı {S.govde.median():.2f} (taban {tum.govde.median():.2f})")
    print(f"  aynı renk seri medyan {S.ayni_renk_seri.median():.0f} (taban {tum.ayni_renk_seri.median():.0f})")
    print("\n== 4. KAZANAN vs KAYBEDEN girişler ==")
    S["kazandi"] = (x.net > 0).to_numpy()
    for k in ("r4_atr", "r24_atr", "fiyat_ema50_atr", "aralik_atr", "konum24", "rsi"):
        v = S[k] * (S.yon if k not in ("aralik_atr", "konum24", "rsi") else 1)
        print(f"  {k}: kazanan medyan {v[S.kazandi].median():+.2f}  kaybeden {v[~S.kazandi].median():+.2f}")
    x.assign(**{f"F_{c}": S[c].to_numpy() for c in S.columns}).to_parquet(Path(__file__).resolve().parents[1] / "results/islemler_ozellik.parquet")


if __name__ == "__main__":
    main()
