@echo off
chcp 65001 >nul
title ForexSAI - Tick Kaydedici (yerel disk)
echo  MT5'ten bid/ask tick'leri ceker, YEREL diske yazar:
echo  "yeni deneme\tickdata\SEMBOL\YYYY-AA-GG.csv.gz"  (gunluk gzip)
echo  Hacim: ~1-2 MB/gun/sembol. Supabase'e YAZMAZ.
echo.
echo  Amac: scalp refleks motoru icin karar-ani spread + mikro-yapi arsivi.
echo  Restart guvenli: state.json ile kaldigi yerden devam eder.
echo.
echo  ACIK KALSIN (1-4 numarali bat'lar gibi surekli calisir).
echo  Terminal: IC Markets (data_recorder ile ayni config).
echo ============================================================
cd /d "%~dp0..\yeni deneme"
python tick_recorder.py
echo.
pause
