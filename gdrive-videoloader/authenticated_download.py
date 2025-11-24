#!/usr/bin/env python3
"""
Authenticated Google Drive Video Downloader
Downloads files from Google Drive using OAuth authentication
"""

import os
import io
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate():
    """Authenticate with Google Drive API and return credentials."""
    creds = None

    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[INFO] Refreshing access token...")
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("\n" + "="*70)
                print("ERROR: credentials.json file not found!")
                print("="*70)
                print("\nYou need to set up Google Drive API credentials first.")
                print("\nFollow these steps:")
                print("\n1. Go to: https://console.cloud.google.com/")
                print("2. Create a new project (or select existing)")
                print("3. Enable Google Drive API:")
                print("   - Go to 'APIs & Services' > 'Library'")
                print("   - Search for 'Google Drive API'")
                print("   - Click 'Enable'")
                print("\n4. Create OAuth credentials:")
                print("   - Go to 'APIs & Services' > 'Credentials'")
                print("   - Click 'Create Credentials' > 'OAuth client ID'")
                print("   - Choose 'Desktop app' as application type")
                print("   - Download the credentials JSON file")
                print("\n5. Save the downloaded file as 'credentials.json' in:")
                print(f"   {os.getcwd()}")
                print("\n" + "="*70)
                return None

            print("[INFO] Starting OAuth flow...")
            print("[INFO] A browser window will open for authentication")
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            print("[INFO] Credentials saved to token.pickle")

    return creds

def get_file_metadata(service, file_id):
    """Get file metadata from Google Drive."""
    try:
        file = service.files().get(fileId=file_id, fields='name,mimeType,size').execute()
        return file
    except Exception as e:
        print(f"Error getting file metadata: {e}")
        return None

def download_file(service, file_id, output_path=None):
    """Download a file from Google Drive."""

    # Get file metadata
    print("[INFO] Fetching file metadata...")
    file_metadata = get_file_metadata(service, file_id)

    if not file_metadata:
        print("Failed to get file metadata")
        return False

    file_name = file_metadata.get('name', 'downloaded_file')
    mime_type = file_metadata.get('mimeType', '')
    file_size = int(file_metadata.get('size', 0))

    print(f"[INFO] File name: {file_name}")
    print(f"[INFO] MIME type: {mime_type}")
    print(f"[INFO] File size: {file_size / (1024*1024):.2f} MB")

    if output_path:
        file_name = output_path

    # Download the file
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_name, 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        print(f"\n[INFO] Downloading to: {file_name}")

        with tqdm(total=file_size, unit='B', unit_scale=True, desc=file_name) as pbar:
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    pbar.update(int(status.resumable_progress) - pbar.n)

        print(f"\n✓ Download completed: {file_name}")
        return True

    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Download files from Google Drive with authentication')
    parser.add_argument('file_id', help='Google Drive file ID')
    parser.add_argument('-o', '--output', help='Output filename (optional)', default=None)

    args = parser.parse_args()

    print("="*70)
    print("Google Drive Authenticated Downloader")
    print("="*70)

    # Authenticate
    creds = authenticate()
    if not creds:
        return

    # Build the service
    print("[INFO] Building Google Drive service...")
    service = build('drive', 'v3', credentials=creds)

    # Download the file
    success = download_file(service, args.file_id, args.output)

    if success:
        print("\n✓ All done!")
    else:
        print("\n✗ Download failed")

if __name__ == '__main__':
    main()
