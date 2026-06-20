@echo off
title MJ Reverse AI - Offline AI Agent
color 0B

echo.
echo =====================================================
echo       MJ REVERSE AI - Offline AI Pendrive Agent
echo =====================================================
echo.

REM ============================================================
REM  PATH RESOLUTION - Automatically detect local or pendrive paths
REM ============================================================

for %%I in ("%~dp0..") do set "PARENT_DIR=%%~fI"
for %%I in ("%~dp0..\..") do set "GRANDPARENT_DIR=%%~fI"

REM 1. Detect Python Executable
set "PENDRIVE_PYTHON="

REM A. Try local or parent/grandparent apps folder (portable mode)
if exist "%~dp0apps\python\python.exe" (
    set "PENDRIVE_PYTHON=%~dp0apps\python\python.exe"
) else if exist "%PARENT_DIR%\apps\python\python.exe" (
    set "PENDRIVE_PYTHON=%PARENT_DIR%\apps\python\python.exe"
) else if exist "%GRANDPARENT_DIR%\apps\python\python.exe" (
    set "PENDRIVE_PYTHON=%GRANDPARENT_DIR%\apps\python\python.exe"
) else if exist "A:\OllamaData\apps\python\python.exe" (
    set "PENDRIVE_PYTHON=A:\OllamaData\apps\python\python.exe"
)

REM B. Try system python from PATH
if not defined PENDRIVE_PYTHON (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "delims=" %%I in ('where python') do (
            set "PENDRIVE_PYTHON=%%I"
            goto :PYTHON_DETECTED
        )
    )
)

REM C. Try specific known user python path
if not defined PENDRIVE_PYTHON (
    if exist "C:\Users\krishna\AppData\Local\Programs\Python\Python311\python.exe" (
        set "PENDRIVE_PYTHON=C:\Users\krishna\AppData\Local\Programs\Python\Python311\python.exe"
    )
)
:PYTHON_DETECTED

REM 2. Detect Pip Executable
set "PENDRIVE_PIP="
if exist "%~dp0apps\python\Scripts\pip.exe" (
    set "PENDRIVE_PIP=%~dp0apps\python\Scripts\pip.exe"
) else if exist "%PARENT_DIR%\apps\python\Scripts\pip.exe" (
    set "PENDRIVE_PIP=%PARENT_DIR%\apps\python\Scripts\pip.exe"
) else if exist "%GRANDPARENT_DIR%\apps\python\Scripts\pip.exe" (
    set "PENDRIVE_PIP=%GRANDPARENT_DIR%\apps\python\Scripts\pip.exe"
) else if exist "A:\OllamaData\apps\python\Scripts\pip.exe" (
    set "PENDRIVE_PIP=A:\OllamaData\apps\python\Scripts\pip.exe"
)

if not defined PENDRIVE_PIP (
    where pip >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "delims=" %%I in ('where pip') do (
            set "PENDRIVE_PIP=%%I"
            goto :PIP_DETECTED
        )
    )
)

if not defined PENDRIVE_PIP (
    if exist "C:\Users\krishna\AppData\Local\Programs\Python\Python311\Scripts\pip.exe" (
        set "PENDRIVE_PIP=C:\Users\krishna\AppData\Local\Programs\Python\Python311\Scripts\pip.exe"
    )
)
:PIP_DETECTED

REM 3. Detect Models Directory
set "PENDRIVE_MODELS=%~dp0models"
if not exist "%PENDRIVE_MODELS%" (
    if exist "%PARENT_DIR%\*.gguf" (
        set "PENDRIVE_MODELS=%PARENT_DIR%"
    ) else if exist "%GRANDPARENT_DIR%\models" (
        set "PENDRIVE_MODELS=%GRANDPARENT_DIR%\models"
    ) else (
        set "PENDRIVE_MODELS=A:\OllamaData\models"
    )
)

REM 4. Set Target Directory for Dependency Installation
set "TARGET_DIR="
if exist "%~dp0apps\python\Lib\site-packages" (
    set "TARGET_DIR=%~dp0apps\python\Lib\site-packages"
) else if exist "%PARENT_DIR%\apps\python\Lib\site-packages" (
    set "TARGET_DIR=%PARENT_DIR%\apps\python\Lib\site-packages"
) else if exist "%GRANDPARENT_DIR%\apps\python\Lib\site-packages" (
    set "TARGET_DIR=%GRANDPARENT_DIR%\apps\python\Lib\site-packages"
) else if exist "A:\OllamaData\apps\python\Lib\site-packages" (
    set "TARGET_DIR=A:\OllamaData\apps\python\Lib\site-packages"
)

