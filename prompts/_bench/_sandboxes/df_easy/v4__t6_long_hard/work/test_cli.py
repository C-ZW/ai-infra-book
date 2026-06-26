from cli import transform


def test_passthrough():
    assert transform(["a", "b", "c"]) == ["a", "b", "c"]


def test_upper():
    assert transform(["a", "b"], upper=True) == ["A", "B"]


def test_reverse():
    assert transform(["a", "b", "c"], reverse=True) == ["c", "b", "a"]


def test_reverse_with_upper():
    assert transform(["a", "b"], upper=True, reverse=True) == ["B", "A"]
