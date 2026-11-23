"""SC — veri katmanı: sağlayıcı işlemleri (UTC'ye hizalı, kapanış tipiyle) + XAU 1m barları (bid + spread modeli).

Tek kaynak ilkesi: her betik barı ve işlemi YALNIZ buradan alır. Her yükleme bütünlük denetiminden geçer; denetim bozuksa
istisna fırlatır (sessiz devam yok).

Saat ekseni (Defter E2/E150): MQL5 zamanları broker sunucu saatidir. Aday modeller ny7 (New York + 7, ABD yaz saati), eet (AB yaz saati)
ve sabit −5…+5 sa. Model, giriş VE çıkış fiyatının bizim 1m barımızın [low, high] aralığına (taban farkı düşülerek) düşme oranıyla seçilir;
ay ay oran raporlanır, %95 altı ay hata sayılır.

Spread (bp): ASK verisi olan (yıl, UTC saati) hücrelerinde medyan (ask_open − bid_open) / bid_open; olmayan yılda en yakın yılın saat profili.
Bp cinsinden taşımak, 2018'in 1.300 $ altınına 2025'in $ spread'ini yüklemeyi önler.
"""
from __future__ import annotations

import datetime as dt
import lzma
import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
ROOT = KOK.parents[1]
KH = ROOT / "research" / "kopya_hesap_20261122"
POZ = KH / "data" / "pozisyonlar.parquet"
HISTORY = KH / "data" / "raw" / "history"
XAU_2018 = ROOT / "research" / "fibo_altin_bolge_20261116" / "cache" / "XAU_1m_raw.parquet"
CH = KOK / "data" / "chunks" / "XAU"
BAR_CACHE = KOK / "data" / "xau_1m.parquet"

HESAPLAR = {"2268766": ("T", "Soma PureGold"), "2347514": ("O", "CWDT BAXP")}
NY = ZoneInfo("America/New_York")
EET = ZoneInfo("Europe/Athens")
HIZA_AY_MIN = 0.95
KOMISYON_USD_OZ = 0.08  # gidiş-dönüş; Soma: 0,01 lot başına −0,04 $ giriş + −0,04 $ çıkış = 8 $/lot = 0,08 $/ons


# ───────────────────────── barlar ─────────────────────────
def _bi5_satirlar(yol: Path) -> list[list[float]]:
    ham = yol.read_bytes()
    if not ham:
        return []
    d = dt.date(int(yol.name[:4]), int(yol.name[4:6]), int(yol.name[6:8]))
    taban = int(dt.datetime.combine(d, dt.time(), tzinfo=dt.timezone.utc).timestamp())
    return [[taban + s, o / 1000, hi / 1000, lo / 1000, c / 1000, v]
            for s, o, c, lo, hi, v in struct.iter_unpack(">5If", lzma.decompress(ham)) if v > 0 and min(o, c, lo, hi) > 0]


def _chunk_df(taraf: str) -> pd.DataFrame:
    satir: list[list[float]] = []
    for f in sorted(CH.glob(f"*_{taraf}.bi5")):
        satir.extend(_bi5_satirlar(f))
    return pd.DataFrame(satir, columns=["t", "open", "high", "low", "close", "vol"])


def spread_modeli(bid: pd.DataFrame, ask_open: pd.DataFrame) -> pd.DataFrame:
    """(yıl, saat) → medyan spread bp. ask_open: kolonlar t, ask_open."""
    m = bid[["t", "open"]].merge(ask_open, on="t", how="inner")
    m["bp"] = (m["ask_open"] - m["open"]) / m["open"] * 1e4
    m = m[(m["bp"] > 0) & (m["bp"] < 50)]
    z = pd.to_datetime(m["t"], unit="s", utc=True)
    tablo = m.assign(yil=z.dt.year, saat=z.dt.hour).groupby(["yil", "saat"])["bp"].agg(["median", "size"]).reset_index()
    return tablo[tablo["size"] >= 30]


def _spread_uygula(bar: pd.DataFrame, tablo: pd.DataFrame) -> np.ndarray:
    z = pd.to_datetime(bar["t"], unit="s", utc=True)
    yil, saat = z.dt.year.to_numpy(), z.dt.hour.to_numpy()
    yillar = np.array(sorted(tablo["yil"].unique()))
    profil = {y: tablo[tablo["yil"] == y].set_index("saat")["median"].reindex(range(24)) for y in yillar}
    for y in yillar:  # eksik saat → o yılın medyanı
        profil[y] = profil[y].fillna(profil[y].median())
    out = np.empty(len(bar))
    for y in np.unique(yil):
        en_yakin = yillar[np.argmin(np.abs(yillar - y))]
        m = yil == y
        out[m] = profil[en_yakin].to_numpy()[saat[m]]
    return out


