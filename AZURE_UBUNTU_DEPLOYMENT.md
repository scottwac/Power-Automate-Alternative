# MatrixCare Automation - Azure Ubuntu Server Deployment

## Prerequisites
- Azure Ubuntu server with SSH access
- Python 3.8+ installed
- Internet access for Google API calls

## Step 1: Prepare Local Files

First, create the environment file with your Google Sheets ID:

```bash
# On your local Windows machine, create .env file
echo "GOOGLE_SHEETS_SPREADSHEET_ID=1tQT3x-X9NxK_Rfg4uYhz71kvFrNbPXR-Wo3QBvaKdGQ" > .env
echo "GMAIL_SUBJECT_FILTER=MatrixCare Automation for Looker Dash" >> .env
echo "GOOGLE_DRIVE_FOLDER_ID=1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq" >> .env
echo "LOG_LEVEL=INFO" >> .env
```

## Step 2: Upload Files to Azure Server

```bash
# Replace with your server details
SERVER_IP="your-azure-server-ip"
USERNAME="your-username"

# Create directory on server
ssh $USERNAME@$SERVER_IP "mkdir -p ~/matrixcare-automation"

# Upload all Python files
scp *.py $USERNAME@$SERVER_IP:~/matrixcare-automation/
scp requirements.txt $USERNAME@$SERVER_IP:~/matrixcare-automation/
scp .env $USERNAME@$SERVER_IP:~/matrixcare-automation/

# Upload credentials (IMPORTANT!)
scp credentials.json $USERNAME@$SERVER_IP:~/matrixcare-automation/
scp token.json $USERNAME@$SERVER_IP:~/matrixcare-automation/
scp drive_token.json $USERNAME@$SERVER_IP:~/matrixcare-automation/
scp sheets_token.json $USERNAME@$SERVER_IP:~/matrixcare-automation/

# Upload unit tests (optional, for testing)
ssh $USERNAME@$SERVER_IP "mkdir -p ~/matrixcare-automation/unit_testing"
scp "unit testing"/*.py $USERNAME@$SERVER_IP:~/matrixcare-automation/unit_testing/
```

## Step 3: Setup Environment on Ubuntu Server

```bash
# SSH into your server
ssh $USERNAME@$SERVER_IP

# Navigate to project directory
cd ~/matrixcare-automation

# Update system packages
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 email_processor.py --test-auth
```

## Step 4: Test the Application

```bash
# Still on the server, test the authentication
python3 email_processor.py --test-auth

# Test a single run
python3 email_processor.py --once

# Test the scheduling logic
cd unit_testing
python3 run_matrixcare_test.py
cd ..
```

## Step 5: Create Systemd Service (Recommended)

Create a service file to run the program automatically:

```bash
# Create service file
sudo nano /etc/systemd/system/matrixcare-automation.service
```

Paste this content:

```ini
[Unit]
Description=MatrixCare Looker Dashboard Automation
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/matrixcare-automation
Environment=PATH=/home/YOUR_USERNAME/matrixcare-automation/venv/bin
ExecStart=/home/YOUR_USERNAME/matrixcare-automation/venv/bin/python email_processor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Replace `YOUR_USERNAME` with your actual username!**

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable matrixcare-automation
sudo systemctl start matrixcare-automation

# Check service status
sudo systemctl status matrixcare-automation
```

## Step 6: Monitor the Service

```bash
# View logs
sudo journalctl -u matrixcare-automation -f

# Check if service is running
sudo systemctl is-active matrixcare-automation

# View application logs
tail -f ~/matrixcare-automation/email_processor.log

# Restart service if needed
sudo systemctl restart matrixcare-automation
```

## Alternative: Run with Screen (Simple Method)

If you prefer not to use systemd:

```bash
# Install screen
sudo apt install screen

# Start a screen session
screen -S matrixcare

# Navigate to directory and activate venv
cd ~/matrixcare-automation
source venv/bin/activate

# Run the program
python3 email_processor.py

# Detach from screen: Ctrl+A, then D
# Reattach later: screen -r matrixcare
```

## Step 7: Verify Deployment

```bash
# Check that the program recognizes the schedule
python3 -c "
from datetime import date
from email_processor import EmailProcessor
import os
os.chdir('/home/YOUR_USERNAME/matrixcare-automation')
processor = EmailProcessor()
print('Reference Tuesday:', processor.reference_tuesday.date())
print('Today is target Tuesday:', processor.is_target_tuesday())
print('Should check emails now:', processor.should_check_emails())
"
```

## Important Notes

### Security
- Keep your credential files secure (`credentials.json`, etc.)
- Consider using Google Cloud IAM service accounts for production
- Ensure your Azure server firewall allows outbound HTTPS (port 443)

### Monitoring
```bash
# Set up log rotation
sudo nano /etc/logrotate.d/matrixcare
```

Add:
```
/home/YOUR_USERNAME/matrixcare-automation/email_processor.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 YOUR_USERNAME YOUR_USERNAME
}
```

### Troubleshooting

1. **Permission errors:**
   ```bash
   chmod +x ~/matrixcare-automation/*.py
   ```

2. **Google API authentication issues:**
   ```bash
   # Check credential files exist
   ls -la ~/matrixcare-automation/*.json
   ```

3. **Service won't start:**
   ```bash
   # Check service logs
   sudo journalctl -u matrixcare-automation --no-pager
   ```

4. **Time zone issues:**
   ```bash
   # Set correct timezone
   sudo timedatectl set-timezone America/New_York  # or your timezone
   ```

## Schedule Confirmation

Your program will run:
- **First time:** September 30, 2025 at 11:20 AM & 12:00 PM
- **Then every 2 weeks:** October 14, October 28, November 11, etc.
- **Target Google Sheet:** `1tQT3x-X9NxK_Rfg4uYhz71kvFrNbPXR-Wo3QBvaKdGQ`

## Quick Commands Reference

```bash
# Start service
sudo systemctl start matrixcare-automation

# Stop service  
sudo systemctl stop matrixcare-automation

# View logs
sudo journalctl -u matrixcare-automation -f

# Test manually
cd ~/matrixcare-automation && source venv/bin/activate && python3 email_processor.py --once
```

Your MatrixCare automation is now ready for deployment! 🚀
