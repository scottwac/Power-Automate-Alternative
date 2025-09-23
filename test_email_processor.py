"""
Unit tests for the email processor components.
"""

import unittest
import os
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
import tempfile

# Import our modules
from gmail_service import GmailService
from google_drive_service import GoogleDriveService
from csv_processor import CSVProcessor
from email_processor import EmailProcessor


class TestGmailService(unittest.TestCase):
    """Test cases for Gmail service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_credentials_file = 'test_credentials.json'
        self.mock_token_file = 'test_token.json'
    
    @patch('gmail_service.build')
    @patch('gmail_service.pickle.load')
    @patch('gmail_service.os.path.exists')
    @patch('builtins.open', create=True)
    def test_authenticate_success(self, mock_open, mock_exists, mock_pickle_load, mock_build):
        """Test successful Gmail authentication."""
        # Mock existing token
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle_load.return_value = mock_creds
        
        # Mock Gmail service
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        gmail_service = GmailService(self.mock_credentials_file, self.mock_token_file)
        
        self.assertEqual(gmail_service.service, mock_service)
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
    
    @patch('gmail_service.build')
    @patch('gmail_service.pickle.load')
    @patch('gmail_service.os.path.exists')
    @patch('builtins.open', create=True)
    def test_search_emails(self, mock_open, mock_exists, mock_pickle_load, mock_build):
        """Test email search functionality."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle_load.return_value = mock_creds
        
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Mock search response
        mock_response = {
            'messages': [
                {'id': 'msg1'},
                {'id': 'msg2'}
            ]
        }
        mock_service.users().messages().list().execute.return_value = mock_response
        
        gmail_service = GmailService(self.mock_credentials_file, self.mock_token_file)
        result = gmail_service.search_emails(
            from_email='test@example.com',
            subject='Test',
            since_minutes=5
        )
        
        self.assertEqual(result, ['msg1', 'msg2'])
    
    def test_download_attachment(self):
        """Test attachment download functionality."""
        gmail_service = GmailService.__new__(GmailService)  # Create without __init__
        
        # Test data
        test_data = b"test,csv,data"
        encoded_data = base64.urlsafe_b64encode(test_data).decode()
        
        result = gmail_service.download_attachment(encoded_data)
        self.assertEqual(result, test_data)


class TestGoogleDriveService(unittest.TestCase):
    """Test cases for Google Drive service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_credentials_file = 'test_credentials.json'
        self.mock_token_file = 'test_drive_token.json'
    
    @patch('google_drive_service.build')
    @patch('google_drive_service.pickle.load')
    @patch('google_drive_service.os.path.exists')
    @patch('builtins.open', create=True)
    def test_upload_file_success(self, mock_open, mock_exists, mock_pickle_load, mock_build):
        """Test successful file upload."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle_load.return_value = mock_creds
        
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Mock upload response
        mock_response = {'id': 'file123'}
        mock_service.files().create().execute.return_value = mock_response
        
        drive_service = GoogleDriveService(self.mock_credentials_file, self.mock_token_file)
        
        test_data = b"test csv content"
        result = drive_service.upload_file(test_data, 'test.csv')
        
        self.assertEqual(result, 'file123')
    
    def test_create_timestamped_filename(self):
        """Test timestamped filename creation."""
        drive_service = GoogleDriveService.__new__(GoogleDriveService)  # Create without __init__
        
        filename = drive_service.create_timestamped_filename('test_file', 'csv')
        
        # Check format: test_file_YYYY-MM-DD_HH-MM-SS.csv
        self.assertTrue(filename.startswith('test_file_'))
        self.assertTrue(filename.endswith('.csv'))
        self.assertEqual(len(filename), len('test_file_2023-12-25_14-30-45.csv'))


class TestCSVProcessor(unittest.TestCase):
    """Test cases for CSV processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = CSVProcessor(max_rows=100)
    
    def test_process_csv_attachment(self):
        """Test CSV processing functionality."""
        # Create test CSV data
        test_csv = """LeadCreationDate,InquiryDate,CommunityName,Classification,TotalLeads,SubSourceName,SourceName
