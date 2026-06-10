import { describe, expect, it } from "vitest";
import {
  bookingStatusBadgeClass,
  formatBookingStatusLabel,
  isPendingApproval,
} from "./bookingStatus";

describe("bookingStatus", () => {
  it("formats pending approval label", () => {
    expect(formatBookingStatusLabel("PENDING_APPROVAL")).toBe("Pending Approval");
  });

  it("detects pending approval", () => {
    expect(isPendingApproval("PENDING_APPROVAL")).toBe(true);
    expect(isPendingApproval("CONFIRMED")).toBe(false);
  });

  it("returns badge classes for confirmed bookings", () => {
    expect(bookingStatusBadgeClass("CONFIRMED")).toContain("indigo");
  });
});
