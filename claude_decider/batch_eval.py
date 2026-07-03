"""
batch_eval.py — Fable TOPLU analiz: biriken kararları TEK çağrıyla değerlendir (sızıntısız).
=============================================================================
NEDEN: Canlı shadow (her kararda ayrı Fable çağrısı) 3 günde haftalık limitin %55'ini yedi.
Bu sistem: kayıtlar journal'da birikir → Fable'a TEK toplu çağrıyla "bu noktalarda işleme
girer miydin, hangi yönde?" sorulur → cevapları zaten-grade-edilmiş GERÇEK sonuçlarla
(cf_outcome, 5m/1m bazlı) eşleştirilir → Fable'ın WR/EV'si ölçülür. ~60 çağrı/gün → 1.

SIZINTI GARANTİLERİ (mekanik, prompt-ricası değil):
 1. SONUÇ ASLA GİTMEZ: outcome/pnl/exit_grades/outcome_at → paketten fiziksel olarak yok.
 2. OPUS KARARI GİTMEZ: decision/reason sıyrılır → Fable kopyalayamaz, bağımsız ölçüm.
 3. KRONOLOJİK FİYAT ZİNCİRİ KIRILIR: mutlak fiyat/S-R seviyesi/zaman damgası SIYRILIR
    (yalnız ATR-göreli: z-skorlar, dist_atr, oranlar) + kayıtlar SHUFFLE edilir →
    "sonraki kaydın fiyatı önceki kaydın geleceği" saldırısı fiziksel olarak imkânsız.
 4. leak_guard(): pakete giren her anahtar BEYAZ-LİSTE ile doğrulanır; yasak anahtar/
    değer bulunursa program ÇAĞRI YAPMADAN durur (fail-closed).

Her kayıt zaten karar-ANI snapshot'ı (dirs_live/forensics o an yazıldı) → kayıt-içi
gelecek bilgisi yok. Eşleştirme: Fable OPEN+yönü counterfactual yönüyle aynıysa
cf_outcome ile grade edilir (1m-dürüst resolve zincirimiz).
"""
from __future__ import annotations
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import JOURNAL_JSONL, call_claude  # noqa: E402

MODEL = "claude-fable-5"
MAX_PER_CALL = 70           # tek çağrıda değerlendirilen kayıt (çıktı token güvenliği)
SHUFFLE_SEED = 42           # tekrarlanabilir karıştırma (answer key lokalde)

# BEYAZ LİSTE — pakete yalnız bunlar girebilir (fail-closed güvenlik)
ALLOWED_KEYS = {
    "i", "symbol", "session", "vix", "vix_regime", "dirs", "tfs",
    "rev_chan", "rev_vwap", "adx", "gate_fired",
    "channel_z", "vwap_z", "vol_ratio", "trend",
    "sup_dist_atr", "sup_touches", "sup_last_reaction",
    "res_dist_atr", "res_touches", "res_last_reaction",
    "BUY", "SELL", "1m", "5m", "30m", "1h", "4h",
}
FORBIDDEN_VALUES = ("WIN", "LOSS", "EXPIRE")   # değerlerde de sonuç sızmasın


