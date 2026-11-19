# CS / AR / VM — çapraz varlık şokları, rejime göre sert gün, oynaklık-yönetimli NASDAQ tutuşu

Ön kayıt: 2026-11-18, sonuçlara bakılmadan. Defter: tek başına petrol/altın/dolar/faiz şoku → NDX yok (DB-05 bunları C3b kapısı olarak,
FK faiz × korku olarak sınadı); ayı rallisi günü / boğa düşüş günü ayrımı yok (YK ayıda son saat rallisi C+); oynaklık-yönetimli
NX-05 yalnız canlı kural kitabında (X), NDX al-tut üstünde değil.
Hedef QQQ (temettü düzeltmeli), eş SPY, bağımsız ^NDX 1985–1999. Olay = tetik günü kapanışı giriş, tutuşta yeni giriş yok; plasebo
aynı yıl rastgele başlangıç (§3-43). Maliyet 2 bp + uzunda `FIN_BP_PER_DAY`. KEŞİF → 2021-10, TEST 2021-11 →.
Hüküm: KEŞİF yönünde TEST yüzdelik ≥ 1 − 0,10/k (k = hücre sayısı) ve eş aynı yön → B; TEST ≥ 0,90 → C+; aksi X.

## CS-01 — çapraz varlık şoku (yfinance CL=F, GC=F 2000+; DX-Y.NYB, ^TNX 1985+)
Şok günleri: petrol ≥ +%4 / ≤ −%4, altın ≥ +%2 / ≤ −%2, dolar ≥ +%1 / ≤ −%1, 10 yıl getirisi Δ ≥ +10 bp / ≤ −10 bp.
8 şok × h ∈ {1, 5} = 16 hücre; yön KEŞİF'te seçilir. Bağımsız: SPY; dolar ve faiz için ^NDX 1985–1999.

## AR-01 — rejime göre sert gün (yön ön kayıtlı)
AR1: kapanış < SMA200 ∧ gün ≥ +%2 (ayı rallisi) → SAT. AR2: kapanış > SMA200 ∧ gün ≤ −%2 (boğada sert düşüş) → AL. h ∈ {1, 5}
(4 hücre). Bağımsız ^NDX 1985–1999 ve SPY.

## VM-01 — oynaklık-yönetimli NASDAQ tutuşu (Moreira–Muir 2017)
w_t = c / RV20_{t−1}² (c tüm dönem ortalama w = 1 olacak biçimde değil, **nedensel**: son 252 g RV20² ortalamasıyla ölçekli,
w = mean252(RV20²) / RV20²), tavan 2, taban 0. Getiri w_{t} × r_t − 2 bp × |Δw| − uzunda finansman (w × FIN). Kıyas al-tut ve
1/RV20 sürümü. Ölçü yıllık getiri, Sharpe, maxDD, onyıl dilimleri (1990'lar, 2000'ler, 2010'lar, 2020–21-10, TEST). Geçme:
Sharpe al-tutun üstünde dilimlerin ≥ 4/5'inde (TEST dahil) ve QQQ + ^NDX + SPY'de → B; TEST'te üstünde ve dilimlerin ≥ 3/5 → C+.
