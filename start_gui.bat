@echo off
setlocal
set "ROOT=%~dp0"
pushd "%ROOT%"
set "PYEXE=%ROOT%venv\Scripts\python.exe"
if not exist "%PYEXE%" (
  echo venv python not found at "%PYEXE%"
  pause
  popd
  exit /b 1
)
start "Autoposter GUI" cmd /k ""%PYEXE%" -u "%ROOT%gui\control_panel.py""
popd
endlocal