def leak_guard(obj, path="root"):
    """Paket ağacını gez: beyaz-liste dışı anahtar veya yasak değer → HATA (çağrı yapılmaz)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k not in ALLOWED_KEYS:
                raise ValueError(f"SIZINTI ENGELLENDİ: yasak anahtar '{k}' @ {path}")
            leak_guard(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for j, v in enumerate(obj):
            leak_guard(v, f"{path}[{j}]")
    elif isinstance(obj, str):
        if obj.upper() in FORBIDDEN_VALUES:
            raise ValueError(f"SIZINTI ENGELLENDİ: yasak değer '{obj}' @ {path}")


def _pack(e, idx: int) -> dict | None:
    """Kayıt → sızıntısız paket. Mutlak fiyat/seviye/zaman YOK; yalnız ATR-göreli + etiket."""
    dl = e.get("dirs_live") or {}
    if not dl:
        return None
    dirs = {}
    for d, lf in dl.items():
        if not lf:
            continue
        dirs[d] = {k: lf.get(k) for k in ("rev_chan", "rev_vwap", "adx", "gate_fired")
                   if lf.get(k) is not None}
    fx = (e.get("forensics") or {}).get("tfs") or {}
    tfs = {}
    for tf, f in fx.items():
        row = {k: f.get(k) for k in ("channel_z", "vwap_z", "adx", "vol_ratio", "trend")
               if f.get(k) is not None}
        sr = f.get("sr") or {}
        if sr.get("sup"):
            row["sup_dist_atr"] = sr["sup"].get("dist_atr")
            row["sup_touches"] = sr["sup"].get("touches")
            if sr["sup"].get("last_reaction"):
                row["sup_last_reaction"] = sr["sup"]["last_reaction"]
        if sr.get("res"):
            row["res_dist_atr"] = sr["res"].get("dist_atr")
            row["res_touches"] = sr["res"].get("touches")
            if sr["res"].get("last_reaction"):
                row["res_last_reaction"] = sr["res"]["last_reaction"]
        if row:
            tfs[tf] = row
    vix = (e.get("vix") or {})
    pack = {"i": idx, "symbol": e.get("symbol"),
            "session": (e.get("context") or {}).get("session"),
            "dirs": dirs}
    if vix.get("value") is not None:
        pack["vix"] = vix.get("value")
        if vix.get("regime"):
            pack["vix_regime"] = vix.get("regime")
    if tfs:
        pack["tfs"] = tfs
    return pack


def build_batch(limit: int = MAX_PER_CALL):
    """Ölçülebilir kayıtları (cf grade'li) seç, paketle, SHUFFLE et. Dönüş (packs, key)."""
    if not JOURNAL_JSONL.exists():
        return [], {}
    rows = [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    usable = [e for e in rows
              if e.get("cf_outcome") in ("WIN", "LOSS") and e.get("dirs_live")
              and not (e.get("batch_eval") or {}).get(MODEL)]          # daha önce değerlendirilmemiş
    usable = usable[-limit:]
    random.seed(SHUFFLE_SEED)
    random.shuffle(usable)                                             # kronolojik zinciri KIR
    packs, key = [], {}
    for idx, e in enumerate(usable):
        p = _pack(e, idx)
        if p:
            packs.append(p)
            key[idx] = e          # answer key LOKALDE kalır, asla gönderilmez
    for p in packs:
        leak_guard(p)             # fail-closed: sızıntı varsa çağrı YAPILMAZ
    return packs, key


PROMPT = """Sen disiplinli bir trader'sın. Aşağıda {n} bağımsız karar-anı durumu var (sıra
RASTGELE, birbirleriyle İLİŞKİSİZ — zincir kurma). Her durumda: dirs = yön başına
mean-reversion aşırılığı (rev_chan/rev_vwap; >2 güçlü ters-aşırılık), gate_fired = doğrulanmış
eşik; tfs = zaman dilimi başına kanal konumu (channel_z), hacim oranı, trend, ve destek/dirence
ATR-mesafe + dokunuş gücü (sup_/res_dist_atr, touches). Mutlak fiyat/zaman bilerek verilmedi.

GÖREV: HER durum için ayrı karar ver — işleme girer miydin? Kurallar: RR~0.67 (breakeven
~%60) → yalnız net kurulumlar; XAUUSD'de ekstra temkinli; karşı yöndeki S/R'a <1 ATR varsa
dikkat. Çıktın SADECE şu JSON (başka hiçbir şey yazma):
{{"answers":[{{"i":0,"action":"OPEN|WAIT","direction":"BUY|SELL|null","size":0.0}}, ...]}}
Tüm {n} durum için cevap ver, i indexlerini aynen kullan.

DURUMLAR:
{data}"""


def evaluate(packs, key, model=MODEL, write=False):
    n = len(packs)
    prompt = PROMPT.format(n=n, data=json.dumps(packs, ensure_ascii=False, separators=(",", ":")))
    print(f"Tek toplu çağrı → {model} ({n} durum, ~{len(prompt)//4} token)...")
    dec = call_claude(prompt, model=model, timeout=420)
    answers = dec.get("answers")
    cost = dec.get("_cost_usd")
    if not isinstance(answers, list):
        print("❌ cevap parse edilemedi:", str(dec.get("_raw") or dec.get("reason"))[:200])
        return
    # eşleştir + grade (cf_outcome = 1m-dürüst zincirimiz; Fable'a hiç gitmedi)
    win = loss = wait = dir_mismatch = 0
    ev_sum = 0.0
    for a in answers:
        e = key.get(a.get("i"))
        if e is None:
            continue
        act = str(a.get("action", "")).upper()
        if act != "OPEN":
            wait += 1; continue
        cf = e.get("counterfactual") or {}
        if str(a.get("direction", "")).upper() != str(cf.get("dir", "")).upper():
            dir_mismatch += 1; continue          # cf yalnız primary yönde grade'li
        if e["cf_outcome"] == "WIN":
            win += 1; ev_sum += e.get("cf_pnl_r") or 0.667
        else:
            loss += 1; ev_sum += e.get("cf_pnl_r") or -1.0
    graded = win + loss
    print("\n" + "=" * 60)
    print(f"FABLE TOPLU DEĞERLENDİRME — {n} durum, maliyet ${cost:.2f}" if cost else f"FABLE TOPLU — {n} durum")
    print("=" * 60)
    print(f"  OPEN: {graded + dir_mismatch} (grade'li {graded}, yön-eşleşmedi {dir_mismatch}) | WAIT: {wait}")
    if graded:
        print(f"  Fable WR: {100*win/graded:.0f}% ({win}/{graded}) | EV: {ev_sum/graded:+.3f}R/işlem")
    # Opus kıyası (aynı kayıtların canlı kararları — lokal, Fable görmedi)
    o_win = o_loss = o_open = 0
    for e in key.values():
        if str((e.get("decision") or {}).get("action", "")).upper() == "OPEN":
            o_open += 1
            if e.get("outcome") == "WIN":
                o_win += 1
            elif e.get("outcome") == "LOSS":
                o_loss += 1
    if o_win + o_loss:
        print(f"  Opus (canlı, aynı kayıtlar): WR {100*o_win/(o_win+o_loss):.0f}% ({o_win}/{o_win+o_loss}), {o_open} OPEN")
    naive_w = sum(1 for e in key.values() if e["cf_outcome"] == "WIN")
    print(f"  Naive-gate (hepsini aç): WR {100*naive_w/len(key):.0f}% ({naive_w}/{len(key)})")
    if cost:
        canli_maliyet = n * 0.55
        print(f"  💰 Tasarruf: canlı shadow olsaydı ~${canli_maliyet:.0f}; toplu çağrı ${cost:.2f} "
              f"(~{canli_maliyet/max(cost,0.01):.0f}× ucuz)")
    if write:      # değerlendirilenleri işaretle (tekrar sorulmasın)
        rows = [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
        marked = {id(e) for e in key.values()}
        by_ts = {e.get("ts"): a for a in answers for e in [key.get(a.get("i"))] if e}
        for r in rows:
            a = by_ts.get(r.get("ts"))
            if a:
                r.setdefault("batch_eval", {})[MODEL] = {"action": a.get("action"),
                                                         "direction": a.get("direction"),
                                                         "size": a.get("size")}
        with open(JOURNAL_JSONL, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  → journal'a batch_eval işlendi (aynı kayıtlar tekrar sorulmaz).")


def main():
    limit = MAX_PER_CALL
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            limit = int(a.split("=")[1])
    packs, key = build_batch(limit)
    print(f"Ölçülebilir (cf-grade'li, daha önce sorulmamış) kayıt: {len(packs)}")
    if not packs:
        print("⏳ değerlendirilecek yeni kayıt yok."); return
    if "--dry-run" in sys.argv:
        print("\n[DRY-RUN] Fable'a gidecek örnek paket (SIZINTI YOK — fiyat/zaman/sonuç/Opus-kararı sıyrıldı):")
        print(json.dumps(packs[0], ensure_ascii=False, indent=1))
        print(f"\nleak_guard: {len(packs)} paket beyaz-listeden geçti ✓  (çağrı yapılmadı)")
        return
    evaluate(packs, key, write="--write" in sys.argv)


if __name__ == "__main__":
    main()
