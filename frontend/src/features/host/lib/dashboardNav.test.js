import { describe, expect, it } from "vitest";
import {
  TAB,
  getNavItems,
  getPageTitle,
  isListingsTab,
  listingsTabId,
  listingsTableTitle,
} from "@/features/host/lib/dashboardNav";

describe("dashboardNav", () => {
  it("returns admin nav items with fleet, host, users, kyc", () => {
    const ids = getNavItems(true).map((item) => item.id);
    expect(ids).toContain(TAB.fleet_listings);
    expect(ids).toContain(TAB.host_listings);
    expect(ids).toContain(TAB.users);
    expect(ids).toContain(TAB.kyc);
    expect(ids).not.toContain(TAB.listings);
  });

  it("returns owner nav items with listings only", () => {
    const ids = getNavItems(false).map((item) => item.id);
    expect(ids).toContain(TAB.listings);
    expect(ids).not.toContain(TAB.fleet_listings);
    expect(ids).not.toContain(TAB.users);
  });

  it("resolves page titles and listings helpers", () => {
    expect(getPageTitle(TAB.bookings, true)).toBe("Bookings");
    expect(getPageTitle("unknown", false)).toBe("Host Dashboard");
    expect(isListingsTab(TAB.host_listings)).toBe(true);
    expect(isListingsTab(TAB.bookings)).toBe(false);
    expect(listingsTabId(true)).toBe(TAB.fleet_listings);
    expect(listingsTabId(false)).toBe(TAB.listings);
    expect(listingsTableTitle(TAB.host_listings, true)).toBe("Host Listings");
    expect(listingsTableTitle(TAB.listings, false)).toBe("My Listings");
  });
});
