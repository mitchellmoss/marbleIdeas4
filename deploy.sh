#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to display progress bar
show_progress() {
    local total=$1
    local current=$2
    local bar_size=40
    local progress=$((current * 100 / total))
    local completed=$((progress * bar_size / 100))
    local remaining=$((bar_size - completed))

    echo -ne "\r["
    for ((i=0; i<completed; i++)); do echo -n "="; done
    for ((i=0; i<remaining; i++)); do echo -n " "; done
    echo -n "] $progress% ($current/$total)"

    if [ $current -eq $total ]; then
        echo
    fi
}

# Check if SSH_PASSWORD is set
if [ -z "$SSH_PASSWORD" ]; then
    log "Error: SSH_PASSWORD environment variable is not set."
    exit 1
fi

# Set variables
SERVER="root@192.168.86.129"
DEPLOY_DIR="/root/marble-gallery"
LOCAL_ZIP="marble_gallery_deploy.zip"
REMOTE_ZIP="marble_gallery_deploy.zip"

# Function to perform full redeployment
full_redeploy() {
    log "Starting full redeployment..."

    # Build the frontend
    log "Building the frontend..."
    cd frontend/marble-gallery
    npm run build
    cd ../..

    total_files=$(find . -type f | wc -l)
    processed_files=0

    log "Zipping the entire codebase (excluding backend/backend-env)..."
    zip -r $LOCAL_ZIP . -x "*.git*" "*.zip" "backend/backend-env/*" "frontend/marble-gallery/node_modules/*"
    processed_files=$((processed_files + total_files))
    show_progress $total_files $processed_files

    log "Creating temporary directory on remote server..."
    sshpass -p "$SSH_PASSWORD" ssh $SERVER "mkdir -p /tmp/marble_deploy"
    processed_files=$((processed_files + 1))
    show_progress $total_files $processed_files

    log "Transferring zip file to remote server..."
    sshpass -p "$SSH_PASSWORD" scp $LOCAL_ZIP $SERVER:/tmp/marble_deploy/
    processed_files=$((processed_files + 1))
    show_progress $total_files $processed_files

    log "Performing server-side operations..."
    sshpass -p "$SSH_PASSWORD" ssh $SERVER << EOF
        set -x  # Enable command tracing
        
        # Check if unzip is installed, if not, install it
        if ! command -v unzip &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y unzip
        fi
        
        mkdir -p $DEPLOY_DIR
        cd $DEPLOY_DIR
        echo "Current directory: \$(pwd)"

        echo "Unzipping new files..."
        unzip -o /tmp/marble_deploy/$REMOTE_ZIP -d $DEPLOY_DIR

        echo "Setting up environment variables..."
        cat << EOT > $DEPLOY_DIR/.env
$(cat .env)
EOT

        echo "Replacing 127.0.0.1:8000 with marble.boston and fixing https in all files..."
        find $DEPLOY_DIR -type f -exec sed -i 's/127\.0\.0\.1:8000/marble.boston/g; s/https\([^:]\)/https:\1/g' {} +

        echo "Cleaning up..."
        rm -v /tmp/marble_deploy/$REMOTE_ZIP
        rmdir -v /tmp/marble_deploy

        echo "Deployment completed."
EOF
    processed_files=$((processed_files + total_files))
    show_progress $total_files $processed_files

    log "Cleaning up local zip file..."
    rm -v $LOCAL_ZIP
    processed_files=$((processed_files + 1))
    show_progress $total_files $processed_files

    log "Deployment script finished."

    # Prompt user with instructions for creating the backend environment
    echo
    echo "IMPORTANT: The backend environment was not copied to the server."
    echo "Please follow these steps to create the environment on the server:"
    echo "1. SSH into the server: ssh $SERVER"
    echo "2. Navigate to the backend directory: cd $DEPLOY_DIR/backend"
    echo "3. Create a new virtual environment: python3 -m venv backend-env"
    echo "4. Activate the environment: source backend-env/bin/activate"
    echo "5. Install the required packages: pip install -r requirements.txt"
    echo "6. Deactivate the environment when done: deactivate"
    echo
}

# Function to start the WSGI server as a daemonized service
start_wsgi_service() {
    log "Starting WSGI server as a daemonized service..."

    sshpass -p "$SSH_PASSWORD" ssh $SERVER << EOF
        set -x  # Enable command tracing

        cd $DEPLOY_DIR/backend

        # Load environment variables
        set -a
        source $DEPLOY_DIR/.env
        set +a

        # Check if systemd is available
        if command -v systemctl &> /dev/null; then
            # Create a systemd service file
            cat << EOT | sudo tee /etc/systemd/system/marble-gallery.service
[Unit]
Description=Marble Gallery WSGI Server
After=network.target

[Service]
User=root
WorkingDirectory=$DEPLOY_DIR/backend
EnvironmentFile=$DEPLOY_DIR/.env
ExecStart=$DEPLOY_DIR/backend/backend-env/bin/gunicorn --workers=4 --bind=0.0.0.0:8000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOT

            # Reload systemd, enable and start the service
            sudo systemctl daemon-reload
            sudo systemctl enable marble-gallery.service
            sudo systemctl start marble-gallery.service

            echo "WSGI server started as a systemd service."
        else
            # If systemd is not available, use nohup
            source backend-env/bin/activate
            nohup gunicorn --workers=4 --bind=0.0.0.0:8000 wsgi:app > /dev/null 2>&1 &
            deactivate

            echo "WSGI server started using nohup."
        fi

        echo "WSGI server startup completed."
EOF

    log "WSGI server startup script finished."
}

