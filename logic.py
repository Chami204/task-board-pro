def time_overlap(a_start, a_end, b_start, b_end):
    return not (a_end <= b_start or a_start >= b_end)


def check_conflict(tasks, tech, date, start, end):

    for t in tasks:
        if t.get("technician") != tech:
            continue

        if t.get("date") != date:
            continue

        if time_overlap(start, end, t.get("start"), t.get("end")):
            return True, t.get("name")

    return False, None


def daily_load(tasks, tech, date):
    total = 0

    for t in tasks:
        if t.get("technician") == tech and t.get("date") == date:
            try:
                total += float(t.get("hours", 0))
            except:
                pass

    return total
    
