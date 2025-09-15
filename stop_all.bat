@echo off
setlocal
set "BASE=%USERPROFILE%\Desktop\autoposter"
set "LOGS=%BASE%\logs"

echo Stopping Autoposter...

rem 1) Kill Python child processes by PID files (precise)
for %%F in (watcher.pid runner.pid) do (
  if exist "%LOGS%\%%F" (
    for /f "usebackq delims=" %%P in ("%LOGS%\%%F") do (
      for /f "tokens=1 delims= " %%Q in ("%%P") do (
        echo - Killing python PID %%Q from %%F...
        taskkill /PID %%Q /T /F >nul 2>&1
      )
    )
  )
)

rem 2) Close any leftover cmd windows by title (explicit PowerShell call)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-Process cmd -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*AUTOP_WATCHER*' -or $_.MainWindowTitle -like '*Autoposter - Watcher*' } | ForEach-Object { Write-Output ('- Closing watcher window PID {0}' -f $_.Id); Stop-Process -Id $_.Id -Force }"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-Process cmd -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*AUTOP_RUNNER*' -or $_.MainWindowTitle -like '*Autoposter - Runner*' } | ForEach-Object { Write-Output ('- Closing runner window PID {0}' -f $_.Id); Stop-Process -Id $_.Id -Force }"

echo Stopped watcher and runner (if they were running).
pause
endlocal





