"""
Google Sheets API service for creating and managing spreadsheets.
"""

import os
import pickle
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import gspread
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Service class for Google Sheets API operations."""
    
    def __init__(self, credentials_file: str, token_file: str = 'sheets_token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.gc = None  # gspread client
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
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
        
        # Initialize both services
        self.service = build('sheets', 'v4', credentials=creds)
        self.gc = gspread.authorize(creds)
        self.creds = creds  # Store credentials for later use
        logger.info("Google Sheets service authenticated successfully")
    
    def create_spreadsheet(self, 
                          title: str, 
                          folder_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Create a new Google Spreadsheet.
        
        Args:
            title: Title for the spreadsheet
            folder_id: Parent folder ID (None for root)
        
        Returns:
            Dictionary with spreadsheet info (id, url, title) or None if failed
        """
        try:
            # Create spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': title
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            
            # Move to folder if specified
            if folder_id:
                try:
                    # Use Drive API to move file
                    drive_service = build('drive', 'v3', credentials=self.creds)
                    
                    # Get current parents
                    file = drive_service.files().get(
                        fileId=spreadsheet_id,
                        fields='parents'
                    ).execute()
                    previous_parents = ",".join(file.get('parents'))
                    
                    # Move file to new folder
                    drive_service.files().update(
                        fileId=spreadsheet_id,
                        addParents=folder_id,
                        removeParents=previous_parents,
                        fields='id, parents'
                    ).execute()
                    
                    logger.info(f"Moved spreadsheet to folder: {folder_id}")
                    
                except HttpError as e:
                    logger.warning(f"Could not move spreadsheet to folder: {e}")
            
            logger.info(f"Created spreadsheet: {title} (ID: {spreadsheet_id})")
            
            return {
                'id': spreadsheet_id,
                'url': spreadsheet_url,
                'title': title
            }
            
        except HttpError as error:
            logger.error(f"Error creating spreadsheet {title}: {error}")
            return None
    
    def write_data_to_sheet(self, 
                           spreadsheet_id: str, 
                           data: List[List[Any]], 
                           sheet_name: str = 'Sheet1',
                           start_cell: str = 'A1') -> bool:
        """
        Write data to a specific sheet in the spreadsheet.
        
        Args:
            spreadsheet_id: The spreadsheet ID
            data: 2D list of data to write
            sheet_name: Name of the sheet to write to
            start_cell: Starting cell (e.g., 'A1')
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not data:
                logger.warning("No data provided to write")
                return False
            
            # Calculate range
            num_rows = len(data)
            num_cols = len(data[0]) if data else 0
            
            # Convert start cell to row/col numbers
            start_col_letter = ''.join(filter(str.isalpha, start_cell))
            start_row = int(''.join(filter(str.isdigit, start_cell)))
            
            # Calculate end cell
            end_col_num = ord(start_col_letter.upper()) - ord('A') + num_cols - 1
            end_col_letter = chr(ord('A') + end_col_num)
            end_row = start_row + num_rows - 1
            
            range_name = f"{sheet_name}!{start_cell}:{end_col_letter}{end_row}"
            
            # Prepare the request
            body = {
                'values': data
            }
            
            # Write data
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            cells_updated = result.get('updatedCells', 0)
            logger.info(f"Updated {cells_updated} cells in {range_name}")
            return True
            
        except HttpError as error:
            logger.error(f"Error writing data to sheet: {error}")
            return False
    
    def format_header_row(self, 
                         spreadsheet_id: str, 
                         sheet_id: int = 0, 
                         num_columns: int = 7) -> bool:
        """
        Format the header row (make it bold, add background color).
        
        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_id: The sheet ID (0 for first sheet)
            num_columns: Number of columns to format
        
        Returns:
            True if successful, False otherwise
        """
        try:
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': num_columns
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 0.2,
                                    'green': 0.6,
                                    'blue': 0.9
                                },
                                'textFormat': {
                                    'bold': True,
                                    'foregroundColor': {
                                        'red': 1.0,
                                        'green': 1.0,
                                        'blue': 1.0
                                    }
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                    }
                }
            ]
            
            body = {'requests': requests}
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            logger.info("Header row formatted successfully")
            return True
            
        except HttpError as error:
            logger.error(f"Error formatting header row: {error}")
            return False
    
    def auto_resize_columns(self, 
                           spreadsheet_id: str, 
                           sheet_id: int = 0) -> bool:
        """
        Auto-resize columns to fit content.
        
        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_id: The sheet ID (0 for first sheet)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            requests = [
                {
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 10  # Resize first 10 columns
                        }
                    }
                }
            ]
            
            body = {'requests': requests}
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            logger.info("Columns auto-resized successfully")
            return True
            
        except HttpError as error:
            logger.error(f"Error auto-resizing columns: {error}")
            return False
    
    def create_and_populate_spreadsheet(self, 
                                       title: str, 
                                       headers: List[str], 
                                       data: List[List[Any]], 
                                       folder_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Create a new spreadsheet and populate it with data.
        
        Args:
            title: Spreadsheet title
            headers: Column headers
            data: Data rows
            folder_id: Parent folder ID
        
        Returns:
            Dictionary with spreadsheet info or None if failed
        """
        try:
            # Create spreadsheet
            sheet_info = self.create_spreadsheet(title, folder_id)
            if not sheet_info:
                return None
            
            spreadsheet_id = sheet_info['id']
            
            # Prepare data with headers
            all_data = [headers] + data
            
            # Write data
            if not self.write_data_to_sheet(spreadsheet_id, all_data):
                logger.error("Failed to write data to spreadsheet")
                return None
            
            # Format header row
            self.format_header_row(spreadsheet_id, num_columns=len(headers))
            
            # Auto-resize columns
            self.auto_resize_columns(spreadsheet_id)
            
            logger.info(f"Successfully created and populated spreadsheet: {title}")
            return sheet_info
            
        except Exception as error:
            logger.error(f"Error creating and populating spreadsheet: {error}")
            return None
    
    def generate_timestamped_title(self, prefix: str) -> str:
        """
        Generate a timestamped title for spreadsheets.
        
        Args:
            prefix: Title prefix
        
        Returns:
            Timestamped title
        """
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        return f"{prefix} - {timestamp}"
    
    def append_data_to_sheet(self, 
                            spreadsheet_id: str, 
                            data: List[List[Any]], 
                            sheet_name: str = 'Sheet1') -> bool:
        """
        Append data to the end of a sheet.
        
        Args:
            spreadsheet_id: The spreadsheet ID
            data: Data to append
            sheet_name: Name of the sheet
        
        Returns:
            True if successful, False otherwise
        """
        try:
            range_name = f"{sheet_name}!A:Z"  # This will append to the end
            
            body = {
                'values': data
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            cells_updated = result.get('updates', {}).get('updatedCells', 0)
            logger.info(f"Appended {len(data)} rows, updated {cells_updated} cells")
            return True
            
        except HttpError as error:
            logger.error(f"Error appending data to sheet: {error}")
            return False
    
    def get_existing_data(self, spreadsheet_id: str, sheet_name: str = 'Sheet1') -> List[List[str]]:
        """
        Get existing data from a sheet to check for duplicates.
        
        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the sheet
        
        Returns:
            List of existing rows
        """
        try:
            range_name = f"{sheet_name}!A:Z"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            logger.info(f"Retrieved {len(values)} existing rows from sheet '{sheet_name}'")
            if values:
                logger.info(f"First row sample: {values[0][:3] if len(values[0]) > 0 else 'Empty row'}")
                if len(values) > 1:
                    logger.info(f"Last row sample: {values[-1][:3] if len(values[-1]) > 0 else 'Empty row'}")
            return values
            
        except HttpError as error:
            logger.error(f"Error getting existing data: {error}")
            return []
    
    def append_data_without_duplicates(self, 
                                      spreadsheet_id: str, 
                                      data: List[List[Any]], 
                                      sheet_name: str = 'Sheet1',
                                      unique_columns: List[int] = None) -> bool:
        """
        Append data to sheet while avoiding duplicates.
        
        Args:
            spreadsheet_id: The spreadsheet ID
            data: Data to append
            sheet_name: Name of the sheet
            unique_columns: List of column indices to check for uniqueness (0-based)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not unique_columns:
                unique_columns = [0]  # Default to first column
            
            # Get existing data
            existing_data = self.get_existing_data(spreadsheet_id, sheet_name)
            
            # Create set of existing unique keys (skip header row if present)
            existing_keys = set()
            for i, row in enumerate(existing_data):
                # Skip the first row if it looks like headers
                if i == 0 and len(existing_data) > 1:
                    # Check if first row contains "Lead ID" or similar headers
                    if any('lead' in str(cell).lower() or 'id' in str(cell).lower() for cell in row if len(row) > max(unique_columns)):
                        logger.info("Skipping header row in duplicate check")
                        continue
                
                if len(row) > max(unique_columns):
                    key = tuple(str(row[i]) if i < len(row) else '' for i in unique_columns)
                    if key and key != ('',):  # Skip empty keys
                        existing_keys.add(key)
            
            logger.info(f"Found {len(existing_keys)} existing unique Lead IDs in sheet")
            
            # Filter out duplicates
            new_data = []
            for row in data:
                key = tuple(str(row[i]) if i < len(row) else '' for i in unique_columns)
                if key not in existing_keys:
                    new_data.append(row)
                    existing_keys.add(key)  # Add to set to prevent duplicates within this batch
            
            if not new_data:
                logger.info("No new data to append (all rows already exist)")
                return True
            
            logger.info(f"Appending {len(new_data)} new rows (filtered out {len(data) - len(new_data)} duplicates)")
            
            # Append only new data
            return self.append_data_to_sheet(spreadsheet_id, new_data, sheet_name)
            
        except Exception as error:
            logger.error(f"Error appending data without duplicates: {error}")
            return False