"""
MatrixCare Looker Dashboard automation email processing script.

This script:
1. Monitors Gmail for emails with subject "MatrixCare Automation for Looker Dash"
2. Processes the email content and appends data to a Google Sheet
3. Appends new data to the existing Google Sheet (doesn't replace)
4. Designed specifically for MatrixCare Looker Dashboard data automation

Note: This script runs the automation when executed. Schedule it externally
using Windows Task Scheduler, cron, or another scheduling tool.
"""

import os
import sys
import logging
import pytz
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

from gmail_service import GmailService
from google_drive_service import GoogleDriveService
from google_sheets_service import GoogleSheetsService
from csv_processor import CSVProcessor

# Load environment variables
load_dotenv()


class EmailProcessor:
    """Main class that orchestrates the email processing workflow."""
    
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.initialize_services()
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_file = os.getenv('LOG_FILE', 'email_processor.log')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Email processor initialized")
    
    def load_config(self):
        """Load configuration from environment variables."""
        self.gmail_credentials_file = os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json')
        self.gmail_token_file = os.getenv('GMAIL_TOKEN_FILE', 'token.json')
        self.gmail_from_email = os.getenv('GMAIL_FROM_EMAIL')
        self.gmail_subject_filter = os.getenv('GMAIL_SUBJECT_FILTER')
        self.gmail_label = os.getenv('GMAIL_LABEL', 'INBOX')
        
        self.drive_credentials_file = os.getenv('GOOGLE_DRIVE_CREDENTIALS_FILE', 'credentials.json')
        # Get folder ID, treat '/' or empty as None (root folder)
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.drive_folder_id = None if folder_id in ['/', '', None] else folder_id
        
        self.sheets_credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
        self.create_sheets = os.getenv('CREATE_GOOGLE_SHEETS', 'true').lower() == 'true'
        # Get target spreadsheet ID for appending data
        spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '').strip()
        self.target_spreadsheet_id = spreadsheet_id if spreadsheet_id else None
        
        self.check_interval_minutes = int(os.getenv('CHECK_INTERVAL_MINUTES', '5'))
        self.max_rows_to_process = int(os.getenv('MAX_ROWS_TO_PROCESS', '5000'))
        
        append_mode = "appending to existing spreadsheet" if self.target_spreadsheet_id else "creating new spreadsheets"
        self.logger.info(f"Configuration loaded - MatrixCare Looker Dash automation, {append_mode}")
    
    def initialize_services(self):
        """Initialize Gmail, Google Drive, and CSV processor services."""
        try:
            self.gmail_service = GmailService(
                self.gmail_credentials_file,
                self.gmail_token_file
            )
            
            self.drive_service = GoogleDriveService(
                self.drive_credentials_file,
                'drive_token.json'
            )
            
            self.sheets_service = GoogleSheetsService(
                self.sheets_credentials_file,
                'sheets_token.json'
            )
            
            self.csv_processor = CSVProcessor(self.max_rows_to_process)
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing services: {e}")
            raise
    
    def process_emails(self, find_recent=False):
        """
        Main processing function that processes emails.
        
        Args:
            find_recent: If True, find the most recent matching email regardless of date.
                        If False, only search for emails from today in EST.
        """
        try:
            if find_recent:
                self.logger.info("Starting email processing cycle - searching for most recent matching email")
            else:
                self.logger.info("Starting email processing cycle")
            
            # Search for emails
            if find_recent:
                # Search without time filter to find most recent email
                self.logger.info("Searching for most recent email matching criteria (no date restriction)")
                message_ids = self.gmail_service.search_emails(
                    from_email=None,  # Accept emails from any sender
                    subject=self.gmail_subject_filter,
                    label=self.gmail_label,
                    has_attachments=True,  # Look for emails WITH CSV attachments
                    since_minutes=None  # No time filter - find most recent
                )
            else:
                # Search for emails from today in EST
                est_tz = pytz.timezone('US/Eastern')
                est_now = datetime.now(est_tz)
                est_start_of_day = est_now.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Calculate minutes since start of EST day
                minutes_since_est_midnight = int((est_now - est_start_of_day).total_seconds() / 60)
                self.logger.info(f"Searching for emails from today in EST (last {minutes_since_est_midnight} minutes)")
                
                message_ids = self.gmail_service.search_emails(
                    from_email=None,  # Accept emails from any sender
                    subject=self.gmail_subject_filter,
                    label=self.gmail_label,
                    has_attachments=True,  # Look for emails WITH CSV attachments
                    since_minutes=minutes_since_est_midnight  # Look for emails from today in EST
                )
            
            if not message_ids:
                self.logger.info("No matching emails found")
                return
            
            if find_recent:
                # Only process the most recent email (first result)
                self.logger.info(f"Found {len(message_ids)} matching emails, processing most recent one")
                self.process_single_email(message_ids[0])
            else:
                self.logger.info(f"Found {len(message_ids)} emails to process")
                # Process each email
                for message_id in message_ids:
                    self.process_single_email(message_id)
            
            self.logger.info("Email processing cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in process_emails: {e}")
    
    def process_single_email(self, message_id: str):
        """
        Process a single email for MatrixCare Looker Dash automation.
        
        Args:
            message_id: Gmail message ID
        """
        try:
            self.logger.info(f"Processing email: {message_id}")
            
            # Get message (no need for attachments for MatrixCare Looker Dash)
            message = self.gmail_service.get_message_with_attachments(message_id)
            if not message:
                self.logger.warning(f"Could not retrieve message: {message_id}")
                return
            
            self.logger.info(f"Email from: {message['from']}, Subject: {message['subject']}")
            
            # Process the email content for MatrixCare Looker Dash
            self.process_matrixcare_email(message)
            
        except Exception as e:
            self.logger.error(f"Error processing email {message_id}: {e}")
    
    def process_matrixcare_email(self, message: Dict):
        """
        Process MatrixCare Looker Dash email with CSV attachments.
        
        Args:
            message: Message dictionary with attachments
        """
        try:
            self.logger.info("Processing MatrixCare Looker Dash email")
            
            email_subject = message.get('subject', '')
            email_from = message.get('from', '')
            attachments = message.get('attachments', [])
            
            if not attachments:
                self.logger.warning("No attachments found in MatrixCare email")
                return
            
            self.logger.info(f"Found {len(attachments)} attachments")
            
            # Process each CSV attachment
            csv_processed = False
            for attachment in attachments:
                filename = attachment.get('filename', '')
                if filename.lower().endswith('.csv'):
                    self.logger.info(f"Processing CSV attachment: {filename}")
                    self.process_csv_attachment(attachment, message)
                    csv_processed = True
                else:
                    self.logger.info(f"Skipping non-CSV attachment: {filename}")
            
            if not csv_processed:
                self.logger.warning("No CSV attachments found to process")
                
        except Exception as e:
            self.logger.error(f"Error processing MatrixCare email: {e}")
    
    def process_csv_attachment(self, attachment: Dict, message: Dict):
        """
        Process a single CSV attachment.
        
        Args:
            attachment: Attachment dictionary
            message: Message dictionary
        """
        try:
            filename = attachment['filename']
            self.logger.info(f"Processing CSV attachment: {filename}")
            
            # Download attachment data
            csv_data = self.gmail_service.download_attachment(attachment['data'])
            if not csv_data:
                self.logger.warning(f"Could not download attachment: {filename}")
                return
            
            # Step 1: Upload original CSV to Google Drive with timestamp
            temp_filename = self.csv_processor.generate_temp_filename(filename)
            temp_file_id = self.drive_service.upload_file(
                csv_data, 
                temp_filename, 
                'text/csv',
                self.drive_folder_id
            )
            
            if not temp_file_id:
                self.logger.error(f"Failed to upload temporary file: {temp_filename}")
                return
            
            self.logger.info(f"Uploaded temporary file: {temp_filename} (ID: {temp_file_id})")
            
            # Step 2: Process the CSV data
            processed_rows = self.csv_processor.process_csv_attachment(csv_data)
            
            if not processed_rows:
                self.logger.warning("No data to process from CSV")
                return
            
            # Step 3: Create Google Sheet with processed data
            if self.create_sheets:
                headers, data_rows = self.csv_processor.prepare_sheets_data(processed_rows)
                
                if self.target_spreadsheet_id:
                    # Append to existing spreadsheet without duplicates (check Lead ID only)
                    success = self.sheets_service.append_data_without_duplicates(
                        spreadsheet_id=self.target_spreadsheet_id,
                        data=data_rows,
                        sheet_name='Sheet1',
                        unique_columns=[7]  # Use Lead ID column (index 7) for uniqueness check
                    )
                    
                    if success:
                        self.logger.info(f"Successfully appended {len(processed_rows)} rows to existing spreadsheet")
                        self.logger.info(f"Spreadsheet ID: {self.target_spreadsheet_id}")
                        self.logger.info(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{self.target_spreadsheet_id}/edit")
                    else:
                        self.logger.error("Failed to append data to existing spreadsheet")
                        # Fallback to CSV upload
                        self._upload_csv_fallback(processed_rows)
                else:
                    # Create new spreadsheet (original behavior)
                    sheet_title = self.csv_processor.generate_sheet_title()
                    
                    sheet_info = self.sheets_service.create_and_populate_spreadsheet(
                        title=sheet_title,
                        headers=headers,
                        data=data_rows,
                        folder_id=self.drive_folder_id
                    )
                    
                    if sheet_info:
                        self.logger.info(f"Successfully created Google Sheet: {sheet_title}")
                        self.logger.info(f"Sheet URL: {sheet_info['url']}")
                        self.logger.info(f"Sheet ID: {sheet_info['id']}")
                        self.logger.info(f"Processed {len(processed_rows)} rows of lead data")
                    else:
                        self.logger.error("Failed to create Google Sheet")
                        # Fallback to CSV upload
                        self._upload_csv_fallback(processed_rows)
            else:
                # Create CSV file if sheets are disabled
                self._upload_csv_fallback(processed_rows)
                
        except Exception as e:
            self.logger.error(f"Error processing CSV attachment {attachment['filename']}: {e}")
    
    def _upload_csv_fallback(self, processed_rows: List[Dict]):
        """
        Fallback method to upload as CSV if Google Sheets creation fails.
        
        Args:
            processed_rows: Processed data rows
        """
        try:
            self.logger.info("Creating CSV file as fallback...")
            
            # Step 3: Create output CSV
            output_csv_data = self.csv_processor.create_output_csv(processed_rows)
            
            if not output_csv_data:
                self.logger.error("Failed to create output CSV")
                return
            
            # Step 4: Upload processed CSV to Google Drive
            output_filename = self.csv_processor.generate_output_filename()
            output_file_id = self.drive_service.upload_file(
                output_csv_data,
                output_filename,
                'text/csv',
                self.drive_folder_id
            )
            
            if output_file_id:
                self.logger.info(f"Successfully processed and uploaded CSV: {output_filename} (ID: {output_file_id})")
                self.logger.info(f"Processed {len(processed_rows)} rows of lead data")
            else:
                self.logger.error(f"Failed to upload processed file: {output_filename}")
                
        except Exception as e:
            self.logger.error(f"Error in CSV fallback: {e}")
    
    def manual_email_check(self):
        """Check for emails from the last 7 days (broader search than default today-only check)."""
        try:
            self.logger.info("Starting manual email check (searching last 7 days)")
            
            # Search for emails - look for emails from any sender in the last 7 days
            message_ids = self.gmail_service.search_emails(
                from_email=None,  # Accept emails from any sender
                subject=self.gmail_subject_filter,
                label=self.gmail_label,
                has_attachments=False,
                since_minutes=7 * 24 * 60  # Look for emails from last 7 days
            )
            
            if not message_ids:
                self.logger.info("No emails found with subject: " + self.gmail_subject_filter)
                return
            
            self.logger.info(f"Found {len(message_ids)} emails to process")
            
            # Process each email
            for message_id in message_ids:
                self.process_single_email(message_id)
            
            self.logger.info("Manual email check completed")
            
        except Exception as e:
            self.logger.error(f"Error in manual email check: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MatrixCare Looker Dashboard Automation')
    parser.add_argument('--test-auth', action='store_true', help='Test authentication only')
    parser.add_argument('--manual-check', action='store_true', help='Check for emails from last 7 days (bypasses today-only filter)')
    parser.add_argument('--recent', action='store_true', help='Find and process the most recent matching email (no date restriction)')
    
    args = parser.parse_args()
    
    try:
        processor = EmailProcessor()
        
        if args.test_auth:
            print("✅ Authentication successful for Gmail, Google Drive, and Google Sheets")
            return
        
        if args.manual_check:
            processor.manual_email_check()
        elif args.recent:
            # Find and process the most recent matching email
            processor.process_emails(find_recent=True)
        else:
            # Default behavior: run the automation once (today's emails only)
            processor.process_emails()
            
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
