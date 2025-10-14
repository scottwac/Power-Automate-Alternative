#!/usr/bin/env python3
"""
Manual OAuth authentication script for headless servers.
This script generates the OAuth tokens without requiring a browser.
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Define scopes for each service
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
DRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]
SHEETS_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def authenticate_service(service_name, scopes, token_file, credentials_file='credentials.json'):
    """Authenticate a Google service and save the token."""
    print(f"\n🔐 Authenticating {service_name}...")
    print("=" * 50)
    
    creds = None
    
    # Check if token already exists and is valid
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
        
        if creds and creds.valid:
            print(f"✅ {service_name} already authenticated!")
            return True
    
    # If credentials are invalid or don't exist, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print(f"✅ {service_name} token refreshed!")
            except Exception as e:
                print(f"❌ Failed to refresh token: {e}")
                creds = None
        
        if not creds:
            # Use console-based OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            
            print(f"\n📋 Manual authentication required for {service_name}")
            print("Follow these steps:")
            print("1. Copy the URL below and open it in a web browser")
            print("2. Sign in to your Google account")
            print("3. Grant the requested permissions")
            print("4. Copy the authorization code from the browser")
            print("5. Paste it back here when prompted")
            print("\n" + "="*50)
            
            # Get the authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f"🔗 Authorization URL:")
            print(auth_url)
            print("\n" + "="*50)
            
            # Get the authorization code from user
            auth_code = input("📝 Enter the authorization code: ").strip()
            
            try:
                # Exchange the code for credentials
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
                print(f"✅ {service_name} authenticated successfully!")
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                return False
        
        # Save credentials for future use
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        print(f"💾 {service_name} token saved to {token_file}")
    
    return True

def main():
    """Main authentication function."""
    print("🚀 Manual Google API Authentication")
    print("=" * 50)
    print("This script will authenticate with Google APIs without requiring a browser on the server.")
    print("You'll need to copy URLs to a web browser and paste back authorization codes.")
    print("\nMake sure you have 'credentials.json' in the current directory.")
    
    if not os.path.exists('credentials.json'):
        print("\n❌ Error: credentials.json not found!")
        print("Please download your Google API credentials and save them as 'credentials.json'")
        return False
    
    print("\n✅ Found credentials.json")
    
    # Authenticate each service
    services = [
        ("Gmail", GMAIL_SCOPES, "token.json"),
        ("Google Drive", DRIVE_SCOPES, "drive_token.json"),
        ("Google Sheets", SHEETS_SCOPES, "sheets_token.json")
    ]
    
    success_count = 0
    for service_name, scopes, token_file in services:
        if authenticate_service(service_name, scopes, token_file):
            success_count += 1
        else:
            print(f"❌ Failed to authenticate {service_name}")
    
    print(f"\n🎉 Authentication Summary")
    print("=" * 50)
    print(f"✅ Successfully authenticated: {success_count}/3 services")
    
    if success_count == 3:
        print("🎯 All services authenticated! You can now run:")
        print("   python email_processor.py --test-auth")
        print("   python email_processor.py --check-in-2min")
        return True
    else:
        print("❌ Some services failed to authenticate. Please try again.")
        return False

if __name__ == "__main__":
    main()
