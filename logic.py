from datetime import datetime

def to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def overlap(a1, a2, b1, b2):
    return a1 < b2 and b1 < a2


def check_conflict(tasks, tech, date, start, end):
    start_m = to_min(start)
    end_m = to_min(end)

    for t in tasks:
        if t["technician"] == tech and t["date"] == date:
            s = to_min(t["start"])
            e = to_min(t["end"])

            if overlap(start_m, end_m, s, e):
                return True, t["name"]

    return False, None


def daily_load(tasks, tech, date):
    return sum(
        float(t["hours"])
        for t in tasks
        if t["technician"] == tech and t["date"] == date
    )