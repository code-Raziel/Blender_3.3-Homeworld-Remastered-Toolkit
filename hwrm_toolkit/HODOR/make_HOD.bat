@echo off
echo "---------------------------"
echo " Building hod for %1"
echo "---------------------------"
SET "ship_id=%1"
REM echo %1
REM echo %2
SET "unit=%~dp0"
%unit:~0,2%
CD %~dp0
HODOR.exe -$SHIP_NAME=%ship_id% -$HWRM_BASE=%2 -script="HodMake.hodor"
TIMEOUT 5
REM PAUSE
