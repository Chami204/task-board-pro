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

sheet = client.open_by_key(
    "1P1f1rW4l1a_hRUGZMJdhkpm7PKenbBFKvV6p5rRjXPs"
).sheet1


# ----------------------------
# AUTO CREATE HEADERS
# ----------------------------
HEADERS = [
    "id", "name", "date", "start", "end",
    "hours", "technician", "assigned_by", "color"
]

values = sheet.get_all_values()

if len(values) == 0:
    sheet.append_row(HEADERS)
elif values[0] != HEADERS:
    sheet.clear()
    sheet.append_row(HEADERS)


# ----------------------------
# GET ALL DATA
# ----------------------------
def get_all():
    return sheet.get_all_records()


# ----------------------------
# APPEND ROW
# ----------------------------
def append(row):
    sheet.append_row(row)
