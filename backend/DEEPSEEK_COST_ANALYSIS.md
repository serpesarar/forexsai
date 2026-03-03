# DeepSeek API Maliyet Analizi

## Fiyatlandırma (Güncel)
- 1M Input Tokens (Cache Hit): $0.028
- 1M Input Tokens (Cache Miss): $0.28
- 1M Output Tokens: $0.42

---

## DeepSeek Kullanan Paneller/Servisler

### 1. RSS NEWS AGGREGATOR (EN PAHALI)
**Dosya:** `services/rss_aggregator.py` → `news_analyzer_v2.py`

| Parametre | Değer |
|-----------|-------|
| Çalışma Sıklığı | Her 2 dakikada bir (120 sn) |
| Saatlik Çağrı | 30 çağrı |
| Günlük Çağrı | ~720 çağrı |
| Aylık Çağrı | ~21,600 çağrı |
| Input Token/Haber | ~2,000 (prompt + haber içeriği) |
| Output Token/Haber | ~800 (JSON yanıt) |

**Günlük Maliyet:**
- Input: 720 × 2,000 = 1.44M tokens × $0.28 = **$0.40**
- Output: 720 × 800 = 576K tokens × $0.42 = **$0.24**
- **Günlük: $0.64** | **Aylık: ~$19.20**

---

### 2. DEEPSEEK MASTER ANALYSIS
**Dosya:** `routers/deepseek_analysis.py` → `services/deepseek_analysis_service.py`

| Parametre | Değer |
|-----------|-------|
| Endpoint | `/api/deepseek/master/{symbol}` |
| Cache TTL | 30 dakika |
| Tahmini Kullanım | Kullanıcı başına 5-10 çağrı/gün |
| Input Token | ~3,000 (uzun prompt + veri) |
| Output Token | ~1,200 (detaylı analiz) |

**Maliyet (10 kullanıcı × 10 çağrı = 100 çağrı/gün):**
- Input: 100 × 3,000 = 300K tokens × $0.28 = **$0.08**
- Output: 100 × 1,200 = 120K tokens × $0.42 = **$0.05**
- **Günlük: $0.13** | **Aylık: ~$3.90**

---

### 3. CLAUDE SIGNAL ANALYZER (DeepSeek-R1)
**Dosya:** `services/claude_signal_analyzer.py`

| Parametre | Değer |
|-----------|-------|
| Kullanım | Her ML tahmininde (15 dk soğuma) |
| Tahmini | ~50 sinyal/gün |
| Input Token | ~2,500 |
| Output Token | ~1,000 |

**Maliyet:**
- Input: 50 × 2,500 = 125K tokens × $0.28 = **$0.035**
- Output: 50 × 1,000 = 50K tokens × $0.42 = **$0.021**
- **Günlük: $0.056** | **Aylık: ~$1.68**

---

### 4. SENTIMENT ANALYZER
**Dosya:** `services/sentiment_analyzer.py`

