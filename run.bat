@echo off
cd /d "%~dp0"
del /s /q __pycache__ 2>nul
rmdir /s /q __pycache__ 2>nul
chcp 65001 >nul
uv run python PicEncryptWin.py
if errorlevel 1 (
    echo.
    echo If failed, try double-clicking "tu pian hun xiao.exe"
    pause
)
