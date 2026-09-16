
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from streamlit_calendar import calendar
from sheets import get_all, append_row, update_row, delete_row, init_sheet


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="R&D Project Tracker",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

init_sheet()

TECHS = [
    "Dinidu",
    "Buddhika",
    "Lakshan",
    "Maindu",
    "Naveen",
    "Samitha"
]

DEFAULT_COLOR = "#1E7E8C"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

/* =========================================================
   GLOBAL
========================================================= */

html, body, [class*="css"] {
    font-size: 14px;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

h1 {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

h2 {
    font-size: 1.4rem !important;
}

h3 {
    font-size: 1.1rem !important;
}


/* =========================================================
   HEADER
========================================================= */

.app-header {
    background: linear-gradient(
        135deg,
        #0F6674,
        #1E7E8C
    );

    padding: 18px 22px;
    border-radius: 16px;
    color: white;
    margin-bottom: 18px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.10);
}

.app-header h1 {
    margin: 0;
    color: white;
    font-size: 1.7rem !important;
}

.app-header p {
    margin: 5px 0 0 0;
    opacity: 0.9;
}


/* =========================================================
   METRIC CARDS
========================================================= */

.metric-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 16px;
    min-height: 110px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.metric-title {
    font-size: 0.85rem;
    color: #6B7280;
    margin-bottom: 6px;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #111827;
}

.metric-subtitle {
    font-size: 0.75rem;
    color: #6B7280;
    margin-top: 4px;
}


/* =========================================================
   TASK CARDS
========================================================= */

.task-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 14px 16px;
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
    margin-top: 5px;
}

.tech-badge {
    display: inline-block;
    background: #E6F4F6;
    color: #0F6674;
    padding: 4px 9px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 7px;
}


/* =========================================================
   SECTION HEADERS
========================================================= */

.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 10px;
    color: #111827;
}


/* =========================================================
   SIDEBAR
========================================================= */

section[data-testid="stSidebar"] {
    padding-top: 1rem;
}

section[data-testid="stSidebar"] .stButton button {
    min-height: 48px;
}


/* =========================================================
   BUTTONS
========================================================= */

.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
}


/* =========================================================
   CALENDAR
========================================================= */

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


/* =========================================================
   DATA EDITOR
========================================================= */

div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"] {
    font-size: 12px !important;
}


/* =========================================================
   MOBILE
========================================================= */

