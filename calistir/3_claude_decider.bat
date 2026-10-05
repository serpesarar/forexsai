@echo off
chcp 65001 >nul
title ForexSAI - 3) Claude Decider (Opus)
echo ============================================================
echo  CLAUDE DECIDER - Pepperstone MT5 + Opus (claude -p)
echo  Gerekli: Pepperstone terminali ACIK + Claude Code login.
echo  Bu pencereyi ACIK birak. CANLI mod: DEMO hesapta kucuk boyutla (<=0.03 lot) emir acar.
echo  Kill-switch: claude_decider\EXECUTE_OFF dosyasi olustur veya DECIDER_EXECUTE=0.
echo ============================================================
cd /d "%~dp0..\claude_decider"
python run_decider.py --live
echo.
echo [DURDU] Bir hata olduysa yukarida gorunur.
pause
