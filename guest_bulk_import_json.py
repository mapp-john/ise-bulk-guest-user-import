import requests
import csv
import getpass
import json

# Prompt user for Cisco ISE API details and CSV file path
ISE_HOST = input("Enter Cisco ISE Host (e.g., https://ise-hostname-or-ip): ").strip()
API_USERNAME = input("Enter API Username: ").strip()
API_PASSWORD = getpass.getpass("Enter API Password: ").strip()
CSV_FILE_PATH = input("Enter path to CSV file with guest users: ").strip()
PORTAL_ID = input("Enter portal ID for ISE Sponsor Portal: ").strip()

# API endpoint for creating individual guest users
url_single = f"{ISE_HOST}/ers/config/guestuser"

# Headers for the API request using JSON content type
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def build_guest_user_json(user):
    """
    Build the JSON payload for creating a single guest user.
    """
    guestuser = {
        "GuestUser": {
            "customFields": {},  # Required empty object to satisfy schema
            "guestAccessInfo": {
                "fromDate": user["fromDate"],
                "location": "San Jose",
                "toDate": user["toDate"],
                "validDays": 1,
            },
            "guestInfo": {
                "emailAddress": user["emailAddress"],
                "enabled": True,
                "firstName": user["firstName"],
                "lastName": user["lastName"],
                "password": user["password"],
                "userName": user["userName"],
            },
            "guestType": user.get("guestType", "Sponsor-Defined"),
            "portalId": PORTAL_ID,
        }
    }
    return json.dumps(guestuser, indent=2)


def read_guest_users_from_csv(csv_file_path):
    guest_users = []
    with open(csv_file_path, mode="r", newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Expecting CSV columns: userName, emailAddress, password, guestType, fromDate, toDate
            guest_user = {
                "firstName": row["firstName"],
                "lastName": row["lastName"],
                "userName": row["userName"],
                "emailAddress": row["emailAddress"],
                "password": row["password"],
                "guestType": row.get("guestType", "Sponsor-Defined"),
                "fromDate": row["fromDate"],  # e.g. 07/21/2025 00:00
                "toDate": row["toDate"],  # e.g. 07/22/2025 23:59
            }
            guest_users.append(guest_user)
    return guest_users


def create_guest_user(user_json):
    response = requests.post(
        url_single, auth=(API_USERNAME, API_PASSWORD), headers=headers, data=user_json, verify=False
    )  # Set verify=True with valid certs
    return response


if __name__ == "__main__":
    guest_users_list = read_guest_users_from_csv(CSV_FILE_PATH)
    for idx, user in enumerate(guest_users_list, start=1):
        json_payload = build_guest_user_json(user)
        print(f"Creating guest user {idx}/{len(guest_users_list)}: {user['userName']}")
        response = create_guest_user(json_payload)
        if response.status_code == 201:
            print(f"Guest user '{user['userName']}' created successfully.")
        else:
            print(
                f"Failed to create guest user '{user['userName']}'. Status code: {response.status_code}"
            )
            print(f"Response: {response.text}")
