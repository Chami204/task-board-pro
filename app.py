import streamlit as st
import pandas as pd

from datetime import (
    datetime,
    date,
    timedelta,
)

import uuid

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

/* ==========================================================
   PAGE
   ========================================================== */

.block-container {
    padding-top: 1rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}


/* ==========================================================
   BUTTONS
   ========================================================== */

.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
}

.stFormSubmitButton > button {
    border-radius: 10px;
    min-height: 46px;
    font-weight: 600;
}


/* ==========================================================
   METRICS
   ========================================================== */

div[data-testid="stMetric"] {
    border: 1px solid rgba(128, 128, 128, 0.20);
    padding: 14px;
    border-radius: 12px;
}


/* ==========================================================
   TABLE
   ========================================================== */

div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"] {
    font-size: 12px;
}


/* ==========================================================
   CALENDAR
   ========================================================== */

.fc {
    font-size: 12px !important;
    width: 100% !important;
}

.fc-view-harness {
    min-height: 600px !important;
}

.fc-event {
    border-radius: 6px !important;
    cursor: pointer !important;
}

.fc-event-title {
    font-size: 11px !important;
    font-weight: 600 !important;
}

.fc-event-time {
    font-size: 10px !important;
    font-weight: 600 !important;
}

.fc-toolbar-title {
    font-size: 1rem !important;
    font-weight: 700 !important;
}

.fc-col-header-cell-cushion {
    font-size: 11px !important;
    font-weight: 600 !important;
}

.fc-timegrid-slot-label {
    font-size: 10px !important;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 768px) {

    .block-container {
        padding-top: 0.6rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
        padding-bottom: 2rem;
    }

    h1 {
        font-size: 1.40rem !important;
    }

    h2 {
        font-size: 1.20rem !important;
    }

    h3 {
        font-size: 1.05rem !important;
    }

    .stButton > button {
        width: 100%;
        min-height: 48px;
    }

    .stFormSubmitButton > button {
        width: 100%;
        min-height: 48px;
    }

    button[data-baseweb="tab"] {
        font-size: 0.74rem !important;
        padding: 10px 5px !important;
    }

    .fc {
        font-size: 10px !important;
    }

    .fc-view-harness {
        min-height: 650px !important;
    }

    .fc-toolbar {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 5px !important;
    }

    .fc-toolbar-title {
        font-size: 0.82rem !important;
    }

    .fc-button {
        font-size: 9px !important;
        padding: 5px 6px !important;
    }

    .fc-event-title {
        font-size: 9px !important;
    }

    .fc-event-time {
        font-size: 8px !important;
    }

    .fc-col-header-cell-cushion {
        font-size: 9px !important;
    }

    .fc-timegrid-slot-label {
        font-size: 8px !important;
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

    st.error(
        "Unable to connect to Google Sheets."
    )

    st.exception(e)

    st.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_date(value):

    try:

        return datetime.strptime(
            str(value).strip(),
            "%Y-%m-%d",
        ).date()

    except (
        ValueError,
        TypeError,
    ):

        return None


def safe_float(
    value,
    default=0.0,
):

    try:
        return float(value)

    except (
        ValueError,
        TypeError,
    ):
        return default


def safe_int(
    value,
    default=0,
):

    try:
        return int(
            float(value)
        )

    except (
        ValueError,
        TypeError,
    ):
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

    icons = {
        "Pending": "🕓",
        "In Progress": "🔄",
        "Completed": "✅",
        "On Hold": "⏸️",
        "Cancelled": "❌",
    }

    return icons.get(
        str(status),
        "📌",
    )


def priority_icon(priority):

    icons = {
        "Low": "🟢",
        "Medium": "🟡",
        "High": "🟠",
        "Urgent": "🔴",
    }

    return icons.get(
        str(priority),
        "⚪",
    )


# ============================================================
# LOAD TASKS
# ============================================================

@st.cache_data(
    show_spinner=False
)
def load_tasks():

    records = get_all()

    data = pd.DataFrame(
        records
    )

    for column in TASK_COLUMNS:

        if column not in data.columns:
            data[column] = ""

    data = data[
        TASK_COLUMNS
    ].copy()

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
            data["status"]
            .str.strip()
            == "",
            "status",
        ] = "Pending"

        data.loc[
            data["priority"]
            .str.strip()
            == "",
            "priority",
        ] = "Medium"

        data.loc[
            data["color"]
            .str.strip()
            == "",
            "color",
        ] = DEFAULT_COLOR

    return data


# ============================================================
# LOAD TECHNICIANS
# ============================================================

@st.cache_data(
    show_spinner=False
)
def load_technicians():

    records = get_technicians()

    data = pd.DataFrame(
        records
    )

    required = [
        "id",
        "name",
        "active",
    ]

    for column in required:

        if column not in data.columns:
            data[column] = ""

    data = data[
        required
    ].copy()

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
            .apply(
                is_active_value
            )
        )

    return data


