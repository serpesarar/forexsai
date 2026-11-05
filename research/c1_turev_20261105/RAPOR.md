# TR — NDX → XAU → USOIL aday taraması (ara rapor, 2026-11-05)
Ön kayıt PROTOCOL.md + EK-1…16. Her hücre `results/denemeler.csv`. Makro sürpriz arşiv inince eklenecek.

| Aday | Kural | Kanıt | Hüküm |
|---|---|---|---|
| **C3b** | NDX, 15:30 ET RSI2<10 → uzun; ilk yükselen 15:30'da çık (≤5 g), stop yok | MT5 2016-26 n=155 +65 bp %78, kart 6/6; **kör: US500 +53,8, US30 +34,4, Duka NDX +100 (broker farkı −1,8)**; QQQ 1999→ | **A** |
| **C3** | Aynı giriş, ertesi 15:30 çıkış | n=201 +45,7 bp %62, kart 6/6 | A− |
| **C1** | ORB uzun ∧ VIX≥18,4 | 10 yıl n=605 +0,185R; kart 6/6; 2026 zayıf; gölgede | B |
| P1 | C3 + C1' | +11.298 bp, 9/9 yıl, DD −1.177 | C (filtre doğrulanmadı) |
| Bilanço gecesi | S13b | 2012-25 + ; 2026 − | C |
| XAU X2 | VIX z≤−1,5 → D 18:30 uzun, D+1 13:00 | 4 dönem + (+4…+32), n≈97, P ≤ %91 | C |
| C4 | 55g dip 10g uzun | rejim bağımlı | C |
| USOIL | hiçbiri | ORB, saat, Donchian, olay barı, şok | X |

Karşıt türevler kenarsız: kırılımı satmak −0,2R; coşku kısa/uzun geçmedi; "RSI2<10 iken SELL açma" canlı işlemlerde kanıt yok.
Yeni tuzaklar: E95 açılış boşluğu, E96 gelecek bilgili taban, E97 yeniden açılış spread'i, E98 şans sayımı, E99 uzlaşma saati.
Beklenti: geçmiş ortalaması üst sınırdır. C3b için en kötü tek işlem −683 bp; stop kullanılmadığı için büyüklük bu kuyruğa göre seçilmeli.
