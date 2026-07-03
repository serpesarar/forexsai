@echo off
chcp 65001 >nul
title ForexSAI - SL Otopsisi (post-mortem)
echo  Kaybedenleri kazananlardan AYIRAN kosulu bulur (placebo-kapili):
echo  hacim, VIX, DXY, kanal mesafesi, multi-TF S/R yakinligi+gucu...
echo.
echo  Ek modlar (CMD'den):
echo    python post_mortem.py --llm     (Fable nitel otopsi - hipotez cumleleri)
echo    python post_mortem.py --write   (adaylari LESSONS'a 'izlenen' ekle)
echo  Veri biriktikce (birkac gun) calistir.
cd /d "%~dp0..\claude_decider"
python post_mortem.py
echo.
pause
