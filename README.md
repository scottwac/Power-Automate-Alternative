# MatrixCare Looker Dashboard Automation

Automated email processing system that monitors Gmail for MatrixCare reports and appends data to Google Sheets on a bi-weekly schedule.

## 🎯 Overview

This system automatically:
- ✅ Monitors Gmail for emails with subject "MatrixCare Automation for Looker Dash"
- ✅ Runs every other Tuesday starting September 30, 2025
- ✅ Checks at 11:20 AM, then again at 12:00 PM if no email found
- ✅ Appends email data to Google Sheets (ID: `1tQT3x-X9NxK_Rfg4uYhz71kvFrNbPXR-Wo3QBvaKdGQ`)
- ✅ Stores files in Google Drive folder: `1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq`

## 🚀 Quick Start

### Prerequisites
- Ubuntu server (tested on Azure)
- Python 3.8+
- Google API credentials
- Gmail and Google Drive access

### One-Command Deployment
```bash
# Make deployment script executable and run
chmod +x deploy.sh
./deploy.sh
```

The deployment script handles everything:
- Environment setup
- Dependency installation
- Service configuration
- Authentication testing
- Monitoring tools setup

## 📅 Schedule

| Date | Type | Status |
|------|------|--------|
| September 30, 2025 | First Run | ✅ Configured |
| October 7, 2025 | Skip Week | ❌ |
| October 14, 2025 | Target Run | ✅ |
| October 21, 2025 | Skip Week | ❌ |
| October 28, 2025 | Target Run | ✅ |
| November 11, 2025 | Target Run | ✅ |

**Times:** 11:20 AM and 12:00 PM on target Tuesdays

## 🛠️ Management Commands

After deployment, use these commands:

```bash
# Quick status check
./status.sh

# View logs (interactive)
./logs.sh

# Restart service
./restart.sh

# Manual service control
sudo systemctl start matrixcare-automation
sudo systemctl stop matrixcare-automation
sudo systemctl restart matrixcare-automation
sudo systemctl status matrixcare-automation
```

## 📊 Monitoring

### Real-Time Monitoring

#### 1. Service Status
```bash
# Check if service is running
./status.sh

# Or check directly
sudo systemctl status matrixcare-automation
```

#### 2. Live Logs
```bash
# View live service logs
sudo journalctl -u matrixcare-automation -f

# View live application logs
tail -f ~/matrixcare-automation/email_processor.log

# Interactive log viewer
./logs.sh
```

#### 3. Resource Usage
```bash
# Check memory and CPU usage
ps aux | grep email_processor

# System resource monitoring
htop
```

### Log Analysis

#### Important Log Patterns

**✅ Successful Operation:**
```
INFO - First check time (11:20 AM) - checking for emails
INFO - Starting email processing cycle
INFO - Found 1 emails to process
INFO - Successfully appended MatrixCare data to Google Sheet
```

**❌ No Emails Found:**
```
INFO - First check time (11:20 AM) - checking for emails
INFO - Starting email processing cycle
INFO - No new emails found
```

**⏰ Off-Schedule:**
```
INFO - Today is not a target Tuesday, skipping email check
```

**🔐 Authentication Issues:**
```
ERROR - Error initializing services: [auth error details]
```

#### Log Commands
```bash
# Search for errors
grep -i "error\|fail\|exception" ~/matrixcare-automation/email_processor.log

# Check last 50 entries
tail -50 ~/matrixcare-automation/email_processor.log

# Search for specific terms
grep -i "target tuesday" ~/matrixcare-automation/email_processor.log

# View logs from specific date
grep "2025-09-30" ~/matrixcare-automation/email_processor.log
```

### Health Checks

#### Daily Health Check Script
Create a daily health check with cron:

```bash
# Edit crontab
crontab -e

# Add this line for daily 9 AM health check
0 9 * * * /home/$USER/matrixcare-automation/status.sh > /tmp/matrixcare-health.log 2>&1
```

#### Manual Health Checks
```bash
# Test authentication
cd ~/matrixcare-automation
source venv/bin/activate
python3 email_processor.py --test-auth

# Test single run
python3 email_processor.py --once

# Run unit tests
cd unit_testing
python3 run_matrixcare_test.py
```

### Monitoring Checklist

