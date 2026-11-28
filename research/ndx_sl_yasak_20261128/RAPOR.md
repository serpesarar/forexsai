# SY — NASDAQ'ta SL olan işlem tipleri: bul ve yasakla (2026-11-28)

**Hüküm:** Yasaklanabilecek yeni bir SL tipi yok. Kanıtın tanıdığı tek düzey aile/yön düzeyi. Orada da kanayan aileler
(MOMSR BUY, CHREV BUY, VIXREG SELL) zaten Temmuz–Ekim arasında fiilen işlem açmayı bıraktı. Ön kayıtlı 5 işlem-tipi bayrağı ile
4 makro olay bayrağının hiçbiri çıtayı geçmedi. Canlı kitapta "SL engelle" ile "TP kaybet" yine birlikte hareket ediyor
(korelasyon **0,98**; SL-06'da 0,996). Bu, SL'nin girişte tanınmadığının bu projedeki üçüncü bağımsız teyidi
(IO-11 → IO-26 → SL-06 → SY).

## 1. Defterden bilinenler (tekrar edilmedi)
IO-11 (4.104 veto genelleşmiyor) · IO-18/20/26 (kovalama, RSI diverjansı ileride tersine döndü) · SL-01…06 (DC/RE 9 yıl, 41 aday,
SL-engel ↔ TP-kayıp korelasyonu 0,996) · SL-08 (SL'yi tanımıyor, oynaklığa göre braket gürültü SL'sini azaltıyor → CANLI) ·
IO-29 Y2 (zarardaki pozisyona ekleme, C, gölgede) · CK-01 (VIXREG +0,010R → SHADOW).

## 2. A — Aile/yön karnesi (canlı NDX, bot_trades 06-30 → 11-26, 452 karar, hizalama kesin %95)
| aile·yön | n | WR | SL % | ort R | P(EV<0) | ÖN R | İLERİ (≥10-10) R | net $ | son işlem |
|---|---|---|---|---|---|---|---|---|---|
| DAYCOMBO BUY | 48 | 70,8 | 29,2 | **+0,222** | 0,04 | +0,281 | +0,114 (17) | +12.266 | 11-26 |
| REENTRY BUY | 23 | | 21,7 | **+0,347** | | +0,516 | +0,238 (14) | +20.496 | 11-11 |
| REENTRY SELL | 14 | | 14,3 | +0,481 | | | | +6.100 | 11-12 |
| DECIDER SELL | 100 | 65,0 | 35,0 | +0,084 | 0,11 | +0,042 | +0,088 (92) | +39 (≤0,03 lot) | 11-19 |
| VIXREG SELL | 210 | 56,2 | 43,3 | +0,003 | 0,47 | −0,000 | +0,166 (4) | +450 (risk 112.663 $) | 11-12 |
| MOMSR BUY | 21 | | 38,1 | −0,040 | | | — | +382 | **07-31** |
| CHREV BUY | 13 | | 46,2 | −0,071 | | | — | −506 | **07-15** |

Ön kayıtlı yasak ölçütünü (ort R<0, P(EV<0)≥%80, iki dönem ≤0, $<0) **hiçbir aile tutmadı**. Eksi olan iki aile n<30 ve zaten
işlem açmıyor. VIXREG SELL 112 bin $ risk taşıyıp +450 $ kazandı. Kenarı yok, ama 10-10'dan beri gate'ler yüzünden 4 işlem açtı.
Kâr payı DAYCOMBO + REENTRY'den geliyor (+38.862 $, NDX netinin tamamından fazla).

## 3. B — Ön kayıtlı işlem-tipi bayrakları (aile tabakalı Δ, gün-blok bootstrap, plasebo ×1000, Holm)
| bayrak | n | Δ R | ÖN / İLERİ / İLERİ-2 Δ | SL engel % | TP kayıp % | P(Δ<0) | plasebo yüzdelik | Holm | hüküm |
|---|---|---|---|---|---|---|---|---|---|
| B1 dar stop NR<0,5 | 47 | **+0,246** | +0,34 / +0,13 / +0,31 | 8,3 | 11,9 | 0,04 | 0,98 | 0,97 | X (TERS: dar stoplu işlemler daha iyi) |
| B2 Y2 zarardaki pozisyona ekleme | 23 | **−0,352** | −0,25 / −0,76 / −0,65 | 7,7 | 3,6 | 0,92 | **0,025** | 0,39 | C (ölçüt dışı, bkz. §3.1) |
| B3 Y1 aynı yönde açık pozisyon | 40 | −0,072 | −0,13 / +0,20 / +0,35 | 8,9 | 8,6 | 0,61 | 0,28 | 1,00 | X |
| B4 günde ≥2 SL'den sonra | 181 | +0,084 | +0,14 / −0,18 / −0,20 | 41,7 | 39,9 | 0,17 | 0,82 | 1,00 | X (SL-02 teyidi) |
| B5 kovalama ≥1,5 ATR5 / 60 dk | 139 | −0,098 | −0,10 / −0,18 / −0,16 | 32,7 | 29,9 | 0,87 | 0,15 | 0,51 | X (SL-engel − TP-kayıp 2,8 puan) |

### 3.1 Y2 neden yasaklanmıyor
23 olayın 18'i Temmuz–Eylül'de CHREV SELL ile VIXREG SELL'in aynı fikri birkaç dakika arayla açmasından geliyor. İki aile de
artık işlem açmıyor. Kalan 5 olayın 3'ü DAYCOMBO (2 SL / 1 TP). IO-21'de DAYCOMBO'nun 315 işlemlik geçmişinde "üst üste açılan"
işlemler **+0,198R** çıkmıştı (ters yön). Kutudaki gölge karnede (`yigilma_shadow.py --karne`) 11-12'den beri **0 Y2 olayı** var.
Etki sıfırdan farklı olabilir ama ileriye taşıyan popülasyon kalmadı. Hüküm C, gölge sürüyor, n ≥ 100'de yeniden ölçülecek.

## 4. EK-1 — Makro olay günü, DAYCOMBO + REENTRY 9 yıl (TD-01 tabanı, 3.517 işlem, taban +0,034R / SL %39,9)
| bayrak | n (gün) | ort R | SL % | P(ortR<0) | plasebo yüzdelik | çağlar 18-20 / 21-23 / 24-26 | hüküm |
|---|---|---|---|---|---|---|---|
| E1 FOMC günü | 204 (39) | **+0,081** | 37,3 | 0,09 | 0,58 | +0,17 / +0,02 / +0,09 | X (TERS: FOMC günü daha iyi) |
| E2 FOMC −120…+60 dk | 108 (35) | +0,101 | 36,1 | 0,10 | 0,66 | +0,04 / +0,10 / +0,16 | X |
| E3 CPI/NFP günü | 241 (56) | −0,024 | 43,2 | 0,66 | 0,19 | +0,02 / **−0,13** / +0,06 | X (tek çağ eksi) |
| E4 herhangi | 431 (92) | +0,021 | 40,6 | 0,33 | 0,27 | +0,09 / −0,06 / +0,07 | X |

## 5. Kullanıcının ölçüsü
Bu oturumdaki 5 bayrağın (SL-engel %, TP-kayıp %) noktaları arasında korelasyon **0,98**. En iyi fark 4 puan (Y2). SL'lerin %60'ını
engelleyen bir kural, TP'lerin de ≈ %60'ını kesiyor. Bu stratejilerde SL bir "giriş tipi" değil, braketin gürültü içindeki sonucu.

## 6. Kâr marjını gerçekten ne yükseltti (defterde kanıtlı, zaten uygulanmış)
1. Aile/yön düzeyinde kesme: MOMSR/CHREV NDX BUY, XAU intraday, USOIL BREAKOUT, decider XAU BUY (OK-01) → kanayan aileler kapalı.
2. Oynaklığa göre braket + eşit $ risk (SL-08, B, CANLI): gürültü SL'lerini azaltıyor, SL'yi "tanımadan".
3. Lot = risk: en kötü 5 gün NDX netinin %81'i (MA-03/05). Kâr marjı girişte değil, lot ve braket tarafında.

## 7. Açık kalan
- Y2 gölgesi (n ≥ 100). VIXREG SELL: kenarsız ve 112 bin $ risk taşıyor. Gate'ler onu fiilen susturdu. Tamamen kapatmak (config
  `VIX_REGIME` kapalı) risk azaltır, beklenen $ etkisi ≈ 0. Bu kullanıcı kararı.

