import {
  Building2,
  CalendarDays,
  CarFront,
  LayoutDashboard,
  ShieldCheck,
  UploadCloud,
  Users,
  Wallet,
} from "lucide-react";

export const TAB = {
  overview: "overview",
  listings: "listings",
  fleet_listings: "fleet_listings",
  host_listings: "host_listings",
  create_listing: "create_listing",
  users: "users",
  kyc: "kyc",
  bookings: "bookings",
  payouts: "payouts",
  availability: "availability",
};

const PAGE_TITLES = {
  [TAB.overview]: "Overview",
  [TAB.listings]: "Manage Listings",
  [TAB.fleet_listings]: "Fleet Listings",
  [TAB.host_listings]: "Host Listings",
  [TAB.create_listing]: "Create Listing",
  [TAB.users]: "Users",
  [TAB.kyc]: "KYC Queue",
  [TAB.bookings]: "Bookings",
  [TAB.payouts]: "Payouts",
  [TAB.availability]: "Availability",
};

export function getNavItems(isAdmin) {
  const items = [{ id: TAB.overview, label: "Overview", icon: LayoutDashboard }];
  if (isAdmin) {
    items.push(
      { id: TAB.fleet_listings, label: "Fleet Listings", icon: CarFront },
      { id: TAB.host_listings, label: "Host Listings", icon: Building2 },
      { id: TAB.create_listing, label: "Create Listing", icon: UploadCloud },
      { id: TAB.users, label: "Users", icon: Users },
      { id: TAB.kyc, label: "KYC Queue", icon: ShieldCheck },
    );
  } else {
    items.push(
      { id: TAB.listings, label: "Listings", icon: CarFront },
      { id: TAB.create_listing, label: "Create Listing", icon: UploadCloud },
      { id: TAB.availability, label: "Availability", icon: CalendarDays },
      { id: TAB.payouts, label: "Payouts", icon: Wallet },
    );
  }
  items.push({ id: TAB.bookings, label: "Bookings", icon: CalendarDays });
  return items;
}

export function getPageTitle(tabId, isAdmin) {
  return PAGE_TITLES[tabId] || (isAdmin ? "Admin Dashboard" : "Host Dashboard");
}

export function isListingsTab(tabId) {
  return (
    tabId === TAB.listings || tabId === TAB.fleet_listings || tabId === TAB.host_listings
  );
}

export function listingsTabId(isAdmin) {
  return isAdmin ? TAB.fleet_listings : TAB.listings;
}

export function listingsTableTitle(activeTab, isAdmin) {
  if (activeTab === TAB.host_listings) return "Host Listings";
  if (isAdmin) return "Fleet Listings";
  return "My Listings";
}