# ============================================================
# REFRESH
# ============================================================

def refresh_all_data():

    load_tasks.clear()

    load_technicians.clear()


# ============================================================
# HEADER
# ============================================================

header_col, refresh_col = (
    st.columns(
        [5, 1]
    )
)


with header_col:

    st.title(
        "🛠️ R&D Project Tracker"
    )

    st.caption(
        "Sohan & Team • Schedule, workload and project tracking"
    )


with refresh_col:

    st.write("")

    st.write("")

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
        help=(
            "Reload all tracker data "
            "from Google Sheets"
        ),
    ):

        refresh_all_data()

        st.session_state[
            "refresh_success"
        ] = True

        st.rerun()


if st.session_state.pop(
    "refresh_success",
    False,
):

    st.success(
        "✅ All tracker data refreshed."
    )


# ============================================================
# LOAD DATA
# ============================================================

try:

    df = load_tasks()

    technicians_df = (
        load_technicians()
    )

except Exception as e:

    st.error(
        "Unable to load tracker data."
    )

    st.exception(e)

    st.stop()


# ============================================================
# ACTIVE TECHNICIANS
# ============================================================

if technicians_df.empty:

    active_technicians_df = (
        pd.DataFrame(
            columns=[
                "id",
                "name",
                "active",
            ]
        )
    )

else:

    active_technicians_df = (
        technicians_df[
            technicians_df[
                "active"
            ]
            == True
        ]
        .copy()
        .sort_values(
            "name"
        )
    )


ACTIVE_TECH_NAMES = (
    active_technicians_df[
        "name"
    ].tolist()
)


