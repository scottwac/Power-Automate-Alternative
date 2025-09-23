"""
Main email processing script that replaces the Power Automate flow.

This script:
1. Monitors Gmail for new emails with attachments from a specific sender
2. Downloads CSV attachments and uploads them to Google Drive
3. Processes the CSV data and creates a new formatted CSV
4. Uploads the processed CSV to Google Drive
5. Runs on a schedule (every 5 minutes by default)
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

from gmail_service import GmailService
from google_drive_service import GoogleDriveService
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
        self.gmail_subject_filter = os.getenv('GMAIL_SUBJECT_FILTER', 'Test')
        self.gmail_label = os.getenv('GMAIL_LABEL', 'INBOX')
        
        self.drive_credentials_file = os.getenv('GOOGLE_DRIVE_CREDENTIALS_FILE', 'credentials.json')
        # Get folder ID, treat '/' or empty as None (root folder)
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.drive_folder_id = None if folder_id in ['/', '', None] else folder_id
        
        self.check_interval_minutes = int(os.getenv('CHECK_INTERVAL_MINUTES', '5'))
        self.max_rows_to_process = int(os.getenv('MAX_ROWS_TO_PROCESS', '5000'))
        
        self.logger.info(f"Configuration loaded - checking every {self.check_interval_minutes} minutes")
    
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
            
            self.csv_processor = CSVProcessor(self.max_rows_to_process)
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing services: {e}")
            raise
    
    def process_emails(self):
        """Main processing function that runs on schedule."""
        try:
            self.logger.info("Starting email processing cycle")
            
            # Search for new emails
            message_ids = self.gmail_service.search_emails(
                from_email=self.gmail_from_email,
                subject=self.gmail_subject_filter,
                label=self.gmail_label,
                has_attachments=True,
                since_minutes=self.check_interval_minutes + 1  # Add buffer
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
        Process a single email with attachments.
        
        Args:
            message_id: Gmail message ID
        """
        try:
            self.logger.info(f"Processing email: {message_id}")
            
            # Get message with attachments
            message = self.gmail_service.get_message_with_attachments(message_id)
            if not message:
                self.logger.warning(f"Could not retrieve message: {message_id}")
                return
            
            self.logger.info(f"Email from: {message['from']}, Subject: {message['subject']}")
            
            # Process each CSV attachment
            csv_attachments = [
                att for att in message['attachments'] 
                if att['filename'].lower().endswith('.csv')
            ]
            
            if not csv_attachments:
                self.logger.info("No CSV attachments found")
                return
            
            for attachment in csv_attachments:
                self.process_csv_attachment(attachment, message)
            
        except Exception as e:
            self.logger.error(f"Error processing email {message_id}: {e}")
    
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
                self.logger.info(f"Successfully processed and uploaded: {output_filename} (ID: {output_file_id})")
                self.logger.info(f"Processed {len(processed_rows)} rows of lead data")
            else:
                self.logger.error(f"Failed to upload processed file: {output_filename}")
                
        except Exception as e:
            self.logger.error(f"Error processing CSV attachment {attachment['filename']}: {e}")
    
    def run_once(self):
        """Run the processing once (useful for testing)."""
        self.process_emails()
    
    def run_scheduled(self):
        """Run the processor on a schedule."""
        self.logger.info(f"Starting scheduled processing every {self.check_interval_minutes} minutes")
        
        # Schedule the job
        schedule.every(self.check_interval_minutes).minutes.do(self.process_emails)
        
        # Run initial check
        self.process_emails()
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds


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
            print("✅ Authentication successful for both Gmail and Google Drive")
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
