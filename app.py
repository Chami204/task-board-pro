import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from sheets import get_all, append_row, init_sheet

# ----------------------
# PAGE CONFIG (MOBILE FRIENDLY)
# ----------------------
st.set_page_config(
    page_title="Technician Task Board",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# CUSTOM UI STYLE (COLOR + MOBILE BOOST)
# ----------------------
st.markdown("""
<style>
/* background */
.stApp {
    background: linear-gradient(to right, #f7f9fc, #eef3f8);
}

/* sidebar */
section[data-testid="stSidebar"] {
    background: #0f172a;
    color: white;
}

/* buttons */
.stButton button {
    background: linear-gradient(90deg, #4f46e5, #06b6d4);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 14px;
    font-weight: 600;
}

/* task cards */
.task-card {
    background: white;
    padding: 14px;
    border-radius: 14px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    border-left: 6px solid #4f46e5;
    margin-bottom: 10px;
}

/* mobile friendly text */
h1, h2, h3 {
    font-family: Arial;
}
</style>
""", unsafe_allow_html=True)

# ----------------------
# LOAD DATA
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

st.title("🛠 Technician Task Board")

# ----------------------
# VIEW SWITCH
# ----------------------
view = st.sidebar.radio(
    "📌 View Mode",
    ["📊 Week View", "📅 Day View", "📋 Task Catalog"]
)

# ----------------------
# FORM (MOBILE FRIENDLY)
# ----------------------
st.sidebar.header("➕ Assign Task")

name = st.sidebar.text_input("Task Name")
techs_selected = st.sidebar.multiselect("Technicians", TECHS)
d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start Time")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")

# ----------------------
# CONFLICT CHECK
# ----------------------
def has_conflict(df, tech, date_str, start_s, end_s):

    if df is None or len(df) == 0:
        return False, None

    for _, r in df.iterrows():

        if str(r.get("date", "")) != date_str:
            continue

        tech_list = [t.strip() for t in str(r.get("technician", "")).split(",")]

        if tech in tech_list:
            if str(r.get("start", "")) < end_s and start_s < str(r.get("end", "")):
                return True, r.get("name", "Task")

    return False, None


# ----------------------
# SAVE TASK
# ----------------------
if st.sidebar.button("🚀 Save Task"):

    if not techs_selected:
        st.sidebar.error("Select at least one technician")
        st.stop()

    start_s = start.strftime("%H:%M")
    end_dt = datetime.combine(date.today(), start) + timedelta(hours=hours)
    end_s = end_dt.strftime("%H:%M")

    for t in techs_selected:
        conflict, task = has_conflict(df, t, str(d), start_s, end_s)

        if conflict:
            st.sidebar.error(f"❌ {t} is busy with '{task}'")
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
        "#4f46e5"
    ])

    st.sidebar.success("✅ Task added!")
    st.rerun()

# ----------------------
# WEEK VIEW (COLORFUL CARDS)
# ----------------------
def week_view():
    st.subheader("📊 Weekly Overview")

    today = date.today()
    week = [today + timedelta(days=i) for i in range(7)]

    for d in week:
        st.markdown(f"### 📅 {d.strftime('%A %d')}")

        day_tasks = df[df["date"] == str(d)]

        if day_tasks.empty:
            st.info("No tasks")

        for _, t in day_tasks.iterrows():

            st.markdown(f"""
            <div class="task-card">
                <b>🧩 {t['name']}</b><br>
                ⏰ {t['start']} → {t['end']}<br>
                👷 {t['technician']}<br>
                📌 {t['assigned_by']}
            </div>
            """, unsafe_allow_html=True)

# ----------------------
# DAY VIEW (CLEAN MOBILE STACK)
# ----------------------
def day_view():
    st.subheader("📅 Daily View")

    selected = st.date_input("Select Day", date.today())

    day_tasks = df[df["date"] == str(selected)]

    if day_tasks.empty:
        st.info("No tasks for this day")

    for _, t in day_tasks.iterrows():

        st.markdown(f"""
        <div class="task-card">
            <b>🧩 {t['name']}</b><br>
            ⏰ {t['start']} → {t['end']}<br>
            👷 {t['technician']}<br>
            📌 {t['assigned_by']}
        </div>
        """, unsafe_allow_html=True)

# ----------------------
# CATALOG VIEW
# ----------------------
def catalog_view():
    st.subheader("📋 All Tasks")
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
