import streamlit as st
import pandas as pd
import uuid
from sheets import get_all, append

st.set_page_config(page_title="Task API", layout="wide")

# ----------------------------
# LOAD DATA
# ----------------------------
def load():
    data = get_all()

    columns = [
        "id", "name", "date", "start", "end",
        "hours", "technician", "assigned_by", "color"
    ]

    if not data:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(data)

    for c in columns:
        if c not in df.columns:
            df[c] = ""

    return df


df = load()


# ----------------------------
# CONFLICT CHECK (NO DOUBLE BOOKING)
# ----------------------------
def time_overlap(start1, end1, start2, end2):
    return not (end1 <= start2 or start1 >= end2)


def has_conflict(tech, date, start, end):
    tasks = df[
        (df["technician"] == tech) &
        (df["date"] == date)
    ]

    for _, t in tasks.iterrows():
        if time_overlap(start, end, t["start"], t["end"]):
            return True, t["name"]

    return False, None


# ----------------------------
# API: GET TASKS
# ----------------------------
if st.query_params.get("action") == "get":
    st.json(df.to_dict("records"))


# ----------------------------
# API: ADD TASK
# ----------------------------
elif st.query_params.get("action") == "add":

    name = st.query_params.get("name")
    tech = st.query_params.get("tech")
    date = st.query_params.get("date")
    start = st.query_params.get("start")
    end = st.query_params.get("end")
    hours = st.query_params.get("hours")
    assigned_by = st.query_params.get("by", "system")

    if not all([name, tech, date, start, end]):
        st.json({"status": "error", "message": "Missing fields"})
        st.stop()

    conflict, task = has_conflict(tech, date, start, end)

    if conflict:
        st.json({"status": "error", "message": f"Conflict with {task}"})
    else:
        append([
            str(uuid.uuid4()),
            name,
            date,
            start,
            end,
            float(hours),
            tech,
            assigned_by,
            "#2D6FB0"
        ])

        st.json({"status": "success"})
