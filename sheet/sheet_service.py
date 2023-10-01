import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from env_variables import GOOGLE_APPLICATION_CREDENTIALS_JSON
service_account_info = json.loads(GOOGLE_APPLICATION_CREDENTIALS_JSON)

# BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
# CREDENTIALS_JSON = os.path.join(BASE_DIR, 'credentials.json')
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class SheetService:
    def __init__(self):

        # Create a new service account in https://console.developers.google.com/apis/credentials,
        # and then share the spreadsheet file using the email of the generated account
        # credentials = service_account.Credentials.from_service_account_info(
        #     service_account_info, scopes=SCOPES)
        credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
        # Call the Sheets API
        self.sheet = service.spreadsheets()

    def get_spreadsheet(self, sheet_id, range, include_grid_data):
        return self.sheet.get(spreadsheetId=sheet_id, ranges=range, includeGridData=include_grid_data).execute()

    def read_sheet(self, sheet_id, range, major_dimension=None, value_render_option='FORMATTED_VALUE'):
        return self.sheet.values().get(spreadsheetId=sheet_id,
                                       range=range,
                                       majorDimension=major_dimension,
                                       valueRenderOption=value_render_option) \
            .execute()

    def read_sheet_multiple(self, sheet_id, ranges, major_dimension=None):
        return self.sheet.values().batchGet(spreadsheetId=sheet_id, ranges=ranges,
                                            majorDimension=major_dimension).execute()

    def write_append_sheet(self, sheet_id, range, values):
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

    def write_sheet(self, sheet_id, range, values):
        body = {
            'values': values,
            'range': range
        }
        result = self.sheet.values().update(
            spreadsheetId=sheet_id,
            range=range,
            valueInputOption='USER_ENTERED',
            body=body).execute()
        return result['updatedRows']

    def clear_sheet(self, sheet_id, range):
        request = self.sheet.values().clear(spreadsheetId=sheet_id, range=range)
        return request.execute()

    def delete_rows(self, spreadsheet_id, sheet_id, start_index, end_index):
        batch_update_spreadsheet_request_body = {
            'requests': [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_index,
                            "endIndex": end_index
                        }
                    }
                },
            ],
        }
        request = self.sheet.batchUpdate(spreadsheetId=spreadsheet_id,
                                         body=batch_update_spreadsheet_request_body)
        return request.execute()

    def add_sheet(self, spreadsheet_id, title, optional_requests=None):
        if optional_requests is None:
            optional_requests = []
        requests = [{
            "addSheet": {
                "properties": {
                    "title": title,
                }
            }
        }] + optional_requests
        body = {
            'requests': requests
        }
        response = self.sheet.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body).execute()
        response = response.get('replies')[0].get('addSheet')
        return response['properties']

    def update_sheet(self, spreadsheet_id, requests):
        body = {
            'requests': requests
        }
        response = self.sheet.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body).execute()
        return response
