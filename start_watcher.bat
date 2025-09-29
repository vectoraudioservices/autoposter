@echo off
setlocal
cd /d "%~dp0"
set "PY=%CD%\venv\Scripts\python.exe"
set "SCRIPT=%CD%\main.py"
start "Autoposter Watcher" cmd /c "chcp 65001>nul & set PYTHONIOENCODING=utf-8 & title Autoposter Watcher & "%PY%" -u "%SCRIPT%""
endlocal




