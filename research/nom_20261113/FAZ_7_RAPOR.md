# FAZ 7 — Panel: "Olasılık Motoru" sayfası (NOM, 2026-11-13)

Sayfa: `frontend/app/olasilik-motoru/page.tsx` → `/olasilik-motoru`; navigasyon: `SharedNavHeader` "Olasılık Motoru".
Bileşen: `frontend/components/nom/ProbabilityEnginePanel.tsx`; servis katmanı: `frontend/lib/api/nom.ts`
(bileşende `fetch` yok — React Query hook'ları, 60 sn yenileme).

| İstenen | Uygulama |
|---|---|
| LONG ve SHORT olasılık barları (kalibre + güven aralığı) | Yön başına üç parçalı yığın bar (TP önce / SL önce / zaman aşımı) + yüzdeler; "bu kovada geçmişte gerçekleşen TP" WF %95 bandı; beklenen R (sürtünmeli) + taban; "kanıtlı hedef / kanıtsız — yalnız bilgi" rozeti |
| Destek/direnç haritası, uzaklık | SVG merdiveni ±3 ATR(H1): her seviye fiyat · ATR uzaklığı · test sayısı · tür (pivot M15/H1/D1, önceki gün, gece, ORB, 20 gün, yuvarlak); çizgi kalınlığı test sayısıyla artar |
| RSI ve rejim göstergeleri | M5/M15/H1/H4/D1 RSI14 şeritleri (30/70 işaretli, aşırı bölge renkli), ADX/rejim, ATR rejimi, EMA dizilimi, HH/HL yapısı, seans, VIX rejimi (18,4), yaklaşan olay |
| "Neden?" (SHAP) | Yön başına TreeSHAP ile P(TP)'yi en çok etkileyen 5 faktör, Türkçe cümle + işaret noktası |
| Geometri ve ufuk seçici | 15 dk / 1 saat / 4 saat / seans sonu düğmeleri; TP/SL 1.0x1.0 … 1.5x1.5 açılır listesi; ATR biriminin puan karşılığı |
| Canlı kalibrasyon grafiği | `nom_predictions`'tan kova bazlı reliability (canlı nokta, bant dışı turuncu) + WF %95 referans çubukları; Brier becerisi, ort. R, mezuniyet durumu, drift uyarısı |
| Durum hâlleri | yükleniyor / hata / `VERI_BAYAT` · `PIYASA_KAPALI` · `UFUK_TANIMSIZ` (tahmin yok) / gölge verisi henüz yok |
| Model sürümü + tazelik | alt bilgi: sürüm, eğitim sonu, veri kaynağı, gecikme (sn), "emir açmaz" notu |

Renk kodu proje sistemine uygun: BUY/LONG yeşil, SELL/SHORT kırmızı, nötr gri; motor vurgusu turuncu.
Tip kontrolü (`tsc --noEmit`) bu dosyalarda hatasız. Tarayıcı doğrulaması: `FAZ_6_RAPOR.md` §Canlı doğrulama.
