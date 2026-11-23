"""In-memory mock OrderOps backend used across chapter examples."""

from __future__ import annotations

import time
from typing import Any

ORDERS: dict[str, dict[str, Any]] = {
    "ORD-2026-88412": {
        "order_id": "ORD-2026-88412",
        "tenant_id": "tenant-apac-01",
        "customer_id": "CUST-9012",
        "status": "delayed",
        "total_usd": 340.0,
        "currency": "USD",
        "items": [
            {"sku": "SKU-IND-401", "qty": 2, "unit_price_usd": 120.0},
            {"sku": "SKU-IND-109", "qty": 1, "unit_price_usd": 100.0},
        ],
        "carrier_tracking": "TRK-99812344",
        "promised_delivery_date": "2026-11-18",
    },
    "ORD-2026-88901": {
        "order_id": "ORD-2026-88901",
        "tenant_id": "tenant-eu-02",
        "customer_id": "CUST-3318",
        "status": "delivered",
        "total_usd": 1850.0,
        "currency": "USD",
        "items": [{"sku": "SKU-PRO-900", "qty": 1, "unit_price_usd": 1850.0}],
        "carrier_tracking": "TRK-77100239",
        "promised_delivery_date": "2026-11-15",
    },
}

STOCK: dict[str, dict[str, int]] = {
    "SKU-IND-401": {"warehouse_a": 14, "warehouse_b": 0, "reserved": 4},
    "SKU-IND-109": {"warehouse_a": 0, "warehouse_b": 22, "reserved": 2},
    "SKU-PRO-900": {"warehouse_a": 3, "warehouse_b": 5, "reserved": 1},
}


class OrderOpsMockBackend:
    def __init__(self) -> None:
        self._refunds: dict[str, dict[str, Any]] = {}

    def get_order(self, order_id: str, tenant_id: str) -> dict[str, Any]:
        order = ORDERS.get(order_id)
        if not order or order["tenant_id"] != tenant_id:
            return {"error": f"Order {order_id} not found for tenant {tenant_id}"}
        return order

    def check_inventory(self, sku: str) -> dict[str, Any]:
        rec = STOCK.get(sku, {"warehouse_a": 0, "warehouse_b": 0, "reserved": 0})
        return {"sku": sku, **rec}

    def issue_refund(
        self,
        *,
        order_id: str,
        tenant_id: str,
        amount_usd: float,
        reason: str,
        idempotency_key: str,
        auto_approve_limit_usd: float = 250.0,
    ) -> dict[str, Any]:
        if idempotency_key in self._refunds:
            return self._refunds[idempotency_key]

        order = self.get_order(order_id, tenant_id)
        if "error" in order:
            return {
                "refund_id": "N/A",
                "order_id": order_id,
                "amount_usd": amount_usd,
                "idempotency_key": idempotency_key,
                "status": "rejected",
                "reason": order["error"],
            }

        if amount_usd > order["total_usd"]:
            status = "rejected"
            final_reason = "Requested refund exceeds order total"
        elif amount_usd > auto_approve_limit_usd:
            status = "pending_hitl"
            final_reason = f"Amount ${amount_usd} exceeds auto-approve limit ${auto_approve_limit_usd}"
        else:
            status = "approved"
            final_reason = reason

        result = {
            "refund_id": f"RF-{int(time.time() * 1000)}",
            "order_id": order_id,
            "amount_usd": amount_usd,
            "idempotency_key": idempotency_key,
            "status": status,
            "reason": final_reason,
        }
        self._refunds[idempotency_key] = result
        return result
