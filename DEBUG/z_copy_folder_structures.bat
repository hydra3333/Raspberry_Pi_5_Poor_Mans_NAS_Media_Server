@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM robocopy: Robust File Copy for Windows.
REM /E: Copies all subdirectories, including empty ones.
REM /R:0: Sets the number of retries on failed copies to zero.
REM /W:0: Sets the wait time between retries to zero seconds.
REM /XF *: Excludes files matching the specified names or paths. Wildcards “*” and “?” are accepted
REM /L: (list-only) switch that simulates the operation without making any actual changes
REM /NFL: No file list - do not log file names.
REM /NDL: No directory list - do not log directory names.
REM /NJH: No job header.
REM /NJS: No job summary.

set "D1=X:\ROOTFOLDER1"
set "D2=V:\ROOTFOLDER2"
set "D3=F:\ROOTFOLDER3"
set "D4=H:\ROOTFOLDER4"
set "D5=K:\ROOTFOLDER5"

call :copy_folder_structure "%D1%"
call :copy_folder_structure "%D2%"
call :copy_folder_structure "%D3%"
call :copy_folder_structure "%D4%"
call :copy_folder_structure "%D5%"

call :ShowFolderCount  "%D1%"
call :ShowFolderCount  "%D2%"
call :ShowFolderCount  "%D3%"
call :ShowFolderCount  "%D4%"
call :ShowFolderCount  "%D5%"

call :ShowTopLevel  "%D1%"
call :ShowTopLevel  "%D2%"
call :ShowTopLevel  "%D3%"
call :ShowTopLevel  "%D4%"
call :ShowTopLevel  "%D5%"

pause
goto :eof

:copy_folder_structure
if /I "%~1" NEQ "%D1%" (robocopy "%~1" "%D1%" /E /R:5 /W:0 /XF *)
if /I "%~1" NEQ "%D2%" (robocopy "%~1" "%D2%" /E /R:5 /W:0 /XF *)
if /I "%~1" NEQ "%D3%" (robocopy "%~1" "%D3%" /E /R:5 /W:0 /XF *)
if /I "%~1" NEQ "%D4%" (robocopy "%~1" "%D4%" /E /R:5 /W:0 /XF *)
if /I "%~1" NEQ "%D5%" (robocopy "%~1" "%D5%" /E /R:5 /W:0 /XF *)
goto :eof

:ShowFolderCount
REM dir /s /b /A:d /W "%~1"
for /f %%a in ('dir /s /b /A:d /W "%~1" ^| find /c /v ""') do set "count=%%a"
echo Total subfolders found in "%~1" = %count%
goto :eof

:ShowTopLevel
echo.
echo Folders at Root Level on "%~1"
dir /b /A:d /W "%~1"
echo.
goto :eof
