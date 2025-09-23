"""
CSV processing module for transforming lead data.
"""

import csv
import json
import logging
from io import StringIO, BytesIO
from typing import List, Dict, Any
from urllib.parse import unquote

logger = logging.getLogger(__name__)


class CSVProcessor:
    """Handles CSV file processing and data transformation."""
    
    def __init__(self, max_rows: int = 5000):
        self.max_rows = max_rows
    
    def process_csv_attachment(self, csv_data: bytes) -> List[Dict[str, str]]:
        """
        Process CSV attachment data similar to Power Automate flow.
        
        Args:
            csv_data: Raw CSV data as bytes
        
        Returns:
            List of processed row dictionaries
        """
        try:
            # Decode CSV data
            csv_text = csv_data.decode('utf-8', errors='ignore')
            
            # Clean the CSV data (similar to Power Automate replace operations)
            # Remove carriage returns and clean quotes
            csv_text = csv_text.replace('\r', '')
            csv_text = csv_text.replace('""', '"')
            
            # Split into lines and skip header (take skip 1)
            lines = csv_text.split('\n')
            if len(lines) > 1:
                lines = lines[1:]  # Skip header
            
            # Take maximum number of rows (similar to take(skip(...), 5000))
            lines = lines[:self.max_rows]
            
            # Filter out empty lines
            lines = [line.strip() for line in lines if line.strip()]
            
            logger.info(f"Processing {len(lines)} CSV rows")
            
            processed_rows = []
            
            for line in lines:
                try:
                    row_data = self._process_csv_row(line)
                    if row_data:
                        processed_rows.append(row_data)
                except Exception as e:
                    logger.warning(f"Error processing row: {line[:100]}... Error: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(processed_rows)} rows")
            return processed_rows
            
        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            return []
    
    def _process_csv_row(self, row_text: str) -> Dict[str, str]:
        """
        Process a single CSV row similar to Power Automate's Split_Row logic.
        
        Args:
            row_text: Raw CSV row text
        
        Returns:
            Dictionary with structured lead data
        """
        try:
            # Clean the row (remove carriage returns, quotes, and split on commas)
            cleaned_row = row_text.replace('\r', '').replace('"', '')
            
            # Handle quoted CSV fields by using CSV reader
            csv_reader = csv.reader(StringIO(row_text))
            fields = next(csv_reader)
            
            # Ensure we have enough fields
            while len(fields) < 7:
                fields.append('')
            
            # Map to the expected structure from Power Automate
            lead_data = {
                'LeadCreationDate': fields[0].strip(),
                'InquiryDate': fields[1].strip(),
                'CommunityName': fields[2].strip(),
                'Classification': fields[3].strip(),
                'TotalLeads': fields[4].strip(),
                'SubSourceName': fields[5].strip(),
                'SourceName': fields[6].strip()
            }
            
            return lead_data
            
        except Exception as e:
            logger.error(f"Error processing CSV row: {e}")
            raise
    
    def create_output_csv(self, processed_rows: List[Dict[str, str]]) -> bytes:
        """
        Create output CSV from processed rows.
        
        Args:
            processed_rows: List of processed row dictionaries
        
        Returns:
            CSV data as bytes
        """
        try:
            if not processed_rows:
                return b''
            
            # Create CSV content
            output = StringIO()
            
            # Get field names from first row
            fieldnames = list(processed_rows[0].keys())
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in processed_rows:
                writer.writerow(row)
            
            # Convert to bytes
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"Created output CSV with {len(processed_rows)} rows")
            return csv_content.encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error creating output CSV: {e}")
            return b''
    
    def generate_temp_filename(self, original_filename: str) -> str:
        """
        Generate temporary filename similar to Power Automate flow.
        
        Args:
            original_filename: Original attachment filename
        
        Returns:
            Temporary filename with timestamp
        """
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        return f"New Leads - Daily TMP {timestamp}.csv"
    
    def generate_output_filename(self) -> str:
        """
        Generate output filename similar to Power Automate flow.
        
        Returns:
            Output filename with timestamp
        """
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%HHmm')
        return f"Lead_Data_{timestamp}.csv"
