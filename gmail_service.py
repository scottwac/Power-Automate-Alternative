"""
Gmail API service for monitoring and processing emails with attachments.
"""

import os
import base64
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

logger = logging.getLogger(__name__)


class GmailService:
    """Service class for Gmail API operations."""
    
    def __init__(self, credentials_file: str, token_file: str):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials are invalid or don't exist, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service authenticated successfully")
    
    def search_emails(self, 
                     from_email: str = None, 
                     subject: str = None, 
                     label: str = 'INBOX',
                     has_attachments: bool = True,
                     since_minutes: int = 5) -> List[str]:
        """
        Search for emails matching criteria.
        
        Args:
            from_email: Email address to filter by (optional - if None, searches all senders)
            subject: Subject line to filter by (optional)
            label: Gmail label to search in
            has_attachments: Whether to filter for emails with attachments
            since_minutes: Look for emails from this many minutes ago
        
        Returns:
            List of message IDs
        """
        try:
            # Build search query
            query_parts = [
                f'label:{label}'
            ]
            
            if from_email:
                query_parts.append(f'from:{from_email}')
            
            if subject:
                query_parts.append(f'subject:{subject}')
            
            if has_attachments:
                query_parts.append('has:attachment')
            
            # Add time filter (last X minutes) if specified
            if since_minutes is not None:
                since_time = datetime.now() - timedelta(minutes=since_minutes)
                query_parts.append(f'after:{int(since_time.timestamp())}')
            
            query = ' '.join(query_parts)
            logger.info(f"Searching emails with query: {query}")
            
            # Execute search
            result = self.service.users().messages().list(
                userId='me',
                q=query
            ).execute()
            
            messages = result.get('messages', [])
            message_ids = [msg['id'] for msg in messages]
            
            logger.info(f"Found {len(message_ids)} matching emails")
            return message_ids
            
        except HttpError as error:
            logger.error(f"Error searching emails: {error}")
            return []
    
    def get_message_with_attachments(self, message_id: str) -> Optional[Dict]:
        """
        Get message details including attachments.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Dictionary with message details and attachments
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            attachments = []
            
            def extract_attachments(parts):
                """Recursively extract attachments from message parts."""
                if not parts:
                    return
                
                for part in parts:
                    if part.get('filename'):
                        attachment_id = part['body'].get('attachmentId')
                        if attachment_id:
                            attachment = self.service.users().messages().attachments().get(
                                userId='me',
                                messageId=message_id,
                                id=attachment_id
                            ).execute()
                            
                            attachments.append({
                                'filename': part['filename'],
                                'mimeType': part['mimeType'],
                                'data': attachment['data']
                            })
                    
                    # Check nested parts
                    if 'parts' in part:
                        extract_attachments(part['parts'])
            
            # Extract attachments from message payload
            payload = message.get('payload', {})
            if 'parts' in payload:
                extract_attachments(payload['parts'])
            
            return {
                'id': message_id,
                'subject': next((h['value'] for h in message['payload']['headers'] 
                               if h['name'] == 'Subject'), ''),
                'from': next((h['value'] for h in message['payload']['headers'] 
                             if h['name'] == 'From'), ''),
                'date': next((h['value'] for h in message['payload']['headers'] 
                             if h['name'] == 'Date'), ''),
                'attachments': attachments
            }
            
        except HttpError as error:
            logger.error(f"Error getting message {message_id}: {error}")
            return None
    
    def download_attachment(self, attachment_data: str) -> bytes:
        """
        Decode and return attachment data.
        
        Args:
            attachment_data: Base64 encoded attachment data
        
        Returns:
            Decoded attachment bytes
        """
        try:
            # Gmail API returns URL-safe base64 encoding
            return base64.urlsafe_b64decode(attachment_data)
        except Exception as error:
            logger.error(f"Error decoding attachment: {error}")
            return b''
