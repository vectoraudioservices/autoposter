@echo off
title AUTOP_RUNNER
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
call "%~dp0venv\Scripts\activate"
python "%~dp0scripts\queue_runner.py"

