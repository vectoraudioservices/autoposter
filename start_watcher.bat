@echo off
title AUTOP_WATCHER
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
call "%~dp0venv\Scripts\activate"
python "%~dp0main.py"

