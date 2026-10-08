# Sonuç — claude_decider: SL otopsisi + sembol başına kural araması (2026-10-08)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) · `pull.py` → `analyze.py` → `placebo.py` · ham: `results/`.
`decider_journal` 2026-06-30 → 10-08: 1.750 OPEN + 1.701 WAIT karşı-olgusu (batch_eval ve sahte "claude exit"
satırları dışarıda). Tek-pozisyon bağımsızlaştırmasından sonra **452 bağımsız OPEN** (DAX 89, NDX 157, USOIL 88,
XAU 118) ve 828 WAIT-cf. Not: ham kayıtların ~%75'i aynı fırsatın tekrar kaydı (E6).

## 1. Decider'ın seçimi değer katıyor mu? (açtı vs açmadığı fırsatlar)

| sembol-yön | OPEN ort R (n) | WAIT-cf ort R (n) | hüküm |
|---|---:|---:|---|
| XAU BUY | +0,06 (99) | **−0,14** (208, P(>0)=%0) | seçim değerli; iki yarıda da + (+0,05/+0,07) |
| DAX BUY | +0,07 (75) | −0,02 (102) | hafif + |
| NDX SELL | +0,04 (101) | −0,04 (69) | hafif + |
| **NDX BUY** | **−0,20** (56, P(>0)=%4) | −0,02 (114) | **seçim zararlı**; yarılar +0,01 / −0,40 |
| **USOIL SELL** | **−0,13** (88, P(>0)=%9) | +0,04 (134) | **seçim zararlı**; yarılar −0,01 / −0,24 |
| XAU SELL / DAX SELL | −0,21 (19) / +0,07 (14) | — / +0,04 | küçük örneklem |

## 2. SL anatomisi — mekanik mi?
Decider'ın SL'leri, açmadığı fırsatların SL'leriyle aynı yapıda: hiç çalışmadı %48–53 (WAIT-cf %57–63),
önce ≥0,3R kâr %25–39, TP'nin ≥%70'ine gelip dönen %11–16 (WAIT-cf %18–26). Tek istisna USOIL: decider'ın
USOIL SL'lerinin %48'i hiç çalışmamış (WAIT-cf %26) → USOIL'de giriş zamanlaması fırsat tabanından kötü.

## 3. Sembol başına kural araması — tesadüften ayırt edilemiyor
4 sembol × (sembol + sembol-yön) × tekli/ikili AND, ileri 3.352 + geri 2.363 kural.
- Eğitim↔sınama Spearman: DAX −0,14/+0,14, NDX +0,34/−0,04, USOIL −0,03/−0,08, XAU +0,25/+0,08 (ileri/geri).
- İki yönde de geçen kural: **gerçek 138**, plasebo (sonuç sembol içinde karıştırılmış, 10 tekrar) **medyan 142,
  aralık 79–177**. NDX 91 (plasebo 18–107) — üst bölgede ama anlamlı değil.
→ Göstergelerden (ADX, VWAP-z, kanal, S/R uzaklığı, hacim, saat, model…) türetilen tek bir eşik kuralına güvenilemez.

## 4. Ayakta kalan iki aday (bağımsız önceki kanıtla aynı yönde)
- **D4 — VIX < 18,4 iken NDX BUY açma.** Decider NDX BUY'larının 45'inden 44'ü VIX rejimine karşı; bu 44 → −0,13R.
  Bağımsız kanıt: K1 VIX_REGIME_GATE (A sınıfı, 10 yıl, plasebo p=0, OOS +17pp), D3'ün aynası.
  Zayıflık: aylık tutarsız (Tem −0,01, Ağu −0,58, Eyl +0,06) → B.
- **D5 — USOIL SELL'i decider'da da kapat.** −0,13R (n=88), açmadığı USOIL SELL'ler +0,04R; 4 ayın 3'ünde ≤0.
  Bağımsız kanıt: bot B1 (USOIL SELL 47 işlem WR %21,3 −21,7R, AKTİF). Zayıflık: Eylül +0,04 → B.
Her ikisi de karar günlüğünden geriye dönük ölçülebilir (`vix_favors_dir`, `dir`) — gölge için kod gerekmez.
Canlıya alma: kullanıcı kararı + D3 ile birlikte değerlendirme.
