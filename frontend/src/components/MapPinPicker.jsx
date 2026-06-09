import { useCallback, useRef, useState } from "react";
import { GoogleMap, MarkerF } from "@react-google-maps/api";
import { CANADA_CENTER, CANADA_MAP_OPTIONS } from "../lib/location";

const mapContainerStyle = { width: "100%", height: "100%" };

export default function MapPinPicker({
  apiKey,
  isLoaded,
  latitude,
  longitude,
  onPinMove,
  countryZoom = 4,
  pinZoom = 14,
}) {
  const mapRef = useRef(null);
  const [centerPosition, setCenterPosition] = useState(() =>
    Number.isFinite(latitude) && Number.isFinite(longitude)
      ? { lat: latitude, lng: longitude }
      : CANADA_CENTER,
  );
  const hasPin = Number.isFinite(latitude) && Number.isFinite(longitude);
  const position = hasPin ? { lat: latitude, lng: longitude } : null;

  const centerRef = useRef(null);
  const readCenter = useCallback(() => {
    const map = mapRef.current;
    if (!map) return null;
    const center = map.getCenter();
    if (!center) return null;
    const lat = center.lat();
    const lng = center.lng();
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
    return { lat, lng };
  }, []);

  const syncMarkerToCenter = useCallback(() => {
    const next = readCenter();
    if (!next) return;
    setCenterPosition((prev) => {
      if (!prev) return next;
      const threshold = 1e-7;
      if (Math.abs(prev.lat - next.lat) < threshold && Math.abs(prev.lng - next.lng) < threshold) {
        return prev;
      }
      return next;
    });
  }, [readCenter]);

  const notifyCenter = useCallback(() => {
    const next = readCenter();
    if (!next) return;
    const { lat, lng } = next;
    const prev = centerRef.current;
    const threshold = 1e-6;
    if (prev && Math.abs(prev.lat - lat) < threshold && Math.abs(prev.lng - lng) < threshold) {
      return;
    }
    centerRef.current = { lat, lng };
    setCenterPosition(next);
    onPinMove(lat, lng);
  }, [onPinMove, readCenter]);

  const handleLoad = useCallback(
    (map) => {
      mapRef.current = map;
      const target = hasPin ? position : CANADA_CENTER;
      map.setCenter(target);
      map.setZoom(hasPin ? pinZoom : countryZoom);
      setCenterPosition(target);
      notifyCenter();
    },
    [countryZoom, hasPin, notifyCenter, pinZoom, position],
  );

  if (!apiKey) {
    return (
      <div className="flex h-full items-center justify-center px-6 text-sm text-gray-600">
        Add `VITE_GOOGLE_MAPS_API_KEY` in `frontend/.env.local` to use map picker.
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="flex h-full items-center justify-center px-6 text-sm text-gray-600">
        Loading map...
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      {!hasPin && (
        <div className="pointer-events-none absolute inset-x-4 top-4 z-10 rounded-lg border border-gray-200 bg-white/95 px-3 py-2 text-sm text-gray-700 shadow-sm">
          Pan the map and keep pin on your pickup spot.
        </div>
      )}
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        defaultCenter={CANADA_CENTER}
        defaultZoom={countryZoom}
        onLoad={handleLoad}
        onCenterChanged={syncMarkerToCenter}
        onIdle={notifyCenter}
        options={CANADA_MAP_OPTIONS}
      >
        <MarkerF
          position={centerPosition}
          draggable={false}
          clickable={false}
        />
      </GoogleMap>
    </div>
  );
}
