//Spreadsheet ID
const spreadsheetId = "INSERT SPREADSHEET ID HERE"

function doGet(e){
  var process = e.parameter.process;
  if(process == '1'){
    formatRequestSheet("Training Requests")
    formatRequestSheet("Retraining Requests")

    const sheet = SpreadsheetApp.openById(spreadsheetId).getSheetByName("Skill Board")
    sortByOneColumn(sheet.getDataRange().offset(1, 0, sheet.getLastRow() - 1), 1)
  }
  if(process == '2'){
    //var pupil = e.parameter.pupil;
    //var trainer = e.parameter.trainer;
    //var position = e.parameter.position;
    //var details = e.parameter.details;
    //var feedback = e.parameter.feedback;
    //var slack_msg = e.parameter.slack_msg;
    //generateSlackMessage("Training", 'pupil', 'trainer', 'position', 'details', 'feedback', 'slack_msg')
    no()
  }

  // Return a simple response for debugging
  return ContentService.createTextOutput('Request processed');
}

function formatRequestSheet(sheetName) {
  const sheet = SpreadsheetApp.openById(spreadsheetId).getSheetByName(sheetName)
  const data = sheet.getDataRange().getValues()
  const header = data[0]

  // Find indecies for header columns
  var fulfill_col = header.indexOf("Fulfilled")
  var emp_col = header.indexOf("Employee Name")
  var pos_col = header.indexOf("Requested Position")
  var request_date_col = header.indexOf("Request Date")

  // Search for --INSERT-CB--' inside the sheet
  for(var i=0; (i < data.length); i++)
  {
    if(data[i][fulfill_col] == '--INSERT-CB--'){
      sheet.getRange(i+1, fulfill_col+1).clear()
      sheet.getRange(i+1, fulfill_col+1).insertCheckboxes() // replace text with checkboxes
    }
  }

  // Autosort
  sortByTwoColumns(sheet.getDataRange().offset(1, 0, sheet.getLastRow() - 1), fulfill_col+1, request_date_col+1)
}

/**
 * A function that sorts a sheet by a single, specified column (higest to lowest)
 * @param {} range The range of cells you wish to sort. 
 *    (Note: Ideally, you'd want to sort by all the cells. So you'd use "something like ws.getDataRange().offset(1, 0, ws.getLastRow() - 1)"
 * @param {int} col The column number you wish to sort the sheet by. 
 *    (Note: The count starts at 1, not 0. Therefore, Column A can be referenced by '1')
 */
function sortByOneColumn(range, col)
{
  range.sort([{column: col, ascending: true}])
}

/**
 * A function that sorts a sheet by two specified columns. 
 * @param {Range} range The range of cells you wish to sort. 
 *    (Note: Ideally, you'd want to sort by all the cells. So you'd use "something like ws.getDataRange().offset(1, 0, ws.getLastRow() - 1)"
 * @param {int} col1 The column number you wish to sort the sheet by. 
 *    (Note: The count starts at 1, not 0. Therefore, Column A can be referenced by '1')
 * @param {int} col2 The column number you wish to sort the sheet by. 
 *    (Note: The count starts at 1, not 0. Therefore, Column A can be referenced by '1')
 */
function sortByTwoColumns(range, col1, col2)
{
  range.sort([{column: col1, ascending: true}, {column: col2, ascending: true}])
}


