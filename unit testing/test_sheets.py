#!/usr/bin/env python3
"""
Test script for Google Sheets functionality.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from google_sheets_service import GoogleSheetsService

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_sheets_service():
    """Test Google Sheets service functionality."""
    
    print("🧪 Testing Google Sheets Service")
    print("================================")
    
    try:
        # Initialize service
        credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
        if folder_id in ['/', '', None]:
            folder_id = None
        
        print(f"📁 Using folder ID: {folder_id or 'Root folder'}")
        
        sheets_service = GoogleSheetsService(credentials_file)
        print("✅ Google Sheets service authenticated successfully")
        
        # Test data
        headers = ['LeadCreationDate', 'InquiryDate', 'CommunityName', 'Classification', 'TotalLeads', 'SubSourceName', 'SourceName']
        test_data = [
            ['2024-01-15', '2024-01-15', 'Sample Community', 'Hot Lead', '1', 'Website', 'Google Ads'],
            ['2024-01-16', '2024-01-16', 'Another Community', 'Warm Lead', '1', 'Email', 'Facebook'],
            ['2024-01-17', '2024-01-17', 'Test Community', 'Cold Lead', '1', 'Phone', 'Referral']
        ]
        
        print(f"📊 Test data: {len(test_data)} rows with {len(headers)} columns")
        
        # Create and populate spreadsheet
        title = "Test Lead Data - Google Sheets Integration"
        
        print(f"📝 Creating spreadsheet: {title}")
        sheet_info = sheets_service.create_and_populate_spreadsheet(
            title=title,
            headers=headers,
            data=test_data,
            folder_id=folder_id
        )
        
        if sheet_info:
            print("✅ Test completed successfully!")
            print(f"📋 Sheet Title: {sheet_info['title']}")
            print(f"🆔 Sheet ID: {sheet_info['id']}")
            print(f"🔗 Sheet URL: {sheet_info['url']}")
            print("")
            print("🎉 You can now view your test spreadsheet in Google Drive!")
            print("   The sheet should have:")
            print("   - Formatted header row (blue background, white text, bold)")
            print("   - Auto-resized columns")
            print("   - 3 rows of test lead data")
            return True
        else:
            print("❌ Failed to create test spreadsheet")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def main():
    """Main test function."""
    
    # Check if credentials exist
    credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file not found: {credentials_file}")
        print("Please ensure your Google API credentials are in place.")
        sys.exit(1)
    
    success = test_sheets_service()
    
    if success:
        print("\n🎊 All tests passed! Google Sheets integration is working correctly.")
    else:
        print("\n💥 Tests failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
