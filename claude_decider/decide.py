"""
decide.py — Opus'un KANIT-TEMELLİ ÖZERK karar katmanı (Pro headless, API maliyeti yok).
=============================================================================
ROL: Opus sabit bir adayı yargılamaz — sembolün canlı durumu + benzer geçmiş kurulumların
GERÇEK WR kanıtından (evidence.py) KENDİ görüşünü oluşturur (aç/bekle, yön, boyut, yönetim).
Kanıt-temelli: grafik folkloruna (H&S/RSI-div/sweep — bizde çöktü) değil, BİZİM 21.5k
deduped sinyalimizin istatistiğine dayanır.

SERT GÜVENLİK (kodda zorlanır, Opus ihlal edemez): XAU SELL + USOIL BUY kalıcı yasak;
size_factor [0,1.0]; günlük zarar limiti executor'da. Bunlar "veteran"a verilen kelepçe
değil, firma kuralları — kanıtla -EV olduğu için.

Model: Opus 4.8 (max) — yargı en iyi brain'i hak eder; kapı/durum seyrek olduğu için
quota sürdürülebilir. Quota sıkışırsa DECIDE_MODEL="sonnet".
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import decider_config as config  # noqa: E402
from gates import CHAN_Z as GATE_CHAN_Z, VWAP_Z as GATE_VWAP_Z  # noqa: E402  (free-cf eşikleri)

MEM = HERE / "memory"
JOURNAL_JSONL = MEM / "journal.jsonl"
JOURNAL_LOCK = MEM / "journal.lock"


from contextlib import contextmanager  # noqa: E402


@contextmanager
def journal_lock(timeout: float = 10.0):
    """Süreçler-arası journal kilidi: decider'ın resolve'ı (tam-dosya yeniden-yazım) ile
    batch_eval --write / append'ler çakışıp SESSİZCE veri kaybetmesin. Fail-open: timeout'ta
    kilitli beklemek yerine uyarıyla devam (canlı döngü asla kilitlenmez). Bayat kilit
    (>60s, sahibi ölmüş) otomatik kırılır."""
    import os
    import time as _t
    MEM.mkdir(parents=True, exist_ok=True)
    deadline = _t.time() + timeout
    fd = None
    while True:
        try:
            if JOURNAL_LOCK.exists() and _t.time() - JOURNAL_LOCK.stat().st_mtime > 60:
                JOURNAL_LOCK.unlink(missing_ok=True)          # bayat kilidi kır
            fd = os.open(str(JOURNAL_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if _t.time() > deadline:
                print("  ⚠ journal.lock timeout — fail-open devam (nadir çakışma riski)")
                break
            _t.sleep(0.25)
        except OSError:
            break
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
            JOURNAL_LOCK.unlink(missing_ok=True)
DECIDE_MODEL = "opus"                       # asıl (canlı) karar modeli
# GÖLGE model A/B: aynı veriye paralel karar verir, AYRI grade edilir (canlı değil, kıyas için).
# 2026-07-03 KAPATILDI (None): canlı çift-çağrı 3 günde haftalık limitin %55'ini yedi.
# Fable artık batch_eval.py ile ölçülür: kayıtlar birikir → TEK toplu çağrı → sızıntısız
# değerlendirme (sonuçlar+fiyat+zaman sıyrılır, shuffle). ~60 çağrı/gün → 1 çağrı/gün.
# GÖZLENEN canlı headless maliyet (3 gün, journal): Opus $0.34/çağrı, Fable $0.55/çağrı —
# "Fable ucuz" varsayımı YANLIŞTI; gerçek tasarruf kolu çağrı SAYISI (CONSULT_REV/cadence/batch).
SHADOW_MODEL = None
# Per-sembol ATR stop çarpanları (grading + trade). Varsayılan RR~0.67.
# XAUUSD "patient WR" ([[xauusd-meta-stop-sizing]]): dar stop → dönüş tamamlanmadan SL.
# Geniş SL ver → sabırlı bounce stop yemeden realize olsun (canlı gözlem: XAU BUY %43/−0.29R dar stopla).
DEFAULT_STOP_ATR = (1.0, 1.5)
STOP_ATR = {
    "XAUUSD": (1.0, 2.5),       # TP 1×ATR (VWAP'a dönüş), SL 2.5×ATR (geniş — sabırlı)
}
TP_ATR, SL_ATR = DEFAULT_STOP_ATR   # geriye-uyum (varsayılan)


def stop_mults(symbol: str) -> tuple[float, float]:
    return STOP_ATR.get(symbol, DEFAULT_STOP_ATR)


def build_trade(symbol: str, direction: str, atr, price, bar_time=None) -> dict | None:
    """Entry + per-sembol ATR TP/SL (grade edilebilir trade). Opus/Fable/free ortak kullanır."""
    if not atr or not price or not direction:
        return None
    buy = str(direction).upper() == "BUY"
    tp_atr, sl_atr = stop_mults(symbol)
    tp = price + tp_atr * atr if buy else price - tp_atr * atr
    sl = price - sl_atr * atr if buy else price + sl_atr * atr
    return {"entry_price": round(price, 5), "atr": round(atr, 5), "tp": round(tp, 5),
            "sl": round(sl, 5), "rr": round(tp_atr / sl_atr, 2), "entry_bar_time": bar_time}


def _shadow_pack(symbol: str, dec: dict, atr, price, bar_time) -> dict | None:
    """Gölge-model kararını (Fable) journal-gömülü pakete indir: karar + kendi trade'i + outcome yeri."""
    if not dec:
        return None
    d = dec.get("direction")
    trade = build_trade(symbol, d, atr, price, bar_time) if str(dec.get("action", "")).upper() == "OPEN" else None
    return {"model": dec.get("_model"),
            "decision": {k: dec.get(k) for k in ("action", "direction", "size_factor", "reason")},
            "trade": trade, "outcome": None, "cost_usd": dec.get("_cost_usd")}

