@echo off
REM Build script for creating one-file executable using PyInstaller

echo Building XML Clone Tool executable...
echo.

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
)

REM Create executable
echo Creating executable...
pyinstaller --onefile --name xml_clone_tool make_clone_xmls.py

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo.
echo Build successful!
echo Executable created in: dist\xml_clone_tool.exe
echo.
