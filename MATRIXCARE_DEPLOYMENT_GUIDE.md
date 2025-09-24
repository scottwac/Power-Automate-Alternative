# MatrixCare Looker Dashboard Automation - Deployment Guide

## Overview
The MatrixCare automation program has been configured to:
- ✅ Look for emails with subject "MatrixCare Automation for Looker Dash"
- ✅ Run every other Tuesday starting September 30, 2025
- ✅ Check at 11:20 AM, then again at 12:00 PM if no email found
- ✅ Append data to your Google Sheet (doesn't replace existing data)
- ✅ Upload to Google Drive folder: `1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq`

## Schedule
**First run:** September 30, 2025 at 11:20 AM & 12:00 PM
**Subsequent runs:** Every 2 weeks (October 14, October 28, November 11, etc.)

## Deployment Options

### Option 1: Keep Running on Server (Recommended)
This keeps the program running continuously on your server:

```bash
# Navigate to your project directory
cd "C:\Users\AedhanCornish\OneDrive - Orchard Digital Marketing, Inc\Desktop\Matrix Care Automation"

# Activate virtual environment
venv\Scripts\activate

# Run the program (it will stay running and check the schedule)
python email_processor.py
```

**Pros:**
- Fully automated - no manual intervention needed
- Runs exactly on schedule
- Logs all activity for monitoring

**Cons:**
- Uses server resources continuously
- Need to restart if server reboots

### Option 2: Use Windows Task Scheduler
Set up a scheduled task to run the program only at the target times:

1. Open Windows Task Scheduler
2. Create a new task
3. Set trigger for every 2 weeks on Tuesday at 11:20 AM
4. Set action to run: `python email_processor.py --once`
5. Repeat for 12:00 PM

**Pros:**
- Uses fewer server resources
- Automatically restarts after reboots
- Built into Windows

**Cons:**
- More complex setup
- Less flexible logging

### Option 3: Run as Windows Service
Convert the program to run as a Windows service:

```bash
# Install service wrapper (if needed)
pip install pywin32

# Then set up as a service (requires admin rights)
```

## Running the Program

### Test Run (Recommended First)
Before deploying, test that everything works:

```bash
# Test authentication
python email_processor.py --test-auth

# Run once to test functionality
python email_processor.py --once

# Run the unit test to verify scheduling
cd "unit testing"
python run_matrixcare_test.py
```

### Production Run
For continuous operation:

```bash
python email_processor.py
```

The program will output logs showing:
- When it's checking for emails
- Whether it found any emails to process
- Success/failure of Google Sheets updates

## Required Configuration

Make sure these environment variables are set (or use the defaults):

```env
# Email settings
GMAIL_SUBJECT_FILTER=MatrixCare Automation for Looker Dash
GMAIL_FROM_EMAIL=growatorchard@gmail.com

# Google Drive folder
GOOGLE_DRIVE_FOLDER_ID=1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq

# Google Sheets (set this to your target spreadsheet ID)
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here

# Logging
LOG_LEVEL=INFO
LOG_FILE=email_processor.log
```

## Monitoring

The program creates logs in `email_processor.log`. Key things to monitor:

```bash
# View recent activity
tail -f email_processor.log

# Check for errors
grep ERROR email_processor.log

# See when it last ran
grep "Starting email processing cycle" email_processor.log
```

## Google Sheets Data Format

When emails are found, data is appended to your Google Sheet with columns:
1. **Timestamp** - When the email was processed
2. **From Email** - Sender's email address  
3. **Subject** - Email subject line
4. **Content** - First 1000 characters of email body
5. **Status** - "Processed"

## Troubleshooting

### Program Not Running at Expected Times
- Check the logs for "Today is not a target Tuesday" messages
- Verify the current date calculation with: `python -c "from datetime import date; print('Today:', date.today(), 'Weekday:', date.today().weekday())"`

### Authentication Issues
- Run `python email_processor.py --test-auth`
- Check that credential files exist: `credentials.json`, `token.json`, `drive_token.json`, `sheets_token.json`

### No Emails Found
- Check Gmail manually for emails with the exact subject
- Verify the sender email address matches your configuration
- Check spam folder

### Google Sheets Not Updating
- Verify `GOOGLE_SHEETS_SPREADSHEET_ID` is set correctly
- Check that the Google Sheets service account has edit permissions
- Look for "Failed to append data" in logs

## Stopping the Program

To stop the running program:
- Press `Ctrl+C` in the terminal
- Or kill the process if running in background

## Next Steps

1. **Test Everything:** Run `python email_processor.py --test-auth` to verify all connections work
2. **Set Spreadsheet ID:** Update the `GOOGLE_SHEETS_SPREADSHEET_ID` environment variable with your actual spreadsheet ID
3. **Choose Deployment Method:** Pick Option 1 (keep running) for simplest setup
4. **Monitor First Run:** Watch the logs on September 30, 2025 to ensure it works correctly

The program is now ready for the September 30, 2025 launch! 🚀