# Sert yasaklar — kanıtlı -EV, Opus ihlal edemez (kod zorlar). config'i de birleştir.
HARD_BANS: set[tuple[str, str]] = {("XAUUSD", "SELL"), ("USOIL.FOREX", "BUY")} | \
    set(getattr(config, "BLOCKED_SYMBOL_DIRECTIONS", set()))

SYSTEM = (
    "Sen ForexSAI'nin baş trader'ısın — 50 yıllık deneyimli, soğukkanlı, KANITA dayalı bir "
    "veteran. Sana bir sembolün canlı durumu VE benzer geçmiş kurulumların gerçek WR kanıtı "
    "(bizim 21.5k deduped sinyalimizden) sunulur. KENDİ görüşünü oluştur: işlem aç mı, bekle mi? "
    "hangi yön? ne boyut? KRİTİK: grafik folkloruna (head&shoulders, RSI-divergence, sweep — "
    "bunlar BİZİM verimizde çöktü) DEĞİL, sana verilen geçmiş istatistiğe dayan. "
    "EŞİK (RR~0.67, breakeven WR ~%60): kanıt WR≥%62 net kurulumları AÇ; %59-62 SINIRDA ise KÜÇÜK "
    "boyutla (0.3-0.4) değerlendir — illa mükemmellik bekleme; yalnız WR<%58 veya bağlam kötüyse BEKLE. "
    "AŞIRI TEMKİNLİ OLMA: geçmişte açmadığın çok kurulum kazanıyordu (özellikle NDX/GDAXI/USOIL). "
    "AMA XAUUSD'de temkinli kal (canlı zayıf). size_factor ∈ [0,1.0]: konviksiyon × bağlam. "
    "Çıktın SADECE tek-satır JSON."
)


