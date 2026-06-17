const RECENT_LISTING_KEY = "hostRecentListingAt";
const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000;

export function markRecentListingCreated() {
  sessionStorage.setItem(RECENT_LISTING_KEY, String(Date.now()));
}

export function isRecentListingHost() {
  const raw = sessionStorage.getItem(RECENT_LISTING_KEY);
  if (!raw) return false;
  return Date.now() - Number(raw) < TWENTY_FOUR_HOURS_MS;
}

export function isListingCreatedWithin24h(createdAt) {
  if (!createdAt) return false;
  const created = new Date(createdAt).getTime();
  if (!Number.isFinite(created)) return false;
  return Date.now() - created < TWENTY_FOUR_HOURS_MS;
}

export function newestListing(listings) {
  if (!Array.isArray(listings) || !listings.length) return null;
  return [...listings].sort(
    (a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime(),
  )[0];
}

export function shouldShowOptimizationChecklist(listings, { isAdmin = false } = {}) {
  if (isAdmin) return false;
  if (isRecentListingHost()) return true;
  return (listings || []).some((listing) => isListingCreatedWithin24h(listing.createdAt));
}
