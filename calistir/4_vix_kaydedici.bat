@echo off
chcp 65001 >nul
title ForexSAI - 4) VIX Kaydedici (Pepperstone)
echo ============================================================
echo  VIX KAYDEDICI - Pepperstone canli VIX - Supabase vix_live
echo  ASAGIDAKI Pepperstone terminal YOLUNU kendi kurulumuna gore
echo  duzenle (bat'a sag tikla - Duzenle). Terminal ACIK olmali.
echo ============================================================
cd /d "%~dp0..\claude_decider"
python vix_recorder.py --terminal "C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"
echo.
echo [DURDU] 'VIX sembolu bulunamadi' derse Market Watch'a VIX ekle.
pause
