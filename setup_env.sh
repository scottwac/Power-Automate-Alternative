#!/bin/bash

# MatrixCare Looker Dashboard Automation - Environment Setup
# Run this script to set up environment variables

echo "Creating .env file with your Google Sheets configuration..."

cat > .env << EOF
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

echo "✅ .env file created successfully!"
echo "📋 Your configuration:"
echo "   - Google Sheets ID: 1tQT3x-X9NxK_Rfg4uYhz71kvFrNbPXR-Wo3QBvaKdGQ"
echo "   - Email Subject: MatrixCare Automation for Looker Dash"
echo "   - Drive Folder ID: 1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq"
echo ""
echo "Ready for Azure Ubuntu deployment! 🚀"
