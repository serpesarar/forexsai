# Korku gecesi paketini genişletmek: yeni evren (sektör/sanayi ETF, mega-cap hisse) + eşik gevşetme — ÖN KAYIT (2026-11-19, sonuçlardan önce)

## Kullanıcı isteği
"Aynı mantıkla daha derin araştır, daha fazla işlem bul; şu an işlem sayımız az." Paket: K1 + OPEX vetosu + XP (NDX'te yılda ≈ 24 işlem).
**Amaç işlem sayısı değil, aynı kalitede EK işlem:** yeni işlemin kendi beklentisi > 0, mevcut paketle aynı güne düşmeyen ("yeni gün") işlemler
ayrıca sayılır, portföy Sharpe'ı düşmemeli.

## Defter kontrolü (3. KURAL)
- K1 ABD endekslerinde B+ (GI-02), Avrupa/Japonya kendi kapanışında 0/5 (GN-06), endeks sepeti X (GN-04: aynı geceler, ρ 0,86–0,96),
  ikinci birim ekleme X (KC-03), K3 B (KG-03, K1 ile 178/250 ortak), K1 %1,0 C+ (KG-04), günlük vekil V1 1993–2017 sağlam (UD-01).
  Olay günü korkusu dönmüyor (ZA-04/UD-03 B). **Sektör ETF'leri ve tek hisseler hiç sınanmadı.** Eşik gevşetme ve K1 ∪ K3 paket (OPEX+XP)
  içinde marjinal işlem kalitesi olarak ölçülmedi.

## Eksen A — yeni evren (günlük vekil, yfinance düzeltilmiş OHLC)
- **Evren (sonuçtan önce sabit):**
  - Sektör SPDR: XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLU (1999+).
  - Sanayi/stil ETF: SMH, IBB, XBI, KRE, XHB, XRT, MDY, RSP.
  - Mega-cap hisse (2026 ilk 20'den uzun geçmişli olanlar): AAPL, MSFT, NVDA, AMZN, GOOGL, META, AVGO, TSLA, JPM, V, WMT, XOM, UNH, JNJ, PG,
    HD, COST, ORCL, NFLX, AMD.
- **Sinyal:** V1(d) = kapanış ≤ (yüksek + düşük)/2 × 0,995 ∧ kapanış < açılış (UD-01 ile aynı). OPEX vetosu (vadeye 0–2 işlem günü).
  XP çıkışı (ilk yükselen kapanış, en geç 5. gün). Maliyet: ETF 2 bp, hisse 5 bp; + finansman (lib.FIN_BP_PER_DAY).
- **Taban (E116):** aynı enstrümanda V1 olmayan günlere aynı XP çıkışıyla girilse elde edilecek ortalama. **Fark = paket − taban.**
- **Dönemler:** KEŞİF başlangıç → 2017-12-31; TEST 2018-01-01 → 2026-11-05 (ileri gölge dönemine dokunulmaz).
- **Alt kümeler (ön kayıtlı, iki tane):**
  1. **Endeksle birlikte:** aynı gün QQQ veya SPY de V1.
  2. **Yeni gün (tek başına):** QQQ ve SPY V1 değil. İşlem sayısını gerçekten artıran kısım bu.
  Yeni gün içinde **haber vekili:** açılış boşluğu ≤ −%2 (büyük olasılıkla bilanço/haber; ilke: haberli düşüş dönmez) vs değil.
- **Geçme (enstrüman grubu = sektör, sanayi/stil, hisse):**
  - Grup havuzunda TEST fark > 0 ve gün bloklu bootstrap P ≥ 0,95; KEŞİF'te de fark > 0.
  - Enstrümanların ≥ %65'inde TEST fark > 0.
  - Alt küme için aynı ölçüt ayrı ayrı. "Yeni gün ∧ haber vekili yok" grubu B olursa işlem artırıcı aday.
- **Portföy:** geçen gruplar için yılda işlem ve **yeni gün** sayısı; NDX paketiyle günlük P&L korelasyonu; eşit riskli birleşik Sharpe ve maksimum düşüş
  (2018–26). Birleşik Sharpe NDX tek başına olandan düşükse "işlem artar ama portföy kötüleşir" → kabul yok.

## Eksen B — eşik gevşetme / birleşim (NDX gün içi, MT5 4 endeks + Duka, mevcut K1 + XP motoru)
- Hücreler (3): K1 TWAP eşiği −%0,4 ve −%0,3 (son saat < 0 aynen); K1 ∪ K3 (K3: 15:00→16:00 ≤ −%0,3). Hepsi OPEX vetolu, XP çıkışlı.
- Ölçülen yalnız **marjinal işlemler** (mevcut K1'de olmayan): ortalama net, isabet, en kötü.
- **Geçme:** marjinal ortalama > 0 hem KEŞİF (≤ 2021-10) hem TEST'te, 4 MT5'in ≥ 3'ünde + Duka TEST'te > 0; Bonferroni 3 hücre (P ≥ 0,983);
  ve birleşik paket Sharpe'ı (yıllık) K1 paketinden düşük değil.

## Genel
- Canlıya bağlama yok. B çıkan eksen için ayrı adımda kutuda sembol kontrolü (salt okuma) ve 2. KURAL kartı.
- Toplam hücre: A'da 3 grup × 3 alt küme (tümü / yeni gün / yeni gün ∧ habersiz) = 9 ana hücre; B'de 3. Sonradan bakılan EK olarak işaretlenir.

## EK-1 (A ve B sonuçlarından SONRA; hüküm değiştirmez, yalnız betimleme)
- A'da portföy ilk koşuda eşit nominalle hesaplandı; ön kayıt "eşit risk" diyordu → düzeltildi (bacak σ'sı NDX paketine eşitlenir),
  iki sürüm de raporlanır.
- **Doz eğrisi (betimleyici):** K1 + OPEX + XP içinde TWAP uzaklığı kovaları (−∞,−50], (−50,−40], (−40,−30], (−30,−20], (−20,−10], (−10,0]
  bp (son saat < 0 aynen); her kovanın KEŞİF/TEST ortalaması, 4 MT5 + Duka. T30'un ötesine geçme kararı buradan VERİLMEZ; ancak ileri gölge
  etiketiyle ve yeni ön kayıtla.
