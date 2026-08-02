-- Notlama ekseni onarımı + karar dayanıklılığı (2026-08-02).
--
-- Neden (denetim, bkz. backend/data/evolution/analyst_reports/bias_karne_denetimi_2026-08-02.md):
--  1) ret_* kolonlarının 47 yönlü satırın 40'ında değeri yanlıştı — mumlar
--     2026-07-28'de broker-saati kaymasından onarıldı ama bu kolonlar onarımdan
--     ÖNCE hesaplanıp dondu. İmza: kayıtlı ret_240m = gerçek ret_60m (180 dk).
--  2) Çapa (`raw_payload.price_at_decision`) NDX 08:00 ET koşusunda bir önceki
--     seans kapanışıydı (~16 saat bayat). Çapa artık karar anındaki son KAPALI
--     5m barın kapanışı; p0 yalnız tazelik teşhisi olarak saklanır.
--
-- Uygula: mcp apply_migration "bias_grading_axis_repair"

-- Notlamanın hangi fiyata dayandığı artık satırda görünür (denetlenebilirlik).
alter table bias_test_log add column if not exists anchor_price   double precision;
alter table bias_test_log add column if not exists anchor_source  text;
-- Karar anındaki payload fiyatının gerçek bara göre sapması (%). Büyükse
-- tartışma motoru bayat fiyatla karar vermiş demektir — kararın kendisi şüpheli.
alter table bias_test_log add column if not exists p0_stale_pct   double precision;

-- "Karar kaça kadar doğru kalıyor?" bloğu. Şema:
--   { "clock_ny": {"10:00": 0.12, ...},   -- NY duvar saatinde işaretli getiri
--     "peak":  {"min": 120, "pct": 0.83},  -- lehte en iyi an
--     "trough":{"min": 30,  "pct": -0.41}, -- aleyhte en kötü an
--     "first_target_min": 95,              -- CIO'nun kendi hedef seviyesine ilk temas
--     "first_invalid_min": null,           -- geçersizleşme seviyesine ilk temas
--     "alive_until_min": 240,              -- yön kesintisiz lehte kaldığı son ufuk
--     "flip_at_min": 300 }                 -- lehteyken ilk kez aleyhe döndüğü an
alter table bias_test_log add column if not exists durability jsonb;

-- Yeniden notlamanın ne zaman yapıldığı (07-28 öncesi değerlerden ayırt etmek için).
alter table bias_test_log add column if not exists regraded_at timestamptz;

create index if not exists idx_bias_test_log_regraded on bias_test_log (regraded_at);
