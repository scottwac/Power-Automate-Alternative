"""
Google Drive API service for file upload and management.
"""

import os
import pickle
import logging
from datetime import datetime
from typing import Optional
from io import BytesIO

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """Service class for Google Drive API operations."""
    
    def __init__(self, credentials_file: str, token_file: str = 'drive_token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API."""
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
        
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive service authenticated successfully")
    
    def upload_file(self, 
                   file_data: bytes, 
                   filename: str, 
                   mime_type: str = 'text/csv',
                   folder_id: Optional[str] = None) -> Optional[str]:
        """
        Upload file to Google Drive.
        
        Args:
            file_data: File content as bytes
            filename: Name for the uploaded file
            mime_type: MIME type of the file
            folder_id: Parent folder ID (None for root)
        
        Returns:
            File ID of uploaded file, or None if failed
        """
        try:
            # Create file metadata
            file_metadata = {'name': filename}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Create media upload object
            media = MediaIoBaseUpload(
                BytesIO(file_data),
                mimetype=mime_type,
                resumable=True
            )
            
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"File uploaded successfully: {filename} (ID: {file_id})")
            return file_id
            
        except HttpError as error:
            logger.error(f"Error uploading file {filename}: {error}")
            return None
    
    def get_file_content(self, file_id: str) -> Optional[bytes]:
        """
        Download file content from Google Drive.
        
        Args:
            file_id: Google Drive file ID
        
        Returns:
            File content as bytes, or None if failed
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = request.execute()
            
            logger.info(f"File content retrieved for ID: {file_id}")
            return file_content
            
        except HttpError as error:
            logger.error(f"Error downloading file {file_id}: {error}")
            return None
    
    def create_timestamped_filename(self, prefix: str, extension: str = 'csv') -> str:
        """
        Create a timestamped filename.
        
        Args:
            prefix: Filename prefix
            extension: File extension (without dot)
        
        Returns:
            Timestamped filename
        """
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        return f"{prefix}_{timestamp}.{extension}"
    
    def upload_csv_with_timestamp(self, 
                                 csv_data: bytes, 
                                 prefix: str = 'processed_data',
                                 folder_id: Optional[str] = None) -> Optional[str]:
        """
        Upload CSV file with automatic timestamp.
        
        Args:
            csv_data: CSV content as bytes
            prefix: Filename prefix
            folder_id: Parent folder ID
        
        Returns:
            File ID of uploaded file
        """
        filename = self.create_timestamped_filename(prefix)
        return self.upload_file(csv_data, filename, 'text/csv', folder_id)
