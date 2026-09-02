"""phase_rules.py — 2026-08-14 karşı-olgusal denetiminin kural motoru (SAF).

Bu modül MT5'e, config'e veya ağa BAĞLI DEĞİLDİR: yalnız sayı alır, karar
döndürür. Böylece Mac'te (MetaTrader5 paketi olmadan) pytest ile test edilir ve
kutuda bot tarafından çağrılır. Bot tarafı yalnız "veriyi topla → bu fonksiyonu
çağır → logla/uygula" yapar.

Kaynak analiz: 1MDATA/mt5_islem_analizi/ (133 NASDAQ işlemi, 33.353 adet 1m bar,
bar-bar karşı-olgusal simülasyon; iki bağımsız model + iki tur çapraz hakemlik).

BAYRAK FELSEFESİ: her kural ayrı bayrak, VARSAYILAN = ESKİ DAVRANIŞ.
Yalnız Faz-0 bayrakları açık teslim edilir (kullanıcı kararı). Bayraklar kutudaki
`config.py`'den okunur; `scripts/bot_flags.py` ile tek komutla açılıp kapanır.

⚠️ KANIT SINIRI: tüm eşikler TEK AYLIK (13 Tem – 13 Ağu 2026) veriden çıkarıldı
ve aynı veri üzerinde optimize edildi. Karşı-olgusal WR'lar (%81.7 / %88.9) örneklem
İÇİ değerlerdir; canlıda bu kadar yüksek çıkmasını BEKLEME. Bayrakların amacı
canlı ölçümü mümkün kılmak — kanıtı ilan etmek değil.
"""
from __future__ import annotations

import math
from datetime import datetime, time as dtime, timezone
from typing import Iterable, Optional, Sequence

