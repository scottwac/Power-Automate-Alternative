#!/bin/bash

# MatrixCare Looker Dashboard Automation - Azure Ubuntu Deployment Script
# This script handles the complete deployment to Azure Ubuntu server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="matrixcare-automation"
APP_DIR="$(pwd)"  # Use current directory instead of hardcoded path
SERVICE_NAME="matrixcare-automation"
VENV_DIR="$APP_DIR/venv"

# Helper functions
print_header() {
    echo -e "${CYAN}=================================================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}=================================================================================${NC}"
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_requirements() {
    print_step "Checking system requirements..."
    
    # Check if running on Ubuntu
    if [[ ! -f /etc/lsb-release ]] || ! grep -q "Ubuntu" /etc/lsb-release; then
        print_error "This script is designed for Ubuntu systems"
        exit 1
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_error "Python 3.8+ is required. Found: $python_version"
        exit 1
    fi
    
    print_success "System requirements check passed"
}

setup_environment() {
    print_step "Setting up Python environment..."
    
    # Update package list
    sudo apt update -y
    
    # Install required packages
    sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential
    
    # Create application directory
    mkdir -p "$APP_DIR"
    cd "$APP_DIR"
    
    # Create virtual environment
    if [[ ! -d "$VENV_DIR" ]]; then
        python3 -m venv "$VENV_DIR"
        print_success "Created virtual environment"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_success "Environment setup complete"
}

install_dependencies() {
    print_step "Installing Python dependencies..."
    
    source "$VENV_DIR/bin/activate"
    
    if [[ -f "$APP_DIR/requirements.txt" ]]; then
        pip install -r "$APP_DIR/requirements.txt"
        print_success "Dependencies installed from requirements.txt"
    else
        print_warning "requirements.txt not found, installing basic dependencies..."
        pip install google-auth google-auth-oauthlib google-auth-httplib2 \
                   google-api-python-client gspread pandas schedule python-dotenv
        print_success "Basic dependencies installed"
    fi
}

setup_configuration() {
    print_step "Setting up configuration..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f "$APP_DIR/.env" ]]; then
        cat > "$APP_DIR/.env" << EOF
# MatrixCare Looker Dashboard Automation Configuration

# Google Sheets Configuration
GOOGLE_SHEETS_SPREADSHEET_ID=1tQT3x-X9NxK_Rfg4uYhz71kvFrNbPXR-Wo3QBvaKdGQ

# Email Configuration
GMAIL_SUBJECT_FILTER=MatrixCare Automation for Looker Dash
GMAIL_FROM_EMAIL=growatorchard@gmail.com
GMAIL_LABEL=INBOX

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=email_processor.log

# Processing Configuration
CREATE_GOOGLE_SHEETS=true
CHECK_INTERVAL_MINUTES=5
MAX_ROWS_TO_PROCESS=5000
EOF
        print_success "Created .env configuration file"
    else
        print_warning ".env file already exists, skipping creation"
    fi
    
    # Check for required credential files
    local missing_files=()
    for file in "credentials.json" "token.json" "drive_token.json" "sheets_token.json"; do
        if [[ ! -f "$APP_DIR/$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_warning "Missing credential files: ${missing_files[*]}"
        print_warning "Please upload these files to $APP_DIR before running the service"
    else
        print_success "All credential files found"
    fi
}

test_authentication() {
    print_step "Testing authentication..."
    
    source "$VENV_DIR/bin/activate"
    cd "$APP_DIR"
    
    if python3 email_processor.py --test-auth; then
        print_success "Authentication test passed"
    else
        print_error "Authentication test failed"
        print_warning "Please check your credential files and Google API permissions"
        return 1
    fi
}

create_systemd_service() {
    print_step "Creating systemd service..."
    
    # Create service file
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=MatrixCare Looker Dashboard Automation
Documentation=https://github.com/your-repo/matrixcare-automation
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin:\$PATH
Environment=PYTHONPATH=$APP_DIR
ExecStart=$VENV_DIR/bin/python email_processor.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    print_success "Systemd service created and enabled"
}

setup_log_rotation() {
    print_step "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/$SERVICE_NAME > /dev/null << EOF
$APP_DIR/email_processor.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF
    
    print_success "Log rotation configured"
}

start_service() {
    print_step "Starting service..."
    
    # Start the service
    sudo systemctl start $SERVICE_NAME
    
    # Wait a moment for service to start
    sleep 3
    
    # Check service status
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Service started successfully"
        sudo systemctl status $SERVICE_NAME --no-pager -l
    else
        print_error "Service failed to start"
        print_error "Service logs:"
        sudo journalctl -u $SERVICE_NAME --no-pager -l
        exit 1
    fi
}

create_monitoring_scripts() {
    print_step "Creating monitoring scripts..."
    
    # Create status script
    cat > "$APP_DIR/status.sh" << 'EOF'
#!/bin/bash
# MatrixCare Automation Status Script

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== MatrixCare Automation Status ==="
echo ""

# Service status
if systemctl is-active --quiet matrixcare-automation; then
    echo -e "🟢 Service Status: ${GREEN}RUNNING${NC}"
else
    echo -e "🔴 Service Status: ${RED}STOPPED${NC}"
fi

# Last activity
echo "📅 Last Log Entry:"
tail -1 ~/matrixcare-automation/email_processor.log 2>/dev/null || echo "   No logs found"

# Next scheduled run
echo ""
echo "⏰ Schedule Information:"
python3 -c "
import sys
sys.path.append('$HOME/matrixcare-automation')
from datetime import date, timedelta
from email_processor import EmailProcessor
import os
os.chdir('$HOME/matrixcare-automation')

try:
    processor = EmailProcessor()
    ref = processor.reference_tuesday.date()
    today = date.today()
    
    # Find next target Tuesday
    current = today
    while current.weekday() != 1 or ((current - ref).days // 7) % 2 != 0:
        current += timedelta(days=1)
    
    print(f'   Reference Tuesday: {ref}')
    print(f'   Today: {today} (Target: {processor.is_target_tuesday()})')
    print(f'   Next Target Tuesday: {current}')
    print(f'   Should check emails now: {processor.should_check_emails()}')
except Exception as e:
    print(f'   Error checking schedule: {e}')
"

echo ""
echo "📊 Resource Usage:"
ps aux | grep -E "python.*email_processor" | grep -v grep | awk '{print "   CPU: " $3 "%, Memory: " $4 "%"}'

echo ""
echo "📝 Recent Logs (last 5 lines):"
tail -5 ~/matrixcare-automation/email_processor.log 2>/dev/null | sed 's/^/   /' || echo "   No logs found"
EOF

    chmod +x "$APP_DIR/status.sh"
    
    # Create logs script
    cat > "$APP_DIR/logs.sh" << 'EOF'
#!/bin/bash
# MatrixCare Automation Logs Script

echo "=== MatrixCare Automation Logs ==="
echo ""
echo "Choose an option:"
echo "1) View live service logs (systemd)"
echo "2) View live application logs"
echo "3) View last 50 application logs"
echo "4) Search logs for errors"
echo "5) Search logs for specific term"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "Press Ctrl+C to exit"
        sudo journalctl -u matrixcare-automation -f
        ;;
    2)
        echo "Press Ctrl+C to exit"
        tail -f ~/matrixcare-automation/email_processor.log
        ;;
    3)
        tail -50 ~/matrixcare-automation/email_processor.log
        ;;
    4)
        echo "Searching for errors..."
        grep -i "error\|fail\|exception" ~/matrixcare-automation/email_processor.log | tail -20
        ;;
    5)
        read -p "Enter search term: " term
        grep -i "$term" ~/matrixcare-automation/email_processor.log | tail -20
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
EOF

    chmod +x "$APP_DIR/logs.sh"
    
    # Create restart script
    cat > "$APP_DIR/restart.sh" << 'EOF'
#!/bin/bash
# MatrixCare Automation Restart Script

echo "🔄 Restarting MatrixCare Automation service..."
sudo systemctl restart matrixcare-automation

echo "⏳ Waiting for service to start..."
sleep 3

if systemctl is-active --quiet matrixcare-automation; then
    echo "✅ Service restarted successfully"
    sudo systemctl status matrixcare-automation --no-pager
else
    echo "❌ Service failed to restart"
    echo "Service logs:"
    sudo journalctl -u matrixcare-automation --no-pager -l
fi
EOF

    chmod +x "$APP_DIR/restart.sh"
    
    print_success "Monitoring scripts created"
}

