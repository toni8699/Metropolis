let sessionToken = null;

function getPlacesLibrary() {
  return window.google?.maps?.places ?? null;
}

function getSessionToken(places) {
  if (!sessionToken && places.AutocompleteSessionToken) {
    sessionToken = new places.AutocompleteSessionToken();
  }
  return sessionToken;
}

/** Normalize legacy + new autocomplete rows to one shape. */
export function normalizePrediction(prediction) {
  if (!prediction) return null;

  if (prediction.placeId || prediction.place_id) {
    const placeId = prediction.placeId || prediction.place_id;
    const mainText =
      prediction.structured_formatting?.main_text ||
      prediction.mainText ||
      prediction.description ||
      "";
    const secondaryText =
      prediction.structured_formatting?.secondary_text ||
      prediction.secondaryText ||
      "";
    return {
      ...prediction,
      placeId,
      place_id: placeId,
      description: prediction.description || mainText,
      structured_formatting: {
        main_text: mainText,
        secondary_text: secondaryText,
      },
    };
  }

  return null;
}

/**
 * Place autocomplete (AutocompleteSuggestion when available, else legacy service).
 */
export async function fetchPlacePredictions(input, options = {}) {
  const trimmed = String(input || "").trim();
  if (!trimmed) return [];

  const places = getPlacesLibrary();
  if (!places) return [];

  const includedPrimaryTypes = options.types?.includes("geocode")
    ? ["geocode"]
    : options.includedPrimaryTypes;

  if (places.AutocompleteSuggestion?.fetchAutocompleteSuggestions) {
    try {
      const request = {
        input: trimmed,
        sessionToken: getSessionToken(places),
      };
      if (includedPrimaryTypes) {
        request.includedPrimaryTypes = includedPrimaryTypes;
      }
      if (options.locationBias) {
        request.locationBias = options.locationBias;
      }
      if (options.bounds) {
        request.locationBias = options.bounds;
      }
      if (options.country) {
        request.includedRegionCodes = [String(options.country).toLowerCase()];
      }

      const { suggestions } =
        await places.AutocompleteSuggestion.fetchAutocompleteSuggestions(request);

      return (suggestions || [])
        .map((suggestion) => {
          const pred = suggestion.placePrediction;
          if (!pred) return null;
          return normalizePrediction({
            placeId: pred.placeId,
            description: pred.text?.text || "",
            mainText: pred.mainText?.text || "",
            secondaryText: pred.secondaryText?.text || "",
            _placePrediction: pred,
          });
        })
        .filter(Boolean);
    } catch {
      // Fall through to legacy AutocompleteService.
    }
  }

  if (!places.AutocompleteService) return [];

  return new Promise((resolve) => {
    const service = new places.AutocompleteService();
    service.getPlacePredictions(
      {
        input: trimmed,
        types: options.types,
        bounds: options.bounds,
        componentRestrictions: options.country
          ? { country: String(options.country).toLowerCase() }
          : undefined,
        sessionToken: getSessionToken(places),
      },
      (predictions, status) => {
        if (status === places.PlacesServiceStatus.OK && predictions?.length) {
          resolve(predictions.map((p) => normalizePrediction(p)).filter(Boolean));
          return;
        }
        resolve([]);
      },
    );
  });
}

/** Resolve lat/lng from a normalized prediction. */
export async function resolvePredictionCoordinates(prediction) {
  const normalized = normalizePrediction(prediction);
  if (!normalized) {
    throw new Error("Invalid place prediction");
  }

  if (normalized._placePrediction?.toPlace) {
    const place = normalized._placePrediction.toPlace();
    await place.fetchFields({ fields: ["location"] });
    const loc = place.location;
    if (loc) {
      const lat = typeof loc.lat === "function" ? loc.lat() : loc.lat;
      const lng = typeof loc.lng === "function" ? loc.lng() : loc.lng;
      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        return { lat, lng };
      }
    }
  }

  const placeId = normalized.placeId || normalized.place_id;
  if (!placeId || !window.google?.maps?.Geocoder) {
    throw new Error("Geocoder unavailable");
  }

  return new Promise((resolve, reject) => {
    const geocoder = new window.google.maps.Geocoder();
    geocoder.geocode({ placeId }, (results, status) => {
      const point = results?.[0]?.geometry?.location;
      if (status === "OK" && point && typeof point.lat === "function") {
        resolve({ lat: point.lat(), lng: point.lng() });
        return;
      }
      reject(new Error("Could not resolve place coordinates"));
    });
  });
}
