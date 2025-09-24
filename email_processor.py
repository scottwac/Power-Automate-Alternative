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
import pytz
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
            
            # Search for new emails - look for emails from any sender with target subject
            message_ids = self.gmail_service.search_emails(
                from_email=None,  # Accept emails from any sender
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
    
    def manual_email_check(self):
        """Manually check for emails regardless of schedule."""
        try:
            self.logger.info("Starting manual email check (bypassing schedule)")
            
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
    
    def run_scheduled(self):
        """Run the processor on a schedule for MatrixCare Looker Dash automation."""
        # Convert EST times to local time for proper scheduling
        est_tz = pytz.timezone('US/Eastern')
        
        # Convert 11:20 AM EST to local time
        est_time_1 = datetime.now(est_tz).replace(hour=11, minute=20, second=0, microsecond=0)
        local_time_1 = est_time_1.astimezone()
        local_time_1_str = local_time_1.strftime("%H:%M")
        
        # Convert 12:00 PM EST to local time  
        est_time_2 = datetime.now(est_tz).replace(hour=12, minute=0, second=0, microsecond=0)
        local_time_2 = est_time_2.astimezone()
        local_time_2_str = local_time_2.strftime("%H:%M")
        
        self.logger.info(f"Starting MatrixCare Looker Dash scheduler - checking every other Tuesday at:")
        self.logger.info(f"  11:20 AM EST ({local_time_1_str} local time)")
        self.logger.info(f"  12:00 PM EST ({local_time_2_str} local time)")
        
        # Schedule the job to run every Tuesday at the converted local times
        schedule.every().tuesday.at(local_time_1_str).do(self.process_emails)
        schedule.every().tuesday.at(local_time_2_str).do(self.process_emails)
        
        # Run initial check
        self.process_emails()
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_custom_schedule(self, est_time: str):
        """Run the processor at a custom time in EST timezone."""
        try:
            # Validate time format (HH:MM)
            datetime.strptime(est_time, "%H:%M")
        except ValueError:
            raise ValueError("Time must be in HH:MM format (24-hour), e.g., '14:30' for 2:30 PM")
        
        # Convert EST time to local time for scheduling
        est_tz = pytz.timezone('US/Eastern')
        local_tz = pytz.timezone('UTC')  # Default to UTC, will be converted to system local time
        
        # Parse the EST time
        est_hour, est_minute = map(int, est_time.split(':'))
        
        # Create a datetime object for today at the specified EST time
        today_est = datetime.now(est_tz).replace(hour=est_hour, minute=est_minute, second=0, microsecond=0)
        
        # Convert to local time
        today_local = today_est.astimezone()
        local_time_str = today_local.strftime("%H:%M")
        
        self.logger.info(f"Starting MatrixCare Looker Dash scheduler - checking every other Tuesday at {est_time} EST ({local_time_str} local time)")
        
        # Schedule the job to run every Tuesday at the converted local time
        schedule.every().tuesday.at(local_time_str).do(self.process_emails)
        
        # Run initial check
        self.process_emails()
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def check_in_2_minutes(self):
        """Schedule an email check to run in exactly 2 minutes."""
        # Calculate the time 2 minutes from now
        check_time = datetime.now() + timedelta(minutes=2)
        check_time_str = check_time.strftime("%H:%M")
        
        # Get current time for logging
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.logger.info(f"Current time: {current_time}")
        self.logger.info(f"Scheduling email check for {check_time_str} (in 2 minutes)")
        
        # Clear any existing scheduled jobs
        schedule.clear()
        
        # Schedule the job for today at the calculated time - use a test version that bypasses day check
        schedule.every().day.at(check_time_str).do(self.process_emails_test)
        
        print(f"⏰ Email check scheduled for {check_time_str} (in 2 minutes)")
        print(f"   Current time: {current_time}")
        print(f"   Will check for emails with subject: '{self.gmail_subject_filter}'")
        print("   Waiting...")
        
        # Keep the script running until the scheduled time and a bit after
        start_time = datetime.now()
        max_wait_time = timedelta(minutes=5)  # Wait up to 5 minutes total
        
        while datetime.now() - start_time < max_wait_time:
            schedule.run_pending()
            time.sleep(10)  # Check every 10 seconds for more responsive timing
            
            # Check if we've passed the scheduled time by more than 1 minute
            if datetime.now() > check_time + timedelta(minutes=1):
                self.logger.info("Scheduled check completed, exiting")
                break
        
        print("✅ 2-minute check completed")
    
    def process_emails_test(self):
        """Test version of process_emails that bypasses the Tuesday check."""
        try:
            self.logger.info("Starting TEST email processing cycle (bypassing Tuesday check)")
            
            # Search for new emails - look for emails from any sender with target subject
            message_ids = self.gmail_service.search_emails(
                from_email=None,  # Accept emails from any sender
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
            
            self.logger.info("TEST email processing cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in process_emails_test: {e}")


def show_time_info():
    """Display current system time and timezone information."""
    import platform
    
    # Get current time in different formats
    now = datetime.now()
    utc_now = datetime.utcnow()
    
    # Get EST time
    est_tz = pytz.timezone('US/Eastern')
    est_now = now.astimezone(est_tz)
    
    print("🕐 Current Time Information")
    print("=" * 50)
    print(f"System Local Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"UTC Time:          {utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"EST Time:          {est_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"System Timezone:   {now.astimezone().tzinfo}")
    print(f"Platform:          {platform.system()} {platform.release()}")
    
    # Show day of week for schedule checking
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    print(f"Day of Week:       {weekday_names[now.weekday()]} (weekday {now.weekday()})")
    
    # Calculate next Tuesday for reference
    days_until_tuesday = (1 - now.weekday()) % 7
    if days_until_tuesday == 0 and now.weekday() == 1:
        print(f"Today Status:      Today IS Tuesday!")
    else:
        next_tuesday = now + timedelta(days=days_until_tuesday)
        print(f"Next Tuesday:      {next_tuesday.strftime('%Y-%m-%d')}")
    
    print("")
    print("📅 Default Schedule Times (EST → Local Conversion)")
    print("-" * 50)
    
    # Show what the default schedule times convert to
    est_morning = datetime.now(est_tz).replace(hour=11, minute=20, second=0, microsecond=0)
    est_noon = datetime.now(est_tz).replace(hour=12, minute=0, second=0, microsecond=0)
    
    local_morning = est_morning.astimezone()
    local_noon = est_noon.astimezone()
    
    print(f"11:20 AM EST  →    {local_morning.strftime('%H:%M')} local time")
    print(f"12:00 PM EST  →    {local_noon.strftime('%H:%M')} local time")
    
    print("=" * 50)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MatrixCare Looker Dashboard Automation')
    parser.add_argument('--once', action='store_true', help='Run once instead of scheduled')
    parser.add_argument('--test-auth', action='store_true', help='Test authentication only')
    parser.add_argument('--manual-check', action='store_true', help='Manually check for emails regardless of schedule')
    parser.add_argument('--custom-time', type=str, metavar='HH:MM', 
                       help='Run on schedule at custom time in EST (24-hour format, e.g., 14:30 for 2:30 PM)')
    parser.add_argument('--check-in-2min', action='store_true', 
                       help='Check for emails in exactly 2 minutes from now (useful for testing)')
    parser.add_argument('--show-time', action='store_true', 
                       help='Show current system time and timezone information')
    
    args = parser.parse_args()
    
    try:
        processor = EmailProcessor()
        
        if args.test_auth:
            print("✅ Authentication successful for Gmail, Google Drive, and Google Sheets")
            return
        
        if args.show_time:
            show_time_info()
            return
        
        if args.manual_check:
            processor.manual_email_check()
        elif args.once:
            processor.run_once()
        elif args.check_in_2min:
            processor.check_in_2_minutes()
        elif args.custom_time:
            processor.run_custom_schedule(args.custom_time)
        else:
            processor.run_scheduled()
            
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
