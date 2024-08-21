import os, json, gspread, time
from jolt_scraper_v4 import downloadCSVs, downloadCSVs_forReinforcements
from google.oauth2.service_account import Credentials
from ss_manip_TRS import readReportFiles, readRequestFiles, readReinforcementFiles
from selenium.common.exceptions import WebDriverException

#from auth import SERVICE_KEY_JSON_FILE
SERVICE_KEY_JSON_FILE = json.loads(os.environ["SERVICE_KEY_JSON_FILE"])

# Removes all files from a directory
def clearDirectory(path):
    print("Clearing the directory " + path)
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        os.remove(file_path)

# Entry Point
if __name__ == "__main__":
    # Set up credentials
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/script.external_request', 'https://www.googleapis.com/auth/script.projects']
    creds = Credentials.from_service_account_info(SERVICE_KEY_JSON_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    #Store the desired list names to download
    listName = ["TRS (TEST): BOH Training Report".lower()]
    listName2 = ["TRS (TEST): Request Training/Retraining (BOH)".lower()]

    # Download files with desired names; will reattempt 3x if a connection error occurs
    attemps = 0
    maxAttempts = 3
    errorOccured = True
    while errorOccured and attemps < maxAttempts:
        try:
            errorOccured = False
            paths = downloadCSVs(listName, listName2)

            listName = "TRS: Reinforcement".lower()
            path, scores = downloadCSVs_forReinforcements(listName)
        except WebDriverException as e:
            print("Connection error occured. Reattempting to launch in a minute...")
            errorOccured = True
            attemps += 1
            p1 = os.path.dirname(os.path.realpath(__file__)) + '\\tmp_reports'
            p2 = os.path.dirname(os.path.realpath(__file__)) + '\\tmp_requests'
            p3 = os.path.dirname(os.path.realpath(__file__)) + '\\tmp_reinforcements'
            clearDirectory(p1)   # Delete temp files; attempt to redownload after the wait time
            clearDirectory(p2)
            clearDirectory(p3)
            time.sleep(60)

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
    
    # Download file for reinforcement reports
    if os.path.exists(path):
        readReinforcementFiles(path, scores, client)
    else:
        print("Unable to find " + str(path))