# Function to set environment variables on the remote server
set_remote_env() {
    log "Setting environment variables on the remote server..."

    if [ ! -f .env ]; then
        log "Error: .env file not found in the current directory."
        exit 1
    fi

    sshpass -p "$SSH_PASSWORD" ssh $SERVER << EOF
        set -x  # Enable command tracing

        mkdir -p $DEPLOY_DIR
        cd $DEPLOY_DIR

        echo "Setting up environment variables..."
        cat << EOT > $DEPLOY_DIR/.env
$(cat .env)
EOT

        echo "Environment variables set successfully."
EOF

    log "Environment variables set on the remote server."
}

# Function to deploy only changed files
deploy_changes() {
    log "Starting deployment of changed files..."

    # Ensure we're in a git repository
    if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        log "Error: Not in a git repository."
        exit 1
    fi

    # Get list of changed files
    changed_files=$(git diff --name-only HEAD)
    if [ -z "$changed_files" ]; then
        log "No changes detected. Nothing to deploy."
        exit 0
    fi

    # Check if frontend files have changed
    if echo "$changed_files" | grep -q "frontend/marble-gallery/"; then
        log "Frontend changes detected. Rebuilding..."
        cd frontend/marble-gallery
        npm run build
        cd ../..
        # Add the build directory to the list of changed files
        changed_files+=$'\n'$(find frontend/marble-gallery/build -type f)
    fi

    total_files=$(echo "$changed_files" | wc -l)
    processed_files=0

    log "Deploying $total_files changed files..."

    # Create a temporary directory for changed files
    temp_dir=$(mktemp -d)
    log "Created temporary directory: $temp_dir"

    # Copy changed files to temporary directory
    echo "$changed_files" | while read -r file; do
        if [ -f "$file" ]; then
            dir=$(dirname "$file")
            mkdir -p "$temp_dir/$dir"
            cp "$file" "$temp_dir/$file"
            processed_files=$((processed_files + 1))
            show_progress $total_files $processed_files
        fi
    done

    # Zip the changed files
    (cd "$temp_dir" && zip -r "$LOCAL_ZIP" .)
    processed_files=$((processed_files + 1))
    show_progress $total_files $processed_files

    log "Transferring changed files to remote server..."
    sshpass -p "$SSH_PASSWORD" scp "$temp_dir/$LOCAL_ZIP" "$SERVER:/tmp/"
    processed_files=$((processed_files + 1))
    show_progress $total_files $processed_files

    log "Updating files on remote server..."
    sshpass -p "$SSH_PASSWORD" ssh $SERVER << EOF
        set -x  # Enable command tracing

        cd $DEPLOY_DIR
        unzip -o /tmp/$REMOTE_ZIP

        # Replace 127.0.0.1:8000 with marble.boston and fix https in changed files
        echo "$changed_files" | while read -r file; do
            if [ -f "$file" ]; then
                sed -i 's/127\.0\.0\.1:8000/marble.boston/g; s/https\([^:]\)/https:\1/g' "$file"
            fi
        done

        rm /tmp/$REMOTE_ZIP
EOF
    processed_files=$((processed_files + total_files))
    show_progress $total_files $processed_files

    log "Cleaning up..."
    rm -rf "$temp_dir"
    processed_files=$((processed_files + 1))
    show_progress $total_files $processed_files

    log "Deployment of changed files completed."
}

# Function to kill the WSGI server service
kill_wsgi_service() {
    log "Stopping WSGI server service..."

    sshpass -p "$SSH_PASSWORD" ssh $SERVER << EOF
        set -x  # Enable command tracing

        # Check if systemd is available
        if command -v systemctl &> /dev/null; then
            # Stop and disable the systemd service
            sudo systemctl stop marble-gallery.service
            sudo systemctl disable marble-gallery.service
            sudo rm /etc/systemd/system/marble-gallery.service
            sudo systemctl daemon-reload

            echo "WSGI server systemd service stopped and removed."
        else
            # If systemd is not available, kill the process using pkill
            pkill -f "gunicorn --workers=4 --bind=0.0.0.0:8000 wsgi:app"

            echo "WSGI server process killed."
        fi

        echo "WSGI server shutdown completed."
EOF

    log "WSGI server shutdown script finished."
}

# Main script logic
case "$1" in
    1)
        full_redeploy
        ;;
    2)
        start_wsgi_service
        ;;
    3)
        set_remote_env
        ;;
    4)
        deploy_changes
        ;;
    5)
        kill_wsgi_service
        ;;
    *)
        echo "Usage: $0 {1|2|3|4|5}"
        echo "  1: Perform full redeployment"
        echo "  2: Start WSGI server as a daemonized service"
        echo "  3: Set environment variables on the remote server"
        echo "  4: Deploy only changed files"
        echo "  5: Kill WSGI server service"
        exit 1
        ;;
esac