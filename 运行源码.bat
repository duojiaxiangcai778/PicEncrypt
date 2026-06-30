@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 清理Python字节码缓存...
if exist __pycache__ rmdir /s /q __pycache__
if exist .venv\__pycache__ rmdir /s /q .venv\__pycache__
echo 启动中...

uv run python PicEncryptWin.py
if errorlevel 1 (
    echo.
    echo 运行失败，请尝试双击「图片混淆.exe」
    pause
)
