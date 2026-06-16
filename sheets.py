import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------
# AUTH SETUP
# -----------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

# -----------------------
# SHEET CONNECTION
# -----------------------
SHEET_ID = "1P1f1rW4l1a_hRUGZMJdhkpm7PKenbBFKvV6p5rRjXPs"
sheet = client.open_by_key(SHEET_ID).sheet1


# -----------------------
# INIT HEADERS (SAFE)
# -----------------------
def init_sheet():
    headers = sheet.row_values(1)

    required = [
        "id", "name", "date", "start", "end",
        "hours", "technician", "assigned_by", "color"
    ]

    # If empty sheet or missing headers → set them
    if not headers or headers != required:
        sheet.clear()
        sheet.append_row(required)


# -----------------------
# GET ALL DATA
# -----------------------
def get_all():
    return sheet.get_all_records()


# -----------------------
# APPEND NEW TASK
# -----------------------
def append_row(row):
    sheet.append_row(row)


# -----------------------
# UPDATE TASK (USED FOR DRAG & DROP)
# -----------------------
def update_row(task_id, updates):
    """
    updates example:
    {
        "date": "2026-06-16",
        "start": "10:00",
        "end": "12:00"
    }
    """

    data = sheet.get_all_records()
    headers = sheet.row_values(1)

    for i, row in enumerate(data, start=2):  # row 2 = first data row
        if str(row["id"]) == str(task_id):

            for key, value in updates.items():
                if key in headers:
                    col = headers.index(key) + 1
                    sheet.update_cell(i, col, value)

            return True

    return False
