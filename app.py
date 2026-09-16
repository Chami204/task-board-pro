import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import html

from streamlit_calendar import calendar

from sheets import (
    get_all,
    append_row,
    update_row,
    delete_row,
    init_sheet,
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
# CONFIGURATION
# ============================================================

TECHS = [
    "Dinidu",
    "Buddhika",
    "Lakshan",
    "Maindu",
    "Naveen",
    "Samitha",
]

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

COLUMNS = [
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
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

/* ---------------------------------------------------------
   GLOBAL
--------------------------------------------------------- */

html, body, [class*="css"] {
    font-size: 14px;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

h1 {
    font-size: 1.8rem !important;
}

h2 {
    font-size: 1.4rem !important;
}

h3 {
    font-size: 1.15rem !important;
}


/* ---------------------------------------------------------
   MAIN HEADER
--------------------------------------------------------- */

.app-header {
    background: linear-gradient(135deg, #0F6674, #1E7E8C);
    padding: 20px 24px;
    border-radius: 16px;
    color: white;
    margin-bottom: 18px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}

.app-header h1 {
    color: white !important;
    margin: 0;
    font-size: 1.8rem !important;
}

.app-header p {
    margin: 6px 0 0 0;
    opacity: 0.92;
}


/* ---------------------------------------------------------
   METRIC CARDS
--------------------------------------------------------- */

.metric-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 16px;
    min-height: 110px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.metric-title {
    font-size: 0.78rem;
    color: #6B7280;
    font-weight: 700;
    letter-spacing: 0.04em;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 750;
    color: #111827;
    margin-top: 4px;
}

.metric-subtitle {
    font-size: 0.78rem;
    color: #6B7280;
    margin-top: 3px;
}


/* ---------------------------------------------------------
   TASK CARDS
--------------------------------------------------------- */

.task-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 15px 17px;
    margin-bottom: 10px;
    box-shadow: 0 2px 7px rgba(0,0,0,0.04);
}

.task-name {
    font-size: 1rem;
    font-weight: 700;
    color: #111827;
}

.task-meta {
    color: #6B7280;
    font-size: 0.82rem;
    margin-top: 6px;
}

.tech-badge {
    display: inline-block;
    background: #E6F4F6;
    color: #0F6674;
    padding: 4px 9px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 650;
    margin-top: 8px;
    margin-right: 5px;
}

.status-badge {
    display: inline-block;
    background: #EEF2FF;
    color: #3730A3;
    padding: 4px 9px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 650;
    margin-top: 8px;
    margin-right: 5px;
}

.priority-low {
    background: #ECFDF5;
    color: #047857;
}

.priority-medium {
    background: #FFFBEB;
    color: #B45309;
}

.priority-high {
    background: #FFF7ED;
    color: #C2410C;
}

.priority-urgent {
    background: #FEF2F2;
    color: #B91C1C;
}


/* ---------------------------------------------------------
   WORKLOAD
--------------------------------------------------------- */

.workload-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 13px 15px;
    margin-bottom: 8px;
}

.workload-name {
    font-weight: 700;
    color: #111827;
}

.workload-meta {
    font-size: 0.82rem;
    color: #6B7280;
    margin-top: 4px;
}


/* ---------------------------------------------------------
   SECTION TITLE
--------------------------------------------------------- */

.section-title {
    font-size: 1.15rem;
    font-weight: 750;
    color: #111827;
    margin-top: 12px;
    margin-bottom: 10px;
}


/* ---------------------------------------------------------
   BUTTONS
--------------------------------------------------------- */

.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
}


/* ---------------------------------------------------------
   CALENDAR
--------------------------------------------------------- */

.fc {
    font-size: 12px !important;
}

.fc-event {
    border-radius: 6px !important;
}

.fc-event-title {
    font-size: 11px !important;
    font-weight: 600 !important;
}

.fc-toolbar-title {
    font-size: 1rem !important;
}


/* ---------------------------------------------------------
   TABLE
--------------------------------------------------------- */

div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"] {
    font-size: 12px !important;
}


/* ---------------------------------------------------------
   MOBILE
--------------------------------------------------------- */

