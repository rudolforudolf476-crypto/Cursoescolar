@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Execute primeiro os comandos de instalacao do README.md.
  pause
  exit /b 1
)
.venv\Scripts\python.exe aimassist.py %*
pause