def load_journal(clean: bool = True) -> list[dict]:
    """Analiz/öğrenme araçları için MERKEZİ journal yükleyici. clean=True → DONUK-FEED
    KOPYALARINI düşürür: bir sembolün ardışık kayıtlarında (cf.dir, cf.entry_price) birebir
    aynıysa yalnız İLKİ kalır. 2026-07-04/05 hafta sonu 263 frozen kayıt (124× aynı entry!)
    tüm istatistikleri zehirlemişti; bu filtre GEÇMİŞİ de GELECEĞİ de jenerik temizler
    (tarih hardcode'u yok — parmak izi: donuk feed = değişmeyen karar). NOT: outcomes.resolve
    HAM okur (grading her kaydı işlemeli); bu filtre YALNIZ analiz/öğrenme katmanı içindir."""
    if not JOURNAL_JSONL.exists():
        return []
    rows = [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not clean:
        return rows
    out, last, dropped = [], {}, 0
    for e in rows:
        cf = e.get("counterfactual") or {}
        fp = (cf.get("dir"), cf.get("entry_price"))
        sym = e.get("symbol")
        if fp != (None, None) and last.get(sym) == fp:
            dropped += 1
            continue
        last[sym] = fp
        out.append(e)
    if dropped:
        print(f"  🧹 journal temizliği: {dropped} donuk-kopya kayıt analiz dışı bırakıldı "
              f"(ham {len(rows)} → temiz {len(out)}; grading etkilenmez)")
    return out


def _read(name: str) -> str:
    p = MEM / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def build_prompt(situation: dict) -> str:
    sym = situation["symbol"]
    bans = [f"{s} {d}" for (s, d) in HARD_BANS if s == sym]
    return f"""{SYSTEM}

=== PLAYBOOK (doğrulanmış priorlar) ===
{_read('PLAYBOOK.md')}

=== LESSONS (terfi etmiş dersler) ===
{_read('LESSONS.md')}

=== REGIME (güncel piyasa bağlamı) ===
{_read('REGIME.md')}

=== CANLI DURUM: {sym} ===
{json.dumps(situation, ensure_ascii=False, indent=2)}

=== SERT YASAK (bu sembol) ===
{bans or "yok"}

GÖREV — {sym} için KENDİ görüşünü oluştur (kanıttan muhakeme et):
- Her yönün `evidence`'ı: benzer geçmiş kurulumda gerçek WR + örnek (n) + OOS. Buna dayan.
- rev_chan/rev_vwap yüksek (ters yönde aşırı) = mean-reversion fırsatı; düşük/negatif = kovalama (kanıtta düşük WR).
- NDX'te VIX rejimi yönü etkiler AMA yalnız vix.fresh=true ise; vix.fresh=false (off-hours/neutral_band → ^VIX donuk/bıçak-sırtı) → VIX'e GÜVENME, yalnız fiyat-kanıtına dayan.
- Açık pozisyon/korelasyon yığılması, near_event=true → küçült/bekle.
- `fakeout` alanı varsa: TAZE bir seviye kırılımı var demektir. `detector.call` en güçlü kanıttır
  (+1-bar LGBM, OOS: SAHTE çağrısı %70, GERÇEK çağrısı %83 isabet; "pending_next_bar" = teyit barı
  kapanmadı, kesin karar ~5dk sonra — o zamana dek temkinli ol). `recommendation` alanını oku:
  · avoid_breakout_direction / fake_probability ≥%75 → kırılım YÖNÜNDE AÇMA ("kırdı, kesin gidecek" tuzağı).
  · fade_candidate (skor≤−2, OOS %87 sahte) → TERS yön lehine EK kanıt — rev_chan/rev_vwap mean-rev
    kanıtınla AYNI yönü gösteriyorsa konviksiyonu artırabilir; tek başına giriş sebebi DEĞİL.
  · breakout_leaning_genuine → sadece "engel yok" demektir (OOS %55 — edge değil), yön kanıtı sayma.
- XAU BUY ise: "patient WR", GENİŞ stop şart (management'a yaz, boyut düşür).
SADECE şu tek-satır JSON'u döndür:
{{"action":"OPEN","direction":"BUY","size_factor":0.7,"entry":"market","reason":"kanıta dayalı kısa gerekçe","management":"stop/hedef/çıkış notu"}}
(işlem açmıyorsan: {{"action":"WAIT","direction":null,"size_factor":0,"reason":"...","management":""}})"""


def _extract_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


_CLAUDE_BIN_CACHE: str | None = None


def _claude_bin() -> str:
    """Claude CLI yolunu çöz (2026-07-23/25 kutu düzeltmeleri).

    Çıplak "claude" Windows'ta PATH'te olmayabiliyor → her karar sessizce
    `claude exit 1` ile WAIT'e düşüyordu. Sıra: CLAUDE_BIN env → PATH →
    bilinen kurulum yolları. Sonuç cache'lenir (her kararda FS taraması yok).

    2026-07-25: kutu raporu — orada claude npm-global DEĞİL, kullanıcı
    node_modules'ına kurulu (`~/node_modules/@anthropic-ai/claude-code-
    win32-x64/claude.exe`); eski liste bunu kaçırdığı için CLAUDE_BIN env'i
    zorunlu hale geliyordu. Platform paketi adı değiştiği için glob ile aranır.
    """
    global _CLAUDE_BIN_CACHE
    if _CLAUDE_BIN_CACHE:
        return _CLAUDE_BIN_CACHE
    import shutil
    home = Path.home()

    def _pick() -> str:
        env_bin = os.getenv("CLAUDE_BIN")
        if env_bin and Path(env_bin).exists():
            return env_bin
        found = shutil.which("claude")
        if found:
            return found
        for cand in (home / "node_modules/.bin/claude.cmd",
                     home / "node_modules/.bin/claude",
                     home / "AppData/Roaming/npm/claude.cmd",
                     home / "AppData/Roaming/npm/claude",
                     home / ".local/bin/claude",
                     Path("/usr/local/bin/claude"),
                     Path("/opt/homebrew/bin/claude")):
            if cand.exists():
                return str(cand)
        # platform paketi (claude-code-win32-x64 / darwin-arm64 / linux-x64…)
        for root in (home / "node_modules/@anthropic-ai",
                     home / "AppData/Roaming/npm/node_modules/@anthropic-ai"):
            if not root.is_dir():
                continue
            for pkg in sorted(root.glob("claude-code-*")):
                for exe in ("claude.exe", "claude"):
                    if (pkg / exe).exists():
                        return str(pkg / exe)
        return "claude"      # son çare: eski davranış (hata mesajı net gelir)

    _CLAUDE_BIN_CACHE = _pick()
    return _CLAUDE_BIN_CACHE


def call_claude(prompt: str, model: str = DECIDE_MODEL, timeout: int = 180) -> dict:
    cmd = [_claude_bin(), "--dangerously-skip-permissions", "-p",
           "--model", model, "--output-format", "json"]
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"action": "WAIT", "reason": "claude timeout", "_error": True}
    if r.returncode != 0:
        return {"action": "WAIT", "reason": f"claude exit {r.returncode}: {r.stderr[:200]}", "_error": True}
    try:
        meta = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"action": "WAIT", "reason": "meta parse fail", "_error": True}
    dec = _extract_json(meta.get("result", ""))
    if dec is None:
        return {"action": "WAIT", "reason": "decision parse fail",
                "_raw": meta.get("result", "")[:300], "_error": True}
    dec["_cost_usd"] = meta.get("total_cost_usd")
    dec["_ms"] = meta.get("duration_ms")
    dec["_model"] = model
    return dec


