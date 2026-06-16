import streamlit as st
import pandas as pd
import uuid
from sheets import get_all, append
from logic import check_conflict

st.set_page_config(page_title="Task API", layout="wide")

# ------------------------
# LOAD DATA
# ------------------------
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


# ------------------------
# OVERLAP CHECK
# ------------------------
def time_overlap(a_start, a_end, b_start, b_end):
    return not (a_end <= b_start or a_start >= b_end)


def has_conflict(tech, date, start, end):
    tasks = df[(df["technician"] == tech) & (df["date"] == date)]

    for _, t in tasks.iterrows():
        if time_overlap(start, end, t["start"], t["end"]):
            return True, t["name"]

    return False, None


# ------------------------
# API ROUTES
# ------------------------

action = st.query_params.get("action")


# GET TASKS
if action == "get":
    st.json(df.to_dict("records"))


# ADD TASK
elif action == "add":

    name = st.query_params.get("name")
    tech = st.query_params.get("tech")
    date = st.query_params.get("date")
    start = st.query_params.get("start")
    end = st.query_params.get("end")
    hours = st.query_params.get("hours")
    by = st.query_params.get("by", "system")

    if not all([name, tech, date, start, end]):
        st.json({"status": "error", "msg": "missing fields"})
        st.stop()

    conflict, task = has_conflict(tech, date, start, end)

    if conflict:
        st.json({"status": "error", "msg": f"Conflict with {task}"})
    else:
        append([
            str(uuid.uuid4()),
            name,
            date,
            start,
            end,
            float(hours),
            tech,
            by,
            "#2D6FB0"
        ])

        st.json({"status": "success"})
