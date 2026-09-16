import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# CONFIGURATION
# ============================================================

SHEET_NAME = "TaskBoard"

TASKS_WORKSHEET = "Tasks"
TECHNICIANS_WORKSHEET = "Technicians"
SETTINGS_WORKSHEET = "Settings"


TASK_HEADERS = [
    "id",
    "name",
    "date",
    "start",
    "end",
    "hours",
    "technician_id",
    "technician",
    "assigned_by",
    "status",
    "priority",
    "progress",
    "notes",
    "color",
]


TECHNICIAN_HEADERS = [
    "id",
    "name",
    "active",
]


SETTINGS_HEADERS = [
    "key",
    "value",
]


# ============================================================
# HELPERS
# ============================================================

def column_letter(number):
    result = ""

    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result

    return result


# ============================================================
# GOOGLE SHEETS CONNECTION
# ============================================================

@st.cache_resource
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


@st.cache_resource
def get_spreadsheet():
    return get_client().open(SHEET_NAME)


# ============================================================
# WORKSHEETS
# ============================================================

def get_or_create_worksheet(name, headers):
    spreadsheet = get_spreadsheet()

    try:
        worksheet = spreadsheet.worksheet(name)

    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=name,
            rows=1000,
            cols=max(len(headers), 10),
        )

    return worksheet


def get_task_worksheet():
    return get_or_create_worksheet(
        TASKS_WORKSHEET,
        TASK_HEADERS,
    )


def get_technician_worksheet():
    return get_or_create_worksheet(
        TECHNICIANS_WORKSHEET,
        TECHNICIAN_HEADERS,
    )


def get_settings_worksheet():
    return get_or_create_worksheet(
        SETTINGS_WORKSHEET,
        SETTINGS_HEADERS,
    )


# ============================================================
# HEADERS
# ============================================================

def ensure_headers(worksheet, required_headers):
    values = worksheet.get_all_values()

    if not values:
        end_column = column_letter(len(required_headers))

        worksheet.update(
            range_name=f"A1:{end_column}1",
            values=[required_headers],
        )

        return

    existing_headers = values[0]
    updated_headers = existing_headers.copy()

    for header in required_headers:
        if header not in updated_headers:
            updated_headers.append(header)

    if updated_headers != existing_headers:
        end_column = column_letter(len(updated_headers))

        worksheet.update(
            range_name=f"A1:{end_column}1",
            values=[updated_headers],
        )


# ============================================================
# INITIALIZE
# ============================================================

def init_sheet():
    task_sheet = get_task_worksheet()
    technician_sheet = get_technician_worksheet()
    settings_sheet = get_settings_worksheet()

    ensure_headers(
        task_sheet,
        TASK_HEADERS,
    )

    ensure_headers(
        technician_sheet,
        TECHNICIAN_HEADERS,
    )

    ensure_headers(
        settings_sheet,
        SETTINGS_HEADERS,
    )


# ============================================================
# TASKS
# ============================================================

def get_all():
    worksheet = get_task_worksheet()
    return worksheet.get_all_records()


def append_row(row):
    worksheet = get_task_worksheet()

    worksheet.append_row(
        row,
        value_input_option="USER_ENTERED",
    )

    return True


# ============================================================
# ROW LOOKUP
# ============================================================

def find_row_by_id(worksheet, item_id):
    ids = worksheet.col_values(1)

    for row_number, value in enumerate(ids, start=1):
        if str(value).strip() == str(item_id).strip():
            return row_number

    return None


# ============================================================
# GENERIC UPDATE
# ============================================================

def update_record(worksheet, item_id, data):
    row_number = find_row_by_id(
        worksheet,
        item_id,
    )

    if not row_number:
        return False

    headers = worksheet.row_values(1)

    updates = []

    for key, value in data.items():
        if key not in headers:
            continue

        column_number = headers.index(key) + 1
        column = column_letter(column_number)

        # Convert NaN to blank.
        try:
            if value != value:
                value = ""
        except Exception:
            pass

        # Convert bools to Google Sheets-friendly values.
        if isinstance(value, bool):
            value = "TRUE" if value else "FALSE"

        updates.append(
            {
                "range": f"{column}{row_number}",
                "values": [[value]],
            }
        )

    if updates:
        worksheet.batch_update(updates)

    return True


# ============================================================
# TASK UPDATE / DELETE
# ============================================================

def update_row(task_id, data):
    worksheet = get_task_worksheet()

    return update_record(
        worksheet,
        task_id,
        data,
    )


def delete_row(task_id):
    worksheet = get_task_worksheet()

    row_number = find_row_by_id(
        worksheet,
        task_id,
    )

    if not row_number:
        return False

    worksheet.delete_rows(row_number)

    return True


# ============================================================
# TECHNICIANS
# ============================================================

def get_technicians():
    worksheet = get_technician_worksheet()
    return worksheet.get_all_records()


def add_technician(
    technician_id,
    name,
    active=True,
):
    worksheet = get_technician_worksheet()

    worksheet.append_row(
        [
            technician_id,
            name,
            "TRUE" if active else "FALSE",
        ],
        value_input_option="USER_ENTERED",
    )

    return True


def update_technician(
    technician_id,
    data,
):
    worksheet = get_technician_worksheet()

    return update_record(
        worksheet,
        technician_id,
        data,
    )


# ============================================================
# SETTINGS
# ============================================================

def get_settings():
    worksheet = get_settings_worksheet()
    return worksheet.get_all_records()


def get_setting(key, default=""):
    """
    Return one value from the Settings worksheet.

    Expected worksheet:

    key                 value
    manager_password    example-password
    """

    worksheet = get_settings_worksheet()
    records = worksheet.get_all_records()

    wanted_key = str(key).strip()

    for record in records:
        record_key = str(
            record.get("key", "")
        ).strip()

        if record_key == wanted_key:
            return str(
                record.get("value", "")
            ).strip()

    return default
