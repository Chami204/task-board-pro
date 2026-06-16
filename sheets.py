import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit secrets
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)

client = gspread.authorize(creds)

SHEET_ID = "1P1f1rW4l1a_hRUGZMJdhkpm7PKenbBFKvV6p5rRjXPs"
sheet = client.open_by_key(SHEET_ID).sheet1


# -----------------------
# INIT HEADERS (auto fix)
# -----------------------
def init_sheet():
    headers = [
        "id", "name", "date", "start", "end",
        "hours", "technicians", "assigned_by", "color"
    ]

    existing = sheet.row_values(1)

    if not existing:
        sheet.append_row(headers)


# -----------------------
# GET ALL TASKS
# -----------------------
def get_all():
    records = sheet.get_all_records()

    # ensure safe output
    for r in records:
        if "technicians" not in r:
            r["technicians"] = ""

    return records


# -----------------------
# ADD TASK
# -----------------------
def append_row(row):
    sheet.append_row(row)
