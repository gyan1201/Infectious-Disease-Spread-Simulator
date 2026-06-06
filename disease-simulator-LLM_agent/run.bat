@echo off
REM ---------------------------------------------------------------------------
REM run.bat  —  Windows CMD launcher for the disease simulator
REM Can be called from any directory:  run.bat [log-prefix] [days]
REM Output always goes to disease-simulator-main\logs\<prefix>\
REM ---------------------------------------------------------------------------

REM Resolve the directory containing this script so paths are always correct
REM regardless of where the user calls run.bat from.
set SCRIPT_DIR=%~dp0

set PREFIX=%1
if "%PREFIX%"=="" set PREFIX=atl-test

set DAYS=%2
if "%DAYS%"=="" set DAYS=90

REM 5 min/step × 288 steps = 1 day
set /a UNTIL=%DAYS% * 288

echo Running simulation: prefix=%PREFIX%  days=%DAYS%  steps=%UNTIL%
echo Output: %SCRIPT_DIR%logs\%PREFIX%\

java ^
  "-Dlog4j2.configurationFactory=edu.gmu.mason.vanilla.log.CustomConfigurationFactory" ^
  "-Dlog.rootDirectory=%SCRIPT_DIR%logs" ^
  "-Dfile.prefix=%PREFIX%" ^
  "-Dsimulation.test=bias" ^
  -jar "%SCRIPT_DIR%target\vanilla-0.1-jar-with-dependencies.jar" ^
  -configuration "%SCRIPT_DIR%examples\atlanta.properties" ^
  -bias.config "%SCRIPT_DIR%examples\bias.llm.properties" ^
  -bias.single.config "%SCRIPT_DIR%examples\bias.single.properties" ^
  -decision.bank "%SCRIPT_DIR%examples\llm.atl.csv" ^
  -until %UNTIL%

if %ERRORLEVEL% neq 0 (
  echo.
  echo Simulation failed with exit code %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)

echo.
echo Done. Results in %SCRIPT_DIR%logs\%PREFIX%\
