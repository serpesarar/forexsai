"""Veri yükleme — SEMBOL BAĞIMSIZ.

Her strateji aynı iki girdiyle çalışır:
  * 1m barlar  : time_utc,open,high,low,close[,tick_volume]
  * işlemler   : box_export_trades_30d.py formatı

⚠️ ZAMAN EKSENİ: işlem CSV'si ile bar CSV'si AYNI eksende olmalı. Yüklemeden
önce `hizalama_kontrol()` çalıştır — 2026-08-29'da bir export +1230 dk kayık
çıkmıştı ve tüm analizleri bozmuştu (bkz. README §Dersler).
"""
from __future__ import annotations
import csv
import datetime as dt
from bisect import bisect_left
from dataclasses import dataclass, field

MAGIC_AILE = {
    "52890969": "MOM/SR", "52890970": "CHREV", "52890971": "VIXREG",
    "52890973": "DAYCOMBO", "52890974": "USOIL_BO", "52890975": "REENTRY",
}


@dataclass
class Veri:
    """Bir sembolün bar + işlem seti."""
    sembol: str
    barlar: list          # [(ts, o, h, l, c), ...] artan
    bar_ts: list          # [ts, ...] bisect için
    islemler: list        # [dict, ...] artan
    _tf_cache: dict = field(default_factory=dict)

    def resample(self, dakika: int) -> list:
        """1m barlardan üst zaman dilimi üret (kova hizalı)."""
        if dakika in self._tf_cache:
            return self._tf_cache[dakika]
        out = {}
        for ts, o, h, l, c in self.barlar:
            d = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
            k = (d.replace(minute=(d.minute // dakika) * dakika, second=0, microsecond=0)
                 if dakika < 60 else d.replace(minute=0, second=0, microsecond=0)).timestamp()
            if k not in out:
                out[k] = [o, h, l, c]
            else:
                out[k][1] = max(out[k][1], h)
                out[k][2] = min(out[k][2], l)
                out[k][3] = c
        r = sorted((k, v[0], v[1], v[2], v[3]) for k, v in out.items())
        self._tf_cache[dakika] = r
        return r

    def baz_usd(self) -> float:
        return sum(t["usd"] for t in self.islemler)


def bar_yukle(path: str) -> tuple[list, list]:
    b = []
    for r in csv.DictReader(open(path)):
        t = dt.datetime.fromisoformat(r["time_utc"].replace("Z", "+00:00"))
        b.append((t.timestamp(), float(r["open"]), float(r["high"]),
                  float(r["low"]), float(r["close"])))
    b.sort()
    return b, [x[0] for x in b]


def islem_yukle(path: str, sembol: str) -> list:
    """box_export formatı → normalize işlem listesi (yalnız kapanmışlar)."""
    T = []
    for r in csv.DictReader(open(path)):
        if r.get("symbol") != sembol or not r.get("close_time_utc"):
            continue
        o = float(r["open_price"])
        sl = float(r["sl_price"] or 0)
        tp = float(r["tp_price"] or 0)
        risk, hedef = abs(o - sl), abs(tp - o)
        if not risk or not hedef:
            continue
        ta = dt.datetime.fromisoformat(r["open_time_utc"])
        T.append({
            "ts": ta.timestamp(), "dt": ta, "yon": r["direction"], "o": o,
            "tp_d": hedef, "sl_d": risk, "lot": float(r["volume"]),
            "usd": float(r["profit"]) + float(r["swap"]),
            "aile": MAGIC_AILE.get(r["magic"], r["magic"]),
            "sl_mi": r["exit_reason"] == "sl",
            "hafta": ta.isocalendar()[1], "ay": ta.month,
        })
    return sorted(T, key=lambda x: x["ts"])


def yukle(sembol: str, bar_csv: str, islem_csv: str) -> Veri:
    b, bt = bar_yukle(bar_csv)
    return Veri(sembol, b, bt, islem_yukle(islem_csv, sembol))


def hizalama_kontrol(v: Veri, tolerans: float = 15.0) -> dict:
    """İşlem fiyatları bar aralığına oturuyor mu? (zaman kayması dedektörü)

    Dönen 'en_iyi_lag' 0 değilse veri KAYIK — analize başlama."""
    bars = {int(ts // 60) * 60: (l, h) for ts, o, h, l, c in v.barlar}
    sonuc = {}
    for lag in (-1230, -180, -60, 0, 60, 180, 1230):
        ic = n = 0
        for t in v.islemler:
            k = int((t["ts"] + lag * 60) // 60) * 60
            b = bars.get(k)
            if not b:
                continue
            n += 1
            if b[0] - tolerans <= t["o"] <= b[1] + tolerans:
                ic += 1
        sonuc[lag] = (ic / n * 100) if n else 0.0
    en_iyi = max(sonuc, key=lambda k: sonuc[k])
    return {"oranlar": sonuc, "en_iyi_lag": en_iyi, "uyum": sonuc[en_iyi],
            "temiz": en_iyi == 0 and sonuc[0] > 90}