# ── Varsayılanlar (bot config'i bunları ezer) ───────────────────────────────
DEFAULTS: dict[str, object] = {
    # FAZ 0 — çıkış tarafı; girişe dokunmaz
    "MGMT_BE_MODE": "conditional_mfe",   # "time30" = eski davranış
    "MGMT_BE_MFE_R": 0.5,                # MFE ≥ 0.5×SL mesafesi → BE
    # ⚠️ 2026-08-15 DIŞ-ÖRNEKLEM'DE ELENDİ → varsayılan KAPALI (0).
    # Plan 120 dk diyordu; iç-örneklemde 120 zararlı, 240 iyiydi. Kuraldan ÖNCEKİ
    # dönemde (2026-06-29→07-12, n=123 NASDAQ) ise 240 dk tek başına net'i
    # +1.607$ → −293$ yaptı (−1.900$). İç-örneklemde +760$. İki dönemin toplamı
    # negatif ve işaret kararsız → açılmıyor. Kanıt: backend/research/box_phase_oos.py
    "MGMT_TIME_STOP_MIN": 0,             # 240 = zombi koruması (kanıtı zayıf)
    "MGMT_TIME_STOP_SYMBOLS": ("NDX.INDX",),
    # ⚠️ 2026-08-15 DIŞ-ÖRNEKLEM'DE ELENDİ → varsayılan "fixed".
    # ATR70 hedefi kazanma oranını İKİ dönemde de yükseltiyor (OOS %58.5→%67.5,
    # iç %61.0→%72.8) ama PARAYI yalnız iç-örneklemde artırıyor: OOS +1.607$ →
    # +1.396$ (−211$), iç +2.842$ → +4.780$ (+1.938$). Çarpanı 4.0'a çıkarmak da
    # kurtarmıyor (OOS −216$). DAX/petrolde de aynı desen: WR ↑, para ↓.
    # Yani küçük hedef "yüksek WR" kozmetiği üretiyor, kenar üretmiyor.
    "TP_MODE": "fixed",                  # "atr" = 2.5×ATR70(1m) deneyi
    "TP_ATR_MULT": 2.5,
    "TP_ATR_PERIOD": 70,                 # 1m bar
    "TP_ATR_SYMBOLS": ("NDX.INDX",),
    "TP_ATR_EXCLUDE_SCOPES": ("DAYCOMBO",),   # scope_key son eki
    # ⚠️ EKLEME (planda yoktu — canlı duman testi zorunlu kıldı): ATR70 ölü
    # saatlerde çöküyor. 2026-08-14 22:02 UTC'de ATR70=4.8pt → TP 12pt / SL 110
    # = RR 0.11 (başabaş WR %90 + spread hedefin ~%15'ini yer). Örneklemde de
    # 133 işlemin 35'i RR<0.30 idi. Taban = TP en az bu kadar × SL mesafesi.
    # Taban taraması (aynı 133 işlem): 0.0→+2.678$ · 0.2→+3.827$ · 0.3→+4.110$ ·
    # 0.4→+3.793$ · 0.5→+500$ · 0.6→−6.219$. Yasak listesindeki "min TP 66pt"
    # tam olarak 0.6 tabanına denk geliyor ve gerçekten felaket — 0.3 ondan
    # çok uzakta ve her spread varsayımında (0/1.5/3pt) tabansızdan İYİ.
    "TP_ATR_MIN_R": 0.3,                      # 0 = taban yok (plandaki hâli)
    # FAZ 1 — varsayılan KAPALI (Faz-0 go/no-go sonrası açılır)
    "NDX_SESSION_BLOCK_ENABLED": False,
    "NDX_SESSION_BLOCK": (("22:00", "07:00"),),
    "NDX_FRIDAY_BLOCK": False,
    "NDX_WEEKEND_HOLD_BLOCK": False,     # Cuma 20:45 UTC sonrası yeni giriş yok
    "NDX_WEEKEND_HOLD_FROM": "20:45",
    "NDX_SR_ENTRY_ENABLED": True,        # False → 1m S/R limit kolu kapalı
    "PHASE1_CONFIG_RESTORE": False,      # ONLY_CONFIRM=True + ZONE_MIN_TOUCH=4
    # FAZ 2 — gölge (ölç, bloklama)
    "POS_TIGHT_ENABLED": True,
    "POS_TIGHT_BLOCK": False,
    "POS_TIGHT_SELL_MIN": 0.60,
    "POS_TIGHT_BUY_MAX": 0.40,
    "SELL_RSI_SHADOW_ENABLED": True,
    "SELL_RSI_MIN": 55.0,
    # FAZ 3 — MOD-E probasyon: sinyalden 5 bar sonra, gürültü bandı geçilmediyse gir.
    # Dış-örneklem doğrulaması (2026-08-15) bunu Faz-0'ın elenen kurallarının
    # AKSİNE iki dönemde de pozitif buldu (dış +3.691$ / iç +7.582$, n=112/126).
    # Canlı icra: probation_exec.py. Varsayılan KAPALI kalır (geri alma güvencesi);
    # kutuda `scripts/bot_flags.py phase3 live` ile açılır.
    "PROBATION_SHADOW_ENABLED": True,    # canlıyken otomatik susar
    "PROBATION_LIVE": False,             # True → emir 5 bar geciktirilir
    "PROBATION_SYMBOLS": ("NDX.INDX",),  # kanıt yalnız NASDAQ'ta
    "PROBATION_BARS": 5,
    "PROBATION_Z": 1.28,
    "PROBATION_MAX_WAIT_MIN": 15,        # bu kadar sürede karara varılamazsa iptal
    # ── RE-ENTRY (2026-08-20): ana işlem kapanınca aynı yönde bir kez daha gir.
    # Üç kapılı sınav (bkz. reentry_exec.py başlığı):
    #   bağımsızlık ✅ (iç %55 / dış %53 örtüşme — piramitte %94'tü)
    #   eşit-risk alfa ✅ (iç +12.462$ / dış +3.850$)
    #   plasebo ❌ dış-örneklemde geçilemedi (p=0.187; iç p=0.000)
    # → VARSAYILAN GÖLGE. 2-4 hafta gölge verisinden sonra "live" yapılır.
    "REENTRY_MODE": "shadow",            # "off" | "shadow" | "live"
    "REENTRY_SYMBOLS": ("NDX.INDX",),    # kanıt yalnız NASDAQ'ta
    "REENTRY_DELAY_TP_MIN": 5,
    "REENTRY_DELAY_SL_MIN": 1,
    "REENTRY_MAX_WAIT_MIN": 20,          # bu süreyi aşan niyet iptal
    # ── USOIL BUY hedef mesafesi (2026-08-20 derin sınama) ──────────────────
    # v3 raporu "TP=0,6R" önerdi; 17 aylık dış-örneklem TERSİNİ söylüyor.
    # Botun USOIL:BUY momentum koşullarıyla üretilen 2.025 sızıntısız hipotetik
    # giriş (5m, spread 0,03, giriş = sinyal barı KAPANIŞI, çözüm SONRAKİ
    # barlardan), işlem başı net:
    #   RR 0,40 −2,3$ · 0,60 +9,3$ · 0,70 (BUGÜNKÜ) +11,2$ · 0,80 +20,2$
    #   RR 1,00 +34,0$ · 1,25 +30,4$ · 1,50 +32,2$ · 2,00 +29,1$
    # RR 1,00 mevcut ayarı HER kesitte geçiyor: kronolojik 1. yarı (−7,6$ vs
    # −17,0$), 2. yarı (+75,7$ vs +39,4$), 18 ayın 12'si, sürtünme ×1,5
    # (+24,7$ vs +4,2$), "aynı anda tek pozisyon" kısıtı (+21,9$ vs +5,8$) ve
    # canlı konum kapısı altında (pos≤0,60: +71,5$ vs +43,4$, n=153).
    # Bootstrap P(EV>0)=%99,6. Plato 0,80–2,00 geniş; uçurum 0,70'in ALTINDA.
    # ⚠️ Scope'un KENDİSİ 1. yarıda negatif (hangi RR olursa olsun) — bu yüzden
    # varsayılan KAPALI: kanıt "RR 1,0 > RR 0,7" için güçlü, "scope her rejimde
    # kârlı" için değil. Açmak: config'e USOIL_BUY_TP_RR = 1.0.
    # Kanıt: backend/research/box_usoil_tp_stability.py + box_usoil_pos_tp.py
    "USOIL_BUY_TP_RR": 0.0,              # 0 = kapalı (%1,04 sabit hedef sürer)
    "USOIL_BUY_TP_SYMBOLS": ("USOIL.FOREX",),
    # Opsiyonel (etkisi nötr ölçüldü)
    # ── FAZ 3 (2026-08-28) — ATR SIKIŞMA FİLTRESİ ────────────────────────
    # Kaynak: dış AI'ın "SL adli tıp" raporu; 120 günlük SIZINTISIZ dış-örneklemde
    # DOĞRULANDI (analyst_reports/sikisma_filtresi_denetimi_2026-08-28.md).
    # Hipotez: ATR14(1m) son 100 dakikanın ortalamasının altındaysa (sıkışma),
    # sinyali doğuran kıpırtı likidite fitilidir — giriş elenmeli.
    #   eşik 1.00'da ELENECEK işlemler: DIŞ n=122 ortR −0.070 / −4.399$
    #                                    İÇ  n= 11 ortR −0.292 / −1.028$
    #   kalan küme:                      DIŞ n=132 ortR +0.111 / +6.802$ (baz +0.024)
    #   4 ailenin 4'ünde de aynı yön (CHREV −0.216, MOM/SR −0.150, VIXREG −0.058).
    # ⚠️ NEDEN GÖLGE: (a) koşullu plasebo YALNIZ 1.00'da geçti (p=0.043;
    # 0.95→0.217, 1.05→0.073) — komşu eşiklerde geçmemesi sınırda etki imzası;
    # (b) 3. kronolojik çeyrek filtreyle de negatif kalıyor (−0.093 → −0.065).
    # Kart ölçüt-3 geçilmeden SQZ_FILTER_BLOCK açılmaz.
    "SQZ_FILTER_ENABLED": True,              # ölç + gölge logla
    "SQZ_FILTER_BLOCK": False,               # True → gerçekten bloklar
    "SQZ_FILTER_MIN": 1.00,                  # ATR14(1m)/ATR100(1m) alt sınırı
    "SQZ_FILTER_SYMBOLS": ("NDX.INDX",),     # kanıt yalnız NASDAQ'ta
    # ── FAZ 3b (2026-08-30) — CUMA ÖĞLEDEN SONRA GİRİŞ BLOĞU ─────────────
    # İki bağımsız ajan doğruladı. GERÇEKLEŞEN para (simülasyon değil), 282 NAS100:
    #   Cuma ≥12 UTC : n=24  −4.050$  (dış AI −4.091$ ile uyumlu)
    #   Cuma <12 UTC : n=16  +48$     → hasar tamamen öğleden sonra
    #   en kötü hücre: Cuma 15 UTC, n=9, −3.557$
    # Koşullu plasebo (5.000 rastgele eşit-büyüklükte blok): p=0,0150 GEÇTİ.
    # ── 2026-08-30 CANLIYA ALINDI — 5 bağımsız test geçildi ────────────────
    #  1) Permutasyon testi (20.000 karıştırma): kalan ortR +0,071 vs elenen
    #     −0,349, fark +0,420 → p=0,0146 GEÇTİ
    #  2) Eşik platosu: 10,11,12,13,14,15 UTC'nin HEPSİ +6.9k…+8.3k (filtresiz
    #     +4.290) → tek bir sihirli saate bağlı DEĞİL, geniş plato
    #  3) Hafta-çıkarma: 9 haftanın 9'unda da filtre bazı geçiyor
    #  4) Aile kırılımı: 5 scope'un 4'ünde pozitif (yalnız DAYCOMBO −123, n=19)
    #  5) Hacim: kalan n=258 ≥ 150 ✓ · davranış değişikliği yalnız %8,5 (24/282)
    #  Ayrıca iki bağımsız ajan aynı sayıyı buldu (−4.050$ / −4.091$).
    #  ⚠️ SINIR: kanıt NASDAQ'a özgü. Çapraz-sembol testinde GER40'ta Cuma ≥12
    #  POZİTİF çıktı (+1.047$, n=7) → başka sembole GENELLEME YAPILMAZ.
    #  Bu, TQ_FRIDAY_COOL'un (soğutma) tam bloğa yükseltilmesidir.
    "FRIDAY_BLOCK_ENABLED": True,            # ölç + logla
    "FRIDAY_BLOCK_LIVE": True,               # CANLI: gerçekten bloklar
    "FRIDAY_BLOCK_FROM_HOUR": 12,            # UTC
    "FRIDAY_BLOCK_SYMBOLS": ("NDX.INDX",),   # kanıt yalnız NASDAQ'ta
    "SCOPE_LOSS_COOLDOWN_ENABLED": False,
    "SCOPE_LOSS_COOLDOWN_MIN": 120,
    "SCOPE_LOSS_COOLDOWN_STREAK": 2,
}


