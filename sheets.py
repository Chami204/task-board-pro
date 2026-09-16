import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


SHEET_NAME = "TaskBoard"
WORKSHEET_NAME = "Tasks"

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


def get_client():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )

    return gspread.authorize(credentials)


def get_worksheet():

    client = get_client()

    spreadsheet = client.open(SHEET_NAME)

    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME,
            rows=1000,
            cols=20
        )

    return worksheet


def init_sheet():

    worksheet = get_worksheet()

    values = worksheet.get_all_values()

    if not values:
        worksheet.append_row(HEADERS)

    elif values[0] != HEADERS:
        # Keeps your sheet structure predictable
        worksheet.update(
            range_name="A1:I1",
            values=[HEADERS]
        )


def get_all():

    worksheet = get_worksheet()

    records = worksheet.get_all_records()

    return records


def append_row(row):

    worksheet = get_worksheet()

    worksheet.append_row(
        row,
        value_input_option="USER_ENTERED"
    )


def find_row_by_id(worksheet, task_id):

    ids = worksheet.col_values(1)

    for row_number, value in enumerate(ids, start=1):

        if str(value) == str(task_id):
            return row_number

    return None


def update_row(task_id, data):

    worksheet = get_worksheet()

    row_number = find_row_by_id(
        worksheet,
        task_id
    )

    if not row_number:
        return False

    header = worksheet.row_values(1)

    for key, value in data.items():

        if key not in header:
            continue

        column_number = header.index(key) + 1

        worksheet.update_cell(
            row_number,
            column_number,
            str(value)
        )

    return True


def delete_row(task_id):

    worksheet = get_worksheet()

    row_number = find_row_by_id(
        worksheet,
        task_id
    )

    if not row_number:
        return False

    worksheet.delete_rows(row_number)

    return True
