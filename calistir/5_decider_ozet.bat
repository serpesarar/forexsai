@echo off
chcp 65001 >nul
title ForexSAI - Decider Performans Ozeti
echo  Decider'in simdiye kadarki WR/EV ozeti (islem ACMAZ, sadece okur):
cd /d "%~dp0..\claude_decider"
python outcomes.py
echo.
pause
