@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo PDF Master startup

where node >nul 2>&1 || (echo ERROR: Node.js is not installed & exit /b 1)
where npm >nul 2>&1 || (echo ERROR: npm is not installed & exit /b 1)
where python >nul 2>&1 || (echo ERROR: Python is not installed & exit /b 1)

if not exist "backend\venv\Scripts\python.exe" (
  python -m venv backend\venv || (echo ERROR: Could not create backend virtual environment & exit /b 1)
)

echo Installing backend dependencies...
backend\venv\Scripts\python.exe -m pip install --upgrade pip >nul
backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt || (echo ERROR: Backend dependency installation failed & exit /b 1)

echo Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
  echo ERROR: Frontend dependency installation failed
  exit /b 1
)
cd ..

curl -fsS http://127.0.0.1:8000/health >nul 2>&1
if errorlevel 1 (
  echo Starting backend...
  powershell -NoProfile -Command "$p = Start-Process -PassThru -WorkingDirectory '%~dp0backend' -FilePath '%~dp0backend\venv\Scripts\python.exe' -ArgumentList '-m uvicorn main:app --host 127.0.0.1 --port 8000'; Set-Content -Path '%~dp0backend.pid' -Value $p.Id"
)

for /l %%i in (1,1,30) do (
  curl -fsS http://127.0.0.1:8000/health >nul 2>&1 && goto backend_ready
  timeout /t 1 /nobreak >nul
)
echo ERROR: Backend did not become healthy
exit /b 1

:backend_ready
curl -fsS http://127.0.0.1:3000 >nul 2>&1
if errorlevel 1 (
  echo Starting frontend...
  cd frontend
  for /f "delims=" %%p in ('powershell -NoProfile -Command "$p = Start-Process -PassThru -WorkingDirectory '%~dp0frontend' -FilePath 'npm.cmd' -ArgumentList 'run dev -- --host 127.0.0.1'; $p.Id"') do set "FRONTEND_PID=%%p"
  echo %FRONTEND_PID%>"%~dp0frontend.pid"
  cd ..
)

for /l %%i in (1,1,30) do (
  curl -fsS http://127.0.0.1:3000 >nul 2>&1 && goto frontend_ready
  timeout /t 1 /nobreak >nul
)
echo ERROR: Frontend did not become ready
exit /b 1

:frontend_ready
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:3000
echo API docs: http://127.0.0.1:8000/api/docs
start "" http://localhost:3000
exit /b 0
