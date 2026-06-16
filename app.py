import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from sheets import get_all, append_row, init_sheet

# ----------------------
# PAGE CONFIG (mobile friendly)
# ----------------------
st.set_page_config(
    page_title="Technician Task Board",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------
# INIT SHEET
# ----------------------
init_sheet()

TECHS = ["Dinidu", "Buddhika", "Kosala"]

# ----------------------
# UI STYLING (LIGHT + COLORFUL)
# ----------------------
st.markdown("""
<style>
/* Background */
.main {
    background-color: #f6f8fb;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff;
}

/* Sidebar text */
.css-1d391kg, .css-1v0mbdj {
    color: #111 !important;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #1E7E8C, #2D9CDB);
    color: white;
    border-radius: 8px;
    padding: 0.4rem 1rem;
    border: none;
}

/* Inputs */
input, textarea, .stSelectbox, .stDateInput, .stTimeInput {
    background-color: white !important;
    color: #111 !important;
}

/* Cards */
.card {
    background: white;
    padding: 12px;
    border-radius: 10px;
    border-left: 5px solid #2D9CDB;
    margin-bottom: 8px;
}

/* Table header */
.table-header {
    background: #1E7E8C;
    color: white;
    padding: 8px;
    border-radius: 6px;
    text-align: center;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ----------------------
# LOAD DATA SAFE
# ----------------------
def load():
    data = get_all()
    df = pd.DataFrame(data)

    expected = ["id","name","date","start","end","hours","technician","assigned_by","color"]

    for c in expected:
        if c not in df.columns:
            df[c] = ""

    return df

df = load()

st.title("🛠 Technician Task Board (PRO VERSION)")

# ----------------------
# MULTI TECH SUPPORT INPUT
# ----------------------
view = st.sidebar.radio(
    "View Mode",
    ["📊 Week View", "📅 Day View", "📋 Task Catalog"]
)

st.sidebar.markdown("## ➕ Assign Task")

name = st.sidebar.text_input("Task Name")

techs_selected = st.sidebar.multiselect(
    "Technicians",
    TECHS
)

d = st.sidebar.date_input("Date", date.today())
start = st.sidebar.time_input("Start Time")
hours = st.sidebar.number_input("Hours", 0.5, 12.0, step=0.5)
assigned_by = st.sidebar.text_input("Assigned By")

# ----------------------
# CONFLICT CHECK (FIXED FOR MULTI TECH)
# ----------------------
def has_conflict(data, tech, date_str, start_s, end_s):
    for r in data:
        try:
            if str(r.get("technician")) != tech:
                continue
            if str(r.get("date")) != date_str:
                continue

            if r.get("start") and r.get("end"):
                if r["start"] < end_s and start_s < r["end"]:
                    return True, r.get("name")
        except:
            continue

    return False, None

# ----------------------
# SAVE TASK (MULTI TECH FIXED)
# ----------------------
if st.sidebar.button("Save Task"):

    if not techs_selected:
        st.sidebar.error("❌ Please select at least one technician")
        st.stop()

    start_s = start.strftime("%H:%M")
    end_dt = datetime.combine(date.today(), start) + timedelta(hours=hours)
    end_s = end_dt.strftime("%H:%M")

    records = df.to_dict("records")

    # check conflicts for EACH technician
    conflict_found = False

    for t in techs_selected:
        conflict, task = has_conflict(records, t, str(d), start_s, end_s)

        if conflict:
            st.sidebar.error(f"❌ {t} is not available ({task})")
            conflict_found = True

    if not conflict_found:

        append_row([
            str(uuid.uuid4()),
            name,
            str(d),
            start_s,
            end_s,
            float(hours),
            ",".join(techs_selected),   # store multiple techs
            assigned_by,
            "#1E7E8C"
        ])

        st.sidebar.success("✅ Task assigned!")
        st.rerun()

# ----------------------
# WEEK VIEW (TABLE STYLE)
# ----------------------
def week_view():
    st.subheader("📊 Week Overview")

    today = date.today()
    week = [today + timedelta(days=i) for i in range(6)]

    rows = []

    for _, r in df.iterrows():
        rows.append([
            r["name"],
            r["date"],
            f"{r['start']} - {r['end']}",
            r["technician"]
        ])

    st.markdown("""
    <div class="table-header">
        TASK | DATE | TIME | TECHNICIANS
    </div>
    """, unsafe_allow_html=True)

    for row in rows:
        st.markdown(f"""
        <div class="card">
            <b>{row[0]}</b><br>
            📅 {row[1]} | ⏰ {row[2]}<br>
            👷 {row[3]}
        </div>
        """, unsafe_allow_html=True)

# ----------------------
# DAY VIEW (TABLE STYLE)
# ----------------------
def day_view():
    st.subheader("📅 Day View")

    selected = st.date_input("Select Day", date.today())

    day_tasks = df[df["date"] == str(selected)]

    st.markdown("""
    <div class="table-header">
        TIME | TASK | TECHNICIANS
    </div>
    """, unsafe_allow_html=True)

    if day_tasks.empty:
        st.info("No tasks for this day")
        return

    for _, t in day_tasks.iterrows():
        st.markdown(f"""
        <div class="card">
            ⏰ {t['start']} - {t['end']}<br>
            <b>{t['name']}</b><br>
            👷 {t['technician']}
        </div>
        """, unsafe_allow_html=True)

# ----------------------
# CATALOG
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
