@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

rem Initialize the variable to store found folders
set "foundFolders="
rem Array of drive letters to check
set "driveLetters=D E F G H I J K L M N O P Q R S T U V W X Y Z"
rem set he range of numbered root folders to check for
set rootFolderStartNumber=1
set rootFolderEndNumber=8
rem Loop through each drive letter
for %%d in (%driveLetters%) do (
    rem Loop through folder numbers 1 to 8
    for /L %%n in (%rootFolderStartNumber%,1,%rootFolderEndNumber%) do (
        set "folder=%%d:\ROOTFOLDER%%n"
		REM echo inner in-loop d=%%d n=%%n checking for folder '!folder!'
        if exist "!folder!" (
            rem Append the found folder to the variable
            set "foundFolders=!foundFolders! "!folder!""
			REM echo in-loop folder='!folder!' foundFolders='!foundFolders!'
        )
    )
)
rem Remove leading space
set "foundFolders=%foundFolders:~1%"
rem Display the result
echo REPLICATING SUBFOLDER-TREES ACROSS/UNDER DISK ROOTS: '%foundFolders%'

REM Iterate the found folders and replciate the folder structures elsewhere
for %%h in (!foundFolders!) do (
	call :do_replicate_folders_only_to_target "%%~h"
)

pause
exit


pause
goto :eof

:do_replicate_folders_only_to_target
echo --- Replicating subfolder-trees under disk root "%~1" across/under disk roots: !foundFolders!
if NOT exist "%~1" do (mkdir "%~1")
REM for %%i in ("%D1%" "%D2%" "%D3%" "%D4%" "%D5%" "%D6%" "%D7%" "%D8%") do (
for %%i in (!foundFolders!) do (
	IF /I "%~1" NEQ "%%~i"  (
		echo ***** xcopy "%~1" "%%~i\" /T /E /Y /F
		xcopy "%~1" "%%~i\" /T /E /Y /F
	)
)
REM   /T           Creates directory structure, but does not copy files. Does not
REM                include empty directories or subdirectories. /T /E includes
REM   /E           Copies directories and subdirectories, including empty ones.
REM                Same as /S /E. May be used to modify /T.
goto :eof
