@echo off
chcp 65001 >nul
title ForexSAI - Cikis Stratejisi Optimizasyonu
echo  Hangi cikis (sabit/trailing/breakeven/time) sembol basina en karli?
echo  Her islem 6 cikisla grade edildi; en yuksek ATR/islem kazanan.
echo  Veri biriktikce (birkac gun sonra) calistir.
cd /d "%~dp0..\claude_decider"
python exit_compare.py
echo.
pause
