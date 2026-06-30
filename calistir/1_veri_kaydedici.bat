@echo off
chcp 65001 >nul
title ForexSAI - 1) Veri Kaydedici (data_recorder)
echo ============================================================
echo  VERI KAYDEDICI - MT5 (IC Markets) - Supabase OHLC+indikator
echo  Bu pencereyi ACIK birak. Kapatirsan kayit durur.
echo ============================================================
cd /d "%~dp0..\yeni deneme"
python data_recorder.py
echo.
echo [DURDU] Bir hata olduysa yukarida gorunur.
pause
