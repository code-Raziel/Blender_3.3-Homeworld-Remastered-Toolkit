@echo off
echo Building hod for %1:
SET ship_id=%1
C:
CD %~dp0
HODOR.exe -$SHIP_NAME=%ship_id% -script="HodMake.hodor"
TIMEOUT 5
