# 🚀 Email Processor Deployment Guide for Ubuntu Azure VM

This guide will help you deploy the Email Processor as a production service on your Ubuntu Azure VM.

## 📋 Prerequisites

- Ubuntu 20.04+ Azure VM
- Root/sudo access
- Internet connectivity
- Google Cloud Console project with Gmail and Drive APIs enabled

## 🛠 Deployment Steps

### 1. Upload Files to VM

Upload these files to your Azure VM:
```bash
# Core application files
*.py
requirements.txt
env_template.txt

# Deployment scripts
deploy.sh
setup_credentials.sh
update_config.sh

# Your Google API credentials
credentials.json
```

### 2. Run Deployment Script

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Run the deployment (requires sudo)
sudo ./deploy.sh
```

This script will:
- ✅ Update system packages
- ✅ Install Python 3.11 and dependencies
- ✅ Create dedicated application user (`emailprocessor`)
- ✅ Set up application directory (`/opt/email-processor`)
- ✅ Create Python virtual environment
- ✅ Install Python dependencies
- ✅ Create systemd service
- ✅ Set up log rotation
- ✅ Create management scripts

### 3. Set Up Credentials

```bash
# Make credentials script executable
chmod +x setup_credentials.sh

# Set up Google API credentials
sudo ./setup_credentials.sh
```

This will:
- Copy `credentials.json` to the application directory
- Test authentication with Google APIs
- Verify everything is working

### 4. Configure Application

```bash
# Make config script executable
chmod +x update_config.sh

# Update configuration interactively
sudo ./update_config.sh
```

Or edit manually:
```bash
sudo nano /opt/email-processor/.env
```

### 5. Start the Service

```bash
# Start the service
sudo systemctl start email-processor

# Check status
sudo systemctl status email-processor

# Enable auto-start on boot
sudo systemctl enable email-processor
```

## 🎮 Service Management

### Quick Commands

```bash
# Service control
email-processor start      # Start service
email-processor stop       # Stop service
email-processor restart    # Restart service
email-processor status     # Check status
email-processor logs       # View real-time logs
email-processor test       # Run one-time test

# Monitoring
/opt/email-processor/monitor.sh  # System overview
```

### Detailed Commands

```bash
# View service logs
sudo journalctl -u email-processor -f

# View application logs
tail -f /opt/email-processor/email_processor.log

# Check service status
sudo systemctl status email-processor

# Restart service
sudo systemctl restart email-processor
```

## 📁 Important File Locations

| Purpose | Location |
|---------|----------|
| Application Code | `/opt/email-processor/` |
| Configuration | `/opt/email-processor/.env` |
| Credentials | `/opt/email-processor/credentials.json` |
| Application Logs | `/opt/email-processor/email_processor.log` |
| System Service | `/etc/systemd/system/email-processor.service` |
| Management Scripts | `/opt/email-processor/manage_service.sh` |

## 🔧 Configuration Options

Edit `/opt/email-processor/.env`:

```bash
# Gmail settings
GMAIL_FROM_EMAIL=your-sender@gmail.com
GMAIL_SUBJECT_FILTER=TEST
GMAIL_LABEL=INBOX

# Google Drive settings  
GOOGLE_DRIVE_FOLDER_ID=1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq

# Processing settings
CHECK_INTERVAL_MINUTES=5
MAX_ROWS_TO_PROCESS=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=email_processor.log
```

## 🔍 Monitoring and Troubleshooting

### Check Service Health

```bash
# Quick health check
/opt/email-processor/monitor.sh

# Detailed service status
sudo systemctl status email-processor --no-pager -l

# Follow live logs
sudo journalctl -u email-processor -f
```

### Common Issues

1. **Authentication Failed**
   ```bash
   # Re-run credential setup
   sudo ./setup_credentials.sh
   ```

2. **Service Won't Start**
   ```bash
   # Check logs for errors
   sudo journalctl -u email-processor --no-pager -l
   
   # Verify configuration
   sudo -u emailprocessor /opt/email-processor/venv/bin/python /opt/email-processor/email_processor.py --test-auth
   ```

3. **Permission Issues**
   ```bash
   # Fix ownership
   sudo chown -R emailprocessor:emailprocessor /opt/email-processor
   ```

4. **Python Dependencies**
   ```bash
   # Reinstall dependencies
   sudo -u emailprocessor /opt/email-processor/venv/bin/pip install -r /opt/email-processor/requirements.txt
   ```

### Log Analysis

```bash
# View recent errors
sudo journalctl -u email-processor --since "1 hour ago" | grep ERROR

# Check application logs
grep ERROR /opt/email-processor/email_processor.log

# Monitor file uploads
grep "uploaded successfully" /opt/email-processor/email_processor.log
```

## 🚀 Performance Tuning

### Adjust Check Frequency

```bash
# Edit configuration
sudo nano /opt/email-processor/.env

# Change CHECK_INTERVAL_MINUTES (default: 5)
CHECK_INTERVAL_MINUTES=3  # Check every 3 minutes

# Restart service
sudo systemctl restart email-processor
```

### Resource Monitoring

```bash
# Check memory usage
ps aux | grep email_processor

# Check disk usage  
du -sh /opt/email-processor

# Monitor system resources
htop
```

## 🔄 Updates and Maintenance

### Update Application Code

1. Stop the service:
   ```bash
   sudo systemctl stop email-processor
   ```

2. Update files:
   ```bash
   sudo cp new_files/* /opt/email-processor/
   sudo chown emailprocessor:emailprocessor /opt/email-processor/*
   ```

3. Update dependencies (if needed):
   ```bash
   sudo -u emailprocessor /opt/email-processor/venv/bin/pip install -r /opt/email-processor/requirements.txt
   ```

4. Restart service:
   ```bash
   sudo systemctl start email-processor
   ```

### Backup Important Data

```bash
# Backup configuration and tokens
sudo tar czf email-processor-backup-$(date +%Y%m%d).tar.gz \
  /opt/email-processor/.env \
  /opt/email-processor/credentials.json \
  /opt/email-processor/token.json \
  /opt/email-processor/drive_token.json \
  /opt/email-processor/email_processor.log
```

## 🔐 Security Considerations

- The service runs as a dedicated user (`emailprocessor`) with minimal privileges
- Credentials are secured with 600 permissions
- Application directory is protected
- Firewall is configured for basic security
- Log rotation prevents disk space issues

## 📞 Support

If you encounter issues:

1. Check the logs: `sudo journalctl -u email-processor -f`
2. Verify configuration: `/opt/email-processor/monitor.sh`
3. Test authentication: `email-processor test`
4. Check system resources: `htop` and `df -h`

---

**🎉 Your Email Processor is now running as a production service on Ubuntu!**
