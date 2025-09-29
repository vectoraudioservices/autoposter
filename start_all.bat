@echo off
setlocal
cd /d "%~dp0"
call "%~dp0start_watcher.bat"
call "%~dp0start_runner.bat"
echo Started watcher and runner.
endlocal


