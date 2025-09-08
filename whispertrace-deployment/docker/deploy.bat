@echo off
:: This script is used to bring up or down the services using Docker Compose.
:: It supports the following options:
::   -e, --environment  Set the environment (default: local)
::   -b, --build        Build all containers before starting or specify a list of images to rebuild
::   -v, --env-file     Path to custom .env file containing environment variables
::
:: Usage:
::   deploy.bat up|down [-e {local|dev|stage|prod}] [-b [image1 image2 ...]] [-v <path to .env file>]
::
:: Example:
::   deploy.bat up -e dev -b                    Brings up the services for the 'dev' environment and builds all containers
::   deploy.bat up -e dev -b whispertrace-api   Brings up the services for the 'dev' environment and builds specified containers
::   deploy.bat down                            Brings down the services for the 'local' environment

:: Default values
set "COMMAND="
set "ENVIRONMENT=local"
set "BUILD=false"
set "BUILD_IMAGES="
set "ENV_FILE="

:: Function to display usage
:usage
echo Usage: deploy.bat {up|down} [-e {local|dev|stage|prod}] [-b [image1 image2 ...]] [-v <path to .env file>]
exit /b 1

:: Parse command line arguments
if "%1" == "up" set "COMMAND=up"
if "%1" == "down" set "COMMAND=down"
shift
:next
if "%1" == "-e" (
    set "ENVIRONMENT=%2"
    shift
    shift
    goto next
)
if "%1" == "-b" (
    set "BUILD=true"
    shift
    :build_images
    if "%1" == "" goto after_parse
    if "%1" == "-v" goto after_parse
    set "BUILD_IMAGES=%BUILD_IMAGES% %1"
    shift
    goto build_images
)
if "%1" == "-v" (
    set "ENV_FILE=%2"
    shift
    shift
    goto next
)
:after_parse

if "%COMMAND%" == "" (
    echo Error: Command 'up' or 'down' is required.
    goto usage
)

set "SCRIPT_DIR=%~dp0"
set "COMPOSE_DIR=%SCRIPT_DIR%\compose"
set "COMPOSE_FILE_BASE=%COMPOSE_DIR%\docker-compose.base.yaml"
set "COMPOSE_FILE_ENV=%COMPOSE_DIR%\docker-compose.%ENVIRONMENT%.yaml"
set "COMPOSE_FILES_OPTION=-f ""%COMPOSE_FILE_BASE%"" -f ""%COMPOSE_FILE_ENV%"""
set "ENV_OPTION=--env-file %COMPOSE_DIR%\.env"

set "BASE_IMAGES=whispertrace-api-base"

if not "%ENV_FILE%" == "" (
    set "ENV_OPTION=--env-file %ENV_FILE%"
)

:: Function to build images
:build_images
for %%i in (%BASE_IMAGES% %BUILD_IMAGES%) do (
    docker-compose %ENV_OPTION% -f "%COMPOSE_FILE_BASE%" build --no-cache %%i
    docker-compose %ENV_OPTION% -f "%COMPOSE_FILE_ENV%" build --no-cache %%i
)

:: Execute the Docker Compose command
if "%COMMAND%" == "up" (
    echo Bringing up services for environment: %ENVIRONMENT%
    call :build_images
    docker-compose %ENV_OPTION% %COMPOSE_FILES_OPTION% up
) else if "%COMMAND%" == "down" (
    echo Bringing down services for environment: %ENVIRONMENT%
    docker-compose %ENV_OPTION% %COMPOSE_FILES_OPTION% down
) else (
    goto usage
)
