#!/bin/bash

# Credentials Setup Script for Email Processor
# Run this after the main deployment to set up Google API credentials

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_DIR="/opt/email-processor"
APP_USER="emailprocessor"

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

echo -e "${BLUE}🔐 Setting up Google API Credentials${NC}"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

# Check if credentials.json exists in current directory
if [ ! -f "credentials.json" ]; then
    print_error "credentials.json not found in current directory"
    echo ""
    echo "Please:"
    echo "1. Download your Google API credentials from Google Cloud Console"
    echo "2. Save it as 'credentials.json' in this directory"
    echo "3. Run this script again"
    exit 1
fi

print_info "Copying credentials.json to application directory..."
cp credentials.json $APP_DIR/
chown $APP_USER:$APP_USER $APP_DIR/credentials.json
chmod 600 $APP_DIR/credentials.json
print_status "Credentials copied and secured"

print_info "Testing authentication..."
cd $APP_DIR
sudo -u $APP_USER ./venv/bin/python email_processor.py --test-auth

if [ $? -eq 0 ]; then
    print_status "Authentication test successful!"
    echo ""
    print_info "You can now start the service:"
    echo "systemctl start email-processor"
else
    print_error "Authentication test failed"
    echo "Please check your credentials and try again"
    exit 1
fi
