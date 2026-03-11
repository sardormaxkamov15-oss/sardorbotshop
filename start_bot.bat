@echo off
title GYM FOOD Bot
color 0A

echo =======================================
echo     GYM FOOD Bot ishga tushmoqda...
echo =======================================

:loop
python main.py
echo.
echo [!] Bot to'xtab qoldi. 5 soniyadan muhit avtomatik qayta tiklanadi...
timeout /t 5 >nul
goto loop
