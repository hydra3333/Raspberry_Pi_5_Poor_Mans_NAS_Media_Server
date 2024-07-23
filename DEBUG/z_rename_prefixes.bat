@echo off

@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM set "the_folder=F:\mp4library\ClassicMovies"
set "the_folder=F:\mp4library\OLDmovies"

REM Define your list of wildcard filenames separated by TRAILING SPACE
set "prefix_list="
set "prefix_list=!prefix_list!Agatha_Christie_ "
set "prefix_list=!prefix_list!Criminal_Games_ "
set "prefix_list=!prefix_list!Miss_Marple_ "
set "prefix_list=!prefix_list!Carry_On_ "
set "prefix_list=!prefix_list!Death_Comes_To_Pemberley_ "
set "prefix_list=!prefix_list!poirot_ "
set "prefix_list=!prefix_list!Anne_Of_Green_Gables_ "
set "prefix_list=!prefix_list!Captain_America_ "
set "prefix_list=!prefix_list!Doctor_Thorne_ "
set "prefix_list=!prefix_list!On_Our_Selection_ "
set "prefix_list=!prefix_list!Phil_Mickelson_ "
set "prefix_list=!prefix_list!Pitch_Perfect_ "
set "prefix_list=!prefix_list!SMILEY_ "
set "prefix_list=!prefix_list!The_ABC_Murders-Series_ "
set "prefix_list=!prefix_list!War_ "
:after_prefix_set

REM Use pushd to change to the specified the_folder
pushd "%the_folder%"
REM Outer loop to iterate through each wildcard filename
for %%z in (%prefix_list%) do (
	REM echo Processing files matching prefix: %%z
	set "old_prefix=%%z"
	REM Replace the trailing character in the prefix with a dash
	set "new_prefix=!old_prefix:~0,-1!-"
	REM call :TCase2 new_prefix
    REM Inner loop to iterate through files matching the wildcard
    for %%y in (%%z*.mp4) do (
		REM echo Processing file: prefix:"%%z" has matching file:"%%y"
		call :rename_file_prefix "%%y" "!old_prefix!" "!new_prefix!"
    )
)
REM Use popd to return to the previous directory
popd

ECHO.
REM Use pushd to change to the specified the_folder
pushd "%the_folder%"
for %%y in (*.mp4) do (
	call :rename_file_plain "%%y"
)
REM Use popd to return to the previous directory
popd


pause
goto :eof

:rename_file_prefix 
REM
set "ren_old_file=%~dpnx1"
set "ren_old_filename=%~n1"
set "ren_old_prefix=%~2"
set "ren_new_prefix=%~3"
REM
set "ren_new_filename=!ren_old_filename:%ren_old_prefix%=%ren_new_prefix%!"
call :TCase2 ren_new_filename
set "ren_new_file=!ren_new_filename!%~x1"
REM
echo RENAME "!ren_old_file!" "!ren_new_file!"
RENAME "!ren_old_file!" "!ren_new_file!"
goto :eof


:rename_file_plain 
REM
set "ren_old_file=%~dpnx1"
set "ren_old_filename=%~n1"
REM
set "ren_new_filename=!ren_old_filename!"
call :TCase2 ren_new_filename
set "ren_new_file=!ren_new_filename!%~x1"
REM
echo RENAME "!ren_old_file!" "!ren_new_file!"
RENAME "!ren_old_file!" "!ren_new_file!"
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

