"""
Debug script to help troubleshoot Gmail search issues.
"""

import os
from dotenv import load_dotenv
from gmail_service import GmailService

load_dotenv()

def debug_gmail_search():
    """Test different search queries to find the email."""
    
    gmail_service = GmailService(
        os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json'),
        os.getenv('GMAIL_TOKEN_FILE', 'token.json')
    )
    
    from_email = os.getenv('GMAIL_FROM_EMAIL', 'growatorchard@gmail.com')
    
    print("🔍 Debugging Gmail search...")
    print(f"Looking for emails from: {from_email}")
    print("-" * 50)
    
    # Test 1: Search for any emails from the sender (no subject filter)
    print("1. Searching for ANY emails from sender...")
    try:
        result = gmail_service.service.users().messages().list(
            userId='me',
            q=f'from:{from_email}'
        ).execute()
        messages = result.get('messages', [])
        print(f"   Found {len(messages)} total emails from {from_email}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Search with subject TEST
    print("\n2. Searching for emails with subject 'TEST'...")
    try:
        result = gmail_service.service.users().messages().list(
            userId='me',
            q=f'from:{from_email} subject:TEST'
        ).execute()
        messages = result.get('messages', [])
        print(f"   Found {len(messages)} emails with subject 'TEST'")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Search with subject test (lowercase)
    print("\n3. Searching for emails with subject 'test' (lowercase)...")
    try:
        result = gmail_service.service.users().messages().list(
            userId='me',
            q=f'from:{from_email} subject:test'
        ).execute()
        messages = result.get('messages', [])
        print(f"   Found {len(messages)} emails with subject 'test'")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Search with attachments
    print("\n4. Searching for emails with attachments...")
    try:
        result = gmail_service.service.users().messages().list(
            userId='me',
            q=f'from:{from_email} has:attachment'
        ).execute()
        messages = result.get('messages', [])
        print(f"   Found {len(messages)} emails with attachments")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: ALL emails in the last hour (from any sender)
    print("\n5. Searching for ALL emails in the last hour...")
    try:
        from datetime import datetime, timedelta
        one_hour_ago = datetime.now() - timedelta(hours=1)
        timestamp = int(one_hour_ago.timestamp())
        
        result = gmail_service.service.users().messages().list(
            userId='me',
            q=f'after:{timestamp}',
            maxResults=50  # Get up to 50 emails
        ).execute()
        messages = result.get('messages', [])
        print(f"   Found {len(messages)} emails in the last hour")
        
        # If we found messages, let's get details on ALL of them
        if messages:
            print("\n📧 ALL emails from the last hour:")
            for i, msg in enumerate(messages):  # Show ALL messages
                try:
                    message = gmail_service.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata'
                    ).execute()
                    
                    headers = message['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    from_addr = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                    
                    # Check for attachments more thoroughly
                    has_attachments = False
                    payload = message['payload']
                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part.get('filename'):
                                has_attachments = True
                                break
                    
                    print(f"   📧 Email {i+1}:")
                    print(f"      From: {from_addr}")
                    print(f"      Subject: '{subject}'")
                    print(f"      Date: {date}")
                    print(f"      Has attachments: {has_attachments}")
                    print(f"      Message ID: {msg['id']}")
                    print()
                    
                except Exception as e:
                    print(f"   Error getting email {i+1}: {e}")
                    
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    debug_gmail_search()
