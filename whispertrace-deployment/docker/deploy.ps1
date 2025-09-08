# This script is used to bring up or down the services using Docker Compose.
# It supports the following options:
#   -e, --environment  Set the environment (default: local)
#   -b, --build        Build all containers before starting or specify a list of images to rebuild
#   -v, --env-file     Path to custom .env file containing environment variables
#
# Usage:
#   ./deploy.ps1 up|down [-e {local|dev|stage|prod}] [-b [image1 image2 ...]] [-v <path to .env file>]
#
# Example:
#   ./deploy.ps1 up -e dev -b                    Brings up the services for the 'dev' environment and builds all containers
#   ./deploy.ps1 up -e dev -b whispertrace-api   Brings up the services for the 'dev' environment and builds specified containers
#   ./deploy.ps1 down                            Brings down the services for the 'local' environment

# Default values
$COMMAND = ""
$ENVIRONMENT = "local"
$BUILD = $false
$BUILD_IMAGES = @()
$ENV_FILE = ""

function Show-Usage {
    Write-Output "Usage: deploy.ps1 {up|down} [-e {local|dev|stage|prod}] [-b [image1 image2 ...]] [-v <path to .env file>]"
    Write-Output "  -e, --environment  Set the environment (default: local)"
    Write-Output "  -b, --build        Build all containers before starting or specify a list of images to rebuild"
    Write-Output "  -v, --env-file     Path to custom .env file containing environment variables"
    exit 1
}

# Parse command line arguments
param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("up", "down")]
    [string]$command,

    [string]$environment = "local",

    [switch]$build,

    [string[]]$build_images = @(),

    [string]$env_file = ""
)

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$COMPOSE_DIR = "$SCRIPT_DIR\compose"
$COMPOSE_FILE_BASE = "$COMPOSE_DIR\docker-compose.base.yaml"
$COMPOSE_FILE_ENV = "$COMPOSE_DIR\docker-compose.$environment.yaml"
$COMPOSE_FILES_OPTION = "-f `"$COMPOSE_FILE_BASE`" -f `"$COMPOSE_FILE_ENV`""
$ENV_OPTION = "--env-file $COMPOSE_DIR\.env"

$BASE_IMAGES = @(
    "whispertrace-api-base",
)

if ($env_file) {
    $ENV_OPTION = "--env-file $env_file"
}

function Build-Images {
    param ([string[]]$images)

    foreach ($image in $images) {
        if (-not (docker images -q $image) -or $build_images -contains $image) {
            docker-compose $ENV_OPTION -f $COMPOSE_FILE_BASE build --no-cache $image
            docker-compose $ENV_OPTION -f $COMPOSE_FILE_ENV build --no-cache $image
        }
    }
}

# Combine BASE_IMAGES and BUILD_IMAGES
$COMBINED_IMAGES = $BASE_IMAGES + $build_images

# Execute Docker Compose commands
if ($command -eq "up") {
    Write-Host "Bringing up services for environment: $environment"

    # Build necessary images
    Build-Images $COMBINED_IMAGES

    docker-compose $ENV_OPTION $COMPOSE_FILES_OPTION up
} elseif ($command -eq "down") {
    Write-Host "Bringing down services for environment: $environment"
    docker-compose $ENV_OPTION $COMPOSE_FILES_OPTION down
} else {
    Show-Usage
}
