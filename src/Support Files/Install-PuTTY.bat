@echo off
:: ============================================================================
:: Name:        Install-PuTTY.bat
:: Description: Downloads and installs the latest stable 64-bit version of PuTTY.
:: Author:      Brandon Jones
:: Version:     1.0
:: Date:        June 12, 2025
:: ============================================================================
setlocal

:: ----------------------------------------------------------------------------
:: 1. Check for Administrator Privileges
:: ----------------------------------------------------------------------------
echo Checking for Administrator privileges...
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo.
    echo ============================================================
    echo  ERROR: Administrator permissions are required.
    echo  Please right-click this script and select "Run as administrator".
    echo ============================================================
    echo.
    pause
    goto :eof
)
echo Privileges OK.

:: ----------------------------------------------------------------------------
:: 2. Set Variables
:: ----------------------------------------------------------------------------
:: The official PuTTY site provides a direct link to the latest stable 64-bit MSI installer.
set "DownloadURL=https://the.earth.li/~sgtatham/putty/latest/w64/putty-64bit-0.83-installer.msi"

:: Define where to save the installer and what to name it.
set "InstallerFile=%TEMP%\putty_installer.msi"

echo.
echo ============================================================
echo  PuTTY Automated Installer
echo ============================================================
echo.
echo  Download URL: %DownloadURL%
echo  Saving to:    %InstallerFile%
echo.

:: ----------------------------------------------------------------------------
:: 3. Download the Installer
:: ----------------------------------------------------------------------------
echo Downloading PuTTY...
:: Use PowerShell (built into modern Windows) to download the file. It's more reliable than older tools.
powershell -Command "try { (New-Object System.Net.WebClient).DownloadFile('%DownloadURL%', '%InstallerFile%') } catch { Write-Host 'DOWNLOAD FAILED'; exit 1 }"

:: Check if the file was created. If not, PowerShell command failed.
if not exist "%InstallerFile%" (
    echo.
    echo ERROR: Download failed.
    echo Please check your internet connection and the Download URL in the script.
    echo.
    pause
    goto :eof
)
echo Download complete.

:: ----------------------------------------------------------------------------
:: 4. Install PuTTY Silently
:: ----------------------------------------------------------------------------
echo.
echo Installing PuTTY silently...
:: Use msiexec to run the installer.
:: /i - Specifies the installer package.
:: /qn - Sets the user interface level to "quiet, no UI". This is the silent part.
msiexec /i "%InstallerFile%" /qn

if %errorLevel% NEQ 0 (
    echo.
    echo ERROR: Installation failed with error code %errorLevel%.
    echo.
    pause
    goto :cleanup
)

echo PuTTY has been successfully installed.

:: ----------------------------------------------------------------------------
:: 5. Cleanup
:: ----------------------------------------------------------------------------
:cleanup
echo.
echo Cleaning up downloaded files...
if exist "%InstallerFile%" (
    del "%InstallerFile%"
)
echo Cleanup complete.
echo.

:: ----------------------------------------------------------------------------
:: 6. Finish
:: ----------------------------------------------------------------------------
echo ============================================================
echo  Installation process finished.
echo ============================================================
echo.
pause
endlocal