Kod: `src/sy.py` (A+B), `src/ek1_olay.py` (EK-1). Sonuçlar: `results/sonuc.json`, `results/ek1_olay.json`, `results/kararlar.parquet`.

## 8. Uygulanan yasak (2026-11-28, kullanıcı hedefi "SL tiplerini yasakla") — defter B22
Kanıtın tanıdığı tek düzey aile×yön olduğundan yasak o düzeyde kondu: **NDX MOMSR BUY, CHREV BUY, VIXREG SELL** artık açılmaz.
Bu üç tip canlı kitapta 244 karar üretti, SL oranı %38–46, toplam +327 $ (risk 132.897 $, SL %43). Kârın tamamını taşıyan DAYCOMBO /
REENTRY / DECIDER / zaman çıkışlı kurallar etkilenmez. Beklenen $ etkisi ≈ 0 (bu ailelerde kenar yok); kazanç = SL sayısı ve $
salınımı (133 bin $ risk) kalkar, risk bütçesi kanıtlı ailelere kalır.
- Kod: `yeni deneme/phase_rules.py` (`SL_TYPE_BAN*`, `sl_type_banned`), `forexsai_demo_bot.py` (`_sl_type_ban_blocks`:
  `_route_open` başı, CHREV giriş öncesi, VIXREG giriş öncesi), test `test_sl_type_ban.py`.
- Ölçüm: engellenen her giriş `gate_skipped.jsonl` → reason `sl_type_ban` (fiyat, aile). Yasağın bedeli `research/gate_audit.py` ile.
- Geri alma: kutu config `SL_TYPE_BAN_BLOCK = False` (gölge) / `SL_TYPE_BAN_ENABLED = False`; liste `SL_TYPE_BAN` ile değişir.
- Yeniden değerlendirme: engellenen ≥ 60 giriş biriktiğinde sanal ort R > +0,05 ve iki yarı > 0 ise ilgili tip listeden çıkarılır.

### 8.1 Geriye dönük etki (aynı canlı kitap, 06-30 → 11-26; örneklem içi, ileri ölçüm B22 karnesinde)
| | karar | SL | net $ | risk $ | **net/risk (kâr marjı)** | ort R | WR | maks. düşüş | en kötü gün | günlük SR |
|---|---|---|---|---|---|---|---|---|---|---|
| mevcut | 452 | 168 | +40.964 | 308.773 | %13,3 | +0,076 | %61,5 | −18.092 | −8.628 | 0,167 |
| yasakla | 208 | **63** | +40.638 | 175.876 | **%23,1** | **+0,171** | %69,2 | −18.892 | −8.628 | 0,189 |
SL sayısı −%63, kâr marjı ×1,74, net $ ≈ aynı (−326 $). Maks. düşüş ve en kötü gün değişmiyor (DAYCOMBO/REENTRY 30 lot günleri).
Aynı risk bütçesi kanıtlı ailelere kalırsa beklenen kâr artışı buradan gelir; bu ayrıca lot kararıdır, otomatik yapılmadı.
