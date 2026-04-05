#!/usr/bin/env python3
"""
Google Sheets API service for The Boat Dude admin interface
Handles pushing data from admin interface to Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
import json
import os
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SheetsService:
    def __init__(self, credentials_path: str = None):
        """
        Initialize the Google Sheets service
        
        Args:
            credentials_path: Path to Google service account credentials JSON file
        """
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH')
        self.scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.client = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                # Use service account credentials
                creds = Credentials.from_service_account_file(
                    self.credentials_path, 
                    scopes=self.scope
                )
                self.client = gspread.authorize(creds)
                logger.info("Authenticated with Google Sheets using service account")
            else:
                # Try to use environment variable with credentials JSON
                creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
                if creds_json:
                    creds_info = json.loads(creds_json)
                    creds = Credentials.from_service_account_info(
                        creds_info, 
                        scopes=self.scope
                    )
                    self.client = gspread.authorize(creds)
                    logger.info("Authenticated with Google Sheets using environment credentials")
                else:
                    logger.error("No Google credentials found. Please set GOOGLE_CREDENTIALS_PATH or GOOGLE_CREDENTIALS_JSON")
                    raise Exception("Google Sheets authentication failed")
        except Exception as e:
            logger.exception(f"Authentication failed: {e}")
            raise
    
    def get_sheet(self, sheet_id: str, worksheet_name: str = None) -> Optional[gspread.Worksheet]:
        """
        Get a specific worksheet from a Google Sheet
        
        Args:
            sheet_id: The Google Sheet ID
            worksheet_name: Name of the worksheet (optional)
            
        Returns:
            gspread.Worksheet object or None if not found
        """
        try:
            sheet = self.client.open_by_key(sheet_id)
            if worksheet_name:
                return sheet.worksheet(worksheet_name)
            else:
                return sheet.sheet1
        except Exception as e:
            logger.exception(f"Failed to get sheet {sheet_id}: {e}")
            return None
    
    def push_boats_data(self, boats_data: List[Dict[str, Any]], sheet_id: str, worksheet_name: str = None) -> bool:
        """
        Push boats data to Google Sheets
        
        Args:
            boats_data: List of boat dictionaries
            sheet_id: Google Sheet ID
            worksheet_name: Worksheet name (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self.get_sheet(sheet_id, worksheet_name)
            if not worksheet:
                return False
            
            # Clear existing data (except header)
            worksheet.clear()
            
            # Define headers based on the admin interface
            headers = [
                'published', 'id', 'title', 'category', 'status', 'price', 'price_display',
                'year', 'make', 'model', 'length_ft', 'hours', 'engine', 'hull', 'color',
                'location', 'description', 'contact_phone', 'contact_email', 'created_at',
                'condition', 'trailer_included', 'propulsion', 'beam_ft', 'draft_ft',
                'fuel_capacity', 'seating_capacity', 'features', 'history', 'maintenance_notes'
            ]
            
            # Add headers
            worksheet.append_row(headers)
            
            # Add data rows
            for boat in boats_data:
                row = []
                for header in headers:
                    value = boat.get(header, '')
                    # Convert boolean values to Y/N for published field
                    if header == 'published' and isinstance(value, bool):
                        value = 'Y' if value else 'N'
                    row.append(str(value) if value is not None else '')
                
                worksheet.append_row(row)
            
            logger.info(f"Successfully pushed {len(boats_data)} boats to Google Sheets")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to push boats data: {e}")
            return False
    
    def push_photos_data(self, photos_data: List[Dict[str, Any]], sheet_id: str, worksheet_name: str = None) -> bool:
        """
        Push photos data to Google Sheets
        
        Args:
            photos_data: List of photo dictionaries
            sheet_id: Google Sheet ID
            worksheet_name: Worksheet name (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self.get_sheet(sheet_id, worksheet_name)
            if not worksheet:
                return False
            
            # Clear existing data (except header)
            worksheet.clear()
            
            # Define headers for photos
            headers = [
                'boat_id', 'photo_id', 'photo_url', 'photo_alt', 'photo_order',
                'is_primary', 'photo_type', 'photo_notes'
            ]
            
            # Add headers
            worksheet.append_row(headers)
            
            # Add data rows
            for photo in photos_data:
                row = []
                for header in headers:
                    value = photo.get(header, '')
                    # Convert boolean values to TRUE/FALSE for is_primary field
                    if header == 'is_primary' and isinstance(value, bool):
                        value = 'TRUE' if value else 'FALSE'
                    row.append(str(value) if value is not None else '')
                
                worksheet.append_row(row)
            
            logger.info(f"Successfully pushed {len(photos_data)} photos to Google Sheets")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to push photos data: {e}")
            return False
    
    def get_boats_data(self, sheet_id: str, worksheet_name: str = None) -> List[Dict[str, Any]]:
        """
        Get boats data from Google Sheets
        
        Args:
            sheet_id: Google Sheet ID
            worksheet_name: Worksheet name (optional)
            
        Returns:
            List of boat dictionaries
        """
        try:
            worksheet = self.get_sheet(sheet_id, worksheet_name)
            if not worksheet:
                return []
            
            # Get all records
            records = worksheet.get_all_records()
            logger.info(f"Retrieved {len(records)} boats from Google Sheets")
            return records
            
        except Exception as e:
            logger.exception(f"Failed to get boats data: {e}")
            return []
    
    def get_photos_data(self, sheet_id: str, worksheet_name: str = None) -> List[Dict[str, Any]]:
        """
        Get photos data from Google Sheets
        
        Args:
            sheet_id: Google Sheet ID
            worksheet_name: Worksheet name (optional)
            
        Returns:
            List of photo dictionaries
        """
        try:
            worksheet = self.get_sheet(sheet_id, worksheet_name)
            if not worksheet:
                return []
            
            # Get all records
            records = worksheet.get_all_records()
            logger.info(f"Retrieved {len(records)} photos from Google Sheets")
            return records
            
        except Exception as e:
            logger.exception(f"Failed to get photos data: {e}")
            return []

# Configuration for The Boat Dude sheets
BOATS_SHEET_ID = "2PACX-1vR8cbFH69KDvgM4QbH3NN9dV00YCQC9Oq9D2QXTK9n6bAqOK0UYWp5xvscLr-Gcq6g4AKKOYlb4bgcW"
PHOTOS_SHEET_ID = "2PACX-1vQBSowD7wrpoH7pCeO101ak6sTPuf9N7D-r8e0exZMKplbePvFbubCHTCyaatRXKom_Y3AZ94EnGU4o"

def create_sheets_service() -> SheetsService:
    """Create a configured SheetsService instance"""
    return SheetsService()
