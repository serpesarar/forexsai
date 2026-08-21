@echo off
chcp 65001 >nul
title ForexSAI - Toplu Model Analizi (Fable + Sonnet, sizintisiz)
echo  Biriken kararlari TEK cagriyla degerlendirir — IKI model AYNI paketleri
echo  gorur (adil A/B). SIZINTI YOK: sonuc/fiyat/zaman/karar siyrilir + shuffle.
echo  Gunde 1 kez yeter (~2 cagri toplam).
echo.
echo  Kumulatif skorbord icin: python batch_eval.py --report
echo  On-izleme (cagri yok):   python batch_eval.py --dry-run
echo ============================================================
cd /d "%~dp0..\claude_decider"
python batch_eval.py --model=claude-fable-5 --write
python batch_eval.py --model=claude-sonnet-5 --write
echo.
echo ──────────── KUMULATIF SKORBORD ────────────
python batch_eval.py --report
echo.
pause
