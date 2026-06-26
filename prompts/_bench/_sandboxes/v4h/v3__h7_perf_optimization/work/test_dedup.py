from dedup import dedupe_preserve_order


def test_basic():
    assert dedupe_preserve_order([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_strings():
    assert dedupe_preserve_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_empty():
    assert dedupe_preserve_order([]) == []
