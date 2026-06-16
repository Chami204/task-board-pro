import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔐 Load credentials ONLY from Streamlit secrets
creds_dict = st.secrets["gcp_service_account"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    scope
)

client = gspread.authorize(creds)

# ✅ IMPORTANT: use your sheet ID (NOT name)
SHEET_ID = "YOUR_SHEET_ID"

sheet = client.open_by_key(1P1f1rW4l1a_hRUGZMJdhkpm7PKenbBFKvV6p5rRjXPs).sheet1


# -----------------------
# INIT HEADERS AUTOMATICALLY
# -----------------------
def init_sheet():
    if sheet.row_count == 0 or sheet.get_all_values() == []:
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
# READ
# -----------------------
def get_all():
    return sheet.get_all_records()


# -----------------------
# WRITE
# -----------------------
def append_row(row):
    sheet.append_row(row)
