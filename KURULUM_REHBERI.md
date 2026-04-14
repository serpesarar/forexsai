# ForexSAI — Claude Code Maksimum Verim Rehberi

## 🎯 Bu Rehberin Amacı

Claude Code'u ForexSAI projenizin "ortak geliştiricisi" haline getirmek.
Kısa komutlarla büyük işler çıkaran, her değişikliğin tüm bağımlılıklarını
otomatik düşünen, proaktif iyileştirmeler sunan bir asistan kurmak.

---

## 📦 ADIM 1: Dosya Yerleşimi

Proje kök dizininize şu dosyaları kopyalayın:

```
forexsai/                         ← proje kökü
├── CLAUDE.md                     ← ANA DOSYA (sana verdiğim büyük dosya)
├── .claude/
│   └── settings.json             ← İzin ayarları
├── .cursorrules                  ← (opsiyonel, Cursor IDE kullanıyorsan)
├── frontend/
├── backend/
└── supabase/
```

### CLAUDE.md Nedir?
Claude Code her oturumda proje kökündeki `CLAUDE.md` dosyasını otomatik okur.
Bu dosya Claude Code'un "beyni" — projenin tüm mimarisini, kurallarını ve
davranış standartlarını içerir. Sana verdiğim `CLAUDE.md` dosyasını olduğu
gibi proje köküne koyduğunda, Claude Code her komutta otomatik olarak:
- Tüm 6 modelin bağımlılık haritasını bilecek
- Regime-aware ağırlık sistemini anlayacak
- Supabase tabloları ve ilişkilerini takip edecek
- Cascade etkileri otomatik düşünecek

---

## 📦 ADIM 2: Claude Code'u Başlatma

Terminal'de proje kökünde:

```bash
# Claude Code'u başlat
claude

# Ya da direkt bir komutla başlat
claude "projeyi incele ve mevcut durumu özetle"
```

İlk oturumda Claude Code otomatik olarak CLAUDE.md'yi okuyacak.
Eğer okumadığını düşünüyorsan:

```
/init
```

yazarak CLAUDE.md'yi yeniden yükletebilirsin.

---

## 📦 ADIM 3: settings.json Ayarları

`.claude/settings.json` dosyası Claude Code'un hangi komutları izinsiz
çalıştırabileceğini belirler. Sana verdiğim ayar dosyasında yaygın
komutlar (npm, pip, python, git, supabase CLI, pytest, dosya işlemleri)
önceden izinli. Bu sayede Claude Code her seferinde "bunu çalıştırabilir
miyim?" diye sormaz, direkt çalıştırır.

Daha fazla izin eklemek istersen:
```json
{
  "permissions": {
    "allow": [
      "Bash(docker:*)",
      "Bash(supabase:*)"
    ]
  }
}
```

---

## 🧠 ADIM 4: Etkili Prompt Yazma Stratejisi

### ❌ KÖTÜ — Belirsiz ve yetersiz:
```
pulse1'i düzelt
```

### ✅ İYİ — Kısa ama yeterli context:
```
pulse1 volume skoru 10p üzerinden çok düz, volume spike tespiti ekle
```

### 🔥 EN İYİ — Niyet + bağlam:
```
pulse1'de ani hacim artışları (volume spike >2x) yakalayıp ekstra skor versin,
regime'e göre farklı yorumlasın (trend'de momentum, ranging'de breakout sinyali)
```

### Altın Kurallar:

1. **"Ne" değil "Neden" söyle** — Claude Code "neden"i bilirse "ne"yi
   kendisi genişletir
   ```
   ❌ "bir tablo ekle"
   ✅ "kullanıcılar son 24 saatteki sinyal performansını hızlıca görmek istiyor"
   ```

2. **Tek cümle yeter, ama niyet net olsun**
   ```
   ✅ "EMEL learning check'i gerçek trade sonuçlarından öğrensin"
   → Claude Code bunu alır, prediction_logs'u analiz eden, win rate hesaplayan,
     EMEL 8. kontrol noktasına feedback veren tam sistemi kurar
   ```

3. **Slash komutlarını kullan:**
   ```
   /compact     — context window dolduğunda sıkıştırır
   /init        — CLAUDE.md'yi yeniden yükler
   /cost        — maliyet takibi
   /clear       — context temizle
   ```

---

## 🔧 ADIM 5: Proje Bazlı Custom Komutlar

`.claude/commands/` klasörüne özel komutlar ekleyebilirsin:

### `.claude/commands/signal-check.md`
```markdown
Tüm 6 modelin (ML, PULSE 1/2/3, EMEL, SMC) sinyal üretim akışlarını
kontrol et. Her model için:
1. Endpoint'in çalışıp çalışmadığını test et
2. Son üretilen sinyali prediction_logs'tan çek
3. Confidence ve direction tutarlılığını kontrol et
4. Cache TTL'lerinin doğru olduğunu doğrula
Sonuçları tablo formatında özetle.
```

