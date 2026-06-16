import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------
# GOOGLE SHEETS SCOPE
# -----------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# -----------------------
# LOAD CREDENTIALS FROM STREAMLIT SECRETS
# -----------------------
creds_dict = st.secrets["gcp_service_account"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    scope
)

client = gspread.authorize(creds)

# -----------------------
# YOUR CORRECT SHEET ID
# -----------------------
SHEET_ID = "1P1f1rW4l1a_hRUGZMJdhkpm7PKenbBFKvV6p5rRjXPs"

# -----------------------
# OPEN SHEET SAFELY
# -----------------------
sheet = client.open_by_key(SHEET_ID).sheet1


# -----------------------
# INITIALIZE HEADERS (AUTO FIX)
# -----------------------
def init_sheet():
    values = sheet.get_all_values()

    if len(values) == 0:
        sheet.append_row([
            "id",
            "name",
            "date",
            "start",
            "end",
            "hours",
            "technician",
            "assigned_by",
            "color"
        ])


# -----------------------
# READ ALL DATA
# -----------------------
def get_all():
    return sheet.get_all_records()


# -----------------------
# APPEND NEW ROW
# -----------------------
def append_row(row):
    sheet.append_row(row)