def _enforce_guardrails(symbol: str, dec: dict, allow_banned: bool = False) -> dict:
    """Sert güvenlik — Opus ne derse desin: yasak yön → WAIT; size [0,1.0]; WAIT → size 0.

    allow_banned=True: SERT-YASAK atlanır — yalnız GÖLGE akışlar için (free mod;
    execute() zaten stub). Canlı kanıt-akışı her zaman allow_banned=False çağırır.
    """
    action = str(dec.get("action", "WAIT")).upper()
    direction = dec.get("direction")
    if (not allow_banned) and action == "OPEN" and direction and (symbol, str(direction).upper()) in HARD_BANS:
        dec["action"] = "WAIT"
        dec["reason"] = f"[SERT-YASAK: {symbol} {direction}] " + str(dec.get("reason", ""))
        dec["size_factor"] = 0.0
        return dec
    try:
        sf = float(dec.get("size_factor", 0.0))
    except (TypeError, ValueError):
        sf = 0.0
    dec["size_factor"] = max(0.0, min(1.0, sf))
    if action != "OPEN":
        dec["size_factor"] = 0.0
    return dec


def decide_situation(situation: dict, model: str = DECIDE_MODEL,
                     shadow_model: str | None = SHADOW_MODEL) -> dict:
    """Opus sembol durumundan KENDİ kararını verir + sert güvenlik kıskacı.
    shadow_model verilirse AYNI prompt'la paralel gölge-karar (A/B, ayrı grade)."""
    prompt = build_prompt(situation)
    dec = _enforce_guardrails(situation["symbol"], call_claude(prompt, model=model))
    if shadow_model:
        sdec = _enforce_guardrails(situation["symbol"], call_claude(prompt, model=shadow_model))
        dec["_shadow"] = sdec
    return dec


