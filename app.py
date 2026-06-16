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
# INIT SHEET (auto headers)
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
# INPUT FORM
# ----------------------
st.sidebar.header("➕ Assign Task")

name = st.sidebar.text_input("Task Name")
tech = st.sidebar.selectbox("Technician", TECHS)
d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start Time")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")


# ----------------------
# TIME CONVERSION + CONFLICT CHECK
# ----------------------
def to_minutes(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def check_conflict(records, technician, date_str, new_start, new_end):
    new_start_m = to_minutes(new_start)
    new_end_m = to_minutes(new_end)

    for r in records:
        if str(r["technician"]) != technician:
            continue
        if str(r["date"]) != date_str:
            continue

        existing_start = to_minutes(r["start"])
        existing_end = to_minutes(r["end"])

        # OVERLAP RULE
        if new_start_m < existing_end and new_end_m > existing_start:
            return True, r["name"]

    return False, None


# ----------------------
# SAVE TASK
# ----------------------
if st.sidebar.button("Save Task"):

    start_s = start.strftime("%H:%M")

    end_dt = datetime.combine(date.today(), start) + timedelta(hours=hours)
    end_s = end_dt.strftime("%H:%M")

    records = df.to_dict("records")

    conflict, task = check_conflict(
        records,
        tech,
        str(d),
        start_s,
        end_s
    )

    if conflict:
        st.sidebar.error("❌ Technician is not available at this time.")
        st.sidebar.warning(f"Clashes with: {task}")
        st.stop()

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

    st.sidebar.success("✅ Task added successfully!")
    st.rerun()


# ----------------------
# WEEK VIEW
# ----------------------
def week_view():
    st.subheader("📊 Week Overview")

    today = date.today()
    week = [today + timedelta(days=i) for i in range(6)]

    cols = st.columns(len(week) + 1)
    cols[0].markdown("**TECH**")

    for i, d in enumerate(week):
        cols[i + 1].markdown(f"**{d.strftime('%a %d')}**")

    for t in TECHS:
        row = [t]

        for d in week:
            day_tasks = df[(df["technician"] == t) & (df["date"] == str(d))]
            load = day_tasks["hours"].sum() if not day_tasks.empty else 0
            row.append(f"{load}h")

        cols = st.columns(len(row))

        for i, cell in enumerate(row):
            if i == 0:
                cols[i].markdown(f"**{cell}**")
            else:
                cols[i].markdown(
                    f"<div style='background:#E9EFF2;padding:10px;border-radius:8px;text-align:center'>{cell}</div>",
                    unsafe_allow_html=True
                )


# ----------------------
# DAY VIEW
# ----------------------
def day_view():
    st.subheader("📅 Day Timeline")

    selected = st.date_input("Select Day", date.today())

    day_tasks = df[df["date"] == str(selected)]

    for tech in TECHS:
        st.markdown(f"### {tech}")

        tasks = day_tasks[day_tasks["technician"] == tech]

        if tasks.empty:
            st.info("No tasks")
        else:
            for _, t in tasks.iterrows():
                st.markdown(
                    f"""
                    <div style="
                        background:#f4f8fa;
                        padding:10px;
                        border-radius:10px;
                        margin-bottom:8px;
                        border-left:5px solid #1E7E8C;
                    ">
                        <b>{t['name']}</b><br>
                        {t['start']} → {t['end']} | {t['hours']}h
                    </div>
                    """,
                    unsafe_allow_html=True
                )


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
