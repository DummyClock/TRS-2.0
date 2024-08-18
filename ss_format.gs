// Time Triggered function (9am Everyday)
function formatSS(){
  // Sort Request Sheets
    autoSort("Training Requests")
    autoSort("Retraining Requests")

  // Sort Skill Board Sheets
    const ss = SpreadsheetApp.getActiveSpreadsheet()
    const ws = ss.getSheetByName("Skill Board")
    sortByOneColumn(ws.getDataRange().offset(1, 0), 1) 
}

// Time Triggered function (12pm on the 1st of the month)
function deleteOutdatedRequest(sheetName){
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName)
  const data = sheet.getDataRange().getValues()
  const header = data[0]

  // Find indecies for header columns
  var fulfill_col = header.indexOf("Fulfilled")
  var request_date_col = header.indexOf("Request Date")

  for (let i = data.length-1; i >= 0; --i){
    date = data[i][request_date_col]
    month = date.toString().split(" ")[1]
    monthNum = getMonthNum(month)
    var valid = checkDate(monthNum)
    if (valid)
    {
      sheet.deleteRow(i+1)
    }
  }

}

// Sorts the requests sheets by the Fulfilled col & Request Date col
function autoSort(sheetName) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName)
  const data = sheet.getDataRange().getValues()
  const header = data[0]

  // Find indecies for header columns
  var fulfill_col = header.indexOf("Fulfilled")
  //var emp_col = header.indexOf("Employee Name")
  //var pos_col = header.indexOf("Requested Position")
  var request_date_col = header.indexOf("Request Date")

  // Autosort
  sortByTwoColumns(sheet.getDataRange().offset(1, 0), fulfill_col+1, request_date_col+1)
}

function checkDate(month){
  var monthOffset = 4;
  var today = new Date();
  var todayMonth = today.getMonth() + 1; 
  //Logger.log("Month: " + today.getMonth())

  if (todayMonth < month)
    todayMonth = todayMonth + 12
  
  var diff_in_month = todayMonth - month
  if (diff_in_month >= monthOffset)
    return true
  else
    return false
}

function getMonthNum(month){
  var monthNum;
  switch(month) {
    case "Jan":
      monthNum = 1;
      break;
    case "Feb":
      monthNum = 2;
      break;
    case "Mar":
      monthNum = 3;
      break;
    case "Apr":
      monthNum = 4;
      break;
    case "May":
      monthNum = 5;
      break;
    case "Jun":
      monthNum = 6;
      break;
    case "Jul":
      monthNum = 7;
      break;
    case "Aug":
      monthNum = 8;
      break;
    case "Sep":
      monthNum = 9;
      break;
    case "Oct":
      monthNum = 10;
      break;
    case "Nov":
      monthNum = 11;
      break;
    case "Dec":
      monthNum = 12;
      break;
    default:
      monthNum = "Invalid month";
      break;
  }

  return monthNum
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
