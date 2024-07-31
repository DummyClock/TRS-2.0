import os
import gspread
from jolt_scraper_v4 import downloadCSVs
from google.oauth2.service_account import Credentials
from ss_manip_TRS import readReportFiles, readRequestFiles

#from auth import SERVICE_KEY_JSON_FILE
SERVICE_KEY_JSON_FILE = os.environ["SERVICE_KEY_JSON_FILE"]
SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/script.external_request', 'https://www.googleapis.com/auth/script.projects']
creds = Credentials.from_service_account_info(SERVICE_KEY_JSON_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
#path = os.path.dirname(os.path.realpath(__file__)) + '\\tmp_reports'
#path2 = os.path.dirname(os.path.realpath(__file__)) + '\\tmp_requests'

#Testing the functions. (Downloads files & lists names of downloaded files)
listName = ["TRS (TEST): BOH Training Report".lower()]
listName2 = ["TRS (TEST): Request Training/Retraining (BOH)".lower()]
paths = downloadCSVs(listName, listName2)
readReportFiles(paths[0], client)
readRequestFiles(paths[1], client)
