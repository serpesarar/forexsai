# Canlı kurallar — lot seviyeleri ve açılış duyurusu

Kullanıcı kararı **2026-11-08**: bulunan pozitif kuralların hepsi kendi lot seviyesiyle (demo hesapta) canlıya bağlandı.
Bir kural işlem açtığında bot ekrana (konsol log'u + `demo_bot.log`) kuralın adını ve geçmiş başarısını yazar:

```
╔══ SİNYAL AÇILDI ═══ C3b — NDX RSI2 geri dönüşü
║ GEÇMİŞ BAŞARI: isabet %78,1 (n 155) · ort +65 bp/işlem · sınıf A
║ SL: ... · TP: ... · tutuş: ... · sıklık: ...
║ NAS100 BUY 2.0 lot @ ... · acil SL ... · ticket ...
╚══ go_live_cards/ndx_c3b_rsi2_upexit.json (...)
```

Tanımlar tek yerde: `yeni deneme/kural_katalogu.py` (`RULES`). Olaylar `kural_canli_olaylar.jsonl` dosyasına da yazılır.

| Kural | Magic | Lot (varsayılan) | config anahtarı | Geçmiş isabet | Ort. getiri | SL | TP / çıkış | Sıklık | Sınıf |
|---|---|---|---|---|---|---|---|---|---|
| **C3b** NDX RSI2 geri dönüşü | +8 | **2.0** | `C3B_LIVE_LOT`, `C3B_LIVE` | %78,1 (n 155) | +65 bp | yok (acil SL %10) | ilk yükselen 15:30 ET fiyatı, en çok 5 gün | ≈1,2/ay | A |
| **CAPREV** kapitülasyon alımı (NDX+DAX) | +7 | **1.0** | `CAPREV_LIVE_LOT`, `CAPREV_LIVE` | %55,3 (n 161) | +0,22R | 1× günlük oynaklık | seans kapanışı | ≈1,3/ay | B+ |
| **ORB × VIX** (NDX, VIX≥18,4) | +9 | **0.75** | `ORB_VIX_LIVE_LOT`, `ORB_VIX_LIVE` | %48,7 (n 152) | +0,295R | aralık ortası | 2R, 15:55 ET zaman çıkışı | ≈5/ay | B |
| **FR-15 teyitli çekiç** (NAS100 + GER40) | +10 | **0.5** (her endeks) | `CEKIC_LIVE_LOT`, `CEKIC_LIVE` | ≈%26–30 (FR-10 ölçümü) | ≈+0,07R | çekiç dibi | 5R, 24 sa, Cuma 16:45 NY çıkışı | ≈7–8/ay/endeks | B |
| **KSG kapanış saati gecesi** (NAS100) | +11 | **0.5** | `KSG_LIVE_LOT`, `KSG_LIVE` | %56,0 (n 1039) | +7,0 bp/gece net | yok (acil SL %6) | ertesi işlem günü 09:30 ET; giriş 16:00 ET, 15:00→16:00 getirisi < 0 ise | ≈10/ay | C+ |

**Lot mantığı:** kanıt sınıfı ve işlem yapısı. En güçlü kanıt (A, yüksek isabet, kısa tutuş) en büyük lotu alır; düşük isabetli,
komşu eşiklerde kırılgan, sık işlem açan FR-15 en küçüğü. Aynı sembolde bu ailelerin toplam açık lotu `RULE_MAX_LOTS_PER_SYMBOL`
(4.5) üstüne çıkamaz — hepsi "korkudan sonra endeks AL" olduğundan çöküş haftasında aynı anda zarar yazarlar.

**KSG (2026-11-10):** kullanıcı kararıyla gölge atlanıp doğrudan canlı. Sınıf C+: etki 2020'den beri (2018-19 eksi). Durdurma ölçütü: n=60 gecede ort. net < 0 → `KSG_LIVE = False`. Gece açıkken CAPREV/ORB kapalıdır; birlikte en çok C3b 2.0 + çekiç + KSG 0.5.

**Canlıya alınmayanlar:** K6 (C), K1 (C+, kör sınav geçmedi), FR-10 (FR-15 onun yerini aldı), C3 (C3b ile aynı giriş), tüm SAT kuralları.

**Kapatma:** kutuda `config.py` içine `C3B_LIVE = False` vb. yaz ve botu yeniden başlat. Lot değiştirmek için aynı yolla `*_LIVE_LOT`.

**Kod bağlantıları:** `c3b_live.py`, `orb_vix_live.py`, `cekic_live.py` (+ `caprev_live.py`), `forexsai_demo_bot.py` ana döngüsü
(çıkışlar frenden önce, girişler gölgelerden sonra), `_bot_magics()` (günlük zarar freni + global tavan yeni magic'leri sayar).
Test: `cd "yeni deneme" && python3 test_kural_canli.py`.

**Bilinen sınırlar:** ORB×VIX 2026'da zayıf (+0,10R); FR-15 isabeti ayrıca kayıtlı değil (ilk 100 işlemde ölçülecek);
C3b kartında stop yok, canlıdaki acil SL %10 örneklemde hiçbir işlemi değiştirmez; yeni kurallar geçmiş kanıtla canlıya alındı,
ileri dönem canlı karnesi gelene kadar "kanıtlanmış" sayılmaz. Durdurma ölçütü (önceden yazılı): kural n=60 işlemde ort. R<0 ise kapat.
