import os, gspread, time, json, requests, pandas as pd
from google.oauth2.service_account import Credentials
from datetime import date
from gspread.exceptions import APIError, GSpreadException
from gspread import cell
from email_handler import sendHTMLEmail

MAX_API_REQUEST = 15
num_of_new_trainees = 0

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
    trainer_value = 'Trainer (You)'
    trainee_value = 'Trainee (Student)'
    date_value = "Date"
    pos_value = 'Position Trainee was Trained On'
    rating_value = 'Please rate the Trainee 1-5 (Use the rubric above)'
    summ_value = 'Please provide a summary of the shift. (Please highlight the positive and your concerns).'
    email_request_value = "Would the trainee like to be emailed a training report?"
    pref_lang_value = "Trainee's Preferred Language"
    email_value = 'Trainee Email'
    email_body_value = 'Advice & Feedback for Trainee'

    """sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(sheet_id)
    all_request_data = sheet.get_all_values()"""

    #Loop through files in directory
    downloadedFiles = os.listdir(path)
    skillChartBatch = []
    requestBatch = []
    for f in downloadedFiles:
        # Convert csv file into dataframe
        file_path = os.path.join(path, f)
        df = pd.read_csv(file_path).T.drop_duplicates()
        new_header = df.iloc[0]  
        df = df[1:]  
        df.columns = new_header  
        
        # Get the columns indicies for specific header values
        training_type_col = df.columns.get_loc(training_type_value)
        trainer_value_col = df.columns.get_loc(trainer_value)
        trainee_value_col = df.columns.get_loc(trainee_value)
        date_value_col =  df.columns.get_loc(date_value)
        pos_value_col = df.columns.get_loc(pos_value)
        rating_value_col = df.columns.get_loc(rating_value)
        summ_value_col = df.columns.get_loc(summ_value)
        email_request_col = df.columns.get_loc(email_request_value)
        pref_lang_col = df.columns.get_loc(pref_lang_value)
        email_value_col = df.columns.get_loc(email_value)
        email_body_value_col = df.columns.get_loc(email_body_value)

        # Attempt to Gather All 3 sheet values
        api_error = True
        api_error_counter = 3
        while api_error and api_error_counter > 0:
            try:
                api_error = False
                ss = client.open_by_key(SPREADSHEET_ID)
                skill_sheet = ss.get_worksheet_by_id(SKILL_SHEET_ID)
                all_skill_rows = skill_sheet.get_all_values()

                all_request_rows = ss.get_worksheet_by_id(REG_REQUEST_ID).get_all_values()
                all_retrain_rows = ss.get_worksheet_by_id(RETRAIN_REQUEST_ID).get_all_values()
                api_request = 4
            except (APIError, GSpreadException) as e:
                # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
                print("Timeout 1")
                api_error = apiTimeOut(api_error_counter)
                api_error_counter -= 1

        # Read each row for specific values & perform processes
        for rows in range(df.shape[0]):
            #Skip if missing data exists (only checks trainee name)
            if df.iloc[rows,trainee_value_col] == "--":
                continue

            #Fix Name Format in dataframe to be: Last, First
            name=df.iloc[rows,trainee_value_col].split()
            df.iloc[rows,trainee_value_col] = name[1] + ", " + name[0]

            #Build the batch for the skill chart
            skillChartBatch.append(rowBatch_sc(df.iloc[rows,trainee_value_col], df.iloc[rows,pos_value_col], df.iloc[rows,rating_value_col], all_skill_rows, SKILL_SHEET_ID))

            #Check which type of training 
            if df.iloc[rows,training_type_col] == "Initial Training":
                all_data = all_request_rows
                sheet_id = REG_REQUEST_ID
            else:                                # Assume Retraining
                all_data = all_retrain_rows
                sheet_id = RETRAIN_REQUEST_ID
            
            #Check if a request was fulfilled
            request = checkRequestSheet(df.iloc[rows,trainee_value_col],df.iloc[rows,pos_value_col], all_data, sheet_id) 
            if request[0]:              # If a request was fulfilled, check it off; otherwise skip
                requestBatch.append(request[1])
                    
            #Slack Message
            #slackMsg(str(df.iloc[rows,trainer_value_col]), str(df.iloc[rows,trainee_value_col]), str(df.iloc[rows,pos_value_col]), str(df.iloc[rows,summ_value_col]), str(df.iloc[rows,email_body_value_col]))

            #Set language encoding
            if df.iloc[rows,pref_lang_col] == "Spanish":
                lang = 'es'
            else:
                lang = 'en'
            
            #Email Trainee (if requested)
            if df.iloc[rows, email_request_col] == "YES":
                print("Attempting to send email.")
                headers = [df.iloc[rows,trainee_value_col], df.iloc[rows,trainer_value_col], df.iloc[rows,pos_value_col], df.iloc[rows,email_body_value_col]]
                trainer_data = ["Trainee", "Trainer","Position", "Shift Summary"]
                sendHTMLEmail(headers,trainer_data,df.iloc[rows, email_value_col], lang)
            else:
                print("Email was not requested.")

    #Comit batch update in Request Charts
    if len(requestBatch) != 0:
        body = {'requests': requestBatch}
        ss.batch_update(body=body)

    #Commit batch update in Skill Chart
    if len(skillChartBatch) != 0:
        body = {'requests': skillChartBatch}
        ss.batch_update(body=body)
        #ss.get_worksheet_by_id(SKILL_SHEET_ID).sort((1, 'asc'))       # Sort

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
        df = pd.read_csv(file_path).T.drop_duplicates()
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
        #While loop checks for api failure
        api_error = True
        api_error_counter = 3
        while api_error and api_error_counter > 0:
            try:
                api_error = False
                training_request_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(REG_REQUEST_ID)
                retraining_request_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(RETRAIN_REQUEST_ID)
                all_values = training_request_sheet.get_all_values()
                retraining_all_values = retraining_request_sheet.get_all_values()
            except (APIError, GSpreadException) as e:
                    # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
                    print("Timeout a")
                    api_error = apiTimeOut(api_error_counter)
                    api_error_counter -= 1

        #Get number of rows in both sheets
        next_empty_row = len(all_values)+1  
        r_next_empty_row = len(retraining_all_values)+1

        # Read each row for specific values & perform processes
        for rows in range(df.shape[0]):
            if df.iloc[rows,trainee_col] == "--":
                continue

            #Fix Name Format in dataframe to be: Last, First
            #print(df.iloc[rows, trainee_col]) comment out (prints trainees full name)
            name=df.iloc[rows,trainee_col].split()
            df.iloc[rows,trainee_col] = name[1] + ", " + name[0]

            #Get headers
            headers = all_values[0]

            #Append Batch for the Row
            date_col_ws =  headers.index("Request Date")+1
            ss_column_indicies= [date_col_ws, headers.index("Employee Name")+1, headers.index("Requested Position")+1, headers.index("Fulfilled")+1, headers.index("Reasons for Request")+1, headers.index("Requested By")+1]
            values = [date.today().strftime("%m/%d/%Y").split()[0], df.iloc[rows,trainee_col], df.iloc[rows,pos_col], "---",df.iloc[rows, details_col], df.iloc[rows, requestor_col]]

            #Set sheet id based on sent data
            if df.iloc[rows,training_type_col] == "Request Training":
                training_requests_batch.extend(formatRequestBatch(next_empty_row, ss_column_indicies, values))
                next_empty_row += 1
            else:
                retraining_requests_batch.extend(formatRequestBatch(next_empty_row, ss_column_indicies, values))
                r_next_empty_row += 1
    
        #While loop checks for api failure
        api_error = True
        api_error_counter = 3
        while api_error and api_error_counter > 0:
            try:
                api_error = False
                training_request_sheet.batch_update(training_requests_batch, value_input_option="USER_ENTERED")
                retraining_request_sheet.batch_update(retraining_requests_batch, value_input_option="USER_ENTERED")
            except (APIError, GSpreadException) as e:
                # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
                print("Timeout b")
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

