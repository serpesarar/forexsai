# Ön-kayıt — IO-18 "NDX SELL düşüşü kovalama" sağlamlık turu (2026-10-10)

Sınanan iddia (IO-18, B−): botun NDX SELL'lerinde giriş anında **C1** = son kapanmış 1h barın kapanışı EMA50'nin ≥2 ATR
altında (SELL-işaretli `g60_ema50 ≥ 2`) veya **C2** = 1h RSI ≤ 35 ise SL oranı belirgin yüksek (C1 %59 vs %36, +16,0R).
IO-19 (ters BUY) döngüsel olduğu için ayrıca sınanmaz; burada yalnız veto iddiası.
Defter: GF-15 (kovalama endeksi C+, bota özgü), E22 (VIXREG geçmişte yeniden kurulamaz), IO-11/IO-17 (genel ayrım yok).

Koşullar ve eşikler SABİT (C1 ≥2 ATR, C2 RSI ≤35); duyarlılık ızgarası yalnız plato kontrolü içindir, seçim yapılmaz.

## Testler
A. Bot içi (237 NDX SELL karar): A1 gün-blok bootstrap (kurtarılan R ve SL farkı) · A2 ay-dışarıda · A3 aile (VIXREG/diğer)
   · A4 eşik platosu (1h EMA50 1,0–3,0 ATR; 1h RSI 30–45; aynı koşulun 5m/15m karşılığı) · A5 **seçim düzeltmeli
   maksimum istatistik**: ~100 özelliğin her biri × iki kuyruk × desil eşikleri (destek ≥25) içinde en büyük "kurtarılan R";
   boş dağılım = sonuç dizisinin özelliklere göre dairesel kaydırılması (1.000 kez, kayma ≥10 işlem). p < 0,05 → madencilik
   gürültüsünü aşıyor.
B. **Yeni olaylar — botun engellenen NDX SELL sinyalleri** (kutu `gate_skipped.jsonl`, 07-28 → 10-10; "shadow" nedenli
   satırlar hariç çünkü onlar yine de açıldı; 30 dk'da bir; gerçek bot girişinin ±15 dk'sı hariç).
C. Panel modellerinin NDX SELL sinyalleri (pulse1/2/3, ml:main, meta, smc; model başına 30 dk'da bir), 06-15 → 10-09.
D. Decider NDX SELL kararları (OPEN + WAIT, yön SELL), 06-30 → 10-08.
E. **Aynı dönem sinyalsiz piyasa** (06-15 → 10-09, hafta içi 06–20 UTC saat başı SELL) — kritik kontrol: etki bu dönemin
   piyasasına mı ait?
F. Fark-içinde-fark: bot C1 etkisi − aynı dönem piyasa C1 etkisi (gün-blok bootstrap).

B–E simülasyonu: giriş sinyalden SONRAKİ 1m açılışı (E7), spread 1,5 puan, **G1 (birincil)** risk = fiyat × %0,373,
RR 0,73 (botun NDX medyanı; sl_ortak sentetiğiyle aynı) · G2 (yan) risk = 0,84 × ATR1h (botun medyan geo_sl_atr1h), RR 0,73.
Aynı barda iki bariyer → SL. Ölçü: SL oranı farkı (C − değil) ve ort R farkı, gün-blok %95.

## Geçme
- **Güçlendi (bota/sinyale özgü):** B'de C1 SL farkı > 0 ve gün-blok %95 alt sınırı > 0 (C2 aynı yönde) VE E'de etki
  belirgin küçük (F'nin alt sınırı > 0) VE A5 p < 0,05.
- **Dönem etkisi:** E'de de benzer pozitif fark → veto bu piyasa rejimine bağlı, sağlam değil (B− → C).
- **Zayıfladı:** B'de fark ≤ 0 veya A5 p ≥ 0,10.
Her durumda yalnız GÖLGE aday (2. KURAL); bot koduna dokunulmaz.
