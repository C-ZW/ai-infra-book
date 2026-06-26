def dedupe_preserve_order(items):
    """Return items with duplicates removed, keeping first-seen order."""
    result = []
    for x in items:
        if x in result:  # O(n) membership scan -> O(n^2) overall
            continue
        result.append(x)
    return result
