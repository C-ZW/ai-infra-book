from cli import transform


def test_passthrough():
    assert transform(["a", "b", "c"]) == ["a", "b", "c"]


def test_upper():
    assert transform(["a", "b"], upper=True) == ["A", "B"]
