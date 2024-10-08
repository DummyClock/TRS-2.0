from selenium import webdriver 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import date, timedelta
from google.oauth2.service_account import Credentials
import os, time, re

#from auth import EMAIL, PASSWORD
# Gets hidden values from Github Secrets - (Remove this block when testing on a locally)
EMAIL = os.environ['EMAIL']
PASSWORD = os.environ['PASSWORD']
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def downloadCSVs(trainingListName, reqListName=None, reinforceListName=None, startDate=None, endDate=None):
    #Get the default one-week-period dates
    print("Searching for files with the name " + str(trainingListName) + ", " +str(reqListName) + ", & " + reinforceListName)
    if startDate == None and endDate == None:
        endDate = str(date.today() - timedelta(days=1))
        startDate = str(date.today() - timedelta(days=3))
    print("-StartDate:"+startDate+"!")

    #Prepare both download locations before launching instance of webdriver in headless mode
    download_dir = os.path.dirname(os.path.realpath(__file__))+ '\\tmp_reports'
    download_dir2 = os.path.dirname(os.path.realpath(__file__))+ '\\tmp_requests'
    download_dir3 = os.path.dirname(os.path.realpath(__file__))+ '\\tmp_reinforcements'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print("Created a temporary directory to store downloads\n\tPath: '" + download_dir +"'")
    if not os.path.exists(download_dir2):
        os.makedirs(download_dir2)
        print("Created a temporary directory to store downloads\n\tPath: '" + download_dir2 +"'")
    if not os.path.exists(download_dir3):
        os.makedirs(download_dir3)
        print("Created a temporary directory to store downloads\n\tPath: '" + download_dir3 +"'")
    
    #Set first download directory 
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download":False,
        "directory_upgrade":True,
    }
    options = Options()
    options.add_argument("--headless=new")
    options.add_experimental_option("prefs", prefs)

    #Launch webdriver instance
    driver = webdriver.Chrome(options = options)
    driver.get("https://app.joltup.com/account#/login")
    time.sleep(3)            # Give time for dynamic elements to load  
    driver.find_element(By.ID, "emailAddress").send_keys(EMAIL)
    driver.find_element(By.ID, "password").send_keys(PASSWORD, Keys.ENTER)
    time.sleep(4)
    driver.get("https://app.joltup.com/review/review/listResultsReporting/gridView")
    time.sleep(6)           # Give time for dynamic elements to load 
    dateRange(driver, startDate, endDate)       # Set date range

    #Start downloading files listed in trainingListName
    print("\t~Downloading file for training lists")
    driver.execute_cdp_cmd('Page.setDownloadBehavior', {
        'behavior': 'allow',
        'downloadPath': download_dir
    })
    trainingListName = trainingListName.lower()
    list_of_titles = driver.find_elements(By.CLASS_NAME, "left-column-item-title")  #Gathers all list titles
    for t in list_of_titles:       #Find desired lists and download the CSV file
        title = t.find_element(By.TAG_NAME, "span").text.lower()
        if title in trainingListName: 
            t.click()
            time.sleep(3)
            driver.find_element(By.CLASS_NAME, "list-download").click()
            time.sleep(5)

    #Optional: Start downloading files listed in reqListName
    print("\t~Downloading file for request lists")
    if reqListName == None:
        return download_dir
    driver.execute_cdp_cmd('Page.setDownloadBehavior', {
        'behavior': 'allow',
        'downloadPath': download_dir2
    })
    reqListName = reqListName.lower()
    list_of_titles = driver.find_elements(By.CLASS_NAME, "left-column-item-title")  #Gathers all list titles
    for t in list_of_titles:        #Find desired lists and download the CSV file
        title = t.find_element(By.TAG_NAME, "span").text.lower()
        if title in reqListName: 
            t.click()
            time.sleep(3)
            driver.find_element(By.CLASS_NAME, "list-download").click()
            time.sleep(5)

    #Optional: Start downloading files matching reinforceListName
    print("\t~Downloading files for reinforcement lists")
    if reinforceListName == None:
        return download_dir, download_dir2
    driver.execute_cdp_cmd('Page.setDownloadBehavior', {
        'behavior': 'allow',
        'downloadPath': download_dir3
    })
    downloaded = False
    scores = []
    reinforceListName = reinforceListName.lower()
    list_of_titles = driver.find_elements(By.CLASS_NAME, "left-column-item-title")  #Gathers all list titles
    for t in list_of_titles:       #Find desired lists and download the CSV file
        title = t.find_element(By.TAG_NAME, "span").text.lower()
        if reinforceListName in title: 
            t.click()
            time.sleep(3)
            downloaded = True
            driver.find_element(By.CLASS_NAME, "list-download").click()
            time.sleep(5)

    #Pull Scores for each Checklists
    if(downloaded):
        driver.get('https://app.joltup.com/review/review/listResultsReporting/lists')
        time.sleep(5)
        driver.find_element(By.CSS_SELECTOR, '[title="List Template Title"]').click() 
        dateRange(driver, startDate, endDate)       # Set date range
        jolt_rows = driver.find_elements(By.CLASS_NAME, 'browse-lists-table-row')
        for row in jolt_rows:
            row_match = False
            for row_elements in row.find_elements(By.XPATH, './*'):
                element_text = row_elements.text.lower()
                if reinforceListName in element_text:
                    row_match = True
                if row_match and re.search(r'\([0-9.]{0,7}%\)', row_elements.text):
                    score = row_elements.text.split(" ")[1]
                    scores.append(score[1:-2])

    #Logout
    driver.get("https://app.joltup.com/site/logout")
    time.sleep(1.5)
    driver.close()
    print("Closed webdriver instance.\n")

    return download_dir, download_dir2, download_dir3, scores

#ISSUE: Correct value is entered, but site does not store it, leaving it to reset
def dateRange(driver, startDate, endDate):
    driver.find_element(By.CLASS_NAME, "date-range-filter").click() #Open up date range picker
    time.sleep(2)

    #Put in the start date
    start_field = driver.find_element(By.ID, "input-start")
    start_field.clear()
    start_field.send_keys(startDate)
    # Trigger focus event on another element to ensure the dates are registered
    driver.find_element(By.CLASS_NAME, "date-range-picker").click()
    time.sleep(1)

    #Put in the end date
    end_field = driver.find_element(By.ID, "input-end")
    end_field.clear()
    end_field.send_keys(endDate)
    # Trigger focus event on another element to ensure the dates are registered
    driver.find_element(By.CLASS_NAME, "date-range-picker").click()
    time.sleep(1)

    #Find and click on "Done" in the Date-Range picker menu
    buttons = driver.find_element(By.CLASS_NAME, "date-range-menu").find_element(By.CLASS_NAME, "button-row").find_elements(By.CLASS_NAME, "button")
    for button in buttons:
        span_text = button.find_element(By.TAG_NAME, "span").text
        if span_text.lower() == "done":
            button.click()
    time.sleep(5)
