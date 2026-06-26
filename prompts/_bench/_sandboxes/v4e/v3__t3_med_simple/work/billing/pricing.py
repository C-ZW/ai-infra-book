"""Pricing helpers for the billing package."""

TAX_RATE = 0.08


def line_subtotal(unit_price, qty):
    """Subtotal for a single line item before tax."""
    return unit_price * qty


def apply_discount(amount, pct):
    """Reduce amount by pct percent (0-100)."""
    return amount * (1 - pct / 100.0)


def compute_total(items, discount_pct=0.0):
    """Total for a list of (unit_price, qty) items, after discount and tax."""
    subtotal = sum(line_subtotal(p, q) for p, q in items)
    discounted = apply_discount(subtotal, discount_pct)
    return round(discounted * (1 + TAX_RATE), 2)
