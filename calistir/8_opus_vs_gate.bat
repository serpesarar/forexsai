@echo off
chcp 65001 >nul
title ForexSAI - Opus vs Gate Baseline
echo  Opus'un secimi "her gate'te ac" aptal kuralindan iyi mi?
echo  Beyin deger katiyor mu / quota'yi hak ediyor mu?
echo  Veri biriktikce (birkac gun sonra) calistir.
cd /d "%~dp0..\claude_decider"
python baseline_compare.py
echo.
pause
