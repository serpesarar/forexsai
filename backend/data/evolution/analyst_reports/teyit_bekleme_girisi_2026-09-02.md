# Kullanıcı mekanizması: "aşağıdaki M30 desteği de kırılana kadar bekle, sonra gir"

**Soru:** 5m kırılımında hemen girmek yerine, 40 puan aşağıdaki M30 desteğinin de
kırılmasını bekleyip oradan girsek — işlemler kâra geçer mi, yoksa TP olacak
işlemleri kaçırır mıyız?

**Cevap: ikisi de oluyor — ve ÜÇÜNCÜ, beklenmedik bir maliyet var.**

## 1. Tarihsel sonuç umut verici görünüyor

M30 desteği bekleme (20-100 puan aralık, 10 puan teyit marjı, 120 dk):
**+16.721$** vs filtresiz **+4.290$**. Denenen 36 hücrenin **36'sı da** bazı geçiyor.

## 2. AMA ayrıştırma mekanizmanın ne olduğunu değiştiriyor

| bileşen | n | etki |
|---|---:|---:|
| Seviye yok → normal giriş | 151 | +4.361 |
| **Gecikmeli giriş yapılanlar** | 75 | +19.490 → +12.359 = **−7.131** |
| **Hiç açılmayanlar** (teyit gelmedi) | 56 | **+19.562** kaçınılan (10 TP / 46 SL) |

**Gecikmeli girişin kendisi para KAYBETTİRİYOR.** Tüm kazanç, teyit gelmeyince
işlemi hiç açmamaktan geliyor. Yani bu "daha iyi giriş" değil,
**"momentum devam etmezse açma" filtresi.**

Girişler ortalama **56 puan aşağıdan** yapılıyor; %17'si orijinal TP mesafesinin
(80 puan) ötesinde — yani hareket bittikten sonra giriliyor.

## 3. Pratik varyant (orijinal fiyata yakın kal)

"Sinyalden sonra X puan daha lehte kapanış olursa gir, olmazsa açma":
en iyi **X=5 puan / 60 dk → +8.898$** (251 giriyor, 31 açılmıyor: 29 SL / 2 TP).

## 4. ⚠️ BU HAFTA (gerçek dış-örneklem) — ÇÖKTÜ

| | filtresiz | X=5 / 60dk |
|---|---:|---:|
| toplam | **+105$** | **−2.020$** |

| zaman | orij. | yeni giriş | orij. sonuç | orij. | yeni |
|---|---:|---:|---|---:|---:|
| 09-01 14:34 | 29161,1 | 29155,4 | **TP** | +400 | **−561** ⚠️ |
| 09-01 20:10 | 29082,8 | AÇILMADI | **TP** | +405 | 0 |
| 09-02 12:30 | 29064,3 | 29050,6 | **TP** | +400 | **−311** ⚠️ |
| 4 SL'in dördü | | hepsi açıldı | SL | −1.498 | −1.538 |

**4 SL'in hiçbirini engellemedi** (hepsinde 5 puanlık devam geldi), buna karşılık
**2 TP'yi zarara çevirdi** ve 1 TP'yi kaçırdı.

## 5. Üçüncü maliyet: gecikmeli giriş KAZANANI ZARARA ÇEVİRİYOR

Tarihsel veride de sistematik (X=5 / 60dk, 195 giriş):

| | adet | etki |
|---|---:|---:|
| TP → SL çevrilen | **13** | **−11.630$** |
| SL → TP kurtarılan | 3 | +2.570$ |
| **net** | | **−9.060$** |

X büyüdükçe kötüleşiyor (X=15 → net −17.238$).

**SEBEP (mekanik, tesadüf değil):** SL **mesafesi sabit** kalıyor. SELL'e daha
aşağıdan girince SL seviyesi de aşağı kayıyor → son fiyat hareketine **daha
yakın** oluyor. Kıl payı hayatta kalan kazananlar bu kaymayla stop yiyor.

## 6. Hüküm: canlıya ALINMADI

Mekanizmanın iki zıt etkisi var:
* **kazanç:** teyit gelmeyince açmama (tarihsel ~+13,7k)
* **kayıp:** giriş fiyatı bozulması → kazananların stop yemesi (~−9,1k)

Net marj ince ve iki büyük zıt kuvvete dayanıyor — yapısal olarak **kırılgan**.
Bu hafta kaçınma etkisi ~0 çıkınca kayıp tarafı baskın geldi ve kural
+105$'ı −2.020$ yaptı.

## 7. Umut veren yön (test edilmedi)
Beklemenin bedeli, SELL'de **daha kötü fiyattan** girmek. Tersi mümkün:
**geri çekilmeyi bekleyip DAHA İYİ fiyattan (yukarıdan) satmak** — botta zaten
`open_trade_sr` + pending limit + `PENDING_EXPIRY_MIN=30` altyapısı var.
Bu, entry-price maliyetini kayıp değil **kazanç** tarafına çevirir. Ayrı test konusu.
