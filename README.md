## GPLogParser

Parses Palo Alto GlobalProtect host logs to aid in troubleshooting. Uses pandas dataframe to save parsed output to Excel workbook (PyOut\__LogType_.xlsx).

##### Workbook Sheets:
* _LogType_ (\* full parsed output)
* Pivot_Error (pivot table count of LogOutput Errors by Date)

\* XML log data which is variably interspersed depending on log event within PanGPS and PanGPA are excluded.

Accepts path (relative or absolute) of the log file intending to be parsed as a parameter during execution. Will automatically parse log if the passed log file name has an associated keyword. If a keyword from the log file name cannot be determined you will be prompted to select the log type:

| Default Name | Keyword (case-insensitive) |
| ------------ | ------- |
| pan\_gp_event.log | event |
| PanGPS.log | GPS |
| PanGPA.log | GPA |

##### Execution Example:
`python .\gp_log_parser.py .\pan_gp_event.log`

##### Prerequisite:
pandas

##### Reference to attain logs:
[GlobalProtect-Event-Log-for-Diagnosis](https://docs.paloaltonetworks.com/globalprotect/5-0/globalprotect-app-new-features/new-features-released-in-gp-agent-5_0/globalprotect-event-log-for-diagnosis.html)
