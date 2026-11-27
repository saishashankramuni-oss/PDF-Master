@echo off
setlocal
cd /d "%~dp0"

if exist backend.pid (
  set /p BACKEND_PID=<backend.pid
  powershell -NoProfile -Command "if ($env:BACKEND_PID) { Stop-Process -Id ([int]$env:BACKEND_PID) -Force -ErrorAction SilentlyContinue }"
  del backend.pid
)
if exist frontend.pid (
  set /p FRONTEND_PID=<frontend.pid
  powershell -NoProfile -Command "if ($env:FRONTEND_PID) { Stop-Process -Id ([int]$env:FRONTEND_PID) -Force -ErrorAction SilentlyContinue }"
  del frontend.pid
)

echo PDF Master services stopped.
