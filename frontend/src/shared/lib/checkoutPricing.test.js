import { describe, expect, it } from "vitest";
import { computeCheckoutTotals } from "@/shared/lib/checkoutPricing";

describe("computeCheckoutTotals", () => {
  it("computes fees for multi-day rental", () => {
    const result = computeCheckoutTotals(100, 3);
    expect(result.subtotal).toBe(300);
    expect(result.cleaningFee).toBe(50);
    expect(result.serviceFee).toBe(30);
    expect(result.total).toBe(380);
    expect(result.dayCount).toBe(3);
  });

  it("uses at least one day", () => {
    expect(computeCheckoutTotals(80, 0).dayCount).toBe(1);
  });
});
