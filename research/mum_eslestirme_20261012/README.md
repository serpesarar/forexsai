# Mum Eşleştirme Motoru — fizibilite ölçümleri (2026-10-12)

> **İleri sonuç testi (ME-02):** `RAPOR_KALDIRMA_TESTI.md` — 98.260 karar anında eşleşme tahminleri rastgele komşu
> düzeyinde; hiçbir kaldırma kuralı bunu değiştirmiyor.

> **v0.2 güncellemesi (aynı gün):** Codex incelemesi (`docs/MUM_ESLESTIRME_TASARIM_INCELEMESI_CODEX.md`) v0.1 sayımlarında
> iki kusur buldu: sorgudan sonraki adaylar da sayılıyordu ve mumlar kendi ATR'lerine bölünüyordu (tasarım pencere-sonu ATR diyor).
> `fizibilite_4_nedensel.py` ikisini düzeltir (aday yalnız j + H ≤ t; ortak pencere-sonu ATR; bağımsız olay aralığı ≥ max(X, H);
> 4h/1d broker gün sınırıyla). **Tasarım kararları artık bu sayılara dayanır**; `fizibilite_1–3` + `ozet.py` tarihsel kayıttır.
> Sonuç: X_max değişmedi (0,2 ATR'de medyan sorgu 5m–1h 2, 4h/1d çoğunlukla 1; üst çeyrek 2–3), olay sayıları düştü;
> yeni bulgu kapasite (1d, 5 y, 33 mum + H=20 → ≤ ~24 bağımsız olay). Ön-kayıt taslağı: `PROTOCOL_TASLAK.md`;
> v0.1 tasarımı: `arsiv/MUM_ESLESTIRME_ALGORITMASI_v0.1.md`.

Tasarım belgesi: [`docs/MUM_ESLESTIRME_ALGORITMASI.md`](../../docs/MUM_ESLESTIRME_ALGORITMASI.md) (§3 bu klasörün sonuçlarıdır).
Defter: `docs/KAPI_KAYIT_DEFTERI.md` → ME-00, E25.

**Soru:** Kullanıcının "son X mumu, her mum %0,01–0,02 payla, 5 yıllık geçmişte eşleştir" tanımı kaç mum taşır?
**Kural:** Bu klasördeki hiçbir betik gelecekteki fiyata (sonuca) bakmaz; yalnız eşleşme SAYAR → yön/büyüklük
araştırmasının ön-kaydı temiz kalır.

## Sonuç (tek paragraf)

Birebir mum-mum eşleşmede beklenen eşleşme ≈ N·p₁^X, dolayısıyla **X_max ≈ ln(N/30) / ln(1/p₁)**. 15 sembol × TF
hücresinde ≥30 bağımsız eşleşme veren en uzun dizi: %0,01 → 0–1 mum, %0,02 → 0–2, 0,2 ATR → 2, 0,3 ATR → 2–3 (formül
öngörüsüyle tutarlı). Sabit % pay semboller arasında 600 kat farklı katılık demek (tek mum eşleşme olasılığı OIL 1h
%0,01, NDX 5m %6,2); 0,2 ATR hepsini %3–6'ya eşitler. Huni ve %80 kısmi eşleşme tavanı 2'de bırakır. Ham pencerede kNN
göreli kontrastı 3 mumda ~4, 30 mumda ~1,5'e (rastgeleye yakın) düşer; **log-zaman piramidi** (33 mum → 7 süper mum)
kontrastı ham 7 mum düzeyinde (2,3–2,6) tutar → uzun bağlam için ana temsil.

## Dosyalar

| Dosya | İş | Süre |
|---|---|---|
| `_common.py` | veri kaynakları (4 sembol × 15 hücre), broker-satır süzgeci, 5 yıl kesimi | — |
| `fizibilite_1_birebir.py` | kullanıcı tanımı: %0,01/0,02/0,05 ve 0,1/0,2/0,3 ATR, X = 1…12 | ~3 dk |
| `fizibilite_2_huni_kismi_knn.py` | huni toleransı, %80 kısmi, kNN göreli kontrast (X = 3…30) | ~4 dk |
| `fizibilite_3_piramit.py` | piramit (D33) vs ham 33/7 mum; piramitte birebir pay | ~1 dk |
| `ozet.py` | `results/ozet.csv` — X_max tablosu + formül sınaması (v0.1) | saniye |
| **`fizibilite_4_nedensel.py`** | **v0.2:** nedensel aday havuzu, ortak pencere-sonu ATR, bağımsız olay, uygunluk, 4h/1d (5 y / 10 y) | ~10 dk |
| **`ozet_v2.py`** | **v0.2:** `results/ozet_v2.csv` — medyan / üst çeyrek / uygun X_max, X=2–3 olay sayıları | saniye |
| `PROTOCOL_TASLAK.md` | ön-kayıt taslağı (dondurulmadı) | — |
| **`kaldirma_testi.py`** | **ileri SONUÇ testi** (kullanıcı isteği): 4 yöntem × 5 eşleşme-kaldırma varyantı × 23 sembol×TF × 3 ufuk; son 7 ay dokunulmadı | ~10 dk (7 çekirdek) |
| **`kaldirma_ozet.py`** | özet, hücre anlamlılığı (gün-blok bootstrap), çoklu-TF uyumu → `results/kaldirma_*.csv` | ~30 sn |
| **`RAPOR_KALDIRMA_TESTI.md`** | **sonuç: yön/büyüklük/hedef tabanlardan iyi değil; eşleşme = rastgele komşu** | — |
| `PROTOCOL_BAGLAM.md` · **`baglam_testi.py`** · `baglam_ozet.py` | ME-03: bağlam (VIX/stres/CAPREV/saat/oynaklık) + çapraz-sembol (12 çift) ön-kayıtlı test | ~4 saat |
| **`RAPOR_BAGLAM_TESTI.md`** | **sonuç: hiçbir kombinasyon yönde katkı vermedi; büyüklükte saatin tipik hareketi yenilmedi** | — |
| `results/*.csv`, `results/fizibilite_3_piramit.txt` | ham çıktılar | — |

```bash
python3 research/mum_eslestirme_20261012/fizibilite_1_birebir.py
python3 research/mum_eslestirme_20261012/fizibilite_2_huni_kismi_knn.py
python3 research/mum_eslestirme_20261012/fizibilite_3_piramit.py
python3 research/mum_eslestirme_20261012/ozet.py
# duman testi: FEAS_ONLY="NDX:1h" FEAS_NQ=4 python3 research/mum_eslestirme_20261012/fizibilite_1_birebir.py /tmp/x.csv
```

Sonuç dosyaları betiklerin ilk sürümüyle (algoritma aynı; yalnız ortak kod `_common.py`'ye taşındı) üretildi;
yeniden düzenlenmiş sürüm duman testinden geçti.

## Veri notları

- Kaynaklar: `research/ndx_pattern_motifs/data` (NDX 5m/15m), `research/ndx_gate_forge/data` (NDX 30m/1h, DAX),
  `research/pinbar_20261010/data` (XAU/OIL; `src == "yahoo"` satırları atıldı — E21).
- Yıllık bar sayısıyla doğrulama: NDX/XAU/OIL 1h 2017'den beri ~5.900 bar/yıl (gerçek 10 yıl); 30m'ler 2021 ortasından
  beri ~11.800 bar/yıl; **DAX 1h 2019'a kadar seyrek** (2012: 254 bar) → yalnız 2020+ kullanılabilir.
- Saat ekseni (yaz dönemi en oynak saat): NDX 14/13, XAU 13/14, OIL 13/14/15 UTC → UTC ile tutarlı.
- Pencereler hafta sonu boşluğunu geçebilir (özellikler mumun kendi açılışına göre olduğu için sayıma etkisi ihmal
  edilebilir); asıl motor segment sınırını geçmeyecek (tasarım §5.4).
