import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from sheets import get_all, append_row, init_sheet

# ----------------------
# PAGE CONFIG
# ----------------------
st.set_page_config(page_title="Technician Task Board", layout="wide")

# ----------------------
# INIT SHEET
# ----------------------
init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# LOAD DATA SAFELY
# ----------------------
def load():
    data = get_all()
    df = pd.DataFrame(data)

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
# VIEW SWITCH
# ----------------------
view = st.sidebar.radio(
    "View Mode",
    ["📊 Week View", "📅 Day View", "📋 Task Catalog"]
)

# ----------------------
# FORM
# ----------------------
st.sidebar.header("➕ Assign Task")

name = st.sidebar.text_input("Task Name")
techs_selected = st.sidebar.multiselect("Technicians", TECHS)
d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start Time")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")

# ----------------------
# CONFLICT CHECK (FIXED)
# ----------------------
def has_conflict(df, tech, date_str, start_s, end_s):

    # safety fix (prevents iterrows crash)
    if df is None or len(df) == 0:
        return False, None

    for _, r in df.iterrows():

        if str(r.get("date", "")) != date_str:
            continue

        tech_list = str(r.get("technician", "")).split(",")

        tech_list = [t.strip() for t in tech_list if t.strip()]

        if tech in tech_list:
            if str(r.get("start", "")) < end_s and start_s < str(r.get("end", "")):
                return True, r.get("name", "Unknown Task")

    return False, None


# ----------------------
# SAVE TASK
# ----------------------
if st.sidebar.button("Save Task"):

    if not techs_selected:
        st.sidebar.error("❌ Please select at least one technician")
        st.stop()

    start_s = start.strftime("%H:%M")
    end_dt = datetime.combine(date.today(), start) + timedelta(hours=hours)
    end_s = end_dt.strftime("%H:%M")

    # 🔥 IMPORTANT FIX: PASS DATAFRAME (NOT dict list)
    records = df

    # check all selected technicians
    for t in techs_selected:
        conflict, task = has_conflict(records, t, str(d), start_s, end_s)

        if conflict:
            st.sidebar.error(f"❌ {t} is not available (conflict with '{task}')")
            st.stop()

    append_row([
        str(uuid.uuid4()),
        name,
        str(d),
        start_s,
        end_s,
        float(hours),
        ",".join(techs_selected),
        assigned_by,
        "#1E7E8C"
    ])

    st.sidebar.success("✅ Task added successfully!")
    st.rerun()

# ----------------------
# WEEK VIEW
# ----------------------
def week_view():
    st.subheader("📊 Week Overview")

    today = date.today()
    week = [today + timedelta(days=i) for i in range(7)]

    rows = []

    for d in week:
        day_tasks = df[df["date"] == str(d)]

        for _, t in day_tasks.iterrows():
            rows.append({
                "Date": d.strftime("%a %d"),
                "Task": t["name"],
                "Time": f"{t['start']} → {t['end']}",
                "Technicians": t["technician"],
                "Hours": t["hours"]
            })

    st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame(), use_container_width=True)


# ----------------------
# DAY VIEW
# ----------------------
def day_view():
    st.subheader("📅 Day View")

    selected = st.date_input("Select Day", date.today())

    day_tasks = df[df["date"] == str(selected)]

    rows = []

    for _, t in day_tasks.iterrows():
        rows.append({
            "Task": t["name"],
            "Time": f"{t['start']} → {t['end']}",
            "Technicians": t["technician"],
            "Hours": t["hours"],
            "Assigned By": t["assigned_by"]
        })

    st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame(), use_container_width=True)


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
else:
    catalog_view()
