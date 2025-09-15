@echo off
cd /d C:\Users\Owner\Desktop\autoposter
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
call venv\Scripts\activate
python scripts\status.py
echo.
pause