def _indirme_tamam() -> bool:
    """Kısmi indirme bar setini sessizce değiştirmesin: 2010–2017 BID + tüm ASK Çarşambaları bitmeden eski chunk kullanılmaz."""
    import sc_duka
    kalan = sc_duka.yapilacaklar()
    if kalan:
        print(f"UYARI: Duka indirmesi bitmedi ({len(kalan)} dosya) → yalnız 2018+ bid ve 2025 ASK spread profili kullanılıyor")
    return not kalan


def bar_surumu() -> str:
    """Bar setinin parmak izi (deneme defterine yazılır): satır sayısı, ilk/son zaman, spread özeti."""
    import hashlib
    b = barlar()
    oz = f"{len(b)}|{b.t[0]}|{b.t[-1]}|{np.round(np.median(b.s / b.o * 1e4), 4)}|{np.round(b.c.sum(), 2)}"
    return hashlib.sha1(oz.encode()).hexdigest()[:10]


def bar_kur() -> pd.DataFrame:
    """2010–2017 (SC chunk'ları, varsa) + 2018–2026 (fibo cache) bid; spread bp modeli; diske yazar."""
    yeni = XAU_2018 if XAU_2018.exists() else None
    if yeni is None:
        raise FileNotFoundError(XAU_2018)
    b18 = pd.read_parquet(yeni)
    parca = [b18[["t", "open", "high", "low", "close", "vol"]]]
    askler = [b18.dropna(subset=["ask_open"])[["t", "ask_open"]]]
    if CH.exists():
        tum = _chunk_df("BID")
        yeni_g = tum[tum["t"] > b18["t"].max()]  # 2026-11-14+ (ileri gölge) her zaman
        if len(yeni_g):
            parca.append(yeni_g)
        if _indirme_tamam():  # 2010–2017 ve tüm ASK yalnız indirme tamsa (kısmi set sonuçları sessizce değiştirmesin)
            parca.insert(0, tum[tum["t"] < b18["t"].min()])
            a = _chunk_df("ASK")
            if len(a):
                askler.append(a[["t", "open"]].rename(columns={"open": "ask_open"}))
    bar = pd.concat(parca, ignore_index=True).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    ask = pd.concat(askler, ignore_index=True).drop_duplicates("t")
    tablo = spread_modeli(bar, ask)
    bar["spr_bp"] = _spread_uygula(bar, tablo)
    bar["t"] = bar["t"].astype("int64")
    bar_denetle(bar)
    BAR_CACHE.parent.mkdir(parents=True, exist_ok=True)
    bar.to_parquet(BAR_CACHE, index=False)
    tablo.to_csv(KOK / "results" / "spread_modeli.csv", index=False)
    return bar


def bar_denetle(bar: pd.DataFrame) -> None:
    t = bar["t"].to_numpy()
    sorun = []
    if (np.diff(t) <= 0).any():
        sorun.append("zaman monoton değil / yinelenen")
    if (t % 60).any():
        sorun.append("dakika başı olmayan zaman")
    o, h, l, c = (bar[k].to_numpy() for k in ("open", "high", "low", "close"))
    if ((h < np.maximum(o, c) - 1e-9) | (l > np.minimum(o, c) + 1e-9)).any():
        sorun.append("OHLC tutarsız")
    if not np.isfinite(bar["spr_bp"]).all() or (bar["spr_bp"] <= 0).any():
        sorun.append("spread eksik/≤0")
    r = np.abs(np.diff(np.log(c)))
    if (r > 0.08).any():  # 1 dakikada %8: bozuk tick
        sorun.append(f"aşırı sıçrama {int((r > 0.08).sum())}")
    if sorun:
        raise ValueError("bar denetimi: " + "; ".join(sorun))


@dataclass(frozen=True)
class Bar:
    t: np.ndarray
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    s: np.ndarray  # spread, fiyat birimi ($)

    def __len__(self) -> int:
        return len(self.t)

    def idx(self, ts: np.ndarray | int) -> np.ndarray:
        """ts'den SONRA ya da ona eşit açılan ilk barın indeksi (dolum barı)."""
        return np.searchsorted(self.t, ts, side="left")

    def dilim(self, a: int, b: int) -> "Bar":
        return Bar(*(x[a:b] for x in (self.t, self.o, self.h, self.l, self.c, self.s)))


@lru_cache(maxsize=1)
def barlar() -> Bar:
    d = pd.read_parquet(BAR_CACHE) if BAR_CACHE.exists() else bar_kur()
    bar_denetle(d)
    o = d["open"].to_numpy(float)
    return Bar(d["t"].to_numpy("int64"), o, d["high"].to_numpy(float), d["low"].to_numpy(float),
               d["close"].to_numpy(float), d["spr_bp"].to_numpy(float) * o / 1e4)


