import os, json, gspread, time
from jolt_scraper_v4 import downloadCSVs
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
    listName = "TRS (TEST): BOH Training Report"
    listName2 = "TRS (TEST): Request Training/Retraining (BOH)"
    reinforceListName = "TRS: Reinforcement"

    # Download files with desired names; will reattempt 3x if a connection error occurs
    attemps = 0
    maxAttempts = 3
    errorOccured = True
    while errorOccured and attemps < maxAttempts:
        try:
            errorOccured = False
            path, path2, path3, scores = downloadCSVs(listName, listName2, reinforceListName)
            #path, scores = downloadCSVs_forReinforcements(reinforceListName)
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
    if os.path.exists(path):
        print("-Reading training reports")
        readReportFiles(path, client)
    else:
        print("[x]Unable to find " + str(path))

    # Check if downloadCSV (part 2) was successful
    if os.path.exists(path2):
        print("-Reading training requests")
        readRequestFiles(path2, client)
    else:
        print("[x]Unable to find " + str(path2))
    
    # Download file for reinforcement reports
    if os.path.exists(path3):
        print("-Reading reinforcement reports")
        readReinforcementFiles(path3, scores, client)
    else:
        print("[x]Unable to find " + str(path3))
