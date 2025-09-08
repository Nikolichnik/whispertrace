#!/bin/bash

# This script is used to bring up or down the services using Docker Compose.
# It supports the following options:
#   -e, --environment  Set the environment (default: local)
#   -b, --build        Build all containers before starting or specify a list of images to rebuild
#   -v, --env-file     Path to custom .env file containing environment variables
#
# Usage:
#   ./deploy.sh up|down [-e {local|dev|stage|prod}] [-b [image1 image2 ...]] [-v <path to .env file>]
#
# Example:
#   ./deploy.sh up -e dev -b                    Brings up the services for the 'dev' environment and builds all containers
#   ./deploy.sh up -e dev -b whispertrace-api   Brings up the services for the 'dev' environment and builds specified containers
#   ./deploy.sh down                            Brings down the services for the 'local' environment
#
# Note: This script should be run from the root directory of the project.
#       The script assumes that the Docker Compose files are located in the 'compose' directory.

# Default values
COMMAND=""
ENVIRONMENT="local"
BUILD=false
BUILD_IMAGES=()
ENV_FILE=""

# Function to display usage
usage() {
    echo "Usage: $0 {up|down} [-e {local|dev|stage|prod}] [-b [image1 image2 ...]] [-v <path to .env file>]"
    echo "  -e, --environment  Set the environment (default: local)"
    echo "  -b, --build        Build all containers before starting or specify a list of images to rebuild"
    echo "  -v, --env-file     Path to custom .env file containing environment variables"
    echo "  -h, --help         Display this help message"
    exit 1
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        up|down) COMMAND="$1"; shift ;;
        -e|--environment) ENVIRONMENT="$2"; shift 2 ;;
        -b|--build)
            BUILD=true
            shift
            while [[ "$#" -gt 0 && ! "$1" =~ ^- ]]; do
                BUILD_IMAGES+=("$1")
                shift
            done
            ;;
        -v|--env-file) ENV_FILE="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
done

# Check if command is provided
if [[ -z "$COMMAND" ]]; then
    echo "Error: Command 'up' or 'down' is required."
    usage
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
COMPOSE_DIR="${SCRIPT_DIR}/compose"
COMPOSE_FILE_BASE="${COMPOSE_DIR}/docker-compose.base.yaml"
COMPOSE_FILE_ENV="${COMPOSE_DIR}/docker-compose.${ENVIRONMENT}.yaml"
COMPOSE_FILES_OPTION="-f ${COMPOSE_FILE_BASE} -f ${COMPOSE_FILE_ENV}"
ENV_OPTION="--env-file ${COMPOSE_DIR}/.env"
BASE_IMAGES=(
    "whispertrace-api-base"
)

# Check if custom environment file is provided
if [[ -n "$ENV_FILE" ]]; then
    ENV_OPTION="--env-file $ENV_FILE"
fi

build_images() {
    local images=("$@")

    for image in "${images[@]}"; do
        if [[ "$(docker images -q $image 2> /dev/null)" == "" || " ${BUILD_IMAGES[@]} " =~ " ${image%-base} " ]]; then
            docker-compose $ENV_OPTION -f $COMPOSE_FILE_BASE build --no-cache "${image%-base}"
            docker-compose $ENV_OPTION -f $COMPOSE_FILE_ENV build --no-cache "${image%-base}"
        fi
    done
}

# Combine BASE_IMAGES and BUILD_IMAGES, ensuring unique elements
COMBINED_IMAGES=("${BASE_IMAGES[@]}")
for img in "${BUILD_IMAGES[@]}"; do
    if [[ ! " ${COMBINED_IMAGES[@]} " =~ " ${img}-base " ]]; then
        COMBINED_IMAGES+=("${img}-base")
    fi
done

# Execute the Docker Compose command
if [[ "$COMMAND" == "up" ]]; then
    echo "Bringing up services for environment: $ENVIRONMENT"

    # Build necessary images
    build_images "${COMBINED_IMAGES[@]}"

    docker-compose $ENV_OPTION $COMPOSE_FILES_OPTION up
elif [[ "$COMMAND" == "down" ]]; then
    echo "Bringing down services for environment: $ENVIRONMENT"
    docker-compose $ENV_OPTION $COMPOSE_FILES_OPTION down
else
    usage
fi