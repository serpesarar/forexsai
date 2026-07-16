@echo off
rem Evrim Ajanı başlatıcı — pencere kapansa da yeniden dener
cd /d "%~dp0"
:loop
python evolution_agent.py
echo Ajan durdu, 30 sn sonra yeniden baslatiliyor...
timeout /t 30 /nobreak >nul
goto loop
