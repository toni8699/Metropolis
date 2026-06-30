/** Browse listing filter URL + API param helpers. */

export const PRICE_DOMAIN = { min: 0, max: 500 };

export const RADIUS_DOMAIN = { min: 5, max: 200, default: 50 };

export const DEFAULT_FILTERS = {
  minPrice: null,
  maxPrice: null,
  bodyTypeIds: [],
  transmission: null,
  fuelTypes: [],
  seats: [],
  featureIds: [],
  radius: RADIUS_DOMAIN.default,
};

export const FILTER_URL_KEYS = [
  "minPrice",
  "maxPrice",
  "bodyTypeIds",
  "transmission",
  "fuelTypes",
  "seats",
  "featureIds",
  "radius",
];

function splitInts(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((part) => Number.parseInt(part.trim(), 10))
    .filter((num) => Number.isFinite(num));
}

function splitStrings(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

export function parseFiltersFromSearchParams(urlSearchParams) {
  const minRaw = urlSearchParams.get("minPrice");
  const maxRaw = urlSearchParams.get("maxPrice");
  const radiusRaw = urlSearchParams.get("radius");
  return {
    minPrice: minRaw != null && minRaw !== "" ? Number(minRaw) : null,
    maxPrice: maxRaw != null && maxRaw !== "" ? Number(maxRaw) : null,
    bodyTypeIds: splitInts(urlSearchParams.get("bodyTypeIds")),
    transmission: urlSearchParams.get("transmission") || null,
    fuelTypes: splitStrings(urlSearchParams.get("fuelTypes")),
    seats: splitInts(urlSearchParams.get("seats")),
    featureIds: splitInts(urlSearchParams.get("featureIds")),
    radius:
      radiusRaw != null && radiusRaw !== "" ? Number(radiusRaw) : RADIUS_DOMAIN.default,
  };
}

export function filtersActive(filters) {
  return (
    filters.minPrice != null
    || filters.maxPrice != null
    || filters.bodyTypeIds.length > 0
    || Boolean(filters.transmission)
    || filters.fuelTypes.length > 0
    || filters.seats.length > 0
    || filters.featureIds.length > 0
  );
}

/** Build URL or API query params. urlOnly=true for browser URL sync. */
export function filtersToParams(filters, { searchContext, pagination, urlOnly = false } = {}) {
  const params = new URLSearchParams();

  if (!urlOnly && searchContext) {
    if (searchContext.searchParams?.pickupDate) {
      params.set("start", `${searchContext.searchParams.pickupDate}T00:00:00Z`);
    }
    if (searchContext.searchParams?.returnDate) {
      params.set("end", `${searchContext.searchParams.returnDate}T00:00:00Z`);
    }
    const coords = searchContext.searchParams?.coordinates;
    if (coords?.lat != null && coords?.lng != null) {
      params.set("lat", String(coords.lat));
      params.set("lng", String(coords.lng));
      params.set("radius", String(filters.radius ?? RADIUS_DOMAIN.default));
    }
  }

  if (filters.minPrice != null) params.set("minPrice", String(filters.minPrice));
  if (filters.maxPrice != null) params.set("maxPrice", String(filters.maxPrice));
  if (filters.bodyTypeIds.length) params.set("bodyTypeIds", filters.bodyTypeIds.join(","));
  if (filters.transmission) params.set("transmission", filters.transmission);
  if (filters.fuelTypes.length) params.set("fuelTypes", filters.fuelTypes.join(","));

  if (urlOnly) {
    if (filters.seats.length) params.set("seats", filters.seats.join(","));
    if (filters.radius != null && filters.radius !== RADIUS_DOMAIN.default) {
      params.set("radius", String(filters.radius));
    }
  } else {
    const exactSeats = filters.seats.filter((seat) => seat !== 7);
    if (exactSeats.length) params.set("seats", exactSeats.join(","));
    if (filters.seats.includes(7)) params.set("seatsGte", "7");
    if (pagination?.limit != null) params.set("limit", String(pagination.limit));
    if (pagination?.offset != null) params.set("offset", String(pagination.offset));
  }

  if (filters.featureIds.length) params.set("featureIds", filters.featureIds.join(","));
  return params;
}
