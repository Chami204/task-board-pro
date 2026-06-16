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
# CONFLICT CHECK (MULTI TECH)
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

    # conflict check for EACH technician
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
# WEEK VIEW (TIME GRID)
# ----------------------
def week_view():
    st.subheader("📊 Week Time Grid")

    today = date.today()
    week = [today + timedelta(days=i) for i in range(6)]

    hours_range = list(range(6, 22))  # 6AM - 9PM

    for d in week:
        st.markdown(f"## {d.strftime('%A %d %b')}")

        grid = pd.DataFrame(index=[f"{h}:00" for h in hours_range], columns=TECHS)
        grid[:] = ""

        day_tasks = df[df["date"] == str(d)]

        for _, t in day_tasks.iterrows():
            techs = [x.strip() for x in str(t["technician"]).split(",")]

            start_h = int(t["start"].split(":")[0])
            end_h = int(t["end"].split(":")[0])

            for h in range(start_h, end_h + 1):
                time_slot = f"{h}:00"
                for tech in techs:
                    if tech in TECHS and time_slot in grid.index:
                        grid.loc[time_slot, tech] = t["name"]

        st.dataframe(grid, use_container_width=True)


# ----------------------
# DAY VIEW (TIME GRID)
# ----------------------
def day_view():
    st.subheader("📅 Day Time Grid")

    selected = st.date_input("Select Day", date.today())

    hours_range = list(range(6, 22))

    grid = pd.DataFrame(index=[f"{h}:00" for h in hours_range], columns=TECHS)
    grid[:] = ""

    day_tasks = df[df["date"] == str(selected)]

    for _, t in day_tasks.iterrows():
        techs = [x.strip() for x in str(t["technician"]).split(",")]

        start_h = int(t["start"].split(":")[0])
        end_h = int(t["end"].split(":")[0])

        for h in range(start_h, end_h + 1):
            time_slot = f"{h}:00"
            for tech in techs:
                if tech in TECHS and time_slot in grid.index:
                    grid.loc[time_slot, tech] = t["name"]

    st.dataframe(grid, use_container_width=True)


# ----------------------
# CATALOG
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
