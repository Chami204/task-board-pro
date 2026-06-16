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


# -----------------------
# INIT HEADERS
# -----------------------
def init_sheet():
    if sheet.row_count == 0:
        sheet.append_row([
            "id", "name", "date", "start", "end",
            "hours", "technician", "assigned_by", "color"
        ])


def get_all():
    data = sheet.get_all_records()
    return data


def append_row(row):
    sheet.append_row(row)