# When a training session is completed, check if there was a request associated with this training and mark it off
def checkRequestSheet(trainee_name, position, all_data, sheet_id):

            #Get header indecies
            empHeader = all_data[0].index("Employee Name")
            posHeader = all_data[0].index("Requested Position")
            fulHeader = all_data[0].index("Fulfilled")

            row_count = 0
            for ss_row in all_data:
                if ss_row[empHeader] == trainee_name and ss_row[posHeader] == position and ss_row[fulHeader] == '---':
                    print("Found match in request sheets")
                    return (True, (
                        {
                        "updateCells": {
                            "rows": [{
                                "values": [{
                                    "userEnteredValue": 
                                    {
                                        "formulaValue": '=IMAGE("https://raw.githubusercontent.com/DummyClock/TRS-2.0/main/misc/Checkmark.png")'
                                    }
                                }]
                            }],
                            "fields": "userEnteredValue",
                            "start": {
                                "sheetId": sheet_id,
                                "rowIndex": row_count,
                                "columnIndex": fulHeader
                                }
                            }
                        }
                    ))
                row_count += 1
            #If Search unsuccesful
            return (False, ())

# Returns a batch for the cell to color in; this'll document that the trainee has learned a new position
def rowBatch_sc(trainee, pos, rating, rows, sheet_id):
            # Set the color based on the rating
            color = getColor(rating)

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
                print("Trainee in Skill Chart not found. Preparing a new entry for them...")
                global num_of_new_trainees 
                num_of_new_trainees = num_of_new_trainees + 1
                row_count = row_count + num_of_new_trainees
                #print(trainee)
                #print(num_of_new_trainees, row_count)
                return {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_count-2,
                            "endRowIndex": row_count-1,
                            "startColumnIndex": 0,
                            "endColumnIndex": 1
                        },
                        "cell": {
                            "userEnteredValue": {
                                "stringValue": trainee
                            }
                        },
                        "fields": "userEnteredValue"
                    }
                },{
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_count - 2,
                            "endRowIndex": row_count - 1,
                            "startColumnIndex": col,
                            "endColumnIndex": col + 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": color['red'],
                                    "green": color['green'],
                                    "blue": color['blue']
                                }
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                        }
                    }
                