### `.claude/commands/add-feature.md`
```markdown
$ARGUMENTS içindeki özelliği ekle. Ekleme yaparken:
1. İlgili tüm dosyaları tara (backend service, router, frontend component)
2. Type tanımlarını güncelle (TypeScript + Python)
3. Supabase schema değişikliği gerekiyorsa migration yaz
4. Mevcut test'leri güncelle, yenilerini ekle
5. Cache invalidation gerekiyorsa uygula
6. İlgili endpoint'leri güncelle
7. Frontend'de state yönetimini güncelle
```

### `.claude/commands/debug-signal.md`
```markdown
$ARGUMENTS sembolü için sinyal debug yap:
1. EODHD'den gelen raw veriyi kontrol et
2. Her modelin ürettiği skoru ayrı ayrı göster
3. Regime detection sonucunu göster
4. Ensemble ağırlıklandırmasını trace et
5. Final sinyal + confidence hesaplamasını adım adım göster
6. prediction_logs'taki son 5 kaydı getir
```

Kullanım:
```
/signal-check
/add-feature volume spike detection for PULSE 1
/debug-signal NDX.INDX
```

---

## 🏆 ADIM 6: Claude Code'dan Maksimum Verimi Almanın 10 Püf Noktası

### 1. Her Oturumun Başında Context Ver
```
"Son oturumda PULSE 3'e order block entegrasyonu eklemiştik.
Şimdi EMEL'in 4. kontrol noktasını (pattern recognition) güçlendirelim."
```

### 2. Birden Fazla İş Tek Komutta
```
"PULSE 2'nin ATH protocol threshold'unu 42%'den 40%'a düşür,
frontend'de ATH badge'ini güncelle, ve bu değişikliğin backtest
etkisini prediction_logs'tan hesapla"
```

### 3. "Bak ve Öner" Komutları
```
"backend/services/ml_prediction_service.py'yi incele,
performans ve kod kalitesi açısından iyileştirme öner"
```

### 4. Refactoring İstekleri
```
"emel_pulse.py 2500+ satır olmuş, mantıksal modüllere ayır
ama hiçbir endpoint veya davranış değişmesin"
```

### 5. Test İstekleri
```
"PULSE 1 scoring sistemi için edge case testleri yaz —
özellikle RSI extreme değerlerinde ve regime geçişlerinde"
```

### 6. Supabase İşlemleri
```
"prediction_logs tablosuna model_version kolonu ekle,
migration yaz, backend'de loglama güncelle,
frontend stats'ta göster"
```

### 7. Debug İstekleri
```
"XAUUSD'de PULSE 3 sinyal üretmiyor,
1m→5m resample mantığından itibaren trace et"
```

### 8. Frontend Geliştirme
```
"sinyal kartlarına confidence breakdown ekle —
her modelin katkısı ayrı bar chart'ta görünsün"
```

### 9. Performance Optimizasyonu
```
"dashboard ilk yüklemesi yavaş, API çağrılarını
paralelize et ve skeleton loading ekle"
```

### 10. Dokümantasyon
```
"yeni eklediğimiz whale tracker endpoint'ini
API referansına ekle ve örnek response yaz"
```

---

## ⚠️ Dikkat Edilmesi Gerekenler

### Context Window Yönetimi
Claude Code'un bir oturumda tutabileceği bilgi sınırlı.
Uzun oturumlarda `/compact` komutuyla context'i sıkıştır.
Çok büyük dosyalar (emel_pulse.py gibi 2500+ satır) varsa
sadece ilgili bölümü referans göster.

### CLAUDE.md'yi Güncel Tut
Projeye yeni model, endpoint veya tablo eklediğinde
CLAUDE.md'yi de güncelle. Claude Code güncel olmayan
bilgiyle çalışırsa hatalı cascade yapabilir.

```
"CLAUDE.md'yi güncelle: yeni eklediğimiz whale_v2 endpoint'ini
API referansına ekle"
```

### Hata Durumunda
Claude Code hata yaparsa, hatayı açıklayıp düzeltmesini iste:
```
"Bu değişiklik regime service'i bozdu çünkü
ADX hesaplaması artık None dönüyor. Düzelt ve
None case'ini handle et"
```

---

## 📊 Önerilen Günlük Workflow

```
Sabah:
  1. claude "dün yapılan değişiklikleri özetle ve bugün ne yapmamız lazım"
  2. claude "tüm testleri çalıştır, kırılan var mı?"

Geliştirme:
  3. Kısa, net komutlarla feature ekle/düzelt
  4. Her büyük değişiklikten sonra: "etkilenen tüm dosyaları kontrol et"

Akşam:
  5. claude "bugün yapılanları commit mesajlarıyla özetle"
  6. claude "CLAUDE.md'yi bugünkü değişikliklere göre güncelle"
```

---

## 🔗 Faydalı Kaynaklar

- Claude Code Dökümantasyonu: https://docs.claude.com
- CLAUDE.md Best Practices: https://docs.claude.com/en/docs/claude-code
- Slash Commands: Terminalde `/help` yaz
- Anthropic Community: https://community.anthropic.com
