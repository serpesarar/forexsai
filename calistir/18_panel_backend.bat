@echo off
chcp 65001 >nul
title ForexSAI - 18) Panel Backend
echo ============================================================
echo  PANEL BACKEND (FastAPI) - Evrim Paneli + ajan tartismasi
echo  + gunluk analist + lifecycle bu surecte calisir.
echo  Bu pencereyi ACIK birak. Kapanirsa 15 sn sonra kendini acar.
echo ============================================================
cd /d "%~dp0..\backend"
:loop
python -m uvicorn main:app --host 0.0.0.0 --port 8000
echo.
echo [DURDU] 15 sn sonra yeniden baslatiliyor... (CTRL+C ile iptal)
timeout /t 15 /nobreak >nul
goto loop
