#!/usr/bin/env python3
"""
Setup script for Google Sheets API integration
This script helps configure the Google Sheets API for The Boat Dude admin interface
"""

import os
import json
import sys
from pathlib import Path

def create_env_file():
    """Create a .env file with necessary environment variables"""
    env_content = """# Google Sheets API Configuration
# Set one of these two options:

# Option 1: Path to credentials JSON file
GOOGLE_CREDENTIALS_PATH=./api/credentials.json

# Option 2: Credentials JSON as environment variable (for production)
# GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
"""
    
    env_path = Path('.env')
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
    else:
        print("⚠️  .env file already exists")

def create_gitignore_entry():
    """Add sensitive files to .gitignore"""
    gitignore_path = Path('.gitignore')
    sensitive_files = [
        '# Google Sheets API credentials',
        'api/credentials.json',
        '.env',
        '__pycache__/',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.Python',
        'env/',
        'venv/',
        '.venv/',
        ''
    ]
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing_content = f.read()
        
        # Check if credentials are already ignored
        if 'api/credentials.json' not in existing_content:
            with open(gitignore_path, 'a') as f:
                f.write('\n' + '\n'.join(sensitive_files))
            print("✅ Added sensitive files to .gitignore")
        else:
            print("⚠️  Sensitive files already in .gitignore")
    else:
        with open(gitignore_path, 'w') as f:
            f.write('\n'.join(sensitive_files))
        print("✅ Created .gitignore with sensitive files")

def print_setup_instructions():
    """Print setup instructions for Google Sheets API"""
    instructions = """
🚤 Google Sheets API Setup Instructions

1. CREATE GOOGLE CLOUD PROJECT:
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing one
   - Enable the Google Sheets API and Google Drive API

2. CREATE SERVICE ACCOUNT:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Give it a name like "boat-dude-sheets"
   - Click "Create and Continue"
   - Skip role assignment for now
   - Click "Done"

3. GENERATE CREDENTIALS:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose "JSON" format
   - Download the JSON file

4. CONFIGURE CREDENTIALS:
   - Rename the downloaded file to 'credentials.json'
   - Move it to the 'api/' directory
   - OR set the GOOGLE_CREDENTIALS_JSON environment variable

5. SHARE GOOGLE SHEETS:
   - Open your Google Sheets (boats and photos)
   - Click "Share" button
   - Add the service account email (from credentials.json)
   - Give it "Editor" permissions

6. INSTALL DEPENDENCIES:
   pip install -r requirements.txt

7. START THE API SERVER:
   python api/app.py

8. TEST THE CONNECTION:
   curl http://localhost:5000/api/health

Your Google Sheets are already configured with these IDs:
- Boats Sheet: 2PACX-1vR8cbFH69KDvgM4QbH3NN9dV00YCQC9Oq9D2QXTK9n6bAqOK0UYWp5xvscLr-Gcq6g4AKKOYlb4bgcW
- Photos Sheet: 2PACX-1vQBSowD7wrpoH7pCeO101ak6sTPuf9N7D-r8e0exZMKplbePvFbubCHTCyaatRXKom_Y3AZ94EnGU4o

Need help? Check the logs when running the API server.
"""
    print(instructions)

def main():
    """Main setup function"""
    print("🚤 Setting up Google Sheets API integration...")
    
    # Create necessary files
    create_env_file()
    create_gitignore_entry()
    
    # Print instructions
    print_setup_instructions()
    
    print("\n✅ Setup files created!")
    print("📝 Follow the instructions above to complete the Google Sheets API setup.")

if __name__ == "__main__":
    main()
