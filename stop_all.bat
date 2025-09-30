@echo off
for %%F in (logs\watcher.pid logs\runner.pid) do (
  if exist "%%F" (
    for /f %%P in (%%F) do taskkill /PID %%P /F >nul 2>&1
    del /q "%%F" 2>nul
  )
)











