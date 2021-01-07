import re
import sys
import pandas as pd

with open(sys.argv[1], 'r') as logFile:
    logData = logFile.read()

# Only retain file name portion of passed in log file.
sub_path = re.compile(r'.*[\\\/]')
fname = sub_path.sub('', sys.argv[1].lower())

# Detect keyword in file name to determine log type, otherwise ask for type.
if ('event' in fname) and (('gps' not in fname) and ('gpa' not in fname)):
    logType = 'Event_Log'
elif ('gps' in fname) and (('event' not in fname) and ('gpa' not in fname)):
    logType = 'GPS_Log'
elif ('gpa' in fname) and (('event' not in fname) and ('gps' not in fname)):
    logType = 'GPA_Log'
else:
    selections = "Enter a number for your log file type:\n(1) pan_gp_event.log\n(2) PanGPS.log\n(3) PanGPA.log\n> "

    logNumInput = input("Log file name did not include a log file keyword ('event', 'GPS', or 'GPA').\n"
                        "Or multiple keywords were found.\n\n" + selections)
    while logNumInput not in ['1', '2', '3']:
        logNumInput = input("Invalid Response\n\n" + selections)

    logType = {'1': 'Event_Log',
               '2': 'GPS_Log',
               '3': 'GPA_Log'}.get(logNumInput)

if logType == 'Event_Log':
    # Regex for two digit year substitution.
    sub_pattern = re.compile(r'(\d\d\/\d\d\/)\d\d(\d\d)')
    
    # Regex for 'pan_gp_event.log' columns.
    pattern = re.compile(r'(\d\d\/\d\d\/\d\d) (\d\d):(\d\d):(\d\d\.\d\d\d) \[(\w+)\s?\]: (.*)')
    
    # Change four digit year to two.
    subbedData = sub_pattern.sub(r'\1\2', logData)
    
    # Make a list of tuples from 'subbedData' and create DataFrame.
    data = pattern.findall(subbedData)
    df = pd.DataFrame(data, columns = ['Date', 'HH', 'MM', 'SS.SSS', 'Type', 'LogOutput'])
else:
    # Regex for 'PanGPS.log' and 'PanGPA.log' columns.
    pattern = re.compile(r'(\(T\d+\))(\w+)\s*(\(\s*\d+\)):\s(\d\d\/\d\d\/\d\d)\s(\d\d):(\d\d):(\d\d:\d\d\d)\s(.*)')

    # Make a list of tuples from 'logData' and create DataFrame.
    data = pattern.findall(logData) 
    df = pd.DataFrame(data, columns = ['Code1', 'Type', 'Code2', 'Date', 'HH', 'MM', 'SS:SSS', 'LogOutput'])

print('Summarized log output:\n')
print(df)

writer = pd.ExcelWriter('PyOut_' + logType + '.xlsx')
df.to_excel(writer, logType)

print("\nFull parsed output saved as 'PyOut_" + logType + ".xlsx' in current path.")

if df.query('Type=="Error"').empty:
    print("No pivot table created because there were no Errors in the log data.")    
else:
    # Pivot on count of LogOutput Errors by Date.
    pivot_log_errors = pd.pivot_table(df[df.Type == 'Error'], index='LogOutput', columns='Date', values='Type', aggfunc='count', margins=True)
    pivot_log_errors.to_excel(writer, 'Pivot_Errors')
    print("Second sheet includes Pivot Table on the count of LogOutput Errors by Date.")

writer.save()
