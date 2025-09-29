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

echo.
echo Usage example:
echo   add_client.bat "MerkabaEntertainment" --quota 2 --hours 11 15 19 --ig-username merkaba_official
echo.

"%PYEXE%" "%ROOT%scripts\add_client.py" %*

echo.
pause
popd
endlocal
