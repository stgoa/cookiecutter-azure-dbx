#!/bin/bash
# This script is used to deploy the project to the dev environment

# import variables from .env
source .env

# export variables
export DATABRICKS_HOST=$DATABRICKS_HOST
export DATABRICKS_TOKEN=$DATABRICKS_TOKEN

# Check that the environment variables DATABRICKS_HOST and DATABRICKS_TOKEN are set
if [[ -z "$DATABRICKS_HOST" || -z "$DATABRICKS_TOKEN" ]]; then
    echo "Error: The environment variables DATABRICKS_HOST and DATABRICKS_TOKEN must be set."
    exit 1
fi

# Function to log messages to a file and print to the console
log() {
    local message="$1"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local log_entry="$timestamp - $message"
    echo "$log_entry" >> deploy.log
    echo "$log_entry"
}

# Function to clean up generated files
cleanup() {
    log "Cleaning up generated files"
    rm -f conf/tasks/sample_task_config.yml
    rm -f conf/deployment.yml
    exit 1  # Exit with an error status code
}


# Set up trap to call cleanup function on script exit
trap cleanup EXIT

# Initialize optional variables
execute_job=false
cluster_name=""

# Process command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --execute-job)
            execute_job=true
            shift
            if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then
                cluster_name="$1"
                shift
            fi
            ;;
        --help)
            usage
            ;;
        *)
            echo "Error: Invalid argument: $1"
            usage
            ;;
    esac
done

# Log script execution
log "Deployment script started"

# Build the project wheel
log "Building the project wheel"
poetry install
poetry build

# Install yglu if not already installed
if ! command -v yglu &>/dev/null; then
    log "Installing yglu"
    pip install yglu
fi


# Generate conf/tasks/gen-sample_task_config
log "Generating sample_task_config.yml"
poetry run yglu conf/tasks/gen-sample_task_config.yml > conf/tasks/sample_task_config.yml

# Generate conf/gen_deployment.yml
log "Generating deployment.yml"
poetry run yglu conf/gen-deployment.yml > conf/deployment.yml

# Deploy to custom environment
log "Deploying to dev environment"
poetry run dbx deploy --environment dev --deployment-file=conf/deployment.yml

# Execute the elasticity job if the flag is set
if [ "$execute_job" = true ]; then
    if [[ -n "$cluster_name" ]]; then
        # Validate the cluster name using a regular expression
        pattern="^[a-zA-Z_]+$"
        if ! [[ "$cluster_name" =~ $pattern ]]; then
            echo "Error: Invalid cluster name. The cluster name must contain only letters (uppercase or lowercase) and underscores."
            usage
            exit 1
        fi
        log "Executing the elasticity job for cluster: $cluster_name"
        poetry run dbx execute dev-{{cookiecutter.workflow_name}} --cluster-name="$cluster_name" --environment=dev
    else
        log "Executing the elasticity job without specifying a cluster name"
        poetry run dbx execute dev-{{cookiecutter.workflow_name}} --environment=dev
    fi
else
    log "Skipping execution of the elasticity job (use --execute-job flag to run)"
fi

# Log script completion
log "Deployment script completed"

# End of script