# ── XAU SERBEST-ZEKÂ modu (kanıt-tablosu YOK, saf muhakeme) ──────────────────
# FREE_EXPLORER=1 (default): KEŞİF modu — gölge hesapta amaç VERİ ÜRETMEK;
# her değerlendirmede yön seçilir, konviksiyon size_factor'da ifade edilir.
# 977/979 WAIT problemi (2026-07): eski "çoğu zaman bekle" telkini + XAU SELL
# yasağı gölge öğrenmeyi boğuyordu — 3 haftada 2 işlem = 0 öğrenilebilir veri.
# FREE_EXPLORER=0 → eski seçici (sniper) davranış geri gelir.
FREE_EXPLORER = os.getenv("FREE_EXPLORER", "1") == "1"

_FREE_SYSTEM_SNIPER = (
    "Sen 50 yıllık deneyimli bir ALTIN (XAUUSD) trader'ısın. XAUUSD intraday'de bizim "
    "istatistiksel edge'imiz YOK — o yüzden sana kanıt-tablosu vermiyoruz; kendi piyasa "
    "okumanı kullan. Sana çok-zaman-dilimli (1m/5m/30m/1h) ham bağlam veriyorum: trend "
    "dizilimi, trend-channel z (fiyatın kanaldaki yeri; +üst −alt, |z|≈2 sınır), momentum, "
    "en yakın destek/direnç (ATR mesafesiyle), VIX rejimi, DXY (dolar — altına ters). "
    "Bir insan trader gibi BÜTÜNE bak: TF'ler uyumlu mu, fiyat anlamlı bir S/R'de mi, makro "
    "destekliyor mu? Net bir kurulum YOKSA BEKLE (çoğu zaman doğru cevap budur). İşlem açacaksan "
    "yönünü, güvenini (size 0-1) ve mantığını söyle. Çıktın SADECE tek-satır JSON."
)

