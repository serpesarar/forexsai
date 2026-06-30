@echo off
chcp 65001 >nul
title ForexSAI - Evidence Tazeleme (base-rate guncelle)
echo  Base-rate'leri canli journal deneyimiyle blend eder (Bayesyen).
echo  ONCE DRY-RUN: sadece hangi hucreler degisecek gosterir (yazMAZ).
echo  Kalibrasyon "sisik" dediyse veya birkac haftada bir calistir.
echo.
echo  Yazmak icin (degisiklikleri onayladiktan sonra) CMD'de:
echo    python claude_decider\refresh_evidence.py --apply
echo  (once otomatik yedek alir)
echo ============================================================
cd /d "%~dp0..\claude_decider"
python refresh_evidence.py
echo.
pause