def flag(config, name: str):
    """config.<name> varsa onu, yoksa DEFAULTS[name] döndür."""
    if config is not None and hasattr(config, name):
        return getattr(config, name)
    return DEFAULTS[name]


# ── Yardımcı: sembol/scope eşleme ───────────────────────────────────────────

def _in(value: str, items: Iterable[str]) -> bool:
    return any(value == x for x in items)


def scope_suffix(scope_key: str) -> str:
    """'NDX.INDX:BUY:DAYCOMBO' → 'DAYCOMBO'; 'NDX.INDX:BUY' → ''."""
    parts = scope_key.split(":")
    return parts[2] if len(parts) > 2 else ""


# ═══ FAZ 0.3 — TP geometrisi (ATR70 1m) ════════════════════════════════════

def true_ranges(bars: Sequence[dict]) -> list[float]:
    """TR listesi (ilk bar hariç). bars: [{"high","low","close"}, ...] eski→yeni."""
    out: list[float] = []
    for i in range(1, len(bars)):
        h, l = float(bars[i]["high"]), float(bars[i]["low"])
        pc = float(bars[i - 1]["close"])
        out.append(max(h - l, abs(h - pc), abs(l - pc)))
    return out


def atr_simple(bars: Sequence[dict], period: int) -> Optional[float]:
    """Son `period` barın ortalama true range'i (basit ortalama).

    Analizde "ATR70(1m) = ~70 barlık ortalama true range" olarak tanımlandı;
    Wilder yumuşatması DEĞİL, düz ortalama kullanılır (tanımla birebir)."""
    if not bars or len(bars) < period + 1:
        return None
    trs = true_ranges(bars)[-period:]
    if not trs:
        return None
    atr = sum(trs) / len(trs)
    return atr if atr > 0 else None


