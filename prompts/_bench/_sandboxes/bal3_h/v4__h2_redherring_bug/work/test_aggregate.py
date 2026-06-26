from aggregate import summarize, top_user

# user_id arrives from two upstream sources: one sends ints, one sends strings.
EVENTS = [
    {"user_id": 1, "amount": 10},
    {"user_id": "1", "amount": 20},
    {"user_id": 2, "amount": 5},
]


def test_user1_total():
    # User 1 spent 10 + 20 = 30, regardless of int/str id formatting.
    assert summarize(EVENTS)["1"] == 30


def test_top_user():
    assert top_user(EVENTS) == "1"
