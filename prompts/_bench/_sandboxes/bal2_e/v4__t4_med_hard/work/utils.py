import re

_DURATION_RE = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?$")


def parse_duration(s):
    """Parse a duration string like '2h', '45m', or '1h30m' into total minutes."""
    s = s.strip()
    m = _DURATION_RE.fullmatch(s)
    if not s or not m:
        raise ValueError(f"invalid duration: {s!r}")
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    return hours * 60 + minutes
