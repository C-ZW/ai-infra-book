from textlib.names import format_name
from textlib.greet import greeting
from textlib.report import roster


def test_format_name():
    assert format_name("Ada Lovelace") == "Lovelace, Ada"


def test_greeting():
    assert greeting("Ada Lovelace") == "Hello, Lovelace, Ada"


def test_roster():
    assert roster(["Ada Lovelace", "Alan Turing"]) == ["Lovelace, Ada", "Turing, Alan"]