ALL_TECH_NAMES = sorted(
    set(
        technicians_df[
            "name"
        ].tolist()
        +
        df[
            "technician"
        ].tolist()
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

    valid_dates = (
        df["date"]
        .apply(
            safe_date
        )
    )

else:

    valid_dates = (
        pd.Series(
            index=df.index,
            dtype="object",
        )
    )


# ============================================================
# DASHBOARD DATA
# ============================================================

today_tasks = df[
    valid_dates
    == today
].copy()


this_week = df[
    (
        valid_dates
        >= week_start
    )
    &
    (
        valid_dates
        <= week_end
    )
].copy()


active_statuses = [
    "Pending",
    "In Progress",
    "On Hold",
]


overdue = df[
    (
        valid_dates
        < today
    )
    &
    (
        df["status"]
        .isin(
            active_statuses
        )
    )
].copy()


in_progress_tasks = df[
    df["status"]
    == "In Progress"
].copy()


# ============================================================
# TECHNICIAN LOOKUP
# ============================================================

def get_technician_record(
    technician_name,
):

    if active_technicians_df.empty:
        return None

    matching = (
        active_technicians_df[
            active_technicians_df[
                "name"
            ]
            == technician_name
        ]
    )

    if matching.empty:
        return None

    return matching.iloc[0]


# ============================================================
# CONFLICT CHECK
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


        if (
            technician_id
            and row_tech_id
        ):

            same_technician = (
                row_tech_id
                == str(
                    technician_id
                )
            )

        else:

            same_technician = (
                row_tech_name
                == str(
                    technician_name
                )
            )


        if not same_technician:
            continue


        if (
            str(
                row["date"]
            ).strip()
            != str(date_str)
        ):
            continue


        if (
            ignore_id
            and str(
                row["id"]
            )
            == str(ignore_id)
        ):
            continue


        if (
            str(
                row["status"]
            )
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
            or not existing_end
        ):
            continue


        if (
            existing_start
            < end_s
            and
            start_s
            < existing_end
        ):

            return (
                True,
                str(
                    row["name"]
                ),
            )

    return False, None


# ============================================================
# SAVE TASK
# ============================================================

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
        start_time
        .strftime("%H:%M")
    )


    end_datetime = (
        datetime.combine(
            task_date,
            start_time,
        )
        +
        timedelta(
            hours=float(
                hours
            )
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


    end_s = (
        end_datetime
        .strftime("%H:%M")
    )


    conflict, task = (
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
            f"Busy with '{task}'",
        )


    append_row(
        [
            str(
                uuid.uuid4()
            ),
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


# ============================================================
# UPDATE SCHEDULE
# ============================================================

def update_task_schedule(
    task_id,
    new_start,
    new_end,
):

    matching = df[
        df["id"]
        .astype(str)
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
        .strftime(
            "%Y-%m-%d"
        )
    )

    start_s = (
        new_start
        .strftime("%H:%M")
    )

    end_s = (
        new_end
        .strftime("%H:%M")
    )


    conflict, task = (
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
            f"{technician_name} is busy with '{task}'.",
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


# ============================================================
# CALENDAR EVENTS
# ============================================================

def build_events(data):

    events = []

    if data.empty:
        return events


    for _, row in data.iterrows():

        try:

            start_dt = (
                datetime.strptime(
                    f"{row['date']} "
                    f"{row['start']}",
                    "%Y-%m-%d %H:%M",
                )
            )

            end_dt = (
                datetime.strptime(
                    f"{row['date']} "
                    f"{row['end']}",
                    "%Y-%m-%d %H:%M",
                )
            )


            color = (
                str(
                    row["color"]
                ).strip()
                or DEFAULT_COLOR
            )


            if (
                row["status"]
                == "Completed"
            ):
                color = "#198754"

            elif (
                row["status"]
                == "On Hold"
            ):
                color = "#F59E0B"

            elif (
                row["status"]
                == "Cancelled"
            ):
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


# ============================================================
# MANAGER OVERVIEW
# ============================================================

today_active = (
    today_tasks[
        ~today_tasks[
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
        this_week[
            "hours"
        ],
        errors="coerce",
    )
    .fillna(0)
    .sum()
)


st.subheader(
    "📊 Manager Overview"
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
        len(
            in_progress_tasks
        ),
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
# FILTERS
# ============================================================

with st.expander(
    "🔎 Filters",
    expanded=False,
):

    with st.form(
        "filters_form"
    ):

        f1, f2, f3, f4 = (
            st.columns(4)
        )


        with f1:

            technician_input = (
                st.selectbox(
                    "Technician",
                    [
                        "All Technicians"
                    ]
                    +
                    ALL_TECH_NAMES,
                )
            )


        with f2:

            status_input = (
                st.selectbox(
                    "Status",
                    [
                        "All Statuses"
                    ]
                    +
                    STATUSES,
                )
            )


        with f3:

            period_input = (
                st.selectbox(
                    "Period",
                    [
                        "All Dates",
                        "Today",
                        "This Week",
                        "Future",
                        "Past",
                    ],
                )
            )


        with f4:

            search_input = (
                st.text_input(
                    "Search",
                    placeholder=(
                        "Task name..."
                    ),
                )
            )


        apply_filters = (
            st.form_submit_button(
                "🔎 Apply Filters",
                use_container_width=True,
            )
        )


    if apply_filters:

        st.session_state[
            "technician_filter"
        ] = technician_input

        st.session_state[
            "status_filter"
        ] = status_input

        st.session_state[
            "period_filter"
        ] = period_input

        st.session_state[
            "search_filter"
        ] = search_input


# ============================================================
# FILTER VALUES
# ============================================================

technician_filter = (
    st.session_state.get(
        "technician_filter",
        "All Technicians",
    )
)

status_filter = (
    st.session_state.get(
        "status_filter",
        "All Statuses",
    )
)

period_filter = (
    st.session_state.get(
        "period_filter",
        "All Dates",
    )
)

search_filter = (
    st.session_state.get(
        "search_filter",
        "",
    )
)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()


if (
    technician_filter
    != "All Technicians"
):

    filtered_df = (
        filtered_df[
            filtered_df[
                "technician"
            ]
            == technician_filter
        ]
    )


if (
    status_filter
    != "All Statuses"
):

    filtered_df = (
        filtered_df[
            filtered_df[
                "status"
            ]
            == status_filter
        ]
    )


if not filtered_df.empty:

    filtered_dates = (
        filtered_df[
            "date"
        ]
        .apply(
            safe_date
        )
    )


    if (
        period_filter
        == "Today"
    ):

        filtered_df = (
            filtered_df[
                filtered_dates
                == today
            ]
        )


    elif (
        period_filter
        == "This Week"
    ):

        filtered_df = (
            filtered_df[
                (
                    filtered_dates
                    >= week_start
                )
                &
                (
                    filtered_dates
                    <= week_end
                )
            ]
        )


    elif (
        period_filter
        == "Future"
    ):

        filtered_df = (
            filtered_df[
                filtered_dates
                > today
            ]
        )


    elif (
        period_filter
        == "Past"
    ):

        filtered_df = (
            filtered_df[
                filtered_dates
                < today
            ]
        )


if search_filter.strip():

    filtered_df = (
        filtered_df[
            filtered_df[
                "name"
            ]
            .astype(str)
            .str.contains(
                search_filter.strip(),
                case=False,
                na=False,
            )
        ]
    )


# ============================================================
# TABS
# ============================================================

(
    tab_dashboard,
    tab_assign,
    tab_calendar,
    tab_tasks,
    tab_admin,
) = st.tabs(
    [
        "🏠 Dashboard",
        "➕ Assign",
        "📅 Calendar",
        "📋 Tasks",
        "⚙️ Admin",
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

with tab_dashboard:

    st.subheader(
        "📌 Today's Schedule"
    )


    if today_tasks.empty:

        st.info(
            "No tasks are scheduled for today."
        )


    else:

        today_sorted = (
            today_tasks
            .sort_values(
                [
                    "start",
                    "technician",
                ]
            )
        )


        for _, row in (
            today_sorted.iterrows()
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
                        f"{row['priority']} Priority"
                    )


                d1, d2, d3 = (
                    st.columns(3)
                )


                with d1:

                    st.write(
                        f"📅 **{row['date']}**"
                    )


                with d2:

                    st.write(
                        f"🕐 **"
                        f"{row['start']} – "
                        f"{row['end']}**"
                    )


                with d3:

                    st.write(
                        f"⏱️ **"
                        f"{safe_float(row['hours']):.1f} h**"
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


                st.caption(
                    f"Progress: {progress}%"
                )

                st.progress(
                    progress
                )


                notes = str(
                    row["notes"]
                ).strip()


                if notes:

                    st.caption(
                        f"📝 {notes}"
                    )


    # ========================================================
    # WORKLOAD
    # ========================================================

    st.subheader(
        "👥 Team Workload — This Week"
    )


    if technicians_df.empty:

        st.info(
            "No technicians have been added."
        )


    else:

        for _, tech_row in (
            technicians_df
            .sort_values(
                "name"
            )
            .iterrows()
        ):

            technician_id = str(
                tech_row["id"]
            ).strip()

            technician_name = str(
                tech_row["name"]
            ).strip()

            active = bool(
                tech_row["active"]
            )


            if this_week.empty:

                technician_tasks = (
                    pd.DataFrame(
                        columns=TASK_COLUMNS
                    )
                )

            else:

                technician_tasks = (
                    this_week[
                        (
                            this_week[
                                "technician_id"
                            ]
                            .astype(str)
                            == technician_id
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
                                ]
                                .astype(str)
                                == technician_name
                            )
                        )
                    ]
                    .copy()
                )


            if not technician_tasks.empty:

                technician_tasks = (
                    technician_tasks[
                        technician_tasks[
                            "status"
                        ]
                        != "Cancelled"
                    ]
                )


            hours_value = (
                pd.to_numeric(
                    technician_tasks[
                        "hours"
                    ],
                    errors="coerce",
                )
                .fillna(0)
                .sum()
            )


            if not active:

                workload_status = (
                    "⚪ Inactive"
                )

            elif hours_value == 0:

                workload_status = (
                    "🟢 Available"
                )

            elif hours_value <= 20:

                workload_status = (
                    "🟢 Light"
                )

            elif hours_value <= 35:

                workload_status = (
                    "🟡 Normal"
                )

            elif hours_value <= 45:

                workload_status = (
                    "🟠 Busy"
                )

            else:

                workload_status = (
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
                        f"**👤 "
                        f"{technician_name}**"
                    )

                    st.caption(
                        workload_status
                    )


                with w2:

                    st.metric(
                        "Tasks",
                        len(
                            technician_tasks
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


    # ========================================================
    # OVERDUE
    # ========================================================

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
                    f"👤 {row['technician']}"
                )

                st.caption(
                    f"Due {row['date']} • "
                    f"{row['start']} • "
                    f"{row['status']} • "
                    f"{row['priority']} Priority"
                )


# ============================================================
# ASSIGN
# ============================================================

with tab_assign:

    st.subheader(
        "➕ Assign New Task"
    )

    st.caption(
        "Assign a task to one or multiple technicians. "
        "Schedule conflicts are checked automatically."
    )


    if active_technicians_df.empty:

        st.warning(
            "There are no active technicians. "
            "Go to Admin and add or activate technicians."
        )


    else:

        with st.form(
            "assign_task_form",
            clear_on_submit=True,
        ):

            task_name = (
                st.text_input(
                    "Task Name *",
                    placeholder=(
                        "Example: Prototype testing"
                    ),
                )
            )


            selected_tech_names = (
                st.multiselect(
                    "Technician(s) *",
                    ACTIVE_TECH_NAMES,
                )
            )


            a1, a2 = (
                st.columns(2)
            )


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


            a3, a4 = (
                st.columns(2)
            )


            with a3:

                selected_hours = (
                    st.number_input(
                        "Duration (hours) *",
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
                    "Assigned By *",
                    placeholder=(
                        "Manager name"
                    ),
                )
            )


            selected_notes = (
                st.text_area(
                    "Notes",
                    placeholder=(
                        "Instructions or comments"
                    ),
                    height=100,
                )
            )


            submitted = (
                st.form_submit_button(
                    "➕ Assign Task",
                    use_container_width=True,
                    type="primary",
                )
            )


        if submitted:

            errors = []


            if not task_name.strip():

                errors.append(
                    "Enter a task name."
                )


            if not selected_tech_names:

                errors.append(
                    "Select at least one technician."
                )


            if not selected_assigned_by.strip():

                errors.append(
                    "Enter who assigned the task."
                )


            if errors:

                for error in errors:
                    st.error(error)


            else:

                successful = []
                failed = []


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
                            f"Technician not found."
                        )

                        continue


                    technician_id = str(
                        tech_record[
                            "id"
                        ]
                    ).strip()


                    ok, message = (
                        save_task(
                            task_name.strip(),
                            technician_id,
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


                if failed:

                    for error in failed:
                        st.error(error)


                if successful:

                    refresh_all_data()

                    st.session_state[
                        "task_added_message"
                    ] = (
                        "Task assigned successfully to "
                        +
                        ", ".join(
                            successful
                        )
                    )

                    st.rerun()


# ============================================================
# CALENDAR
# ============================================================

with tab_calendar:

    st.subheader(
        "📅 Project Calendar"
    )

    st.caption(
        "View the full team schedule. "
        "Drag a task to another time or day to reschedule it."
    )


    calendar_filter_col1, calendar_filter_col2 = (
        st.columns(
            [2, 1]
        )
    )


    with calendar_filter_col1:

        calendar_technician = (
            st.selectbox(
                "Show technician",
                [
                    "All Technicians"
                ]
                +
                ALL_TECH_NAMES,
                key=(
                    "calendar_technician_filter"
                ),
            )
        )


    with calendar_filter_col2:

        show_completed = (
            st.checkbox(
                "Show completed",
                value=True,
                key=(
                    "calendar_show_completed"
                ),
            )
        )


    calendar_df = df.copy()


    if (
        calendar_technician
        != "All Technicians"
    ):

        calendar_df = (
            calendar_df[
                calendar_df[
                    "technician"
                ]
                == calendar_technician
            ]
            .copy()
        )


    if not show_completed:

        calendar_df = (
            calendar_df[
                ~calendar_df[
                    "status"
                ].isin(
                    [
                        "Completed",
                        "Cancelled",
                    ]
                )
            ]
            .copy()
        )


    calendar_events = (
        build_events(
            calendar_df
        )
    )


    calendar_options = {
        "initialView": "timeGridWeek",
        "editable": True,
        "selectable": True,
        "navLinks": True,
        "nowIndicator": True,
        "allDaySlot": False,
        "height": 700,
    
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
    
        "slotMinTime": "06:00:00",
        "slotMaxTime": "22:00:00",
        "slotDuration": "00:30:00",
        "scrollTime": "08:00:00",
    }
    # ============================================================
    # CALENDAR COMPONENT CSS
    # ============================================================
    
    calendar_css = """
    .fc {
        font-size: 12px;
    }
    
    .fc-toolbar-title {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
    }
    
    .fc-button {
        border-radius: 6px !important;
    }
    
    .fc-timegrid-slot {
        height: 38px !important;
    }
    
    .fc-timegrid-slot-label {
        font-size: 10px !important;
    }
    
    .fc-col-header-cell-cushion {
        font-size: 11px !important;
        font-weight: 600 !important;
    }
    
    .fc-event {
        border-radius: 5px !important;
        padding: 2px !important;
        cursor: pointer !important;
    }
    
    .fc-event-title {
        font-size: 10px !important;
        font-weight: 600 !important;
    }
    
    .fc-event-time {
        font-size: 9px !important;
        font-weight: 600 !important;
    }
    
    .fc-daygrid-day-number {
        font-size: 11px !important;
    }
    
    .fc-scrollgrid {
        border-radius: 8px !important;
    }
"""

    calendar_result = calendar(
        events=calendar_events,
        options=calendar_options,
        custom_css=calendar_css,
        callbacks=[
            "eventClick",
            "eventChange",
            "eventDrop",
            "eventResize",
            "eventsSet",
        ],
        key="project_calendar",
    )


    if calendar_df.empty:

        st.info(
            "There are currently no tasks "
            "to display on the calendar."
        )

    else:

        st.caption(
            f"📌 Showing "
            f"{len(calendar_df)} "
            f"scheduled task(s)"
        )


    # --------------------------------------------------------
    # CALENDAR DRAG / RESIZE
    # --------------------------------------------------------

    if (
        calendar_result
        and isinstance(
            calendar_result,
            dict,
        )
    ):

        event_type = next(
            iter(
                calendar_result
            ),
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
                    event.get(
                        "start"
                    )
                )


                end_value = (
                    event.get(
                        "end"
                    )
                )


                if (
                    not task_id
                    or not start_value
                ):

                    st.error(
                        "Unable to identify "
                        "the calendar task."
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

                        matching_task = (
                            df[
                                df["id"]
                                .astype(str)
                                == task_id
                            ]
                        )


                        if matching_task.empty:

                            st.error(
                                "Task not found."
                            )

                            st.stop()


                        original_hours = (
                            safe_float(
                                matching_task
                                .iloc[0][
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

                        st.rerun()


                    else:

                        st.error(
                            f"❌ {message}"
                        )


            except Exception as e:

                st.error(
                    "Calendar change "
                    "could not be saved."
                )

                st.exception(e)


# ============================================================
# TASKS
# ============================================================

with tab_tasks:

    st.subheader(
        f"📋 Tasks ({len(filtered_df)})"
    )


    if filtered_df.empty:

        st.info(
            "No tasks match the selected filters."
        )


    else:

        task_list = (
            filtered_df
            .sort_values(
                [
                    "date",
                    "start",
                ]
            )
        )


        for _, row in (
            task_list.iterrows()
        ):

            with st.container(
                border=True
            ):

                t1, t2 = (
                    st.columns(
                        [3, 1]
                    )
                )


                with t1:

                    st.markdown(
                        f"### {row['name']}"
                    )

                    st.caption(
                        f"👤 {row['technician']} • "
                        f"Assigned by "
                        f"{row['assigned_by']}"
                    )


                with t2:

                    st.write(
                        f"**"
                        f"{status_icon(row['status'])} "
                        f"{row['status']}**"
                    )

                    st.caption(
                        f"{priority_icon(row['priority'])} "
                        f"{row['priority']} Priority"
                    )


                d1, d2, d3 = (
                    st.columns(3)
                )


                with d1:

                    st.write(
                        f"📅 **{row['date']}**"
                    )


                with d2:

                    st.write(
                        f"🕐 **"
                        f"{row['start']} – "
                        f"{row['end']}**"
                    )


                with d3:

                    st.write(
                        f"⏱️ **"
                        f"{safe_float(row['hours']):.1f} h**"
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


                st.caption(
                    f"Progress: {progress}%"
                )

                st.progress(
                    progress
                )


                notes = str(
                    row["notes"]
                ).strip()


                if notes:

                    st.caption(
                        f"📝 {notes}"
                    )


# ============================================================
# ADMIN
# ============================================================

with tab_admin:

    st.subheader(
        "⚙️ Manager / Admin"
    )


    (
        admin_tech_tab,
        admin_task_tab,
    ) = st.tabs(
        [
            "👥 Manage Technicians",
            "✏️ Manage Tasks",
        ]
    )


    # ========================================================
    # TECHNICIANS
    # ========================================================

    with admin_tech_tab:

        st.subheader(
            "👥 Technicians"
        )

        st.caption(
            "Add technicians or activate/deactivate them."
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
                        "That technician already exists."
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

                    st.rerun()


        st.divider()


        if technicians_df.empty:

            st.info(
                "No technicians added."
            )


        else:

            for _, tech_row in (
                technicians_df
                .sort_values(
                    "name"
                )
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

                    tc1, tc2 = (
                        st.columns(
                            [3, 1]
                        )
                    )


                    with tc1:

                        st.markdown(
                            f"**👤 {tech_name}**"
                        )


                        if active:

                            st.caption(
                                f"🟢 Active • "
                                f"{tech_id}"
                            )

                        else:

                            st.caption(
                                f"⚪ Inactive • "
                                f"{tech_id}"
                            )


                    with tc2:

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

    with admin_task_tab:

        st.subheader(
            "✏️ Manage Tasks"
        )

        st.caption(
            "Select one task, make the required changes, "
            "then press Update Task."
        )


        if df.empty:

            st.info(
                "There are currently no tasks."
            )


        else:

            task_options = {}


            for _, row in (
                df.iterrows()
            ):

                label = (
                    f"{row['name']} | "
                    f"{row['technician']} | "
                    f"{row['date']} "
                    f"{row['start']}"
                )


                task_options[
                    label
                ] = str(
                    row["id"]
                )


            selected_task_label = (
                st.selectbox(
                    "Select Task",
                    list(
                        task_options.keys()
                    ),
                )
            )


            selected_task_id = (
                task_options[
                    selected_task_label
                ]
            )


            selected_task = (
                df[
                    df["id"]
                    .astype(str)
                    == selected_task_id
                ]
                .iloc[0]
            )


            # =================================================
            # EDIT FORM
            # =================================================

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


                technician_options = (
                    ALL_TECH_NAMES.copy()
                )


                current_technician = str(
                    selected_task[
                        "technician"
                    ]
                )


                if (
                    current_technician
                    and
                    current_technician
                    not in technician_options
                ):

                    technician_options.append(
                        current_technician
                    )


                technician_options = (
                    sorted(
                        technician_options
                    )
                )


                if technician_options:

                    try:

                        technician_index = (
                            technician_options
                            .index(
                                current_technician
                            )
                        )

                    except ValueError:

                        technician_index = 0


                    edit_technician = (
                        st.selectbox(
                            "Technician",
                            technician_options,
                            index=(
                                technician_index
                            ),
                        )
                    )

                else:

                    edit_technician = (
                        current_technician
                    )

                    st.warning(
                        "No technicians available."
                    )


                ec1, ec2 = (
                    st.columns(2)
                )


                with ec1:

                    current_date = (
                        safe_date(
                            selected_task[
                                "date"
                            ]
                        )
                        or today
                    )


                    edit_date = (
                        st.date_input(
                            "Date",
                            value=(
                                current_date
                            ),
                        )
                    )


                with ec2:

                    try:

                        current_start = (
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

                        current_start = (
                            datetime.now()
                            .replace(
                                second=0,
                                microsecond=0,
                            )
                            .time()
                        )


                    edit_start = (
                        st.time_input(
                            "Start Time",
                            value=(
                                current_start
                            ),
                        )
                    )


                ec3, ec4 = (
                    st.columns(2)
                )


                with ec3:

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


                with ec4:

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


                ec5, ec6 = (
                    st.columns(2)
                )


                with ec5:

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
                            index=(
                                status_index
                            ),
                        )
                    )


                with ec6:

                    edit_progress = (
                        st.slider(
                            "Progress %",
                            min_value=0,
                            max_value=100,
                            value=max(
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
                            step=5,
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


                save_changes = (
                    st.form_submit_button(
                        "💾 Update Task",
                        use_container_width=True,
                        type="primary",
                    )
                )


            # =================================================
            # SAVE EDIT
            # =================================================

            if save_changes:

                if not edit_name.strip():

                    st.error(
                        "Task name cannot be empty."
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


                    technician_id = (
                        str(
                            tech_match
                            .iloc[0][
                                "id"
                            ]
                        )
                        if not tech_match.empty
                        else ""
                    )


                    start_string = (
                        edit_start
                        .strftime(
                            "%H:%M"
                        )
                    )


                    end_datetime = (
                        datetime.combine(
                            edit_date,
                            edit_start,
                        )
                        +
                        timedelta(
                            hours=(
                                edit_hours
                            )
                        )
                    )


                    if (
                        end_datetime.date()
                        != edit_date
                    ):

                        st.error(
                            "Task cannot continue "
                            "past midnight."
                        )


                    else:

                        end_string = (
                            end_datetime
                            .strftime(
                                "%H:%M"
                            )
                        )


                        conflict, conflict_task = (
                            has_conflict(
                                df,
                                technician_id,
                                edit_technician,
                                str(
                                    edit_date
                                ),
                                start_string,
                                end_string,
                                ignore_id=(
                                    selected_task_id
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

                            update_row(
                                selected_task_id,
                                {
                                    "name":
                                        edit_name.strip(),

                                    "date":
                                        str(
                                            edit_date
                                        ),

                                    "start":
                                        start_string,

                                    "end":
                                        end_string,

                                    "hours":
                                        float(
                                            edit_hours
                                        ),

                                    "technician_id":
                                        technician_id,

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
                                        int(
                                            edit_progress
                                        ),

                                    "notes":
                                        edit_notes
                                        .strip(),
                                },
                            )


                            refresh_all_data()

                            st.rerun()


            # =================================================
            # DELETE TASK
            # =================================================

            st.divider()

            st.subheader(
                "🗑️ Delete Task"
            )

            st.caption(
                "Deleting a task permanently removes it "
                "from the tracker and Google Sheet."
            )


            if st.button(
                "🗑️ Delete Selected Task",
                use_container_width=True,
            ):

                st.session_state[
                    "confirm_delete_task"
                ] = selected_task_id


            if (
                st.session_state.get(
                    "confirm_delete_task"
                )
                == selected_task_id
            ):

                st.warning(
                    f"Are you sure you want to delete "
                    f"**{selected_task['name']}**?"
                )


                dc1, dc2 = (
                    st.columns(2)
                )


                with dc1:

                    if st.button(
                        "Yes, Delete",
                        use_container_width=True,
                        type="primary",
                    ):

                        delete_row(
                            selected_task_id
                        )

                        st.session_state.pop(
                            "confirm_delete_task",
                            None,
                        )

                        refresh_all_data()

                        st.rerun()


                with dc2:

                    if st.button(
                        "Cancel",
                        use_container_width=True,
                    ):

                        st.session_state.pop(
                            "confirm_delete_task",
                            None,
                        )

                        st.rerun()
