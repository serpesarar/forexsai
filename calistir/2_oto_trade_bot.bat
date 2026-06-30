@echo off
chcp 65001 >nul
title ForexSAI - 2) Oto Trade Bot
echo ============================================================
echo  OTO TRADE BOT - MT5 (IC Markets) - kural-bazli scope'lar
echo  Bu pencereyi ACIK birak. MT5 terminali ACIK + AutoTrading
echo  (Algo Trading) YESIL olmali, yoksa emir gonderemez.
echo ============================================================
cd /d "%~dp0..\yeni deneme"
python forexsai_demo_bot.py
echo.
echo [DURDU] Bir hata olduysa yukarida gorunur.
pause
