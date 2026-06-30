@echo off
chcp 65001 >nul
title ForexSAI - Kalibrasyon (tahminler tutuyor mu)
echo  [1] Kanit base-rate'leri kalibre mi? (%85 dedigi canli %85 mi)
echo  [2] size_factor guvenilir mi? (Opus'un konviksiyon'u sinyal mi)
echo  Veri biriktikce (birkac gun sonra) calistir.
cd /d "%~dp0..\claude_decider"
python calibration.py
echo.
pause
