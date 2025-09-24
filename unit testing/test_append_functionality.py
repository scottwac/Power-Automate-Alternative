#!/usr/bin/env python3
"""
Test script to verify the append functionality works correctly.
This script creates a test spreadsheet and tests appending data to it.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from google_sheets_service import GoogleSheetsService

def test_append_functionality():
    """Test the append functionality with a sample spreadsheet."""
    
    print("🧪 Testing Google Sheets append functionality...")
    
    try:
        # Initialize the sheets service
        sheets_service = GoogleSheetsService('credentials.json', 'sheets_token.json')
        print("✅ Google Sheets service initialized")
        
        # Create a test spreadsheet
        test_title = f"Test Append Functionality - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        headers = ['LeadCreationDate', 'InquiryDate', 'CommunityName', 'Classification', 'TotalLeads', 'SubSourceName', 'SourceName']
        initial_data = [
            ['2024-01-01', '2024-01-01', 'Test Community 1', 'Hot', '5', 'Web', 'Google'],
            ['2024-01-02', '2024-01-02', 'Test Community 2', 'Warm', '3', 'Email', 'Newsletter']
        ]
        
        print("📊 Creating test spreadsheet...")
        sheet_info = sheets_service.create_and_populate_spreadsheet(
            title=test_title,
            headers=headers,
            data=initial_data
        )
        
        if not sheet_info:
            print("❌ Failed to create test spreadsheet")
            return False
        
        print(f"✅ Created test spreadsheet: {sheet_info['id']}")
        print(f"📝 URL: {sheet_info['url']}")
        
        # Test appending data
        print("\n📝 Testing append functionality...")
        append_data = [
            ['2024-01-03', '2024-01-03', 'Test Community 3', 'Cold', '2', 'Social', 'Facebook'],
            ['2024-01-04', '2024-01-04', 'Test Community 4', 'Hot', '8', 'Referral', 'Word of mouth']
        ]
        
        success = sheets_service.append_data_to_sheet(
            spreadsheet_id=sheet_info['id'],
            data=append_data,
            sheet_name='Sheet1'
        )
        
        if success:
            print("✅ Successfully appended data to spreadsheet")
            print(f"🎉 Test completed! Check the spreadsheet: {sheet_info['url']}")
            print(f"\n💡 To use append mode in the email processor, set this in your .env file:")
            print(f"GOOGLE_SHEETS_SPREADSHEET_ID={sheet_info['id']}")
            return True
        else:
            print("❌ Failed to append data to spreadsheet")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def main():
    """Main entry point."""
    print("🚀 Starting append functionality test...")
    
    # Check if credentials exist
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found. Please ensure Google API credentials are set up.")
        sys.exit(1)
    
    success = test_append_functionality()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
