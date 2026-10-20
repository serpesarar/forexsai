# Ön-kayıt — Mum Benzerlik Tarayıcısı algoritma varyantları (ME-12)

2026-10-20, sonuç görülmeden. Taban motor (V0: oto-ölçekli OHLC RMS, k=20 çoğunluk oyu) karnede 40 hücrenin hiçbirinde
rastgele komşu / sürüklenme tabanını aşmadı. Kullanıcı motorun "gerçekten benzer olanı bulup geleceği" göstermesini
istiyor. Aynı sızıntısız düzenekte 4 varyant:

- V1: k=50 çoğunluk oyu (OHLC RMS)
- V2: k=50, benzerlik-ağırlıklı oy (w = exp(−rms/medyan_rms))
- V3: kapanış-çizgisi şekli (z-normalize, ME-08 ölçüsü), k=20 çoğunluk
- V4: V3 + V2 (kapanış şekli, k=50 ağırlıklı)

Sorgular: her sembol × TF × n∈{50,100}, arşivin son %30'u, 200 sorgu, ızgara karneden YARIM ADIM kaydırılmış (yeni
noktalar). Ufuk H = HORIZONS[tf][1]. Kütüphane yalnız sorgudan önce ufku bitmiş pencereler.

Geçme (varyant başına): 40 hücre birleşik isabet − birleşik max(rastgele komşu, hep-çoğunluk) > 1,96·SE (SE = 0,5/√N_toplam)
VE endeksler (NDX+DAX) ile emtia (XAU+USOIL) ayrı ayrı > 0. 4 varyant → Bonferroni z > 2,5. Geçen olmazsa motor
"bilgi amaçlı" kalır.
