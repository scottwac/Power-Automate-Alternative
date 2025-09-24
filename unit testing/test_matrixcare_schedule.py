"""
Unit tests for MatrixCare Looker Dashboard automation scheduling.

This test verifies that the program correctly identifies target Tuesdays 
and processes emails at the right times.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_processor import EmailProcessor


class TestMatrixCareSchedule(unittest.TestCase):
    """Test the MatrixCare scheduling functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        with patch.dict(os.environ, {
            'GMAIL_CREDENTIALS_FILE': 'test_credentials.json',
            'GMAIL_TOKEN_FILE': 'test_token.json',
            'GMAIL_FROM_EMAIL': 'test@example.com',
            'GMAIL_SUBJECT_FILTER': 'MatrixCare Automation for Looker Dash',
            'GOOGLE_DRIVE_FOLDER_ID': '1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq',
            'GOOGLE_SHEETS_SPREADSHEET_ID': 'test_spreadsheet_id',
            'LOG_LEVEL': 'DEBUG'
        }):
            # Mock the service initializations
            with patch('email_processor.GmailService'), \
                 patch('email_processor.GoogleDriveService'), \
                 patch('email_processor.GoogleSheetsService'), \
                 patch('email_processor.CSVProcessor'):
                
                self.processor = EmailProcessor()
    
    def test_is_target_tuesday_correct_day(self):
        """Test that is_target_tuesday correctly identifies target Tuesdays."""
        # Mock the reference Tuesday (September 30, 2025) - this should be a target (week 0)
        target_tuesday = date(2025, 9, 30)
        
        with patch('email_processor.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.date.return_value = target_tuesday
            mock_datetime.now.return_value = mock_now
            
            result = self.processor.is_target_tuesday()
            self.assertTrue(result, "September 30, 2025 should be a target Tuesday (first target)")
    
    def test_is_target_tuesday_wrong_day(self):
        """Test that is_target_tuesday rejects non-Tuesdays."""
        # Mock a Wednesday
        wednesday = date(2025, 10, 9)
        
        with patch('email_processor.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.date.return_value = wednesday
            mock_datetime.now.return_value = mock_now
            
            result = self.processor.is_target_tuesday()
            self.assertFalse(result, "Wednesday should not be a target day")
    
    def test_is_target_tuesday_off_week(self):
        """Test that is_target_tuesday rejects off-week Tuesdays."""
        # Mock a Tuesday that should NOT be a target (odd week difference from reference)
        # Reference is 2025-09-30, so 2025-10-07 should NOT be a target (1 week later, odd)
        off_tuesday = date(2025, 10, 7)
        
        with patch('email_processor.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.date.return_value = off_tuesday
            mock_datetime.now.return_value = mock_now
            
            result = self.processor.is_target_tuesday()
            self.assertFalse(result, "October 7, 2025 should not be a target Tuesday (off week)")
    
    def test_is_target_tuesday_second_target(self):
        """Test that is_target_tuesday correctly identifies the second target Tuesday."""
        # Mock the second target Tuesday (October 14, 2025) - this should be a target (week 2)
        second_target = date(2025, 10, 14)
        
        with patch('email_processor.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.date.return_value = second_target
            mock_datetime.now.return_value = mock_now
            
            result = self.processor.is_target_tuesday()
            self.assertTrue(result, "October 14, 2025 should be a target Tuesday (second target)")
    
    def test_should_check_emails_at_1120(self):
        """Test that should_check_emails returns True at 11:20 AM on target Tuesday."""
        target_tuesday = date(2025, 9, 30)  # First target Tuesday
        target_time = datetime(2025, 9, 30, 11, 20, 0)  # 11:20 AM
        
        with patch('email_processor.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.date.return_value = target_tuesday
            mock_now.time.return_value = target_time.time()
            mock_datetime.now.return_value = mock_now
            
            result = self.processor.should_check_emails()
            self.assertTrue(result, "Should check emails at 11:20 AM on target Tuesday")
    
    def test_should_check_emails_at_1200(self):
        """Test that should_check_emails returns True at 12:00 PM on target Tuesday."""
        target_tuesday = date(2025, 9, 30)  # First target Tuesday
        target_time = datetime(2025, 9, 30, 12, 0, 0)  # 12:00 PM
        
        with patch('email_processor.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.date.return_value = target_tuesday
            mock_now.time.return_value = target_time.time()
            mock_datetime.now.return_value = mock_now
            
            result = self.processor.should_check_emails()
            self.assertTrue(result, "Should check emails at 12:00 PM on target Tuesday")
    
    def test_should_check_emails_wrong_time(self):
        """Test that should_check_emails returns False at wrong time."""
        target_tuesday = date(2025, 9, 30)  # First target Tuesday
        wrong_time = datetime(2025, 9, 30, 10, 30, 0)  # 10:30 AM
        
        with patch('email_processor.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.date.return_value = target_tuesday
            mock_now.time.return_value = wrong_time.time()
            mock_datetime.now.return_value = mock_now
            
            result = self.processor.should_check_emails()
            self.assertFalse(result, "Should not check emails at 10:30 AM")
    
    def test_process_emails_with_mock_schedule(self):
        """Test the full process_emails workflow with mocked schedule."""
        # Setup mocks
        mock_message = {
            'from': 'test@matrixcare.com',
            'subject': 'MatrixCare Automation for Looker Dash',
            'body': 'Test email content for Looker Dashboard'
        }
        
        # Mock the Gmail service to return a message
        self.processor.gmail_service.search_emails = Mock(return_value=['msg123'])
        self.processor.gmail_service.get_message_with_attachments = Mock(return_value=mock_message)
        
        # Mock the Sheets service
        self.processor.sheets_service.append_data_to_sheet = Mock(return_value=True)
        
        # Set target spreadsheet ID
        self.processor.target_spreadsheet_id = 'test_spreadsheet_id'
        
        # Mock the time to be the correct Tuesday at 11:20 AM
        target_tuesday = date(2025, 9, 30)
        target_time = datetime(2025, 9, 30, 11, 20, 0)
        
        with patch('email_processor.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.date.return_value = target_tuesday
            mock_now.time.return_value = target_time.time()
            mock_now.strftime.return_value = '2025-09-30 11:20:00'
            mock_datetime.now.return_value = mock_now
            
            # Run the process
            self.processor.process_emails()
            
            # Verify that Gmail was searched
            self.processor.gmail_service.search_emails.assert_called_once()
            
            # Verify that the message was retrieved
            self.processor.gmail_service.get_message_with_attachments.assert_called_once_with('msg123')
            
            # Verify that data was appended to the sheet
            self.processor.sheets_service.append_data_to_sheet.assert_called_once()
            
            # Check the call arguments to sheets service
            call_args = self.processor.sheets_service.append_data_to_sheet.call_args
            self.assertEqual(call_args[1]['spreadsheet_id'], 'test_spreadsheet_id')
            self.assertEqual(call_args[1]['sheet_name'], 'Sheet1')
            
            # Check that data contains expected values
            data = call_args[1]['data'][0]  # First row of data
            self.assertEqual(data[1], 'test@matrixcare.com')  # From email
            self.assertEqual(data[2], 'MatrixCare Automation for Looker Dash')  # Subject
            self.assertEqual(data[3], 'Test email content for Looker Dashboard')  # Content
            self.assertEqual(data[4], 'Processed')  # Status


class TestMatrixCareIntegration(unittest.TestCase):
    """Integration test that simulates the actual workflow."""
    
    def test_full_workflow_simulation(self):
        """Test the complete workflow by simulating it's the right time."""
        print("\n" + "="*60)
        print("INTEGRATION TEST: MatrixCare Looker Dashboard Automation")
        print("="*60)
        
        # Mock environment variables for the test
        test_env = {
            'GMAIL_CREDENTIALS_FILE': 'credentials.json',
            'GMAIL_TOKEN_FILE': 'token.json',
            'GMAIL_FROM_EMAIL': 'growatorchard@gmail.com',
            'GMAIL_SUBJECT_FILTER': 'MatrixCare Automation for Looker Dash',
            'GOOGLE_DRIVE_FOLDER_ID': '1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq',
            'GOOGLE_SHEETS_SPREADSHEET_ID': 'your_actual_spreadsheet_id_here',
            'LOG_LEVEL': 'INFO'
        }
        
        with patch.dict(os.environ, test_env):
            # Mock services to avoid actual API calls
            with patch('email_processor.GmailService') as MockGmail, \
                 patch('email_processor.GoogleDriveService') as MockDrive, \
                 patch('email_processor.GoogleSheetsService') as MockSheets, \
                 patch('email_processor.CSVProcessor') as MockCSV:
                
                # Setup service mocks
                mock_gmail = MockGmail.return_value
                mock_sheets = MockSheets.return_value
                
                # Mock email search results
                mock_gmail.search_emails.return_value = ['test_message_123']
                
                # Mock email message
                mock_message = {
                    'from': 'automation@matrixcare.com',
                    'subject': 'MatrixCare Automation for Looker Dash',
                    'body': 'Dashboard data for October 8, 2025\n\nKey metrics:\n- Total patients: 1,234\n- Active cases: 567\n- Completed assessments: 890'
                }
                mock_gmail.get_message_with_attachments.return_value = mock_message
                
                # Mock successful sheet append
                mock_sheets.append_data_to_sheet.return_value = True
                
                # Create processor
                processor = EmailProcessor()
                processor.target_spreadsheet_id = 'test_spreadsheet_id'
                
                # Mock the current time to be Tuesday, October 8, 2025 at 11:20 AM
                target_time = datetime(2025, 9, 30, 11, 20, 0)
                
                with patch('email_processor.datetime') as mock_dt:
                    mock_now = Mock()
                    mock_now.date.return_value = target_time.date()
                    mock_now.time.return_value = target_time.time()
                    mock_now.strftime.return_value = '2025-09-30 11:20:00'
                    mock_dt.now.return_value = mock_now
                    
                    print(f"🕐 Simulated time: {target_time}")
                    print(f"📅 Is target Tuesday: {processor.is_target_tuesday()}")
                    print(f"✅ Should check emails: {processor.should_check_emails()}")
                    
                    # Run the email processing
                    print("\n🔄 Running email processing...")
                    processor.process_emails()
                    
                    # Verify the workflow
                    print("\n📋 Verification Results:")
                    print(f"   Gmail search called: {mock_gmail.search_emails.called}")
                    print(f"   Message retrieved: {mock_gmail.get_message_with_attachments.called}")
                    print(f"   Sheet append called: {mock_sheets.append_data_to_sheet.called}")
                    
                    if mock_sheets.append_data_to_sheet.called:
                        call_args = mock_sheets.append_data_to_sheet.call_args
                        data_row = call_args[1]['data'][0]
                        print(f"   Data appended: {data_row}")
                    
                    print("\n✅ Test completed successfully!")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
