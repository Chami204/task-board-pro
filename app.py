import streamlit as st
import pandas as pd
from datetime import datetime, date
import uuid

from streamlit_calendar import calendar
from sheets import get_all, append_row, init_sheet

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(page_title="Task Scheduler", layout="wide")

init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# LOAD DATA
# ----------------------
def load():
    df = pd.DataFrame(get_all())

    expected = ["id","name","date","start","end","hours","technician","assigned_by","color"]
    for c in expected:
        if c not in df.columns:
            df[c] = ""

    return df

df = load()

st.title("📅 Drag & Drop Technician Scheduler")

# ----------------------
# CONVERT TO CALENDAR EVENTS
# ----------------------
def to_events(df):
    events = []

    for _, r in df.iterrows():
        try:
            tech_list = str(r["technician"]).split(",")

            for tech in tech_list:
                events.append({
                    "title": f"{r['name']} ({tech})",
                    "start": f"{r['date']}T{r['start']}",
                    "end": f"{r['date']}T{r['end']}",
                    "resourceId": tech,
                    "backgroundColor": "#2D9CDB"
                })
        except:
            continue

    return events

events = to_events(df)

# ----------------------
# CALENDAR OPTIONS
# ----------------------
calendar_options = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay"
    },
    "initialView": "timeGridWeek",
    "slotMinTime": "06:00:00",
    "slotMaxTime": "20:00:00"
}

# ----------------------
# RENDER CALENDAR
# ----------------------
calendar_response = calendar(
    events=events,
    options=calendar_options,
    key="calendar"
)

# ----------------------
# SIDEBAR: ADD TASK
# ----------------------
st.sidebar.header("➕ Add Task")

name = st.sidebar.text_input("Task Name")
techs = st.sidebar.multiselect("Technicians", TECHS)
d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")

# ----------------------
# SAVE NEW TASK
# ----------------------
if st.sidebar.button("Add Task"):

    if not techs:
        st.sidebar.error("Select technician")
        st.stop()

    start_s = start.strftime("%H:%M")
    end_dt = datetime.combine(date.today(), start)
    end_s = (end_dt).strftime("%H:%M")

    # FIX END TIME PROPERLY
    from datetime import timedelta
    end_dt = datetime.combine(date.today(), start) + timedelta(hours=hours)
    end_s = end_dt.strftime("%H:%M")

    append_row([
        str(uuid.uuid4()),
        name,
        str(d),
        start_s,
        end_s,
        float(hours),
        ",".join(techs),
        assigned_by,
        "#2D6FB0"
    ])

    st.sidebar.success("Task added!")
    st.rerun()
