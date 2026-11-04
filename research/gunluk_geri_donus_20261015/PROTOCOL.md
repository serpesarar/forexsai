# Ön-kayıt — Günlük endeks geri dönüşü (negatif seri bağımlılık) — GR-01

> 2026-10-15, sonuç hesaplanmadan yazıldı. Kullanıcı isteği: "günlük endeks geri dönüşünü test et".
> Literatür: Baltussen, van Bekkum & Da (2019, JFE 132) — 2000'lerden beri büyük endekslerde günlük getiriler negatif
> otokorelasyonlu; MAC(5)'e karşı strateji S&P 500'de yıllık Sharpe ≈ 0,67 (2 Mart 1999 sonrası); vadelilerde maliyet
> sonrası kâr şüpheli. Yerel önceki: GF-05 ("dünkü getiri" 34 koşulun içinde, tek başına kenar yok), GF-10/12/16
> (stres sonrası düşüş döner, coşku sonrası yükseliş dönmez — CAPREV). Bu test yeni olarak: yayımlanmış sürekli sinyal,
> otokorelasyon rejim koşulu, simetrik/asimetrik ayrıştırma, bağımsız piyasa (DAX).

## Veri
- NDX nakit endeks günlük kapanışları (`research/ndx_gate_forge/data/macro_daily_patched.csv`, `NDXCASH_close`,
  tamamlanmış kapanış, E20) 2015-01-02 → 2026-09-30. İkincil teyit: `SPX_close` (aynı dosya; makalenin piyasası, NDX'ten
  bağımsız değil). Bağımsız piyasa: DAX CFD, 1h'ten NY 17:00 sınırlı günlük (`research/mum_eslestirme_20261012/kaldirma_testi.py`
  `load_tf("DAX","1d")`, 2020-01 →).
- r_t = ln(C_t / C_{t−1}) (kapanıştan kapanışa). İşlem: t kapanışında karar, t+1 kapanışında çıkış (r_{t+1}).

## Stratejiler (pozisyon_{t+1})
- **S1 (birincil):** −sign(r_t).
- S2: −sign(s_t), s_t = Σ_{k=1..5} w_k · r_{t−k+1}, w = (5,4,3,2,1)/15.
- S3: S2 yalnız ρ̄_t < 0 iken (ρ̄ = son 250 günün ρ1..ρ5 otokorelasyonlarının aynı w ile ağırlıklı ortalaması, yalnız t'ye
  kadarki veri); değilse pozisyon yok.
- Ayrıştırma (tanımlayıcı): S1'in uzun bacağı (düşüş sonrası al) ve kısa bacağı (yükseliş sonrası sat) ayrı; kıyas = aynı
  günlerdeki "hep uzun" getirisi.
- Taban: hep uzun (sürüklenme); ayrıca eğim β: r_{t+1} = a + β r_t (β < 0 beklenir).

## Maliyet (NAS100 CFD, 1 lot = 1 $/puan)
- Her pozisyon değişiminde 1,5 puan spread; her tutulan gece için 5 puan finansman (uzun ve kısa için temkinli aynı; Cuma
  ×3). Puan maliyeti o günün NDX seviyesine bölünerek getiriye çevrilir. Brüt ve net ayrı raporlanır.

## Bölümler
- **Geliştirme:** 2015-01-02 → 2025-11-30 (NDX, SPX).
- **Doğrulama (bir kez):** 2025-12-01 → 2026-09-30 (NDX; ~210 gün → düşük güç, en küçük saptanabilir etki raporlanır).
  Bu dönem başka hipotezler (ME-07 gece, GM-01 gamma) için açıldı; günlük geri dönüş orada sınanmadı.
- **Bağımsız piyasa:** DAX 2020-01 → son (hiç sınanmadı).

## Geçme ölçütleri (S1, NDX geliştirme)
- Brüt ortalama günlük getiri > 0, 5 günlük blok bootstrap (B = 10.000) tek yönlü P ≥ 0,975; iki kronolojik yarıda
  (2015–2020 / 2021–2025-11) > 0; yıllık Sharpe ≥ 0,3; β < 0 (P ≥ 0,975).
- **Net** (maliyet sonrası) ortalama > 0 ayrıca raporlanır; işlem stratejisi iddiası için o da > 0 olmalı.
- Geçerse: doğrulamada aynı işaret + bağımsız piyasada (DAX) aynı işaret P ≥ 0,90 → B sınıfı. S2/S3 ve ayrıştırma ikincil.
