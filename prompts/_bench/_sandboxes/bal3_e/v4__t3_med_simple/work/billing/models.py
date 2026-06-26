"""Data models for billing."""

from dataclasses import dataclass


@dataclass
class Item:
    name: str
    unit_price: float
    qty: int


@dataclass
class Invoice:
    customer: str
    items: list
