import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from sheets import get_all, append_row, init_sheet

# ----------------------
# PAGE CONFIG
# ----------------------
st.set_page_config(page_title="Technician Task Board", layout="wide")

init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# LOAD DATA
# ----------------------
def load():
    df = pd.DataFrame(get_all())

    expected_cols = [
        "id", "name", "date", "start", "end",
        "hours", "technician", "assigned_by", "color"
    ]

    for c in expected_cols:
        if c not in df.columns:
            df[c] = ""

    return df


df = load()

st.title("🛠 Technician Task Board (PRO VERSION)")

# ----------------------
# CONFLICT CHECK
# ----------------------
def has_conflict(df, tech, date_str, start_s, end_s):
    for _, r in df.iterrows():
        if str(r["date"]) != date_str:
            continue

        tech_list = [t.strip() for t in str(r["technician"]).split(",")]

        if tech in tech_list:
            if r["start"] < end_s and start_s < r["end"]:
                return True, r["name"]

    return False, None


# ----------------------
# SIDEBAR
# ----------------------
view = st.sidebar.radio(
    "View Mode",
    ["📊 Week View", "📅 Day View", "📋 Task Catalog"]
)

st.sidebar.header("➕ Assign Task")

name = st.sidebar.text_input("Task Name")
tech_multi = st.sidebar.multiselect("Technicians", TECHS)
d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start Time")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")


# ----------------------
# SAVE TASK
# ----------------------
if st.sidebar.button("Save Task"):

    if not tech_multi:
        st.sidebar.error("Select at least one technician")
        st.stop()

    start_s = start.strftime("%H:%M")
    end_dt = datetime.combine(date.today(), start) + timedelta(hours=hours)
    end_s = end_dt.strftime("%H:%M")

    records = df.to_dict("records")

    # conflict check per technician
    for t in tech_multi:
        conflict, task = has_conflict(records, t, str(d), start_s, end_s)
        if conflict:
            st.sidebar.error(f"❌ {t} not available (conflict with {task})")
            st.stop()

    append_row([
        str(uuid.uuid4()),
        name,
        str(d),
        start_s,
        end_s,
        float(hours),
        ",".join(tech_multi),
        assigned_by,
        "#1E7E8C"
    ])

    st.sidebar.success("✅ Task added!")
    st.rerun()


# ----------------------
# WEEK VIEW (TIME RANGE TABLE)
# ----------------------
def week_view():
    st.subheader("📊 Week Overview (Time Range View)")

    today = date.today()
    week = [today + timedelta(days=i) for i in range(6)]

    for d in week:
        st.markdown(f"## {d.strftime('%A %d %b')}")

        day_tasks = df[df["date"] == str(d)]

        if day_tasks.empty:
            st.info("No tasks")
            continue

        table_data = []

        for _, t in day_tasks.iterrows():
            table_data.append({
                "Time": f"{t['start']} - {t['end']}",
                "Task": t["name"],
                "Technicians": t["technician"],
                "Hours": t["hours"],
                "Assigned By": t["assigned_by"]
            })

        st.dataframe(pd.DataFrame(table_data), use_container_width=True)


# ----------------------
# DAY VIEW (TIME RANGE TABLE)
# ----------------------
def day_view():
    st.subheader("📅 Day Schedule (Time Range View)")

    selected = st.date_input("Select Day", date.today())

    day_tasks = df[df["date"] == str(selected)]

    if day_tasks.empty:
        st.info("No tasks for this day")
        return

    table_data = []

    for _, t in day_tasks.iterrows():
        table_data.append({
            "Time": f"{t['start']} - {t['end']}",
            "Task": t["name"],
            "Technicians": t["technician"],
            "Hours": t["hours"],
            "Assigned By": t["assigned_by"]
        })

    st.dataframe(pd.DataFrame(table_data), use_container_width=True)


# ----------------------
# CATALOG VIEW
# ----------------------
def catalog_view():
    st.subheader("📋 Task Catalog")
    st.dataframe(df, use_container_width=True)


# ----------------------
# ROUTER
# ----------------------
if view == "📊 Week View":
    week_view()

elif view == "📅 Day View":
    day_view()

elif view == "📋 Task Catalog":
    catalog_view()