| Parametre | Değer |
|-----------|-------|
| Kullanım | Her haber için (duygu analizi) |
| Çağrı/ Gün | ~200 (RSS'ten gelen haberler) |
| Input Token | ~1,500 |
| Output Token | ~500 |

**Maliyet:**
- Input: 200 × 1,500 = 300K tokens × $0.28 = **$0.08**
- Output: 200 × 500 = 100K tokens × $0.42 = **$0.04**
- **Günlük: $0.12** | **Aylık: ~$3.60**

---

### 5. DETAILED AI ANALYSIS SERVICE
**Dosya:** `services/detailed_ai_analysis_service.py`

| Parametre | Değer |
|-----------|-------|
| Kullanım | Detaylı piyasa analizi (manuel) |
| Tahmini | ~20 çağrı/gün |
| Input Token | ~4,000 (çok uzun prompt) |
| Output Token | ~1,800 |

**Maliyet:**
- Input: 20 × 4,000 = 80K tokens × $0.28 = **$0.022**
- Output: 20 × 1,800 = 36K tokens × $0.42 = **$0.015**
- **Günlük: $0.037** | **Aylık: ~$1.11**

---

### 6. PATTERN ANALYZER
**Dosya:** `services/pattern_analyzer.py`

| Parametre | Değer |
|-----------|-------|
| Kullanım | Mum deseni analizi |
| Tahmini | ~30 çağrı/gün |
| Input Token | ~2,000 |
| Output Token | ~600 |

**Maliyet:**
- **Günlük: ~$0.04** | **Aylık: ~$1.20**

---

### 7. NEWS ANALYZER (Eski)
**Dosya:** `services/news_analyzer.py`

| Parametre | Değer |
|-----------|-------|
| Kullanım | Eski haber analizi (fallback) |
| Tahmini | ~100 çağrı/gün |

**Maliyet:**
- **Günlük: ~$0.08** | **Aylık: ~$2.40**

---

## TOPLAM MALİYET

| Servis | Günlük | Aylık |
|--------|--------|-------|
| RSS Aggregator | $0.64 | $19.20 |
| Master Analysis | $0.13 | $3.90 |
| Signal Analyzer | $0.06 | $1.68 |
| Sentiment Analyzer | $0.12 | $3.60 |
| Detailed AI | $0.04 | $1.11 |
| Pattern Analyzer | $0.04 | $1.20 |
| News Analyzer (Eski) | $0.08 | $2.40 |
| **TOPLAM** | **$1.11** | **~$33.00** |

---

## OPTİMİZASYON ÖNERİLERİ

### 1. RSS Aggregator - ÇEVİRİ ÖNBELLEĞİ (ÖNEMLİ)
**Problem:** Her haber için DeepSeek çağrısı çok pahalı

**Çözüm:** Benzer haberleri önbelleğe al
```python
# Aynı başlık pattern'i varsa çeviriyi tekrar kullan
if similar_title_cached:
    return cached_translation
```
**Tasarruf:** %30-40 ($10-15/ay)

---

### 2. Master Analysis - DAHA UZUN CACHE
**Problem:** 30 dakika cache çok kısa

**Çözüm:** 2 saat cache + piyasa açıkken sık, kapalıyken seyrek
**Tasarruf:** %50 ($2/ay)

---

### 3. Sentiment Analyzer - KALDIR
**Problem:** RSS zaten duygu analizi yapıyor, tekrar işlem

**Çözüm:** RSS'ten gelen sentiment'i kullan, ayrı çağrı yapma
**Tasarruf:** $3.60/ay (tamamen kaldırılabilir)

---

### 4. Cache Hit Oranını Artır
**Problem:** Her çağrı cache miss sayılıyor

**Çözüm:** Aynı haber/sembol için cache kullan
**Fiyat Farkı:** Cache hit $0.028 vs Cache miss $0.28 (10x daha ucuz!)

---

## OPTİMİZE EDİLMİŞ TAHMİNİ MALİYET

Optimizasyonlar sonrası:
- RSS: $19.20 → $12.00 (cache + önbellek)
- Master: $3.90 → $2.00 (uzun cache)
- Sentiment: $3.60 → $0.00 (kaldır)
- Diğerleri: $6.30 → $4.00 (cache)

**Yeni Toplam: ~$18/ay** (yerine $33)

---

## ACİL DURUM: BAKİYE BİTTİĞİNDE

DeepSeek bakiyen bittiği için şu an:
1. Tüm AI analizleri **FALLBACK** (rule-based) çalışıyor
2. Çeviriler kalitesiz (basit keyword replacement)
3. Analizler derin değil

### Seçenekler:

**A) DeepSeek Bakiye Yükle**
- Min: $5-10
- Aylık ihtiyaç: ~$20-30

**B) Claude'a Geç (Anthropic)**
- Claude 3 Haiku çok daha ucuz
- Daha iyi Türkçe çeviri
- Aylık: ~$10-15

**C) OpenAI GPT-4o-mini**
- En ucuz seçenek
- Aylık: ~$5-8

**D) Sadece Fallback Kullan**
- Ücretsiz
- Kalite düşük ama çalışır
