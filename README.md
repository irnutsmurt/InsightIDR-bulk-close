# InsightIDR-bulk-close
This script is designed to interact with the InsightIDR API to fetch and close alerts within a specified date range. Users can choose to close all alerts or select specific alerts to close. The script includes error handling and logging functionalities for efficient tracking and debugging.

## Requirements
* Python 3.x
* requests library

## Setup
Install the required library:
```
pip install -r requirements.txt
```

Configure the script with the appropriate url as needed as your url may use different regions. The url https://us2.api.insight.rapid7.com/idr/v1/investigations you'd replace the us2 with whatever your region is. You can find this when you use the insightidr console.
```
def get_new_alerts(api_key, from_date, to_date):
    insightidr_url = "https://us2.api.insight.rapid7.com/idr/v1/investigations"
    insightidr_headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
```
And
```
def post_alert_closure(api_key, from_date, to_date, source, alert_type=None):
    url = "https://us2.api.insight.rapid7.com/idr/v1/investigations/bulk_close"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
```

## Usage
Run the script from the command line:
```
python bulkcloseidralerts.py
```

The script will prompt you to:
* Enter your API Key.
* Enter the start and end dates for the date range.
* Choose to close all open alerts within the specified time frame, specific alerts, or exit the script.

### Logging
The script generates a log file (bulkclose.log) to record the operations, status messages, and any errors encountered during the execution.

## Notes
* Ensure your API key has the necessary permissions to access and modify the InsightIDR investigations.
* Date inputs must be in the format YYYY-MM-DD.
* The script includes validation checks for user inputs and date formats.
