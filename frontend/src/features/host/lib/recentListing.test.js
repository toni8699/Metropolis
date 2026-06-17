import { describe, expect, it, beforeEach, afterEach } from "vitest";
import {
  isListingCreatedWithin24h,
  isRecentListingHost,
  markRecentListingCreated,
  shouldShowOptimizationChecklist,
} from "@/features/host/lib/recentListing";

describe("recentListing helpers", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it("marks and reads recent host listing within 24h", () => {
    expect(isRecentListingHost()).toBe(false);
    markRecentListingCreated();
    expect(isRecentListingHost()).toBe(true);
  });

  it("detects listings created within 24 hours", () => {
    const recent = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    const old = new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString();
    expect(isListingCreatedWithin24h(recent)).toBe(true);
    expect(isListingCreatedWithin24h(old)).toBe(false);
  });

  it("shows optimization checklist for new hosts only", () => {
    markRecentListingCreated();
    expect(shouldShowOptimizationChecklist([], { isAdmin: false })).toBe(true);
    expect(shouldShowOptimizationChecklist([], { isAdmin: true })).toBe(false);
  });
});
