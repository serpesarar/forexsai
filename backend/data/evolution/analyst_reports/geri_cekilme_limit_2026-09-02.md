# S08 — Geri çekilmede daha iyi fiyattan giriş (oturumun tek OOS-geçen stratejisi)

**Fikir:** sinyalde hemen girme; X puan **daha iyi** fiyata limit koy
(SELL → yukarıdan sat). Süre içinde dolmazsa market'ten gir.

Bu, S07'nin (aşağıdaki desteği bekle) **tersi**. S07 giriş fiyatını bozup SL'i
fiyata yaklaştırıyordu; S08 tam tersini yapıyor: SL uzaklaşır, TP yaklaşır.

## Sonuç

| | tarihsel (284) | **bu hafta (8, OOS)** |
|---|---:|---:|
| filtresiz | +5.023 | +105 |
| X=20 / 30dk, dolmazsa market | **+19.606** | **+970** ✅ |
| X=20 / 30dk, dolmazsa atla | +725 | +501 |

Dayanıklılık: **4/4 çeyrek** (Ç3 −2.627 → +5.481), **7/9 hafta**,
doluluk **%74** (211/284).

**Risk-sabit kontrol:** TP/SL mutlak seviyeleri sabit tutulduğunda (sinyal
fiyatına göre risk değişmez) sonuç **+21.652$** — yani kazanç "daha fazla risk
almaktan" değil, gerçekten **giriş kalitesinden** geliyor.

Bu haftanın en çarpıcı örneği: 09-02 08:53 SELL, orijinal −549$ (SL);
20 puan yukarıdan girilince **+391$ (TP)**.

## ⚠️ Neden GÖLGE, neden hemen canlı değil

X'e tepki **monoton artıyor** — X5=+11.288 … X40=+27.266, **plato yok.**
Bu, S04'te yakaladığım "sınır artefaktı" imzasının aynısı: model beklemenin
maliyetini eksik sayıyor (sinyalin bayatlaması, limitin gerçekten dolacağı
varsayımı, fiyat X puan aleyhte giderken kurulumun hâlâ geçerli sayılması).
Sonuçlar **üst sınır** olarak okunmalı.

## Bot'ta altyapı zaten var
`open_trade_sr` pending limit + `PENDING_EXPIRY_MIN=30` mevcut. İki fark:
1. Bot limiti **S/R bölgesine** koyuyor, sabit X ofsetine değil.
2. `SR_FALLBACK_MARKET=False` → dolmazsa **atlıyor**; test bu varyantın çok daha
   zayıf olduğunu söylüyor (+725 vs +19.606).

**Önerilen ilk adım:** S08'i gölge bayrağı olarak bağla; canlı doluluk oranı
ölçülsün (simülasyondaki %74 gerçekleşiyor mu?). Doluluk tutuyorsa
`SR_FALLBACK_MARKET` tartışması kanıtla açılır.
