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

/**
 * Resolve the user's coordinates via the browser Geolocation API.
 * Returns `{ coords, error }`; `coords` is null on failure and `error` is one of
 * "insecure" | "unsupported" | "denied" | "unavailable" | "timeout".
 *
 * Note: browsers only show the permission prompt on a secure context
 * (https:// or localhost). On an insecure origin (e.g. an http:// LAN IP) the
 * API errors immediately with no prompt — surfaced here as "insecure".
 */
export function getUserLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve({ coords: null, error: "unsupported" });
      return;
    }
    if (typeof window !== "undefined" && window.isSecureContext === false) {
      resolve({ coords: null, error: "insecure" });
      return;
    }

    const onSuccess = (pos) =>
      resolve({ coords: { lat: pos.coords.latitude, lng: pos.coords.longitude }, error: null });
    const reasonFor = (err) =>
      err.code === err.PERMISSION_DENIED
        ? "denied"
        : err.code === err.TIMEOUT
          ? "timeout"
          : "unavailable";

    // Safari/CoreLocation often returns POSITION_UNAVAILABLE on the first attempt even when
    // permission is granted; retry once with a fresh high-accuracy fix before giving up.
    const attempt = (isRetry) => {
      navigator.geolocation.getCurrentPosition(
        onSuccess,
        (err) => {
          if (!isRetry && err.code === err.POSITION_UNAVAILABLE) {
            setTimeout(() => attempt(true), 700);
            return;
          }
          resolve({ coords: null, error: reasonFor(err) });
        },
        isRetry
          ? { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
          : { enableHighAccuracy: false, timeout: 15000, maximumAge: 60000 }
      );
    };
    attempt(false);
  });
}
