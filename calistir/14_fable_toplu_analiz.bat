@echo off
chcp 65001 >nul
title ForexSAI - Fable Toplu Analiz (tek cagri, sizintisiz)
echo  Biriken kararlari TEK cagriyla Fable'a degerlendirtir (canli shadow yerine).
echo  SIZINTI YOK: sonuc/fiyat/zaman/Opus-karari siyrilir + kayitlar karistirilir.
echo  Gunde 1 kez yeter. Once ne gidecegini gormek icin CMD'den:
echo    python batch_eval.py --dry-run
echo  Degerlendirilenleri isaretlemek icin (tekrar sorulmaz):
echo    python batch_eval.py --write
echo ============================================================
cd /d "%~dp0..\claude_decider"
python batch_eval.py --write
echo.
pause
