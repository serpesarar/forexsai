@echo off
chcp 65001 >nul
title ForexSAI - 23) DBG canli izleyici (SALT-OKUMA)
echo ============================================================
echo  DBG 303733 gercek botunu izler. Emir gondermez, sifre islemez.
echo  Terminal: C:\Program Files\MetaTrader 5 (investor girisi).
echo  Botun Pepperstone terminaline dokunmaz.
echo  Veri: %%LOCALAPPDATA%%\dbg_izleyici
echo  Ozet: python calistir\dbg_izleyici\dbg_izleyici_ozet.py
echo ============================================================
cd /d "%~dp0dbg_izleyici"
python dbg_izleyici.py
echo.
echo [DURDU] Bir hata olduysa yukarida gorunur.
pause
