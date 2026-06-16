import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from sheets import get_all, append_row, init_sheet
from logic import check_conflict

# ----------------------
# PAGE
# ----------------------
st.set_page_config(page_title="Technician Task Board", layout="wide")

init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]


# ----------------------
# LOAD DATA SAFE
# ----------------------
def load():
    data = get_all()
    df = pd.DataFrame(data)

    expected = [
        "id", "name", "date", "start", "end",
        "hours", "technicians", "assigned_by", "color"
    ]

    for c in expected:
        if c not in df.columns:
            df[c] = ""

    return df


df = load()

st.title("🛠 Technician Task Board")


# ----------------------
# VIEW
# ----------------------
view = st.sidebar.radio("View", ["Week View", "Day View", "Catalog"])


# ----------------------
# INPUT
# ----------------------
st.sidebar.header("➕ Assign Task")

name = st.sidebar.text_input("Task Name")
techs = st.sidebar.multiselect("Technicians", TECHS)
d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")


# ----------------------
# SAVE TASK
# ----------------------
if st.sidebar.button("Save Task"):

    if not name or not techs:
        st.sidebar.error("Enter task + select technicians")
    else:
        start_s = start.strftime("%H:%M")

        end_dt = datetime.combine(d, start) + timedelta(hours=hours)
        end_s = end_dt.strftime("%H:%M")

        conflict, task = check_conflict(
            df.to_dict("records"),
            techs,
            str(d),
            start_s,
            end_s
        )

        if conflict:
            st.sidebar.error(f"❌ Technician not available (clash with {task})")
        else:
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

            st.sidebar.success("✅ Task added!")
            st.rerun()


# ----------------------
# WEEK VIEW
# ----------------------
def week_view():
    st.subheader("📊 Week View")

    today = date.today()
    week = [today + timedelta(days=i) for i in range(6)]

    table = []

    for tech in TECHS:
        row = [tech]

        for d in week:
            day_tasks = df[
                (df["technicians"].astype(str).str.contains(tech)) &
                (df["date"] == str(d))
            ]

            load = day_tasks["hours"].sum() if not day_tasks.empty else 0
            row.append(f"{load}h")

        table.append(row)

    st.dataframe(
        pd.DataFrame(table, columns=["Tech"] + [str(d) for d in week]),
        use_container_width=True
    )


# ----------------------
# DAY VIEW
# ----------------------
def day_view():
    st.subheader("📅 Day View")

    selected = st.date_input("Select Date", date.today())

    day = df[df["date"] == str(selected)]

    for tech in TECHS:
        st.markdown(f"### {tech}")

        tasks = day[day["technicians"].astype(str).str.contains(tech)]

        if tasks.empty:
            st.info("No tasks")
        else:
            for _, t in tasks.iterrows():
                st.write(f"🟦 {t['name']} | {t['start']} - {t['end']} | {t['hours']}h")


# ----------------------
# CATALOG
# ----------------------
def catalog():
    st.subheader("📋 Task Catalog")
    st.dataframe(df, use_container_width=True)


# ----------------------
# ROUTER
# ----------------------
if view == "Week View":
    week_view()
elif view == "Day View":
    day_view()
else:
    catalog()
