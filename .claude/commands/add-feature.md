$ARGUMENTS içindeki özelliği ForexSAI projesine ekle.

Ekleme yaparken şu kontrol listesini takip et:

## Backend
1. İlgili service dosyasını bul veya yeni oluştur
2. Router'a endpoint ekle (eğer gerekiyorsa)
3. Type hints ve docstring'leri yaz
4. Error handling ekle (try/except + logging)
5. Cache stratejisi belirle (TTL ne olmalı?)

## Database
6. Supabase schema değişikliği gerekiyorsa migration SQL yaz
7. Index gerekiyorsa ekle
8. RLS policy güncelle

## Frontend
9. TypeScript type/interface tanımla
10. API service fonksiyonu yaz
11. Component oluştur veya mevcut component'i güncelle
12. Loading, error ve empty state'leri ekle
13. Responsive tasarım kontrol et

## Entegrasyon
14. Mevcut 6 modelle etkileşim var mı? Varsa bağlantıları kur
15. Regime-aware davranış gerekiyor mu?
16. WebSocket broadcast gerekiyor mu?
17. prediction_logs'a loglama gerekiyor mu?

## Kalite
18. Edge case'leri düşün ve handle et
19. İlgili test'leri güncelle veya yaz
20. CLAUDE.md'yi güncellenmesi gerekiyorsa bildir

Tüm değişiklikleri tek seferde yap, ikinci komut gerektirme.
