export const googleMapId = import.meta.env.VITE_GOOGLE_MAP_ID?.trim() || undefined;

/** Geographic center of Canada — default map view when no pin is set. */
export const CANADA_CENTER = { lat: 56.1304, lng: -106.3468 };

export const CANADA_MAP_OPTIONS = {
  streetViewControl: false,
  mapTypeControl: false,
  fullscreenControl: false,
  clickableIcons: false,
};

/** Parse lat/lng from number or locale decimal string (e.g. "43,65"). */
export function parseCoord(value) {
  if (value == null) return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const normalized = String(value).trim().replace(",", ".");
  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

export function listingCoords(entity) {
  const lat = parseCoord(entity?.lat ?? entity?.latitude);
  const lng = parseCoord(entity?.lng ?? entity?.longitude);
  if (lat == null || lng == null) return null;
  return { lat, lng };
}

export function haversineKm(from, to) {
  if (!from || !to) return null;
  const R = 6371;
  const dLat = deg2rad(to.lat - from.lat);
  const dLng = deg2rad(to.lng - from.lng);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(from.lat)) *
      Math.cos(deg2rad(to.lat)) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function deg2rad(deg) {
  return deg * (Math.PI / 180);
}

export function getUserLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(null),
      { enableHighAccuracy: false, timeout: 4000 }
    );
  });
}
