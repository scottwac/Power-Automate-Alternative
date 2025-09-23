"""
Quick test script to verify your credentials are working.
"""

import os
from gmail_service import GmailService
from google_drive_service import GoogleDriveService

def test_credentials():
    """Test if credentials work for both services."""
    try:
        print("🔍 Testing Gmail API...")
        gmail = GmailService('credentials.json', 'token.json')
        print("✅ Gmail API authentication successful!")
        
        print("\n🔍 Testing Google Drive API...")
        drive = GoogleDriveService('credentials.json', 'drive_token.json')
        print("✅ Google Drive API authentication successful!")
        
        print("\n🎉 All credentials are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_credentials()
