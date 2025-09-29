@echo off
setlocal
cd /d "%~dp0"
set "PY=%CD%\venv\Scripts\python.exe"
set "SCRIPT=%CD%\scripts\queue_runner.py"
start "Autoposter Runner" cmd /c "chcp 65001>nul & set PYTHONIOENCODING=utf-8 & title Autoposter Runner & "%PY%" -u "%SCRIPT%""
endlocal




