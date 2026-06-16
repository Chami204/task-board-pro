import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from streamlit_calendar import calendar
from sheets import get_all, append_row, init_sheet

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(page_title="Technician Scheduler", layout="wide")

init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# VIEW MODE (IMPORTANT FIX)
# ----------------------
view_mode = st.radio(
    "📱 Select View Mode",
    ["📱 Mobile View", "💻 Desktop View"],
    horizontal=True
)

# ----------------------
# STYLE
# ----------------------
st.markdown("""
<style>
.task-card {
    background: #ffffff;
    border: 1px solid #e6e6e6;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
}

.small-text {
    font-size: 13px;
    color: #555;
}

section[data-testid="stSidebar"] {
    background: #f7f9fc;
}
</style>
""", unsafe_allow_html=True)

# ----------------------
# LOAD DATA
# ----------------------
def load():
    df = pd.DataFrame(get_all())

    cols = [
        "id", "name", "date", "start", "end",
        "hours", "technician", "assigned_by", "color"
    ]

    for c in cols:
        if c not in df.columns:
            df[c] = ""

    return df

df = load()

# ----------------------
# FIX: SAFE DATETIME CHECK (CRITICAL)
# ----------------------
def has_conflict(df, tech, date_str, start_s, end_s):
    for _, r in df.iterrows():

        if str(r["technician"]) != tech:
            continue

        if str(r["date"]) != date_str:
            continue

        # ensure safe compare
        try:
            existing_start = str(r["start"])
            existing_end = str(r["end"])

            if existing_start < end_s and start_s < existing_end:
                return True, r["name"]
        except:
            continue

    return False, None


# ----------------------
# SAVE TASK (MULTI TECH FIX)
# ----------------------
def save_task(name, tech, d, start, hours, assigned_by):

    start_s = start.strftime("%H:%M")
    end_dt = datetime.combine(d, start) + timedelta(hours=hours)
    end_s = end_dt.strftime("%H:%M")

    conflict, task = has_conflict(df, tech, str(d), start_s, end_s)

    if conflict:
        return False, task

    append_row([
        str(uuid.uuid4()),
        name,
        str(d),
        start_s,
        end_s,
        float(hours),
        tech,
        assigned_by,
        "#1E7E8C"
    ])

    return True, None


# ----------------------
# SIDEBAR INPUT
# ----------------------
st.sidebar.header("➕ Assign Task")

name = st.sidebar.text_input("Task Name")
techs_selected = st.sidebar.multiselect("Technicians", TECHS)
d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start Time")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")

if st.sidebar.button("Save Task"):

    if not name or not techs_selected:
        st.sidebar.error("Fill Task Name + Select Technicians")
        st.stop()

    errors = []

    for t in techs_selected:
        ok, conflict = save_task(name, t, d, start, hours, assigned_by)
        if not ok:
            errors.append(f"{t} busy with {conflict}")

    if errors:
        st.sidebar.error("❌ " + " | ".join(errors))
    else:
        st.sidebar.success("✅ Task assigned successfully")
        st.rerun()


# ----------------------
# BUILD CALENDAR EVENTS
# ----------------------
def build_events(df):
    events = []

    for _, r in df.iterrows():
        try:
            start_dt = datetime.strptime(f"{r['date']} {r['start']}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{r['date']} {r['end']}", "%Y-%m-%d %H:%M")

            events.append({
                "title": f"{r['name']} - {r['technician']}",
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "color": r.get("color", "#1E7E8C")
            })
        except:
            continue

    return events


events = build_events(df)

# ----------------------
# CALENDAR OPTIONS
# ----------------------
calendar_options = {
    "editable": False,   # safe mode (prevents sync bugs)
    "selectable": True,
    "initialView": "timeGridWeek",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay"
    }
}

# ----------------------
# MOBILE VIEW
# ----------------------
if view_mode == "📱 Mobile View":

    st.title("📱 Mobile Task View")

    calendar(
        events=events,
        options=calendar_options,
        key="mobile_calendar"
    )

    st.subheader("📋 Tasks")

    for _, r in df.iterrows():
        st.markdown(f"""
        <div class="task-card">
            <b>{r['name']}</b><br>
            👨‍🔧 {r['technician']}<br>
            🕒 {r['start']} → {r['end']}<br>
            📅 {r['date']}
        </div>
        """, unsafe_allow_html=True)


# ----------------------
# DESKTOP VIEW
# ----------------------
else:

    st.title("💻 Desktop Scheduler")

    col1, col2 = st.columns([2, 1])

    with col1:
        calendar(
            events=events,
            options=calendar_options,
            key="desktop_calendar"
        )

    with col2:
        st.subheader("📋 Task List")

        for _, r in df.iterrows():
            st.markdown(f"""
            <div class="task-card">
                <b>{r['name']}</b><br>
                👨‍🔧 {r['technician']}<br>
                🕒 {r['start']} → {r['end']}<br>
                📅 {r['date']}
            </div>
            """, unsafe_allow_html=True)
