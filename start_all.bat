@echo off
cd /d C:\autoposter
start "watcher" cmd /k venv\Scripts\python main.py
start "runner"  cmd /k venv\Scripts\python scripts\queue_runner.py
