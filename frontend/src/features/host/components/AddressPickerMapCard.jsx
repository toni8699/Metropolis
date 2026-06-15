import { GoogleMap, Marker } from "@react-google-maps/api";
import { MapPin } from "lucide-react";
import { CANADA_CENTER, CANADA_MAP_OPTIONS } from "@/shared/lib/location";

const mapContainerStyle = {
  width: "100%",
  height: "260px",
};

export default function AddressPickerMapCard({ apiKey, isMapLoaded, latitude, longitude }) {
  const lat = Number(latitude);
  const lng = Number(longitude);
  const hasCoordinates = Number.isFinite(lat) && Number.isFinite(lng);
  const center = hasCoordinates ? { lat, lng } : CANADA_CENTER;
  const zoom = hasCoordinates ? 14 : 4;

  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      <div className="border-b border-gray-200 px-4 py-3 flex items-center gap-2">
        <MapPin className="h-4 w-4 text-gray-500" />
        <p className="text-sm font-medium text-gray-700">Location map preview</p>
      </div>
      <div className="p-4">
        {!apiKey ? (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            Add `VITE_GOOGLE_MAPS_API_KEY` in `frontend/.env.local` to show map preview.
          </div>
        ) : !isMapLoaded ? (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            Loading map...
          </div>
        ) : (
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={center}
            zoom={zoom}
            options={CANADA_MAP_OPTIONS}
          >
            {hasCoordinates && <Marker position={{ lat, lng }} />}
          </GoogleMap>
        )}
      </div>
    </div>
  );
}
