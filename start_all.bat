@echo off
set "BASE=%USERPROFILE%\Desktop\autoposter"
if not exist "%BASE%" echo Folder not found: %BASE% & pause & exit /b
if not exist "%BASE%\start_watcher.bat" echo Missing: %BASE%\start_watcher.bat & pause & exit /b
if not exist "%BASE%\start_runner.bat"  echo Missing: %BASE%\start_runner.bat  & pause & exit /b

rem Use /c so each window closes when its batch finishes (after Python ends)
start "AUTOP_WATCHER" /D "%BASE%" cmd /c start_watcher.bat
start "AUTOP_RUNNER"  /D "%BASE%" cmd /c start_runner.bat
