@echo off
setlocal
set "ROOT=%~dp0"
pushd "%ROOT%"

echo === DEBUG: Listing relevant processes ===
echo.
echo -- CMD windows with titles:
powershell -NoProfile -Command "Get-Process cmd -ErrorAction SilentlyContinue | Select-Object Id,MainWindowTitle | Format-Table -AutoSize"

echo.
echo -- Python processes and their command lines (filtered to 'autoposter'):
powershell -NoProfile -Command ^
  "$p = Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*.exe' -and $_.CommandLine -match 'autoposter' }; if ($p) { $p | Select-Object ProcessId, Name, CommandLine | Format-Table -AutoSize } else { 'None' }"

echo.
echo -- PID files (if any):
for %%F in (logs\watcher.pid logs\runner.pid) do (
  if exist "%%F" (
    set /p P=<"%%F"
    echo %%F = !P!
  ) else (
    echo %%F = (missing)
  )
)

echo.
echo === Attempting gentle kill by window title ===
taskkill /FI "WINDOWTITLE eq Autoposter Watcher" /T /F
taskkill /FI "WINDOWTITLE eq Autoposter Runner"  /T /F
taskkill /FI "WINDOWTITLE eq Autoposter Watcher*" /T /F
taskkill /FI "WINDOWTITLE eq Autoposter Runner*"  /T /F

echo.
echo === Attempting kill by PID files ===
for %%F in (logs\watcher.pid logs\runner.pid) do (
  if exist "%%F" (
    set /p P=<"%%F"
    if not "!P!"=="" taskkill /PID !P! /T /F
  )
)

echo.
echo === Attempting kill by command line match ===
powershell -NoProfile -Command ^
  "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*.exe' -and ($_.CommandLine -match 'autoposter\\main\\.py' -or $_.CommandLine -match 'autoposter\\scripts\\queue_runner\\.py') }; if ($procs) { $procs | ForEach-Object { Write-Host ('Killing PID ' + $_.ProcessId + ' : ' + $_.CommandLine); Stop-Process -Id $_.ProcessId -Force } } else { 'None to kill' }"

echo.
echo === Remaining cmd windows (post-kill) ===
powershell -NoProfile -Command "Get-Process cmd -ErrorAction SilentlyContinue | Select-Object Id,MainWindowTitle | Format-Table -AutoSize"

echo.
pause
popd
endlocal
