import streamlit as st
import pandas as pd
import uuid
import hmac

from datetime import (
    datetime,
    date,
    timedelta,
)

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
    get_projects,
    add_project,
    update_project,
    get_setting,
)


# ============================================================
# PAGE
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


# Existing columns stay first.
# New columns are appended.
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
    "project_id",
    "project",
    "location",
    "technician_comments",
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
        font-size: 1.03rem !important;
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
# INITIALIZE
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
        str(value).strip().lower()
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


def format_project(value):
    value = str(value).strip()

    if value:
        return value

    return "No Project"


# ============================================================
# DATA
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
            "project_id",
            "project",
            "location",
            "technician_comments",
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

    columns = [
        "id",
        "name",
        "active",
    ]

    for column in columns:
        if column not in data.columns:
            data[column] = ""

    data = data[columns].copy()

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
def load_projects():
    records = get_projects()

    data = pd.DataFrame(records)

    columns = [
        "id",
        "name",
        "description",
        "active",
        "created_at",
    ]

    for column in columns:
        if column not in data.columns:
            data[column] = ""

    data = data[columns].copy()

    if not data.empty:

        for column in [
            "id",
            "name",
            "description",
            "created_at",
        ]:
            data[column] = (
                data[column]
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


def refresh_all_data():
    load_tasks.clear()
    load_technicians.clear()
    load_projects.clear()
    load_manager_password.clear()


# ============================================================
# FLASH
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
# LOAD
# ============================================================

try:
    df = load_tasks()
    technicians_df = load_technicians()
    projects_df = load_projects()

except Exception as e:
    st.error("Unable to load tracker data.")
    st.exception(e)
    st.stop()


# ============================================================
# TECHNICIANS / PROJECTS
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


if projects_df.empty:
    active_projects_df = pd.DataFrame(
        columns=[
            "id",
            "name",
            "description",
            "active",
            "created_at",
        ]
    )

else:
    active_projects_df = (
        projects_df[
            projects_df["active"] == True
        ]
        .copy()
        .sort_values("name")
    )


ACTIVE_PROJECT_NAMES = (
    active_projects_df["name"]
    .tolist()
)


ALL_PROJECT_NAMES = sorted(
    set(
        projects_df["name"].tolist()
        +
        df["project"].tolist()
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
# AVAILABILITY
# ============================================================

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

        if str(row["status"]).strip() == "Cancelled":
            continue

        if (
            ignore_id
            and
            str(row["id"]).strip()
            == str(ignore_id).strip()
        ):
            continue

        if (
            str(row["date"]).strip()
            != str(date_str).strip()
        ):
            continue

        row_tech_id = str(
            row.get(
                "technician_id",
                "",
            )
        ).strip()

        row_tech_name = str(
            row.get(
                "technician",
                "",
            )
        ).strip()

        if technician_id and row_tech_id:
            same_technician = (
                row_tech_id
                == str(technician_id).strip()
            )

        else:
            same_technician = (
                row_tech_name
                == str(technician_name).strip()
            )

        if not same_technician:
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


def get_available_technicians(
    task_date,
    start_time,
    hours,
):
    if active_technicians_df.empty:
        return []

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

    if end_datetime.date() != task_date:
        return []

    date_str = str(task_date)
    start_s = start_time.strftime("%H:%M")
    end_s = end_datetime.strftime("%H:%M")

    available = []

    for _, tech in active_technicians_df.iterrows():

        tech_id = str(
            tech["id"]
        ).strip()

        tech_name = str(
            tech["name"]
        ).strip()

        conflict, _ = has_conflict(
            df,
            tech_id,
            tech_name,
            date_str,
            start_s,
            end_s,
        )

        if not conflict:
            available.append(
                tech_name
            )

    return available


def get_technician_record(name):
    matching = active_technicians_df[
        active_technicians_df["name"]
        == name
    ]

    if matching.empty:
        return None

    return matching.iloc[0]


def get_project_record(name):
    matching = active_projects_df[
        active_projects_df["name"]
        == name
    ]

    if matching.empty:
        return None

    return matching.iloc[0]


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
        "Projects • Tasks • Team Scheduling"
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
        "Select your name to view your assigned work."
    )


    if not ALL_TECH_NAMES:
        st.warning(
            "No technicians are available."
        )

        st.stop()


    selected_technician = st.selectbox(
        "Who are you?",
        ALL_TECH_NAMES,
        key="technician_dashboard_name",
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


    today_tasks = technician_tasks[
        technician_tasks["_date"]
        == today
    ].copy()


    upcoming_tasks = technician_tasks[
        (
            technician_tasks["_date"]
            > today
        )
        &
        (
            ~technician_tasks["status"]
            .isin(
                [
                    "Completed",
                    "Cancelled",
                ]
            )
        )
    ].copy()


    overdue_tasks = technician_tasks[
        (
            technician_tasks["_date"]
            < today
        )
        &
        (
            technician_tasks["status"]
            .isin(
                [
                    "Pending",
                    "In Progress",
                    "On Hold",
                ]
            )
        )
    ].copy()


    completed_tasks = technician_tasks[
        technician_tasks["status"]
        == "Completed"
    ].copy()


    t1, t2 = st.columns(2)


    with t1:
        st.metric(
            "📌 Today",
            len(today_tasks),
        )


    with t2:
        active_count = len(
            technician_tasks[
                technician_tasks["status"]
                .isin(
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


    # ========================================================
    # TECHNICIAN TASK CARD
    # ========================================================

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

        project_name = format_project(
            row["project"]
        )

        location = str(
            row["location"]
        ).strip()

        comments = str(
            row["technician_comments"]
        ).strip()


        with st.container(border=True):

            st.markdown(
                f"### {row['name']}"
            )

            # Project is intentionally prominent.
            st.write(
                f"📁 **Project: "
                f"{project_name}**"
            )


            if location:
                st.write(
                    f"📍 **Location:** "
                    f"{location}"
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
                    f"Assigned by: "
                    f"{assigned_by}"
                )


            notes = str(
                row["notes"]
            ).strip()


            if notes:
                st.info(
                    f"📝 Manager Notes\n\n{notes}"
                )


            st.progress(
                current_progress
            )

            st.caption(
                f"Progress: "
                f"{current_progress}%"
            )


            if comments:

                with st.expander(
                    "💬 Technician Comments",
                    expanded=False,
                ):
                    st.text(comments)


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


                new_comment = st.text_area(
                    "Add Comment",
                    placeholder=(
                        "Add an update, issue, "
                        "observation or note..."
                    ),
                    height=90,
                )


                submitted = (
                    st.form_submit_button(
                        "💾 Save Update",
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


                updated_comments = comments


                if new_comment.strip():

                    timestamp = datetime.now().strftime(
                        "%Y-%m-%d %H:%M"
                    )

                    comment_entry = (
                        f"[{timestamp}] "
                        f"{selected_technician}: "
                        f"{new_comment.strip()}"
                    )


                    if updated_comments:
                        updated_comments += (
                            "\n\n"
                            + comment_entry
                        )

                    else:
                        updated_comments = (
                            comment_entry
                        )


                success = update_row(
                    task_id,
                    {
                        "status":
                            new_status,

                        "progress":
                            final_progress,

                        "technician_comments":
                            updated_comments,
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


    # ========================================================
    # TECHNICIAN TABS
    # ========================================================

    (
        tab_today,
        tab_upcoming,
        tab_overdue,
        tab_done,
    ) = st.tabs(
        [
            "📌 Today",
            "📅 Upcoming",
            "⚠️ Overdue",
            "✅ Done",
        ]
    )


    with tab_today:

        if today_tasks.empty:
            st.info(
                "No tasks scheduled today."
            )

        else:
            for _, row in (
                today_tasks
                .sort_values("start")
                .iterrows()
            ):
                technician_task_card(
                    row,
                    "today",
                )


    with tab_upcoming:

        if upcoming_tasks.empty:
            st.info(
                "No upcoming tasks."
            )

        else:
            for _, row in (
                upcoming_tasks
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


    with tab_overdue:

        if overdue_tasks.empty:
            st.success(
                "No overdue tasks."
            )

        else:
            for _, row in (
                overdue_tasks
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


    with tab_done:

        if completed_tasks.empty:
            st.info(
                "No completed tasks."
            )

        else:
            for _, row in (
                completed_tasks
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


    st.stop()


# ============================================================
# MANAGER PASSWORD
# ============================================================

manager_password = (
    load_manager_password()
)


if not manager_password:

    st.header(
        "👔 Manager Dashboard"
    )

    st.error(
        "Manager password is not configured."
    )

    st.info(
        "Open TaskBoard → Settings. "
        "Set key to manager_password "
        "and put your password in the value column."
    )

    st.stop()


if not st.session_state.get(
    "manager_authenticated",
    False,
):

    st.header(
        "👔 Manager Dashboard"
    )


    with st.form(
        "manager_login"
    ):

        entered_password = st.text_input(
            "Manager Password",
            type="password",
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


# ============================================================
# MANAGER HEADER
# ============================================================

manager_header, lock_col = st.columns(
    [4, 1]
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


# ============================================================
# MANAGER DATA
# ============================================================

today_manager_tasks = df[
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


in_progress = df[
    df["status"]
    == "In Progress"
].copy()


today_active = (
    today_manager_tasks[
        ~today_manager_tasks[
            "status"
        ].isin(
            [
                "Completed",
                "Cancelled",
            ]
        )
    ]
)


weekly_hours = (
    pd.to_numeric(
        this_week["hours"],
        errors="coerce",
    )
    .fillna(0)
    .sum()
)


m1, m2, m3, m4 = st.columns(4)


with m1:
    st.metric(
        "📌 Today",
        len(today_active),
    )


with m2:
    st.metric(
        "🔄 In Progress",
        len(in_progress),
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


# ============================================================
# MANAGER TABS
# ============================================================

(
    dashboard_tab,
    assign_tab,
    calendar_tab,
    tasks_tab,
    projects_tab,
    admin_tab,
) = st.tabs(
    [
        "🏠 Dashboard",
        "➕ Assign",
        "📅 Calendar",
        "📋 Tasks",
        "📁 Projects",
        "⚙️ Admin",
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

with dashboard_tab:

    st.subheader(
        "📌 Today's Schedule"
    )


    if today_manager_tasks.empty:
        st.info(
            "No tasks scheduled today."
        )

    else:

        for _, row in (
            today_manager_tasks
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

                c1, c2 = st.columns(
                    [3, 1]
                )


                with c1:

                    st.markdown(
                        f"### {row['name']}"
                    )

                    st.write(
                        f"📁 **"
                        f"{format_project(row['project'])}"
                        f"**"
                    )

                    st.caption(
                        f"👤 {row['technician']} • "
                        f"{row['start']} – "
                        f"{row['end']}"
                    )


                    location = str(
                        row["location"]
                    ).strip()

                    if location:
                        st.caption(
                            f"📍 {location}"
                        )


                with c2:

                    st.write(
                        f"{status_icon(row['status'])} "
                        f"**{row['status']}**"
                    )

                    st.caption(
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


                comments = str(
                    row[
                        "technician_comments"
                    ]
                ).strip()

                if comments:

                    with st.expander(
                        "💬 Technician Comments"
                    ):
                        st.text(comments)


    # ========================================================
    # WORKLOAD
    # ========================================================

    st.subheader(
        "👥 Team Workload — This Week"
    )


    if technicians_df.empty:
        st.info(
            "No technicians available."
        )

    else:

        for _, tech in (
            technicians_df
            .sort_values("name")
            .iterrows()
        ):

            tech_id = str(
                tech["id"]
            ).strip()

            tech_name = str(
                tech["name"]
            ).strip()

            active = bool(
                tech["active"]
            )


            tech_week = this_week[
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
            ].copy()


            tech_week = tech_week[
                tech_week["status"]
                != "Cancelled"
            ]


            hours_value = (
                pd.to_numeric(
                    tech_week["hours"],
                    errors="coerce",
                )
                .fillna(0)
                .sum()
            )


            if not active:
                workload = "⚪ Inactive"

            elif hours_value == 0:
                workload = "🟢 Available"

            elif hours_value <= 20:
                workload = "🟢 Light"

            elif hours_value <= 35:
                workload = "🟡 Normal"

            elif hours_value <= 45:
                workload = "🟠 Busy"

            else:
                workload = "🔴 Heavy"


            with st.container(
                border=True
            ):

                w1, w2, w3 = st.columns(
                    [2, 1, 1]
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
                        len(tech_week),
                    )


                with w3:
                    st.metric(
                        "Hours",
                        f"{hours_value:.1f}",
                    )


                st.progress(
                    min(
                        100,
                        int(
                            (
                                hours_value
                                / 45
                            )
                            * 100
                        ),
                    )
                )


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
                    f"**⚠️ {row['name']}**"
                )

                st.write(
                    f"📁 "
                    f"{format_project(row['project'])}"
                )

                st.caption(
                    f"👤 {row['technician']} • "
                    f"{row['date']} • "
                    f"{row['start']} • "
                    f"{row['status']}"
                )


# ============================================================
# ASSIGN
# ============================================================

with assign_tab:

    st.subheader(
        "➕ Assign Task"
    )

    st.caption(
        "Choose the time first. "
        "Only technicians who are free for the "
        "entire selected time will be available."
    )


    # These widgets intentionally sit OUTSIDE the form.
    # This lets Streamlit recalculate technician availability
    # immediately when the manager changes the schedule.

    schedule_col1, schedule_col2, schedule_col3 = (
        st.columns(3)
    )


    with schedule_col1:

        assign_date = st.date_input(
            "Date *",
            value=today,
            key="assign_date",
        )


    with schedule_col2:

        assign_start = st.time_input(
            "Start Time *",
            key="assign_start",
        )


    with schedule_col3:

        assign_hours = st.number_input(
            "Duration (hours) *",
            min_value=0.5,
            max_value=12.0,
            value=1.0,
            step=0.5,
            key="assign_hours",
        )


    assign_end_datetime = (
        datetime.combine(
            assign_date,
            assign_start,
        )
        +
        timedelta(
            hours=float(
                assign_hours
            )
        )
    )


    if (
        assign_end_datetime.date()
        != assign_date
    ):

        st.error(
            "This task would continue past midnight. "
            "Choose an earlier start time or shorter duration."
        )

        available_technicians = []

    else:

        st.info(
            f"🕐 Selected time: "
            f"{assign_start.strftime('%H:%M')} – "
            f"{assign_end_datetime.strftime('%H:%M')}"
        )


        available_technicians = (
            get_available_technicians(
                assign_date,
                assign_start,
                assign_hours,
            )
        )


        total_active = len(
            ACTIVE_TECH_NAMES
        )

        total_available = len(
            available_technicians
        )


        if available_technicians:

            st.success(
                f"✅ {total_available} of "
                f"{total_active} active technicians "
                f"available for this time."
            )

        else:

            st.warning(
                "No active technicians are available "
                "for the entire selected time."
            )


    # ========================================================
    # ASSIGN FORM
    # ========================================================

    if available_technicians:

        with st.form(
            "assign_task_form",
            clear_on_submit=True,
        ):

            task_name = st.text_input(
                "Task Name *"
            )


            selected_project = st.selectbox(
                "Project",
                [
                    "No Project"
                ]
                +
                ACTIVE_PROJECT_NAMES,
            )


            selected_tech_names = (
                st.multiselect(
                    "Available Technician(s) *",
                    available_technicians,
                )
            )


            location = st.text_input(
                "Location (optional)",
                placeholder=(
                    "Example: Workshop, Lab 2, "
                    "Customer Site..."
                ),
            )


            a1, a2 = st.columns(2)


            with a1:

                selected_priority = (
                    st.selectbox(
                        "Priority",
                        PRIORITIES,
                        index=1,
                    )
                )


            with a2:

                assigned_by = (
                    st.text_input(
                        "Assigned By *"
                    )
                )


            notes = st.text_area(
                "Manager Notes",
                height=100,
            )


            submit_assignment = (
                st.form_submit_button(
                    "➕ Assign Task",
                    use_container_width=True,
                    type="primary",
                )
            )


        if submit_assignment:

            if not task_name.strip():

                st.error(
                    "Enter a task name."
                )


            elif not selected_tech_names:

                st.error(
                    "Select at least one technician."
                )


            elif not assigned_by.strip():

                st.error(
                    "Enter who assigned the task."
                )


            else:

                project_id = ""
                project_name = ""


                if (
                    selected_project
                    != "No Project"
                ):

                    project_record = (
                        get_project_record(
                            selected_project
                        )
                    )


                    if project_record is not None:

                        project_id = str(
                            project_record["id"]
                        ).strip()

                        project_name = str(
                            project_record["name"]
                        ).strip()


                start_s = (
                    assign_start
                    .strftime("%H:%M")
                )

                end_s = (
                    assign_end_datetime
                    .strftime("%H:%M")
                )


                successful = []
                failed = []


                # Re-check availability immediately before
                # writing to Sheets.
                for technician_name in (
                    selected_tech_names
                ):

                    tech_record = (
                        get_technician_record(
                            technician_name
                        )
                    )


                    if tech_record is None:

                        failed.append(
                            f"{technician_name}: "
                            f"technician not found."
                        )

                        continue


                    technician_id = str(
                        tech_record["id"]
                    ).strip()


                    conflict, conflict_task = (
                        has_conflict(
                            df,
                            technician_id,
                            technician_name,
                            str(assign_date),
                            start_s,
                            end_s,
                        )
                    )


                    if conflict:

                        failed.append(
                            f"{technician_name}: "
                            f"now conflicts with "
                            f"'{conflict_task}'."
                        )

                        continue


                    append_row(
                        [
                            str(uuid.uuid4()),
                            task_name.strip(),
                            str(assign_date),
                            start_s,
                            end_s,
                            float(assign_hours),
                            technician_id,
                            technician_name,
                            assigned_by.strip(),
                            "Pending",
                            selected_priority,
                            0,
                            notes.strip(),
                            DEFAULT_COLOR,

                            # New columns
                            project_id,
                            project_name,
                            location.strip(),
                            "",
                        ]
                    )


                    successful.append(
                        technician_name
                    )


                for failure in failed:
                    st.error(failure)


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


# ============================================================
# CALENDAR
# ============================================================

with calendar_tab:

    st.subheader(
        "📅 Project Calendar"
    )


    calendar_filter1, calendar_filter2 = (
        st.columns(2)
    )


    with calendar_filter1:

        calendar_technician = (
            st.selectbox(
                "Technician",
                [
                    "All Technicians"
                ]
                +
                ALL_TECH_NAMES,
                key="calendar_technician",
            )
        )


    with calendar_filter2:

        calendar_project = (
            st.selectbox(
                "Project",
                [
                    "All Projects"
                ]
                +
                ALL_PROJECT_NAMES,
                key="calendar_project",
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
        ]


    if (
        calendar_project
        != "All Projects"
    ):

        calendar_df = calendar_df[
            calendar_df["project"]
            == calendar_project
        ]


    calendar_events = []


    for _, row in (
        calendar_df.iterrows()
    ):

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


            project_text = (
                str(row["project"]).strip()
            )


            if project_text:

                title = (
                    f"{project_text} | "
                    f"{row['name']} • "
                    f"{row['technician']}"
                )

            else:

                title = (
                    f"{row['name']} • "
                    f"{row['technician']}"
                )


            calendar_events.append(
                {
                    "id":
                        str(row["id"]),

                    "title":
                        title,

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


    calendar_options = {

        "initialView":
            "timeGridWeek",

        "editable":
            False,

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
            "today":
                "Today",

            "month":
                "Month",

            "week":
                "Week",

            "day":
                "Day",
        },

        "eventTimeFormat": {
            "hour":
                "2-digit",

            "minute":
                "2-digit",

            "hour12":
                False,
        },

        "slotLabelFormat": {
            "hour":
                "2-digit",

            "minute":
                "2-digit",

            "hour12":
                False,
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


    calendar(
        events=calendar_events,
        options=calendar_options,
        custom_css=calendar_css,
        key="project_calendar",
    )


# ============================================================
# TASK LIST
# ============================================================

with tasks_tab:

    st.subheader(
        f"📋 All Tasks ({len(df)})"
    )


    f1, f2, f3 = st.columns(3)


    with f1:

        filter_technician = (
            st.selectbox(
                "Technician",
                [
                    "All Technicians"
                ]
                +
                ALL_TECH_NAMES,
                key="tasks_technician",
            )
        )


    with f2:

        filter_project = (
            st.selectbox(
                "Project",
                [
                    "All Projects"
                ]
                +
                ALL_PROJECT_NAMES,
                key="tasks_project",
            )
        )


    with f3:

        filter_status = (
            st.selectbox(
                "Status",
                [
                    "All Statuses"
                ]
                +
                STATUSES,
                key="tasks_status",
            )
        )


    display_tasks = df.copy()


    if (
        filter_technician
        != "All Technicians"
    ):

        display_tasks = display_tasks[
            display_tasks["technician"]
            == filter_technician
        ]


    if (
        filter_project
        != "All Projects"
    ):

        display_tasks = display_tasks[
            display_tasks["project"]
            == filter_project
        ]


    if (
        filter_status
        != "All Statuses"
    ):

        display_tasks = display_tasks[
            display_tasks["status"]
            == filter_status
        ]


    if display_tasks.empty:

        st.info(
            "No tasks match these filters."
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
                    f"📁 **Project:** "
                    f"{format_project(row['project'])}"
                )


                st.write(
                    f"👤 **{row['technician']}**"
                )


                location = str(
                    row["location"]
                ).strip()

                if location:
                    st.write(
                        f"📍 {location}"
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


                comments = str(
                    row[
                        "technician_comments"
                    ]
                ).strip()


                if comments:

                    with st.expander(
                        "💬 Technician Comments"
                    ):
                        st.text(comments)


# ============================================================
# PROJECTS
# ============================================================

with projects_tab:

    st.subheader(
        "📁 Projects"
    )

    st.caption(
        "Create projects here, then assign tasks "
        "under those projects."
    )


    with st.form(
        "create_project_form",
        clear_on_submit=True,
    ):

        new_project_name = (
            st.text_input(
                "Project Name *"
            )
        )


        new_project_description = (
            st.text_area(
                "Project Description",
                height=100,
            )
        )


        create_project = (
            st.form_submit_button(
                "➕ Create Project",
                use_container_width=True,
                type="primary",
            )
        )


    if create_project:

        clean_name = (
            new_project_name.strip()
        )


        if not clean_name:

            st.error(
                "Enter a project name."
            )


        else:

            existing_names = [
                str(name)
                .strip()
                .lower()

                for name in (
                    projects_df[
                        "name"
                    ].tolist()
                )
            ]


            if (
                clean_name.lower()
                in existing_names
            ):

                st.error(
                    "A project with this name "
                    "already exists."
                )


            else:

                project_id = (
                    "PROJ-"
                    +
                    uuid.uuid4()
                    .hex[:8]
                    .upper()
                )


                add_project(
                    project_id,
                    clean_name,
                    new_project_description.strip(),
                    True,
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                )


                refresh_all_data()

                set_flash(
                    f"Project '{clean_name}' created."
                )

                st.rerun()


    st.divider()


    if projects_df.empty:

        st.info(
            "No projects have been created yet."
        )


    else:

        for _, project_row in (
            projects_df
            .sort_values(
                "name"
            )
            .iterrows()
        ):

            project_id = str(
                project_row["id"]
            )

            project_name = str(
                project_row["name"]
            )

            description = str(
                project_row["description"]
            ).strip()

            active = bool(
                project_row["active"]
            )


            project_tasks = df[
                (
                    df["project_id"]
                    .astype(str)
                    == project_id
                )
                |
                (
                    (
                        df["project_id"]
                        .astype(str)
                        .str.strip()
                        == ""
                    )
                    &
                    (
                        df["project"]
                        .astype(str)
                        == project_name
                    )
                )
            ]


            with st.container(
                border=True
            ):

                p1, p2 = st.columns(
                    [3, 1]
                )


                with p1:

                    st.markdown(
                        f"### 📁 {project_name}"
                    )

                    st.caption(
                        (
                            "🟢 Active"
                            if active
                            else "⚪ Inactive"
                        )
                        +
                        f" • {len(project_tasks)} tasks"
                    )


                    if description:
                        st.write(
                            description
                        )


                with p2:

                    if active:

                        if st.button(
                            "Deactivate",
                            key=(
                                f"deactivate_project_"
                                f"{project_id}"
                            ),
                            use_container_width=True,
                        ):

                            update_project(
                                project_id,
                                {
                                    "active":
                                        False
                                },
                            )

                            refresh_all_data()

                            set_flash(
                                f"{project_name} deactivated."
                            )

                            st.rerun()

                    else:

                        if st.button(
                            "Activate",
                            key=(
                                f"activate_project_"
                                f"{project_id}"
                            ),
                            use_container_width=True,
                        ):

                            update_project(
                                project_id,
                                {
                                    "active":
                                        True
                                },
                            )

                            refresh_all_data()

                            set_flash(
                                f"{project_name} activated."
                            )

                            st.rerun()


                if not project_tasks.empty:

                    with st.expander(
                        "View Project Tasks"
                    ):

                        for _, task in (
                            project_tasks
                            .sort_values(
                                [
                                    "date",
                                    "start",
                                ]
                            )
                            .iterrows()
                        ):

                            st.write(
                                f"**{task['name']}** — "
                                f"{task['technician']} — "
                                f"{task['date']} "
                                f"{task['start']} — "
                                f"{task['status']}"
                            )


# ============================================================
# ADMIN
# ============================================================

with admin_tab:

    (
        technician_admin_tab,
        task_admin_tab,
    ) = st.tabs(
        [
            "👥 Technicians",
            "✏️ Manage Tasks",
        ]
    )


    # ========================================================
    # TECHNICIAN ADMIN
    # ========================================================

    with technician_admin_tab:

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


            add_tech_submit = (
                st.form_submit_button(
                    "➕ Add Technician",
                    use_container_width=True,
                    type="primary",
                )
            )


        if add_tech_submit:

            clean_name = (
                new_technician_name
                .strip()
            )


            if not clean_name:

                st.error(
                    "Enter a technician name."
                )


            else:

                existing = [
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
                    in existing
                ):

                    st.error(
                        "Technician already exists."
                    )


                else:

                    tech_id = (
                        "TECH-"
                        +
                        uuid.uuid4()
                        .hex[:8]
                        .upper()
                    )


                    add_technician(
                        tech_id,
                        clean_name,
                        True,
                    )


                    refresh_all_data()

                    set_flash(
                        f"{clean_name} added."
                    )

                    st.rerun()


        st.divider()


        for _, tech in (
            technicians_df
            .sort_values("name")
            .iterrows()
        ):

            tech_id = str(
                tech["id"]
            )

            tech_name = str(
                tech["name"]
            )

            active = bool(
                tech["active"]
            )


            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [3, 1]
                )


                with c1:

                    st.markdown(
                        f"**👤 {tech_name}**"
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

                            st.rerun()


    # ========================================================
    # MANAGE TASKS
    # ========================================================

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


            for _, row in (
                df.iterrows()
            ):

                task_id = str(
                    row["id"]
                )

                label = (
                    f"{row['name']} | "
                    f"{row['technician']} | "
                    f"{row['date']} "
                    f"{row['start']} | "
                    f"{task_id[:8]}"
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
                    df["id"]
                    .astype(str)
                    == selected_id
                ]
                .iloc[0]
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


            current_project = str(
                selected_task[
                    "project"
                ]
            ).strip()


            edit_project_options = [
                "No Project"
            ] + ACTIVE_PROJECT_NAMES


            if (
                current_project
                and
                current_project
                not in edit_project_options
            ):

                edit_project_options.append(
                    current_project
                )


            try:

                project_index = (
                    edit_project_options.index(
                        current_project
                        if current_project
                        else "No Project"
                    )
                )

            except ValueError:

                project_index = 0


            try:

                tech_index = (
                    edit_tech_options.index(
                        current_tech
                    )
                )

            except ValueError:

                tech_index = 0


            with st.form(
                "edit_task_form"
            ):

                edit_name = st.text_input(
                    "Task Name",
                    value=str(
                        selected_task[
                            "name"
                        ]
                    ),
                )


                edit_project = st.selectbox(
                    "Project",
                    edit_project_options,
                    index=project_index,
                )


                edit_technician = (
                    st.selectbox(
                        "Technician",
                        edit_tech_options,
                        index=tech_index,
                    )
                    if edit_tech_options
                    else ""
                )


                e1, e2 = st.columns(2)


                with e1:

                    edit_date = st.date_input(
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
                            value=existing_start,
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
                            index=priority_index,
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


                edit_location = (
                    st.text_input(
                        "Location (optional)",
                        value=str(
                            selected_task[
                                "location"
                            ]
                        ),
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
                        "Manager Notes",
                        value=str(
                            selected_task[
                                "notes"
                            ]
                        ),
                    )
                )


                save_edit = (
                    st.form_submit_button(
                        "💾 Update Task",
                        use_container_width=True,
                        type="primary",
                    )
                )


            if save_edit:

                if not edit_name.strip():

                    st.error(
                        "Task name cannot be empty."
                    )


                elif not edit_technician:

                    st.error(
                        "Select a technician."
                    )


                else:

                    end_dt = (
                        datetime.combine(
                            edit_date,
                            edit_start,
                        )
                        +
                        timedelta(
                            hours=float(
                                edit_hours
                            )
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

                        start_s = (
                            edit_start
                            .strftime("%H:%M")
                        )

                        end_s = (
                            end_dt
                            .strftime("%H:%M")
                        )


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
                                f"is not available. "
                                f"Conflict: "
                                f"{conflict_task}"
                            )


                        else:

                            project_id = ""
                            project_name = ""


                            if (
                                edit_project
                                != "No Project"
                            ):

                                project_match = (
                                    projects_df[
                                        projects_df[
                                            "name"
                                        ]
                                        == edit_project
                                    ]
                                )


                                if not project_match.empty:

                                    project_id = str(
                                        project_match
                                        .iloc[0]["id"]
                                    )

                                    project_name = (
                                        edit_project
                                    )


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

                                    "project_id":
                                        project_id,

                                    "project":
                                        project_name,

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

                                    "location":
                                        edit_location
                                        .strip(),
                                },
                            )


                            if success:

                                refresh_all_data()

                                set_flash(
                                    "Task updated successfully."
                                )

                                st.rerun()


            # =================================================
            # COMMENTS VIEW
            # =================================================

            comments = str(
                selected_task[
                    "technician_comments"
                ]
            ).strip()


            if comments:

                st.subheader(
                    "💬 Technician Comments"
                )

                st.text(comments)


            # =================================================
            # DELETE
            # =================================================

            st.divider()

            st.subheader(
                "🗑️ Delete Task"
            )


            if st.button(
                "🗑️ Delete Selected Task",
                use_container_width=True,
                key="delete_selected_task",
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


                d1, d2 = st.columns(2)


                with d1:

                    if st.button(
                        "Yes, Delete",
                        type="primary",
                        use_container_width=True,
                        key="confirm_delete",
                    ):

                        delete_row(
                            selected_id
                        )

                        st.session_state.pop(
                            "confirm_delete_task",
                            None,
                        )

                        refresh_all_data()

                        set_flash(
                            "Task deleted."
                        )

                        st.rerun()


                with d2:

                    if st.button(
                        "Cancel",
                        use_container_width=True,
                        key="cancel_delete",
                    ):

                        st.session_state.pop(
                            "confirm_delete_task",
                            None,
                        )

                        st.rerun()
