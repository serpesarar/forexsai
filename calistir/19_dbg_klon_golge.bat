@echo off
chcp 65001 >nul
title ForexSAI - 19) DBG klon izgarasi (GOLGE)
echo ============================================================
echo  DBG 303733 botunun klonu - GOLGE: hic emir gondermez, yalniz log yazar.
echo  Terminal: Pepperstone (botla ayni, salt-okuma). Magic 52896686.
echo  Log: calistir\dbg_klon\dbg_klon_log.jsonl
echo  Kanit: research/dbg_xau_tersine_20261029/RAPOR.md (kenar yok, kart RED)
echo  CANLI mod bu bat'ta YOK - bilincli olarak.
echo ============================================================
cd /d "%~dp0dbg_klon"
python dbg_klon_runner.py --terminal "C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"
echo.
echo [DURDU] Bir hata olduysa yukarida gorunur.
pause
