# Google Drive API Authentication Guide

This guide will help you set up OAuth authentication to download restricted Google Drive videos.

## Prerequisites

- Python 3.7+
- Google account
- Access to Google Cloud Console

## Step-by-Step Setup

### 1. Install Required Packages

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client tqdm
```

### 2. Create Google Cloud Project & Enable API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
   - Enter a project name (e.g., "gdrive-downloader")
   - Click "Create"
4. Wait for the project to be created, then select it

### 3. Enable Google Drive API

1. In the left sidebar, go to **"APIs & Services"** > **"Library"**
2. Search for **"Google Drive API"**
3. Click on it and press **"Enable"**

### 4. Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"Create Credentials"** button at the top
3. Select **"OAuth client ID"**
4. If prompted to configure OAuth consent screen:
   - Click "Configure Consent Screen"
   - Choose "External" (unless you have a Google Workspace)
   - Fill in:
     - App name: "GDrive Video Downloader"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - Skip "Scopes" (click "Save and Continue")
   - Add your email as a test user
   - Click "Save and Continue"
5. Back to "Create OAuth client ID":
   - Application type: **"Desktop app"**
   - Name: "GDrive Downloader Client"
   - Click **"Create"**
6. Click **"Download JSON"** on the popup
7. Save the file as `credentials.json` in the `gdrive-videoloader` directory

### 5. Download Your Video

```bash
cd gdrive-videoloader
python authenticated_download.py 1dxTuc8uIIeaoUHafXsk22EIUvc9lE6C3
```

**What happens:**
1. First time: A browser window will open
2. Sign in with your Google account
3. Grant permissions to the app
4. The download will start automatically
5. A `token.pickle` file will be created for future use

### 6. Optional: Specify Output Filename

```bash
python authenticated_download.py 1dxTuc8uIIeaoUHafXsk22EIUvc9lE6C3 -o my_video.mp4
```

## Troubleshooting

### "credentials.json not found"
- Make sure you downloaded the OAuth credentials from Google Cloud Console
- Save it as `credentials.json` in the same directory as the script

### "Access denied" or "403 Forbidden"
- Make sure you're logged in with the Google account that has access to the file
- Check if the file is shared with your account

### "This app isn't verified"
- Click "Advanced" and then "Go to GDrive Video Downloader (unsafe)"
- This is safe since you created the app yourself

### Token expired
- Delete `token.pickle` file and run the script again to re-authenticate

## Files Created

- `credentials.json` - Your OAuth client credentials (don't share this!)
- `token.pickle` - Your access token (don't share this!)
- Both files are in `.gitignore` for security

## Security Notes

- Never commit `credentials.json` or `token.pickle` to version control
- Don't share these files with anyone
- The script only requests read-only access to your Google Drive
