# KSG OPEX vetosunu canlı KSG'ye bağlama — canlı kodla yeniden oynatma — ÖN KAYIT (2026-11-19, sonuçlardan önce)

## Kaynak
Devir raporu §6/2. Defter §2.94 GX-05: canlı KSG girişini OPEX'e 0–2 işlem günü kala açmamak **B** (kart `ndx_ksg_opex_vetosu` 6/6,
bağımsız 6/6 besleme eksi −9…−22 bp, havuz P 1,00; Duka vetolanan −4,7 bp P 0,77). Bu sınama tekrarlanmaz (3. KURAL).

## Yeni olan (bağlamadan önce)
1. **Canlı kodla birebir oynatma:** `yeni deneme/ksg_live.find_signal` (O16/O15 − 1 < 0, ≥ 12 seans barı) + `exit_due` (ertesi işlem günü
   09:30 ET) + VIX ≥ 25'te çift lot (`entry_lot`, dünkü VIX kapanışı). Veto takvimi `yeni deneme/korku_live.opex_veto` (canlıya girecek
   fonksiyonun kendisi). Besleme: MT5 NAS100 M30 (canlı broker) ve Dukascopy NDX 1m → 30 dk, 2018-05 → 2026-11-05.
   Giriş 16:00 barı açılışı + spread (MT5 `sp`, Duka `sp`), çıkış 09:30 barı açılışı, finansman.
2. **Kitap etkisi:** lot ağırlıklı gece P&L'i (1 ya da 2 birim) vetolu / vetosuz; yıllık toplam bp, gece başına Sharpe (yıllık), maks. düşüş.
3. **Yoğunlaşma:** vetolanan gecelerin kaçında canlı KORKU (T30) da sinyal verirdi (KORKU zaten aynı günlerde vetolu) ve C3b ile çakışma — betimleyici.

## Geçme ölçütü (bağlama önerisi)
- Vetolanan gecelerin lot ağırlıklı ortalaması < 0 **her iki beslemede** ve iki yarıda (2018-05…2022-06 / 2022-07…2026-11) en az birinde < 0, diğerinde ≤ +3 bp.
- Vetolu kitabın yıllık Sharpe'ı vetosuzdan **düşük değil** (iki beslemede) ve yıllık toplam bp kaybı vetolananların toplamından fazla değil.
- Sağlanırsa: `ksg_live`'a `config.KSG_OPEX_VETO` (varsayılan True) ile veto eklenmesi önerilir; bağlama kullanıcı onayıyla.
- Sağlanmazsa: B kalır, bağlanmaz; nedeni yazılır.
