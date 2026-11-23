import type { OrderRecord, RefundResult } from "./types.js";

const ORDERS: Record<string, OrderRecord> = {
  "ORD-2026-88412": {
    orderId: "ORD-2026-88412",
    tenantId: "tenant-apac-01",
    customerId: "CUST-9012",
    status: "delayed",
    totalUsd: 340.0,
    currency: "USD",
    items: [
      { sku: "SKU-IND-401", qty: 2, unitPriceUsd: 120.0 },
      { sku: "SKU-IND-109", qty: 1, unitPriceUsd: 100.0 },
    ],
    carrierTracking: "TRK-99812344",
    promisedDeliveryDate: "2026-11-18",
  },
  "ORD-2026-88901": {
    orderId: "ORD-2026-88901",
    tenantId: "tenant-eu-02",
    customerId: "CUST-3318",
    status: "delivered",
    totalUsd: 1850.0,
    currency: "USD",
    items: [{ sku: "SKU-PRO-900", qty: 1, unitPriceUsd: 1850.0 }],
    carrierTracking: "TRK-77100239",
    promisedDeliveryDate: "2026-11-15",
  },
};

const REFUND_IDEMPOTENCY_STORE = new Map<string, RefundResult>();

export class OrderOpsMockBackend {
  getOrder(orderId: string, tenantId: string): OrderRecord | { error: string } {
    const order = ORDERS[orderId];
    if (!order || order.tenantId !== tenantId) {
      return { error: `Order ${orderId} not found for tenant ${tenantId}` };
    }
    return order;
  }

  checkInventory(sku: string): { sku: string; warehouseA: number; warehouseB: number; reserved: number } {
    const stockMap: Record<string, { warehouseA: number; warehouseB: number; reserved: number }> = {
      "SKU-IND-401": { warehouseA: 14, warehouseB: 0, reserved: 4 },
      "SKU-IND-109": { warehouseA: 0, warehouseB: 22, reserved: 2 },
      "SKU-PRO-900": { warehouseA: 3, warehouseB: 5, reserved: 1 },
    };
    const rec = stockMap[sku] ?? { warehouseA: 0, warehouseB: 0, reserved: 0 };
    return { sku, ...rec };
  }

  issueRefund(params: {
    orderId: string;
    tenantId: string;
    amountUsd: number;
    reason: string;
    idempotencyKey: string;
    autoApproveLimitUsd?: number;
  }): RefundResult {
    const existing = REFUND_IDEMPOTENCY_STORE.get(params.idempotencyKey);
    if (existing) {
      return existing;
    }

    const order = this.getOrder(params.orderId, params.tenantId);
    if ("error" in order) {
      return {
        refundId: "N/A",
        orderId: params.orderId,
        amountUsd: params.amountUsd,
        idempotencyKey: params.idempotencyKey,
        status: "rejected",
        reason: order.error,
      };
    }

    const limit = params.autoApproveLimitUsd ?? 250.0;
    const status =
      params.amountUsd > order.totalUsd
        ? "rejected"
        : params.amountUsd > limit
          ? "pending_hitl"
          : "approved";

    const result: RefundResult = {
      refundId: `RF-${Date.now()}`,
      orderId: params.orderId,
      amountUsd: params.amountUsd,
      idempotencyKey: params.idempotencyKey,
      status,
      reason:
        status === "rejected"
          ? "Requested refund exceeds order total"
          : status === "pending_hitl"
            ? `Amount $${params.amountUsd} exceeds auto-approve limit $${limit}`
            : params.reason,
    };
    REFUND_IDEMPOTENCY_STORE.set(params.idempotencyKey, result);
    return result;
  }
}
