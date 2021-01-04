### GPLogParser

Parses Palo Alto GlobalProtect host logs to aid in troubleshooting. Saves parsed output to Excel workbook (GP_Log_PyOut.xlsx):

Sheets:
1. GP Log (full parsed output)
2. Pivot - Error (count of LogOutput Errors by Date)

Accepts below logs as command line input. Will automatically parse associated log if the passed log file name has an associated keyword.

Accepted Logs:
Default name - Keyword
pan_gp_event.log - event
PanGPA.log - GPA
PanGPS.log - GPS
