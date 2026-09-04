"""Ölçüm ve kabul kapıları.

⚠️ Bu oturumun en pahalı dersi: İÇ-ÖRNEKLEM dayanıklılığı (plato, hafta-çıkarma,
permütasyon) GERÇEK DIŞ-ÖRNEKLEMİN yerini TUTMAZ. Bir kural in-sample'da
plato + 9/9 hafta + p=0,003 verip yeni haftada tam ters dönebildi.
Bu yüzden `dis_orneklem` ALANI DOLDURULMADAN hiçbir strateji 'geçti' sayılmaz.
"""
from __future__ import annotations
import random
import statistics


def R(t, usd: float | None = None) -> float:
    """İşlemin R karşılığı (risk = sl_d × lot)."""
    v = t["usd"] if usd is None else usd
    return v / (t["sl_d"] * t["lot"])


def ozet(islemler, degerler: dict | None = None) -> dict:
    """degerler: id(t) -> yeni USD. Verilmezse gerçek sonuç kullanılır."""
    def d(t):
        return degerler.get(id(t), 0.0) if degerler is not None else t["usd"]
    v = [d(t) for t in islemler]
    n = len(v) or 1
    return {"n": len(v), "usd": sum(v),
            "wr": sum(1 for x in v if x > 0) / n * 100,
            "ortR": statistics.mean([R(t, d(t)) for t in islemler]) if islemler else 0.0}


def ceyrekler(islemler, degerler=None) -> list[float]:
    q = len(islemler) // 4
    out = []
    for i in range(4):
        dil = islemler[i * q:(i + 1) * q if i < 3 else len(islemler)]
        out.append(ozet(dil, degerler)["usd"])
    return out


def hafta_cikarma(islemler, degerler) -> tuple[int, int]:
    """Kaç haftada kural bazı geçiyor? (tek haftaya bağımlılık dedektörü)"""
    haftalar = sorted({t["hafta"] for t in islemler})
    iyi = 0
    for h in haftalar:
        alt = [t for t in islemler if t["hafta"] != h]
        if ozet(alt, degerler)["usd"] > ozet(alt)["usd"]:
            iyi += 1
    return iyi, len(haftalar)


def permutasyon(kalan, elenen, N: int = 20000, tohum: int = 7) -> float:
    """Elenen küme gerçekten daha mı kötü? Dönen: p değeri."""
    if not kalan or not elenen:
        return 1.0
    rnd = random.Random(tohum)
    a = [R(t) for t in kalan]
    b = [R(t) for t in elenen]
    gozlenen = statistics.mean(a) - statistics.mean(b)
    hepsi = a + b
    k = len(a)
    say = 0
    for _ in range(N):
        rnd.shuffle(hepsi)
        if statistics.mean(hepsi[:k]) - statistics.mean(hepsi[k:]) >= gozlenen:
            say += 1
    return say / N


def bootstrap(farklar, N: int = 5000, tohum: int = 11) -> tuple[float, float, float]:
    """Farkın %95 GA'sı + P(fark>0). GA sıfırı içeriyorsa gürültüden ayrılamaz."""
    if not farklar:
        return 0.0, 0.0, 0.0
    rnd = random.Random(tohum)
    n = len(farklar)
    boot = sorted(sum(farklar[rnd.randrange(n)] for _ in range(n)) for _ in range(N))
    return boot[int(0.025 * N)], boot[int(0.975 * N)], sum(1 for x in boot if x > 0) / N


def kart(islemler, degerler, dis_orneklem: str = "YAPILMADI") -> str:
    """Canlıya alma kartı (CLAUDE.md 6 ölçüt + dış-örneklem şartı)."""
    b, m = ozet(islemler), ozet(islemler, degerler)
    cey = ceyrekler(islemler, degerler)
    iyi, top = hafta_cikarma(islemler, degerler)
    farklar = [degerler.get(id(t), 0.0) - t["usd"] for t in islemler]
    lo, hi, p = bootstrap(farklar)
    sat = [
        f"  hacim        : n={m['n']}  {'GEÇTİ' if m['n'] >= 150 else 'KALDI (<150)'}",
        f"  beklenti     : ortR={m['ortR']:+.3f} (baz {b['ortR']:+.3f})",
        f"  çeyrekler    : {[round(c) for c in cey]}  "
        f"{sum(1 for c in cey if c > 0)}/4 pozitif",
        f"  hafta-çıkarma: {iyi}/{top}",
        f"  bootstrap    : %95GA=[{lo:+.0f},{hi:+.0f}] P(fark>0)=%{p*100:.1f}  "
        f"{'GEÇTİ' if lo > 0 else 'KALDI (GA sıfırı içeriyor)'}",
        f"  DIŞ-ÖRNEKLEM : {dis_orneklem}",
        f"  USD          : {b['usd']:+.0f} → {m['usd']:+.0f}  ({m['usd']-b['usd']:+.0f})",
    ]
    return "\n".join(sat)
