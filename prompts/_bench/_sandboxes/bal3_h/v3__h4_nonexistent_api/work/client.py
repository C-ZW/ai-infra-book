class ApiClient:
    """Minimal HTTP client. Only GET and POST are supported by the backend."""

    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, path):
        return {"_method": "GET", "path": path}

    def post(self, path, body):
        return {"_method": "POST", "path": path, "body": body}