@media (max-width: 768px) {

    .block-container {
        padding: 0.7rem 0.7rem 2rem 0.7rem;
    }

    h1 {
        font-size: 1.35rem !important;
    }

    h2 {
        font-size: 1.15rem !important;
    }

    .app-header {
        padding: 15px;
        border-radius: 12px;
    }

    .app-header h1 {
        font-size: 1.35rem !important;
    }

    .metric-card {
        min-height: 90px;
        padding: 12px;
    }

    .metric-value {
        font-size: 1.4rem;
    }

    .metric-title {
        font-size: 0.75rem;
    }

    .task-card {
        padding: 13px;
    }

    .stButton > button {
        width: 100%;
        min-height: 48px;
    }

    /* Make tabs easier to tap */
    button[data-baseweb="tab"] {
        font-size: 0.85rem !important;
        padding: 10px 8px !important;
    }

    /* Calendar toolbar */
    .fc-toolbar {
        flex-wrap: wrap !important;
        gap: 5px !important;
    }

    .fc-toolbar-title {
        font-size: 0.9rem !important;
    }

    .fc-button {
        font-size: 11px !important;
        padding: 5px 7px !important;
    }

    /* Hide spreadsheet on phones */
    .desktop-only {
        display: none !important;
    }
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

def load():
    data = get_all()

    df = pd.DataFrame(data)

    cols = [
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

    for c in cols:
        if c not in df.columns:
            df[c] = ""

    if not df.empty:
        df["date"] = df["date"].astype(str)
        df["technician"] = df["technician"].astype(str)

    return df


df = load()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_date(value):
    try:
        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()
    except:
        return None


def has_conflict(
    data,
    tech,
    date_str,
    start_s,
    end_s,
    ignore_id=None
):

    for _, r in data.iterrows():

        if str(r["technician"]) != str(tech):
            continue

        if str(r["date"]) != str(date_str):
            continue

        if ignore_id and str(r["id"]) == str(ignore_id):
            continue

        try:

            existing_start = str(r["start"])
            existing_end = str(r["end"])

            if (
                existing_start < end_s
                and start_s < existing_end
            ):
                return True, r["name"]

        except:
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
    assigned_by
):

    start_s = start_time.strftime("%H:%M")

    end_dt = (
        datetime.combine(task_date, start_time)
        + timedelta(hours=float(hours))
    )

    end_s = end_dt.strftime("%H:%M")

    conflict, task = has_conflict(
        df,
        tech,
        str(task_date),
        start_s,
        end_s
    )

    if conflict:
        return False, task

    append_row([
        str(uuid.uuid4()),
        name,
        str(task_date),
        start_s,
        end_s,
        float(hours),
        tech,
        assigned_by,
        DEFAULT_COLOR
    ])

    return True, None


# ============================================================
# UPDATE TASK
# ============================================================

def update_task(task_id, new_start, new_end):

    for _, r in df.iterrows():

        if str(r["id"]) != str(task_id):
            continue

        tech = r["technician"]

        date_str = new_start.date().strftime(
            "%Y-%m-%d"
        )

        start_s = new_start.strftime("%H:%M")
        end_s = new_end.strftime("%H:%M")

        conflict, task = has_conflict(
            df,
            tech,
            date_str,
            start_s,
            end_s,
            task_id
        )

        if conflict:
            return False, task

        duration = (
            new_end - new_start
        ).total_seconds() / 3600

        update_row(
            task_id,
            {
                "date": date_str,
                "start": start_s,
                "end": end_s,
                "hours": round(duration, 2)
            }
        )

        return True, None

    return False, "Task not found"


# ============================================================
# DELETE TASK
# ============================================================

def delete_task(task_id):
    return delete_row(task_id)


# ============================================================
# BUILD EVENTS
# ============================================================

def build_events(data):

    events = []

    for _, r in data.iterrows():

        try:

            start_dt = datetime.strptime(
                f"{r['date']} {r['start']}",
                "%Y-%m-%d %H:%M"
            )

            end_dt = datetime.strptime(
                f"{r['date']} {r['end']}",
                "%Y-%m-%d %H:%M"
            )

            events.append({
                "id": str(r["id"]),
                "title": (
                    f"{r['name']} • "
                    f"{r['technician']}"
                ),
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "color": (
                    r.get("color", DEFAULT_COLOR)
                    or DEFAULT_COLOR
                )
            })

        except:
            continue

    return events


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="app-header">

<h1>🛠️ R&D Project Tracker</h1>

<p>
Sohan & Team • Project Schedule & Workload Monitor
</p>

</div>
""", unsafe_allow_html=True)


# ============================================================
# DATE / DATA SUMMARY
# ============================================================

today = date.today()

if not df.empty:

    valid_dates = df["date"].apply(safe_date)

    today_tasks = df[
        valid_dates == today
    ]

    week_start = today - timedelta(
        days=today.weekday()
    )

    week_end = week_start + timedelta(days=6)

    this_week = df[
        (valid_dates >= week_start)
        & (valid_dates <= week_end)
    ]

    overdue = df[
        valid_dates < today
    ]

else:

    today_tasks = pd.DataFrame()
    this_week = pd.DataFrame()
    overdue = pd.DataFrame()


# ============================================================
# MANAGER DASHBOARD
# ============================================================

st.markdown(
    '<div class="section-title">📊 Manager Overview</div>',
    unsafe_allow_html=True
)

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">TODAY</div>
            <div class="metric-value">
                {len(today_tasks)}
            </div>
            <div class="metric-subtitle">
                tasks scheduled
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with m2:
    total_hours = (
        pd.to_numeric(
            this_week["hours"],
            errors="coerce"
        ).fillna(0).sum()
        if not this_week.empty
        else 0
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">THIS WEEK</div>
            <div class="metric-value">
                {total_hours:.1f}h
            </div>
            <div class="metric-subtitle">
                planned work
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with m3:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">TEAM</div>
            <div class="metric-value">
                {len(TECHS)}
            </div>
            <div class="metric-subtitle">
                technicians
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with m4:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">OVERDUE</div>
            <div class="metric-value">
                {len(overdue)}
            </div>
            <div class="metric-subtitle">
                previous-date tasks
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.write("")


# ============================================================
# SIDEBAR - ASSIGN TASK
# ============================================================

with st.sidebar:

    st.header("➕ Assign New Task")

    st.caption(
        "Add a task to one or more technicians."
    )

    name = st.text_input(
        "Task Name",
        placeholder="e.g. Prototype testing"
    )

    techs_selected = st.multiselect(
        "Technician(s)",
        TECHS
    )

    d = st.date_input(
        "Date",
        today
    )

    start = st.time_input(
        "Start Time"
    )

    hours = st.number_input(
        "Duration (hours)",
        min_value=0.5,
        max_value=12.0,
        value=1.0,
        step=0.5
    )

    assigned_by = st.text_input(
        "Assigned By",
        placeholder="Manager name"
    )

    st.write("")

    save_clicked = st.button(
        "💾 Assign Task",
        use_container_width=True
    )

    if save_clicked:

        errors = []

        if not name.strip():
            errors.append(
                "Task name is required."
            )

        if not techs_selected:
            errors.append(
                "Select at least one technician."
            )

        if not assigned_by.strip():
            errors.append(
                "Assigned By is required."
            )

        if errors:

            for error in errors:
                st.error(error)

        else:

            for technician in techs_selected:

                ok, conflict = save_task(
                    name.strip(),
                    technician,
                    d,
                    start,
                    hours,
                    assigned_by.strip()
                )

                if not ok:

                    errors.append(
                        f"{technician} is busy with "
                        f"'{conflict}'."
                    )

            if errors:

                st.error(
                    " | ".join(errors)
                )

            else:

                st.success(
                    "✅ Task assigned successfully!"
                )

                st.rerun()


# ============================================================
# FILTERS
# ============================================================

st.markdown(
    '<div class="section-title">🔎 Quick Filters</div>',
    unsafe_allow_html=True
)

f1, f2, f3 = st.columns(3)

with f1:

    technician_filter = st.selectbox(
        "Technician",
        ["All Technicians"] + TECHS
    )

with f2:

    date_filter = st.selectbox(
        "Date",
        [
            "All Dates",
            "Today",
            "This Week",
            "Future",
            "Past"
        ]
    )

with f3:

    search_text = st.text_input(
        "Search",
        placeholder="Search task name..."
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


if date_filter != "All Dates" and not filtered_df.empty:

    dates = filtered_df["date"].apply(
        safe_date
    )

    if date_filter == "Today":

        filtered_df = filtered_df[
            dates == today
        ]

    elif date_filter == "This Week":

        filtered_df = filtered_df[
            (dates >= week_start)
            & (dates <= week_end)
        ]

    elif date_filter == "Future":

        filtered_df = filtered_df[
            dates > today
        ]

    elif date_filter == "Past":

        filtered_df = filtered_df[
            dates < today
        ]


if search_text.strip():

    search = search_text.lower()

    filtered_df = filtered_df[
        filtered_df["name"]
        .astype(str)
        .str.lower()
        .str.contains(
            search,
            na=False
        )
    ]


# ============================================================
# MAIN TABS
# ============================================================

tab_dashboard, tab_calendar, tab_tasks, tab_admin = st.tabs(
    [
        "🏠 Dashboard",
        "📅 Calendar",
        "📋 Tasks",
        "⚙️ Admin"
    ]
)


# ============================================================
# DASHBOARD TAB
# ============================================================

with tab_dashboard:

    st.subheader("Today's Work")

    if today_tasks.empty:

        st.info(
            "🎉 No tasks scheduled for today."
        )

    else:

        today_sorted = today_tasks.sort_values(
            by=["start", "technician"]
        )

        for _, row in today_sorted.iterrows():

            st.markdown(
                f"""
                <div class="task-card">

                    <div class="task-name">
                        {row["name"]}
                    </div>

                    <div class="task-meta">
                        🕐 {row["start"]} – {row["end"]}
                        &nbsp;&nbsp; • &nbsp;&nbsp;
                        ⏱️ {row["hours"]}h
                    </div>

                    <span class="tech-badge">
                        👤 {row["technician"]}
                    </span>

                    <div class="task-meta">
                        Assigned by: {row["assigned_by"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


    st.write("")

    # --------------------------------------------------------
    # TEAM WORKLOAD
    # --------------------------------------------------------

    st.subheader("👥 Team Workload")

    workload = []

    for technician in TECHS:

        technician_tasks = this_week[
            this_week["technician"]
            == technician
        ]

        hours = (
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
            "Hours": round(hours, 1)
        })

    workload_df = pd.DataFrame(
        workload
    )

    if not workload_df.empty:

        for _, row in workload_df.iterrows():

            st.markdown(
                f"""
                <div class="task-card">

                    <div class="task-name">
                        👤 {row["Technician"]}
                    </div>

                    <div class="task-meta">
                        📋 {row["Tasks"]} tasks
                        &nbsp;&nbsp; • &nbsp;&nbsp;
                        ⏱️ {row["Hours"]} hours
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


    # --------------------------------------------------------
    # OVERDUE
    # --------------------------------------------------------

    if not overdue.empty:

        st.write("")

        st.subheader("⚠️ Previous-Date Tasks")

        for _, row in overdue.head(10).iterrows():

            st.warning(
                f"**{row['name']}** — "
                f"{row['technician']} — "
                f"{row['date']}"
            )


# ============================================================
# CALENDAR TAB
# ============================================================

with tab_calendar:

    st.subheader("📅 Project Calendar")

    st.caption(
        "Drag a task to another time to reschedule it."
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

        "slotMinTime": "06:00:00",

        "slotMaxTime": "22:00:00",

        "allDaySlot": False,

        "expandRows": True,

        "headerToolbar": {

            "left": "prev,next today",

            "center": "title",

            "right": (
                "dayGridMonth,"
                "timeGridWeek,"
                "timeGridDay"
            )
        },

        "eventTimeFormat": {
            "hour": "2-digit",
            "minute": "2-digit",
            "hour12": False
        }
    }

    calendar_result = calendar(
        events=calendar_events,
        options=calendar_options,
        key="main_calendar"
    )

    if (
        calendar_result
        and isinstance(
            calendar_result,
            dict
        )
    ):

        event_type = list(
            calendar_result.keys()
        )[0]

        if event_type in [
            "eventDrop",
            "eventChange"
        ]:

            event = calendar_result[
                event_type
            ]["event"]

            task_id = event["id"]

            try:

                new_start = datetime.fromisoformat(
                    event["start"]
                )

                new_end = datetime.fromisoformat(
                    event["end"]
                )

                ok, msg = update_task(
                    task_id,
                    new_start,
                    new_end
                )

                if ok:

                    st.success(
                        "✅ Schedule updated."
                    )

                    st.rerun()

                else:

                    st.error(
                        f"❌ Cannot move task: {msg}"
                    )

            except Exception as e:

                st.error(
                    "Unable to update the task."
                )


# ============================================================
# TASK LIST TAB
# ============================================================

with tab_tasks:

    st.subheader(
        f"📋 Tasks ({len(filtered_df)})"
    )

    if filtered_df.empty:

        st.info(
            "No tasks match your filters."
        )

    else:

        display_df = filtered_df.sort_values(
            by=["date", "start"]
        )

        # ----------------------------------------------------
        # MOBILE FRIENDLY CARD VIEW
        # ----------------------------------------------------

        for _, row in display_df.iterrows():

            st.markdown(
                f"""
                <div class="task-card">

                    <div class="task-name">
                        {row["name"]}
                    </div>

                    <div class="task-meta">
                        📅 {row["date"]}
                    </div>

                    <div class="task-meta">
                        🕐 {row["start"]} – {row["end"]}
                        &nbsp;&nbsp; • &nbsp;&nbsp;
                        ⏱️ {row["hours"]}h
                    </div>

                    <span class="tech-badge">
                        👤 {row["technician"]}
                    </span>

                    <div class="task-meta">
                        👨‍💼 Assigned by:
                        {row["assigned_by"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# ADMIN TAB
# ============================================================

with tab_admin:

    st.subheader("⚙️ Task Administration")

    st.warning(
        "This section is intended mainly for managers/admins. "
        "Use the Dashboard and Calendar for normal tracking."
    )

    if df.empty:

        st.info(
            "There are no tasks to manage."
        )

    else:

        admin_df = df.copy()

        edited_df = st.data_editor(
            admin_df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "id": st.column_config.TextColumn(
                    "ID",
                    disabled=True
                ),
                "name": st.column_config.TextColumn(
                    "Task"
                ),
                "date": st.column_config.TextColumn(
                    "Date"
                ),
                "start": st.column_config.TextColumn(
                    "Start"
                ),
                "end": st.column_config.TextColumn(
                    "End"
                ),
                "hours": st.column_config.NumberColumn(
                    "Hours",
                    min_value=0,
                    step=0.5
                ),
                "technician": st.column_config.SelectboxColumn(
                    "Technician",
                    options=TECHS
                ),
                "assigned_by": st.column_config.TextColumn(
                    "Assigned By"
                ),
                "color": st.column_config.TextColumn(
                    "Color"
                )
            }
        )

        st.write("")

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "💾 Save All Changes",
                use_container_width=True
            ):

                try:

                    for _, row in edited_df.iterrows():

                        update_row(
                            row["id"],
                            row.to_dict()
                        )

                    st.success(
                        "✅ Changes saved."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Unable to save changes: {e}"
                    )

        with c2:

            delete_id = st.selectbox(
                "Select Task to Delete",
                df["id"].tolist(),
                format_func=lambda x: (
                    df.loc[
                        df["id"] == x,
                        "name"
                    ].iloc[0]
                    if not df.loc[
                        df["id"] == x
                    ].empty
                    else x
                )
            )

            if st.button(
                "🗑️ Delete Selected Task",
                use_container_width=True
            ):

                st.session_state[
                    "confirm_delete"
                ] = delete_id


        # ----------------------------------------------------
        # DELETE CONFIRMATION
        # ----------------------------------------------------

        if "confirm_delete" in st.session_state:

            confirm_id = (
                st.session_state[
                    "confirm_delete"
                ]
            )

            task_name = (
                df.loc[
                    df["id"] == confirm_id,
                    "name"
                ].iloc[0]
                if not df.loc[
                    df["id"] == confirm_id
                ].empty
                else "this task"
            )

            st.error(
                f"Are you sure you want to delete "
                f"**{task_name}**?"
            )

            d1, d2 = st.columns(2)

            with d1:

                if st.button(
                    "Yes, Delete",
                    use_container_width=True
                ):

                    delete_task(
                        confirm_id
                    )

                    del st.session_state[
                        "confirm_delete"
                    ]

                    st.success(
                        "Task deleted."
                    )

                    st.rerun()

            with d2:

                if st.button(
                    "Cancel",
                    use_container_width=True
                ):

                    del st.session_state[
                        "confirm_delete"
                    ]

                    st.rerun()
