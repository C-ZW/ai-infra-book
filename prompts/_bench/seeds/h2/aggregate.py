def summarize(events):
    """Sum 'amount' per 'user_id' across events. Returns {user_id: total}."""
    totals = {}
    for e in events:
        uid = e["user_id"]
        totals[uid] = totals.get(uid, 0) + e["amount"]
    return totals


def top_user(events):
    """Return the user_id with the highest total spend."""
    totals = summarize(events)
    return max(totals, key=totals.get)
