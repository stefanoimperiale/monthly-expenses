import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
CREDENTIALS_JSON = os.path.join(BASE_DIR, 'credentials.json')
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class SheetService:
    def __init__(self):
        # Create a new service account in https://console.developers.google.com/apis/credentials,
        # and then share the spreadsheet file using the email of the generated account
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_JSON, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
        # Call the Sheets API
        self.sheet = service.spreadsheets()

    def get_spreadsheet(self, sheet_id, range, include_grid_data):
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
