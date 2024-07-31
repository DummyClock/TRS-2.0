import os
import pandas as pd
import gspread
import time
import json
import requests
from google.oauth2.service_account import Credentials
from datetime import date
from gspread.exceptions import APIError
from gspread import cell
from email_handler import sendHTMLEmail

MAX_API_REQUEST = 15

#from auth import SPREADSHEET_ID, SKILL_SHEET_ID, REG_REQUEST_ID, RETRAIN_REQUEST_ID, WEBHOOK_URL
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
SKILL_SHEET_ID = os.environ['SKILL_SHEET_ID']
REG_REQUEST_ID = os.environ['REG_REQUEST_ID']
RETRAIN_REQUEST_ID = os.environ['RETRAIN_REQUEST_ID']
WEBHOOK_URL = os.environ['WEBHOOK_URL']

# Will search the downloaded csv files in path for specific values (assuming the files are for Training Reports)
def readReportFiles(path, client):
    # Values to search for within the downloaded csv files
    training_type_value = "Which training was conducted?"
    trainer_value = 'Trainer'
    trainee_value = 'Trainee'
    date_value = "Date"
    pos_value = 'Position Trainee was Trained On'
    rating_value = 'Please rate the Trainee 1-5 (Use the rubric above)'
    summ_value = 'Please provide a summary of the shift. (Please highlight the positive and your concerns).'
    email_request_value = "Would you like to email the trainee?"
    email_value = 'Trainee Email'
    email_body_value = 'Optional: Advice & Feedback for Trainee'

    #Loop through files in directory
    downloadedFiles = os.listdir(path)
    skillChartBatch = []
    for f in downloadedFiles:
        # Convert csv file into dataframe
        file_path = os.path.join(path, f)
        df = pd.read_csv(file_path).T
        new_header = df.iloc[0]  
        df = df[1:]  
        df.columns = new_header  
        
        # Get the columns indicies for specific header values
        #print(df.columns)
        training_type_col = df.columns.get_loc(training_type_value)
        trainer_value_col = df.columns.get_loc(trainer_value)
        trainee_value_col = df.columns.get_loc(trainee_value)
        date_value_col =  df.columns.get_loc(date_value)
        pos_value_col = df.columns.get_loc(pos_value)
        rating_value_col = df.columns.get_loc(rating_value)
        summ_value_col = df.columns.get_loc(summ_value)
        email_request_col = df.columns.get_loc(email_request_value)
        email_value_col = df.columns.get_loc(email_value)
        email_body_value_col = df.columns.get_loc(email_body_value)

        # Read each row for specific values & perform processed
        api_request = 0
        for rows in range(df.shape[0]):
            #Fix Name Format in dataframe to be: Last, First
            name=df.iloc[rows,trainee_value_col].split()
            df.iloc[rows,trainee_value_col] = name[1] + ", " + name[0]

            #Update the skill chart
            updateSkillChart(df.iloc[rows,trainee_value_col], df.iloc[rows,pos_value_col], df.iloc[rows,rating_value_col], client)
            api_request += 2

            #Check which type of training was conducted and check it off from one of the Request sheets
            if df.iloc[rows,training_type_col] == "Initial Training":
                sheet_id = REG_REQUEST_ID
            else:                                # Assume Retraining
                sheet_id = RETRAIN_REQUEST_ID
            checkRequestSheet(df.iloc[rows,trainee_value_col],df.iloc[rows,pos_value_col], sheet_id, client)     # If a request was fulfilled, if so check it off
            api_request += 2
                    
            #Slack Message
            #slackMsg(str(df.iloc[rows,trainer_value_col]), str(df.iloc[rows,trainee_value_col]), str(df.iloc[rows,pos_value_col]), str(df.iloc[rows,summ_value_col]), str(df.iloc[rows,email_body_value_col]))

            #Email Trainee (if requested)
            if df.iloc[rows, email_request_col] == "YES":
                print("Attempting to send email.")
                headers = [df.iloc[rows,trainee_value_col], df.iloc[rows,trainer_value_col], df.iloc[rows,pos_value_col], df.iloc[rows,email_body_value_col]]
                trainer_data = ["Trainee", "Trainer","Position", "Shift Summary"]
                sendHTMLEmail(headers,trainer_data,df.iloc[rows, email_value_col])
            else:
                print("Email was not requested.")

            if api_request > MAX_API_REQUEST:
                print("Too many API request made. Taking a quick minute break...")
                api_request = 0
                time.sleep(60)

    #return removeDupCleaningTasks(important_results)
    #sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(SKILL_SHEET_ID)
    #sheet.format(skillChartBatch)
    #sheet.format('I6', {'backgroundColor': {'red': 0.0, 'green': 0.0, 'blue': 0.0}})
    return skillChartBatch

