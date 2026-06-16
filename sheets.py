import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = st.secrets["gcp_service_account"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(
    "1P1f1rW4l1a_hRUGZMJdhkpm7PKenbBFKvV6p5rRjXPs"
).sheet1


# Create headers automatically if sheet is empty
HEADERS = [
    "id",
    "name",
    "date",
    "start",
    "end",
    "hours",
    "technician",
    "assigned_by",
    "color"
]

if len(sheet.get_all_values()) == 0:
    sheet.append_row(HEADERS)


def get_all():
    return sheet.get_all_records()


def append(row):
    sheet.append_row(row)
