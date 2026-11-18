# Ön kayıt — Korku gecesi sepeti: K1'in NDX + US30 + US2000'de birlikte işlenmesi (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
K1 dört ABD endeksinde ayrı ayrı çalışıyor (GI-02 B+). Tetikler endeks başına farklı geceler seçiyor. Soru: aynı toplam riski endekslere
bölmek portföyün günlük Sharpe oranını artırır mı (çeşitlendirme), yoksa korelasyon yüzünden hiçbir şey kazandırmaz mı?

## Veri ve kural
MT5 M30 (aynı broker, tutarlılık için): NAS100, US30, US2000 (2018-05 →). US500 yalnız 2021 → olduğu için dışarıda; bilgi olarak
2021 sonrası 4'lü sepet raporlanır. K1 değiştirilmeden (16:00 TWAP × 0,995 altı ∧ son saat aşağı → 16:00 AL, ertesi 16:00).

## Karşılaştırma
- **Tek:** yalnız NAS100 K1, 1 risk birimi.
- **Sepet:** her endeks kendi K1'iyle; her işlem 1/3 birim. Birim = endeksin tüm K1 işlemlerinin σ'sı (eşit risk).
- Ölçü: günlük piyasa değeri (16:00 → 16:00, boşta 0) Sharpe √252, maxDD (tek birimin σ cinsinden), yıllık getiri.
- **B:** ESKİ (→ 2021-10) ve YENİ ikisinde de Sharpe(sepet) > Sharpe(tek) ∧ tüm dönem maxDD(sepet) ≥ maxDD(tek), yani daha sığ.
- Yalnız biri → C; hiçbiri → X.
Bilgi: endeksler arası işlem günü korelasyonu, sepet kazancının endekslere dağılımı.
