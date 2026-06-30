@echo off
chcp 65001 >nul
title ForexSAI - Decider Ogrenme (haftalik)
echo  Decider'in kendi gecmisini re-damitir (kanit-kapili ders cikarma).
echo  Haftada bir calistir. LESSONS.md'yi gunceller.
cd /d "%~dp0..\claude_decider"
python distill_journal.py
echo.
pause
