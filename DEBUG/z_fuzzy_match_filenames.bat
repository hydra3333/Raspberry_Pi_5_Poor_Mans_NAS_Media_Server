@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM --------- setup paths and exe filenames ----------------------------
set "root=X:\CONVERT\"
set "vs_root=C:\SOFTWARE\Vapoursynth-x64\"
set "scratch_Folder=D:\VRDTVSP-SCRATCH\"

if /I NOT "!root:~-1!" == "\" (set "root=!root!\")
if /I NOT "!vs_root:~-1!" == "\" (set "vs_root=!vs_root!\")
set "root_nobackslash=%root:~0,-1%"
set "vs_root_nobackslash=%vs_root:~0,-1%"

set "vs_path_drive=!vs_root:~,2!"
set "vs_scripts_path=!vs_root!vs-scripts\"
set "vs_plugins_path=!vs_root!vs-plugins\"
set "vs_coreplugins_path=!vs_root!vs-coreplugins\"

if /I NOT "!vs_scripts_path:~-1!" == "\" (set "vs_scripts_path=!vs_scripts_path!\")
if /I NOT "!vs_plugins_path:~-1!" == "\" (set "vs_plugins_path=!vs_plugins_path!\")
if /I NOT "!vs_coreplugins_path:~-1!" == "\" (set "vs_coreplugins_path=!vs_coreplugins_path!\")

set "ffmpegexe64=!vs_root!ffmpeg.exe"
set "ffmpegexe64_OpenCL=!vs_root!ffmpeg_OpenCL.exe"
set "ffprobeexe64=!vs_root!ffprobe.exe"
set "mediainfoexe64=!vs_root!MediaInfo.exe"
set "dgindexNVexe64=!vs_root!DGIndex\DGIndexNV.exe"
set "vspipeexe64=!vs_root!VSPipe.exe"
set "py_exe=!vs_root!python.exe"
set "Insomniaexe64=C:\SOFTWARE\Insomnia\64-bit\Insomnia.exe"
REM --------- setup paths and exe filenames ----------------------------

REM -- Header ---------------------------------------------------------------------
REM set header to date and time and computer name
CALL :get_header_String "header"
REM -- Header ---------------------------------------------------------------------

REM -- Prepare the log file ---------------------------------------------------------------------
REM SET vrdlog=%root%%~n0-!header!.log
set "vrdlog=%~dpn0-!header!.log
REM ECHO !DATE! !TIME! DEL /F "!vrdlog!"
REM DEL /F "!vrdlog!" >NUL 2>&1
REM -- Prepare the log file ---------------------------------------------------------------------

REM --------- setup LOG file and TEMP filenames ----------------------------
REM base the filenames on the running script filename using %~n0
SET tempfile=!scratch_Folder!%~n0-!header!-temp.txt
DEL /F "!tempfile!"

SET tempfile_stderr=!scratch_Folder!%~n0-!header!-temp_stderr.txt
DEL /F "!tempfile!"

set "temp_cmd_file=!temp_Folder!temp_cmd_file.bat"
DEL /F "!temp_cmd_file!"
REM --------- setup LOG file and TEMP filenames ----------------------------


set "Path_to_py_z_fuzzy_match_filenames=!root!z_fuzzy_match_filenames.py"

