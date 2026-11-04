@echo off
chcp 65001 >nul
title ForexSAI - 24) Coklu sembol klon (GOLGE)
echo ============================================================
echo  DBG izgara klonu: NAS100, GER40, SpotCrude + referans XAUUSD.
echo  TAMAMEN SANAL: hic emir gondermez, yalniz tick okur.
echo  Veri: %%LOCALAPPDATA%%\klon_coklu
echo  Ozet: python calistir\klon_coklu\klon_coklu_ozet.py
echo ============================================================
cd /d "%~dp0klon_coklu"
python klon_coklu.py
echo.
echo [DURDU] Bir hata olduysa yukarida gorunur.
pause
