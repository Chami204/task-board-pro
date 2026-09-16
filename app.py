import streamlit as st
import pandas as pd
import uuid
import hmac

from datetime import datetime, date, timedelta

from streamlit_calendar import calendar

from sheets import (
    init_sheet,
    get_all,
    append_row,
    update_row,
    delete_row,
    get_technicians,
    add_technician,
    update_technician,
    get_setting,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="R&D Project Tracker",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CONSTANTS
# ============================================================

STATUSES = [
    "Pending",
    "In Progress",
    "Completed",
    "On Hold",
    "Cancelled",
]

TECHNICIAN_STATUSES = [
    "Pending",
    "In Progress",
    "Completed",
    "On Hold",
]

PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Urgent",
]

DEFAULT_COLOR = "#1E7E8C"

TASK_COLUMNS = [
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


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.block-container {
    padding-top: 1rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

.stButton > button,
.stFormSubmitButton > button {
    border-radius: 10px;
    min-height: 44px;
    font-weight: 600;
}

div[data-testid="stMetric"] {
    border: 1px solid rgba(128,128,128,0.22);
    border-radius: 12px;
    padding: 12px;
}

/* Mobile */

@media (max-width: 768px) {

    .block-container {
        padding-top: 0.5rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
        padding-bottom: 2rem;
    }

    h1 {
        font-size: 1.40rem !important;
    }

    h2 {
        font-size: 1.18rem !important;
    }

    h3 {
        font-size: 1.02rem !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        width: 100%;
        min-height: 48px;
    }

    button[data-baseweb="tab"] {
        font-size: 0.72rem !important;
        padding: 8px 4px !important;
    }

}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# INITIALIZE GOOGLE SHEETS
# ============================================================

@st.cache_resource
def initialize_database():
    init_sheet()
    return True


try:
    initialize_database()

except Exception as e:
    st.error("Unable to connect to Google Sheets.")
    st.exception(e)
    st.stop()


# ============================================================
# HELPERS
# ============================================================

def safe_date(value):
    try:
        return datetime.strptime(
            str(value).strip(),
            "%Y-%m-%d",
        ).date()

    except (ValueError, TypeError):
        return None


def safe_float(value, default=0.0):
    try:
        return float(value)

    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    try:
        return int(float(value))

    except (ValueError, TypeError):
        return default


def is_active_value(value):
    return (
        str(value)
        .strip()
        .lower()
        in [
            "true",
            "1",
            "yes",
            "active",
        ]
    )


def status_icon(status):
    return {
        "Pending": "🕓",
        "In Progress": "🔄",
        "Completed": "✅",
        "On Hold": "⏸️",
        "Cancelled": "❌",
    }.get(str(status), "📌")


def priority_icon(priority):
    return {
        "Low": "🟢",
        "Medium": "🟡",
        "High": "🟠",
        "Urgent": "🔴",
    }.get(str(priority), "⚪")


# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data(show_spinner=False)
def load_tasks():
    records = get_all()

    data = pd.DataFrame(records)

    for column in TASK_COLUMNS:
        if column not in data.columns:
            data[column] = ""

    data = data[TASK_COLUMNS].copy()

    if not data.empty:
        string_columns = [
            "id",
            "name",
            "date",
            "start",
            "end",
            "technician_id",
            "technician",
            "assigned_by",
            "status",
            "priority",
            "notes",
            "color",
        ]

        for column in string_columns:
            data[column] = (
                data[column]
                .fillna("")
                .astype(str)
            )

        data["hours"] = pd.to_numeric(
            data["hours"],
            errors="coerce",
        ).fillna(0.0)

        data["progress"] = pd.to_numeric(
            data["progress"],
            errors="coerce",
        ).fillna(0)

        data.loc[
            data["status"].str.strip() == "",
            "status",
        ] = "Pending"

        data.loc[
            data["priority"].str.strip() == "",
            "priority",
        ] = "Medium"

        data.loc[
            data["color"].str.strip() == "",
            "color",
        ] = DEFAULT_COLOR

    return data


@st.cache_data(show_spinner=False)
def load_technicians():
    records = get_technicians()

    data = pd.DataFrame(records)

    required = [
        "id",
        "name",
        "active",
    ]

    for column in required:
        if column not in data.columns:
            data[column] = ""

    data = data[required].copy()

    if not data.empty:
        data["id"] = (
            data["id"]
            .fillna("")
            .astype(str)
        )

        data["name"] = (
            data["name"]
            .fillna("")
            .astype(str)
        )

        data["active"] = (
            data["active"]
            .apply(is_active_value)
        )

    return data


@st.cache_data(show_spinner=False)
def load_manager_password():
    return get_setting(
        "manager_password",
        "",
    )


# ============================================================
# REFRESH
# ============================================================

def refresh_all_data():
    load_tasks.clear()
    load_technicians.clear()
    load_manager_password.clear()


# ============================================================
# FLASH MESSAGES
# ============================================================

def set_flash(message):
    st.session_state["flash_message"] = message


def show_flash():
    message = st.session_state.pop(
        "flash_message",
        None,
    )

    if message:
        st.success(message)


# ============================================================
# LOAD DATA
# ============================================================

try:
    df = load_tasks()
    technicians_df = load_technicians()

except Exception as e:
    st.error("Unable to load tracker data.")
    st.exception(e)
    st.stop()


# ============================================================
# TECHNICIANS
# ============================================================

if technicians_df.empty:
    active_technicians_df = pd.DataFrame(
        columns=[
            "id",
            "name",
            "active",
        ]
    )

else:
    active_technicians_df = (
        technicians_df[
            technicians_df["active"] == True
        ]
        .copy()
        .sort_values("name")
    )


ACTIVE_TECH_NAMES = (
    active_technicians_df["name"]
    .tolist()
)


ALL_TECH_NAMES = sorted(
    set(
        technicians_df["name"].tolist()
        +
        df["technician"].tolist()
    )
    -
    {""}
)


# ============================================================
# DATES
# ============================================================

today = date.today()

week_start = (
    today
    -
    timedelta(
        days=today.weekday()
    )
)

week_end = (
    week_start
    +
    timedelta(days=6)
)


if not df.empty:
    valid_dates = df["date"].apply(
        safe_date
    )

else:
    valid_dates = pd.Series(
        index=df.index,
        dtype="object",
    )


# ============================================================
# HEADER
# ============================================================

header_col, refresh_col = st.columns(
    [4, 1]
)


with header_col:
    st.title(
        "🛠️ R&D Project Tracker"
    )

    st.caption(
        "TaskBoard • Project and technician tracking"
    )


with refresh_col:
    st.write("")

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):
        refresh_all_data()

        set_flash(
            "All data refreshed from Google Sheets."
        )

        st.rerun()


show_flash()


# ============================================================
# DASHBOARD SELECTOR
# ============================================================

dashboard_mode = st.radio(
    "Dashboard",
    [
        "🔧 Technician",
        "👔 Manager",
    ],
    horizontal=True,
)


st.divider()


# ============================================================
# TECHNICIAN DASHBOARD
# ============================================================

if dashboard_mode == "🔧 Technician":

    st.header(
        "🔧 Technician Dashboard"
    )

    st.caption(
        "Select your name to view and update your work."
    )


    if not ALL_TECH_NAMES:
        st.warning(
            "No technicians are available."
        )

        st.stop()


    selected_technician = st.selectbox(
        "Who are you?",
        ALL_TECH_NAMES,
        key="technician_name",
    )


    technician_tasks = df[
        df["technician"]
        == selected_technician
    ].copy()


    if technician_tasks.empty:
        st.success(
            "You currently have no assigned tasks."
        )

        st.stop()


    technician_tasks["_date"] = (
        technician_tasks["date"]
        .apply(safe_date)
    )


    # --------------------------------------------------------
    # GROUP TASKS
    # --------------------------------------------------------

    today_tech_tasks = technician_tasks[
        technician_tasks["_date"] == today
    ].copy()


    upcoming_tech_tasks = technician_tasks[
        (
            technician_tasks["_date"] > today
        )
        &
        (
            ~technician_tasks["status"].isin(
                [
                    "Completed",
                    "Cancelled",
                ]
            )
        )
    ].copy()


    overdue_tech_tasks = technician_tasks[
        (
            technician_tasks["_date"] < today
        )
        &
        (
            technician_tasks["status"].isin(
                [
                    "Pending",
                    "In Progress",
                    "On Hold",
                ]
            )
        )
    ].copy()


    completed_tech_tasks = technician_tasks[
        technician_tasks["status"]
        == "Completed"
    ].copy()


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    t1, t2 = st.columns(2)


    with t1:
        st.metric(
            "📌 Today",
            len(today_tech_tasks),
        )


    with t2:
        active_count = len(
            technician_tasks[
                technician_tasks["status"].isin(
                    [
                        "Pending",
                        "In Progress",
                        "On Hold",
                    ]
                )
            ]
        )

        st.metric(
            "🔄 Active",
            active_count,
        )


    # --------------------------------------------------------
    # TASK CARD
    # --------------------------------------------------------

    def technician_task_card(
        row,
        prefix,
    ):
        task_id = str(row["id"])

        current_status = str(
            row["status"]
        )

        current_progress = max(
            0,
            min(
                100,
                safe_int(
                    row["progress"]
                ),
            ),
        )


        with st.container(border=True):

            st.markdown(
                f"### {row['name']}"
            )

            st.write(
                f"{priority_icon(row['priority'])} "
                f"**{row['priority']} Priority**"
            )


            c1, c2 = st.columns(2)


            with c1:
                st.write(
                    f"📅 **{row['date']}**"
                )


            with c2:
                st.write(
                    f"🕐 **{row['start']} – "
                    f"{row['end']}**"
                )


            st.caption(
                f"⏱️ "
                f"{safe_float(row['hours']):.1f} hours"
            )


            assigned_by = str(
                row["assigned_by"]
            ).strip()

            if assigned_by:
                st.caption(
                    f"Assigned by: {assigned_by}"
                )


            notes = str(
                row["notes"]
            ).strip()

            if notes:
                st.info(
                    f"📝 {notes}"
                )


            st.progress(
                current_progress
            )

            st.caption(
                f"Current progress: "
                f"{current_progress}%"
            )


            with st.form(
                f"tech_update_{prefix}_{task_id}"
            ):

                if (
                    current_status
                    in TECHNICIAN_STATUSES
                ):
                    status_index = (
                        TECHNICIAN_STATUSES.index(
                            current_status
                        )
                    )
                else:
                    status_index = 0


                new_status = st.selectbox(
                    "Status",
                    TECHNICIAN_STATUSES,
                    index=status_index,
                )


                new_progress = st.slider(
                    "Progress %",
                    0,
                    100,
                    current_progress,
                    5,
                )


                submitted = (
                    st.form_submit_button(
                        "💾 Update",
                        use_container_width=True,
                        type="primary",
                    )
                )


            if submitted:

                final_progress = (
                    100
                    if new_status
                    == "Completed"
                    else int(new_progress)
                )


                success = update_row(
                    task_id,
                    {
                        "status":
                            new_status,

                        "progress":
                            final_progress,
                    },
                )


                if success:
                    refresh_all_data()

                    set_flash(
                        f"{row['name']} updated."
                    )

                    st.rerun()

                else:
                    st.error(
                        "Task could not be updated."
                    )


    # --------------------------------------------------------
    # TECHNICIAN TABS
    # --------------------------------------------------------

    (
        tech_today,
        tech_upcoming,
        tech_overdue,
        tech_done,
    ) = st.tabs(
        [
            "📌 Today",
            "📅 Upcoming",
            "⚠️ Overdue",
            "✅ Done",
        ]
    )


    with tech_today:

        if today_tech_tasks.empty:
            st.info(
                "No tasks scheduled today."
            )

        else:
            for _, row in (
                today_tech_tasks
                .sort_values("start")
                .iterrows()
            ):
                technician_task_card(
                    row,
                    "today",
                )


    with tech_upcoming:

        if upcoming_tech_tasks.empty:
            st.info(
                "No upcoming tasks."
            )

        else:
            for _, row in (
                upcoming_tech_tasks
                .sort_values(
                    [
                        "_date",
                        "start",
                    ]
                )
                .iterrows()
            ):
                technician_task_card(
                    row,
                    "upcoming",
                )


    with tech_overdue:

        if overdue_tech_tasks.empty:
            st.success(
                "No overdue tasks."
            )

        else:
            for _, row in (
                overdue_tech_tasks
                .sort_values(
                    [
                        "_date",
                        "start",
                    ]
                )
                .iterrows()
            ):
                technician_task_card(
                    row,
                    "overdue",
                )


    with tech_done:

        if completed_tech_tasks.empty:
            st.info(
                "No completed tasks."
            )

        else:
            for _, row in (
                completed_tech_tasks
                .sort_values(
                    "_date",
                    ascending=False,
                )
                .iterrows()
            ):
                technician_task_card(
                    row,
                    "done",
                )


# ============================================================
# MANAGER DASHBOARD
# ============================================================

else:

    manager_password = (
        load_manager_password()
    )


    # --------------------------------------------------------
    # PASSWORD NOT CONFIGURED
    # --------------------------------------------------------

    if not manager_password:

        st.header(
            "👔 Manager Dashboard"
        )

        st.error(
            "Manager password is not configured."
        )

        st.info(
            "Open TaskBoard → Settings and enter "
            "manager_password in column A and "
            "your password in column B."
        )

        st.stop()


    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if not st.session_state.get(
        "manager_authenticated",
        False,
    ):

        st.header(
            "👔 Manager Dashboard"
        )

        st.caption(
            "Enter the manager password."
        )


        with st.form(
            "manager_login"
        ):

            entered_password = (
                st.text_input(
                    "Manager Password",
                    type="password",
                )
            )


            unlock = (
                st.form_submit_button(
                    "🔓 Unlock Dashboard",
                    use_container_width=True,
                    type="primary",
                )
            )


        if unlock:

            if hmac.compare_digest(
                entered_password,
                manager_password,
            ):
                st.session_state[
                    "manager_authenticated"
                ] = True

                set_flash(
                    "Manager Dashboard unlocked."
                )

                st.rerun()

            else:
                st.error(
                    "Incorrect manager password."
                )


        st.stop()


    # --------------------------------------------------------
    # MANAGER HEADER
    # --------------------------------------------------------

    manager_header, lock_col = (
        st.columns(
            [4, 1]
        )
    )


    with manager_header:
        st.header(
            "👔 Manager Dashboard"
        )


    with lock_col:

        if st.button(
            "🔒 Lock",
            use_container_width=True,
        ):
            st.session_state[
                "manager_authenticated"
            ] = False

            st.rerun()


    # ========================================================
    # MANAGER DATA
    # ========================================================

    today_tasks = df[
        valid_dates == today
    ].copy()


    this_week = df[
        (
            valid_dates >= week_start
        )
        &
        (
            valid_dates <= week_end
        )
    ].copy()


    active_statuses = [
        "Pending",
        "In Progress",
        "On Hold",
    ]


    overdue = df[
        (
            valid_dates < today
        )
        &
        (
            df["status"].isin(
                active_statuses
            )
        )
    ].copy()


    in_progress_tasks = df[
        df["status"]
        == "In Progress"
    ].copy()


    # ========================================================
    # TECHNICIAN LOOKUP
    # ========================================================

    def get_technician_record(
        technician_name,
    ):
        if active_technicians_df.empty:
            return None

        matching = (
            active_technicians_df[
                active_technicians_df["name"]
                == technician_name
            ]
        )

        if matching.empty:
            return None

        return matching.iloc[0]


    # ========================================================
    # CONFLICT CHECK
    # ========================================================

    def has_conflict(
        data,
        technician_id,
        technician_name,
        date_str,
        start_s,
        end_s,
        ignore_id=None,
    ):
        if data.empty:
            return False, None


        for _, row in data.iterrows():

            row_tech_id = str(
                row.get(
                    "technician_id",
                    ""
                )
            ).strip()

            row_tech_name = str(
                row.get(
                    "technician",
                    ""
                )
            ).strip()


            if technician_id and row_tech_id:
                same_technician = (
                    row_tech_id
                    == str(technician_id)
                )

            else:
                same_technician = (
                    row_tech_name
                    == str(technician_name)
                )


            if not same_technician:
                continue


            if (
                str(row["date"]).strip()
                != str(date_str)
            ):
                continue


            if (
                ignore_id
                and
                str(row["id"])
                == str(ignore_id)
            ):
                continue


            if (
                str(row["status"])
                == "Cancelled"
            ):
                continue


            existing_start = str(
                row["start"]
            ).strip()

            existing_end = str(
                row["end"]
            ).strip()


            if (
                not existing_start
                or
                not existing_end
            ):
                continue


            if (
                existing_start < end_s
                and
                start_s < existing_end
            ):
                return (
                    True,
                    str(row["name"]),
                )


        return False, None


    # ========================================================
    # SAVE TASK
    # ========================================================

    def save_task(
        name,
        technician_id,
        technician_name,
        task_date,
        start_time,
        hours,
        assigned_by,
        priority,
        notes,
    ):
        start_s = (
            start_time.strftime(
                "%H:%M"
            )
        )


        end_datetime = (
            datetime.combine(
                task_date,
                start_time,
            )
            +
            timedelta(
                hours=float(hours)
            )
        )


        if (
            end_datetime.date()
            != task_date
        ):
            return (
                False,
                "Task cannot continue past midnight.",
            )


        end_s = end_datetime.strftime(
            "%H:%M"
        )


        conflict, conflict_task = (
            has_conflict(
                df,
                technician_id,
                technician_name,
                str(task_date),
                start_s,
                end_s,
            )
        )


        if conflict:
            return (
                False,
                f"Busy with '{conflict_task}'",
            )


        append_row(
            [
                str(uuid.uuid4()),
                name,
                str(task_date),
                start_s,
                end_s,
                float(hours),
                technician_id,
                technician_name,
                assigned_by,
                "Pending",
                priority,
                0,
                notes,
                DEFAULT_COLOR,
            ]
        )


        return True, None


    # ========================================================
    # UPDATE CALENDAR TASK
    # ========================================================

    def update_task_schedule(
        task_id,
        new_start,
        new_end,
    ):
        matching = df[
            df["id"].astype(str)
            == str(task_id)
        ]


        if matching.empty:
            return (
                False,
                "Task not found.",
            )


        row = matching.iloc[0]


        if (
            new_start.date()
            != new_end.date()
        ):
            return (
                False,
                "Task cannot continue into another day.",
            )


        technician_id = str(
            row["technician_id"]
        ).strip()

        technician_name = str(
            row["technician"]
        ).strip()


        date_str = (
            new_start.date()
            .strftime("%Y-%m-%d")
        )

        start_s = (
            new_start.strftime(
                "%H:%M"
            )
        )

        end_s = (
            new_end.strftime(
                "%H:%M"
            )
        )


        conflict, conflict_task = (
            has_conflict(
                df,
                technician_id,
                technician_name,
                date_str,
                start_s,
                end_s,
                ignore_id=task_id,
            )
        )


        if conflict:
            return (
                False,
                f"{technician_name} is busy "
                f"with '{conflict_task}'.",
            )


        duration = (
            new_end
            - new_start
        ).total_seconds() / 3600


        update_row(
            task_id,
            {
                "date": date_str,
                "start": start_s,
                "end": end_s,
                "hours": round(
                    duration,
                    2,
                ),
            },
        )


        return True, None


    # ========================================================
    # CALENDAR EVENTS
    # ========================================================

    def build_events(data):
        events = []


        if data.empty:
            return events


        for _, row in data.iterrows():

            try:
                start_dt = datetime.strptime(
                    f"{row['date']} "
                    f"{row['start']}",
                    "%Y-%m-%d %H:%M",
                )

                end_dt = datetime.strptime(
                    f"{row['date']} "
                    f"{row['end']}",
                    "%Y-%m-%d %H:%M",
                )


                color = (
                    str(row["color"]).strip()
                    or DEFAULT_COLOR
                )


                if row["status"] == "Completed":
                    color = "#198754"

                elif row["status"] == "On Hold":
                    color = "#F59E0B"

                elif row["status"] == "Cancelled":
                    color = "#6B7280"


                events.append(
                    {
                        "id": str(
                            row["id"]
                        ),

                        "title": (
                            f"{row['name']} • "
                            f"{row['technician']}"
                        ),

                        "start":
                            start_dt.isoformat(),

                        "end":
                            end_dt.isoformat(),

                        "color":
                            color,
                    }
                )


            except (
                ValueError,
                TypeError,
            ):
                continue


        return events


    # ========================================================
    # OVERVIEW
    # ========================================================

    today_active = today_tasks[
        ~today_tasks["status"].isin(
            [
                "Completed",
                "Cancelled",
            ]
        )
    ]


    weekly_hours = (
        pd.to_numeric(
            this_week["hours"],
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )


    m1, m2, m3, m4 = (
        st.columns(4)
    )


    with m1:
        st.metric(
            "📌 Today",
            len(today_active),
        )


    with m2:
        st.metric(
            "🔄 In Progress",
            len(in_progress_tasks),
        )


    with m3:
        st.metric(
            "⏱️ This Week",
            f"{weekly_hours:.1f} h",
        )


    with m4:
        st.metric(
            "⚠️ Overdue",
            len(overdue),
        )


    st.divider()


    # ========================================================
    # MANAGER TABS
    # ========================================================

    (
        dashboard_tab,
        assign_tab,
        calendar_tab,
        tasks_tab,
        admin_tab,
    ) = st.tabs(
        [
            "🏠 Dashboard",
            "➕ Assign",
            "📅 Calendar",
            "📋 Tasks",
            "⚙️ Admin",
        ]
    )


    # ========================================================
    # DASHBOARD TAB
    # ========================================================

    with dashboard_tab:

        st.subheader(
            "📌 Today's Schedule"
        )


        if today_tasks.empty:
            st.info(
                "No tasks scheduled today."
            )

        else:

            for _, row in (
                today_tasks
                .sort_values(
                    [
                        "start",
                        "technician",
                    ]
                )
                .iterrows()
            ):

                with st.container(
                    border=True
                ):

                    c1, c2 = (
                        st.columns(
                            [3, 1]
                        )
                    )


                    with c1:
                        st.markdown(
                            f"### {row['name']}"
                        )

                        st.caption(
                            f"👤 {row['technician']} • "
                            f"Assigned by "
                            f"{row['assigned_by']}"
                        )


                    with c2:
                        st.write(
                            f"**"
                            f"{status_icon(row['status'])} "
                            f"{row['status']}**"
                        )

                        st.caption(
                            f"{priority_icon(row['priority'])} "
                            f"{row['priority']}"
                        )


                    st.write(
                        f"🕐 **{row['start']} – "
                        f"{row['end']}** • "
                        f"⏱️ "
                        f"{safe_float(row['hours']):.1f}h"
                    )


                    progress = max(
                        0,
                        min(
                            100,
                            safe_int(
                                row["progress"]
                            ),
                        ),
                    )


                    st.progress(progress)

                    st.caption(
                        f"Progress: {progress}%"
                    )


        # ----------------------------------------------------
        # WORKLOAD
        # ----------------------------------------------------

        st.subheader(
            "👥 Team Workload — This Week"
        )


        if technicians_df.empty:
            st.info(
                "No technicians added."
            )

        else:

            for _, tech_row in (
                technicians_df
                .sort_values("name")
                .iterrows()
            ):

                tech_id = str(
                    tech_row["id"]
                ).strip()

                tech_name = str(
                    tech_row["name"]
                ).strip()

                active = bool(
                    tech_row["active"]
                )


                technician_week = (
                    this_week[
                        (
                            this_week[
                                "technician_id"
                            ].astype(str)
                            == tech_id
                        )
                        |
                        (
                            (
                                this_week[
                                    "technician_id"
                                ]
                                .astype(str)
                                .str.strip()
                                == ""
                            )
                            &
                            (
                                this_week[
                                    "technician"
                                ].astype(str)
                                == tech_name
                            )
                        )
                    ]
                    .copy()
                )


                technician_week = (
                    technician_week[
                        technician_week[
                            "status"
                        ]
                        != "Cancelled"
                    ]
                )


                hours_value = (
                    pd.to_numeric(
                        technician_week[
                            "hours"
                        ],
                        errors="coerce",
                    )
                    .fillna(0)
                    .sum()
                )


                if not active:
                    workload = (
                        "⚪ Inactive"
                    )

                elif hours_value == 0:
                    workload = (
                        "🟢 Available"
                    )

                elif hours_value <= 20:
                    workload = (
                        "🟢 Light"
                    )

                elif hours_value <= 35:
                    workload = (
                        "🟡 Normal"
                    )

                elif hours_value <= 45:
                    workload = (
                        "🟠 Busy"
                    )

                else:
                    workload = (
                        "🔴 Heavy"
                    )


                with st.container(
                    border=True
                ):

                    w1, w2, w3 = (
                        st.columns(
                            [2, 1, 1]
                        )
                    )


                    with w1:
                        st.markdown(
                            f"**👤 {tech_name}**"
                        )

                        st.caption(
                            workload
                        )


                    with w2:
                        st.metric(
                            "Tasks",
                            len(
                                technician_week
                            ),
                        )


                    with w3:
                        st.metric(
                            "Hours",
                            f"{hours_value:.1f}",
                        )


                    workload_percent = min(
                        100,
                        int(
                            (
                                hours_value
                                / 45
                            )
                            * 100
                        ),
                    )

                    st.progress(
                        workload_percent
                    )


        # ----------------------------------------------------
        # OVERDUE
        # ----------------------------------------------------

        st.subheader(
            "⚠️ Needs Attention"
        )


        if overdue.empty:
            st.success(
                "No overdue active tasks."
            )

        else:

            for _, row in (
                overdue
                .sort_values(
                    [
                        "date",
                        "start",
                    ]
                )
                .iterrows()
            ):

                with st.container(
                    border=True
                ):
                    st.markdown(
                        f"**⚠️ "
                        f"{row['name']}**"
                    )

                    st.write(
                        f"👤 {row['technician']}"
                    )

                    st.caption(
                        f"{row['date']} • "
                        f"{row['start']} • "
                        f"{row['status']}"
                    )


    # ========================================================
    # ASSIGN TAB
    # ========================================================

    with assign_tab:

        st.subheader(
            "➕ Assign New Task"
        )

        st.caption(
            "Schedule conflicts are checked automatically."
        )


        if active_technicians_df.empty:
            st.warning(
                "No active technicians are available."
            )

        else:

            with st.form(
                "assign_task_form",
                clear_on_submit=True,
            ):

                task_name = (
                    st.text_input(
                        "Task Name *"
                    )
                )


                selected_tech_names = (
                    st.multiselect(
                        "Technician(s) *",
                        ACTIVE_TECH_NAMES,
                    )
                )


                a1, a2 = st.columns(2)


                with a1:
                    selected_date = (
                        st.date_input(
                            "Date *",
                            today,
                        )
                    )


                with a2:
                    selected_start = (
                        st.time_input(
                            "Start Time *"
                        )
                    )


                a3, a4 = st.columns(2)


                with a3:
                    selected_hours = (
                        st.number_input(
                            "Duration (hours)",
                            min_value=0.5,
                            max_value=12.0,
                            value=1.0,
                            step=0.5,
                        )
                    )


                with a4:
                    selected_priority = (
                        st.selectbox(
                            "Priority",
                            PRIORITIES,
                            index=1,
                        )
                    )


                selected_assigned_by = (
                    st.text_input(
                        "Assigned By *"
                    )
                )


                selected_notes = (
                    st.text_area(
                        "Notes",
                        height=100,
                    )
                )


                assign_submit = (
                    st.form_submit_button(
                        "➕ Assign Task",
                        use_container_width=True,
                        type="primary",
                    )
                )


            if assign_submit:

                if not task_name.strip():
                    st.error(
                        "Enter a task name."
                    )

                elif not selected_tech_names:
                    st.error(
                        "Select at least one technician."
                    )

                elif not selected_assigned_by.strip():
                    st.error(
                        "Enter who assigned the task."
                    )

                else:

                    successful = []
                    failed = []


                    for technician_name in (
                        selected_tech_names
                    ):

                        record = (
                            get_technician_record(
                                technician_name
                            )
                        )


                        if record is None:
                            failed.append(
                                f"{technician_name}: "
                                f"Technician not found."
                            )

                            continue


                        tech_id = str(
                            record["id"]
                        ).strip()


                        ok, message = (
                            save_task(
                                task_name.strip(),
                                tech_id,
                                technician_name,
                                selected_date,
                                selected_start,
                                selected_hours,
                                selected_assigned_by.strip(),
                                selected_priority,
                                selected_notes.strip(),
                            )
                        )


                        if ok:
                            successful.append(
                                technician_name
                            )

                        else:
                            failed.append(
                                f"{technician_name}: "
                                f"{message}"
                            )


                    for message in failed:
                        st.error(message)


                    if successful:
                        refresh_all_data()

                        set_flash(
                            "Task assigned to "
                            +
                            ", ".join(
                                successful
                            )
                        )

                        st.rerun()


    # ========================================================
    # CALENDAR TAB
    # ========================================================

    with calendar_tab:

        st.subheader(
            "📅 Project Calendar"
        )

        st.caption(
            "Month / Week / Day team schedule."
        )


        cf1, cf2 = st.columns(
            [2, 1]
        )


        with cf1:
            calendar_technician = (
                st.selectbox(
                    "Technician",
                    [
                        "All Technicians"
                    ]
                    +
                    ALL_TECH_NAMES,
                    key=(
                        "calendar_technician"
                    ),
                )
            )


        with cf2:
            show_completed = (
                st.checkbox(
                    "Show completed",
                    value=True,
                    key=(
                        "calendar_completed"
                    ),
                )
            )


        calendar_df = df.copy()


        if (
            calendar_technician
            != "All Technicians"
        ):
            calendar_df = calendar_df[
                calendar_df["technician"]
                == calendar_technician
            ].copy()


        if not show_completed:
            calendar_df = calendar_df[
                ~calendar_df["status"].isin(
                    [
                        "Completed",
                        "Cancelled",
                    ]
                )
            ].copy()


        calendar_events = (
            build_events(
                calendar_df
            )
        )


        calendar_options = {
            "initialView":
                "timeGridWeek",

            "editable":
                True,

            "selectable":
                True,

            "navLinks":
                True,

            "nowIndicator":
                True,

            "allDaySlot":
                False,

            "height":
                720,

            "slotMinTime":
                "06:00:00",

            "slotMaxTime":
                "22:00:00",

            "slotDuration":
                "00:30:00",

            "scrollTime":
                "08:00:00",

            "expandRows":
                True,

            "headerToolbar": {
                "left":
                    "prev,next today",

                "center":
                    "title",

                "right":
                    (
                        "dayGridMonth,"
                        "timeGridWeek,"
                        "timeGridDay"
                    ),
            },

            "buttonText": {
                "today": "Today",
                "month": "Month",
                "week": "Week",
                "day": "Day",
            },

            "eventTimeFormat": {
                "hour": "2-digit",
                "minute": "2-digit",
                "hour12": False,
            },

            "slotLabelFormat": {
                "hour": "2-digit",
                "minute": "2-digit",
                "hour12": False,
            },
        }


        calendar_css = """
        .fc {
            font-size: 12px;
        }

        .fc-toolbar-title {
            font-size: 1.05rem !important;
            font-weight: 700 !important;
        }

        .fc-button {
            border-radius: 6px !important;
        }

        .fc-timegrid-slot {
            height: 36px !important;
        }

        .fc-event {
            border-radius: 5px !important;
            cursor: pointer !important;
        }

        .fc-event-title {
            font-size: 10px !important;
            font-weight: 600 !important;
        }

        .fc-event-time {
            font-size: 9px !important;
        }
        """


        calendar_result = calendar(
            events=calendar_events,
            options=calendar_options,
            custom_css=calendar_css,
            callbacks=[
                "eventDrop",
                "eventChange",
                "eventResize",
            ],
            key="project_calendar",
        )


        if calendar_df.empty:
            st.info(
                "No tasks to display on the calendar."
            )


        # ----------------------------------------------------
        # HANDLE CALENDAR CHANGES
        # ----------------------------------------------------

        if (
            calendar_result
            and
            isinstance(
                calendar_result,
                dict,
            )
        ):

            event_type = next(
                iter(calendar_result),
                None,
            )


            if event_type in [
                "eventDrop",
                "eventChange",
                "eventResize",
            ]:

                try:
                    event_data = (
                        calendar_result[
                            event_type
                        ]
                    )

                    event = (
                        event_data.get(
                            "event",
                            {}
                        )
                    )


                    task_id = str(
                        event.get(
                            "id",
                            ""
                        )
                    ).strip()


                    start_value = (
                        event.get("start")
                    )

                    end_value = (
                        event.get("end")
                    )


                    if not task_id:
                        st.error(
                            "Unable to identify task."
                        )

                    elif not start_value:
                        st.error(
                            "Unable to determine new start time."
                        )

                    else:

                        new_start = (
                            datetime.fromisoformat(
                                start_value.replace(
                                    "Z",
                                    "+00:00",
                                )
                            )
                        )


                        if end_value:
                            new_end = (
                                datetime.fromisoformat(
                                    end_value.replace(
                                        "Z",
                                        "+00:00",
                                    )
                                )
                            )

                        else:
                            matching = df[
                                df["id"].astype(str)
                                == task_id
                            ]


                            if matching.empty:
                                st.error(
                                    "Task not found."
                                )

                                st.stop()


                            original_hours = (
                                safe_float(
                                    matching.iloc[0][
                                        "hours"
                                    ],
                                    1.0,
                                )
                            )


                            new_end = (
                                new_start
                                +
                                timedelta(
                                    hours=(
                                        original_hours
                                    )
                                )
                            )


                        if (
                            new_start.tzinfo
                            is not None
                        ):
                            new_start = (
                                new_start.replace(
                                    tzinfo=None
                                )
                            )


                        if (
                            new_end.tzinfo
                            is not None
                        ):
                            new_end = (
                                new_end.replace(
                                    tzinfo=None
                                )
                            )


                        ok, message = (
                            update_task_schedule(
                                task_id,
                                new_start,
                                new_end,
                            )
                        )


                        if ok:
                            refresh_all_data()

                            set_flash(
                                "Task schedule updated."
                            )

                            st.rerun()

                        else:
                            st.error(message)


                except Exception as e:
                    st.error(
                        "Calendar change could not be saved."
                    )

                    st.exception(e)


    # ========================================================
    # TASKS TAB
    # ========================================================

    with tasks_tab:

        st.subheader(
            f"📋 Tasks ({len(df)})"
        )


        filter_col1, filter_col2 = (
            st.columns(2)
        )


        with filter_col1:
            task_filter_tech = (
                st.selectbox(
                    "Technician",
                    [
                        "All Technicians"
                    ]
                    +
                    ALL_TECH_NAMES,
                    key=(
                        "task_filter_tech"
                    ),
                )
            )


        with filter_col2:
            task_filter_status = (
                st.selectbox(
                    "Status",
                    [
                        "All Statuses"
                    ]
                    +
                    STATUSES,
                    key=(
                        "task_filter_status"
                    ),
                )
            )


        display_tasks = df.copy()


        if (
            task_filter_tech
            != "All Technicians"
        ):
            display_tasks = (
                display_tasks[
                    display_tasks["technician"]
                    == task_filter_tech
                ]
            )


        if (
            task_filter_status
            != "All Statuses"
        ):
            display_tasks = (
                display_tasks[
                    display_tasks["status"]
                    == task_filter_status
                ]
            )


        if display_tasks.empty:
            st.info(
                "No tasks match the filters."
            )

        else:

            for _, row in (
                display_tasks
                .sort_values(
                    [
                        "date",
                        "start",
                    ],
                    ascending=[
                        False,
                        True,
                    ],
                )
                .iterrows()
            ):

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### {row['name']}"
                    )

                    st.write(
                        f"👤 **"
                        f"{row['technician']}**"
                    )

                    st.caption(
                        f"📅 {row['date']} • "
                        f"🕐 {row['start']} – "
                        f"{row['end']} • "
                        f"⏱️ "
                        f"{safe_float(row['hours']):.1f}h"
                    )

                    st.write(
                        f"{status_icon(row['status'])} "
                        f"**{row['status']}** • "
                        f"{priority_icon(row['priority'])} "
                        f"{row['priority']}"
                    )


                    progress = max(
                        0,
                        min(
                            100,
                            safe_int(
                                row["progress"]
                            ),
                        ),
                    )


                    st.progress(progress)

                    st.caption(
                        f"Progress: {progress}%"
                    )


                    notes = str(
                        row["notes"]
                    ).strip()

                    if notes:
                        st.caption(
                            f"📝 {notes}"
                        )


    # ========================================================
    # ADMIN TAB
    # ========================================================

    with admin_tab:

        tech_admin_tab, task_admin_tab = (
            st.tabs(
                [
                    "👥 Technicians",
                    "✏️ Manage Tasks",
                ]
            )
        )


        # ====================================================
        # TECHNICIANS
        # ====================================================

        with tech_admin_tab:

            st.subheader(
                "👥 Manage Technicians"
            )


            with st.form(
                "add_technician_form",
                clear_on_submit=True,
            ):

                new_technician_name = (
                    st.text_input(
                        "Technician Name"
                    )
                )


                add_submit = (
                    st.form_submit_button(
                        "➕ Add Technician",
                        use_container_width=True,
                        type="primary",
                    )
                )


            if add_submit:

                clean_name = (
                    new_technician_name
                    .strip()
                )


                if not clean_name:
                    st.error(
                        "Enter a technician name."
                    )

                else:
                    existing_names = [
                        str(name)
                        .strip()
                        .lower()

                        for name in (
                            technicians_df[
                                "name"
                            ].tolist()
                        )
                    ]


                    if (
                        clean_name.lower()
                        in existing_names
                    ):
                        st.error(
                            "Technician already exists."
                        )

                    else:
                        technician_id = (
                            "TECH-"
                            +
                            uuid.uuid4()
                            .hex[:8]
                            .upper()
                        )


                        add_technician(
                            technician_id,
                            clean_name,
                            True,
                        )


                        refresh_all_data()

                        set_flash(
                            f"{clean_name} added."
                        )

                        st.rerun()


            st.divider()


            if technicians_df.empty:
                st.info(
                    "No technicians added."
                )

            else:

                for _, tech_row in (
                    technicians_df
                    .sort_values("name")
                    .iterrows()
                ):

                    tech_id = str(
                        tech_row["id"]
                    )

                    tech_name = str(
                        tech_row["name"]
                    )

                    active = bool(
                        tech_row["active"]
                    )


                    with st.container(
                        border=True
                    ):

                        c1, c2 = (
                            st.columns(
                                [3, 1]
                            )
                        )


                        with c1:
                            st.markdown(
                                f"**👤 "
                                f"{tech_name}**"
                            )

                            st.caption(
                                (
                                    "🟢 Active"
                                    if active
                                    else "⚪ Inactive"
                                )
                                +
                                f" • {tech_id}"
                            )


                        with c2:

                            if active:

                                if st.button(
                                    "Deactivate",
                                    key=(
                                        f"deactivate_"
                                        f"{tech_id}"
                                    ),
                                    use_container_width=True,
                                ):
                                    update_technician(
                                        tech_id,
                                        {
                                            "active":
                                                False
                                        },
                                    )

                                    refresh_all_data()

                                    set_flash(
                                        f"{tech_name} deactivated."
                                    )

                                    st.rerun()

                            else:

                                if st.button(
                                    "Activate",
                                    key=(
                                        f"activate_"
                                        f"{tech_id}"
                                    ),
                                    use_container_width=True,
                                ):
                                    update_technician(
                                        tech_id,
                                        {
                                            "active":
                                                True
                                        },
                                    )

                                    refresh_all_data()

                                    set_flash(
                                        f"{tech_name} activated."
                                    )

                                    st.rerun()


        # ====================================================
        # MANAGE TASKS
        # ====================================================

        with task_admin_tab:

            st.subheader(
                "✏️ Manage Tasks"
            )


            if df.empty:
                st.info(
                    "No tasks available."
                )

            else:

                task_options = {}


                for _, row in df.iterrows():

                    task_id = str(
                        row["id"]
                    )

                    short_id = (
                        task_id[:8]
                    )

                    label = (
                        f"{row['name']} | "
                        f"{row['technician']} | "
                        f"{row['date']} "
                        f"{row['start']} | "
                        f"{short_id}"
                    )

                    task_options[
                        label
                    ] = task_id


                selected_label = (
                    st.selectbox(
                        "Select Task",
                        list(
                            task_options.keys()
                        ),
                    )
                )


                selected_id = (
                    task_options[
                        selected_label
                    ]
                )


                selected_task = (
                    df[
                        df["id"].astype(str)
                        == selected_id
                    ]
                    .iloc[0]
                )


                # --------------------------------------------
                # EDIT TASK
                # --------------------------------------------

                with st.form(
                    "edit_task_form"
                ):

                    edit_name = (
                        st.text_input(
                            "Task Name",
                            value=str(
                                selected_task[
                                    "name"
                                ]
                            ),
                        )
                    )


                    current_tech = str(
                        selected_task[
                            "technician"
                        ]
                    )


                    edit_tech_options = (
                        ACTIVE_TECH_NAMES.copy()
                    )


                    if (
                        current_tech
                        and
                        current_tech
                        not in edit_tech_options
                    ):
                        edit_tech_options.append(
                            current_tech
                        )


                    edit_tech_options = sorted(
                        set(
                            edit_tech_options
                        )
                    )


                    if edit_tech_options:

                        try:
                            current_index = (
                                edit_tech_options
                                .index(
                                    current_tech
                                )
                            )

                        except ValueError:
                            current_index = 0


                        edit_technician = (
                            st.selectbox(
                                "Technician",
                                edit_tech_options,
                                index=current_index,
                            )
                        )

                    else:
                        edit_technician = (
                            current_tech
                        )

                        st.warning(
                            "No active technicians."
                        )


                    e1, e2 = st.columns(2)


                    with e1:
                        edit_date = (
                            st.date_input(
                                "Date",
                                value=(
                                    safe_date(
                                        selected_task[
                                            "date"
                                        ]
                                    )
                                    or today
                                ),
                            )
                        )


                    with e2:

                        try:
                            existing_start = (
                                datetime.strptime(
                                    str(
                                        selected_task[
                                            "start"
                                        ]
                                    ),
                                    "%H:%M",
                                )
                                .time()
                            )

                        except ValueError:
                            existing_start = (
                                datetime.now()
                                .replace(
                                    second=0,
                                    microsecond=0,
                                )
                                .time()
                            )


                        edit_start = (
                            st.time_input(
                                "Start",
                                value=(
                                    existing_start
                                ),
                            )
                        )


                    e3, e4 = st.columns(2)


                    with e3:
                        edit_hours = (
                            st.number_input(
                                "Duration (hours)",
                                min_value=0.5,
                                max_value=12.0,
                                value=max(
                                    0.5,
                                    safe_float(
                                        selected_task[
                                            "hours"
                                        ],
                                        1.0,
                                    ),
                                ),
                                step=0.5,
                            )
                        )


                    with e4:
                        current_priority = str(
                            selected_task[
                                "priority"
                            ]
                        )


                        priority_index = (
                            PRIORITIES.index(
                                current_priority
                            )
                            if current_priority
                            in PRIORITIES
                            else 1
                        )


                        edit_priority = (
                            st.selectbox(
                                "Priority",
                                PRIORITIES,
                                index=(
                                    priority_index
                                ),
                            )
                        )


                    e5, e6 = st.columns(2)


                    with e5:
                        current_status = str(
                            selected_task[
                                "status"
                            ]
                        )


                        status_index = (
                            STATUSES.index(
                                current_status
                            )
                            if current_status
                            in STATUSES
                            else 0
                        )


                        edit_status = (
                            st.selectbox(
                                "Status",
                                STATUSES,
                                index=status_index,
                            )
                        )


                    with e6:
                        edit_progress = (
                            st.slider(
                                "Progress %",
                                0,
                                100,
                                max(
                                    0,
                                    min(
                                        100,
                                        safe_int(
                                            selected_task[
                                                "progress"
                                            ]
                                        ),
                                    ),
                                ),
                                5,
                            )
                        )


                    edit_assigned_by = (
                        st.text_input(
                            "Assigned By",
                            value=str(
                                selected_task[
                                    "assigned_by"
                                ]
                            ),
                        )
                    )


                    edit_notes = (
                        st.text_area(
                            "Notes",
                            value=str(
                                selected_task[
                                    "notes"
                                ]
                            ),
                            height=100,
                        )
                    )


                    save_edit = (
                        st.form_submit_button(
                            "💾 Update Task",
                            use_container_width=True,
                            type="primary",
                        )
                    )


                # --------------------------------------------
                # SAVE TASK
                # --------------------------------------------

                if save_edit:

                    if not edit_name.strip():
                        st.error(
                            "Task name cannot be empty."
                        )

                    elif not edit_assigned_by.strip():
                        st.error(
                            "Assigned By cannot be empty."
                        )

                    elif not edit_technician:
                        st.error(
                            "Select a technician."
                        )

                    else:

                        tech_match = (
                            technicians_df[
                                technicians_df[
                                    "name"
                                ]
                                == edit_technician
                            ]
                        )


                        tech_id = (
                            str(
                                tech_match
                                .iloc[0]["id"]
                            )
                            if not tech_match.empty
                            else ""
                        )


                        start_s = (
                            edit_start.strftime(
                                "%H:%M"
                            )
                        )


                        end_dt = (
                            datetime.combine(
                                edit_date,
                                edit_start,
                            )
                            +
                            timedelta(
                                hours=edit_hours
                            )
                        )


                        if (
                            end_dt.date()
                            != edit_date
                        ):
                            st.error(
                                "Task cannot continue "
                                "past midnight."
                            )

                        else:

                            end_s = (
                                end_dt.strftime(
                                    "%H:%M"
                                )
                            )


                            conflict, conflict_task = (
                                has_conflict(
                                    df,
                                    tech_id,
                                    edit_technician,
                                    str(edit_date),
                                    start_s,
                                    end_s,
                                    ignore_id=(
                                        selected_id
                                    ),
                                )
                            )


                            if conflict:
                                st.error(
                                    f"{edit_technician} "
                                    f"is busy with "
                                    f"'{conflict_task}'."
                                )

                            else:

                                final_progress = (
                                    100
                                    if edit_status
                                    == "Completed"
                                    else int(
                                        edit_progress
                                    )
                                )


                                success = update_row(
                                    selected_id,
                                    {
                                        "name":
                                            edit_name.strip(),

                                        "date":
                                            str(edit_date),

                                        "start":
                                            start_s,

                                        "end":
                                            end_s,

                                        "hours":
                                            float(
                                                edit_hours
                                            ),

                                        "technician_id":
                                            tech_id,

                                        "technician":
                                            edit_technician,

                                        "assigned_by":
                                            edit_assigned_by
                                            .strip(),

                                        "status":
                                            edit_status,

                                        "priority":
                                            edit_priority,

                                        "progress":
                                            final_progress,

                                        "notes":
                                            edit_notes
                                            .strip(),
                                    },
                                )


                                if success:
                                    refresh_all_data()

                                    set_flash(
                                        "Task updated successfully."
                                    )

                                    st.rerun()

                                else:
                                    st.error(
                                        "Task could not be updated."
                                    )


                # --------------------------------------------
                # DELETE TASK
                # --------------------------------------------

                st.divider()

                st.subheader(
                    "🗑️ Delete Task"
                )


                if st.button(
                    "🗑️ Delete Selected Task",
                    use_container_width=True,
                    key=(
                        "delete_selected_task"
                    ),
                ):
                    st.session_state[
                        "confirm_delete_task"
                    ] = selected_id


                if (
                    st.session_state.get(
                        "confirm_delete_task"
                    )
                    == selected_id
                ):

                    st.warning(
                        f"Delete "
                        f"'{selected_task['name']}'?"
                    )


                    d1, d2 = (
                        st.columns(2)
                    )


                    with d1:

                        if st.button(
                            "Yes, Delete",
                            use_container_width=True,
                            type="primary",
                            key=(
                                "confirm_delete"
                            ),
                        ):
                            success = (
                                delete_row(
                                    selected_id
                                )
                            )


                            if success:
                                st.session_state.pop(
                                    "confirm_delete_task",
                                    None,
                                )

                                refresh_all_data()

                                set_flash(
                                    "Task deleted."
                                )

                                st.rerun()

                            else:
                                st.error(
                                    "Task could not be deleted."
                                )


                    with d2:

                        if st.button(
                            "Cancel",
                            use_container_width=True,
                            key=(
                                "cancel_delete"
                            ),
                        ):
                            st.session_state.pop(
                                "confirm_delete_task",
                                None,
                            )

                            st.rerun()
