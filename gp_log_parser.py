import re
import sys
import pandas as pd

with open(sys.argv[1], 'r') as logFile:
    if ('event' in sys.argv[1]) and (('GPS' not in sys.argv[1]) or ('GPA' not in sys.argv[1])):
        logType = 'event'
    elif ('GPS' in sys.argv[1]) and (('event' not in sys.argv[1]) or ('GPA' not in sys.argv[1])):
        logType = 'gps'
    elif ('GPA' in sys.argv[1]) and (('event' not in sys.argv[1]) or ('GPS' not in sys.argv[1])):
        logType = 'gpa'
    else:
        print("* Log file name did not include a log file keyword ('event', 'GPS', or 'GPA').\n"
              "Or multiple keywords were found.\n\n"
              "Enter a number for your log file type:\n"
              "(1) pan_gp_event.log\n"
              "(2) PanGPS.log\n"
              "(3) PanGPA.log")
    logData = logFile.read()

if logType == 'event':
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
    # Regex for 'PanGPS.log' columns.
    pattern = re.compile(r'(\(T\d+\))(\w+)\s*(\(\s*\d+\)):\s(\d\d\/\d\d\/\d\d)\s(\d\d):(\d\d):(\d\d:\d\d\d)\s(.*)')

    # Make a list of tuples from 'logData' and create DataFrame.
    data = pattern.findall(logData) 
    df = pd.DataFrame(data, columns = ['Code1', 'Type', 'Code2', 'Date', 'HH', 'MM', 'SS:SSS', 'LogOutput'])

print('Summarized log output:\n')
print(df)

# Pivot on count of LogOutput Errors by Date.
# * check for case where there are no erros to pivot on
pivot_log_errors = pd.pivot_table(df[df.Type == 'Error'], index='LogOutput', columns='Date', values='Type', aggfunc='count')

writer = pd.ExcelWriter('GP_Log_PyOut.xlsx')
df.to_excel(writer, 'GP Log')
pivot_log_errors.to_excel(writer, 'Pivot - Errors')
writer.save()

print("\nFull parsed output saved as 'GP_Log_PyOut.xlsx' in current path.\n"
      "Second sheet includes Pivot Table on the count of LogOutput Errors by Date.")
