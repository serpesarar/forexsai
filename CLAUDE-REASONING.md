# ForexSAI — Reasoning & Thinking Protocols

> Bu dosya CLAUDE.md tarafından otomatik okunur.
> Opus 4.8'in extended thinking kapasitesini en verimli şekilde kullanmak için
> somut düşünme protokolleri içerir.

---

## 🧠 Düşünme Tetikleyicileri — Ne Zaman Derinlemesine Düşün

**Her zaman derin düşün:**
- Birden fazla servisi etkileyen değişiklik (signal_lifecycle + prediction_logger + supabase)
- Yeni endpoint ekleme (CORS, auth, cache TTL, schema, frontend contract hepsi etkilenir)
- ML feature değişikliği (model retrain gerekir mi? backward compat? Supabase log şeması?)
- DataHub veya mt5_redis_client'a dokunma (tüm 6 model downstream etkisi)
- "Hızlıca şunu değiştir" gibi görünen ama cascade etkisi büyük olan talepler

**Kısa yoldan git (derin thinking israf):**
- Tek dosya, bağımsız utility fonksiyon
- Type fix / import düzeltme
- Tailwind class güncellemesi
- Log mesajı / comment değişikliği

---

## ✅ Pre-Edit Protokolü — Dosyaya Dokunmadan Önce

Her dosya değişikliğinden önce şu soruları içsel olarak yanıtla:

1. **Okudun mu?** — `Read` tool ile dosyanın güncel halini gör, hafızandan çalışma
2. **Kim çağırıyor?** — Bu fonksiyonu/endpoint'i kim import ediyor?
3. **Ne etkiliyor?** — Downstream'de ne kırılabilir?
4. **Type contract değişiyor mu?** — TypeScript interface güncellemesi gerekir mi?
5. **Supabase etkileniyor mu?** — Schema, migration, index değişikliği?
6. **Test edilebilir mi?** — Değişikliği nasıl verify edeceğim?

Cevaplarda belirsizlik varsa: önce `Bash` ile ilgili dosyaları tara, sonra düzenle.

---

## 🔍 Cascade Verification — Değişiklik Sonrası Kontrol

Bir değişiklik yaptıktan sonra sırayla kontrol et:

```
Değişiklik: [ne değişti]
  ↓
Backend etki: [hangi servisler etkilendi]
  ↓
Frontend etki: [hangi component/hook/type etkilendi]
  ↓
Supabase etki: [tablo/kolon/index değişikliği var mı]
  ↓
WebSocket etki: [broadcast payload değişti mi]
  ↓
Signal lifecycle etki: [aktif sinyaller etkileniyor mu]
```

Bu zincirde herhangi bir halka "evet" dönerse → o halkayı da güncelle.

---

## 📐 Epistemik Kalibrasyon — Ne Zaman Sor, Ne Zaman Devam Et

**Devam et (sor ma):**
- Cevabı CLAUDE.md'den veya proje mantığından çıkarabiliyorsan
- Değişiklik tek dosyayla sınırlıysa
- Pattern zaten kodda mevcut ve aynısını uyguluyorsan

**Dur ve sor:**
- İki farklı yaklaşım eşit derecede makul görünüyorsa (farklı trade-off'lar)
- Silme/refactor işlemi geriye döndürülemezse
- Production data'ya (Supabase) dokunacaksan
- "Bu değişiklik başka bir şeyi kırar mı?" sorusuna kesin cevap veremiyorsan

**Asla tahmin etme:**
- Environment variable değerleri
- Supabase schema'nın güncel hali (önce `Execute SQL` ile bak)
- Redis'te hangi key'lerin mevcut olduğu
- Hangi sinyallerin şu an aktif olduğu

---

## 🛡️ Hata Önleme Reflexleri

### Yeni Kod Yazmadan Önce
```python
# Şunu sormadan geçme:
# - Bu pattern kodda başka nerede var? (tekrar etme, merge et)
# - Bu async mi olmalı? (FastAPI context'inde evet, neredeyse her zaman)
# - Exception bu fonksiyonun içinde mi handle edilmeli yoksa yukarıya mı fırlatılmalı?
# - Bu değer None olabilir mi? (None check ekle)
# - Bu bir N+1 query mi yaratıyor? (batch al)
```

### Supabase'e Yazarken
- `INSERT` yerine `UPSERT` düşün (idempotency)
- Batch insert tercih et (tek tek döngü değil)
- `created_at` alanı otomatik mi, yoksa sen mi set edeceksin?
- RLS politikası bu işlemi bloklar mı?

### Frontend'de Component Yazarken
- `loading` state yok mu? → Ekle
- `error` state yok mu? → Ekle
- `empty` state (veri boş gelirse) yok mu? → Ekle
- API çağrısı direkt component'te mi? → Service layer'a taşı

---

## 🎯 Kalite Standartları — Her Çıktıda Geçerli

### "Bitti" Ne Demektir?
Bir görev ancak şunların tamamı sağlandıysa bittir:
- ✓ Ana işlevsellik çalışıyor
- ✓ Error case'ler handle ediliyor (try/except + logging)
- ✓ Type tanımları güncel (Python type hints, TypeScript interface)
- ✓ Cascade etkiler taşındı (bağımlı dosyalar güncellendi)
- ✓ Magic number'lar constant olarak tanımlandı
- ✓ Production'da kalmaması gereken debug print/log'lar temizlendi

### Kısmi Çıktı Verme
Eğer bir görevin tamamını yapamıyorsan (context limit, belirsizlik, vb.):
- Ne yapıldığını net yaz
- Ne eksik kaldığını ve neden söyle
- Bir sonraki adımı kullanıcının verebileceği en kısa komut olarak öner

---

## 💬 Hata ve Geri Bildirim Yönetimi

- Hata yaparsan: kabul et, analiz et, düzelt — aşırı özür döngüsüne girme
- Kullanıcı kısa/belirsiz bir komut verirse: önce en makul yorumla uygula, sonra "Bunu X olarak yorumladım, doğru mu?" diye sor
- Birden fazla makul yaklaşım varsa: "A daha hızlı ama B daha güvenli" gibi trade-off'u özetle, karar kullanıcıya bırak
- Bir şeyin neden yanlış olduğunu düşünüyorsan: kibarca ama net söyle, "emin değilim ama" kalıbına kaçma

---

## ⚡ ForexSAI Spesifik Hızlı Kurallar

| Durum | Doğru Davranış |
|-------|----------------|
| "Şunu ekle" → etkisi büyük | Önce cascade haritasını çiz, sonra yaz |
| ML feature değişikliği | model retrain gerekip gerekmediğini belirt |
| Yeni Supabase kolonu | Migration dosyası oluştur, index'i unutma |
| signal_lifecycle.py değişikliği | 2dk interval mantığını koru, test et |
| DataHub'a yeni field | mt5_redis_client'ın onu set edip etmediğini kontrol et |
| Frontend yeni API call | Backend endpoint'in response schema'sı önce |
| Cache TTL değişikliği | CLAUDE.md'deki Cache TTL tablosunu güncelle |
| market_closed_invalid oranı arttı | signal_lifecycle.py:593 MCI gate'e bak |
