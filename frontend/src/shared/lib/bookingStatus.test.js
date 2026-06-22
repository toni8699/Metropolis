import { describe, expect, it } from "vitest";
import {
  bookingStatusBadgeClass,
  formatBookingStatusLabel,
  isPendingApproval,
} from "@/shared/lib/bookingStatus";

describe("bookingStatus", () => {
  it("formats pending approval label", () => {
    expect(formatBookingStatusLabel("PENDING_APPROVAL")).toBe("Pending approval");
  });

  it("formats unpaid pending label", () => {
    expect(formatBookingStatusLabel("PENDING")).toBe("Awaiting payment");
  });

  it("detects pending approval", () => {
    expect(isPendingApproval("PENDING_APPROVAL")).toBe(true);
    expect(isPendingApproval("CONFIRMED")).toBe(false);
  });

  it("returns badge classes for confirmed bookings", () => {
    expect(bookingStatusBadgeClass("CONFIRMED")).toContain("indigo");
  });
});