# Will search the downloaded csv files in path for specific values (assuming the files are for Requests)
def readRequestFiles(path, client):
    # Values to search for within the downloaded csv files
    training_type_value = "What type of training are you requesting?"
    requestor_value = 'Who is filling out this Request'
    trainee_value = 'Employee to be Trained'
    pos_value = 'Request Position'
    details_value = 'Reasons for Request'

    #Loop through files in directory
    downloadedFiles = os.listdir(path)
    training_requests_batch = []
    retraining_requests_batch = []
    for f in downloadedFiles:
        # Convert csv file into dataframe
        file_path = os.path.join(path, f)
        df = pd.read_csv(file_path).T
        new_header = df.iloc[0]  
        df = df[1:]  
        df.columns = new_header  

        #Get column indicies
        training_type_col = df.columns.get_loc(training_type_value)
        requestor_col = df.columns.get_loc(requestor_value)
        trainee_col = df.columns.get_loc(trainee_value)
        pos_col = df.columns.get_loc(pos_value)
        details_col = df.columns.get_loc(details_value)

        # Read each row for specific values & perform processed
        try:
            api_error = True
            api_error_counter = 3

            #While loop checks for api failure
            while api_error and api_error_counter > 0:
                api_error = False
                training_request_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(REG_REQUEST_ID)
                retraining_request_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(RETRAIN_REQUEST_ID)
                all_values = training_request_sheet.get_all_values()
                retraining_all_values = retraining_request_sheet.get_all_values()
        except APIError as e:
                # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
                api_error = apiTimeOut(api_error_counter)
                api_error_counter -= 1

        headers = all_values[0]
        next_empty_row = len(all_values)+1  
        r_next_empty_row = len(retraining_all_values)+1

        
        for rows in range(df.shape[0]):
            #Fix Name Format in dataframe to be: Last, First
            name=df.iloc[rows,trainee_col].split()
            df.iloc[rows,trainee_col] = name[1] + ", " + name[0]

            #Append Batch for the Row
            ss_column_indicies= [headers.index("Request Date")+1, headers.index("Employee Name")+1, headers.index("Requested Position")+1, headers.index("Fulfilled")+1, headers.index("Reasons for Request")+1, headers.index("Requested By")+1]
            values = [date.today().strftime("%m/%d/%Y").split()[0], df.iloc[rows,trainee_col], df.iloc[rows,pos_col], "--INSERT-CB--",df.iloc[rows, details_col], df.iloc[rows, requestor_col]]

            #Set sheet id based on sent data
            if df.iloc[rows,training_type_col] == "Request Training":
                training_requests_batch.extend(formatRequestBatch(next_empty_row, ss_column_indicies, values))
                next_empty_row += 1
            else:
                retraining_requests_batch.extend(formatRequestBatch(next_empty_row, ss_column_indicies, values))
                r_next_empty_row += 1
    
        #print(training_requests_batch)
        try:
            api_error = True
            api_error_counter = 3

            #While loop checks for api failure
            while api_error and api_error_counter > 0:
                training_request_sheet.batch_update(training_requests_batch, value_input_option="USER_ENTERED")
                retraining_request_sheet.batch_update(retraining_requests_batch, value_input_option="USER_ENTERED")
        except APIError as e:
                # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
                api_error = apiTimeOut(api_error_counter)
                api_error_counter -= 1
  
        # Call Google Scripts File to insert checkboxes & sort both sheets
        web_app_url = 'https://script.google.com/macros/s/AKfycbxXKXtYg1sSq4V4Ldi7Faul7DtJfzmiyht-qq3R0eftlWzlaOHPmz53SsF0aHdh-U_6/exec'
        try:
            api_error = True
            api_error_counter = 3

            #While loop checks for api failure
            while api_error and api_error_counter > 0:
                api_error = False
                params = {
                        'process': '1',
                    }
                response = requests.get(web_app_url, params=params)
                print(response.text)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
            api_error = apiTimeOut(api_error_counter)
            api_error_counter -= 1

    return

# Send a slack message documenting completed training/retraining reports
def slackMsg(trainer, pupil, pos, details, feedback):
    # Replace this URL with your Slack Incoming Webhook URL
    webhook_url = WEBHOOK_URL

    msg = "*Heads up  <!channel>, a New Report is Available!*\n\n*" + trainer + "* just Submitted a Training Report!\n>Date: " + str(date.today()) + "\n\t• Trainee: *" + pupil + "*\n\t• Position: *" + pos + "*\n" 
    msg = msg + "\n----------------------------------------------\n>*Feedback given by Trainer " + trainer + "*\n\t•"+ feedback +"\n"
    msg = msg + ">\n\n*>Thoughts from " + trainer + "*\n```" + details + "```\n" + "\n:chicken: *Excellent job, " + trainer + "! Thank you for your hard work!* :chicken:"

    # Define the message payload
    message = {
        'text': msg,
    }

    # Send the message
    response = requests.post(
        webhook_url,
        data=json.dumps(message),
        headers={'Content-Type': 'application/json'}
    )

    # Check if the request was successful
    if response.status_code == 200:
        print('Message posted successfully.')
    else:
        print(f'Failed to post message. Status code: {response.status_code}')
        print(f'Response text: {response.text}')