#-----------Return dict request (if found)
            return {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_count-1,
                            "endRowIndex": row_count,
                            "startColumnIndex": col,
                            "endColumnIndex": col+1
                                },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": color['red'],
                                    "green": color["green"],
                                    "blue": color["blue"]
                                }
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                }

def getColor(rating):
    if rating == '1' or rating == '2':
        return {"red": 50,"green": 0,"blue": 0}             # Red
    elif rating == '3' or rating == '4':
        return {"red": 1,"green": 0.647,"blue": 0}          # Orange
    elif rating == '5':
        return {"red": 1,"green": 1,"blue": 0}              # Yellow

    
    # Default (Error)
    print("Color for rating not found")
    return {"red": 0,"green": 0,"blue": 0}

"""WILL USE FOR REINFORCEMENT REPORT
    if rating == '1':
        return {"red": 50,"green": 0,"blue": 0}             # Red
    elif rating == '2':
        return {"red": 1,"green": 0.647,"blue": 0}          # Orange
    elif rating == '3':
        return {"red": 1,"green": 1,"blue": 0}              # Yellow
    elif rating == '4':
        return {"red": 0,"green": 0,"blue": 10}             # Blue
    elif rating == '5':
        return {"red": 0,"green": 10,"blue": 0}             # Green
                                                            # Missing Dark Green  
"""
                                                                              
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

# Function that handles timeouts for an api error
def apiTimeOut(api_error_counter):
    # If API Error occurs, reattempt to access Google Sheets API (MAX ATTEMPS = 3)
    if api_error_counter > 0: 
        print("Minute quota for Google Sheets API reached. Will attempt to access again. \n\tPlease wait a moment...\n\tAttempts left: " + str(api_error_counter))
        time.sleep(66)  
    else:
        print("Unable to Google Sheets API right now. Skipping this process.")
    return True




#Testing code
if __name__ == "__main__":
    from auth import SERVICE_KEY_JSON_FILE, SPREADSHEET_ID
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/script.external_request', 'https://www.googleapis.com/auth/script.projects']
    creds = Credentials.from_service_account_info(SERVICE_KEY_JSON_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    path = os.path.dirname(os.path.realpath(__file__)) + '\\tmp_reports'
    path2 = os.path.dirname(os.path.realpath(__file__)) + '\\tmp_requests'

    readReportFiles(path, client)
    readRequestFiles(path2, client)
