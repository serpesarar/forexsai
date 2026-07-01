@echo off
chcp 65001 >nul
title ForexSAI - Model Kiyas (Opus vs Fable5)
echo  Ayni veriye Opus 4.8 ve Fable 5 karar verdi; hangisi iyi?
echo  Karar anlasmasi + acilan islem kalitesi + ayrisma kimin lehine.
echo  Veri biriktikce (birkac gun sonra) calistir.
cd /d "%~dp0..\claude_decider"
python model_compare.py
echo.
pause
