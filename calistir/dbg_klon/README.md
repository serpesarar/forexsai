# DBG klon ızgarası: denemeye hazır paket (GÖLGE varsayılan)

DBG 303733 hesabındaki botun C3 kurallarının (M3, taban × 1,1, TP ortalama ± 5 $, adım tablosu, UTC pencereleri) çalışan kopyası.
**2026-10-30: kutuda GÖLGE modda çalıştırıldı** (kullanıcı kararı). Başlatıcı `calistir/19_dbg_klon_golge.bat`; kaynak kopya ve testler `research/dbg_xau_tersine_20261029/paket_klon/`.

> Önce okuyun: geri testte bu ızgaranın **kenarı yok**.
> - Zarar kesicisi takılınca beklenti spread'siz ≈ 0, spread'le negatif.
> - Kesicisiz hâli, 0,01 standart lotla bile 16 ayı atlatmak için ~2M $ sermaye istiyor.
> - 10.000 $ hesap: 1:100 kaldıraçta, rastgele başlangıçların %89'unda ilk ay içinde stop-out.
>
> Ayrıntı: `research/dbg_xau_tersine_20261029/RAPOR.md` §13–§18. Gölge çalıştırmanın amacı para kazanmak değil, icra mekaniğini (bar açılışı dolumu, spread, TP dolumu) ölçmek.

## Dosyalar

| dosya | iş |
|---|---|
| `klon_kurallar.py` | Saf karar çekirdeği: adım tablosu, lot, UTC pencereleri, `decide_side`. Geri test motoru (`../klon_motor.py`) da bunu kullanır. |
| `klon_yonetici.py` | Olay güdümlü sepet yöneticisi. `on_bar` taze giriş/ekleme yapar, `on_tick` kesici ve TP'yi işler. MT5'ten bağımsızdır. |
| `dbg_klon_runner.py` | MT5 koşucusu. Varsayılan GÖLGE: sanal dolum + JSONL log, `order_send` hiç çağrılmaz. |
| `test_klon_paket.py` | 6 test: tersine mühendislik kurallarıyla eşitlik, kesiciler, UTC penceresi, **yönetici = geri test motoru** (Haziran 2026, olay olay aynı), gölgede sıfır emir. |

Testleri çalıştırma (proje kökünden):
```bash
DBG_M1_CLEAN=<m1_clean.parquet yolu> .venv/bin/python -m pytest research/dbg_xau_tersine_20261029/paket_klon/test_klon_paket.py -q
```
Son koşu: `6 passed`.

## Emniyet bayrakları (varsayılanlar 10k $ demo için)

| bayrak | varsayılan | ne yapar |
|---|---|---|
| `--taban` / `--carpan` / `--tp` | 0,01 / 1,1 / 5,0 | Klon ayarı. DBG'nin tabanı 0,05 **cent** lot = 0,0005 standart lot; 0,01 standart lot onun 20 katı. |
| `--max-seviye` | 30 | Tavanda yeni ekleme yapılmaz. Sepet TP'yi bekler, zarar büyümeye devam edebilir. |
| `--max-sepet-zarar` | 1000 USD | Sepet yüzen zararı bunu aşınca sepet piyasadan kapatılır. |
| `--max-toplam-zarar` | 2500 USD | İki sepetin toplam yüzen zararı aşılırsa hepsi kapanır ve koşucu durur. |
| `--min-marjin-seviyesi` | %300 | Hesabın marjin seviyesi altına inerse yeni giriş ve ekleme yapılmaz. |
| `DBG_KLON_OFF` dosyası | yok | Bu klasörde varsa yeni taze giriş açılmaz. Mevcut sepetler ekleme ve TP ile yönetilir. |
| `--canli --demo-onayi EVET` | kapalı | Gerçek emir gönderir. Hesap DEMO değilse veya hedge değilse açılmayı reddeder. |

Kimlik bilgileri:
- Magic **52896686**. Bot 52890969(+n) ve decider 52890989 ile çakışmaz.
- Yorum `DBGK B3` biçiminde, 28 karakteri geçmez. 31+ karakterlik yorum MT5'te emri reddettirir.

## Nasıl açılır (kullanıcı kararı sonrası)

1. **Ayrı bir demo hesap ve terminal kullanın.** Ana botun hesabında çalıştırılırsa iki sepetin marjini ana botla paylaşılır; derin sepet botun işlemlerini de stop-out'a sürükleyebilir. Hesap **hedge** olmalı.
2. Klasörü kutuya taşıyın. `research/` kutuda sparse-checkout dışında olduğu için repo köküne ayrı bir klasör (ör. `dbg_klon/`) olarak kopyalamak ve `main`'e push etmek gerekir. Ajanın yeniden başlatma haritasında bu klasör yok, yani hiçbir süreç kendiliğinden başlamaz.
3. GÖLGE başlatma (MT5 terminali açıkken):
   ```
   python dbg_klon\dbg_klon_runner.py --terminal "C:\...\terminal64.exe"
   ```
4. İzleme:
   - `dbg_klon_log.jsonl`: `fresh` / `add` / `tp` / `kesici` / `nabiz` olayları.
   - `dbg_klon_state.json`: yeniden başlatmaya dayanıklı sepet durumu.
   - Bir hafta sonra log, aynı haftanın geri testiyle (`../klon_motor.py`) olay olay kıyaslanır. Ölçülecekler: bar açılışı spread'i, olay eşleşmesi, sanal TP sayısı.
5. Demo'da gerçek emir yalnız gölge kıyası temiz çıkarsa ve bilerek:
   ```
   python dbg_klon\dbg_klon_runner.py --canli --demo-onayi EVET --max-sepet-zarar 1000 --max-toplam-zarar 2500
   ```
   Kesici takılıyken geri test beklentisi negatif. Bu adım icra ölçümüdür, kâr beklentisi değil.

## Bilinen sınırlar

- Gölge dolumlar 0,5 sn'lik yoklama fiyatıyla yapılır. Yoklamalar arasındaki tepe ve dipler kaçabilir. Geri test M1 tepe/dip kullanır.
- Canlı modda TP, sunucu tarafında tüm pozisyonlara yazılır. Yönetici de tick'te TP'yi denetler ve kalan pozisyonları kapatır (yedek).
- Swap modellenmedi. Geri testte kesicisiz 16 ayda 0,01 tabanla ~396 lot-gece birikti (DBG ölçeğinde 1.979). Uzun pozisyon swap'ı brokerın oranıyla çarpılmalıdır.
- Broker'ın tek emir ve toplam lot sınırları kontrol edilmez. Kesicisiz derin sepetlerde lot 0,01 × 1,1^82 ≈ 25 lot'a çıkıyor.
