@echo off
call .venv\Scripts\activate.bat

echo.
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building executable...
pyinstaller widget.spec

echo.
echo Build complete! Executable file is in dist folder
pause
