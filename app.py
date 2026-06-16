import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import uuid

from sheets import get_all, append
from logic import check_conflict, daily_load

st.set_page_config(layout="wide")

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# LOAD DATA
# ----------------------
def load():
    data = get_all()
    return pd.DataFrame(data)


df = load()

st.title("🛠 Technician Task Board (PRO VERSION)")


# ----------------------
# SIDEBAR - VIEW SWITCH
# ----------------------
view = st.sidebar.radio(
    "View Mode",
    ["📊 Week View", "📅 Day View", "📋 Task Catalog"]
)


# ----------------------
# ADD TASK FORM
# ----------------------
st.sidebar.header("➕ Assign Task")

name = st.sidebar.text_input("Task Name")
tech = st.sidebar.selectbox("Technician", TECHS)
d = st.sidebar.date_input("Date")
start = st.sidebar.time_input("Start")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")


if st.sidebar.button("Save Task"):

    start_s = start.strftime("%H:%M")
    end_dt = datetime.combine(datetime.today(), start) + timedelta(hours=hours)
    end_s = end_dt.time().strftime("%H:%M")

    conflict, task = check_conflict(df.to_dict("records"), tech, str(d), start_s, end_s)

    if conflict:
        st.sidebar.error(f"❌ Conflict with: {task}")
    else:
        append([
            str(uuid.uuid4()),
            name,
            str(d),
            start_s,
            end_s,
            hours,
            tech,
            assigned_by,
            "#2D6FB0"
        ])
        st.sidebar.success("✅ Task added!")
        st.rerun()


# ----------------------
# WEEK VIEW (like your HTML grid)
# ----------------------
def week_view():
    st.subheader("📊 Week Overview")

    today = date.today()
    week = [today + timedelta(days=i) for i in range(6)]

    cols = st.columns(7)
    cols[0].write("TECH")

    for i, d in enumerate(week):
        cols[i+1].write(d.strftime("%a %d"))

    for t in TECHS:
        row = [t]

        for d in week:
            day_tasks = df[(df["technician"] == t) & (df["date"] == str(d))]

            load = day_tasks["hours"].sum() if not day_tasks.empty else 0

            row.append(f"{load}h")

        cols = st.columns(7)
        for i, cell in enumerate(row):
            cols[i].write(cell)


# ----------------------
# DAY VIEW (timeline style)
# ----------------------
def day_view():
    st.subheader("📅 Day Timeline")

    selected = st.date_input("Select Day", date.today())

    day_tasks = df[df["date"] == str(selected)]

    for tech in TECHS:
        st.markdown(f"### {tech}")

        tasks = day_tasks[day_tasks["technician"] == tech]

        if tasks.empty:
            st.write("No tasks")
        else:
            for _, t in tasks.iterrows():
                st.write(
                    f"🟦 {t['name']} | {t['start']} - {t['end']} | {t['hours']}h"
                )


# ----------------------
# CATALOG VIEW
# ----------------------
def catalog_view():
    st.subheader("📋 Task List")

    st.dataframe(df)


# ----------------------
# ROUTER
# ----------------------
if view == "📊 Week View":
    week_view()

elif view == "📅 Day View":
    day_view()

elif view == "📋 Task Catalog":
    catalog_view()