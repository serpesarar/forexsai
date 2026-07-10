@echo off
chcp 65001 >nul
title ForexSAI - Meta-Allocator (motor bazli sermaye tahsisi)
echo  GERCEK MT5 sonuclarindan motor bazli rolling-EV olcer ve onerilen
echo  lot carpanlarini verir (kanayan 0.25x, kazanan 1.5x'e kadar).
echo  Once MT5'ten deal export CSV'si gerekir (paket formatinda).
echo.
echo  Kullanim (CMD'den, CSV yolunu ver):
echo    python allocator.py --deals=..\mt5_deals.csv --days=7
echo  Haftada 1 kos; onerileri config.py lot carpanlarina ELLE yansit.
echo ============================================================
cd /d "%~dp0..\claude_decider"
python allocator.py %*
echo.
pause
