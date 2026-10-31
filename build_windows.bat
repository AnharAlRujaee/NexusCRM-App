@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv-build\Scripts\python.exe" (
    py -3 -m venv .venv-build
    if errorlevel 1 exit /b 1
)

if not exist "build" mkdir build

".venv-build\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b %errorlevel%

".venv-build\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 exit /b %errorlevel%

".venv-build\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed --name NexusCRM --specpath build --workpath build\work --distpath dist --collect-all googleapiclient --collect-all google_auth_oauthlib --collect-all google.auth --collect-all google.oauth2 --hidden-import google_auth_httplib2 --collect-all httplib2 main.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo Build complete: dist\NexusCRM\NexusCRM.exe
echo Distribute the entire dist\NexusCRM folder, not only the executable.