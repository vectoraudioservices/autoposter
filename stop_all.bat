@echo off
setlocal
cd /d "%~dp0"
echo Stopping Autoposter...

:: Use PowerShell only (avoids CMD quoting issues)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue';" ^
  "$titles=@('Autoposter Watcher','Autoposter Runner','Autoposter Web Panel');" ^
  "Get-Process | Where-Object { $titles -contains $_.MainWindowTitle } | Stop-Process -Force;" ^
  "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'autoposter\\(scripts\\queue_runner\\.py|main\\.py|server\\web_panel\\.py)' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force };" ^
  "Remove-Item -Force 'logs\\watcher.pid','logs\\runner.pid' -ErrorAction SilentlyContinue;" ^
  "Write-Host 'Stopped watcher and runner (if they were running).'"

endlocal












