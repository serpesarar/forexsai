$ARGUMENTS sembolü için sembol sayfasını oluştur veya güncelle.

Eğer sembol sayfası henüz yoksa, şu 5 bölümlü yapıyı oluştur:

## Sayfa Yapısı (önem sırasına göre yukarıdan aşağıya)

1. **Üst Bar** — Canlı fiyat + Meta Signal özet (yan yana)
2. **Ortak Grafik** — SharedChart component, timeframe sekmeleri, overlay toggle'ları
3. **Sinyal Grid** — 6 model kartı 2×3 grid (ML, EMEL, SMC, Pulse1, Pulse2, Pulse3)
4. **Piyasa Bağlamı** — Regime + COT/Whale + AI Panel özet (3 kart)
5. **Performans Scoreboard** — Yatay kaydırılabilir model performans kartları

## Kontrol Listesi

Her bölüm için:
- [ ] Doğru API endpoint'e bağlı mı?
- [ ] Loading skeleton var mı?
- [ ] Error state var mı?
- [ ] Empty state var mı?
- [ ] Dark mode doğru çalışıyor mu?
- [ ] Responsive breakpoint'ler (desktop/tablet/mobil)
- [ ] Renk kodlaması tutarlı mı? (BUY=yeşil, SELL=kırmızı, HOLD=gri)

## Tekrar Kontrolü
- Bu sembol için başka yerde aynı paneli gösteren component var mı?
- Varsa kaldır, yeni sayfaya yönlendir
- SharedChart kullanılıyor mu, yoksa kendi grafiği mi var?

## Component Reuse
SignalCard, ConfidenceBar, StatusBadge gibi shared component'ler zaten varsa
onları kullan, yoksa oluştur ve diğer sembol sayfaları da kullanabilecek
şekilde props-driven yap.

Sonuçları göster: hangi component'ler oluşturuldu, hangiler yeniden kullanıldı,
hangiler temizlendi.
