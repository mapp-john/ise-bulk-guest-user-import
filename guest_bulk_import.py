import requests
import csv
import getpass
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# Prompt user for Cisco ISE API details and CSV file path
ISE_HOST = input("Enter Cisco ISE Host (e.g., https://ise-hostname-or-ip): ").strip()
API_USERNAME = input("Enter API Username: ").strip()
API_PASSWORD = getpass.getpass("Enter API Password: ").strip()
CSV_FILE_PATH = input("Enter path to CSV file with guest users: ").strip()
PORTAL_ID = input("Enter portal ID for ISE Sponsor Portal: ").strip()

# API endpoint for bulk creating guest users
url_bulk = f"{ISE_HOST}/ers/config/guestuser/bulk/submit"

# Headers for the API request
headers = {
    "Content-Type": "application/vnd.com.cisco.ise.identity.guestuser.2.0+xml",
    "Accept": "application/vnd.com.cisco.ise.identity.guestuser.2.0+xml",
}

# Namespace URIs
NS4 = "identity.ers.ise.cisco.com"
NS5 = "trustsec.ers.ise.cisco.com"
NS6 = "sxp.ers.ise.cisco.com"
NS7 = "anc.ers.ise.cisco.com"
NS8 = "network.ers.ise.cisco.com"
ERS = "ers.ise.cisco.com"
XS = "http://www.w3.org/2001/XMLSchema"


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def build_guest_user_xml(guest_users):
    # Create root element with namespaces and attributes (no ET.register_namespace calls)
    root = Element(
        f"{{{NS4}}}guestUserBulkRequest",
        {
            "operationType": "create",
            "resourceMediaType": "vnd.com.cisco.ise.identity.guestuser.2.0+xml",
            "xmlns:ns6": NS6,
            "xmlns:ns5": NS5,
            "xmlns:ns8": NS8,
            "xmlns:ns7": NS7,
            "xmlns:ers": ERS,
            "xmlns:xs": XS,
            "xmlns:ns4": NS4,
        },
    )

    resources_list = SubElement(root, f"{{{NS4}}}resourcesList")

    for user in guest_users:
        guestuser = SubElement(resources_list, f"{{{NS4}}}guestuser")
        guestuser.attrib["xmlns:ns0"] = "identity.ers.ise.cisco.com"

        # Add child elements under ns4:guestuser
        custom_fields = SubElement(guestuser, f"customFields")
        # Add required empty <customFields> element to satisfy schema
        custom_fields.text = " "

        # Add child elements under ns4:guestuser
        guest_access_info = SubElement(guestuser, f"guestAccessInfo")

        # Add child elements under guestAccessInfo
        start_date = SubElement(guest_access_info, f"fromDate")
        start_date.text = user["fromDate"]
        end_date = SubElement(guest_access_info, f"location")
        end_date.text = "San Jose"
        end_date = SubElement(guest_access_info, f"toDate")  # e.g. 07/22/2025 23:59
        end_date.text = user["toDate"]
        end_date = SubElement(guest_access_info, f"validDays")
        end_date.text = "1"

        # Add child elements under ns4:guestuser
        guest_info = SubElement(guestuser, f"guestInfo")

        # Add child elements under guestInfo
        email_address = SubElement(guest_info, f"emailAddress")
        email_address.text = user["emailAddress"]
        enabled = SubElement(guest_info, f"enabled")
        enabled.text = "true"
        first_name = SubElement(guest_info, f"firstName")
        first_name.text = user["firstName"]
        last_name = SubElement(guest_info, f"lastName")
        last_name.text = user["lastName"]
        password = SubElement(guest_info, f"password")
        password.text = user["password"]
        user_name = SubElement(guest_info, f"userName")
        user_name.text = user["userName"]

        # Add child elements under ns4:guestuser
        guest_type = SubElement(guestuser, f"guestType")
        guest_type.text = user.get("guestType", "Sponsor-Defined")
        portal_id = SubElement(guestuser, f"portalId")
        portal_id.text = PORTAL_ID

    return prettify_xml(root)


def read_guest_users_from_csv(csv_file_path):
    guest_users = []
    with open(csv_file_path, mode="r", newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Expecting CSV columns: userName, emailAddress, password, guestType, startDate, endDate
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


def bulk_create_guest_users_xml(xml_data):
    response = requests.put(
        url_bulk, auth=(API_USERNAME, API_PASSWORD), headers=headers, data=xml_data, verify=False
    )  # Set verify=True with valid certs
    if response.status_code == 202:
        print("Bulk guest users created successfully.")
    else:
        print(f"Failed to create bulk guest users. Status code: {response.status_code}")
        print(f"Response: {response.text}")


if __name__ == "__main__":
    guest_users_list = read_guest_users_from_csv(CSV_FILE_PATH)
    xml_payload = build_guest_user_xml(guest_users_list)
    # print("Generated XML Payload:")
    # print(xml_payload)
    bulk_create_guest_users_xml(xml_payload)
