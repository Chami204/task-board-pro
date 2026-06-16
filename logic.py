def overlap(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def check_conflict(records, technicians, date, start, end):
    """
    technicians = list OR string
    """

    if isinstance(technicians, str):
        technicians = [technicians]

    for r in records:
        r_techs = r.get("technicians", [])

        # handle old string format safely
        if isinstance(r_techs, str):
            r_techs = [t.strip() for t in r_techs.split(",") if t.strip()]

        if r.get("date") != date:
            continue

        r_start = r.get("start")
        r_end = r.get("end")

        for t in technicians:
            if t in r_techs:
                if overlap(start, end, r_start, r_end):
                    return True, r.get("name")

    return False, None
