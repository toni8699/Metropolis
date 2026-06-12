import { describe, expect, it } from "vitest";
import { validateReviewForm } from "@/shared/lib/reviewForm";

describe("validateReviewForm", () => {
  it("requires overall rating", () => {
    expect(validateReviewForm({ rating: 0 }).ok).toBe(false);
  });

  it("allows listing review without sub-ratings", () => {
    expect(validateReviewForm({ rating: 5, targetType: "LISTING" }).ok).toBe(true);
  });

  it("rejects unknown target type", () => {
    expect(validateReviewForm({ rating: 4, targetType: "VEHICLE" }).ok).toBe(false);
  });
});
