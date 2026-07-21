-- Shadow tracker: 'meta' (6-model core ensemble) üçüncü kaynak olarak eklendi.
-- Sadece CHECK kısıtı genişletilir — veri/indeks değişmez.
alter table public.shadow_pattern_trades
  drop constraint if exists shadow_pattern_trades_source_check;

alter table public.shadow_pattern_trades
  add constraint shadow_pattern_trades_source_check
  check (source in ('pattern', 'fakeout', 'meta'));
