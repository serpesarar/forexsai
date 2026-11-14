# FAZ 3 — Karar noktaları ve etiketler (Yön Lab, 2026-11-14)

Kod: `src/core.py`, `src/build_grid.py`. Çıktı: `data/run_real/` (ve `run_mart1…10/`).

- **Izgara:** 109.910 karar noktası (15 dk, 2021-12-01 → 2026-11-04; KEŞİF 58.723 · DOĞRULAMA 31.916 · KÖR 19.264). Olay noktaları =
  ızgaradan referansa ≤ 0,25 ATR(H1) yakın olanlar, aynı üye için ≥ 60 dk refrakter (ret/kırılım atlası).
- **Etiketler** (yalnız t'den sonra açılan 1m BID barları):
  1. `dir_15m/1h/4h/sess` işaret + büyüklük (ATR).
  2. `sym_1`: ±1·ATR(M15), 60 dk; ve FU/FD tablosundan ±0,5/1/1,5·ATR(H1), 8 s.
  3. Referans yarışı: aile içi en yakın üst/alt seviye (0,05–3 ATR), 8 s.
  4. Değdikten sonra: ilk değişten itibaren seviyeden ±0,5 ATR, 4 s (kırılım / ret).
- **İlk-geçiş tabloları** `FU/FD [N × 60]`: her noktada 0,05…3,00 ATR(H1) uzaklıktaki seviyeye ilk değme dakikası. Gerçek seviye,
  hayalet seviye ve simetrik yarış aynı tablodan okunur (uzaklık 0,05 ATR yukarı yuvarlanır) → gerçek ve hayalet arasındaki tek fark
  seviyenin "gerçek" olmasıdır.
- **Sıfırlar her etiketin yanında:** analitik `p0 = D/(U+D)`; hayalet `p_hay` (aynı yarıyıl × NY saati × H1 ATR-oranı ondalığı
  kovasındaki BAŞKA günlerin aynı uzaklıktaki sonucu — aynı gün komşuları yolu paylaştığı için dışlandı); eşlenmiş taban (durumlar
  için kova ortalaması); martingal piyasa (10 sentetik yol: 30 dk bloklar aynı yarım-saat dilimi × yarıyıl içinde günler arası
  karıştırıldı, bar şekli korundu; tüm hesaplar baştan).
- Aynı-bar belirsizliği (iki seviyeye aynı dakikada değme) yarışlardan çıkarıldı; çözülme oranı tablolarda (`cozulme`).
