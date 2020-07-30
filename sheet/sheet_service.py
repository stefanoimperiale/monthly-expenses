import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
TOKEN_PICKLE = os.path.join(BASE_DIR, 'token.pickle')
CREDENTIALS_JSON = os.path.join(BASE_DIR, 'credentials.json')
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class SheetService:
    def __init__(self):
        credentials = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(TOKEN_PICKLE):
            with open(TOKEN_PICKLE, 'rb') as token:
                credentials = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_JSON, SCOPES)
                credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(credentials, token)

        service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
        # Call the Sheets API
        self.sheet = service.spreadsheets()

    def get_sheet(self, sheet_id, range, include_grid_data):
        return self.sheet.get(spreadsheetId=sheet_id, ranges=range, includeGridData=include_grid_data).execute()

    def read_sheet(self, sheet_id, range):
        return self.sheet.values().get(spreadsheetId=sheet_id, range=range).execute()

    def write_sheet(self, sheet_id, range, values):
        body = {
            'values': values,
            'range': range
        }
        result = self.sheet.values().append(
            spreadsheetId=sheet_id,
            range=range,
            valueInputOption='USER_ENTERED',
            body=body).execute()
        return result.get('updates').get('updatedRows')