run_tests() {
    print_step "Running deployment tests..."
    
    source "$VENV_DIR/bin/activate"
    cd "$APP_DIR"
    
    # Test authentication
    if ! python3 email_processor.py --test-auth; then
        print_error "Authentication test failed"
        return 1
    fi
    
    # Test single run
    print_step "Testing single email processing run..."
    if python3 email_processor.py --once; then
        print_success "Single run test passed"
    else
        print_warning "Single run test completed with warnings (this is normal if no emails found)"
    fi
    
    # Test schedule logic if unit tests exist
    if [[ -d "$APP_DIR/unit_testing" ]]; then
        print_step "Running unit tests..."
        cd "$APP_DIR/unit_testing"
        if python3 run_matrixcare_test.py; then
            print_success "Unit tests passed"
        else
            print_warning "Unit tests failed (check test configuration)"
        fi
        cd "$APP_DIR"
    fi
    
    print_success "All tests completed"
}

print_deployment_summary() {
    print_header "DEPLOYMENT COMPLETE"
    
    echo -e "${GREEN}🎉 MatrixCare Looker Dashboard Automation has been successfully deployed!${NC}"
    echo ""
    echo -e "${CYAN}📋 Configuration Summary:${NC}"
    echo "   • Service Name: $SERVICE_NAME"
    echo "   • Install Directory: $APP_DIR"
    echo "   • Google Sheets ID: 1tQT3x-X9NxK_Rfg4uYhz71kvFrNbPXR-Wo3QBvaKdGQ"
    echo "   • Schedule: Every other Tuesday starting Sept 30, 2025 at 11:20 AM & 12:00 PM"
    echo ""
    echo -e "${CYAN}🔧 Management Commands:${NC}"
    echo "   • Check status:    ./status.sh"
    echo "   • View logs:       ./logs.sh"
    echo "   • Restart service: ./restart.sh"
    echo "   • Service control: sudo systemctl [start|stop|restart|status] $SERVICE_NAME"
    echo ""
    echo -e "${CYAN}📊 Monitoring:${NC}"
    echo "   • Live logs:       sudo journalctl -u $SERVICE_NAME -f"
    echo "   • App logs:        tail -f $APP_DIR/email_processor.log"
    echo "   • Service status:  sudo systemctl status $SERVICE_NAME"
    echo ""
    echo -e "${CYAN}📁 Important Files:${NC}"
    echo "   • Configuration:   $APP_DIR/.env"
    echo "   • Application log: $APP_DIR/email_processor.log"
    echo "   • Service file:    /etc/systemd/system/$SERVICE_NAME.service"
    echo ""
    echo -e "${YELLOW}⚠️  Remember to:${NC}"
    echo "   • Ensure all credential files are uploaded to $APP_DIR"
    echo "   • Check service status regularly: ./status.sh"
    echo "   • Monitor logs around scheduled run times"
    echo ""
    echo -e "${GREEN}The service is now running and will automatically start on system boot.${NC}"
}

