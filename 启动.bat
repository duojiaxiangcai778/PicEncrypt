@echo off
chcp 65001 >nul
cd /d E:\图片混淆
echo 清理Python缓存...
if exist __pycache__ rmdir /s /q __pycache__
if exist .venv\Lib\site-packages\PIL\__pycache__ rmdir /s /q .venv\Lib\site-packages\PIL\__pycache__
echo 清理完成
echo.
echo 当前目录文件:
dir /b
echo.
echo 按任意键运行程序...
pause >nul
uv run python PicEncryptWin.py
pause
