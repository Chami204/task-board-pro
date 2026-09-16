import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# GOOGLE SHEET CONFIG
# ============================================================

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
    "status",
    "priority",
    "progress",
    "notes",
    "color",
]


# ============================================================
# GOOGLE CLIENT
# ============================================================

def get_client():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes,
    )

    return gspread.authorize(credentials)


# ============================================================
# GET SPREADSHEET
# ============================================================

def get_spreadsheet():

    client = get_client()

    spreadsheet = client.open(
        SHEET_NAME
    )

    return spreadsheet


# ============================================================
# GET WORKSHEET
# ============================================================

def get_worksheet():

    spreadsheet = get_spreadsheet()

    try:

        worksheet = spreadsheet.worksheet(
            WORKSHEET_NAME
        )

    except gspread.WorksheetNotFound:

        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME,
            rows=1000,
            cols=len(HEADERS),
        )

    return worksheet


# ============================================================
# INITIALIZE SHEET
# ============================================================

def init_sheet():

    worksheet = get_worksheet()

    values = worksheet.get_all_values()

    # --------------------------------------------------------
    # Completely empty worksheet
    # --------------------------------------------------------

    if not values:

        worksheet.update(
            range_name="A1:M1",
            values=[HEADERS],
        )

        return


    # --------------------------------------------------------
    # Existing worksheet
    # --------------------------------------------------------

    existing_headers = values[0]

    # Add any missing new columns without destroying
    # existing task data.

    new_headers = existing_headers.copy()

    for header in HEADERS:

        if header not in new_headers:
            new_headers.append(header)


    if new_headers != existing_headers:

        end_column = column_letter(
            len(new_headers)
        )

        worksheet.update(
            range_name=f"A1:{end_column}1",
            values=[new_headers],
        )


# ============================================================
# COLUMN LETTER
# ============================================================

def column_letter(number):

    result = ""

    while number:

        number, remainder = divmod(
            number - 1,
            26
        )

        result = (
            chr(65 + remainder)
            + result
        )

    return result


# ============================================================
# GET ALL TASKS
# ============================================================

def get_all():

    worksheet = get_worksheet()

    records = worksheet.get_all_records()

    return records


# ============================================================
# APPEND TASK
# ============================================================

def append_row(row):

    worksheet = get_worksheet()

    worksheet.append_row(
        row,
        value_input_option="USER_ENTERED",
    )


# ============================================================
# FIND ROW BY TASK ID
# ============================================================

def find_row_by_id(
    worksheet,
    task_id,
):

    ids = worksheet.col_values(1)

    # Row 1 is the header.
    for row_number, value in enumerate(
        ids,
        start=1,
    ):

        if str(value).strip() == str(
            task_id
        ).strip():

            return row_number

    return None


# ============================================================
# UPDATE TASK
# ============================================================

def update_row(
    task_id,
    data,
):

    worksheet = get_worksheet()

    row_number = find_row_by_id(
        worksheet,
        task_id,
    )

    if not row_number:
        return False


    headers = worksheet.row_values(1)

    # Build one batch update rather than repeatedly
    # writing individual cells.

    updates = []

    for key, value in data.items():

        if key not in headers:
            continue

        column_number = (
            headers.index(key) + 1
        )

        column = column_letter(
            column_number
        )

        # Handle pandas NaN values.
        try:
            if value != value:
                value = ""
        except Exception:
            pass

        updates.append({
            "range": (
                f"{column}{row_number}"
            ),
            "values": [[value]],
        })


    if updates:

        worksheet.batch_update(
            updates
        )

    return True


# ============================================================
# DELETE TASK
# ============================================================

def delete_row(task_id):

    worksheet = get_worksheet()

    row_number = find_row_by_id(
        worksheet,
        task_id,
    )

    if not row_number:
        return False

    worksheet.delete_rows(
        row_number
    )

    return True
