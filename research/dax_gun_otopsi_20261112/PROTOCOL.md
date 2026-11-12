# DAX 11–12 Kasım otopsisi — ön kayıt (2026-11-12 21:55 UTC, sonuçlara bakmadan)

Gözlem (yalnız bu iki gün): 11-11'de CEKIC 09:00, MOMSR 09:15, DECIDER 09:27 aynı düşüşe ardışık AL → üçü SL;
11-12'de DECIDER 11:00/11:21 ve CHREV 12:00 gün tepesinden (27.022) inen fiyata AL → CHREV 10 lot −1.320 $.

Defterde zaten X: bıçak yakalama (IO-25 H1), kayıp sonrası tekrar / kovalama / 1h ters trend (IO-04), SL girişte tanınmıyor (IO-26).
Bu yüzden onları YENİDEN sınamıyorum. Yeni soru: **aileler arası yığılma**.

## Y1 — kalabalık giriş (sembol × yön)
Tanım: giriş anında aynı sembolde aynı yönde BAŞKA bir bot pozisyonu açık (hangi aile olursa olsun).
Ölçü: ort R (r_exit) var/yok; Δ, gün-blok bootstrap (5.000), kronolojik iki yarı, aile içi (aileye göre tabakalı fark).
Geçme (gölge adayı, B−): Δ < 0, P(Δ<0) ≥ 0,95, iki yarıda da < 0, tabakalı fark < 0. Aksi C/X.

## Y2 — açık pozisyon zararda iken ekleme
Tanım: Y1 ∧ o açık pozisyon(lar)ın en az biri giriş anında zararda (giriş fiyatına göre). Aynı ölçüler. (Y1'in alt kümesi; ikisi Holm.)

## Y3 — risk dağılımı (sınama değil, ölçüm)
CHREV GER40 işlem başı $ risk (|E−SL| × lot × tick değeri ≈ kayıp $): dağılım; 11-12 işlemi kaçıncı yüzdelik.

Veri: `output/islem_otopsi/2026-11-12_2142_all/islemler.csv` (bot_trades 400 g, 1.080 işlem, saat ekseni ALIGNED).
