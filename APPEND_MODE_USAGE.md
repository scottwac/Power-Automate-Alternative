# Google Sheets Append Mode Usage

This document explains how to configure the email processor to append data to an existing Google Spreadsheet instead of creating new ones each time.

## Configuration

### Option 1: Append to Existing Spreadsheet

To append data to an existing Google Spreadsheet, set the `GOOGLE_SHEETS_SPREADSHEET_ID` environment variable in your `.env` file:

```env
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
CREATE_GOOGLE_SHEETS=true
GOOGLE_SHEETS_SPREADSHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

Where `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` is your Google Spreadsheet ID.

### Option 2: Create New Spreadsheets (Default Behavior)

To continue creating new spreadsheets each time (original behavior), leave the `GOOGLE_SHEETS_SPREADSHEET_ID` empty or comment it out:

```env
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
CREATE_GOOGLE_SHEETS=true
# GOOGLE_SHEETS_SPREADSHEET_ID=
```

## How to Get a Spreadsheet ID

1. Open your Google Spreadsheet in a web browser
2. Look at the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
3. Copy the `SPREADSHEET_ID` part from the URL

For example, if your URL is:
```
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0
```

Then your Spreadsheet ID is: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`

## Behavior

### Append Mode (when GOOGLE_SHEETS_SPREADSHEET_ID is set)
- New data will be appended to the end of the existing spreadsheet
- Headers are NOT added again (assuming they already exist)
- The original data in the spreadsheet remains unchanged
- All new email attachments will add their data to the same sheet

### Create Mode (when GOOGLE_SHEETS_SPREADSHEET_ID is empty)
- A new spreadsheet is created for each email processing cycle
- Each spreadsheet gets its own timestamp in the title
- Headers are included in each new spreadsheet

## Testing the Append Functionality

You can test the append functionality using the provided test script:

```bash
python test_append_functionality.py
```

This script will:
1. Create a test spreadsheet with sample data
2. Test appending additional data to it
3. Provide you with the Spreadsheet ID to use in your configuration

## Important Notes

1. **Permissions**: Make sure your Google API credentials have access to the target spreadsheet
2. **Sheet Name**: The system appends to "Sheet1" by default. Make sure this sheet exists in your target spreadsheet
3. **Data Structure**: The append function expects the same column structure as defined in the CSV processor
4. **Error Handling**: If appending fails, the system will fall back to creating CSV files

## Expected Data Structure

The system expects these columns in your target spreadsheet:
- LeadCreationDate
- InquiryDate  
- CommunityName
- Classification
- TotalLeads
- SubSourceName
- SourceName

Make sure your target spreadsheet has headers that match this structure.
