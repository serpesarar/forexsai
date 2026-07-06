# MiroShark → ForexSAI — Günlük NASDAQ Bias Köprüsü (Kurulum)

MiroShark her gün bir kez CIO ajanıyla NASDAQ günlük bias'ı (bullish / bearish /
neutral / choppy) üretir. Bu bias ForexSAI'ye aktarılıp `daily_bias` tablosuna
yazılır ve Precision Veto Engine tarafından **yumuşak** bir güven ayarı olarak
kullanılır (asla sert override değil — MiroShark günde 1 kez çalışır, gün içi
fiyat aksiyonu her zaman önceliklidir). **Sadece NASDAQ (NDX.INDX) etkilenir.**

---

## 1. Ortak WEBHOOK_SECRET üret

Güçlü, rastgele bir değer üret (bir kez, iki tarafa da aynısını koyacaksın):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 2. MiroShark `.env` (webhook gönderen taraf)

MiroShark'ın `.env` dosyasına ekle:

```
WEBHOOK_URL=https://<forexsai-backend-url>/api/miroshark/webhook
WEBHOOK_SECRET=<1. adımdaki değer>
# Sadece tamamlanmış simülasyonlarda tetikle:
WEBHOOK_EVENTS=simulation.completed
```

MiroShark isteği şöyle imzalamalı (Stripe/GitHub şeması):

```
X-MiroShark-Signature: sha256=<hmac_sha256(secret, raw_body)>
```

## 3. ForexSAI `.env` (webhook alan taraf)

ForexSAI backend `.env` dosyasına **aynı** secret'i ekle:

```
WEBHOOK_SECRET=<1. adımdaki değer>
```

Bu değer `backend/config.py` içinde `settings.miroshark_webhook_secret` olarak
okunur. Secret tanımlı değilse `/webhook` endpoint'i 503 döner (sessizce kabul
etmez).

---

## Endpoint'ler

| Method | Path | Açıklama |
|--------|------|----------|
| `POST` | `/api/miroshark/webhook` | İmzalı push (üretim yolu). İmza geçersiz → 401, JSON bozuk → 400, DB yazılamadı → 503. |
| `POST` | `/api/miroshark/manual-bias` | İmzasız fallback — MiroShark UI'dan (:3000) çıkan JSON'u elle yapıştır. Aynı UPSERT. |
| `GET`  | `/api/miroshark/current-bias?symbol=NDX.INDX` | Bugünkü bias veya `{"bias": null, "status": "no_bias_today"}`. |

Aynı gün ikinci kez gelen bias **UPSERT** ile mevcut satırı günceller
(`bias_date` + `symbol` unique) — tek kayıt kalır.

## Beklenen CIO payload'ı (esnek parse)

Parser hem düz hem `cio_final` / `result` / `data` altında sarılı gövdeyi kabul
eder; bilinmeyen alanlar `raw_payload` içinde saklanır. Tek zorunlu alan bias
yönüdür.

```json
{
  "nasdaq_daily_bias": "bullish",
  "confidence": 72,
  "expected_close": "positive",
  "trade_mode": "buy_dips_only",
  "risk_level": "medium",
  "main_support": 20150.0,
  "main_resistance": 20520.0,
  "invalid_if": "NQ breaks below premarket low",
  "reason_summary": "...",
  "agent_agreement": "high",
  "risk_flags": ["cpi_tomorrow"],
  "debate_winner": "bull"
}
```

## Manuel test (secret ayarlıysa)

```bash
SECRET="<WEBHOOK_SECRET>"
BODY='{"nasdaq_daily_bias":"bullish","confidence":72,"trade_mode":"buy_dips_only","main_support":20150,"main_resistance":20520,"invalid_if":"break premarket low"}'
SIG="sha256=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')"
curl -sS -X POST http://localhost:8000/api/miroshark/webhook \
  -H "Content-Type: application/json" \
  -H "X-MiroShark-Signature: $SIG" \
  -d "$BODY"

curl -sS "http://localhost:8000/api/miroshark/current-bias?symbol=NDX.INDX"
```
