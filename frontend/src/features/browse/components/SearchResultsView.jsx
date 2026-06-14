import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  GoogleMap,
  OverlayView,
  OverlayViewF,
  useJsApiLoader,
} from "@react-google-maps/api";
import {
  ChevronLeft,
  ChevronRight,
  List,
  Map as MapIcon,
} from "lucide-react";
import CarGrid from "@/shared/components/CarGrid";
import ListingRatingLine from "@/features/listings/components/ListingRatingLine";
import BodyCard from "@/shared/components/BodyCard";
import { formatPricePerDay } from "@/shared/lib/formatPrice";
import { spreadOverlappingMarkers } from "@/shared/lib/mapMarkers";

const fallbackCenter = { lat: 43.6532, lng: -79.3832 };
const simplifiedMapStyles = [
  { featureType: "administrative", elementType: "all", stylers: [{ visibility: "off" }] },
  { featureType: "poi.business", elementType: "all", stylers: [{ visibility: "off" }] },
  { featureType: "poi.medical", elementType: "all", stylers: [{ visibility: "off" }] },
  { featureType: "poi.school", elementType: "all", stylers: [{ visibility: "off" }] },
  { featureType: "transit", elementType: "all", stylers: [{ visibility: "off" }] },
];

function parseCoord(value) {
  if (value == null) return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const normalized = String(value).trim().replace(",", ".");
  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

const markerOffset = (width, height) => ({
  x: -(width / 2),
  y: -(height / 2),
});

function PriceMarker({ car, isActive, onClick }) {
  const priceLabel = formatPricePerDay(car.pricePerDay);
  if (priceLabel == null) return null;

  return (
    <OverlayViewF
      position={{ lat: car.lat, lng: car.lng }}
      mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
      getPixelPositionOffset={markerOffset}
    >
      <div style={{ position: "absolute", left: 0, top: 0 }}>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onClick();
          }}
          onMouseDown={(event) => event.stopPropagation()}
          onTouchStart={(event) => event.stopPropagation()}
          className={`cursor-pointer whitespace-nowrap rounded-full border-2 border-black px-3 py-1.5 text-sm font-extrabold shadow-[4px_4px_0px_0px_rgba(24,59,30,0.6)] transition-transform hover:scale-105 ${
            isActive ? "bg-[#183B1E] text-white" : "bg-[#FCFCE5] text-black"
          }`}
        >
          ${priceLabel}
        </button>
      </div>
    </OverlayViewF>
  );
}