REM ******************************************************************************************************************************************
REM ******************************************************************************************************************************************
REM ******************************************************************************************************************************************
REM
REM Check if filenames are a "safe string" without special characters like !~`!@#$%^&*()+=[]{}\|:;'"<>,?/
REM If a filename isn't "safe" then rename it so it really is safe
REM Allowed only characters a-z,A-Z,0-9,-,_,.,space
REM
REM - Fix filenames with special characters
REM - Move date in filename to end of filename
REM - Set timestamps (Date Created, Date Modified) to the date in the filename and a (localized TZ time for that date) of 00:00:00
REM


ECHO "!py_exe!" "!Path_to_py_z_fuzzy_match_filenames!"
"!py_exe!" "!Path_to_py_z_fuzzy_match_filenames!"
dir /b "z_fuzzy_match_results*.csv"

pause
goto :eof


REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM
:LoCase
REM Subroutine to convert a variable VALUE to all lower case.
REM The argument for this subroutine is the variable NAME.
FOR %%i IN ("A=a" "B=b" "C=c" "D=d" "E=e" "F=f" "G=g" "H=h" "I=i" "J=j" "K=k" "L=l" "M=m" "N=n" "O=o" "P=p" "Q=q" "R=r" "S=s" "T=t" "U=u" "V=v" "W=w" "X=x" "Y=y" "Z=z") DO CALL set "%1=%%%1:%%~i%%"
goto :eof

:UpCase
REM Subroutine to convert a variable VALUE to all UPPER CASE.
REM The argument for this subroutine is the variable NAME.
FOR %%i IN ("a=A" "b=B" "c=C" "d=D" "e=E" "f=F" "g=G" "h=H" "i=I" "j=J" "k=K" "l=L" "m=M" "n=N" "o=O" "p=P" "q=Q" "r=R" "s=S" "t=T" "u=U" "v=V" "w=W" "x=X" "y=Y" "z=Z") DO CALL set "%1=%%%1:%%~i%%"
goto :eof

:TCase
REM Subroutine to convert a variable VALUE to Title Case.
REM The argument for this subroutine is the variable NAME.
FOR %%i IN (" a= A" " b= B" " c= C" " d= D" " e= E" " f= F" " g= G" " h= H" " i= I" " j= J" " k= K" " l= L" " m= M" " n= N" " o= O" " p= P" " q= Q" " r= R" " s= S" " t= T" " u= U" " v= V" " w= W" " x= X" " y= Y" " z= Z") DO CALL set "%1=%%%1:%%~i%%"
goto :eof

:TCase2
REM Subroutine to convert a variable VALUE to Title Case.
REM The argument for this subroutine is the variable NAME.
call :LoCase %1
FOR %%i IN (" a= A" " b= B" " c= C" " d= D" " e= E" " f= F" " g= G" " h= H" " i= I" " j= J" " k= K" " l= L" " m= M" " n= N" " o= O" " p= P" " q= Q" " r= R" " s= S" " t= T" " u= U" " v= V" " w= W" " x= X" " y= Y" " z= Z" ^
           ".a=.A" ".b=.B" ".c=.C" ".d=.D" ".e=.E" ".f=.F" ".g=.G" ".h=.H" ".i=.I" ".j=.J" ".k=.K" ".l=.L" ".m=.M" ".n=.N" ".o=.O" ".p=.P" ".q=.Q" ".r=.R" ".s=.S" ".t=.T" ".u=.U" ".v=.V" ".w=.W" ".x=.X" ".y=.Y" ".z=.Z" ^
           "_a=_A" "_b=_B" "_c=_C" "_d=_D" "_e=_E" "_f=_F" "_g=_G" "_h=_H" "_i=_I" "_j=_J" "_k=_K" "_l=_L" "_m=_M" "_n=_N" "_o=_O" "_p=_P" "_q=_Q" "_r=_R" "_s=_S" "_t=_T" "_u=_U" "_v=_V" "_w=_W" "_x=_X" "_y=_Y" "_z=_Z" ^
           "-a=-A" "-b=-B" "-c=-C" "-d=-D" "-e=-E" "-f=-F" "-g=-G" "-h=-H" "-i=-I" "-j=-J" "-k=-K" "-l=-L" "-m=-M" "-n=-N" "-o=-O" "-p=-P" "-q=-Q" "-r=-R" "-s=-S" "-t=-T" "-u=-U" "-v=-V" "-w=-W" "-x=-X" "-y=-Y" "-z=-Z") DO (
				CALL set "%1=%%%1:%%~i%%"
			)
call set "first_letter=!%1:~0,1!"
call set "rest_of_string=!%1:~1!"
call :UpCase first_letter
Call CALL set "%1=!first_letter!!rest_of_string!"
goto :eof


REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM
:calc_single_number_result
REM use VBS to evaluate an incoming formula string which has no embedded special characters 
REM and yield a result which has no embedded special characters
REM eg   CALL :calc_single_number_result "Int((1+2+3+4+5+6)/10.0)" "return_variable_name"
set "Datey=%DATE: =0%"
set "Timey=%time: =0%"
set "eval_datetime=!Datey:~10,4!-!Datey:~7,2!-!Datey:~4,2!.!Timey:~0,2!.!Timey:~3,2!.!Timey:~6,2!.!Timey:~9,2!"
set "eval_datetime=!eval_datetime: =0!"
set "eval_formula_vbs_filename=.\VTDTVS_eval_formula-!eval_datetime!.vbs"
set "eval_formula=%~1"
set "eval_variable_name=%~2"
set "eval_single_number_result="
REM ECHO 'cscript //nologo "!eval_formula_vbs_filename!" "!eval_formula!"'
for /f %%A in ('cscript //nologo "!eval_formula_vbs_filename!" "!eval_formula!"') do (
    set "!eval_variable_name!=%%A"
    set "eval_single_number_result=%%A"
)
DEL /F "!eval_formula_vbs_filename!" >NUL 2>&1
REM ECHO "eval_formula_vbs_filename=!eval_formula_vbs_filename!"
REM ECHO "eval_variable_name=!eval_variable_name! eval_formula=!eval_formula! eval_single_number_result=!eval_single_number_result!"
goto :eof


REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM
:calc_single_number_result_py
REM Use Python to evaluate an incoming formula string which has no embedded special characters 
REM and yield a result which has no embedded special characters
REM Example usage: CALL :calc_single_number_result "1+2+3+4+5+6" "return_variable_name"
set "eval_formula=%~1"
set "eval_variable_name=%~2"
set "Datey=%DATE: =0%"
set "Timey=%time: =0%"
set "eval_datetime=!Datey:~10,4!-!Datey:~7,2!-!Datey:~4,2!.!Timey:~0,2!.!Timey:~3,2!.!Timey:~6,2!.!Timey:~9,2!"
set "eval_datetime=!eval_datetime: =0!"
set "eval_result_filename=.\VTDTVS_eval_formula-!eval_datetime!.txt"
REM Evaluate the formula using Python
set "eval_single_number_result="
"!py_exe!" -c "print(str(eval('!eval_formula!'))+'\n')" >"!eval_result_filename!" 2>&1
set /p eval_single_number_result=<"!eval_result_filename!"
set "!eval_variable_name!=!eval_single_number_result!"
set "eval_single_number_result="
DEL /F "!eval_result_filename!" >NUL 2>&1
goto :eof


REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM
:get_date_time_String
REM return a datetime string with spaces replaced by zeroes in format yyyy-mm-dd hh.mm.ss.hh
set "datetimestring_variable_name=%~1"
set "Datey=!DATE: =0!"
set "Timey=!TIME: =0!"
set "eval_datetime=!Datey:~10,4!-!Datey:~7,2!-!Datey:~4,2! !Timey:~0,2!.!Timey:~3,2!.!Timey:~6,2!.!Timey:~9,2!"
set "!datetimestring_variable_name!=!eval_datetime!"
goto :eof


REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM
:get_date_time_String_nospaces
REM return a datetime string with spaces replaced by zeroes and no spaces in format yyyy-mm-dd.hh.mm.ss.hh
set "ns_datetimestring_variable_name=%~1"
set "ns_eval_datetime="
CALL :get_date_time_String "ns_eval_datetime"
set "ns_eval_datetime=!ns_eval_datetime: =.!"
set "!ns_datetimestring_variable_name!=!ns_eval_datetime!"
goto :eof


REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM
:get_header_String
REM Create a Header
set "ghs_header_variable_name=%~1"
CALL :get_date_time_String_nospaces "ghs_date_time_String"
set "!ghs_header_variable_name!=!ghs_date_time_String!-!COMPUTERNAME!"
goto :eof


REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM
:remove_trailing_backslash_into_variable
REM remove trailing backslash from p1 "!source_TS_Folder!" into p2 "the_folder"
set "rtbiv_path=%~1"
set "rtbiv_variable=%~2"
if /I "!rtbiv_path:~-1!" == "\" (set "rtbiv_path=!rtbiv_path:~,-1!")
if /I "!rtbiv_path:~-1!" == "\" (set "rtbiv_path=!rtbiv_path:~,-1!")
if /I "!rtbiv_path:~-1!" == "\" (set "rtbiv_path=!rtbiv_path:~,-1!")
if /I "!rtbiv_path:~-1!" == "\" (set "rtbiv_path=!rtbiv_path:~,-1!")
if /I "!rtbiv_path:~-1!" == "\" (set "rtbiv_path=!rtbiv_path:~,-1!")
set "!rtbiv_variable!=!rtbiv_path!"
goto :eof


REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM ---------------------------------------------------------------------------------------------------------------------------------------------------------
REM
:make_double_backslashes_into_variable
REM double every backslash in p1 "!source_TS_Folder!" into p2 "the_folder"
set "rtbiv_path=%~1"
set "rtbiv_variable=%~2"
REM make all double backslashes into single backslashes first; do it multiple times to ensure multiples are caught
set "rtbiv_path=!rtbiv_path:\\=\!"
set "rtbiv_path=!rtbiv_path:\\=\!"
set "rtbiv_path=!rtbiv_path:\\=\!"
set "rtbiv_path=!rtbiv_path:\\=\!"
set "rtbiv_path=!rtbiv_path:\\=\!"
REM now make double backslashes
set "rtbiv_path=!rtbiv_path:\=\\!"
set "!rtbiv_variable!=!rtbiv_path!"
goto :eof
