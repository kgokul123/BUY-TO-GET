import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.conf import settings

# 📂 Categories Images Google Drive Folder ID
FOLDER_ID = '1-iWWSNb7sjPQ1HMFQ-zXtKD_nzSUZNip'

def upload_image_to_google_drive(file_obj, filename):
    try:
        creds_path = os.path.join(settings.BASE_DIR, 'credentials.json')
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': filename,
            'parents': [FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(file_obj, mimetype='image/jpeg', resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()
        
        return file.get('webContentLink')
    except Exception as e:
        print(f"Drive Upload Error: {e}")
        return None