@echo off
cd /d "%~dp0"
if exist "dist\xml_clone_tool.exe" (
	dist\xml_clone_tool.exe --config config.yaml --pause
) else (
	echo dist\xml_clone_tool.exe bulunamadi. Lütfen önce build.bat ile derleyin.
	pause
)
