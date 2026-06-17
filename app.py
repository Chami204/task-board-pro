import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from streamlit_calendar import calendar
from sheets import get_all, append_row, update_row, delete_row, init_sheet

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(page_title="R&D Project Schedule - Sohan and Team", layout="wide")

init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# LOAD DATA
# ----------------------
def load():
    df = pd.DataFrame(get_all())

    cols = ["id","name","date","start","end","hours","technician","assigned_by","color"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""

    return df


df = load()

# ----------------------
# CONFLICT CHECK
# ----------------------
def has_conflict(df, tech, date_str, start_s, end_s, ignore_id=None):
    for _, r in df.iterrows():

        if str(r["technician"]) != tech:
            continue
        if str(r["date"]) != date_str:
            continue

        if ignore_id and str(r["id"]) == str(ignore_id):
            continue

        try:
            if str(r["start"]) < end_s and start_s < str(r["end"]):
                return True, r["name"]
        except:
            continue

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
# UPDATE TASK (DRAG DROP)
# ----------------------
def update_task(task_id, new_start, new_end):

    for _, r in df.iterrows():

        if str(r["id"]) != str(task_id):
            continue

        tech = r["technician"]
        date_str = new_start.date().strftime("%Y-%m-%d")
        start_s = new_start.strftime("%H:%M")
        end_s = new_end.strftime("%H:%M")

        conflict, task = has_conflict(df, tech, date_str, start_s, end_s, task_id)

        if conflict:
            return False, task

        update_row(task_id, {
            "date": date_str,
            "start": start_s,
            "end": end_s
        })

        return True, None

    return False, "Task not found"


# ----------------------
# DELETE TASK
# ----------------------
def delete_task(task_id):
    return delete_row(task_id)


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

    errors = []

    for t in techs_selected:
        ok, conflict = save_task(name, t, d, start, hours, assigned_by)
        if not ok:
            errors.append(f"{t} busy with {conflict}")

    if errors:
        st.sidebar.error("❌ " + " | ".join(errors))
    else:
        st.sidebar.success("Task added")
        st.rerun()


# ----------------------
# EVENTS
# ----------------------
def build_events(df):
    events = []

    for _, r in df.iterrows():
        try:
            start_dt = datetime.strptime(f"{r['date']} {r['start']}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{r['date']} {r['end']}", "%Y-%m-%d %H:%M")

            events.append({
                "id": r["id"],
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
# UI TABS (NEW FEATURE)
# ----------------------
tab1, tab2 = st.tabs(["📅 Calendar", "📋 Spreadsheet View"])

# ======================
# TAB 1 - CALENDAR
# ======================
with tab1:

    st.title("🛠 Technician Scheduler")

    calendar_options = {
        "editable": True,
        "selectable": True,
        "initialView": "timeGridWeek",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay"
        }
    }

    calendar_result = calendar(
        events=events,
        options=calendar_options,
        key="main_calendar"
    )

    if calendar_result and isinstance(calendar_result, dict):

        event_type = list(calendar_result.keys())[0]

        if event_type in ["eventDrop", "eventChange"]:

            event = calendar_result[event_type]["event"]

            task_id = event["id"]
            new_start = datetime.fromisoformat(event["start"])
            new_end = datetime.fromisoformat(event["end"])

            ok, msg = update_task(task_id, new_start, new_end)

            if ok:
                st.success("Updated successfully")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


# ======================
# TAB 2 - SPREADSHEET
# ======================
with tab2:

    st.subheader("📋 Editable Task Sheet")

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Changes to Google Sheets"):
            for _, row in edited_df.iterrows():
                update_row(row["id"], row.to_dict())

            st.success("Saved successfully!")
            st.rerun()

    with col2:
        delete_id = st.selectbox("Delete Task", df["id"].tolist())

        if st.button("🗑 Delete Task"):
            delete_task(delete_id)
            st.success("Deleted successfully!")
            st.rerun()