# Updates the Skill Chart within Google Sheets to keep track of what positions employees know
def updateSkillChart(trainee_name, position, rating, client):
 #Store results pulled from csv file
    # Read each row for specific values & perform processed
        #Fail Safe for API Failure
        try:
            api_error = True
            api_error_counter = 3
            #While loop checks for api failure
            while api_error and api_error_counter > 0:
                #Build format request for Skill Chart
                api_error = False
                skillChartBatch=rowBatchForSkillChart(trainee_name, position, rating, client, SKILL_SHEET_ID)
            
                #Batch Add Rows to Initial Training 
                #print(skillChartBatch)
                sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(SKILL_SHEET_ID)
                sheet.format(skillChartBatch[0], skillChartBatch[1])
        except APIError as e:
                # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
                api_error = apiTimeOut(api_error_counter)
                api_error_counter -= 1

# When a training session is completed, check if there was a request associated with this training and mark it off
def checkRequestSheet(trainee_name, position, sheet_id, client):
    #Get Sheet
    #Fail Safe for API Failure
    try:
        api_error = True
        api_error_counter = 3    
        while api_error and api_error_counter > 0:
            api_error = False
            sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(sheet_id)
            all_data = sheet.get_all_values()

            empHeader = all_data[0].index("Employee Name")
            posHeader = all_data[0].index("Requested Position")
            fulHeader = all_data[0].index("Fulfilled")

            for ss_row in all_data:
                #print("-",reformatted_name, df.iloc[rows,trainee_value_col])
                if ss_row[empHeader] == trainee_name and ss_row[posHeader] == position and ss_row[fulHeader] == 'FALSE':
                    print("Hit")
                    sheet.update_cell(all_data.index(ss_row)+1, fulHeader+1, "TRUE")
                    break
    except APIError as e:
                # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
                api_error = apiTimeOut(api_error_counter)
                api_error_counter -= 1

# INCOMPLETE: Doesn't update based on the rating of the employee
# Returns a batch for the cell to color in; this'll document that the trainee has learned a new position
def rowBatchForSkillChart(trainee, pos, rating, client, sheet_id):
    #Fail Safe for API Failure
    api_error = True
    api_error_counter = 3
    while api_error and api_error_counter > 0:
        try:
            #Get Sheet
            api_error = False
            sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(sheet_id)
            rows = sheet.get_all_values()

            #Find column
            col = rows[0].index(pos)

            #Find Row w/ matching trainee name & Edit (INCOMPLETE)
            found = False
            row_count = 0
            for row in rows:
                if row[0] == trainee:
                    found = True
                    break
                row_count += 1
            row_count += 1

            #If not found, add new row
            if not found:
                print("Trainee in Skill Chart not found. Adding a new entry for them...")
                sheet.update_cell(row_count, 1, trainee)

            color = {"red": 0,"green": 0,"blue": 80}
            
            return (cell.Cell(row_count, col+1).address, {'backgroundColor': {"red": color['red'], "green": color['green'], "blue": color['blue']}})
        except APIError as e:
            # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
            api_error = apiTimeOut(api_error_counter)
            api_error_counter -= 1
            print(e)

def formatSkillChartBatch(row, columns, color):
    #print(cell.Cell(row-1, columns).address)
    return (cell.Cell(row, columns).address, {'backgroundColor': {"red": color['red'], "green": color['green'], "blue": color['blue']}})
                                                                          
def formatRequestBatch(row, columns, values):
    a1_notation = {}
    for i in range(len(columns)):
        a1_notation[cell.Cell(row, columns[i]).address] = values[i]
    return [{'range': c, 'values':[[value]]} for c, value in a1_notation.items()]


# Removes a cleaning task that has a more recent date
def removeDupCleaningTasks(list_of_dictionaries):
    for dic in list_of_dictionaries:
        for d in list_of_dictionaries:
            if dic.values() == d.values():
                continue
            elif dic["Area/Descriptor"] in d.values() and dic["Task"] == d.values():
                list_of_dictionaries.remove(dic)
                continue
    #print(len(list_of_dictionaries))
    return list_of_dictionaries

def apiTimeOut(api_error_counter):
    # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
    if api_error_counter > 0: 
        print("Minute Quota for Google Sheets API reached (CLEANING_SPREADSHEET). Will attempt to access again. \n\tPlease wait a moment...\n\tAttempts Left: " + str(api_error_counter))
        time.sleep(66)  
    else:
        print("Unable to Google Sheets API right now. Skipping this process.")
    return True




"""#Testing code
from auth import SERVICE_KEY_JSON_FILE, SPREADSHEET_ID
SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/script.external_request', 'https://www.googleapis.com/auth/script.projects']
creds = Credentials.from_service_account_info(SERVICE_KEY_JSON_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
path = os.path.dirname(os.path.realpath(__file__)) + '\\tmp_reports'
path2 = os.path.dirname(os.path.realpath(__file__)) + '\\tmp_requests'

readReportFiles(path, client)
readRequestFiles(path2, client)
#test()"""
