@echo off
set "ROOT=%~dp0"
"%ROOT%venv\Scripts\python.exe" "%ROOT%scripts\queue_fast_forward.py" --seconds 5
pause