# ───────────────────────── sağlayıcı işlemleri ─────────────────────────
def _history(hesap: str) -> pd.DataFrame:
    grup = HESAPLAR[hesap][0]
    h = pd.read_csv(HISTORY / f"{hesap}_{grup}.history.csv", sep=";", encoding="utf-8-sig", dtype=str)
    h = h[h["Direction"].isin(["In", "Out"]) & h["Symbol"].fillna("").str.upper().str.startswith("XAUUSD")].copy()
    h["t"] = pd.to_datetime(h["Time"], format="%Y.%m.%d %H:%M:%S")
    h["px"] = h["Price"].str.replace(" ", "", regex=False).astype(float).round(5)
    yorum = h["Comment"].fillna("")
    h["tip"] = np.select([yorum.str.contains(r"\[sl"), yorum.str.contains(r"\[tp"), yorum.str.contains("so:")],
                         ["SL", "TP", "stop-out"], "bot")
    h["seviye"] = pd.to_numeric(yorum.str.extract(r"\[(?:sl|tp) ([\d.\s]+)\]")[0].str.replace(" ", "", regex=False),
                                errors="coerce")
    return h


def _kapanis_tipi(hesap: str, p: pd.DataFrame) -> pd.DataFrame:
    h = _history(hesap)
    h = h[h["Direction"] == "Out"].copy()
    h["sira"] = h.groupby(["t", "px"]).cumcount()
    p = p.assign(px=p["close_price"].round(5))
    p["sira"] = p.groupby(["close_time", "px"]).cumcount()
    m = p.merge(h[["t", "px", "sira", "tip", "seviye"]], left_on=["close_time", "px", "sira"],
                right_on=["t", "px", "sira"], how="left", validate="one_to_one")
    return m.drop(columns=["t", "px", "sira"]).assign(tip=lambda x: x["tip"].fillna("?"))


def _ny7(ts: np.ndarray) -> np.ndarray:
    z = pd.to_datetime(ts - 2 * 3600, unit="s", utc=True)
    return np.where([x.astimezone(NY).dst().total_seconds() > 0 for x in z], 3 * 3600, 2 * 3600)


def _eet(ts: np.ndarray) -> np.ndarray:
    z = pd.to_datetime(ts - 2 * 3600, unit="s", utc=True)
    return np.array([x.astimezone(EET).utcoffset().total_seconds() for x in z]).astype("int64")


def _icerde(bar: Bar, ts_utc: np.ndarray, px: np.ndarray, taban: float, tol: np.ndarray) -> np.ndarray:
    dk = ts_utc // 60 * 60
    i = np.minimum(np.searchsorted(bar.t, dk), len(bar) - 1)
    var = bar.t[i] == dk
    x = px - taban
    return var & (x >= bar.l[i] - tol) & (x <= bar.h[i] + tol)


def hizala(p: pd.DataFrame, bar: Bar) -> tuple[str, float, pd.DataFrame, pd.DataFrame]:
    """En iyi saat modeli. Dönüş: (model, oran, UTC sütunları eklenmiş p, ay ay oran tablosu)."""
    ta = p["open_time"].astype("int64").to_numpy() // 10**9
    tk = p["close_time"].astype("int64").to_numpy() // 10**9
    adaylar = {f"sabit{h:+d}": np.full(len(p), h * 3600) for h in range(-5, 6)}
    adaylar["ny7"], adaylar["eet"] = _ny7(ta), _eet(ta)
    tol = 2 * np.median(bar.s) + 1e-4 * p["open_price"].to_numpy()
    sonuc = []
    for ad, ofs in adaylar.items():
        ua = ta - ofs
        dk = ua // 60 * 60
        i = np.minimum(np.searchsorted(bar.t, dk), len(bar) - 1)
        var = bar.t[i] == dk
        if var.mean() < 0.5:
            continue
        taban = float(np.median((p["open_price"].to_numpy() - (bar.h[i] + bar.l[i]) / 2)[var]))
        ok = (_icerde(bar, ua, p["open_price"].to_numpy(), taban, tol)
              & _icerde(bar, tk - _ofs_kapanis(ad, tk), p["close_price"].to_numpy(), taban, tol))
        sonuc.append((ok.mean(), ad, ofs, taban, ok))
    _, ad, ofs, _, _ = max(sonuc, key=lambda x: x[0])  # saat modeli küresel tabanla seçilir (model seçimi sağlam)
    q = p.assign(t_giris=ta - ofs, t_cikis=tk - _ofs_kapanis(ad, tk))
    # Fiyat tabanı aydan aya kayıyor (2026'da −2,7…+1,8 $): hizalama denetimi AY tabanıyla yapılır. Simülasyon tabanı KULLANMAZ.
    # Taban, her ay için −6…+6 $ ızgarasında giriş+çıkış barda-olma oranını en yükselten değerdir (yalnız denetim ölçüsü).
    ay_k = q["open_time"].dt.to_period("M").to_numpy()
    q["taban"], q["hizali"] = np.nan, False
    for ay in np.unique(ay_k):
        m = ay_k == ay
        g = q[m]
        en = (-1.0, 0.0, None)
        for tb in np.arange(-6.0, 6.01, 0.1):
            ok = (_icerde(bar, g["t_giris"].to_numpy(), g["open_price"].to_numpy(), tb, tol[m])
                  & _icerde(bar, g["t_cikis"].to_numpy(), g["close_price"].to_numpy(), tb, tol[m]))
            if ok.mean() > en[0] + 1e-12:
                en = (ok.mean(), tb, ok)
        q.loc[m, "taban"], q.loc[m, "hizali"] = round(en[1], 1), en[2]
    q["bar_var"] = (q["t_cikis"].to_numpy() <= bar.t[-1]) & (q["t_giris"].to_numpy() >= bar.t[0])
    kapsam = q[q["bar_var"]]
    ay = kapsam.groupby(kapsam["open_time"].dt.to_period("M"))["hizali"].agg(["mean", "size"]).reset_index()
    return ad, float(kapsam["hizali"].mean()), q, ay


