# Sonuç — Decider XAUUSD işlemleri: SL/TP derin analizi, ileri sınama ve erken kesme kuralı (2026-10-21)

Ön-kayıt: [PROTOCOL_ILERI.md](PROTOCOL_ILERI.md) (+ `erken_kes_saglamlik.py` başlığı). Otopsi: `output/islem_otopsi/2026-10-20_2348_xau_decider/`.
Veri: `decider_xau_tpsl_20261015` pipeline'ı birebir kopyalanıp 2026-10-20'ye tazelendi (journal OPEN 887, icra 94/94).

## 1. Gerçek icralar (94, hepsi BUY; son 2 hafta 79)
| | n | WR | başabaş | ortR | net |
|---|---|---|---|---|---|
| tümü | 94 | %63,8 | %60 | +0,06 [−0,10…+0,22] | +41 $ |
| son 14 gün | 79 | %63,3 | %60 | +0,05 | +39 $ |
- **Giriş zamanlaması rastgeleden iyi:** aynı geometride ±10 gün rastgele girişe göre +0,16R/işlem (P %95). Decider doğru anı
  seçiyor; sorun braketin maliyeti (rastgele giriş −0,10R).
- **SL'lerin yapısı (34):** %50'si "yön doğru" (stoptan sonra TP seviyesine gitti; yaşatacak stop medyan 1,70R), %56'sı ilk 10 dk'da,
  %32'si hiç çalışmadı. Ama stopu/TP'yi değiştirmek kurtarmıyor (§11 geometri tablosu ve DX-01: aynı riskte hiçbir SL/TP
  çarpanı belirgin iyi değil).
- **Ayrışma 5. dakikada:** SL'ye gidecek işlemler 5. dk'da belirgin geride (AUC 0,81).
- Giriş bayrakları (karar anı) SL'yi açıklamıyor; `KOVALAMA` (SL %18 vs %36, n=17) DX-02 R1 ailesinde.

## 2. DX-02 kurallarının ileri sınaması (≥10-15; 68 karar / 4 gün) — `results/ileri.md`
Önceden kayıtlı tek B adayı **R1 (güç tetiği) tutmadı:** G1 −0,086 vs kural-dışı −0,078; G2 −0,054 vs −0,279 (P 0,75), ortR negatif.
İleri dönemin tamamı negatif (G1 −0,08, G2 −0,18) ve yalnız 4 gün → giriş kuralları için hüküm: kenar yok (DX-02 ile tutarlı).

## 3. Yeni kural: ERKEN KESME — 5. dakikada R ≤ −0,5 ise kapat — `results/yol_adaylari.md`, `erken_kes_saglamlik.md`
| küme | n | fark (R/işlem) | P(fark>0) | yarılar |
|---|---|---|---|---|
| gölge kararlar (icra edilmemiş, keşfe katılmadı) | 566 | +0,013 | %97,9 | +0,002 / +0,024 |
| ileri ≥10-15 | 68 | +0,037 | %99,7 | −0,017 / +0,091 |
| tümü (BUY) | 660 | +0,014 | %98,3 | +0,006 / +0,022 |
| gerçekçi çıkış (sonraki bar açılışı) | 660 | +0,013 | %97,5 | +0,005 / +0,021 |
| spread ×1,5 | 660 | +0,011 | %92 | −0,002 / +0,024 |
- **Plato:** dakika {3,5,7,10,15} × eşik {−0,3…−0,7} → 25 hücrenin 24'ü ≥ 0 (en güçlü 7–10 dk / −0,3…−0,4).
- **Plasebo:** aynı kural rastgele günlerdeki girişlerde medyan +0,002 → gerçek kazanç plaseboların %93'ünden büyük: kural
  decider'ın SL'ye gidecek girişlerini erken yakalıyor, braketin genel bir özelliği değil.
- **SELL'e taşınmıyor** (n=82, tutarsız) — decider XAU canlıda yalnız BUY.
- **Sınır:** kural uygulanmış decider XAU BUY ortR +0,003 (P %55) — iyileştirir, tek başına kârlı yapmaz. Kart ölçüt-2 (beklenti)
  bu yüzden geçmez; kural bir **yönetim iyileştirmesi** olarak değerlendirilmeli.
- M9 ile fark: M9 (bot, "kâra geçince BE/kilit") kazananları öldürüyordu; bu kural yalnız erken ve belirgin zarardaki işlemi keser
  (5. dk'da −0,5R'deki 11 SL'ye karşı yalnız 2 TP).

## Hüküm
Giriş tarafında kanıtlı kural yok (R1 ileride düştü). **Yönetim tarafında bir kural geçti: 5 dk / −0,5R erken kesme (B sınıfı,
küçük ama tutarlı +0,013R/işlem).** Canlıya bağlamak decider'ın pozisyon izleyicisine kod demektir → kullanıcı kararı.