2023-12-01,2023-12-01,Test Community,Hot Lead,1,Online,Website
2023-12-02,2023-12-02,Another Community,Warm Lead,2,Referral,Agent"""
        
        csv_data = test_csv.encode('utf-8')
        result = self.processor.process_csv_attachment(csv_data)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['LeadCreationDate'], '2023-12-01')
        self.assertEqual(result[0]['CommunityName'], 'Test Community')
        self.assertEqual(result[1]['TotalLeads'], '2')
    
    def test_process_csv_row(self):
        """Test individual row processing."""
        test_row = '"2023-12-01","2023-12-01","Test Community","Hot Lead","1","Online","Website"'
        
        result = self.processor._process_csv_row(test_row)
        
        expected = {
            'LeadCreationDate': '2023-12-01',
            'InquiryDate': '2023-12-01',
            'CommunityName': 'Test Community',
            'Classification': 'Hot Lead',
            'TotalLeads': '1',
            'SubSourceName': 'Online',
            'SourceName': 'Website'
        }
        
        self.assertEqual(result, expected)
    
    def test_create_output_csv(self):
        """Test output CSV creation."""
        test_data = [
            {
                'LeadCreationDate': '2023-12-01',
                'InquiryDate': '2023-12-01',
                'CommunityName': 'Test Community',
                'Classification': 'Hot Lead',
                'TotalLeads': '1',
                'SubSourceName': 'Online',
                'SourceName': 'Website'
            }
        ]
        
        result = self.processor.create_output_csv(test_data)
        
        # Decode and check content
        csv_content = result.decode('utf-8')
        self.assertIn('LeadCreationDate', csv_content)
        self.assertIn('Test Community', csv_content)
        self.assertIn('Hot Lead', csv_content)
    
    def test_generate_filenames(self):
        """Test filename generation."""
        temp_filename = self.processor.generate_temp_filename('original.csv')
        output_filename = self.processor.generate_output_filename()
        
        self.assertTrue(temp_filename.startswith('New Leads - Daily TMP'))
        self.assertTrue(temp_filename.endswith('.csv'))
        
        self.assertTrue(output_filename.startswith('Lead_Data_'))
        self.assertTrue(output_filename.endswith('.csv'))


class TestEmailProcessor(unittest.TestCase):
    """Test cases for main email processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary environment variables
        self.env_vars = {
            'GMAIL_CREDENTIALS_FILE': 'test_credentials.json',
            'GMAIL_TOKEN_FILE': 'test_token.json',
            'GMAIL_FROM_EMAIL': 'test@example.com',
            'GMAIL_SUBJECT_FILTER': 'Test',
            'GMAIL_LABEL': 'INBOX',
            'GOOGLE_DRIVE_CREDENTIALS_FILE': 'test_credentials.json',
            'CHECK_INTERVAL_MINUTES': '5',
            'MAX_ROWS_TO_PROCESS': '100',
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'test.log'
        }
    
    @patch.dict(os.environ, {})
    @patch('email_processor.GmailService')
    @patch('email_processor.GoogleDriveService')
    @patch('email_processor.CSVProcessor')
    def test_email_processor_initialization(self, mock_csv, mock_drive, mock_gmail):
        """Test email processor initialization."""
        # Set environment variables
        for key, value in self.env_vars.items():
            os.environ[key] = value
        
        processor = EmailProcessor()
        
        # Verify services were initialized
        mock_gmail.assert_called_once()
        mock_drive.assert_called_once()
        mock_csv.assert_called_once()
    
    @patch.dict(os.environ, {})
    @patch('email_processor.GmailService')
    @patch('email_processor.GoogleDriveService')
    @patch('email_processor.CSVProcessor')
    def test_process_emails_no_messages(self, mock_csv, mock_drive, mock_gmail):
        """Test processing when no emails are found."""
        # Set environment variables
        for key, value in self.env_vars.items():
            os.environ[key] = value
        
        # Mock Gmail service to return no messages
        mock_gmail_instance = Mock()
        mock_gmail_instance.search_emails.return_value = []
        mock_gmail.return_value = mock_gmail_instance
        
        processor = EmailProcessor()
        processor.process_emails()
        
        # Verify search was called but no processing occurred
        mock_gmail_instance.search_emails.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    def test_end_to_end_csv_processing(self):
        """Test complete CSV processing workflow."""
        # Create test CSV data
        test_csv = """LeadCreationDate,InquiryDate,CommunityName,Classification,TotalLeads,SubSourceName,SourceName
2023-12-01,2023-12-01,Test Community,Hot Lead,1,Online,Website
2023-12-02,2023-12-02,Another Community,Warm Lead,2,Referral,Agent"""
        
        processor = CSVProcessor()
        
        # Process the CSV
        csv_data = test_csv.encode('utf-8')
        processed_rows = processor.process_csv_attachment(csv_data)
        
        # Create output CSV
        output_csv = processor.create_output_csv(processed_rows)
        
        # Verify the complete workflow
        self.assertEqual(len(processed_rows), 2)
        self.assertGreater(len(output_csv), 0)
        
        # Verify output contains expected data
        output_text = output_csv.decode('utf-8')
        self.assertIn('LeadCreationDate', output_text)
        self.assertIn('Test Community', output_text)


def create_test_credentials():
    """Create mock credentials file for testing."""
    mock_credentials = {
        "installed": {
            "client_id": "test_client_id",
            "project_id": "test_project",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_secret": "test_secret",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open('test_credentials.json', 'w') as f:
        json.dump(mock_credentials, f)


def cleanup_test_files():
    """Clean up test files."""
    test_files = [
        'test_credentials.json',
        'test_token.json',
        'test_drive_token.json',
        'test.log'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


if __name__ == '__main__':
    # Create test credentials
    create_test_credentials()
    
    try:
        # Run tests
        unittest.main(verbosity=2)
    finally:
        # Clean up
        cleanup_test_files()
