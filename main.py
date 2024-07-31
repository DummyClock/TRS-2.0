import os
import gspread
import json
from jolt_scraper_v4 import downloadCSVs
from google.oauth2.service_account import Credentials
from ss_manip_TRS import readReportFiles, readRequestFiles

#from auth import SERVICE_KEY_JSON_FILE
SERVICE_KEY_JSON_FILE = json.loads(os.environ["SERVICE_KEY_JSON_FILE"])

SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/script.external_request', 'https://www.googleapis.com/auth/script.projects']
creds = Credentials.from_service_account_info(SERVICE_KEY_JSON_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

#Testing the functions. (Downloads files & lists names of downloaded files)
listName = ["TRS (TEST): BOH Training Report".lower()]
listName2 = ["TRS (TEST): Request Training/Retraining (BOH)".lower()]
paths = downloadCSVs(listName, listName2)

# Check if downloadCSV (part 1) was successful
if os.path.exists(paths[0]):
    readReportFiles(paths[0], client)
else:
    print("Unable to find " + str(paths[0]))

# Check if downloadCSV (part 2) was successful
if os.path.exists(paths[1]):
    readRequestFiles(paths[1], client)
else:
    print("Unable to find " + str(paths[1]))
