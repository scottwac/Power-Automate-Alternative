#!/bin/bash

# Email Processor Deployment Script for Ubuntu Azure VM
# This script sets up the email processor as a systemd service

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="email-processor"
APP_USER="emailprocessor"
APP_DIR="/opt/email-processor"
SERVICE_NAME="email-processor"
PYTHON_VERSION="3.11"

echo -e "${BLUE}🚀 Starting Email Processor Deployment on Ubuntu Azure VM${NC}"
echo "=================================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_info "Step 1: Updating system packages..."
apt update && apt upgrade -y
print_status "System packages updated"

print_info "Step 2: Installing Python and required system packages..."
apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev \
    python3-pip git curl wget unzip software-properties-common \
    build-essential libssl-dev libffi-dev
print_status "Python and system packages installed"

print_info "Step 3: Creating application user..."
if id "$APP_USER" &>/dev/null; then
    print_warning "User $APP_USER already exists"
else
    useradd --system --home $APP_DIR --shell /bin/bash --create-home $APP_USER
    print_status "Created user: $APP_USER"
fi

print_info "Step 4: Creating application directory..."
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR
print_status "Application directory created: $APP_DIR"

print_info "Step 5: Setting up Python virtual environment..."
sudo -u $APP_USER python${PYTHON_VERSION} -m venv $APP_DIR/venv
print_status "Virtual environment created"

print_info "Step 6: Copying application files..."
# Copy all Python files and requirements
cp *.py $APP_DIR/
cp requirements.txt $APP_DIR/
cp env_template.txt $APP_DIR/

# Copy or create .env file
if [ -f ".env" ]; then
    cp .env $APP_DIR/
    print_status "Copied existing .env file"
else
    cp env_template.txt $APP_DIR/.env
    print_warning "Created .env from template - you need to configure it"
fi

# Set ownership
chown -R $APP_USER:$APP_USER $APP_DIR
print_status "Application files copied"

print_info "Step 7: Installing Python dependencies..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt
print_status "Python dependencies installed"

print_info "Step 8: Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Email Processor Service
After=network.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python email_processor.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF

print_status "Systemd service created"

print_info "Step 9: Setting up log rotation..."
cat > /etc/logrotate.d/${SERVICE_NAME} << EOF
$APP_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su $APP_USER $APP_USER
}
EOF

print_status "Log rotation configured"

print_info "Step 10: Reloading systemd and enabling service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
print_status "Service enabled"

# Create management scripts
print_info "Step 11: Creating management scripts..."

# Service management script
cat > $APP_DIR/manage_service.sh << 'EOF'
#!/bin/bash

SERVICE_NAME="email-processor"
APP_DIR="/opt/email-processor"

case "$1" in
    start)
        echo "Starting email processor service..."
        sudo systemctl start $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    stop)
        echo "Stopping email processor service..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "Restarting email processor service..."
        sudo systemctl restart $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    status)
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    logs)
        echo "Showing recent logs..."
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    logs-tail)
        echo "Following logs..."
        tail -f $APP_DIR/email_processor.log
        ;;
    test)
        echo "Running one-time test..."
        cd $APP_DIR
        sudo -u emailprocessor ./venv/bin/python email_processor.py --once
        ;;
    update)
        echo "Updating application..."
        sudo systemctl stop $SERVICE_NAME
        # Add your update commands here
        sudo systemctl start $SERVICE_NAME
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|logs-tail|test|update}"
        exit 1
        ;;
esac
EOF

chmod +x $APP_DIR/manage_service.sh
chown $APP_USER:$APP_USER $APP_DIR/manage_service.sh

# Create symlink for easy access
ln -sf $APP_DIR/manage_service.sh /usr/local/bin/email-processor

print_status "Management scripts created"

print_info "Step 12: Creating monitoring script..."
cat > $APP_DIR/monitor.sh << 'EOF'
#!/bin/bash

APP_DIR="/opt/email-processor"
SERVICE_NAME="email-processor"

echo "=== Email Processor Status ==="
echo "Service Status:"
systemctl is-active $SERVICE_NAME

echo -e "\nLast 10 log entries:"
tail -n 10 $APP_DIR/email_processor.log

echo -e "\nDisk usage:"
du -sh $APP_DIR

echo -e "\nMemory usage:"
ps aux | grep email_processor.py | grep -v grep | awk '{print $4"%"}'

echo -e "\nService uptime:"
systemctl show $SERVICE_NAME --property=ActiveEnterTimestamp
EOF

chmod +x $APP_DIR/monitor.sh
chown $APP_USER:$APP_USER $APP_DIR/monitor.sh

print_status "Monitoring script created"

print_info "Step 13: Setting up firewall (if needed)..."
# Most cloud VMs have external firewalls, but set up local rules
ufw allow ssh
ufw --force enable
print_status "Basic firewall configured"

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Configure your credentials:"
echo "   - Copy your Google credentials.json to: $APP_DIR/credentials.json"
echo "   - Edit the .env file: $APP_DIR/.env"
echo ""
echo "2. Test the setup:"
echo "   sudo -u $APP_USER $APP_DIR/venv/bin/python $APP_DIR/email_processor.py --test-auth"
echo ""
echo "3. Start the service:"
echo "   systemctl start $SERVICE_NAME"
echo ""
echo -e "${BLUE}Management commands:${NC}"
echo "   email-processor start     # Start the service"
echo "   email-processor stop      # Stop the service"
echo "   email-processor restart   # Restart the service"
echo "   email-processor status    # Check service status"
echo "   email-processor logs      # View real-time logs"
echo "   email-processor test      # Run one-time test"
echo ""
echo -e "${BLUE}Monitoring:${NC}"
echo "   $APP_DIR/monitor.sh       # Check system status"
echo "   journalctl -u $SERVICE_NAME -f  # Follow service logs"
echo ""
echo -e "${YELLOW}Important files:${NC}"
echo "   Application: $APP_DIR/"
echo "   Logs: $APP_DIR/email_processor.log"
echo "   Service: /etc/systemd/system/${SERVICE_NAME}.service"
echo "   Config: $APP_DIR/.env"
echo ""

if [ ! -f "$APP_DIR/credentials.json" ]; then
    print_warning "Don't forget to upload your Google credentials.json file!"
fi

if grep -q "GOOGLE_DRIVE_FOLDER_ID=$" "$APP_DIR/.env"; then
    print_warning "Configure your .env file before starting the service"
fi
