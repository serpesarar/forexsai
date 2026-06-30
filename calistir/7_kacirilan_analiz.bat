@echo off
chcp 65001 >nul
title ForexSAI - Kacirilan Firsat Analizi (recall)
echo  Decider'in ACMADIGI islemlerden hangileri kazanirdi? (karsi-olgu)
echo  Fazla korumaci filtre var mi + yeni filtre adayi (placebo-kapili).
echo  Veri biriktikce (birkac gun sonra) calistir.
cd /d "%~dp0..\claude_decider"
python analyze_missed.py
echo.
pause
