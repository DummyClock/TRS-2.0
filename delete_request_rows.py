import gspread
import time
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

#from auth import SPREADSHEET_ID, SERVICE_KEY_JSON_FILE, REG_REQUEST_ID, RETRAIN_REQUEST_ID
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
SERVICE_KEY_JSON_FILE = json.loads(os.environ["SERVICE_KEY_JSON_FILE"])
REG_REQUEST_ID = os.environ['REG_REQUEST_ID']
RETRAIN_REQUEST_ID = os.environ['RETRAIN_REQUEST_ID']

def apiTimeOut(api_error_counter):
    # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
    if api_error_counter > 0: 
        print("Minute Quota for Google Sheets API reached (CLEANING_SPREADSHEET). Will attempt to access again. \n\tPlease wait a moment...\n\tAttempts Left: " + str(api_error_counter))
        time.sleep(66)  
    else:
        print("Unable to Google Sheets API right now. Skipping this process.")
    return True

try:
    api_error = True
    api_error_counter = 3

    while api_error and api_error_counter > 0:
        # Set up credentials
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(SERVICE_KEY_JSON_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)

        # Get Sheets
        t_req_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(REG_REQUEST_ID)
        r_req_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(RETRAIN_REQUEST_ID)

        # Get the number of rows (with data) in each sheet
        t_req_len = len(t_req_sheet.get_all_values())
        r_req_len = len(r_req_sheet.get_all_values())

        # Get the max number of rows in each sheet
        max_training = t_req_sheet.row_count
        max_retraining = r_req_sheet.row_count

        # Delete rows
        if t_req_len >= max_training-120:
            print("Deleting the last 100 rows from Training Request Sheet.")
            t_req_sheet.delete_rows(start_index=max_training-100, end_index=max_training)

        if r_req_len >= max_retraining-120:
            print("Deleting the last 100 rows from Retraining Request Sheet.")
            r_req_sheet.delete_rows(start_index=max_retraining-100, end_index=max_retraining)
except APIError as e:
                # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
                api_error = apiTimeOut(api_error_counter)
                api_error_counter -= 1 