def tp_distance(scope_key: str, forexsai_sym: str, bars_1m: Optional[Sequence[dict]],
                fixed_tp_dist: float, config=None,
                sl_dist: float | None = None) -> tuple[float, str]:
    """(tp_mesafesi, kaynak). Kapsam dışı / veri yoksa sabit değere düşer (fail-open).

    Kapsam: TP_MODE='atr' + sembol TP_ATR_SYMBOLS içinde + scope son eki
    TP_ATR_EXCLUDE_SCOPES'ta DEĞİL (DAYCOMBO muaf — kendi geometrisi sağlıklı).

    sl_dist verilirse TP_ATR_MIN_R tabanı uygulanır (ölü saatte RR 0.11 koruması).
    """
    if str(flag(config, "TP_MODE")).lower() != "atr":
        return fixed_tp_dist, "fixed"
    if not _in(forexsai_sym, flag(config, "TP_ATR_SYMBOLS")):
        return fixed_tp_dist, "fixed_scope_out"
    if _in(scope_suffix(scope_key), flag(config, "TP_ATR_EXCLUDE_SCOPES")):
        return fixed_tp_dist, "fixed_scope_excluded"
    atr = atr_simple(bars_1m or [], int(flag(config, "TP_ATR_PERIOD")))
    if atr is None:
        return fixed_tp_dist, "fixed_no_atr"
    dist = float(flag(config, "TP_ATR_MULT")) * atr
    if dist <= 0:
        return fixed_tp_dist, "fixed_bad_atr"
    min_r = float(flag(config, "TP_ATR_MIN_R") or 0)
    if sl_dist and min_r > 0 and dist < min_r * sl_dist:
        return min_r * float(sl_dist), "atr70_floored"
    return dist, "atr70"


