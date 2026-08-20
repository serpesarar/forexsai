# USOIL v3 "Test Listesi Uygulama Raporu" — bağımsız denetim

**Tarih:** 2026-08-20 · **Konu:** karşı ajanın F1+F2 giriş rejim filtresi, cooldown,
TP=0,6R ve yan iddiaları · **Sonuç:** 1 iddia gerçek ama **zaten canlı**, 1 iddia
**tam tersine** çıktı, kalanı elendi.

Raporun kendi kabul ettiği açık kapı H4'tü ("derin dış-örneklem — yerelde
çalıştırılamaz"). Bu denetim tam olarak o kapıyı kapattı: kutudaki MT5'ten
**17 aylık** veri (2025-03-31 → 2026-08-20) ve botun **gerçek** USOIL:BUY
momentum koşullarıyla üretilen **2.025 sızıntısız hipotetik giriş** + botun
**64 gerçek** MOM/SR BUY işlemi.

Araçlar: `backend/research/box_usoil_v3_oos.py` · `box_usoil_pos_tp.py` ·
`box_usoil_tp_stability.py` · `box_usoil_posgate_hole.py` ·
`1MDATA/usoil_islem_analizi/07_v3_denetim.py`

---

## 1. Kapı kapı sonuç

| İddia | Rapor diyor | Denetim | Karar |
|---|---|---|---|
| **F1** ATR14/ATR60 ≤ 1,09 | p=0,003, ana bulgunun yarısı | 17 ayda **tamamen düz**: eşik 0,85→1,50 arası WR %58,7–59,9. Hiçbir ayrım yok | ❌ **gürültü** |
| **F2** pos_in_range(4s) ≤ 0,85 | p=0,028 | **Gerçek**: işlem başı +11,3$ → +39,5$ (n=1.037). Üst bant (0,85–1,00) −18,3$/işlem | ✅ ama **zaten canlı** |
| **F1+F2** paketi | n=23 WR %82,6 +4.020$ | Aritmetik doğrulandı — ama n=23 için **BUY şartı da** gerekiyor (F1+F2 tek başına n=38 WR %65,8) | ⚠️ etiket yanlış |
| **p<0,001** | koşullu plasebo | Eşik **sabit** tutulunca p=0,006; eşik ızgarası da permüte edilince **p=0,038**. Derin örneklemde 2B arama p=0,064–0,072 | ⚠️ şişik |
| **Cooldown** 2 SL → 4 saat | +1.198$ kurtarıyor | 12 hücrelik ızgaranın en iyisi; ızgara aramalı plaseboda **p=0,225** | ❌ gürültü |
| **TP=0,6R** (para şampiyonu) | +4.336$ | Derin örneklemde **+9,3$/işlem** — botun bugünkü RR 0,70'inden (+11,2$) bile **kötü**. RR 1,00 → **+34,0$** | ❌ **ters** |
| **TP=2×ATR14** (WR şampiyonu) | %66,2 | Aynı bilinen desen: WR ↑, para ↓ (F1+F2 kümesinde +3.594$ → +2.138$) | ❌ kozmetik |
| C7 spike · G3 fade · F3 kovalamama · günlük devre kesici · BE@TP≤1,25R · saat bloğu | raporun kendisi elemiş | Bizim önceki ölçümlerimizle uyumlu | ✅ elenmiş kalsın |
| **Re-entry** (SL→1dk aynı yön) | +1.285$ aday | 2026-08-20'de zaten canlıya alındı (`REENTRY_MODE=live`) | ➖ mevcut |

---

## 2. Ana bulgu: F2 zaten canlı, üstelik daha sıkısı

Botta **2026-07-28'den beri** `POSITION_GATE_ENABLED=True`, `POS_BUY_MAX=0.60`
(`forexsai_demo_bot.entry_position` / `_position_gate_blocks`). Ölçüm birebir
aynı: son 48×5dk (4 saat) aralığında giriş fiyatının yeri.

Yani rapor **kapıyı yeniden keşfetti** — ve raporun veri penceresi (07-13 → 08-14)
kapının **öncesini** kapsıyor. "Elenen grup WR %35,7 / −1.716$" dediği işlemlerin
tamamı kapı yokken açılmış işlemler.

**Kapıda delik yok** (`box_usoil_posgate_hole.py`): 2026-07-28 sonrası açılan
8 USOIL MOM/SR BUY işleminin **hepsi** konum ≤0,57. Öncesinde 0,60–0,95 aralığında
düzinelerce işlem var.

### Eşik gevşetilmeli mi? (0,60 → 0,85)

Derin örneklem eşiğin doğru yerini net gösteriyor — uçurum **0,85'te**:

| bant | n | WR | işlem başı |
|---|---|---|---|
| (0,40–0,50] | 38 | %76,3 | +157,3$ |
| (0,50–0,60] | 81 | %59,3 | +4,0$ |
| (0,60–0,85] — **kapının blokladığı** | 884 | %61,9 | **+38,9$** |
| (0,85–0,90] | 306 | %59,2 | +2,8$ |
| (0,90–1,00] | 681 | %55,1 | **−27,7$** |

