import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

SHEET_ID = "1P1f1rW4l1a_hRUGZMJdhkpm7PKenbBFKvV6p5rRjXPs"
sheet = client.open_by_key(SHEET_ID).sheet1


# ----------------------
# INIT HEADERS (AUTO)
# ----------------------
def init_sheet():
    expected = [
        "id", "name", "date", "start", "end",
        "hours", "technician", "assigned_by", "color"
    ]

    existing = sheet.row_values(1)

    if not existing or existing != expected:
        sheet.clear()
        sheet.append_row(expected)


# ----------------------
# GET DATA
# ----------------------
def get_all():
    return sheet.get_all_records()


# ----------------------
# APPEND ROW
# ----------------------
def append_row(row):
    sheet.append_row(row)