def usoil_buy_tp_distance(scope_key: str, forexsai_sym: str, direction: str,
                          sl_dist: float, config=None) -> Optional[float]:
    """USOIL BUY için RR-tabanlı hedef mesafesi. Kapsam dışıysa None (dokunma).

    Kapsam: USOIL_BUY_TP_RR > 0 + sembol USOIL_BUY_TP_SYMBOLS içinde +
    yön BUY. SL mesafesi geçerli değilse None (fail-open).

    Gerekçe ve ölçüm: DEFAULTS["USOIL_BUY_TP_RR"] başlığındaki blok.
    """
    try:
        rr = float(flag(config, "USOIL_BUY_TP_RR") or 0)
    except (TypeError, ValueError):
        return None
    if rr <= 0:
        return None
    if direction.upper() != "BUY":
        return None
    if not _in(forexsai_sym, flag(config, "USOIL_BUY_TP_SYMBOLS")):
        return None
    if _in(scope_suffix(scope_key), flag(config, "TP_ATR_EXCLUDE_SCOPES")):
        return None
    if not sl_dist or sl_dist <= 0:
        return None
    return rr * float(sl_dist)


# ═══ FAZ 0.1 / 0.2 — pozisyon yönetimi kararları ════════════════════════════

def be_should_arm(mode: str, mfe: float, sl_dist: float, age_sec: float,
                  be_minutes: float, mfe_r: float = 0.5) -> bool:
    """Başabaş-stop devreye girmeli mi?

    mode='conditional_mfe' → pozisyon en az mfe_r×SL kadar lehe gitmişse (MFE)
    mode='time30'          → eski davranış: yaş ≥ be_minutes
    Diğer/kapalı           → asla.
    """
    if sl_dist <= 0:
        return False
    if mode == "conditional_mfe":
        return mfe >= mfe_r * sl_dist
    if mode == "time30":
        return age_sec >= be_minutes * 60
    return False


def time_stop_due(age_sec: float, minutes: float) -> bool:
    """120 dk dolduysa ve pozisyon hâlâ açıksa piyasadan kapat."""
    return bool(minutes) and minutes > 0 and age_sec >= minutes * 60


# ═══ FAZ 1.1 / 1.2 — giriş zaman pencereleri ═══════════════════════════════

def _parse_hhmm(s: str) -> dtime:
    h, m = str(s).split(":")
    return dtime(int(h), int(m))


def _in_window(now: dtime, start: dtime, end: dtime) -> bool:
    """Gece yarısını aşan pencereleri de doğru değerlendirir (22:00→07:00)."""
    if start <= end:
        return start <= now < end
    return now >= start or now < end


