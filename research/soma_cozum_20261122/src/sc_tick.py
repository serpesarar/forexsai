"""SC-11 — Dukascopy XAUUSD saatlik tik verisi: olay listesi, gereken saatler, indirme, ayrıştırma, bütünlük denetimi.

Tik kaydı (20 bayt, büyük-endian): saat başından ms, ask, bid (×1000), ask hacmi, bid hacmi.
Dosya yolu Dukascopy'de ay 0 tabanlıdır. Ham dosyalar `data/tick/XAU/<YYYYMMDDHH>.bi5` (gitignore: research/**/data/).
Kullanım: .venv/bin/python -I research/soma_cozum_20261122/src/sc_tick.py [say|indir|denetle]
"""
from __future__ import annotations

import datetime as dt
import http.client
import lzma
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc_degerlendir as D  # noqa: E402
import sc_veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
TK = KOK / "data" / "tick" / "XAU"
FEED = "XAUUSD"
KAYIT = np.dtype([("ms", ">u4"), ("ask", ">u4"), ("bid", ">u4"), ("av", ">f4"), ("bv", ">f4")])
GERI_SN = 4200      # olay öncesi: 10 dk pencere + 60 dk geriye bakış
ILERI_SN = 900      # olay sonrası: 10 dk pencere + pay
ISKA_SN = 1800      # ıska: ±30 dk içinde aynı yönde Soma/CWDT girişi yok
Q_HUKUM = 0.995     # PROTOCOL SC-11 eki: hüküm pencereleri
Q_BETIM = 0.998
ISCI = int(os.getenv("DUKA_WORKERS", "6"))
BEKLE_S = float(os.getenv("DUKA_PACE_S", "0.2"))
_TL = threading.local()


# ───────────────────────── olaylar ─────────────────────────
def kesim() -> int:
    X = pd.read_parquet(KOK / "results" / "sc08_matris_son.parquet", columns=["hesap", "bolum", "t_giris"])
    return int(X.loc[(X["hesap"] == "2268766") & (X["bolum"] == "ILERI"), "t_giris"].min())


def ilk_bacaklar(hesap: str) -> pd.DataFrame:
    p = V.islemler(hesap, sessiz=True)
    a, b = D.DONEM["HESAP"]
    p = p[p["bar_var"] & (p["t_giris"] >= D.ts(a)) & (p["t_giris"] < D.ts(b))]
    ilk = p.sort_values("t_giris").groupby("sinyal").first().reset_index()
    return pd.DataFrame({"t": ilk["t_giris"].to_numpy("int64"), "y": ilk["yon"].to_numpy(int), "sinyal": ilk["sinyal"].to_numpy(),
                         "hesap": hesap})


def ateslemeler(q: float) -> pd.DataFrame:
    """SC-08 dakika kapanışı model ateşlemeleri (KEŞİF eşiği q, soğuma 0, yükselen kenar). t = karar anı (dakika kapanışı)."""
    import sc08_kural as K
    G = pd.read_parquet(KOK / "results" / "sc08_skor_son.parquet")
    G = G.assign(t=G["t"] + 60)
    e = float(np.quantile(G["skor"][G["t"] < kesim()], q))
    K.SOGUMA = 0
    A = K.ateslemeler(G.assign(ok=G["skor"] >= e))
    return A[["t", "y", "skor"]].reset_index(drop=True).assign(esik=e)


def _yakin(t: np.ndarray, y: np.ndarray, T: np.ndarray, Y: np.ndarray, pencere: int) -> np.ndarray:
    o = np.argsort(T)
    T, Y = T[o], Y[o]
    sonuc = np.zeros(len(t), bool)
    for i, (ti, yi) in enumerate(zip(t, y)):
        a, b = np.searchsorted(T, ti - pencere), np.searchsorted(T, ti + pencere, side="right")
        sonuc[i] = bool(np.any(Y[a:b] == yi))
    return sonuc


