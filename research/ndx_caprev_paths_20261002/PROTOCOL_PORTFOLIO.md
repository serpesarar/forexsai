# Tanısal sermaye çakışması denetimi

Beş yeni varyasyon ve iki birleşimin sonuçları görüldükten sonra sabitlendi.
Yeni eşik/optimizasyon değil; tek başına strateji kazancı, mevcut bot araştırma
portföyüne eklendiğinde gerçek toplam katkı mıdır sorusunun icra denetimidir.
Tüm dönemler retrospektif; gerçek bot sinyal evreni diye sunulmayacak.

Daha önce dondurulan özgün beşli: opening_break, exhaustion SELL, sweep SELL,
variance_switch, failed_break BUY; fast/core/slow geometrileri ve öncelikleri
korunur. Ham fırsatlar yeniden yürütülür; eski kabul edilmiş alt kümeyi yeniden
kullanmak yasak. CAPREV tek başına aynı risk birimiyle alınmış üç tanım eklenir:
BASE, HALF_RISING, TP1_RISING. Başlangıçta bir toplam risk birimi; kısmi çıkış
sonrası CAP'in kalan pozisyonu varsa başka girişe izin yok.

Girişler kronolojik. Aynı dakikada CAP öncelikli; daha önce açık normal pozisyon
varsa CAP alınmaz. Tek açık toplam pozisyon, girişler arası10 dakika, eski
stratejiler15:55/CAP16:00 kapanış. CAP niyeti sonraya taşınmaz ve sırf veto edilen
pozisyonu kurtarmak için mevcut işlem kapatılmaz. Ana/spread3/kayma1/gecikme1M1;
aynı 5 dönem ve M1 fiyatlar. Ek üç portföy + değişmeyen taban =4 yapılandırma.
Bu tur toplam12 strateji/çıkış tanımı +4 portföy tanımı =**16**, hücre sayısı
program çıktısından kaydedilecek. Net USD/gerçek eşit-risk dolumu iddiası yok.
