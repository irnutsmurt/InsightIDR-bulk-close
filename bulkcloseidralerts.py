import logging
import requests
import json
import getpass
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='bulkclose.log',
                    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

def get_new_alerts(api_key, from_date, to_date):
    insightidr_url = "https://us2.api.insight.rapid7.com/idr/v1/investigations"
    insightidr_headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Format dates to ISO format for the API request
    from_date_iso = from_date.isoformat() + "Z"
    to_date_iso = to_date.isoformat() + "Z"

    params = {
        "start_time": from_date_iso,
        "end_time": to_date_iso,
        "statuses": "OPEN"
    }

    logging.info("Fetching new alerts...")
    response = requests.get(insightidr_url, headers=insightidr_headers, params=params)

    if response.status_code != 200:
        logging.error(f"Failed to get investigations from InsightIDR: {response.reason}")
        return None

    # Save the raw response to a file
    with open('raw_alerts.json', 'w') as file:
        json.dump(response.json(), file, indent=4)

    investigations = response.json()['data']
    open_investigations_with_alerts = []
    for inv in investigations:
        # Use a default value for source if it's not present
        source = inv.get('source', 'UNKNOWN_SOURCE')
        if inv['status'] == 'OPEN':
            alert_type = inv['alerts'][0]['type'] if inv.get('alerts') else None
            open_investigations_with_alerts.append({
                'id': inv['id'],
                'title': inv['title'],
                'source': source,  # Include source
                'alert_type': alert_type
            })

    logging.info(f"Number of open alerts found: {len(open_investigations_with_alerts)}")
    return open_investigations_with_alerts

def post_alert_closure(api_key, from_date, to_date, source, alert_type=None):
    url = "https://us2.api.insight.rapid7.com/idr/v1/investigations/bulk_close"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "from": from_date.isoformat() + "Z",
        "to": to_date.isoformat() + "Z",
        "source": source
    }

    # Include alert_type only for ALERT source
    if source == "ALERT" and alert_type:
        data["alert_type"] = alert_type

    response = requests.post(url, headers=headers, json=data)
    # Log the response
    logging.info(f"Response Status Code: {response.status_code}")
    logging.info(f"Response Reason: {response.reason}")
    logging.info(f"Response Content: {response.text}")

    return response

def validate_date(date_input):
    if not date_input:
        return None, "Date cannot be blank."
    try:
        date_obj = datetime.strptime(date_input, "%Y-%m-%d")
        return date_obj, None
    except ValueError:
        return None, "Invalid date format. Please use the format YYYY-MM-DD."

def main():
    api_key = ""
    while True:
        if not api_key:
            api_key = getpass.getpass("Enter your API Key: ")
            if not api_key:
                logging.error("API Key cannot be blank. Please try again.")
                continue

        while True:
            from_date_input = input("Enter the start date (YYYY-MM-DD e.g., 2018-06-06): ")
            from_date, from_date_error = validate_date(from_date_input)
            if from_date_error:
                logging.error(from_date_error)
                continue

            to_date_input = input("Enter the end date (YYYY-MM-DD e.g., 2018-06-07): ")
            to_date, to_date_error = validate_date(to_date_input)
            if to_date_error:
                logging.error(to_date_error)
                continue

            if from_date > to_date:
                logging.error("Start date must be before the end date. Please try again.")
                continue

            break

        open_investigations = get_new_alerts(api_key, from_date, to_date)

        if not open_investigations:
            logging.info("No open investigations found.")
            while True:
                choice = input("Do you want to: \n1. Enter a different date range\n2. Exit\nEnter your choice (1 or 2): ")
                if choice not in ['1', '2']:
                    logging.error("Invalid choice. Please enter 1 or 2.")
                    continue
                break

            if choice == '2':
                logging.info("Exiting the script.")
                break
            continue

        logging.info("Menu: Do you want to close alerts?")
        while True:
            choice = input("Enter your choice (1, 2, or 3): ")
            if choice not in ['1', '2', '3']:
                logging.error("Invalid choice. Please enter 1, 2, or 3.")
                continue
            break

        total_closed_alerts = 0

        if choice == '1':
            # Group investigations by source
            investigations_by_source = {}
            for inv in open_investigations:
                source = inv.get('source', 'UNKNOWN')
                investigations_by_source.setdefault(source, []).append(inv)

            # Close investigations for each source
            for source, inv_list in investigations_by_source.items():
                alert_type = inv_list[0]['alert_type'] if source == "ALERT" else None
                response = post_alert_closure(api_key, from_date, to_date, source, alert_type)
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        num_closed = response_data.get('num_closed', 0)
                        total_closed_alerts += num_closed
                        logging.info(f"Closed {num_closed} {source} source investigations.")
                    except json.JSONDecodeError:
                        logging.error("Failed to parse response JSON.")
                else:
                    logging.error(f"Failed to close {source} source investigations.")

            logging.info(f"Total closed alerts: {total_closed_alerts}")

        elif choice == '2':
            while True:
                logging.info("Processing specific alert closures...")
                for i, inv in enumerate(open_investigations):
                    print(f"{i+1}. {inv['title']}")

                selected = input("Enter alert numbers to close (comma-separated, 0 to return to the main menu): ")
                selected_indices = [int(x.strip()) for x in selected.split(',') if x.strip().isdigit()]

                for idx in selected_indices:
                    if idx == 0:
                        break  # Break out of the loop to return to the main menu

                    if 1 <= idx <= len(open_investigations):
                        inv = open_investigations[idx-1]
                        source = inv.get('source', 'UNKNOWN')  # Define source here for each specific investigation
                        if inv['alert_type']:
                            response = post_alert_closure(api_key, from_date, to_date, source, inv['alert_type'])
                            if response.status_code == 200:
                                print(f"Successfully closed alert: {inv['title']}")
                            else:
                                print(f"Failed to close alert: {inv['title']}")
                        else:
                            print(f"Alert type missing for investigation: {inv['title']}")

                post_close_choice = input("\nDo you want to:\n1. Close other alerts\n2. Enter a different date range\n3. Exit\nEnter your choice (1, 2, or 3): ")
                if post_close_choice not in ['1', '2', '3']:
                    print("Invalid choice. Please enter 1, 2, or 3.")
                    continue
                if post_close_choice == '1':
                    continue
                elif post_close_choice == '2':
                    break
                elif post_close_choice == '3':
                    logging.info("Exiting the script.")
                    return

        elif choice == '3':
            logging.info("Exiting the script.")
            break

if __name__ == "__main__":
    main()