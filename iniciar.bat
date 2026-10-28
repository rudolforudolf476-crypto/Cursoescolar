@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Execute primeiro os comandos de instalacao do README.md.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -X faulthandler -u aimassist.py %*
set "aimassist_exit=%errorlevel%"
echo.
echo Programa terminou com codigo %aimassist_exit%. Consulte aimassist.log nesta pasta.
pause
exit /b %aimassist_exit%
