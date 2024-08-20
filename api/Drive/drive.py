import os
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
creds_path = os.path.join(os.getcwd(),r'api\\Drive\\')
# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def upload(file_path, file_name):
    try:
        folder_id = "1BxfWD3lHMju7j7ZTsPXIPr4RY7xQWQ0j"
        creds = None
        # Check for valid credentials
        if os.path.exists(creds_path+'token.json'):
            creds = Credentials.from_authorized_user_file(creds_path+'token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path+'creds.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open(creds_path+'token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('drive', 'v3', credentials=creds)

        # Specify the file to upload
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]  # Specify the folder ID
        }
        media = MediaFileUpload(file_path, mimetype='application/pdf')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')
        permission = {
            'role': 'reader',
            'type': 'anyone'
        }
        service.permissions().create(fileId=file_id, body=permission).execute()

        print(f'File uploaded successfully. File ID: {file_id}')
        print(f'Public URL: https://drive.google.com/file/d/{file_id}/view')
        return file_id
    except Exception as e:
        print(e)
        return False

def delete(file_id):
    creds = None
    # Check for valid credentials
    if os.path.exists(creds_path+'token.json'):
        creds = Credentials.from_authorized_user_file(creds_path+'token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path+
                'creds.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(creds_path+'token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    try:
        service.files().delete(fileId=file_id).execute()
        print(f'File with ID {file_id} has been deleted successfully.')
        return True
    except Exception as e:
        print(f'An error occurred: {e}')
        return False
