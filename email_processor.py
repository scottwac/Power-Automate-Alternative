"""
MatrixCare Looker Dashboard automation email processing script.

This script:
1. Monitors Gmail for emails with subject "MatrixCare Automation for Looker Dash"
2. Processes the email content and appends data to a Google Sheet
3. Runs on a schedule every other Tuesday at 11:20 AM and 12:00 PM
4. Appends new data to the existing Google Sheet (doesn't replace)
5. Designed specifically for MatrixCare Looker Dashboard data automation
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
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
        self.gmail_from_email = os.getenv('GMAIL_FROM_EMAIL', 'growatorchard@gmail.com')
        self.gmail_subject_filter = os.getenv('GMAIL_SUBJECT_FILTER', 'MatrixCare Automation for Looker Dash')
        self.gmail_label = os.getenv('GMAIL_LABEL', 'INBOX')
        
        self.drive_credentials_file = os.getenv('GOOGLE_DRIVE_CREDENTIALS_FILE', 'credentials.json')
        # Get folder ID, treat '/' or empty as None (root folder)
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1xrzn2LZ-URdb1nx_7MspHyytq6LVk1iq')
        self.drive_folder_id = None if folder_id in ['/', '', None] else folder_id
        
        self.sheets_credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
        self.create_sheets = os.getenv('CREATE_GOOGLE_SHEETS', 'true').lower() == 'true'
        # Get target spreadsheet ID for appending data
        spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '').strip()
        self.target_spreadsheet_id = spreadsheet_id if spreadsheet_id else None
        
        self.check_interval_minutes = int(os.getenv('CHECK_INTERVAL_MINUTES', '5'))
        self.max_rows_to_process = int(os.getenv('MAX_ROWS_TO_PROCESS', '5000'))
        
        # Store reference date for "every other Tuesday" calculation (first Tuesday we want to run)
        # You can adjust this date to match your desired schedule
        self.reference_tuesday = datetime(2025, 9, 30)  # A Tuesday to start from
        
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
    
    def is_target_tuesday(self) -> bool:
        """
        Check if today is one of the target Tuesdays (every other Tuesday).
        
        Returns:
            True if today is a target Tuesday, False otherwise
        """
        today = datetime.now().date()
        
        # Check if today is a Tuesday (weekday 1)
        if today.weekday() != 1:
            return False
        
        # Calculate weeks difference from reference Tuesday
        ref_date = self.reference_tuesday.date()
        days_diff = (today - ref_date).days
        weeks_diff = days_diff // 7
        
        # Return True if the week difference is even (every other Tuesday)
        return weeks_diff % 2 == 0
    
    def should_check_emails(self) -> bool:
        """
        Check if we should check emails based on the schedule.
        
        Returns:
            True if we should check emails, False otherwise
        """
        if not self.is_target_tuesday():
            self.logger.info("Today is not a target Tuesday, skipping email check")
            return False
        
        now = datetime.now()
        current_time = now.time()
        
        # Check if it's 11:20 AM or 12:00 PM
        if current_time.hour == 11 and current_time.minute == 20:
            self.logger.info("First check time (11:20 AM) - checking for emails")
            return True
        elif current_time.hour == 12 and current_time.minute == 0:
            self.logger.info("Second check time (12:00 PM) - checking for emails")
            return True
        
        return False
    
    def process_emails(self):
        """Main processing function that runs on schedule."""
        try:
            # Check if we should process emails based on schedule
            if not self.should_check_emails():
                return
            
            self.logger.info("Starting email processing cycle")
            
            # Search for new emails - look for emails from any time (not just recent)
            message_ids = self.gmail_service.search_emails(
                from_email=self.gmail_from_email,
                subject=self.gmail_subject_filter,
                label=self.gmail_label,
                has_attachments=False,  # Changed to False since we're looking for SET files, not CSV attachments
                since_minutes=None  # Look for any emails with this subject
            )
            
            if not message_ids:
                self.logger.info("No new emails found")
                return
            
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
        Process MatrixCare Looker Dash email and append data to Google Sheet.
        
        Args:
            message: Message dictionary
        """
        try:
            self.logger.info("Processing MatrixCare Looker Dash email")
            
            # Get email content
            email_content = message.get('body', '')
            email_subject = message.get('subject', '')
            email_from = message.get('from', '')
            
            if not email_content.strip():
                self.logger.warning("Email has no content")
                return
            
            # Create data row for the Google Sheet
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Prepare data for Google Sheets - customize this based on what data you want to extract
            data_row = [
                timestamp,
                email_from,
                email_subject,
                email_content[:1000],  # Limit content to first 1000 chars
                'Processed'
            ]
            
            # Append to Google Sheet if target spreadsheet is configured
            if self.target_spreadsheet_id:
                success = self.sheets_service.append_data_to_sheet(
                    spreadsheet_id=self.target_spreadsheet_id,
                    data=[data_row],  # Pass as list of rows
                    sheet_name='Sheet1'
                )
                
                if success:
                    self.logger.info(f"Successfully appended MatrixCare data to Google Sheet")
                    self.logger.info(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{self.target_spreadsheet_id}/edit")
                else:
                    self.logger.error("Failed to append data to Google Sheet")
            else:
                self.logger.warning("No target spreadsheet ID configured - cannot append data")
            
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
                    # Append to existing spreadsheet
                    success = self.sheets_service.append_data_to_sheet(
                        spreadsheet_id=self.target_spreadsheet_id,
                        data=data_rows,
                        sheet_name='Sheet1'
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
    
    def run_once(self):
        """Run the processing once (useful for testing)."""
        self.process_emails()
    
    def run_scheduled(self):
        """Run the processor on a schedule for MatrixCare Looker Dash automation."""
        self.logger.info("Starting MatrixCare Looker Dash scheduler - checking every other Tuesday at 11:20 AM and 12:00 PM")
        
        # Schedule the job to run every day at 11:20 and 12:00 (the method will check if it's the right day)
        schedule.every().tuesday.at("11:20").do(self.process_emails)
        schedule.every().tuesday.at("12:00").do(self.process_emails)
        
        # Run initial check
        self.process_emails()
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email processor to replace Power Automate flow')
    parser.add_argument('--once', action='store_true', help='Run once instead of scheduled')
    parser.add_argument('--test-auth', action='store_true', help='Test authentication only')
    
    args = parser.parse_args()
    
    try:
        processor = EmailProcessor()
        
        if args.test_auth:
            print("✅ Authentication successful for Gmail, Google Drive, and Google Sheets")
            return
        
        if args.once:
            processor.run_once()
        else:
            processor.run_scheduled()
            
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