_FREE_SYSTEM_EXPLORER = (
    "Sen 50 yıllık deneyimli bir ALTIN (XAUUSD) trader'ısın ve bu bir GÖLGE (kağıt) hesap — "
    "gerçek para YOK, amaç VERİ ÜRETMEK ve kalibrasyon öğrenmek. Sana çok-zaman-dilimli "
    "(1m/5m/30m/1h) ham bağlam veriyorum: trend dizilimi, trend-channel z (+üst −alt, |z|≈2 "
    "sınır), momentum, en yakın destek/direnç (ATR mesafesiyle), VIX rejimi, DXY (dolar — "
    "altına ters). KURAL: HER değerlendirmede piyasayı oku ve bir YÖN SEÇ — BUY veya SELL "
    "(ikisi de serbest). WAIT yalnız veri bozuk/eksikse meşrudur; 'kurulum net değil' WAIT "
    "sebebi DEĞİLDİR — kararsızlığını yön yerine DÜŞÜK size_factor ile ifade et. "
    "size_factor = konviksiyon kalibrasyonun: 0.1-0.2 zayıf his, 0.3-0.5 makul kurulum, "
    "0.6-1.0 güçlü çok-TF uyum. Bu kalibrasyon ölçülecek: hangi konviksiyon seviyen ve hangi "
    "koşullar gerçekten kazanıyor — GERÇEK filtreyi bu veriden çıkaracağız. Dürüst ol: "
    "emin değilken 0.15 ile yön seçmek, WAIT'ten çok daha değerlidir. Çıktın SADECE tek-satır JSON."
)

FREE_SYSTEM = _FREE_SYSTEM_EXPLORER if FREE_EXPLORER else _FREE_SYSTEM_SNIPER


def build_free_prompt(ctx: dict) -> str:
    # forensics varken multi_tf ÇİFTE veri (channel_z/adx/trend iki kez) → prompt'tan düş
    # (~%40 token tasarrufu her XAU çağrısında; journal'da ikisi de durur)
    pctx = {k: v for k, v in ctx.items() if not (k == "multi_tf" and ctx.get("forensics"))}
    return f"""{FREE_SYSTEM}

=== XAUUSD ÇOK-TF HAM BAĞLAM (kanıt değil, senin yorumlaman için) ===
{json.dumps(pctx, ensure_ascii=False, indent=2)}

GÖREV — bir altın uzmanı gibi bu resmi oku:
- Çok-TF uyum: 1m/5m/30m/1h trendleri hizalı mı, yoksa çelişiyor mu (çelişki=belirsizlik)?
- Konum: fiyat destek/dirence yakın mı (dönüş fırsatı), yoksa boşlukta mı (kovalama)?
- channel_z: bir TF'de ±2'ye yakınsa mean-reversion; ortadaysa trend-devamı olabilir.
- Makro: VIX stres + DXY zayıf = altın güçlü; DXY güçlü = altına baskı.
{("- GÖLGE KEŞİF: bir yön SEÇ (BUY veya SELL) + dürüst size_factor (0.1=zayıf his, 1.0=güçlü uyum). WAIT yalnız bozuk/eksik veri."
  if FREE_EXPLORER else
  "- BELİRSİZSEN veya net kurulum yoksa WAIT (disiplin — zorlama).")}
SADECE şu tek-satır JSON:
{{"action":"OPEN","direction":"BUY|SELL","size_factor":0.4,"reason":"çok-TF + S/R + makro mantığın","management":"stop/hedef notu"}}
(WAIT gerekiyorsa: {{"action":"WAIT","direction":null,"size_factor":0,"reason":"...","management":""}})"""


def decide_free(ctx: dict, model: str = DECIDE_MODEL,
                shadow_model: str | None = SHADOW_MODEL) -> dict:
    """XAU serbest-zekâ kararı — kanıt-tablosu yok, Opus'un çıplak muhakemesi. Guardrail: XAU
    SELL yasak (HARD_BANS), size [0,1.0]. Deneysel → çağıran journal'a mode='free' yazar.
    shadow_model verilirse Fable5 AYNI bağlama paralel karar verir (A/B)."""
    # GÖLGE akış: SERT-YASAK atlanır (FREE_EXPLORER ile SELL de serbest) —
    # execute() stub, gerçek emir yok; amaç iki yönde de öğrenme verisi.
    prompt = build_free_prompt(ctx)
    dec = _enforce_guardrails("XAUUSD", call_claude(prompt, model=model),
                              allow_banned=FREE_EXPLORER)
    dec["_mode"] = "free"
    if shadow_model:
        dec["_shadow"] = _enforce_guardrails("XAUUSD", call_claude(prompt, model=shadow_model),
                                             allow_banned=FREE_EXPLORER)
    return dec


