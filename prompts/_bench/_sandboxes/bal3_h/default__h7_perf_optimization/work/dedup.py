def dedupe_preserve_order(items):
    """Return items with duplicates removed, keeping first-seen order."""
    seen = set()
    result = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        result.append(x)
    return result