set LAUNCHER=%~dp0launcher.py

REM ============================================================
REM  1. Check Python exists
REM ============================================================
if not exist "%PENDRIVE_PYTHON%" (
    echo [ERROR] Python interpreter not found in local path or pendrive!
    echo         Expected at: %~dp0..\apps\python\python.exe
    echo.
    echo Please ensure Python 3.10 or 3.11 is installed inside the apps folder.
    pause
    exit /b 1
)

echo [OK] Found Python interpreter: %PENDRIVE_PYTHON%

REM ============================================================
REM  2. Check if pip is available
REM ============================================================
if exist "%PENDRIVE_PIP%" goto PIP_READY

echo [WARN] pip not found. Attempting to bootstrap pip...
"%PENDRIVE_PYTHON%" -m ensurepip --upgrade >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Could not bootstrap pip. Please install pip manually.
    pause
    exit /b 1
)
echo [OK] pip bootstrapped successfully.

:PIP_READY

REM ============================================================
REM  3. Check if llama-cpp-python is installed
REM ============================================================
"%PENDRIVE_PYTHON%" -c "import llama_cpp" >nul 2>&1
if %errorlevel% equ 0 goto LLAMA_READY

echo [WARN] llama-cpp-python is NOT installed in Python environment.
echo.
set /p INSTALL="Do you want to install it now? [y/N]: "
if /i "%INSTALL%" neq "y" goto INSTALL_REFUSED

echo.
echo [INFO] Installing llama-cpp-python (compatible v0.3.19 CPU wheel)...
echo        This may take several minutes on first run...
echo.
if defined TARGET_DIR (
    "%PENDRIVE_PYTHON%" -m pip install llama-cpp-python==0.3.19 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu --target "%TARGET_DIR%"
) else (
    "%PENDRIVE_PYTHON%" -m pip install llama-cpp-python==0.3.19 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
)
if %errorlevel% neq 0 goto INSTALL_FAILED

echo.
echo [OK] llama-cpp-python installed successfully!
goto LLAMA_READY

:INSTALL_FAILED
echo.
echo [ERROR] Installation failed.
echo         Check your internet connection.
pause
exit /b 1

:INSTALL_REFUSED
echo [ERROR] Cannot run without llama-cpp-python. Exiting.
pause
exit /b 1

:LLAMA_READY
echo [OK] llama-cpp-python is ready.

REM ============================================================
REM  4. Check Models Folder
REM ============================================================
if not exist "%PENDRIVE_MODELS%" (
    echo [WARN] Models folder not found at: %PENDRIVE_MODELS%
    echo        Creating it now...
    mkdir "%PENDRIVE_MODELS%"
    echo [OK] Created: %PENDRIVE_MODELS%
    echo.
    echo Please place your .gguf model files in:
    echo   %PENDRIVE_MODELS%
    echo.
    pause
    exit /b 1
)

REM Check for at least one .gguf model
dir /b "%PENDRIVE_MODELS%\*.gguf" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] No .gguf model files found in:
    echo        %PENDRIVE_MODELS%
    echo.
    echo Please copy at least one .gguf model to that folder.
    echo Recommended models ^(from Hugging Face^):
    echo   - Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf
    echo   - Llama-3.1-8B-Instruct-Q4_K_M.gguf
    echo   - DeepSeek-Coder-6.7B-Q4_K_M.gguf
    echo.
    pause
    exit /b 1
)

echo [OK] GGUF models found in: %PENDRIVE_MODELS%

REM ============================================================
REM  5. Self-healing check: make sure launcher.py exists
REM ============================================================
if not exist "%LAUNCHER%" (
    echo [ERROR] launcher.py not found at: %LAUNCHER%
    echo         Cannot start MJ Reverse AI.
    pause
    exit /b 1
)

REM ============================================================
REM  6. Launch MJ Reverse AI using pendrive Python
rem ============================================================
echo.
echo [OK] All checks passed. Launching MJ Reverse AI...
echo =====================================================
echo.

"%PENDRIVE_PYTHON%" "%LAUNCHER%"

echo.
echo =====================================================
echo  MJ Reverse AI has exited.
echo =====================================================
pause