def _ofs_kapanis(ad: str, tk: np.ndarray) -> np.ndarray:
    if ad == "ny7":
        return _ny7(tk)
    if ad == "eet":
        return _eet(tk)
    return np.full(len(tk), int(ad[5:]) * 3600)


def islemler(hesap: str = "2268766", sessiz: bool = False) -> pd.DataFrame:
    """Sağlayıcının XAU pozisyonları, UTC zamanlı. Kolonlar: t_giris/t_cikis (UTC sn), yon, lot, giris/cikis (broker fiyatı),
    tip (SL/TP/bot/?), seviye (kapanış yorumundaki SL/TP seviyesi), net ($), bp_kendi, sinyal (olay kimliği), hizali."""
    poz = pd.read_parquet(POZ)
    p = poz[(poz["hesap"] == hesap) & poz["symbol"].str.upper().str.startswith("XAUUSD")].copy()
    p = p.sort_values(["open_time", "close_time"]).reset_index(drop=True)
    p = _kapanis_tipi(hesap, p)
    bar = barlar()
    ad, oran, p, ay = hizala(p, bar)
    kotu = ay[(ay["mean"] < HIZA_AY_MIN) & (ay["size"] >= 10)]
    if not sessiz:
        print(f"[{hesap}] saat modeli {ad}, hizalama %{oran * 100:.1f} (bar kapsamında {int(p['bar_var'].sum())}/{len(p)}), "
              f"%{HIZA_AY_MIN * 100:.0f} altı ay: {len(kotu)}")
    p["yon"] = np.where(p["side"] == "buy", 1, -1)
    p["bp_kendi"] = p["yon"] * (p["close_price"] - p["open_price"]) / p["open_price"] * 1e4
    p["sure_sn"] = p["t_cikis"] - p["t_giris"]
    p.attrs.update(saat_modeli=ad, hizalama=oran, kotu_ay=kotu.to_dict("records"))
    return sinyal_ata(p)


SINYAL_BOSLUK_SN = 300


def sinyal_ata(p: pd.DataFrame) -> pd.DataFrame:
    """Olay = aynı yönde, önceki girişten ≤ 5 dk sonra açılan pozisyonlar zinciri (E9: bölünmüş bacaklar tek karar)."""
    p = p.sort_values("t_giris").reset_index(drop=True)
    sid = np.zeros(len(p), int)
    son_t = {1: -10**12, -1: -10**12}
    son_id = {1: -1, -1: -1}
    sayac = -1
    for k, (t, y) in enumerate(zip(p["t_giris"].to_numpy(), p["yon"].to_numpy())):
        if t - son_t[y] > SINYAL_BOSLUK_SN:
            sayac += 1
            son_id[y] = sayac
        sid[k] = son_id[y]
        son_t[y] = t
    p["sinyal"] = sid
    p["bacak"] = p.groupby("sinyal").cumcount()
    return p


if __name__ == "__main__":
    b = bar_kur()
    print("bar", len(b), pd.to_datetime(b["t"].min(), unit="s"), pd.to_datetime(b["t"].max(), unit="s"))
    for h in HESAPLAR:
        x = islemler(h)
        print(h, len(x), "sinyal", x["sinyal"].nunique(), x["tip"].value_counts().to_dict())
