Projenin günlük sağlık kontrolünü yap:

## Kod Kalitesi
1. Son değişiklikleri git log'dan çek ve özetle
2. Kırılan import veya bağımlılık var mı kontrol et
3. TODO/FIXME/HACK yorumlarını listele

## Sinyal Performansı
4. prediction_logs'tan son 24 saatteki sinyalleri çek
5. Model bazlı win rate hesapla
6. Fake signal timeout tetiklenmiş mi?
7. En iyi ve en kötü performans gösteren model hangisi?

## Sistem Sağlığı
8. Cache TTL'leri doğru çalışıyor mu?
9. EODHD API kullanımı (100K limit'e göre yüzde kaç?)
10. Supabase bağlantı durumu

## Öneriler
11. Performans iyileştirme fırsatları
12. Kod tekrarı (DRY violation) var mı?
13. Eksik error handling
14. Güncellenmeyi bekleyen CLAUDE.md bölümleri

Özeti kısa ve aksiyona yönelik tut.