(başabaş WR %58,9 · 1B plasebo p=0,007 · bootstrap P(EV>0)=%99,4 · spread ×2'de hâlâ +18,6$)

**Yine de gevşetmiyoruz:** kronolojik iki yarı testi kalıyor — 1. yarı **−2,7$**/işlem,
2. yarı +80,6$. 18 ayın 8'i negatif. go_live_gate 3. ölçütü (iki yarı da ≥0)
geçilmiyor. Backlog'a alındı.

---

## 3. Yeni bulgu: hedef mesafesi yanlış yönde ayarlı

Raporun TP iddiasını sınarken tersi çıktı. 2.025 hipotetik giriş, spread 0,03,
giriş = sinyal barı kapanışı, çözüm sonraki barlardan, aynı barda TP+SL → kayıp:

| RR | n | WR | işlem başı | 1. yarı | 2. yarı | P(EV>0) | spread ×1,5 | sıralı kısıt |
|---|---|---|---|---|---|---|---|---|
| 0,60 (rapor) | 2025 | %62,9 | +9,3$ | −13,5$ | +32,1$ | %83,5 | +1,3$ | +6,7$ |
| **0,70 (bugünkü)** | 2024 | %59,2 | **+11,2$** | −17,0$ | +39,4$ | %86,0 | +4,2$ | +5,8$ |
| 0,80 | 2024 | %56,8 | +20,2$ | −14,4$ | +54,7$ | %96,6 | +13,6$ | +21,0$ |
| **1,00 (aday)** | 2022 | %52,3 | **+34,0$** | **−7,6$** | +75,7$ | **%99,6** | +24,7$ | +21,9$ |
| 1,25 | 2009 | %46,0 | +30,4$ | −33,7$ | +94,5$ | %98,8 | +22,6$ | +17,4$ |
| 1,50 | 1992 | %41,6 | +32,2$ | −37,8$ | +102,2$ | %98,5 | +23,5$ | +33,9$ |

RR 1,00, mevcut ayarı **her kesitte** geçiyor: iki kronolojik yarıda da, 18 ayın
12'sinde, sürtünme stresinde, "aynı anda tek pozisyon" kısıtında ve **canlı konum
kapısı altında** (pos≤0,60: +71,5$ vs +43,4$, n=153). Plato 0,80–2,00 geniş;
uçurum 0,70'in **altında** — yani raporun gittiği yön.

⚠️ **Ama scope'un kendisi 1. yarıda negatif** (hangi RR olursa olsun). Kanıt
"RR 1,0 > RR 0,7" için güçlü; "bu scope her rejimde kârlı" için değil.

**Uygulama:** `phase_rules.DEFAULTS["USOIL_BUY_TP_RR"]` + `forexsai_demo_bot._fixed_distances`
kancası yazıldı, **varsayılan 0,0 = KAPALI**. Açmak tek satır: kutunun config'ine
`USOIL_BUY_TP_RR = 1.0`. Yalnız BUY, yalnız USOIL, DAYCOMBO muaf, bozuk girdide
fail-open. Testler: `tests/test_usoil_buy_tp.py` (5 test).

---

## 4. Metodolojik notlar (raporun sayıları neden şişikti)

1. **Eşik araması permüte edilmemiş.** F1'in eşiği (1,09) ve F2'nin (0,85) aynı
   veride seçilmiş. Plaseboyu sabit eşikle koşarsan p=0,006, eşik aramasını da
   tekrarlarsan p=0,038 — 6 kat fark.
2. **Başabaş yanlış varsayılmış.** F1+F2 kümesinin medyan RR'i 0,78 → başabaş
   WR %56,2. "WR %82,6, binom p=0,005" hesabı p₀=%50 varsayıyor; doğru nulle
   karşı p=0,151.
3. **Baz yanlış seçilmiş.** 74 işlemin 19'u USOIL_BREAKOUT (zaten gölge), 19'u
   MOM/SR SELL (zaten bloklu). Gerçek canlı baz 36 işlem.
4. **Paket kendi bileşeninden kötü.** Raporun "BUY+F1+F2+TP0,6R" paketi (+4.209$),
   canlı baza yalnız TP=0,6R uygulamaktan (+5.951$) **1.742$ daha az** kazandırıyor.

---

## 5. Ne değişti / ne değişmedi

**Değişmedi (bilinçli):** konum kapısı 0,60'ta kalıyor · TP geometrisi %1,04'te
kalıyor (bayrak kapalı) · cooldown/spike/fade/saat bloğu eklenmedi.

**Değişti:** `USOIL_BUY_TP_RR` bayrağı + kancası + 5 test · dört araştırma scripti.

**Sıradaki karar (backlog):** (a) `USOIL_BUY_TP_RR=1.0` açılsın mı — açılırsa
2 hafta sonra gerçek işlemlerle RR 0,70 dönemine karşı karne; (b) konum kapısı
0,60→0,85 gevşetmesi, ancak rejim bağımlılığı çözülürse.
