# Parses Palo Alto GlobalProtect host logs to aid in troubleshooting. 
# Tested with Windows host logs, GlobalProtect App version 5.1.5.

from functools import reduce
import re
import sys
import matplotlib.pyplot as plt
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

latency_logs_available = False

if logType == 'Event_Log':
    # Regex to check for four digit year starting with '00' (assumed logging error).
    sub_pattern = re.compile(r'(\d\d\/\d\d\/)00(\d\d)')
    
    # Regex for 'pan_gp_event.log' columns.
    pattern = re.compile(r'(\d\d\/\d\d\/\d\d\d\d) (\d\d):(\d\d):(\d\d\.\d\d\d) \[(\w+)\s?\]: (.*)')
    
    # Substitute '00' for '20' if found in four digit year.
    subbedData = sub_pattern.sub(r'\g<1>20\g<2>', logData)
    
    # Make a list of tuples from 'subbedData' and create DataFrame.
    data = pattern.findall(subbedData)
    df = pd.DataFrame(data, columns = ['Date', 'HH', 'MM', 'SS.SSS', 'Type', 'LogOutput'])
else:
    # Regex for 'PanGPS.log' and 'PanGPA.log' columns.
    pattern = re.compile(r'(\(T\d+\))(\w+)\s*(\(\s*\d+\)):\s(\d\d\/\d\d\/\d\d)\s(\d\d):(\d\d):(\d\d:\d\d\d)\s(.*)')

    # Make a list of tuples from 'logData' and create DataFrame.
    data = pattern.findall(logData) 
    df = pd.DataFrame(data, columns = ['Code1', 'Type', 'Code2', 'Date', 'HH', 'MM', 'SS:SSS', 'LogOutput'])

    # Parse latency stats if available, compute Mean, Median, and plot by Datetime.
    if logType == 'GPS_Log':
        if not (df.query('Code2=="( 953)"').empty):
            # Get relevant columns for latency data and expand LogOutput column to Gateway and Latency.
            latency_logs_available = True
            gps_stats = df.loc[df.Code2 == '( 953)', ['Date','HH','MM','LogOutput']]
            gps_stats[['LogOutput','Latency']] = gps_stats['LogOutput'].str.split(' ', 1, expand=True)
            gps_stats.rename(columns={'LogOutput': 'Gateway'}, inplace=True)
            gps_stats['Latency'] = pd.to_numeric(gps_stats['Latency'].str.strip('ms'))
    
            # Get another DataFrame that excludes -1 ms latency.
            # Unclear on meaning of negative latency thus filtering this out from plotting but included separately in stats.
            gps_stats_exc = gps_stats.loc[gps_stats.Latency != -1, ['Date','HH','MM','Gateway','Latency']]
    
            # Compute stats with overall latency data and -1 filtered out, grouped by Gateway.
            overall_latency_mean = gps_stats.groupby(['Gateway']).mean()
            filtered_latency_mean = gps_stats_exc.groupby(['Gateway']).mean()

            overall_latency_median = gps_stats.groupby(['Gateway']).median()
            filtered_latency_median = gps_stats_exc.groupby(['Gateway']).median()
    
            # Merge stats into one table. 
            stats_dfs = [filtered_latency_mean, filtered_latency_median, overall_latency_mean, overall_latency_median]
            merged = reduce(lambda left,right: pd.merge(left,right, on=['Gateway'], how='outer', suffixes=('_Mean','_Median')), stats_dfs)
    
            # Concatenate Date and Time strings then format as Datetime for plotting.
            gps_stats_exc['Datetime'] = gps_stats_exc['Date'] + gps_stats_exc['HH'] + gps_stats_exc['MM']
            gps_stats_exc['Datetime'] = pd.to_datetime(gps_stats_exc.Datetime, format='%m/%d/%y%H%M').dt.strftime('%m/%d %H:%M')

            # Create subplots by Gateway for filtered Dataframe and plot Latency by Datetime.
            fig, ax = plt.subplots()
            for key, grp in gps_stats_exc.groupby(['Gateway']):
                ax = grp.plot(ax=ax, kind='line', x='Datetime', y='Latency', label=key)
            plt.legend(loc='best')

# Convert date format to display the year first for sorting.
df['Date'] = pd.to_datetime(df.Date).dt.date

# Allows LogOutput to be written to cell if it starts with '=' (otherwise detected as an Excel function).
df['LogOutput'] = df['LogOutput'].apply(lambda x: "'" + str(x) if str(x)[0] == '=' else x)

print('Summarized log output:\n')
print(df)
writer = pd.ExcelWriter('PyOut_' + logType + '.xlsx', engine='openpyxl')
df.to_excel(writer, logType)

if logType == 'GPS_Log':
    if latency_logs_available == True:
        print("\nLatency (ms) Mean and Median by Gateway (source data in 'Latency_Stats' sheet)\n1st Pair with -1 Filtered Out, 2nd Pair with -1 Included:\n")
        print(merged)
        gps_stats.to_excel(writer, 'Latency_Stats')
        merged.to_excel(writer, 'Latency_Stats', startcol=7)
    else:
        print('\nNo latency debug messages (Code2 953) in the log data, skipping latency statistics and plotting.')

print("\nFull parsed output saved as 'PyOut_" + logType + ".xlsx' in current path.")

if df.query('Type=="Error"').empty:
    print("No pivot table created because there were no Errors in the log data.")    
else:
    # Pivot on count of LogOutput Errors by Date.
    pivot_log_errors = pd.pivot_table(df[df.Type == 'Error'], index='LogOutput', columns='Date', values='Type', aggfunc='count', margins=True)
    pivot_log_errors.to_excel(writer, 'Pivot_Errors')
    print("'Pivot_Errors' sheet includes Pivot Table on the count of LogOutput Errors by Date.")

writer.save()
if latency_logs_available == True:
    plt.show()
