import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";

const containerStyle = {
  width: "100%",
  height: "420px",
};

const fallbackCenter = { lat: 45.5017, lng: -73.5673 };

export default function MapView({ listings, onSelect }) {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const { isLoaded } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey: apiKey || "",
  });

  if (!apiKey) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
        Add `VITE_GOOGLE_MAPS_API_KEY` in `frontend/.env.local` to enable map.
      </div>
    );
  }

  if (!isLoaded) {
    return <div className="p-4">Loading map...</div>;
  }

  const first = listings.find((l) => l.lat && l.lng);
  const center = first ? { lat: first.lat, lng: first.lng } : fallbackCenter;

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={12}>
      {listings
        .filter((l) => l.lat && l.lng)
        .map((listing) => (
          <Marker
            key={listing.listingId}
            position={{ lat: listing.lat, lng: listing.lng }}
            onClick={() => onSelect(listing)}
          />
        ))}
    </GoogleMap>
  );
}
