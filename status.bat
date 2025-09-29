@echo off
setlocal
cd /d "%~dp0"

:: Robust status using PowerShell only (no tasklist filters)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue';" ^
  "$root = Convert-Path '.';" ^
  "$watcher = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match [Regex]::Escape('\\autoposter\\main.py') };" ^
  "$runner  = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match [Regex]::Escape('\\autoposter\\scripts\\queue_runner.py') };" ^
  "Write-Host '=== Autoposter Status ===';" ^
  "if ($watcher) { Write-Host ('Watcher: RUNNING (PID: {0})' -f ($watcher.ProcessId)) } else { Write-Host 'Watcher: STOPPED' };" ^
  "if ($runner)  { Write-Host ('Runner : RUNNING (PID: {0})'  -f ($runner.ProcessId)) } else { Write-Host 'Runner : STOPPED' };" ^
  ""; ^
  "try {" ^
  "  $q = & '$root\\venv\\Scripts\\python.exe' '$root\\scripts\\db_queue_inspect.py' 2>$null;" ^
  "} catch { $q = $null }" ^
  "if ($q) { Write-Host ''; Write-Host $q } else { Write-Host ''; Write-Host 'Queue: (db_queue_inspect.py not available or venv not active)'; };" ^
  ""; ^
  "Write-Host ''; Write-Host '--- Tail logs/autoposter.log (last ~10) ---';" ^
  "if (Test-Path '$root\\logs\\autoposter.log') { Get-Content -Path '$root\\logs\\autoposter.log' -Encoding UTF8 -Tail 10 | Write-Host } else { Write-Host '(no log yet)' };" ^
  ""; ^
  "Write-Host ''; Write-Host '--- Tail logs/post_runner.log (last ~10) ---';" ^
  "if (Test-Path '$root\\logs\\post_runner.log') { Get-Content -Path '$root\\logs\\post_runner.log' -Encoding UTF8 -Tail 10 | Write-Host } else { Write-Host '(no log yet)' };" ^
  ""
endlocal

