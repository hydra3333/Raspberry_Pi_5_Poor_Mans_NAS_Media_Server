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





XCOPY source [destination] [/A | /M] [/D[:date]] [/P] [/S [/E]] [/V] [/W]
                           [/C] [/I] [/-I] [/Q] [/F] [/L] [/G] [/H] [/R] [/T]
                           [/U] [/K] [/N] [/O] [/X] [/Y] [/-Y] [/Z] [/B] [/J]
                           [/EXCLUDE:file1[+file2][+file3]...] [/COMPRESS]

  source       Specifies the file(s) to copy.
  destination  Specifies the location and/or name of new files.
  /A           Copies only files with the archive attribute set,
               doesn't change the attribute.
  /M           Copies only files with the archive attribute set,
               turns off the archive attribute.
  /D:m-d-y     Copies files changed on or after the specified date.
               If no date is given, copies only those files whose
               source time is newer than the destination time.
  /EXCLUDE:file1[+file2][+file3]...
               Specifies a list of files containing strings.  Each string
               should be in a separate line in the files.  When any of the
               strings match any part of the absolute path of the file to be
               copied, that file will be excluded from being copied.  For
               example, specifying a string like \obj\ or .obj will exclude
               all files underneath the directory obj or all files with the
               .obj extension respectively.
  /P           Prompts you before creating each destination file.
  /S           Copies directories and subdirectories except empty ones.
  /E           Copies directories and subdirectories, including empty ones.
               Same as /S /E. May be used to modify /T.
  /V           Verifies the size of each new file.
  /W           Prompts you to press a key before copying.
  /C           Continues copying even if errors occur.
  /I           If destination does not exist and copying more than one file,
               assumes that destination must be a directory.
  /-I          If destination does not exist and copying a single specified file,
               assumes that destination must be a file.
  /Q           Does not display file names while copying.
  /F           Displays full source and destination file names while copying.
  /L           Displays files that would be copied.
  /G           Allows the copying of encrypted files to destination that does
               not support encryption.
  /H           Copies hidden and system files also.
  /R           Overwrites read-only files.
  /T           Creates directory structure, but does not copy files. Does not
               include empty directories or subdirectories. /T /E includes
               empty directories and subdirectories.
  /U           Copies only files that already exist in destination.
  /K           Copies attributes. Normal Xcopy will reset read-only attributes.
  /N           Copies using the generated short names.
  /O           Copies file ownership and ACL information.
  /X           Copies file audit settings (implies /O).
  /Y           Suppresses prompting to confirm you want to overwrite an
               existing destination file.
  /-Y          Causes prompting to confirm you want to overwrite an
               existing destination file.
  /Z           Copies networked files in restartable mode.
  /B           Copies the Symbolic Link itself versus the target of the link.
  /J           Copies using unbuffered I/O. Recommended for very large files.
  /COMPRESS    Request network compression during file transfer where
               applicable.
  /SPARSE      Preserves the sparse state when copying a sparse file.

The switch /Y may be preset in the COPYCMD environment variable.
This may be overridden with /-Y on the command line.


in a dos .bat file, how can I check every mounted drive letter for the existence of 
a uniquely numbered folder in the drive root eg "X:\ROOTFOLDER1" through to "H:\ROOTFOLDER8"
and populate a single variable with the those found, which would at the end contain something like
this including the quotes around each one found:
"X:\ROOTFOLDER1" "H:\ROOTFOLDER2" "I:\ROOTFOLDER8"  "Z:\ROOTFOLDER8"


this .bat
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
		echo inner in-loop d=%%d n=%%n checking for folder '!folder!'
        if exist "!folder!" (
            rem Append the found folder to the variable
            set "foundFolders=!foundFolders! "%folder%""
			echo "in-loop folder="!folder!" foundFolders=!foundFolders!"
        )
    )
)
rem Remove leading space
set "foundFolders=%foundFolders:~1%"
rem Display the result
echo foundFolders="%foundFolders%"
pause
exit
yields this result:
inner in-loop d=D n=1 checking for folder ''
inner in-loop d=D n=2 checking for folder ''
inner in-loop d=D n=3 checking for folder ''
inner in-loop d=D n=4 checking for folder ''
inner in-loop d=D n=5 checking for folder ''
inner in-loop d=D n=6 checking for folder ''
inner in-loop d=D n=7 checking for folder ''
inner in-loop d=D n=8 checking for folder ''
inner in-loop d=E n=1 checking for folder ''
inner in-loop d=E n=2 checking for folder ''
inner in-loop d=E n=3 checking for folder ''
inner in-loop d=E n=4 checking for folder ''
inner in-loop d=E n=5 checking for folder ''
inner in-loop d=E n=6 checking for folder ''
inner in-loop d=E n=7 checking for folder ''
inner in-loop d=E n=8 checking for folder ''