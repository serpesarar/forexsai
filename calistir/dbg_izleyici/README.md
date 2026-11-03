# DBG 303733 canlı izleyici (salt-okuma)

Başkasının botunu (DBG 303733, magic 6686) izler. Emir göndermez, şifre işlemez, kendi kenarımız değildir.
Amaç mekanizma: TP değişiklik anı, sessizlik anındaki hesap durumu, ayar değişimleri, DBG fiyatıyla klon kıyası, ham tick arşivi.

## Kutudaki düzen

| terminal | hesap | kim kullanıyor |
|---|---|---|
| `C:\Program Files\Pepperstone MetaTrader 5` | Pepperstone demo | bot, decider, kaydedici, VIX, ajan, DBG klon gölge |
| `C:\Program Files\MetaTrader 5` | DBG 303733 (investor) | yalnız bu izleyici |

- MT5 Python her süreci tek terminale bağlar. Birlikte çalışmanın şartı, **her sürecin terminal yolunu vermesi**.
- Ajan da artık yolla bağlanıyor (`agent_config.MT5_TERMINAL_PATH`); yanlışlıkla DBG'ye takılırsa bağlantıyı kapatır.
- Yolsuz `mt5.initialize()` çağıran araştırma betikleri (`backend/research/*`) DBG terminali açıkken yanlış hesaba bağlanabilir.
  Kutuda çalıştırılacaksa `MT5_TERMINAL_PATH` verilmeli ya da sonuçtaki hesap kontrol edilmeli.

## Çalışma

- Başlatıcı `calistir/23_dbg_izleyici.bat`. Ajan denetiminde: süreç yoksa ya da log 15 dk sessizse yeniden başlatır.
- Terminal kapalıysa izleyici açar; giriş terminalde kayıtlı oturumla olur.
- Bilerek durdurmak: önce bu klasöre `DBG_IZLEYICI_DURDUR` dosyası yazın.
- Veri: `%LOCALAPPDATA%\dbg_izleyici\` (OneDrive dışında): `dbg_izleyici_log.jsonl`, `ticks\YYYYMMDD.csv.gz`.
- Özet: `python calistir\dbg_izleyici\dbg_izleyici_ozet.py [YYYY-MM-DD]`

## Kayıtlı oturum düşerse

Logda `baglanti_yok` sürer ya da `reddedildi` görünür. Kullanıcı terminalde Dosya → Hesap Aç'tan investor şifresiyle girer ve "şifreyi kaydet"i işaretler.
Şifre betiğe, sohbete ya da `remote.py` kuyruğuna yazılmaz: kuyruk Supabase'de düz metin saklanır.

## Geçmiş tick pencereleri

`kutu_tick_aktar.py` + `tick_pencereleri.csv`: ilk ayrışma çevresindeki 149 pencere (`research/dbg_xau_ilk_ayrisma_20261030/`).

    python kutu_tick_aktar.py --terminal "C:\Program Files\MetaTrader 5\terminal64.exe" --pencereler tick_pencereleri.csv --cikis "%LOCALAPPDATA%\dbg_izleyici\pencereler"
