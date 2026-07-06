@echo off
chcp 65001 >nul
title ForexSAI - Gosterge Olay Taramasi (indicator_snapshots)
echo  data_recorder'in biriktirdigi 29 gostergedeki OLAYLARI tarar
echo  (MACD/RSI/Stoch/BB/VWAP/SAR/ADX/EMA kesisim ve esik asimlari) ve
echo  her birinin scalp ayirt gucunu olcer: 1:1 ATR ilk-temas, placebo,
echo  IS/OOS. Cita: *plasebo-ustu + OOS>=50 + n>=30 birlikte.
echo.
echo  Ek modlar (CMD'den):
echo    python indicator_event_scan.py --symbol XAU   (tek sembol)
echo    python indicator_event_scan.py --days 14      (son 14 gun)
echo.
echo  Veri biriktikce (30+ gun) haftada 1 calistirmak yeterli.
echo  NOT: 2026-07-03 MACD kesisimi bu bataryadan GECEMEDI (referans:
echo  research/macd_cross_scalp_analysis.py) — cita herkes icin ayni.
echo ============================================================
cd /d "%~dp0..\claude_decider"
python indicator_event_scan.py
echo.
pause
