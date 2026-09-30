@echo off
cd /d "%~dp0"
python scripts/install.py --install %*
exit /b %errorlevel%
