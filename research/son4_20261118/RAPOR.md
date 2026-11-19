# Son dört kapı — zaman çıkışlı adaylar ve OPEX vade penceresi (2026-11-18)

Ön kayıt `PROTOCOL.md` + EK-1…7. Kod `src/`, çıktılar `results/`. Kart `backend/data/evolution/go_live_cards/ndx_opex_korku_vetosu.json`.

## Sonuç: 4 kapı adayı, 1'i B
| # | Kapı | Kanıt | Hüküm |
|---|---|---|---|
| **1** | **OPEX Çar/Per korku alımı vetosu** — aylık opsiyon vadesi haftasının Çarşamba ve Perşembe günü C3b/C3, K1 korku gecesi ve ertesi seans uzunlarını AÇMA | C3b QQQ (giriş gününe göre, sızıntısız) −66 bp P 0,99; **bağımsız ^NDX 1985–99 −240 bp P 0,9998**; gerçek gün içi K1 5 besleme (Duka NDX, MT5 NAS100, US500, US30, US2000) 5/5 eksi −41…−89 bp, havuz P 1,00; OPEX dışı Çar/Per'e göre 8/8 set eksi (gün etkisi değil); canlı kitap Duka 2018–26 C3B −106 bp (ESKİ −134 / YENİ −102), C3 −61; sıradan gece tutuşu (KSG) farksız → etki korku dönüşüne özgü. Kart 5/6 (vetolanan işlemler ikinci yarıda mutlak ≈ 0, göreli −43 bp P 0,989) | **B** (veto; canlıya bağlama kullanıcı kararı) |
| 2 | ORB×VIX OPEX Çar–Cum vetosu (uzun kırılım) | Ön kayıtlı öngörü tuttu: Duka −0,30R P 0,976, ESKİ −0,25 / YENİ −0,34; genel sürüm Duka'yı yeniden üretiyor (−0,27); bağımsız NQ 5m −0,17, MT5 M15 −0,28 ama örtüşmesiz havuz P 0,79. Aşağı kırılım kolu OPEX'te tersine artı (+0,16R) | C+ |
| 3 | Perşembe korku alımı vetosu (haftalık vade, doğal deney) | Haftalık opsiyon 2005'te başladı: Perşembe girişli K1/C3b farkı 1993–2004'te ≈ 0 (QQQ C3b +8, SPY K1 +3), 2005–2022'de −32…−42 (P 0,91–0,95), 2022 sonrası −45…−97; SPY C3b uymuyor | C+ |
| 4 | OPEX Çar kapanış → Cuma kapanış SAT (VS W3 → EK-1 OX) | NDX 4 dönemde diğer haftalara göre +18…+30 bp (P 0,79–0,92), QQQ 1999–2026 P 0,987, gün içi kör havuz P 0,993; ama ^GSPC 1983–98 ters ve endeks opsiyonu olmayan 1950–83'te de var (t 2,1) → mekanizma OPEX değil, ay ortası takvim etkisi olabilir | C+ |

## Elenenler
- **SN yükseliş serisi** (NQ-03 genişletmesi): seri 6 → 5 g aynı yıl rastgele başlangıçla yüzdelik 0,49, broker 2008+ −2 bp → **X**; NQ-03'ün C+'ı boğa yıllarının sürüklenmesiydi (E103).
- **HP aynı saat dilimi sürekliliği** (HKS 2010): endekslerde **ters** — dilim getirileri 20 günlük geçmişine göre dönüyor (plasebodan anlamlı kötü, 5 besleme); tersini işlemek spread sonrası ≈ 0 → X.
- **SB sabah trendi** 13:00 → 16:00: tüm NDX beslemelerinde artı (Duka kart 6/6 +6 bp, 2016–18 H1 +4,4, EET30 +6,0) ama US500/US30/US2000'de yok ve olay günü öngörüsü ters → C+ kalır.
- **VS VIX vade haftası:** W3 dışında pencereler X; W3 OPEX etkisine dönüştü (yukarıda 4).
- **Vade sonrası doz** (OPEX sonrası Pzt/Salı korku alımı): X.

## Mekanizma okuması
Vadeye 1–2 gün kala korku dönüşü çalışmıyor; vade geçtikten sonra da ekstra kazanç yok. Dealer'ların vadesi gelen opsiyon hedge'i
(gamma) vade öncesinde fiyatın dönüşünü bastırıyor olabilir; vade haftasında genel zayıflık (4) ve uzun kırılımın sönmesi (2) aynı
resmi veriyor. Mekanizma doğrulanmadı (opsiyon pozisyon verisi yok); kural yalnız ölçülen davranışa dayanıyor.
