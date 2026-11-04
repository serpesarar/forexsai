# Codex Trade Edge Lab — kurulum ve ilk deneme özeti

**Tarih:** 29 Eylül 2026  
**Durum:** Yerel araştırma aracı hazır. Canlı strateji veya bot kapısı değiştirilmedi.

## Nereye ne eklendi?

| Konum | Amaç |
|---|---|
| `.agents/skills/trade-edge-lab/SKILL.md` | Codex'in işlem otopsisi ve strateji araştırması istendiğinde uygulayacağı proje becerisi. Karar anı verisi, kronolojik test, risk ve gölge doğrulama sınırlarını tanımlar. |
| `.agents/skills/trade-edge-lab/references/data_contract.md` | İşlem ve 1 dakikalık bar verisinin beklenen alanlarını, sonuçların nasıl okunacağını ve NDX pilotunun veri kısıtlarını açıklar. |
| `.agents/skills/trade-edge-lab/scripts/audit_trades.py` | Yerel JSON işlem kaydı ile CSV barlarını eşler; girişten önce kapanmış barlardan EMA20/EMA50, beş bar momentumu ve fiyat/EMA20 uyumu çıkarır. Kronolojik 70/30 karşılaştırma, belirsizlik aralığı, rapor ve grafik üretir. Ağ veya canlı veritabanına bağlanmaz. |
| `.agents/skills/trade-edge-lab/tests/test_audit_trades.py` | İşleme giriş anındaki açık/gelecek barın kullanılmamasını, tahmin edilmiş stopun R sayılmamasını ve sonuçları test başlangıcını aşan eğitim işlemlerinin dışlanmasını doğrular. |
| `AGENTS.md` | Yeni beceriye kısa yönlendirme eklendi; Codex ilgili görevlerde onu bulabilir. |
| `backend/data/evolution/system_registry.json` | Aracı araştırma bileşeni olarak Evrim Paneli sistem haritasına kaydeder. Ayrıca yerel oturum notu `session_log.json` dosyasına yazıldı. |
| `output/trade-edge-lab/ndx-pilot/` | Mevcut NDX kayıtlarıyla üretilmiş ilk `report.md`, `summary.json` ve `trade_examples.png`. |

Bu kurulumda ayrıca Codex Goal, beceriyi ve ilk pilotu tamamlamak için kullanıldı. Goal tek bir Codex görevine aittir; proje dosyalarına veya trading botuna kalıcı bir çalışma döngüsü eklemez.

## İlk pilotun gösterdiği

Kaynak: `research/trade_mgmt_ndx/trades.json` ve `bars_1m.csv`, **15 Haziran–9 Temmuz 2026**. 225 gerçek işlemden 219'u karar öncesi bar geçmişiyle eşleşti; 6 işlem veri boşluğu veya yetersiz geçmiş nedeniyle dışlandı. Test dilimi 2 Temmuz 2026 UTC itibarıyla 66 işlem içeriyor.

| Önceden tanımlı filtre | Test n | Gerçek PnL işaretine göre kazanma | Wilson %95 aralık |
|---|---:|---:|---:|
| Tüm eşleşen işlemler | 66 | %54,5 | %42,6–66,0 |
| En az iki gösterge uyumlu | 36 | %61,1 | %44,9–75,2 |
| Üç gösterge uyumlu | 30 | %53,3 | %36,1–69,8 |
| **Tam iki gösterge uyumlu** | **6** | **%100** | **%61,0–100,0** |

Son satır yalnızca **6 işlem** içeriyor. Bu, %70+ bir stratejinin kanıtı değildir; aralık geniştir ve rapora bakarak o alt kümeyi seçmek yeni bir bağımsız test dönemi gerektirir. Ayrıca veri yalnız açılmış işlemleri içeriyor; botun reddettiği veya `WAIT` dediği fırsatlar yok. Kullanılan üç gösterge, sistemin tüm sinyal oylarını temsil etmez.

NDX dosyasında bazı stop mesafeleri sonradan tahmin edildiği için araç bu pilotta **R bazında beklenen getiri üretmiyor**. Gerçek giriş anındaki `risk_cash` veya doğrulanmış stop mesafesi sağlanmadan bir kazanma oranı, kârlı strateji kararı için yeterli değildir. Grafikte TP/SL seviyeleri görsel bağlamdır; kaynakta tahmin edilmiş olabilir.

## Nasıl yeniden çalıştırılır?

Proje kökünden:

```bash
python3 .agents/skills/trade-edge-lab/scripts/audit_trades.py \
  --trades research/trade_mgmt_ndx/trades.json \
  --bars research/trade_mgmt_ndx/bars_1m.csv \
  --symbol NDX.INDX \
  --out output/trade-edge-lab/ndx-pilot
```

Codex'e doğrudan “`$trade-edge-lab` ile şu işlem kümesini incele” denebilir. Daha sonraki aşamada gerçek risk tutarı, spread, strateji sürümü ve açılmayan fırsatların karar anı görüntüleri eklenmeli. Adaylar ileri dönemde gölge olarak ölçüldükten sonra mevcut canlıya alma kartıyla değerlendirilmelidir.

## Doğrulama

- Skill yapısı `quick_validate.py` ile doğrulandı.
- Üç davranış testi geçti.
- Pilot raporu ve grafik gerçek yerel dosyalardan yeniden üretildi; grafik görsel olarak kontrol edildi.
