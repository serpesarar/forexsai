@echo off
chcp 65001 >nul
title ForexSAI - 3) Claude Decider (Opus)
echo ============================================================
echo  CLAUDE DECIDER - Pepperstone MT5 + Opus (claude -p)
echo  Gerekli: Pepperstone terminali ACIK + Claude Code login.
echo  Bu pencereyi ACIK birak. Shadow mod (islem ACMAZ, kaydeder).
echo ============================================================
cd /d "%~dp0..\claude_decider"
python run_decider.py
echo.
echo [DURDU] Bir hata olduysa yukarida gorunur.
pause