def entry_window_block(now_utc: datetime, forexsai_sym: str,
                       config=None) -> tuple[bool, str]:
    """(bloklandı_mı, sebep) — NDX'e özel seans/gün yasakları. Diğer semboller serbest.

    Kanıt (bu ayın 133 NASDAQ işlemi):
      ASIA 22-07 UTC : n=36  WR %50.0  −2.139$
      Cuma           : n=21  WR %38.1  −1.518$
    """
    if forexsai_sym != "NDX.INDX":
        return False, ""
    t = now_utc.timetz().replace(tzinfo=None)

    if flag(config, "NDX_SESSION_BLOCK_ENABLED"):
        for start_s, end_s in flag(config, "NDX_SESSION_BLOCK"):
            if _in_window(t, _parse_hhmm(start_s), _parse_hhmm(end_s)):
                return True, f"ASIA/seans yasağı {start_s}-{end_s} UTC (n=36, WR %50, −2.139$)"

    if flag(config, "NDX_FRIDAY_BLOCK") and now_utc.isoweekday() == 5:
        return True, "Cuma yasağı (n=21, WR %38.1, −1.518$)"

    if flag(config, "NDX_WEEKEND_HOLD_BLOCK") and now_utc.isoweekday() == 5:
        if t >= _parse_hhmm(flag(config, "NDX_WEEKEND_HOLD_FROM")):
            return True, "hafta sonu taşıma yasağı (Cuma kapanışa yakın giriş yok)"
    return False, ""


def only_confirm_required(config=None) -> Optional[bool]:
    """Faz-1.4: SCOUT sinyaller oy sayılmasın (repo varsayılanına dönüş).

    None → dokunma (config ne diyorsa o). True → CONFIRM zorunlu."""
    return True if flag(config, "PHASE1_CONFIG_RESTORE") else None


def zone_min_touch(config=None, current: int = 2) -> int:
    """Faz-1.4: zayıf S/R bölgesi musluğunu kıs (2 → 4)."""
    return 4 if flag(config, "PHASE1_CONFIG_RESTORE") else current


def sr_entry_allowed(forexsai_sym: str, config=None) -> bool:
    """Faz-1.3: NDX'te 1m S/R pullback (limit) kolu.

    ⚠️ Bu kol KAPATILIR, DÜZELTİLMEZ: analizde min-TP tabanı koymak
    (66pt) −5.909$ üretti — yasak listesinde."""
    if forexsai_sym != "NDX.INDX":
        return True
    return bool(flag(config, "NDX_SR_ENTRY_ENABLED"))


# ═══ FAZ 2 — dalga konumu + RSI (gölge) ════════════════════════════════════

def wave_position(bars_5m: Sequence[dict], price: float) -> Optional[float]:
    """wavePos = (fiyat − min) / (max − min), son 48×5m bar. 0=dip, 1=tepe."""
    if not bars_5m or len(bars_5m) < 20:
        return None
    hi = max(float(b["high"]) for b in bars_5m)
    lo = min(float(b["low"]) for b in bars_5m)
    if hi <= lo:
        return None
    return (float(price) - lo) / (hi - lo)


def position_gate_blocks(direction: str, pos: Optional[float],
                         sell_min: float, buy_max: float) -> bool:
    """SELL dalganın dibinde / BUY tepesinde → blok. pos=None → fail-open."""
    if pos is None:
        return False
    if direction == "SELL":
        return pos < sell_min
    if direction == "BUY":
        return pos > buy_max
    return False


