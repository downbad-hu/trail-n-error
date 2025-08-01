@echo off
echo Installing Visual C++ Redistributable packages...
echo This may help resolve "The ordinal 380 could not be located" errors
echo.

REM Download URLs for Visual C++ Redistributable packages
set VC2015_2019_x86=https://aka.ms/vs/16/release/vc_redist.x86.exe
set VC2015_2019_x64=https://aka.ms/vs/16/release/vc_redist.x64.exe

echo Downloading Visual C++ 2015-2019 Redistributable (x86)...
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('%VC2015_2019_x86%', 'vc_redist.x86.exe')"

echo Downloading Visual C++ 2015-2019 Redistributable (x64)...
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('%VC2015_2019_x64%', 'vc_redist.x64.exe')"

echo.
echo Installing Visual C++ 2015-2019 Redistributable (x86)...
start /wait vc_redist.x86.exe /install /quiet /norestart

echo Installing Visual C++ 2015-2019 Redistributable (x64)...
start /wait vc_redist.x64.exe /install /quiet /norestart

echo.
echo Cleaning up...
del vc_redist.x86.exe
del vc_redist.x64.exe

echo.
echo Installation complete!
echo Please try running PyDownloadManager.exe again.
echo.

pause