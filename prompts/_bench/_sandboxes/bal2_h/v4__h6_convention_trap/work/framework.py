"""In-house micro web framework. Conventions used across ALL handlers:
- declare routes with the @route(path) decorator
- return success with ok(payload); never return raw dicts
- return failures with err(message); errors are RETURNED, never raised
- build strings with str.format(), not f-strings
"""

_ROUTES = {}


def route(path, method="GET"):
    def deco(fn):
        _ROUTES[(method.upper(), path)] = fn
        return fn
    return deco


def ok(payload):
    return {"status": "ok", "data": payload}


def err(message):
    return {"status": "error", "message": message}