#### Weekly Monitoring (Recommended)
- [ ] Check service status: `./status.sh`
- [ ] Review recent logs: `tail -50 ~/matrixcare-automation/email_processor.log`
- [ ] Verify disk space: `df -h`
- [ ] Check for errors: `grep ERROR ~/matrixcare-automation/email_processor.log`

#### Target Tuesday Monitoring
On scheduled run days (every other Tuesday):

- [ ] **11:15 AM:** Check service is running
- [ ] **11:25 AM:** Verify 11:20 run in logs
- [ ] **12:05 PM:** Check if 12:00 run was needed
- [ ] **End of day:** Verify Google Sheets was updated

#### Monthly Monitoring
- [ ] Check log file size: `ls -lh ~/matrixcare-automation/email_processor.log`
- [ ] Review service uptime: `sudo systemctl show matrixcare-automation --property=ActiveEnterTimestamp`
- [ ] Test manual run: `python3 email_processor.py --once`
- [ ] Verify Google API quotas

## 🔧 Configuration

### Environment Variables
Located in `~/matrixcare-automation/.env`:

```env
# Google Sheets Configuration
GOOGLE_SHEETS_SPREADSHEET_ID=1tQT3x-X9NxK_Rfg4uYhz71kvFrNbPXR-Wo3QBvaKdGQ

# Email Configuration
GMAIL_SUBJECT_FILTER=MatrixCare Automation for Looker Dash
GMAIL_FROM_EMAIL=growatorchard@gmail.com

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=email_processor.log
```

### Required Files
```
~/matrixcare-automation/
├── credentials.json          # Google API credentials
├── token.json               # Gmail OAuth token
├── drive_token.json         # Google Drive OAuth token
├── sheets_token.json        # Google Sheets OAuth token
├── .env                     # Environment configuration
└── email_processor.log      # Application logs
```

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service logs
sudo journalctl -u matrixcare-automation --no-pager

# Check configuration
cat ~/matrixcare-automation/.env

# Test authentication
cd ~/matrixcare-automation && source venv/bin/activate && python3 email_processor.py --test-auth
```

#### Authentication Errors
```bash
# Re-authenticate
cd ~/matrixcare-automation
source venv/bin/activate

# Remove old tokens
rm -f *token.json

# Run auth test to regenerate
python3 email_processor.py --test-auth
```

#### No Emails Processing
1. Check Gmail manually for emails with exact subject
2. Verify sender email address
3. Check spam folder
4. Review email filter settings

#### Google Sheets Not Updating
1. Verify spreadsheet ID in `.env`
2. Check Google Sheets API permissions
3. Ensure service account has edit access
4. Test manual update: `python3 email_processor.py --once`

### Emergency Procedures

#### Service Not Responding
```bash
# Force restart
sudo systemctl stop matrixcare-automation
sleep 5
sudo systemctl start matrixcare-automation

# Check status
./status.sh
```

#### Disk Space Issues
```bash
# Check space
df -h

# Rotate logs manually
sudo logrotate /etc/logrotate.d/matrixcare-automation

# Clean old logs
find ~/matrixcare-automation -name "*.log.*" -mtime +30 -delete
```

## 📞 Support

### Getting Help
1. **Check logs first:** `./logs.sh`
2. **Run status check:** `./status.sh`
3. **Test authentication:** `python3 email_processor.py --test-auth`
4. **Review this README**

### Useful Commands Reference
```bash
# Deployment
./deploy.sh                    # Full deployment
./deploy.sh --status          # Quick status
./deploy.sh --logs            # View logs
./deploy.sh --restart         # Restart service
./deploy.sh --test            # Run tests

# Service Management
sudo systemctl status matrixcare-automation
sudo systemctl restart matrixcare-automation
sudo journalctl -u matrixcare-automation -f

# Application
cd ~/matrixcare-automation && source venv/bin/activate
python3 email_processor.py --test-auth
python3 email_processor.py --once
```

## 📈 Performance

### Expected Resource Usage
- **CPU:** < 1% (idle), 10-20% (during processing)
- **Memory:** ~50-100 MB
- **Disk:** Logs rotate automatically, minimal growth
- **Network:** Minimal (only during email checks and Google API calls)

### Optimization
- Logs rotate daily, keep 30 days
- Service auto-restarts on failure
- Minimal resource usage when idle
- Efficient scheduling (only checks on target days)

---

**Last Updated:** September 2025  
**Version:** 1.0  
**Schedule Start:** September 30, 2025
