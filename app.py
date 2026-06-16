import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid

from sheets import get_all, append_row, init_sheet

# ----------------------
# PAGE CONFIG
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
# UI STYLE (FIXED INPUT VISIBILITY)
# ----------------------
st.markdown("""
<style>

/* BACKGROUND */
.main {
    background-color: #f6f8fb;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #ffffff;
    padding: 10px;
}

/* SIDEBAR SECTION */
.sidebar-section {
    border: 1px solid #e6eaf0;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 14px;
    background: #fafbfc;
}

/* SECTION TITLE */
.sidebar-title {
    font-size: 14px;
    font-weight: 600;
    color: #1E7E8C;
    margin-bottom: 10px;
}

/* =========================
   INPUT BOXES (FIXED VISIBILITY)
   ========================= */

input, textarea {
    background-color: #ffffff !important;
    color: #111 !important;
    border: 1px solid #cfd8dc !important;
    border-radius: 8px !important;
    padding: 8px !important;
}

/* Streamlit inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input,
.stTimeInput > div > div > input {
    background-color: #ffffff !important;
    color: #111 !important;
    border: 1px solid #cfd8dc !important;
    border-radius: 8px !important;
    padding: 8px !important;
    box-shadow: none !important;
}

/* Focus effect */
input:focus {
    border: 1px solid #2D9CDB !important;
    box-shadow: 0px 0px 6px rgba(45,156,219,0.3) !important;
    outline: none !important;
}

/* Selectbox */
.stSelectbox > div {
    border: 1px solid #cfd8dc !important;
    border-radius: 8px !important;
    background: white !important;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg, #1E7E8C, #2D9CDB);
    color: white;
    border-radius: 8px;
    padding: 0.55rem 1rem;
    border: none;
    width: 100%;
}

/* TASK CARD */
.card {
    background: white;
    padding: 12px;
    border-radius: 12px;
    border-left: 5px solid #2D9CDB;
    margin-bottom: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
}

/* HEADER BAR */
.table-header {
    background: #1E7E8C;
    color: white;
    padding: 10px;
    border-radius: 8px;
    text-align: center;
    font-weight: bold;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# ----------------------
# LOAD DATA
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
# VIEW SWITCH
# ----------------------
view = st.sidebar.radio(
    "View Mode",
    ["📊 Week View", "📅 Day View", "📋 Task Catalog"]
)

# ----------------------
# SIDEBAR FORM (CLEAN + BORDERS)
# ----------------------
st.sidebar.markdown("## ➕ Task Entry")

with st.sidebar:
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Task Details</div>', unsafe_allow_html=True)
    name = st.text_input("Task Name")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Technicians</div>', unsafe_allow_html=True)
    techs_selected = st.multiselect("Select Technicians", TECHS)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Schedule</div>', unsafe_allow_html=True)
    d = st.date_input("Date", date.today())
    start = st.time_input("Start Time")
    hours = st.number_input("Hours", 0.5, 12.0, step=0.5)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Assignment Info</div>', unsafe_allow_html=True)
    assigned_by = st.text_input("Assigned By")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------
# CONFLICT CHECK
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
# SAVE TASK
# ----------------------
if st.sidebar.button("Save Task"):

    if not techs_selected:
        st.sidebar.error("❌ Please select at least one technician")
        st.stop()

    start_s = start.strftime("%H:%M")
    end_dt = datetime.combine(date.today(), start) + timedelta(hours=hours)
    end_s = end_dt.strftime("%H:%M")

    records = df.to_dict("records")

    for t in techs_selected:
        conflict, task = has_conflict(records, t, str(d), start_s, end_s)

        if conflict:
            st.sidebar.error(f"❌ {t} is not available ({task})")
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

    st.sidebar.success("✅ Task Assigned Successfully")
    st.rerun()

# ----------------------
# WEEK VIEW
# ----------------------
def week_view():
    st.subheader("📊 Week Overview")

    for _, r in df.iterrows():
        st.markdown(f"""
        <div class="card">
            <b>{r['name']}</b><br>
            📅 {r['date']}<br>
            ⏰ {r['start']} - {r['end']}<br>
            👷 {r['technician']}
        </div>
        """, unsafe_allow_html=True)

# ----------------------
# DAY VIEW
# ----------------------
def day_view():
    st.subheader("📅 Day View")

    selected = st.date_input("Select Day", date.today())

    day_tasks = df[df["date"] == str(selected)]

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