def append_free_journal(ctx: dict, dec: dict) -> dict:
    """XAU serbest-zekâ kararını journal'a yaz (mode='free' etiketli, ayrı ölçülür). OPEN ise
    entry+ATR TP/SL (XAU geniş stop) → outcomes.py grade eder. Kanıt-temelli akıştan ayrı analiz."""
    d = dec.get("direction")
    atr, price, bt = ctx.get("atr_5m"), ctx.get("price"), ctx.get("bar_time_5m")
    trade = build_trade("XAUUSD", d, atr, price, bt) if str(dec.get("action", "")).upper() == "OPEN" else None
    shadow = _shadow_pack("XAUUSD", dec.get("_shadow"), atr, price, bt)

    # KARŞI-OLGU (Paket 2): free mod WAIT dese bile "açsaydı BUY" grade edilir — yoksa
    # 80 karar = 0 öğrenilebilir veri (recall/otopsi/batch/exit XAU'yu hiç göremiyordu).
    # Yalnız BUY (XAU SELL sert yasak). live bloğu forensics-5m'den, gates eşikleriyle.
    cf = None
    lf = None
    if atr and price and ("XAUUSD", "BUY") not in HARD_BANS:
        f5 = ((ctx.get("forensics") or {}).get("tfs") or {}).get("5m") or {}
        cz, vz = f5.get("channel_z"), f5.get("vwap_z")
        rev_c = (-float(cz)) if cz is not None else None      # BUY hizalı: −z
        rev_v = (-float(vz)) if vz is not None else None
        lf = {"rev_chan": round(rev_c, 2) if rev_c is not None else None,
              "rev_vwap": round(rev_v, 2) if rev_v is not None else None,
              "adx": f5.get("adx"), "atr": atr,
              "gate_fired": bool((rev_c is not None and rev_c > GATE_CHAN_Z)
                                 or (rev_v is not None and rev_v > GATE_VWAP_Z))}
        t = build_trade("XAUUSD", "BUY", atr, price, bt)
        if t:
            cf = {"dir": "BUY", **t, "live": lf}

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "symbol": "XAUUSD", "mode": "free",
        "decision": {k: dec.get(k) for k in ("action", "direction", "size_factor", "reason", "management")},
        "trade": trade,
        "counterfactual": cf,                      # "açsaydı BUY" — outcomes grade eder
        "cf_outcome": None,
        "dirs_live": {"BUY": lf} if lf else None,  # batch_eval free kayıtları da görsün
        "free_context": {k: ctx.get(k) for k in ("price", "session", "support", "resistance",
                                                 "dist_to_support_atr", "dist_to_resistance_atr", "macro")},
        "multi_tf": ctx.get("multi_tf"),
        "forensics": ctx.get("forensics"),   # SL-otopsi snapshot
        "model": dec.get("_model", DECIDE_MODEL), "cost_usd": dec.get("_cost_usd"),
        "shadow_model": shadow,          # Fable5 A/B kararı (ayrı grade)
        "outcome": None,
    }
    MEM.mkdir(parents=True, exist_ok=True)
    with journal_lock(timeout=5.0):
        with open(JOURNAL_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def append_journal(situation: dict, dec: dict) -> dict:
    """Kararı ham deneyim olarak journal.jsonl'e yaz (re-damıtma yakıtı; outcome sonra dolar)."""
    sym = situation["symbol"]
    chosen = dec.get("direction")
    chosen_blk = (situation.get("directions", {}).get(chosen, {}) or {}) if chosen else {}
    used_ev = chosen_blk.get("evidence")
    live = chosen_blk.get("live") or {}

    price, bt = situation.get("price"), situation.get("bar_time")
    dl = situation.get("directions") or {}
    # ATR yön-bağımsız → chosen live yoksa herhangi bir yönün live'ından al (shadow/WAIT için)
    atr_any = live.get("atr") or next((b.get("live", {}).get("atr") for b in dl.values() if b.get("live")), None)

    # OPEN ise: entry + ATR TP/SL (sonra outcome'da WIN/LOSS taranır)
    trade = build_trade(sym, chosen, live.get("atr"), price, bt) \
        if str(dec.get("action", "")).upper() == "OPEN" and chosen else None

    # KARŞI-OLGU: primary_dir "açsaydı" — HER kayda (recall/analyze_missed grade eder)
    cf = None
    primary = situation.get("primary_dir")
    if primary:
        plive = (dl.get(primary) or {}).get("live") or {}
        ptrade = build_trade(sym, primary, plive.get("atr"), price, bt)
        if ptrade:
            cf = {"dir": primary, **ptrade, "live": plive}

    # GÖLGE model (Fable) — aynı prompt, ayrı grade (A/B). Kendi yön/size'ıyla.
    shadow = _shadow_pack(sym, dec.get("_shadow"), atr_any, price, bt)

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "symbol": sym,
        "decision": {k: dec.get(k) for k in ("action", "direction", "size_factor", "entry", "reason", "management")},
        "trade": trade,
        "live": live or None,
        "evidence_used": used_ev,
        "counterfactual": cf,        # primary_dir "açsaydı" — analyze_missed grade eder
        "cf_outcome": None,
        "dirs_live": {d: (b.get("live") or {}) for d, b in (situation.get("directions") or {}).items()},
        "forensics": situation.get("forensics"),   # SL-otopsi: hacim/VIX/DXY/kanal/multi-TF S/R
        "vix": situation.get("vix"),
        "context": situation.get("context"),
        "model": dec.get("_model", DECIDE_MODEL), "cost_usd": dec.get("_cost_usd"),
        "shadow_model": shadow,          # Fable5 A/B kararı (ayrı grade)
        "outcome": None,
    }
    MEM.mkdir(parents=True, exist_ok=True)
    with journal_lock(timeout=5.0):
        with open(JOURNAL_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


if __name__ == "__main__":
    # uçtan-uca tek test: sentetik NDX oversold durumu → Opus kendi görüşü → journal
    import sys as _s
    _s.path.insert(0, str(HERE))
    import evidence as ev
    import math
    bars = [{"high": 100 + math.sin(i / 5), "low": 99 + math.sin(i / 5),
             "close": 100 + math.sin(i / 5), "volume": 1000} for i in range(60)]
    bars[-1] = {"high": 95.1, "low": 94.8, "close": 95.0, "volume": 5000}
    tables = ev.load_tables()
    sit = {"symbol": "NDX.INDX",
           "vix": {"value": 21.3, "regime": "stress", "favored": "BUY"},
           "context": {"session": "NY", "open_positions": 0, "near_event": False, "recent": "geçmiş yok"},
           "directions": {}}
    for d in ("BUY", "SELL"):
        lf = ev.live_features(bars, d, vix=21.3)
        sit["directions"][d] = {"live": lf, "evidence": ev.evidence_pack("NDX.INDX", d, lf, tables)}
    print(f"Opus karar veriyor ({DECIDE_MODEL})...")
    dec = decide_situation(sit)
    print(json.dumps({k: v for k, v in dec.items() if not k.startswith("_")}, ensure_ascii=False, indent=2))
    print(f"(cost≈${dec.get('_cost_usd')}, {dec.get('_ms')}ms)")
    append_journal(sit, dec)
    print("journal'a yazıldı.")
