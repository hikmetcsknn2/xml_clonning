@echo off
REM Example runs of the XML Clone Tool

echo ========================================
echo XML Clone Tool - Example Runs
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    exit /b 1
)

echo Example 1: Process both feeds with default config
echo ----------------------------------------
python make_clone_xmls.py --config config.yaml
echo.

echo Example 2: Process only eBijuteri feed
echo ----------------------------------------
python make_clone_xmls.py --config config.yaml --only ebi
echo.

echo Example 3: Process only TeknoTok feed with custom prefix
echo ----------------------------------------
python make_clone_xmls.py --config config.yaml --only tkt --prefix "test_"
echo.

echo Example 4: Process with custom output directory
echo ----------------------------------------
python make_clone_xmls.py --config config.yaml --out-dir output
echo.

echo Example 5: Compare eBijuteri files (if they exist)
echo ----------------------------------------
if exist ebi_out.xml (
    echo Note: This requires original XML file. Skipping...
) else (
    echo Note: ebi_out.xml not found. Run Example 1 first.
)
echo.

echo Example 6: Compare TeknoTok files (if they exist)
echo ----------------------------------------
if exist tkt_out.xml (
    echo Note: This requires original XML file. Skipping...
) else (
    echo Note: tkt_out.xml not found. Run Example 1 first.
)
echo.

echo Done!