# Main deployment function
main() {
    print_header "MatrixCare Looker Dashboard Automation - Azure Ubuntu Deployment"
    
    echo "This script will:"
    echo "  • Set up Python environment"
    echo "  • Install dependencies"
    echo "  • Configure the application"
    echo "  • Create systemd service"
    echo "  • Set up monitoring tools"
    echo "  • Run deployment tests"
    echo ""
    
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
    
    check_requirements
    setup_environment
    install_dependencies
    setup_configuration
    create_systemd_service
    setup_log_rotation
    create_monitoring_scripts
    
    if test_authentication; then
        start_service
        run_tests
        print_deployment_summary
    else
        print_error "Deployment failed due to authentication issues"
        print_warning "Please check your Google API credentials and re-run the deployment"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MatrixCare Automation Deployment Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --status       Show service status"
        echo "  --logs         Show recent logs"
        echo "  --restart      Restart the service"
        echo "  --test         Run tests only"
        echo ""
        exit 0
        ;;
    --status)
        if [[ -f "$APP_DIR/status.sh" ]]; then
            "$APP_DIR/status.sh"
        else
            echo "Status script not found. Run deployment first."
        fi
        exit 0
        ;;
    --logs)
        if [[ -f "$APP_DIR/logs.sh" ]]; then
            "$APP_DIR/logs.sh"
        else
            echo "Logs script not found. Run deployment first."
        fi
        exit 0
        ;;
    --restart)
        if [[ -f "$APP_DIR/restart.sh" ]]; then
            "$APP_DIR/restart.sh"
        else
            echo "Restart script not found. Run deployment first."
        fi
        exit 0
        ;;
    --test)
        if [[ -d "$APP_DIR" ]]; then
            cd "$APP_DIR"
            source "$VENV_DIR/bin/activate"
            run_tests
        else
            echo "Application not deployed. Run deployment first."
        fi
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac