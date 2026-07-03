@echo off
REM Chay Speak Grader tren Windows. Double-click file nay hoac chay trong CMD.
cd /d "%~dp0"

REM Cai uv neu chua co (uv tu lo Python + thu vien).
where uv >nul 2>nul
if %errorlevel% neq 0 (
  echo Chua co uv - dang cai dat mot lan duy nhat...
  powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

REM Tao .env neu chua co.
if not exist ".env" (
  echo Chua co file .env. Tao tu mau...
  copy ".env.example" ".env" >nul
  echo Hay mo .env va dan GEMINI_API_KEY cua ban ^(lay free tai https://aistudio.google.com^).
)

echo Khoi dong app... lan dau uv se tai thu vien, hoi lau mot chut.
REM --no-dev: chi cai thu vien chay app, bo qua nhom dev (pytest...) de nhe may.
uv run --no-dev app.py
pause
