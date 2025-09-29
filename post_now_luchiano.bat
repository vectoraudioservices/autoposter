@echo off
set "ROOT=%~dp0"
cd /d "%ROOT%"
powershell -NoProfile -Command "$ts=(Get-Date).ToString('yyyyMMdd_HHmmss'); Copy-Item 'content\ig_live_smoke_test.jpg' ('content\Luchiano\post_'+$ts+'.jpg')"
echo Dropped a new test post for Luchiano.
pause