function MapPopupCard({ car }) {
  const images = car.images?.length
    ? car.images
    : [car.image || car.photos?.[0]].filter(Boolean);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const currentImage = images[currentImageIndex];
  const listingUrl = `/app/listings/${car.listingId || car.id}`;
  const title = [car.make || car.brand, car.model].filter(Boolean).join(" ");

  const handleNextImage = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (images.length <= 1) return;
    setCurrentImageIndex((index) => (index + 1) % images.length);
  };

  const handlePrevImage = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (images.length <= 1) return;
    setCurrentImageIndex((index) => (index - 1 + images.length) % images.length);
  };

  return (
    <a
      href={listingUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="group block w-[280px] cursor-pointer overflow-hidden rounded-[1.8rem] border-2 border-black bg-[#FCFCE5] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.55)]"
      onClick={(event) => event.stopPropagation()}
      onMouseDown={(event) => event.stopPropagation()}
      onTouchStart={(event) => event.stopPropagation()}
    >
      <div className="relative h-[180px] w-full overflow-hidden rounded-b-[1.2rem] bg-[#dbe8be]">
        {currentImage ? (
          <img
            src={currentImage}
            alt={car.title || title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gray-100 text-sm text-gray-500">
            No image
          </div>
        )}

        {images.length > 1 && (
          <>
            <button
              onClick={handlePrevImage}
              className="absolute left-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border-2 border-black bg-[#FCFCE5] text-black opacity-0 shadow-sm transition hover:scale-110 group-hover:opacity-100"
              aria-label="Previous image"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={handleNextImage}
              className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border-2 border-black bg-[#FCFCE5] text-black opacity-0 shadow-sm transition hover:scale-110 group-hover:opacity-100"
              aria-label="Next image"
            >
              <ChevronRight size={16} />
            </button>

            <div className="absolute bottom-3 left-0 right-0 flex justify-center gap-1.5">
              {images.map((image, index) => (
                <span
                  key={`${image}-${index}`}
                  className={`h-1.5 w-1.5 rounded-full ${
                    index === currentImageIndex ? "bg-white" : "bg-white/60"
                  }`}
                />
              ))}
            </div>
          </>
        )}
      </div>

      <div className="flex flex-col gap-1.5 p-4">
        <div className="flex w-full items-center gap-3">
          <p className="min-w-0 flex-1 truncate text-lg font-extrabold text-black">
            {title || car.title || "Vehicle"}
          </p>
          <ListingRatingLine listing={car} />
        </div>
        <p className="truncate text-sm font-semibold text-[#35593b]">
          {car.details || car.sourceType || "Automatic"}
        </p>
        <p className="mt-1 text-black">
          <span className="font-extrabold">${formatPricePerDay(car.pricePerDay) ?? "—"}</span>
          <span className="font-semibold"> / day</span>
        </p>
      </div>
    </a>
  );
}

function ListingPopup({ car }) {
  return (
    <OverlayViewF
      position={{ lat: car.lat, lng: car.lng }}
      mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
    >
      <div
        className="relative"
        style={{ transform: "translate(-50%, calc(-100% - 14px))" }}
        onClick={(event) => event.stopPropagation()}
        onMouseDown={(event) => event.stopPropagation()}
        onTouchStart={(event) => event.stopPropagation()}
      >
        <MapPopupCard car={car} />
      </div>
    </OverlayViewF>
  );
}

function fitMapToCars(map, cars) {
  if (!map || !cars.length || !window.google?.maps) return;
  const bounds = new window.google.maps.LatLngBounds();
  for (const car of cars) {
    bounds.extend({ lat: car.lat, lng: car.lng });
  }
  map.fitBounds(bounds, { top: 64, right: 48, bottom: 48, left: 48 });
}

export default function SearchResultsView({
  cars = [],
  cityLabel = "Toronto",
  searchCenter = null,
  isLoading = false,
}) {
  const [activeId, setActiveId] = useState(null);
  const [isMapFullscreen, setIsMapFullscreen] = useState(false);
  const [selectedCar, setSelectedCar] = useState(null);
  const mapRef = useRef(null);
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const { isLoaded } = useJsApiLoader({
    id: "google-maps-script",
    googleMapsApiKey: apiKey || "",
    libraries: ["places"],
  });

  const mapCars = useMemo(() => {
    const withCoords = cars
      .map((car) => {
        const lat = parseCoord(car.lat ?? car.latitude);
        const lng = parseCoord(car.lng ?? car.longitude);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
        const listingId = car.listingId ?? car.id;
        const pricePerDay =
          car.pricePerDay ?? car.price_per_day ?? car.priceSnapshot?.pricePerDay;
        return {
          ...car,
          id: listingId,
          listingId,
          lat,
          lng,
          pricePerDay,
        };
      })
      .filter(Boolean);
    return spreadOverlappingMarkers(withCoords);
  }, [cars]);

  // Center on listing pins first — search city can be far from Toronto fleet data.
  const center = useMemo(() => {
    if (mapCars.length > 0) {
      const latAvg = mapCars.reduce((sum, c) => sum + c.lat, 0) / mapCars.length;
      const lngAvg = mapCars.reduce((sum, c) => sum + c.lng, 0) / mapCars.length;
      return { lat: latAvg, lng: lngAvg };
    }
    if (
      searchCenter &&
      Number.isFinite(searchCenter.lat) &&
      Number.isFinite(searchCenter.lng)
    ) {
      return { lat: searchCenter.lat, lng: searchCenter.lng };
    }
    return fallbackCenter;
  }, [mapCars, searchCenter]);

  const onMapLoad = useCallback((map) => {
    mapRef.current = map;
  }, []);

  useEffect(() => {
    if (mapCars.length > 0) {
      fitMapToCars(mapRef.current, mapCars);
    } else if (
      mapRef.current &&
      searchCenter &&
      Number.isFinite(searchCenter.lat) &&
      Number.isFinite(searchCenter.lng)
    ) {
      mapRef.current.setCenter({ lat: searchCenter.lat, lng: searchCenter.lng });
      mapRef.current.setZoom(11);
    }
  }, [mapCars, searchCenter]);

  const handleMapClick = (event) => {
    if (event?.placeId) {
      event.stop();
      return;
    }
    setSelectedCar(null);
  };

  return (
    <div className="w-full">
      <div className="flex w-full flex-col gap-4 md:flex-row md:gap-5">
        <BodyCard
          className={`w-full px-3 py-4 sm:px-4 lg:px-5 transition-all duration-300 ${
            isMapFullscreen ? "hidden" : "md:w-[55%] xl:w-[60%]"
          }`}
        >
          <h2 className="mb-4 text-xl font-extrabold text-[#183B1E]">
            {isLoading ? "Loading cars..." : `${cars.length} cars in ${cityLabel}`}
          </h2>
          <div className="mb-4 md:hidden">
            <button
              onClick={() => setIsMapFullscreen(true)}
              className="mx-auto flex items-center gap-1.5 rounded-full border-2 border-black border-b-4 bg-[#E34B31] px-4 py-2 text-sm font-extrabold text-white shadow-[4px_4px_0px_0px_rgba(0,0,0,0.8)] active:border-b-0"
            >
              <MapIcon className="h-4 w-4" />
              Show map
            </button>
          </div>
          {isLoading ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {Array.from({ length: 6 }).map((_, idx) => (
                <div key={idx} className="space-y-3">
                  <div className="aspect-[20/19] animate-pulse rounded-2xl bg-gray-200" />
                  <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200" />
                  <div className="h-4 w-1/2 animate-pulse rounded bg-gray-100" />
                </div>
              ))}
            </div>
          ) : cars.length === 0 ? (
            <div className="rounded-3xl border-2 border-black bg-[#FCFCE5] p-6 text-center shadow-[6px_6px_0px_0px_rgba(24,59,30,0.5)]">
              <p className="text-base font-extrabold text-[#183B1E]">No cars near {cityLabel}</p>
              <p className="mt-2 text-sm text-[#35593b]">
                Try another city or widen your search. Listings only show within 50 km of your
                picked location.
              </p>
            </div>
          ) : (
            <CarGrid
              cars={cars}
              compact
              distanceById={Object.fromEntries(cars.map((c) => [c.id, c.distanceKm]))}
            />
          )}
        </BodyCard>

        <aside
          className={`${
            isMapFullscreen
              ? "block w-full"
              : "hidden md:block md:w-[45%] xl:w-[40%]"
          } transition-all duration-300`}
        >
          <div className="sticky top-[64px] h-[calc(100vh-64px)] p-4">
            {!apiKey ? (
              <div className="rounded-2xl border border-slate-300 bg-white p-4 text-sm text-slate-700">
                Add `VITE_GOOGLE_MAPS_API_KEY` in `frontend/.env.local` to show map.
              </div>
            ) : !isLoaded ? (
              <div className="rounded-2xl border border-slate-300 bg-white p-4 text-sm text-slate-700">
                Loading map...
              </div>
            ) : (
              <div className="relative h-full w-full overflow-hidden rounded-2xl border-2 border-black shadow-[6px_6px_0px_0px_rgba(24,59,30,0.45)]">
                <button
                  onClick={() => setIsMapFullscreen((v) => !v)}
                  className="absolute left-1/2 top-2.5 z-10 -translate-x-1/2 rounded-full border-2 border-black border-b-4 bg-[#FCFCE5] px-3 py-1.5 text-xs font-extrabold text-[#183B1E] shadow-md active:border-b-0"
                >
                  {isMapFullscreen ? (
                    <span className="flex items-center gap-2">
                      <List className="h-3.5 w-3.5" />
                      Show list
                    </span>
                  ) : (
                    "Full screen map"
                  )}
                </button>
                <GoogleMap
                  mapContainerStyle={{ width: "100%", height: "100%" }}
                  center={center}
                  zoom={mapCars.length > 1 ? 11 : 12}
                  onLoad={onMapLoad}
                  onClick={handleMapClick}
                  options={{
                    disableDefaultUI: true,
                    zoomControl: true,
                    clickableIcons: false,
                    styles: simplifiedMapStyles,
                  }}
                >
                  {mapCars.map((car) => {
                    const markerKey = car.listingId ?? car.id;
                    return (
                      <PriceMarker
                        key={markerKey}
                        car={car}
                        isActive={activeId === markerKey}
                        onClick={() => {
                          setActiveId(markerKey);
                          setSelectedCar(car);
                        }}
                      />
                    );
                  })}

                  {selectedCar && (
                    <ListingPopup
                      car={selectedCar}
                    />
                  )}
                </GoogleMap>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
