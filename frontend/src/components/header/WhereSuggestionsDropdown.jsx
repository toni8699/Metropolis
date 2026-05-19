import { MapPin } from "lucide-react";

export default function WhereSuggestionsDropdown({
  isLoading,
  placePredictions,
  placesError,
  searchQuery,
  onPickPrediction,
}) {
  return (
    <div className="absolute top-[80px] left-0 z-50 w-[430px] rounded-3xl border border-gray-200 bg-white p-4 shadow-xl">
      {isLoading ? (
        <div className="space-y-3">
          {[0, 1, 2].map((row) => (
            <div
              key={row}
              className="flex items-center gap-3 rounded-2xl px-3 py-3"
            >
              <div className="h-10 w-10 animate-pulse rounded-full bg-gray-200" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-40 animate-pulse rounded bg-gray-200" />
                <div className="h-3 w-56 animate-pulse rounded bg-gray-100" />
              </div>
            </div>
          ))}
        </div>
      ) : placePredictions.length > 0 ? (
        <div className="space-y-1">
          {placePredictions.map((prediction) => {
            const title =
              prediction.structured_formatting?.main_text ||
              prediction.description;
            const subtitle =
              prediction.structured_formatting?.secondary_text || "";
            return (
              <button
                key={prediction.place_id}
                onClick={() => onPickPrediction(prediction, title)}
                className="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left transition hover:bg-gray-50"
              >
                <span className="rounded-xl bg-gray-100 p-3 text-gray-700">
                  <MapPin className="h-5 w-5" />
                </span>
                <span className="min-w-0 flex-1 space-y-0.5">
                  <span className="block truncate text-base text-gray-900">
                    {title}
                  </span>
                  <span className="block truncate text-sm text-gray-500">
                    {subtitle}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      ) : placesError ? (
        <p className="px-2 py-6 text-center text-sm text-red-500">{placesError}</p>
      ) : searchQuery.trim() ? (
        <p className="px-2 py-6 text-center text-sm text-gray-500">
          No locations found.
        </p>
      ) : (
        <p className="px-2 py-6 text-center text-sm text-gray-500">
          Start typing to search locations.
        </p>
      )}
    </div>
  );
}
