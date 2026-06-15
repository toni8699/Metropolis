import { useEffect, useState } from "react";
import { fetchPlacePredictions } from "@/shared/lib/placesAutocomplete";

const DEFAULT_TYPES = ["geocode"];

/** Debounced Google Places autocomplete for a text query. */
export function usePlacesAutocomplete(
  query,
  {
    enabled = true,
    debounceMs = 300,
    types = DEFAULT_TYPES,
    country,
    mapsReady = true,
    placesLoadError = null,
  } = {},
) {
  const [predictions, setPredictions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [placesError, setPlacesError] = useState("");
  const mapsLoadFailed = Boolean(placesLoadError);

  useEffect(() => {
    if (!enabled) {
      setPredictions([]);
      setIsLoading(false);
      setPlacesError("");
      return undefined;
    }

    const trimmed = query.trim();
    if (!trimmed) {
      setPredictions([]);
      setIsLoading(false);
      setPlacesError("");
      return undefined;
    }

    if (mapsLoadFailed) {
      setPredictions([]);
      setIsLoading(false);
      setPlacesError("Google Maps failed to load.");
      return undefined;
    }

    if (!mapsReady || !window.google?.maps?.places) {
      setPredictions([]);
      setIsLoading(false);
      setPlacesError("Location suggestions are not ready yet.");
      return undefined;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(async () => {
      setIsLoading(true);
      setPlacesError("");
      try {
        const next = await fetchPlacePredictions(trimmed, { types, country });
        if (!cancelled) {
          setPredictions(next);
        }
      } catch {
        if (!cancelled) {
          setPredictions([]);
          setPlacesError("Could not fetch location suggestions.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }, debounceMs);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [query, enabled, debounceMs, types, country, mapsReady, mapsLoadFailed]);

  return { predictions, isLoading, placesError, setPlacesError, setPredictions };
}