def _atr_from(bars: Sequence[dict]) -> Optional[float]:
    """Wilder-olmayan basit ATR (ortalama TR). Yetersiz veri → None."""
    if not bars or len(bars) < 2:
        return None
    trs = []
    for i in range(1, len(bars)):
        h, l = float(bars[i]["high"]), float(bars[i]["low"])
        pc = float(bars[i - 1]["close"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs) / len(trs) if trs else None


def friday_blocks(now_utc, from_hour: int) -> bool:
    """Cuma ≥from_hour UTC → giriş elenmeli. now_utc=None → fail-open (False)."""
    if now_utc is None:
        return False
    return now_utc.weekday() == 4 and now_utc.hour >= int(from_hour)


def squeeze_ratio(closed_1m: Sequence[dict], fast: int = 14,
                  slow: int = 100) -> Optional[float]:
    """ATR14(1m) / ATR100(1m) — sıkışma oranı. <1 = piyasa son 100 dakikanın
    ortalamasından SAKİN. Yalnız KAPANMIŞ barlar verilmelidir (koşan bar
    çağıran tarafta elenir). Yetersiz veri → None (fail-open)."""
    if not closed_1m or len(closed_1m) < slow + 1:
        return None
    a_fast = _atr_from(list(closed_1m)[-(fast + 1):])
    a_slow = _atr_from(list(closed_1m)[-(slow + 1):])
    if not a_fast or not a_slow:
        return None
    return a_fast / a_slow


def squeeze_blocks(ratio: Optional[float], min_ratio: float) -> bool:
    """True → sıkışık piyasa, giriş elenmeli. ratio=None → fail-open (False)."""
    if ratio is None:
        return False
    return float(ratio) < float(min_ratio)


def rsi(closes: Sequence[float], period: int = 14) -> Optional[float]:
    """Wilder RSI. Yetersiz veri → None (fail-open)."""
    if closes is None or len(closes) < period + 1:
        return None
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = float(closes[i]) - float(closes[i - 1])
        gains += max(d, 0.0)
        losses += max(-d, 0.0)
    ag, al = gains / period, losses / period
    for i in range(period + 1, len(closes)):
        d = float(closes[i]) - float(closes[i - 1])
        ag = (ag * (period - 1) + max(d, 0.0)) / period
        al = (al * (period - 1) + max(-d, 0.0)) / period
    if al == 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + ag / al)


# ═══ FAZ 3 — MOD-E probasyon ═══════════════════════════════════════════════

def probation_band(atr_1m: float, bars: int = 5, z: float = 1.28) -> float:
    """Brownian %90 gürültü bandı: z × ATR14(1m) × √bars."""
    return float(z) * float(atr_1m) * math.sqrt(float(bars))


def probation_verdict(direction: str, signal_price: float, atr_1m: float,
                      bars_after: Sequence[dict], bars: int = 5,
                      z: float = 1.28) -> tuple[bool, float, float]:
    """(iptal_mi, aleyhe_max_hareket, band).

    Sinyalden sonraki `bars` adet 1m barda aleyhe en fazla ne kadar gidildi?
    Band aşıldıysa sinyal ölmüş sayılır → giriş İPTAL.
    BUY için aleyhe = signal_price − min(low); SELL için = max(high) − signal_price.
    """
    band = probation_band(atr_1m, bars, z)
    if not bars_after:
        return False, 0.0, band
    seg = list(bars_after)[:bars]
    if direction == "BUY":
        adverse = float(signal_price) - min(float(b["low"]) for b in seg)
    else:
        adverse = max(float(b["high"]) for b in seg) - float(signal_price)
    adverse = max(adverse, 0.0)
    return adverse > band, adverse, band


# ═══ Opsiyonel — ardışık SL soğuması ═══════════════════════════════════════
# ⚠️ DURUM: kural motoru hazır ama BOTA BAĞLANMADI (etkisi karşı-olgusalda nötr
# ölçüldü: −106$ kaybı kesiyor). Bağlamak scope başına kayıp-serisi takibi
# gerektiriyor (MT5 geçmişi) — backlog'da. Bayrak açılsa bile şu an bir yerde
# çağrılmıyor; yanıltmasın diye burada açıkça yazılıdır.

def loss_streak_cooldown_active(last_loss_ts: Optional[float], streak: int,
                                now_ts: float, config=None) -> tuple[bool, float]:
    """(aktif_mi, kalan_dk). streak ≥ eşik ve son kayıptan bu yana < süre ise blok."""
    if not flag(config, "SCOPE_LOSS_COOLDOWN_ENABLED") or not last_loss_ts:
        return False, 0.0
    need = int(flag(config, "SCOPE_LOSS_COOLDOWN_STREAK"))
    if streak < need:
        return False, 0.0
    minutes = float(flag(config, "SCOPE_LOSS_COOLDOWN_MIN"))
    elapsed = (now_ts - last_loss_ts) / 60.0
    return (elapsed < minutes), max(0.0, minutes - elapsed)
