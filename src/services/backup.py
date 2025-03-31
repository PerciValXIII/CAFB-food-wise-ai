import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from supabase import create_client, Client
from typing import List, Dict

# ------------------------------------------------------------------------------
# 1. Configuration
# ------------------------------------------------------------------------------
# Google Sheets
GOOGLE_SERVICE_ACCOUNT_FILE = "service_account.json"
SHEET_ID = "1q_EtF4lwFP2rNhLSIS58-kSGKzZtulyO3ETyzNmWb_E"
WORKSHEET_NAME = "main"  # or any tab name

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TABLE_NAME = "main2"

# Define the columns that exist in both DB and Sheet (in the same order in your Sheet header)
COLUMNS = [
    "district",
    "location",
    "direction_route",
    "width",
    "height",
    "area",
    "type",
    "rate_sqft_1_months",
    "rate_sqft_3_months",
    "rate_sqft_6_months",
    "rate_sqft_12_months",
    "floor",
    "hoarding_id",
    "hoarding_code",
    "status",
    "location_coordinates",
    "available",
    "lat",
    "long",
    "state",
    "available_date"
]


# ------------------------------------------------------------------------------
# 2. Supabase Client
# ------------------------------------------------------------------------------
def get_supabase_client() -> Client:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

# ------------------------------------------------------------------------------
# 3. Google Sheets Client
# ------------------------------------------------------------------------------
def get_worksheet():
    """
    Return the gspread Worksheet instance for the given SHEET_ID and WORKSHEET_NAME.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SERVICE_ACCOUNT_FILE, scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(WORKSHEET_NAME)
    return worksheet

# ------------------------------------------------------------------------------
# 4. Fetch Data from Supabase
# ------------------------------------------------------------------------------
def fetch_supabase_rows(supabase: Client) -> List[Dict]:
    """
    Fetch all rows from the Supabase table, return as a list of dictionaries.
    """
    resp = supabase.table(TABLE_NAME).select("*").execute()
    #resp = supabase.rpc("execute_sql", {"query": "SELECT * FROM public.main2 ORDER BY hoarding_id;"}).execute()
    if not resp:
        print("Error fetching from Supabase:", resp.data)
        return []

    return resp.data  # list of dicts

# ------------------------------------------------------------------------------
# 5. Write Data to Google Sheet
# ------------------------------------------------------------------------------
def write_data_to_sheet(worksheet, data: List[Dict]):
    """
    Clear the sheet and write the data into it using batch updates.
    """
    # Clear the worksheet
    worksheet.clear()

    # Prepare data for batch update
    all_rows = [COLUMNS]  # Start with the header row
    for row in data:
        all_rows.append([row.get(col, "") for col in COLUMNS])

    # Perform a batch update
    worksheet.update("A1", all_rows)


# ------------------------------------------------------------------------------
# 6. Main Logic
# ------------------------------------------------------------------------------
def sync_supabase_to_sheet():
    """
    Fetch everything from Supabase, clear the sheet, and write the data into the sheet.
    """
    supabase = get_supabase_client()
    worksheet = get_worksheet()

    # Fetch data from Supabase
    data = fetch_supabase_rows(supabase)
    if data:  # Check if there's data to sort
        data = sorted(data, key=lambda row: row.get("hoarding_id", 0))
    #print("data",data)

    # Write data to the Google Sheet
    write_data_to_sheet(worksheet, data)

    print("Sync complete! All Supabase data written to the sheet.")