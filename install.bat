@echo off
cd /d "%~dp0"
where py >nul 2>nul || (echo Install Python 3.9 or newer from python.org and add it to PATH.& pause & exit /b 1)
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\python.exe -m pip install --upgrade pip
call .venv\Scripts\python.exe -m pip install -e .
echo Installed. Run: .venv\Scripts\pealang.exe examples\hello.pea