@media (max-width: 768px) {

    html, body, [class*="css"] {
        font-size: 13px !important;
    }

    .block-container {
        padding: 0.7rem 0.65rem 2rem 0.65rem;
    }

    .app-header {
        padding: 15px;
        border-radius: 12px;
    }

    .app-header h1 {
        font-size: 1.3rem !important;
    }

    .app-header p {
        font-size: 0.8rem;
    }

    .metric-card {
        min-height: 90px;
        padding: 11px;
    }

    .metric-value {
        font-size: 1.35rem;
    }

    .metric-title {
        font-size: 0.68rem;
    }

    .metric-subtitle {
        font-size: 0.7rem;
    }

    .task-card {
        padding: 13px;
    }

    .stButton > button {
        width: 100%;
        min-height: 48px;
    }

    button[data-baseweb="tab"] {
        font-size: 0.78rem !important;
        padding: 10px 5px !important;
    }

    .fc-toolbar {
        flex-wrap: wrap !important;
        gap: 5px !important;
    }

    .fc-toolbar-title {
        font-size: 0.85rem !important;
    }

    .fc-button {
        font-size: 10px !important;
        padding: 5px 6px !important;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# INITIALIZE GOOGLE SHEET
# ============================================================

try:
    init_sheet()
except Exception as e:
    st.error("Unable to connect to Google Sheets.")
    st.exception(e)
    st.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def escape(value):
    """Escape text before inserting it into HTML."""
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def safe_date(value):
    """Convert a sheet date to Python date safely."""
    try:
        return datetime.strptime(
            str(value).strip(),
            "%Y-%m-%d"
        ).date()
    except (ValueError, TypeError):
        return None


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def priority_class(priority):
    priority = str(priority).lower().strip()

    if priority == "low":
        return "priority-low"
    elif priority == "medium":
        return "priority-medium"
    elif priority == "high":
        return "priority-high"
    elif priority == "urgent":
        return "priority-urgent"

    return ""


# ============================================================
# LOAD DATA
# ============================================================

def load():

    try:
        records = get_all()
    except Exception as e:
        st.error("Unable to load tasks from Google Sheets.")
        st.exception(e)
        return pd.DataFrame(columns=COLUMNS)

    df = pd.DataFrame(records)

    # --------------------------------------------------------
    # IMPORTANT KEYERROR FIX
    # --------------------------------------------------------
    # Even when Google Sheets has no data, the dataframe
    # will always contain all required columns.
    # --------------------------------------------------------

    for column in COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[COLUMNS].copy()

    if not df.empty:

        df["id"] = df["id"].astype(str)
        df["name"] = df["name"].astype(str)
        df["date"] = df["date"].astype(str)
        df["start"] = df["start"].astype(str)
        df["end"] = df["end"].astype(str)
        df["technician"] = df["technician"].astype(str)
        df["assigned_by"] = df["assigned_by"].astype(str)
        df["status"] = df["status"].astype(str)
        df["priority"] = df["priority"].astype(str)
        df["notes"] = df["notes"].astype(str)
        df["color"] = df["color"].astype(str)

        df["hours"] = pd.to_numeric(
            df["hours"],
            errors="coerce"
        ).fillna(0.0)

        df["progress"] = pd.to_numeric(
            df["progress"],
            errors="coerce"
        ).fillna(0)

        # Old rows without the new fields
        df.loc[
            df["status"].str.strip() == "",
            "status"
        ] = "Pending"

        df.loc[
            df["priority"].str.strip() == "",
            "priority"
        ] = "Medium"

        df.loc[
            df["color"].str.strip() == "",
            "color"
        ] = DEFAULT_COLOR

    return df


df = load()


# ============================================================
# CURRENT DATES
# ============================================================

today = date.today()

week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=6)


# ============================================================
# DATE SERIES
# ============================================================

if not df.empty:
    valid_dates = df["date"].apply(safe_date)
else:
    valid_dates = pd.Series(
        index=df.index,
        dtype="object"
    )


# ============================================================
# DASHBOARD DATA
# ============================================================

# These always preserve the original columns.
today_tasks = df[
    valid_dates == today
].copy()

this_week = df[
    (valid_dates >= week_start)
    & (valid_dates <= week_end)
].copy()

active_statuses = [
    "Pending",
    "In Progress",
    "On Hold",
]

overdue = df[
    (valid_dates < today)
    & (df["status"].isin(active_statuses))
].copy()

completed_tasks = df[
    df["status"] == "Completed"
].copy()

in_progress_tasks = df[
    df["status"] == "In Progress"
].copy()


# ============================================================
# CONFLICT CHECK
# ============================================================

def has_conflict(
    data,
    tech,
    date_str,
    start_s,
    end_s,
    ignore_id=None,
):

    if data.empty:
        return False, None

    required = {
        "technician",
        "date",
        "start",
        "end",
        "id",
        "name",
        "status",
    }

    if not required.issubset(data.columns):
        return False, None

    for _, row in data.iterrows():

        if str(row["technician"]) != str(tech):
            continue

        if str(row["date"]) != str(date_str):
            continue

        if ignore_id and str(row["id"]) == str(ignore_id):
            continue

        # Cancelled tasks should not block time.
        if str(row["status"]) == "Cancelled":
            continue

        try:

            existing_start = str(row["start"]).strip()
            existing_end = str(row["end"]).strip()

            if (
                existing_start < end_s
                and start_s < existing_end
            ):
                return True, str(row["name"])

        except Exception:
            continue

    return False, None


# ============================================================
# SAVE TASK
# ============================================================

def save_task(
    name,
    tech,
    task_date,
    start_time,
    hours,
    assigned_by,
    priority,
    notes,
):

    start_s = start_time.strftime("%H:%M")

    end_datetime = (
        datetime.combine(task_date, start_time)
        + timedelta(hours=float(hours))
    )

    # Prevent a task from silently crossing into another day.
    if end_datetime.date() != task_date:
        return False, "Task cannot continue past midnight."

    end_s = end_datetime.strftime("%H:%M")

    conflict, conflicting_task = has_conflict(
        df,
        tech,
        str(task_date),
        start_s,
        end_s,
    )

    if conflict:
        return False, conflicting_task

    append_row([
        str(uuid.uuid4()),
        name,
        str(task_date),
        start_s,
        end_s,
        float(hours),
        tech,
        assigned_by,
        "Pending",
        priority,
        0,
        notes,
        DEFAULT_COLOR,
    ])

    return True, None


# ============================================================
# UPDATE CALENDAR TASK
# ============================================================

def update_task_schedule(
    task_id,
    new_start,
    new_end,
):

    if df.empty:
        return False, "Task not found"

    matching = df[
        df["id"].astype(str) == str(task_id)
    ]

    if matching.empty:
        return False, "Task not found"

    row = matching.iloc[0]

    if new_start.date() != new_end.date():
        return False, "Tasks cannot continue into another day."

    tech = str(row["technician"])

    date_str = new_start.date().strftime(
        "%Y-%m-%d"
    )

    start_s = new_start.strftime("%H:%M")
    end_s = new_end.strftime("%H:%M")

    conflict, conflicting_task = has_conflict(
        df,
        tech,
        date_str,
        start_s,
        end_s,
        ignore_id=task_id,
    )

    if conflict:
        return False, (
            f"{tech} is already busy with "
            f"'{conflicting_task}'."
        )

    duration = (
        new_end - new_start
    ).total_seconds() / 3600

    update_row(
        task_id,
        {
            "date": date_str,
            "start": start_s,
            "end": end_s,
            "hours": round(duration, 2),
        },
    )

    return True, None


# ============================================================
# BUILD CALENDAR EVENTS
# ============================================================

def build_events(data):

    events = []

    if data.empty:
        return events

    for _, row in data.iterrows():

        try:

            start_dt = datetime.strptime(
                f"{row['date']} {row['start']}",
                "%Y-%m-%d %H:%M",
            )

            end_dt = datetime.strptime(
                f"{row['date']} {row['end']}",
                "%Y-%m-%d %H:%M",
            )

            color = (
                str(row["color"]).strip()
                if str(row["color"]).strip()
                else DEFAULT_COLOR
            )

            # Completed tasks appear green.
            if str(row["status"]) == "Completed":
                color = "#198754"

            # On-hold tasks appear orange.
            elif str(row["status"]) == "On Hold":
                color = "#F59E0B"

            # Cancelled tasks appear grey.
            elif str(row["status"]) == "Cancelled":
                color = "#6B7280"

            events.append({
                "id": str(row["id"]),
                "title": (
                    f"{row['name']} • "
                    f"{row['technician']}"
                ),
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "color": color,
            })

        except (ValueError, TypeError):
            continue

    return events


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="app-header">
        <h1>🛠️ R&D Project Tracker</h1>
        <p>
            Sohan & Team • Schedule, workload and project tracking
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("➕ Assign Task")

    st.caption(
        "Assign a new task to one or more technicians."
    )

    name = st.text_input(
        "Task Name *",
        placeholder="Example: Prototype testing",
    )

    selected_techs = st.multiselect(
        "Technician(s) *",
        TECHS,
    )

    task_date = st.date_input(
        "Date *",
        today,
    )

    start_time = st.time_input(
        "Start Time *",
        value=datetime.now().replace(
            second=0,
            microsecond=0
        ).time(),
    )

    hours = st.number_input(
        "Duration (hours) *",
        min_value=0.5,
        max_value=12.0,
        value=1.0,
        step=0.5,
    )

    priority = st.selectbox(
        "Priority",
        PRIORITIES,
        index=1,
    )

    assigned_by = st.text_input(
        "Assigned By *",
        placeholder="Manager name",
    )

    notes = st.text_area(
        "Notes",
        placeholder="Optional instructions or comments",
        height=100,
    )

    if st.button(
        "💾 Assign Task",
        use_container_width=True,
        type="primary",
    ):

        validation_errors = []

        if not name.strip():
            validation_errors.append(
                "Enter a task name."
            )

        if not selected_techs:
            validation_errors.append(
                "Select at least one technician."
            )

        if not assigned_by.strip():
            validation_errors.append(
                "Enter who assigned the task."
            )

        if validation_errors:

            for error in validation_errors:
                st.error(error)

        else:

            failed = []
            successful = []

            for technician in selected_techs:

                ok, message = save_task(
                    name=name.strip(),
                    tech=technician,
                    task_date=task_date,
                    start_time=start_time,
                    hours=hours,
                    assigned_by=assigned_by.strip(),
                    priority=priority,
                    notes=notes.strip(),
                )

                if ok:
                    successful.append(technician)
                else:
                    failed.append(
                        f"{technician}: {message}"
                    )

            if successful:
                st.success(
                    "Assigned to: "
                    + ", ".join(successful)
                )

            if failed:
                for error in failed:
                    st.error(error)
            else:
                st.rerun()


# ============================================================
# MANAGER METRICS
# ============================================================

today_active = today_tasks[
    ~today_tasks["status"].isin(
        ["Completed", "Cancelled"]
    )
]

weekly_hours = (
    pd.to_numeric(
        this_week["hours"],
        errors="coerce"
    )
    .fillna(0)
    .sum()
)

st.markdown(
    '<div class="section-title">📊 Manager Overview</div>',
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">TODAY</div>
            <div class="metric-value">{len(today_active)}</div>
            <div class="metric-subtitle">
                active tasks
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">IN PROGRESS</div>
            <div class="metric-value">{len(in_progress_tasks)}</div>
            <div class="metric-subtitle">
                current tasks
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">THIS WEEK</div>
            <div class="metric-value">{weekly_hours:.1f}h</div>
            <div class="metric-subtitle">
                planned workload
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">OVERDUE</div>
            <div class="metric-value">{len(overdue)}</div>
            <div class="metric-subtitle">
                needs attention
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# FILTERS
# ============================================================

st.write("")

with st.expander(
    "🔎 Filters",
    expanded=False,
):

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        technician_filter = st.selectbox(
            "Technician",
            ["All Technicians"] + TECHS,
        )

    with f2:
        status_filter = st.selectbox(
            "Status",
            ["All Statuses"] + STATUSES,
        )

    with f3:
        date_filter = st.selectbox(
            "Period",
            [
                "All Dates",
                "Today",
                "This Week",
                "Future",
                "Past",
            ],
        )

    with f4:
        search_text = st.text_input(
            "Search",
            placeholder="Task name...",
        )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()

if technician_filter != "All Technicians":

    filtered_df = filtered_df[
        filtered_df["technician"]
        == technician_filter
    ]


if status_filter != "All Statuses":

    filtered_df = filtered_df[
        filtered_df["status"]
        == status_filter
    ]


if not filtered_df.empty:

    filtered_dates = filtered_df[
        "date"
    ].apply(safe_date)

    if date_filter == "Today":

        filtered_df = filtered_df[
            filtered_dates == today
        ]

    elif date_filter == "This Week":

        filtered_df = filtered_df[
            (filtered_dates >= week_start)
            & (filtered_dates <= week_end)
        ]

    elif date_filter == "Future":

        filtered_df = filtered_df[
            filtered_dates > today
        ]

    elif date_filter == "Past":

        filtered_df = filtered_df[
            filtered_dates < today
        ]


if search_text.strip():

    filtered_df = filtered_df[
        filtered_df["name"]
        .astype(str)
        .str.contains(
            search_text.strip(),
            case=False,
            na=False,
        )
    ]


# ============================================================
# TABS
# ============================================================

tab_dashboard, tab_calendar, tab_tasks, tab_admin = st.tabs(
    [
        "🏠 Dashboard",
        "📅 Calendar",
        "📋 Tasks",
        "⚙️ Admin",
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

with tab_dashboard:

    # --------------------------------------------------------
    # TODAY
    # --------------------------------------------------------

    st.subheader("📌 Today's Schedule")

    if today_tasks.empty:

        st.info(
            "No tasks are scheduled for today."
        )

    else:

        today_sorted = today_tasks.sort_values(
            by=["start", "technician"]
        )

        for _, row in today_sorted.iterrows():

            p_class = priority_class(
                row["priority"]
            )

            st.markdown(
                f"""
                <div class="task-card">

                    <div class="task-name">
                        {escape(row["name"])}
                    </div>

                    <div class="task-meta">
                        🕐 {escape(row["start"])}
                        –
                        {escape(row["end"])}
                        &nbsp; • &nbsp;
                        ⏱️ {safe_float(row["hours"]):.1f}h
                    </div>

                    <span class="tech-badge">
                        👤 {escape(row["technician"])}
                    </span>

                    <span class="status-badge">
                        {escape(row["status"])}
                    </span>

                    <span class="status-badge {p_class}">
                        {escape(row["priority"])}
                    </span>

                    <div class="task-meta">
                        Progress:
                        {int(safe_float(row["progress"]))}%
                        &nbsp; • &nbsp;
                        Assigned by:
                        {escape(row["assigned_by"])}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


    # --------------------------------------------------------
    # TEAM WORKLOAD
    # --------------------------------------------------------

    st.write("")
    st.subheader("👥 Team Workload — This Week")

    workload = []

    for technician in TECHS:

        # Critical KeyError protection
        if (
            this_week.empty
            or "technician" not in this_week.columns
        ):

            technician_tasks = pd.DataFrame(
                columns=COLUMNS
            )

        else:

            technician_tasks = this_week[
                this_week["technician"].astype(str)
                == technician
            ].copy()

        # Ignore cancelled work
        if (
            not technician_tasks.empty
            and "status" in technician_tasks.columns
        ):

            technician_tasks = technician_tasks[
                technician_tasks["status"]
                != "Cancelled"
            ]

        if (
            technician_tasks.empty
            or "hours" not in technician_tasks.columns
        ):
            technician_hours = 0.0

        else:
            technician_hours = (
                pd.to_numeric(
                    technician_tasks["hours"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

        workload.append({
            "Technician": technician,
            "Tasks": len(technician_tasks),
            "Hours": round(
                float(technician_hours),
                1
            ),
        })


    workload_df = pd.DataFrame(workload)

    for _, row in workload_df.iterrows():

        hours_value = float(row["Hours"])

        if hours_value == 0:
            workload_status = "Available"
            workload_icon = "🟢"

        elif hours_value <= 20:
            workload_status = "Light"
            workload_icon = "🟢"

        elif hours_value <= 35:
            workload_status = "Normal"
            workload_icon = "🟡"

        elif hours_value <= 45:
            workload_status = "Busy"
            workload_icon = "🟠"

        else:
            workload_status = "Heavy"
            workload_icon = "🔴"

        st.markdown(
            f"""
            <div class="workload-card">

                <div class="workload-name">
                    👤 {escape(row["Technician"])}
                </div>

                <div class="workload-meta">
                    📋 {int(row["Tasks"])} tasks
                    &nbsp; • &nbsp;
                    ⏱️ {hours_value:.1f} hours
                    &nbsp; • &nbsp;
                    {workload_icon} {workload_status}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # --------------------------------------------------------
    # NEEDS ATTENTION
    # --------------------------------------------------------

    st.write("")
    st.subheader("⚠️ Needs Attention")

    if overdue.empty:

        st.success(
            "No overdue active tasks."
        )

    else:

        overdue_sorted = overdue.sort_values(
            by=["date", "start"]
        )

        for _, row in overdue_sorted.iterrows():

            st.error(
                f"{row['name']} — "
                f"{row['technician']} — "
                f"Due {row['date']} — "
                f"{row['status']}"
            )


# ============================================================
# CALENDAR
# ============================================================

with tab_calendar:

    st.subheader("📅 Project Calendar")

    st.caption(
        "Drag tasks to reschedule them. "
        "The system checks technician conflicts automatically."
    )

    calendar_events = build_events(
        filtered_df
    )

    calendar_options = {

        "editable": True,

        "selectable": True,

        "initialView": "timeGridWeek",

        "height": "auto",

        "nowIndicator": True,

        "allDaySlot": False,

        "slotMinTime": "06:00:00",

        "slotMaxTime": "22:00:00",

        "expandRows": True,

        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": (
                "dayGridMonth,"
                "timeGridWeek,"
                "timeGridDay"
            ),
        },

        "eventTimeFormat": {
            "hour": "2-digit",
            "minute": "2-digit",
            "hour12": False,
        },
    }

    calendar_result = calendar(
        events=calendar_events,
        options=calendar_options,
        key="main_calendar",
    )

    if (
        calendar_result
        and isinstance(calendar_result, dict)
    ):

        event_type = next(
            iter(calendar_result),
            None
        )

        if event_type in [
            "eventDrop",
            "eventChange",
        ]:

            try:

                event = calendar_result[
                    event_type
                ]["event"]

                task_id = event["id"]

                new_start = datetime.fromisoformat(
                    event["start"]
                )

                new_end = datetime.fromisoformat(
                    event["end"]
                )

                ok, message = update_task_schedule(
                    task_id,
                    new_start,
                    new_end,
                )

                if ok:

                    st.success(
                        "Schedule updated successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        f"❌ {message}"
                    )

            except Exception as e:

                st.error(
                    "Unable to update this calendar event."
                )


# ============================================================
# TASK LIST
# ============================================================

with tab_tasks:

    st.subheader(
        f"📋 Task List ({len(filtered_df)})"
    )

    if filtered_df.empty:

        st.info(
            "No tasks match the selected filters."
        )

    else:

        task_list = filtered_df.sort_values(
            by=["date", "start"]
        )

        for _, row in task_list.iterrows():

            p_class = priority_class(
                row["priority"]
            )

            notes_text = escape(
                row["notes"]
            )

            notes_html = ""

            if notes_text.strip():
                notes_html = (
                    f'<div class="task-meta">'
                    f'📝 {notes_text}'
                    f'</div>'
                )

            st.markdown(
                f"""
                <div class="task-card">

                    <div class="task-name">
                        {escape(row["name"])}
                    </div>

                    <div class="task-meta">
                        📅 {escape(row["date"])}
                    </div>

                    <div class="task-meta">
                        🕐 {escape(row["start"])}
                        –
                        {escape(row["end"])}
                        &nbsp; • &nbsp;
                        ⏱️ {safe_float(row["hours"]):.1f}h
                    </div>

                    <span class="tech-badge">
                        👤 {escape(row["technician"])}
                    </span>

                    <span class="status-badge">
                        {escape(row["status"])}
                    </span>

                    <span class="status-badge {p_class}">
                        {escape(row["priority"])}
                    </span>

                    <div class="task-meta">
                        📈 Progress:
                        {int(safe_float(row["progress"]))}%
                    </div>

                    <div class="task-meta">
                        👨‍💼 Assigned by:
                        {escape(row["assigned_by"])}
                    </div>

                    {notes_html}

                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# ADMIN
# ============================================================

with tab_admin:

    st.subheader("⚙️ Manager / Admin")

    st.caption(
        "Edit task details, progress and status here."
    )

    if df.empty:

        st.info(
            "There are currently no tasks."
        )

    else:

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={

                "id": st.column_config.TextColumn(
                    "ID",
                    disabled=True,
                ),

                "name": st.column_config.TextColumn(
                    "Task",
                    required=True,
                ),

                "date": st.column_config.TextColumn(
                    "Date",
                ),

                "start": st.column_config.TextColumn(
                    "Start",
                ),

                "end": st.column_config.TextColumn(
                    "End",
                ),

                "hours": st.column_config.NumberColumn(
                    "Hours",
                    min_value=0.0,
                    step=0.5,
                ),

                "technician":
                    st.column_config.SelectboxColumn(
                        "Technician",
                        options=TECHS,
                        required=True,
                    ),

                "assigned_by":
                    st.column_config.TextColumn(
                        "Assigned By",
                    ),

                "status":
                    st.column_config.SelectboxColumn(
                        "Status",
                        options=STATUSES,
                        required=True,
                    ),

                "priority":
                    st.column_config.SelectboxColumn(
                        "Priority",
                        options=PRIORITIES,
                        required=True,
                    ),

                "progress":
                    st.column_config.ProgressColumn(
                        "Progress",
                        min_value=0,
                        max_value=100,
                        format="%d%%",
                    ),

                "notes":
                    st.column_config.TextColumn(
                        "Notes",
                    ),

                "color":
                    st.column_config.TextColumn(
                        "Calendar Color",
                    ),
            },
        )

        st.write("")

        if st.button(
            "💾 Save All Changes",
            use_container_width=True,
            type="primary",
        ):

            try:

                for _, row in edited_df.iterrows():

                    task_id = str(
                        row["id"]
                    ).strip()

                    if not task_id:
                        continue

                    update_row(
                        task_id,
                        row.to_dict(),
                    )

                st.success(
                    "All changes saved successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "Unable to save changes."
                )

                st.exception(e)


        # ----------------------------------------------------
        # DELETE SECTION
        # ----------------------------------------------------

        st.divider()

        st.subheader("🗑️ Delete Task")

        task_options = {}

        for _, row in df.iterrows():

            label = (
                f"{row['name']} | "
                f"{row['technician']} | "
                f"{row['date']} {row['start']}"
            )

            task_options[label] = row["id"]


        selected_label = st.selectbox(
            "Select task",
            list(task_options.keys()),
        )

        selected_delete_id = task_options[
            selected_label
        ]


        if st.button(
            "🗑️ Delete Selected Task",
            use_container_width=True,
        ):

            st.session_state[
                "delete_confirmation"
            ] = selected_delete_id


        if (
            "delete_confirmation"
            in st.session_state
        ):

            confirmation_id = st.session_state[
                "delete_confirmation"
            ]

            matching = df[
                df["id"].astype(str)
                == str(confirmation_id)
            ]

            if not matching.empty:

                task_name_to_delete = (
                    matching.iloc[0]["name"]
                )

                st.warning(
                    f"Are you sure you want to permanently "
                    f"delete **{task_name_to_delete}**?"
                )

                delete_col1, delete_col2 = st.columns(2)

                with delete_col1:

                    if st.button(
                        "Yes, Delete",
                        use_container_width=True,
                        type="primary",
                    ):

                        delete_row(
                            confirmation_id
                        )

                        del st.session_state[
                            "delete_confirmation"
                        ]

                        st.success(
                            "Task deleted successfully."
                        )

                        st.rerun()

                with delete_col2:

                    if st.button(
                        "Cancel",
                        use_container_width=True,
                    ):

                        del st.session_state[
                            "delete_confirmation"
                        ]

                        st.rerun()
