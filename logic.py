from datetime import datetime

def to_minutes(t):
    """Convert 'HH:MM' → minutes"""
    h, m = map(int, t.split(":"))
    return h * 60 + m


def check_conflict(records, technician, date, new_start, new_end):
    """
    Returns:
    (True, conflicting_task_name) if conflict exists
    """

    new_start_m = to_minutes(new_start)
    new_end_m = to_minutes(new_end)

    for r in records:
        if r["technician"] != technician:
            continue
        if str(r["date"]) != str(date):
            continue

        existing_start = to_minutes(r["start"])
        existing_end = to_minutes(r["end"])

        # 🔴 OVERLAP RULE (MOST IMPORTANT PART)
        if new_start_m < existing_end and new_end_m > existing_start:
            return True, r["name"]

    return False, None


def daily_load(records, technician, date):
    total = 0
    for r in records:
        if r["technician"] == technician and str(r["date"]) == str(date):
            total += float(r["hours"])
    return total
