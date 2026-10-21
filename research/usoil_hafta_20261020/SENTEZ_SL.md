# USOIL son hafta — zarar ettiren 2 işlemin derin otopsisi, bağlantılar ve geçmiş sınaması (2026-10-20)

Ön-kayıt: [PROTOCOL_SL.md](PROTOCOL_SL.md). Tekil otopsiler: `output/islem_otopsi/2026-10-20_2335_usoil/otopsi_405554591.md`,
`otopsi_406667349.md` (+ grafikler). Bot logu: `results/log_sl.txt`. Sınama: `sl_hipotez.py` → `results/sl_hipotez.md`.

## 1. Neden zarar ettiler?
### #405554591 — Pazar 22:09 UTC, MOMSR BUY 10 lot, −1.486 $
- **Ne oldu:** haftalık açılışın ilk dakikaları. Açılıştan önce konum kapısı BUY'u (fiyat 4s dalganın tepesinde, 0,73)
  engelliyordu. Açılışta fiyat düşünce konum kapısı açıldı, 3 voter + backend "FALLBACK_MARKET" verdi ve bot S/R geri
  çekilme yoluyla 7 dokunuşlu bölgeye LIMIT BUY koydu (99,67).
- **Giriş anı:** son 15 dk −5,8 ATR5, 5m RSI 22, 4s aralığın dibinde (0,02), gün −%1,2. Bu değerlerin hepsi botun önceki
  USOIL BUY'larında **hiç görülmemişti (0. yüzdelik)** — bot "momentum" BUY'unu düşen bıçakta açtı.
- **Botun kendi uyarıları (gölgede, engellemedi):** giriş skoru 4/8 (ihlal: ema200_tarafi, 1h_karsi_momentum,
  bicak_yakalama, 5m_trend). Backend SL'i basis farkı (%0,67) yüzünden reddedildi → config SL %1,49.
- **Yol:** en iyi nokta +0,07R (13. dk), 28. dk'da yapı kırıldı, 85. dk'da aleyhte hacim şoku; 501. dk'da SL. Çıkış sonrası
  fiyat girişe geri döndü (kararsız). Tür: **"hiç çalışmadı"**.
### #406667349 — Salı 12:15 UTC, MOMSR BUY 10 lot, −1.515 $
- **Ne oldu:** petrol gün içinde +%2,4 yükselmişti. 2 voter + backend; S/R geri çekilme LIMIT BUY 101,636 (6 dokunuşlu bölge).
- **Uyarılar (gölgede):** seans filtresi (12 UTC < 13), sıkı konum kapısı (0,60), giriş skoru 5/8 (ema200_tarafi,
  adx_dusuk, bicak_yakalama). Backend SL basis farkıyla reddedildi.
- **Yol:** en iyi +0,06R (4. dk), 7. dk'da yapı kırıldı, son bacak ilk bacaktan ×1,7 hacimli; 80. dk'da SL ve **SL sonrası
  fiyat −3,5R daha düştü** → gerçek bir yön dönüşü (stop genişliği kurtarmazdı). Tür: **"hiç çalışmadı / yön yanlış"**.

## 2. Bağlantılar (iki SL'nin ortak noktaları)
| ortak nokta | geçmişte SL'yi açıklıyor mu? |
|---|---|
| ikisi de "hiç çalışmadı" (MFE < 0,15R) | bu tip USOIL SL'lerinin %44'ü; rastgele girişte %42 → mekanik, bota özgü değil |
| ikisi de S/R geri çekilme LIMIT yolu | botun USOIL BUY'larının 80/88'i bu yoldan; ortR +0,017 (market yolu 8 işlem +0,245 — n çok küçük) |
| ikisinde `bicak_yakalama` (30 dk'da −1,5 ATR1m) | **hayır** — kalan 88 bot işleminde Δ +0,01R; 9.135 panel sinyalinde −0,015 |
| ikisinde `ema200_tarafi` (log) | hayır — Δ +0,08 (bot), −0,01 (panel) |
| giriş skoru ≤5 | botta yok (Δ −0,04, P %61); panelde zayıf uyarı (Δ −0,07, P %94) |
| backend SL basis farkı | hayır — SL'lerde medyan %1,15, TP'lerde %1,48 (vadeli–CFD kalıcı farkı) |
| (yalnız 1.) haftalık açılış | botta önceden yalnız 1 işlem; panel −0,15R ama yarılar ters; spread normal (0,028 vs 0,024) |
| (yalnız 2.) gün ≥+%2 ralli sonrası | botta TERS (+0,21R daha iyi); bot döneminin panelinde −0,18R; yarılar ters |

## 3. Geçmiş sınaması — `results/sl_hipotez.md` (6 hipotez × 3 popülasyon, eşikler önceden)
Hiçbiri ön-kayıtlı ölçütü geçmedi (botta P(kurt>0) ≥ %90 + panelde P(Δ<0) ≥ %90 ve iki yarıda + engellenenlerde aynı işaret).

## 4. Bu hatayı nasıl engelleyebilirdik?
- **Kanıtlı bir giriş kuralıyla: engelleyemezdik.** İki SL'nin giriş anındaki özellikleri, botun geçmiş USOIL BUY'larında
  TP'leri de aynı sıklıkta taşıyor. Otopsinin §2b plasebosu da aynı şeyi söylüyor: botun USOIL girişi rastgeleden ayırt edilemiyor
  (−0,06R, P %23) → tek tek SL'ler büyük ölçüde braketin (TP %1,04 / SL %1,49, RR 0,70) doğal sonucu.
- **Mantıksal ama kanıtsız tek aday:** haftalık açılışın ilk 30–60 dakikasında yeni giriş açmamak (NDX'te Asya yasağı B3
  zaten var; USOIL'de yok). Botun geçmişinde neredeyse hiç örneği yok (1 işlem), panelde yarılar tutarsız → kural değil,
  istenirse gölge kaydı.
- **Yapma:** stop genişletmek (#406667349 SL sonrası −3,5R gitti), kâra geçince BE/kilit (M9 elendi), seans kapısını açmak
  (B15 ileri dönemde ters, IO-24).
