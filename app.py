import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from streamlit_calendar import calendar

from sheets import get_all, append_row, init_sheet

# ----------------------
# PAGE CONFIG
# ----------------------
st.set_page_config(page_title="Technician Scheduler", layout="wide")

init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# MOBILE FRIENDLY UI
# ----------------------
st.markdown("""
<style>
/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: #f7f9fc;
    border-right: 1px solid #e0e0e0;
}

/* Inputs */
input, .stSelectbox, .stDateInput, .stTimeInput {
    border-radius: 8px !important;
}

/* Cards */
.task-card {
    background: #ffffff;
    border: 1px solid #e6e6e6;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 8px;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
    .block-container {
        padding: 10px;
    }
}
</style>
""", unsafe_allow_html=True)

# ----------------------
# LOAD DATA
# ----------------------
def load():
    data = get_all()
    df = pd.DataFrame(data)

    expected = [
        "id", "name", "date", "start", "end",
        "hours", "technician", "assigned_by", "color"
    ]

    for c in expected:
        if c not in df.columns:
            df[c] = ""

    return df


df = load()

# ----------------------
# CONFLICT CHECK
# ----------------------
def has_conflict(df, tech, date_str, start_s, end_s):
    for _, r in df.iterrows():
        if str(r["technician"]) == tech and str(r["date"]) == date_str:
            if r["start"] < end_s and start_s < r["end"]:
                return True, r["name"]
    return False, None


# ----------------------
# SAVE TASK
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
st.sidebar.title("➕ Assign Task")

name = st.sidebar.text_input("Task Name")
techs_selected = st.sidebar.multiselect("Technicians", TECHS)
d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start Time")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")

if st.sidebar.button("Save Task"):

    if not techs_selected:
        st.sidebar.error("Select at least one technician")
        st.stop()

    success = True
    conflict_msg = None

    for t in techs_selected:
        ok, conflict = save_task(name, t, d, start, hours, assigned_by)
        if not ok:
            success = False
            conflict_msg = f"{t} is busy with {conflict}"

    if success:
        st.sidebar.success("Task assigned!")
        st.rerun()
    else:
        st.sidebar.error(f"❌ Conflict: {conflict_msg}")


# ----------------------
# CALENDAR EVENTS BUILDER
# ----------------------
def build_events(df):
    events = []

    for _, r in df.iterrows():
        try:
            start_dt = datetime.strptime(f"{r['date']} {r['start']}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{r['date']} {r['end']}", "%Y-%m-%d %H:%M")

            events.append({
                "title": f"{r['name']} ({r['technician']})",
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "color": r.get("color", "#1E7E8C")
            })
        except:
            continue

    return events


events = build_events(df)

# ----------------------
# CALENDAR VIEW (DRAG & DROP)
# ----------------------
st.title("🛠 Technician Scheduler (Drag & Drop Calendar)")

calendar_options = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay"
    },
    "initialView": "timeGridWeek",
}

calendar_result = calendar(
    events=events,
    options=calendar_options,
    key="calendar"
)

# ----------------------
# HANDLE DRAG & DROP UPDATE
# ----------------------
if calendar_result and "eventDrop" in calendar_result:
    dropped = calendar_result["eventDrop"]

    event_title = dropped["event"]["title"]
    new_start = dropped["event"]["start"]
    new_end = dropped["event"]["end"]

    st.info(f"Updated: {event_title}")
    st.write("New time:", new_start, "→", new_end)

# ----------------------
# MOBILE TASK LIST BELOW CALENDAR
# ----------------------
st.subheader("📋 Task List (Mobile View)")

for _, r in df.iterrows():
    st.markdown(f"""
    <div class="task-card">
        <b>{r['name']}</b><br>
        👨‍🔧 {r['technician']}<br>
        🕒 {r['start']} → {r['end']}<br>
        📅 {r['date']}
    </div>
    """, unsafe_allow_html=True)
