@echo off
title MJ Reverse AI - Offline AI Agent
color 0B
setlocal EnableDelayedExpansion

echo.
echo =====================================================
echo       MJ REVERSE AI - Offline AI Agent
echo =====================================================
echo.

REM ============================================================
REM  PATHS  - Everything is relative to THIS script's folder
REM ============================================================
set "BASE=%~dp0"
REM Remove trailing backslash from BASE
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

set "APPS_DIR=%BASE%\apps\python"
set "PYTHON=%APPS_DIR%\python.exe"
set "PIP=%APPS_DIR%\Scripts\pip.exe"
set "SITE_PKG=%APPS_DIR%\Lib\site-packages"
set "MODELS_DIR=%BASE%\models"
set "LAUNCHER=%BASE%\launcher.py"
set "TEMP_SETUP=%BASE%\installer_data"

echo [INFO] Base folder : %BASE%
echo [INFO] Python path : %PYTHON%
echo [INFO] Models path : %MODELS_DIR%
echo.

REM ============================================================
REM  STEP 1 - Auto-install Python if missing
REM ============================================================
if exist "%PYTHON%" (
    echo [OK]   Python already installed at: %APPS_DIR%
    goto :PYTHON_READY
)

echo [SETUP] Python not found. Downloading Python 3.11 installer...
echo         This only happens once. Please wait...
echo.

REM Create needed folders
if not exist "%APPS_DIR%"   mkdir "%APPS_DIR%"
if not exist "%TEMP_SETUP%" mkdir "%TEMP_SETUP%"

set "PY_INSTALLER=%TEMP_SETUP%\python-3.11.9-amd64.exe"

REM Download Python 3.11.9 installer using PowerShell (built into every Windows)
powershell -NoProfile -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
     $wc = New-Object System.Net.WebClient; ^
     $wc.DownloadFile('https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe', '%PY_INSTALLER%')"

if not exist "%PY_INSTALLER%" (
    echo [ERROR] Failed to download Python installer.
    echo         Check your internet connection and try again.
    pause
    exit /b 1
)

echo [SETUP] Installing Python 3.11 into: %APPS_DIR%
echo         (Silent install - this may take 1-2 minutes)

REM Install Python silently into the local apps\python folder
"%PY_INSTALLER%" /quiet ^
    InstallAllUsers=0 ^
    TargetDir="%APPS_DIR%" ^
    Include_launcher=0 ^
    Include_test=0 ^
    Include_doc=0 ^
    PrependPath=0 ^
    Shortcuts=0

if not exist "%PYTHON%" (
    echo [ERROR] Python installation failed!
    echo         Try running START.bat as Administrator.
    pause
    exit /b 1
)

echo [OK]   Python 3.11 installed successfully!
echo.

:PYTHON_READY

REM ============================================================
REM  STEP 2 - Bootstrap pip if missing
REM ============================================================
if exist "%PIP%" goto :PIP_READY

echo [SETUP] pip not found. Bootstrapping pip...

REM Try ensurepip first (works if pip is bundled with Python)
"%PYTHON%" -m ensurepip --upgrade >nul 2>&1

if exist "%PIP%" (
    echo [OK]   pip bootstrapped via ensurepip.
    goto :PIP_READY
)

REM Fallback: download get-pip.py
set "GETPIP=%TEMP_SETUP%\get-pip.py"
powershell -NoProfile -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
     $wc = New-Object System.Net.WebClient; ^
     $wc.DownloadFile('https://bootstrap.pypa.io/get-pip.py', '%GETPIP%')"

if not exist "%GETPIP%" (
    echo [ERROR] Could not download get-pip.py. Check internet connection.
    pause
    exit /b 1
)

"%PYTHON%" "%GETPIP%" --quiet
if not exist "%PIP%" (
    echo [ERROR] pip installation failed.
    pause
    exit /b 1
)
echo [OK]   pip installed via get-pip.py.

:PIP_READY
echo [OK]   pip is ready.

REM ============================================================
REM  STEP 3 - Auto-install llama-cpp-python if missing
REM ============================================================
"%PYTHON%" -c "import llama_cpp" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK]   llama-cpp-python is already installed.
    goto :LLAMA_READY
)

echo [SETUP] Installing llama-cpp-python (CPU build)...
echo         This downloads ~150 MB and only happens once.
echo         Do NOT close this window!
echo.

REM Create site-packages folder if it doesn't exist yet
if not exist "%SITE_PKG%" mkdir "%SITE_PKG%"

"%PIP%" install llama-cpp-python==0.3.19 ^
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu ^
    --target "%SITE_PKG%" ^
    --quiet

REM Verify the install worked
"%PYTHON%" -c "import llama_cpp" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] llama-cpp-python installation failed!
    echo         Check your internet connection.
    pause
    exit /b 1
)

echo [OK]   llama-cpp-python installed successfully!

:LLAMA_READY

REM ============================================================
REM  STEP 4 - Ensure models folder exists and has .gguf files
REM ============================================================
if not exist "%MODELS_DIR%" (
    echo [INFO] Creating models folder...
    mkdir "%MODELS_DIR%"
)

dir /b "%MODELS_DIR%\*.gguf" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARN] No .gguf model files found in:
    echo        %MODELS_DIR%
    echo.
    echo  Please run install.bat to download a model, OR
    echo  manually place a .gguf file in the models folder.
    echo.
    pause
    exit /b 1
)

echo [OK]   GGUF models found in: %MODELS_DIR%

REM ============================================================
REM  STEP 5 - Verify launcher.py exists
REM ============================================================
if not exist "%LAUNCHER%" (
    echo [ERROR] launcher.py not found at: %LAUNCHER%
    echo         The project files may be incomplete.
    pause
    exit /b 1
)

REM ============================================================
REM  STEP 6 - Launch MJ Reverse AI
REM ============================================================
echo.
echo [OK]   All checks passed. Starting MJ Reverse AI...
echo =====================================================
echo.

"%PYTHON%" "%LAUNCHER%"

echo.
echo =====================================================
echo  MJ Reverse AI has exited.
echo =====================================================
pause
