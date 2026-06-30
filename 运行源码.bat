@echo off
chcp 65001 >nul
cd /d "%~dp0"
uv run python PicEncryptWin.py
if errorlevel 1 (
    echo.
    echo 运行失败，请尝试双击「图片混淆.exe」
    pause
)
