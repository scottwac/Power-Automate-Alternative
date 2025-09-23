# Email Processor Setup Instructions

This Python script replaces your Power Automate flow for processing emails with CSV attachments.

## 📁 Files Created

- `email_processor.py` - Main script
- `gmail_service.py` - Gmail API integration
- `google_drive_service.py` - Google Drive API integration  
- `csv_processor.py` - CSV data processing
- `requirements.txt` - Python dependencies
- `env_template.txt` - Environment variables template

## 🔧 Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Google API Credentials

#### For Gmail API:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create credentials (OAuth 2.0 client ID)
5. Download the credentials file as `credentials.json`

#### For Google Drive API:
1. In the same project, enable Google Drive API
2. Use the same `credentials.json` file (or create separate one)

### 3. Configure Environment Variables

1. Copy `env_template.txt` to `.env`
2. Update the values in `.env`:

```env
# Gmail API Configuration
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
GMAIL_FROM_EMAIL=growatorchard@gmail.com
GMAIL_SUBJECT_FILTER=Test
GMAIL_LABEL=INBOX

# Google Drive API Configuration
GOOGLE_DRIVE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_FOLDER_ID=/

# Processing Configuration
CHECK_INTERVAL_MINUTES=5
MAX_ROWS_TO_PROCESS=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=email_processor.log
```

### 4. First Run (Authentication)

Test authentication:
```bash
python email_processor.py --test-auth
```

This will open a browser window for OAuth authentication for both Gmail and Google Drive APIs.

## 🚀 Usage

### Run Once (for testing)
```bash
python email_processor.py --once
```

### Run Scheduled (production)
```bash
python email_processor.py
```

The script will:
- Check for new emails every 5 minutes (configurable)
- Process CSV attachments from `growatorchard@gmail.com` with subject "Test"
- Upload original CSV with timestamp to Google Drive
- Process and transform the data
- Upload processed CSV with new timestamp to Google Drive

## 📊 What the Script Does

1. **Email Monitoring**: Checks Gmail every 5 minutes for new emails matching criteria
2. **File Upload**: Uploads original CSV attachments to Google Drive with timestamp
3. **Data Processing**: 
   - Parses CSV data
   - Transforms into structured format with fields:
     - LeadCreationDate
     - InquiryDate  
     - CommunityName
     - Classification
     - TotalLeads
     - SubSourceName
     - SourceName
4. **Output Generation**: Creates new CSV with processed data
5. **Final Upload**: Uploads processed CSV to Google Drive

## 🔍 Monitoring

- Check `email_processor.log` for detailed logs
- The script logs all operations including successes and errors
- Use `--once` flag for manual testing

## 🛠 Troubleshooting

1. **Authentication Issues**: 
   - Make sure `credentials.json` is in the same directory
   - Run `--test-auth` to verify setup

2. **Permission Errors**:
   - Ensure Gmail and Google Drive APIs are enabled
   - Check OAuth scopes in Google Cloud Console

3. **File Not Found**:
   - Verify paths in `.env` file
   - Make sure credentials file exists

## 📈 Advanced Configuration

- Modify `CHECK_INTERVAL_MINUTES` to change monitoring frequency
- Adjust `MAX_ROWS_TO_PROCESS` for large CSV files
- Change `LOG_LEVEL` to DEBUG for more detailed logging
- Set `GOOGLE_DRIVE_FOLDER_ID` to upload to specific folder

## 🔄 Running as a Service

For production, consider running as a system service:

### Windows (using Task Scheduler)
Create a task that runs `python email_processor.py` on startup

### Linux (using systemd)
Create a service file in `/etc/systemd/system/email-processor.service`

### Docker
The script can be containerized for easier deployment.
