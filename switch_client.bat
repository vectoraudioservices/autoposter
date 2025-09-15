@echo off
setlocal
cd /d "%USERPROFILE%\Desktop\autoposter"

if not exist "venv\Scripts\python.exe" (
  echo Error: venv not found at "%CD%\venv\Scripts\python.exe"
  echo Open a terminal and run:  python -m venv venv
  echo then install deps again in the venv if needed.
  echo.
  pause
  exit /b 1
)

call "venv\Scripts\activate"

rem If no client name is provided, show usage + available clients (the Python script handles this)
if "%~1"=="" (
  python scripts\switch_client.py
) else (
  python scripts\switch_client.py %*
)

echo.
pause
endlocal


