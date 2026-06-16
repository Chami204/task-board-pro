import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from sheets import get_all, append_row, init_sheet

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(page_title="Technician Task Board", layout="wide")

init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# LOAD DATA (ALWAYS FRESH)
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

st.title("🛠 Technician Task Board")

# ----------------------
# CONFLICT LOGIC (FIXED)
# ----------------------
def to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def check_conflict(records, tech, date_str, new_start, new_end):
    new_s = to_min(new_start)
    new_e = to_min(new_end)

    for r in records:
        if str(r["technician"]) != tech:
            continue
        if str(r["date"]) != date_str:
            continue

        old_s = to_min(r["start"])
        old_e = to_min(r["end"])

        # OVERLAP RULE
        if new_s < old_e and new_e > old_s:
            return True, r["name"]

    return False, None


# ----------------------
# SIDEBAR INPUT
# ----------------------
view = st.sidebar.radio("View", ["Week View", "Day View", "Tasks"])

st.sidebar.header("➕ Assign Task")

name = st.sidebar.text_input("Task Name")
tech = st.sidebar.selectbox("Technician", TECHS)
d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")

# ----------------------
# SAVE TASK (FINAL FIX)
# ----------------------
if st.sidebar.button("Save Task"):

    # 🔥 ALWAYS REFRESH SHEET BEFORE CHECK
    df_latest = pd.DataFrame(get_all())
    records = df_latest.to_dict("records")

    start_s = start.strftime("%H:%M")
    end_dt = datetime.combine(date.today(), start) + timedelta(hours=hours)
    end_s = end_dt.strftime("%H:%M")

    conflict, task = check_conflict(
        records,
        tech,
        str(d),
        start_s,
        end_s
    )

    if conflict:
        st.sidebar.error("❌ Technician is NOT available at this time")
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

    for t in TECHS:
        st.markdown(f"### {t}")

        cols = st.columns(len(week))

        for i, d in enumerate(week):
            day_tasks = df[(df["technician"] == t) & (df["date"] == str(d))]
            load = day_tasks["hours"].sum() if not day_tasks.empty else 0
            cols[i].metric(d.strftime("%a %d"), f"{load}h")


# ----------------------
# DAY VIEW
# ----------------------
def day_view():
    st.subheader("📅 Day View")

    selected = st.date_input("Select Date", date.today())
    day_tasks = df[df["date"] == str(selected)]

    for t in TECHS:
        st.markdown(f"### {t}")

        tasks = day_tasks[day_tasks["technician"] == t]

        if tasks.empty:
            st.info("No tasks")
        else:
            for _, r in tasks.iterrows():
                st.write(f"🟦 {r['name']} | {r['start']} - {r['end']} | {r['hours']}h")


# ----------------------
# TASK LIST
# ----------------------
def task_view():
    st.subheader("📋 All Tasks")
    st.dataframe(df, use_container_width=True)


# ----------------------
# ROUTER
# ----------------------
if view == "Week View":
    week_view()
elif view == "Day View":
    day_view()
else:
    task_view()
