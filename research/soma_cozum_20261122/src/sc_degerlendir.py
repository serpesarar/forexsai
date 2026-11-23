"""SC — standart değerlendirme + deneme defteri + kilitli KASA koruması.

Dönemler (PROTOCOL.md SC-00, sonuçlardan önce donduruldu):
  HESAP       2024-11-01 → 2026-11-14  sağlayıcının dönemi: çözümleme (strateji SEÇİMİ burada yapılırsa bağımsız sayılmaz)
  GELISTIRME  2018-01-01 → 2022-01-01  sınırsız iterasyon (hepsi deftere yazılır)
  DOGRULAMA   2022-01-01 → 2024-11-01  aday başına bir koşu; Bonferroni N = o güne kadar doğrulamaya giren aday sayısı
  KASA        2010-01-01 → 2018-01-01  kilitli: yalnız PROTOCOL.md'de KASA adayı olarak yazılmış kimlik, kimlik başına BİR kez

Her `kaydet` çağrısı results/deneme_defteri.jsonl'a satır ekler (bar sürümü, git kısa hash, parametreler, özet).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

import sc_veri as V

KOK = Path(__file__).resolve().parents[1]
DEFTER = KOK / "results" / "deneme_defteri.jsonl"
KASA_KAYIT = KOK / "results" / "kasa_kullanim.json"
PROTOKOL = KOK / "PROTOCOL.md"
DONEM = {
    "HESAP": ("2024-11-01", "2026-11-14"),
    "GELISTIRME": ("2018-01-01", "2022-01-01"),
    "DOGRULAMA": ("2022-01-01", "2024-11-01"),
    "KASA": ("2010-01-01", "2018-01-01"),
}
N_BOOT = 5000
TOHUM = 20261122


def ts(tarih: str) -> int:
    return int(pd.Timestamp(tarih, tz="UTC").timestamp())


def donem_maske(t: np.ndarray, donem: str, deney_id: str | None = None) -> np.ndarray:
    if donem == "KASA":
        kasa_izni(deney_id)
    a, b = DONEM[donem]
    return (t >= ts(a)) & (t < ts(b))


def kasa_izni(deney_id: str | None) -> None:
    """KASA yalnız: SC_KASA_ACIK=<deney_id> ortam değişkeni ∧ kimlik PROTOCOL.md 'KASA ADAYI: <id>' satırında ∧ daha önce açılmamış."""
    if not deney_id or os.getenv("SC_KASA_ACIK") != deney_id:
        raise PermissionError("KASA kilitli: SC_KASA_ACIK=<deney_id> gerekir")
    if not re.search(rf"KASA ADAYI:\s*{re.escape(deney_id)}\b", PROTOKOL.read_text()):
        raise PermissionError(f"{deney_id} PROTOCOL.md'de KASA ADAYI olarak ön kayıtlı değil")
    kayit = json.loads(KASA_KAYIT.read_text()) if KASA_KAYIT.exists() else {}
    if deney_id in kayit:
        raise PermissionError(f"{deney_id} KASA'yı {kayit[deney_id]} tarihinde zaten kullandı (kimlik başına bir kez)")
    kayit[deney_id] = time.strftime("%Y-%m-%d %H:%M:%S")
    KASA_KAYIT.write_text(json.dumps(kayit, indent=1, ensure_ascii=False))


# ───────────────────────── istatistik ─────────────────────────
def gun_blok_P(x: np.ndarray, gun: np.ndarray, n_boot: int = N_BOOT, tohum: int = TOHUM) -> float:
    """Gün bloklu bootstrap: P(ortalama > 0). Günler yeniden örneklenir, gün içi işlemler birlikte."""
    if len(x) < 2:
        return float("nan")
    kod, ters = np.unique(gun, return_inverse=True)
    top = np.bincount(ters, weights=x)
    adet = np.bincount(ters).astype(float)
    rng = np.random.default_rng(tohum)
    sec = rng.integers(0, len(kod), (n_boot, len(kod)))
    ort = top[sec].sum(1) / adet[sec].sum(1)
    return float((ort > 0).mean())


def fark_P(a: np.ndarray, b: np.ndarray, gun: np.ndarray, **kw) -> float:
    """Eşleşmiş fark (a − b) için gün bloklu P(fark > 0)."""
    m = np.isfinite(a) & np.isfinite(b)
    return gun_blok_P(a[m] - b[m], gun[m], **kw)


def tek_pozisyon(df: pd.DataFrame, t0: str = "t0", t1: str = "t1") -> pd.DataFrame:
    """Aynı anda tek pozisyon (kart ölçütü 6): kronolojik, açık pozisyon varken gelen işlem atlanır."""
    d = df.sort_values(t0)
    tut, son = [], -1
    for k, (a, b) in enumerate(zip(d[t0].to_numpy(), d[t1].to_numpy())):
        if a >= son:
            tut.append(k)
            son = b
    return d.iloc[tut]


def ozet(df: pd.DataFrame, bp: str = "bp", t: str = "t0") -> dict:
    d = df[np.isfinite(df[bp])].sort_values(t)
    x = d[bp].to_numpy()
    if len(x) == 0:
        return {"n": 0}
    gun = (d[t].to_numpy() // 86400)
    yil = pd.to_datetime(d[t], unit="s").dt.year.to_numpy()
    yari = len(x) // 2
    kazanc, kayip = x[x > 0].sum(), -x[x < 0].sum()
    gunluk = pd.Series(x).groupby(gun).sum()
    egri = np.cumsum(x)
    return {
        "n": int(len(x)), "ort_bp": round(float(x.mean()), 3), "medyan_bp": round(float(np.median(x)), 3),
        "isabet": round(float((x > 0).mean()), 3), "PF": round(float(kazanc / kayip), 3) if kayip > 0 else None,
        "toplam_bp": round(float(x.sum()), 1), "P": round(gun_blok_P(x, gun), 4),
        "yari1": round(float(x[:yari].mean()), 3) if yari else None, "yari2": round(float(x[yari:].mean()), 3),
        "yillik": {int(y): round(float(x[yil == y].mean()), 2) for y in np.unique(yil)},
        "yillik_n": {int(y): int((yil == y).sum()) for y in np.unique(yil)},
        "sharpe_gunluk": round(float(gunluk.mean() / gunluk.std() * np.sqrt(252)), 3) if gunluk.std() > 0 else None,
        "maks_dusus_bp": round(float((np.maximum.accumulate(egri) - egri).max()), 1),
    }


# ───────────────────────── deneme defteri ─────────────────────────
def _git() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=KOK).stdout.strip()
    except Exception:  # noqa: BLE001
        return "?"


def kaydet(deney_id: str, donem: str, parametre: dict, sonuc: dict, not_: str = "") -> dict:
    satir = {"zaman": time.strftime("%Y-%m-%d %H:%M:%S"), "deney": deney_id, "donem": donem,
             "bar": V.bar_surumu(), "git": _git(), "parametre": parametre, "sonuc": sonuc, "not": not_}
    satir["kimlik"] = hashlib.sha1(json.dumps([deney_id, donem, parametre], sort_keys=True, default=str)
                                   .encode()).hexdigest()[:10]
    DEFTER.parent.mkdir(parents=True, exist_ok=True)
    with DEFTER.open("a") as f:
        f.write(json.dumps(satir, ensure_ascii=False, default=str) + "\n")
    return satir


def defter() -> pd.DataFrame:
    if not DEFTER.exists():
        return pd.DataFrame()
    return pd.DataFrame([json.loads(s) for s in DEFTER.read_text().splitlines() if s.strip()])


def dogrulama_sayisi() -> int:
    """Bonferroni için: DOGRULAMA dönemine giren farklı aday (deney+parametre) sayısı."""
    d = defter()
    return int(d[d["donem"] == "DOGRULAMA"]["kimlik"].nunique()) if len(d) else 0
