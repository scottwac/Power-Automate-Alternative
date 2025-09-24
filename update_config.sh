#!/bin/bash

# Configuration Update Script for Email Processor
# Use this to easily update the .env configuration

set -e

APP_DIR="/opt/email-processor"
APP_USER="emailprocessor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo -e "${BLUE}⚙️  Email Processor Configuration Update${NC}"
echo "======================================="

ENV_FILE="$APP_DIR/.env"

# Backup current config
cp $ENV_FILE $ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)
print_info "Current configuration backed up"

echo ""
echo "Current configuration:"
echo "====================="
cat $ENV_FILE
echo ""

# Interactive configuration update
read -p "Update Gmail sender email? [current: $(grep GMAIL_FROM_EMAIL $ENV_FILE | cut -d'=' -f2)] (y/N): " update_email
if [[ $update_email =~ ^[Yy]$ ]]; then
    read -p "Enter Gmail sender email: " gmail_email
    sed -i "s/GMAIL_FROM_EMAIL=.*/GMAIL_FROM_EMAIL=$gmail_email/" $ENV_FILE
    print_status "Gmail sender email updated"
fi

read -p "Update subject filter? [current: $(grep GMAIL_SUBJECT_FILTER $ENV_FILE | cut -d'=' -f2)] (y/N): " update_subject
if [[ $update_subject =~ ^[Yy]$ ]]; then
    read -p "Enter subject filter: " subject_filter
    sed -i "s/GMAIL_SUBJECT_FILTER=.*/GMAIL_SUBJECT_FILTER=$subject_filter/" $ENV_FILE
    print_status "Subject filter updated"
fi

read -p "Update Google Drive folder ID? [current: $(grep GOOGLE_DRIVE_FOLDER_ID $ENV_FILE | cut -d'=' -f2)] (y/N): " update_folder
if [[ $update_folder =~ ^[Yy]$ ]]; then
    echo "Enter Google Drive folder ID (leave empty for root folder):"
    echo "You can get this from the folder URL: https://drive.google.com/drive/folders/FOLDER_ID_HERE"
    read -p "Folder ID: " folder_id
    sed -i "s/GOOGLE_DRIVE_FOLDER_ID=.*/GOOGLE_DRIVE_FOLDER_ID=$folder_id/" $ENV_FILE
    print_status "Google Drive folder ID updated"
fi

read -p "Update check interval? [current: $(grep CHECK_INTERVAL_MINUTES $ENV_FILE | cut -d'=' -f2) minutes] (y/N): " update_interval
if [[ $update_interval =~ ^[Yy]$ ]]; then
    read -p "Enter check interval in minutes: " interval
    sed -i "s/CHECK_INTERVAL_MINUTES=.*/CHECK_INTERVAL_MINUTES=$interval/" $ENV_FILE
    print_status "Check interval updated"
fi

read -p "Enable Google Sheets creation? [current: $(grep CREATE_GOOGLE_SHEETS $ENV_FILE | cut -d'=' -f2)] (y/N): " update_sheets
if [[ $update_sheets =~ ^[Yy]$ ]]; then
    echo "Create Google Sheets instead of CSV files?"
    echo "  true  - Create Google Sheets (recommended)"
    echo "  false - Create CSV files"
    read -p "Enable Google Sheets (true/false): " sheets_enabled
    sed -i "s/CREATE_GOOGLE_SHEETS=.*/CREATE_GOOGLE_SHEETS=$sheets_enabled/" $ENV_FILE
    print_status "Google Sheets setting updated"
fi

# Set correct ownership
chown $APP_USER:$APP_USER $ENV_FILE

echo ""
echo "Updated configuration:"
echo "====================="
cat $ENV_FILE
echo ""

read -p "Restart the service to apply changes? (y/N): " restart_service
if [[ $restart_service =~ ^[Yy]$ ]]; then
    systemctl restart email-processor
    print_status "Service restarted with new configuration"
    echo ""
    print_info "Checking service status..."
    systemctl status email-processor --no-pager
fi

print_status "Configuration update completed!"