@lru_cache(maxsize=1)
def olaylar() -> pd.DataFrame:
    """tur: P (sağlayıcı ilk bacağı) | F (q 0,995 ateşlemesi; iska=True ise ±30 dk sağlayıcı girişi yok)."""
    P = pd.concat([ilk_bacaklar("2268766"), ilk_bacaklar("2347514")], ignore_index=True).assign(tur="P")
    F = ateslemeler(Q_HUKUM).assign(tur="F", hesap="model")
    e_betim = float(ateslemeler(Q_BETIM)["esik"].iloc[0])
    F["q998"] = F["skor"] >= e_betim
    F["iska"] = ~_yakin(F["t"].to_numpy(), F["y"].to_numpy(), P["t"].to_numpy(), P["y"].to_numpy(), ISKA_SN)
    E = pd.concat([P, F], ignore_index=True)
    E["bolum"] = np.where(E["t"] < kesim(), "KESIF", "ILERI")
    return E.sort_values("t").reset_index(drop=True)


def gereken_saatler(E: pd.DataFrame) -> list[int]:
    s: set[int] = set()
    for t in E["t"].to_numpy("int64"):
        s.update(range((t - GERI_SN) // 3600 * 3600, (t + ILERI_SN) // 3600 * 3600 + 1, 3600))
    return sorted(s)


# ───────────────────────── indirme ─────────────────────────
def yol(h: int) -> Path:
    return TK / f"{dt.datetime.fromtimestamp(h, dt.timezone.utc):%Y%m%d%H}.bi5"


def _baglanti() -> http.client.HTTPSConnection:
    c = getattr(_TL, "c", None)
    if c is None:
        c = _TL.c = http.client.HTTPSConnection("datafeed.dukascopy.com", timeout=120)
    return c


def _al(h: int) -> bool:
    d = dt.datetime.fromtimestamp(h, dt.timezone.utc)
    u = f"/datafeed/{FEED}/{d:%Y}/{d.month - 1:02d}/{d:%d}/{d:%H}h_ticks.bi5"
    bekle = 15
    for _ in range(6):
        try:
            c = _baglanti()
            c.request("GET", u, headers={"User-Agent": "Mozilla/5.0", "Connection": "keep-alive"})
            r = c.getresponse()
            govde = r.read()
            if r.status in (200, 404):
                tmp = yol(h).with_suffix(".tmp")
                tmp.write_bytes(govde if r.status == 200 else b"")
                tmp.rename(yol(h))  # atomik
                time.sleep(BEKLE_S)
                return True
            kod = r.status
        except Exception as e:  # noqa: BLE001 — ağ hatası: bağlantıyı yenile, yeniden dene
            kod = type(e).__name__
            try:
                _TL.c.close()
            except Exception:  # noqa: BLE001
                pass
            _TL.c = None
        print(time.strftime("%H:%M:%S"), "engel", kod, d, "bekle", bekle, flush=True)
        time.sleep(bekle)
        bekle = min(bekle * 2, 120)
    return False


def indir() -> None:
    TK.mkdir(parents=True, exist_ok=True)
    onceki = None
    for tur in range(60):  # sunucu engeli saatlerce sürebilir: ilerleme yoksa 10 dk bekle, yeniden dene
        isler = [h for h in gereken_saatler(olaylar()) if not yol(h).exists()]
        print(time.strftime("%H:%M:%S"), "tur", tur, "kalan", len(isler), flush=True)
        if not isler:
            break
        if onceki is not None and len(isler) >= onceki:
            time.sleep(600)
        onceki = len(isler)
        n = 0
        with ThreadPoolExecutor(ISCI) as ex:
            for _ in ex.map(_al, isler):
                n += 1
                if n % 200 == 0:
                    print(time.strftime("%H:%M:%S"), n, "/", len(isler), flush=True)
    print("TİK İNDİRME BİTTİ, kalan", sum(not yol(h).exists() for h in gereken_saatler(olaylar())), flush=True)


# ───────────────────────── okuma ─────────────────────────
@lru_cache(maxsize=4096)
def saat(h: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(t_ms mutlak, bid, ask, hacim) — dosya yoksa istisna, boşsa (piyasa kapalı) boş diziler."""
    ham = yol(h).read_bytes()
    if not ham:
        z = np.zeros(0)
        return z.astype("int64"), z, z, z
    r = np.frombuffer(lzma.decompress(ham), dtype=KAYIT)
    t = h * 1000 + r["ms"].astype("int64")
    return t, r["bid"].astype(float) / 1000, r["ask"].astype(float) / 1000, (r["av"] + r["bv"]).astype(float)


def aralik(a: int, b: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """[a, b) saniye aralığındaki tikler (t_ms, bid, ask, hacim)."""
    parca = [saat(h) for h in range(a // 3600 * 3600, (b - 1) // 3600 * 3600 + 1, 3600)]
    t, bid, ask, v = (np.concatenate([p[i] for p in parca]) for i in range(4))
    m = (t >= a * 1000) & (t < b * 1000)
    return t[m], bid[m], ask[m], v[m]


def tik_1m(h: int) -> pd.DataFrame:
    """Saatin tiklerinden 1m BID OHLC (bütünlük testi için)."""
    t, bid, _, _ = saat(h)
    if not len(t):
        return pd.DataFrame(columns=["t", "o", "h", "l", "c"])
    dk = t // 60000 * 60
    s = pd.DataFrame({"dk": dk, "b": bid}).groupby("dk")["b"]
    return pd.DataFrame({"t": s.first().index.to_numpy(), "o": s.first().to_numpy(), "h": s.max().to_numpy(),
                         "l": s.min().to_numpy(), "c": s.last().to_numpy()})


def denetle(saatler: list[int] | None = None, tol: float = 0.0011) -> dict:
    """Tikten kurulan 1m BID OHLC = Dukascopy 1m mumları (≥ %99 dakika), ms monoton, ask ≥ bid. Bozuksa istisna."""
    bar = V.barlar()
    saatler = saatler if saatler is not None else [h for h in gereken_saatler(olaylar()) if yol(h).exists()]
    n_dk = n_esit = n_ters = n_mono = 0
    for h in saatler:
        t, bid, ask, _ = saat(h)
        if not len(t):
            continue
        n_mono += int(np.any(np.diff(t) < 0))
        n_ters += int(np.sum(ask < bid))
        T = tik_1m(h)
        j = np.searchsorted(bar.t, T["t"].to_numpy())
        ok = (j < len(bar)) & (bar.t[np.minimum(j, len(bar) - 1)] == T["t"].to_numpy())
        j, T = j[ok], T[ok]
        es = ((np.abs(bar.o[j] - T["o"]) <= tol) & (np.abs(bar.h[j] - T["h"]) <= tol) & (np.abs(bar.l[j] - T["l"]) <= tol)
              & (np.abs(bar.c[j] - T["c"]) <= tol))
        n_dk += len(T)
        n_esit += int(es.sum())
    r = {"saat": len(saatler), "dakika": n_dk, "esit_pay": round(n_esit / max(n_dk, 1), 5), "monoton_bozuk_saat": n_mono,
         "ask_lt_bid": n_ters}
    if n_dk and (r["esit_pay"] < 0.99 or n_mono or n_ters):
        raise RuntimeError(f"tik bütünlüğü bozuk: {r}")
    return r


if __name__ == "__main__":
    k = sys.argv[1] if len(sys.argv) > 1 else "say"
    if k == "say":
        E = olaylar()
        print(E.groupby(["tur", "bolum"]).size(), "\nıska", int(E["iska"].fillna(False).sum()), "saat", len(gereken_saatler(E)))
    elif k == "indir":
        indir()
    elif k == "denetle":
        print(denetle())
