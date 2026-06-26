import urllib.request


def fetch_url(url):
    """Fetch a URL and return the decoded body. Stdlib only."""
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.read().decode()
