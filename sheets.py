import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔐 Load from Streamlit Secrets
creds_dict = st.secrets["gcp_service_account"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)
files = client.list_spreadsheet_files()

print("=== FILES VISIBLE TO SERVICE ACCOUNT ===")
for f in files:
    print(f["name"], f["id"])

sheet = client.open("TaskBoard").sheet1


def get_all():
    return sheet.get_all_records()


def append(row):
    sheet.append_row(row)
