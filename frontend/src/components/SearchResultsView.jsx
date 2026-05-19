import { useMemo, useState } from "react";
import {
  GoogleMap,
  OverlayView,
  useJsApiLoader,
} from "@react-google-maps/api";
import {
  ChevronLeft,
  ChevronRight,
  List,
  Map as MapIcon,
  Star,
} from "lucide-react";
import CarGrid from "./CarGrid";

const fallbackCenter = { lat: 45.5017, lng: -73.5673 };
const simplifiedMapStyles = [
  { featureType: "administrative", elementType: "all", stylers: [{ visibility: "off" }] },
  { featureType: "poi.business", elementType: "all", stylers: [{ visibility: "off" }] },
  { featureType: "poi.medical", elementType: "all", stylers: [{ visibility: "off" }] },
  { featureType: "poi.school", elementType: "all", stylers: [{ visibility: "off" }] },
  { featureType: "transit", elementType: "all", stylers: [{ visibility: "off" }] },
];

function PriceMarker({ car, isActive, onClick }) {
  return (
    <OverlayView
      position={{ lat: car.lat, lng: car.lng }}
      mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
    >
      <button
        onClick={(event) => {
          event.stopPropagation();
          onClick();
        }}
        onMouseDown={(event) => event.stopPropagation()}
        onTouchStart={(event) => event.stopPropagation()}
        className={`cursor-pointer rounded-full border border-gray-200 px-3 py-1.5 text-sm font-bold shadow-md transition-transform hover:scale-105 ${
          isActive ? "bg-gray-900 text-white" : "bg-white text-gray-900"
        }`}
      >
        ${car.pricePerDay}
      </button>
    </OverlayView>
  );
}

function MapPopupCard({ car }) {
  const images = car.images?.length
    ? car.images
    : [car.image || car.photos?.[0]].filter(Boolean);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const currentImage = images[currentImageIndex];
  const listingUrl = `/listings/${car.listingId || car.id}`;
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
      className="group block w-[280px] cursor-pointer overflow-hidden rounded-2xl bg-white shadow-2xl"
      onClick={(event) => event.stopPropagation()}
      onMouseDown={(event) => event.stopPropagation()}
      onTouchStart={(event) => event.stopPropagation()}
    >
      <div className="relative h-[180px] w-full overflow-hidden bg-gray-100">
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
              className="absolute left-2 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-gray-900 opacity-0 shadow-sm transition hover:scale-110 hover:bg-white group-hover:opacity-100"
              aria-label="Previous image"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={handleNextImage}
              className="absolute right-2 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-gray-900 opacity-0 shadow-sm transition hover:scale-110 hover:bg-white group-hover:opacity-100"
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

      <div className="flex flex-col gap-1 p-4">
        <div className="flex w-full items-center gap-3">
          <p className="min-w-0 flex-1 truncate font-semibold text-gray-900">
            {title || car.title || "Vehicle"}
          </p>
          <span className="flex items-center gap-1 text-sm font-medium text-gray-900">
            <Star className="h-4 w-4 fill-gray-900 text-gray-900" />
            {Number(car.rating || 4.9).toFixed(2)}
          </span>
        </div>
        <p className="truncate text-sm text-gray-500">
          {car.details || car.sourceType || "Automatic"}
        </p>
        <p className="mt-1 text-gray-900">
          <span className="font-bold">${car.pricePerDay}</span>
          <span className="font-normal"> / day</span>
        </p>
      </div>
    </a>
  );
}

function ListingPopup({ car }) {
  return (
    <OverlayView
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
    </OverlayView>
  );
}

export default function SearchResultsView({
  cars = [],
  cityLabel = "Montreal",
  searchCenter = null,
  isLoading = false,
}) {
  const [activeId, setActiveId] = useState(null);
  const [isMapFullscreen, setIsMapFullscreen] = useState(false);
  const [selectedCar, setSelectedCar] = useState(null);
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const { isLoaded } = useJsApiLoader({
    id: "google-maps-script",
    googleMapsApiKey: apiKey || "",
    libraries: ["places"],
  });

  const mapCars = useMemo(
    () => cars.filter((c) => Number.isFinite(c.lat) && Number.isFinite(c.lng)),
    [cars]
  );

  const center = useMemo(() => {
    if (
      searchCenter &&
      Number.isFinite(searchCenter.lat) &&
      Number.isFinite(searchCenter.lng)
    ) {
      return { lat: searchCenter.lat, lng: searchCenter.lng };
    }
    if (mapCars.length === 0) return fallbackCenter;
    const latAvg = mapCars.reduce((sum, c) => sum + c.lat, 0) / mapCars.length;
    const lngAvg = mapCars.reduce((sum, c) => sum + c.lng, 0) / mapCars.length;
    return { lat: latAvg, lng: lngAvg };
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
      <div className="flex w-full flex-col md:flex-row">
        <section
          className={`w-full px-4 py-6 sm:px-6 lg:px-8 transition-all duration-300 ${
            isMapFullscreen ? "hidden" : "md:w-[55%] xl:w-[60%]"
          }`}
        >
          <h2 className="mb-6 text-xl font-semibold">
            {isLoading ? "Loading cars..." : `${cars.length} cars in ${cityLabel}`}
          </h2>
          <div className="mb-4 md:hidden">
            <button
              onClick={() => setIsMapFullscreen(true)}
              className="mx-auto flex items-center gap-2 rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium shadow-sm"
            >
              <MapIcon className="h-4 w-4" />
              Show map
            </button>
          </div>
          {isLoading ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              {Array.from({ length: 6 }).map((_, idx) => (
                <div key={idx} className="space-y-3">
                  <div className="aspect-[20/19] animate-pulse rounded-2xl bg-gray-200" />
                  <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200" />
                  <div className="h-4 w-1/2 animate-pulse rounded bg-gray-100" />
                </div>
              ))}
            </div>
          ) : (
            <CarGrid
              cars={cars}
              compact
              distanceById={Object.fromEntries(cars.map((c) => [c.id, c.distanceKm]))}
            />
          )}
        </section>

        <aside
          className={`${
            isMapFullscreen
              ? "block w-full"
              : "hidden md:block md:w-[45%] xl:w-[40%]"
          } transition-all duration-300`}
        >
          <div className="sticky top-[80px] h-[calc(100vh-80px)] overflow-hidden">
            {!apiKey ? (
              <div className="m-4 rounded-xl border border-slate-300 bg-white p-4 text-sm text-slate-700">
                Add `VITE_GOOGLE_MAPS_API_KEY` in `frontend/.env.local` to show map.
              </div>
            ) : !isLoaded ? (
              <div className="m-4 rounded-xl border border-slate-300 bg-white p-4 text-sm text-slate-700">
                Loading map...
              </div>
            ) : (
              <div className="relative h-full w-full">
                <button
                  onClick={() => setIsMapFullscreen((v) => !v)}
                  className="absolute left-1/2 top-4 z-10 -translate-x-1/2 rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium shadow-md"
                >
                  {isMapFullscreen ? (
                    <span className="flex items-center gap-2">
                      <List className="h-4 w-4" />
                      Show list
                    </span>
                  ) : (
                    "Full screen map"
                  )}
                </button>
                <GoogleMap
                  mapContainerStyle={{ width: "100%", height: "100%" }}
                  center={center}
                  zoom={12}
                  onClick={handleMapClick}
                  options={{
                    disableDefaultUI: true,
                    zoomControl: true,
                    clickableIcons: false,
                    styles: simplifiedMapStyles,
                  }}
                >
                  {mapCars.map((car) => (
                    <PriceMarker
                      key={car.id}
                      car={car}
                      isActive={activeId === car.id}
                      onClick={() => {
                        setActiveId(car.id);
                        setSelectedCar(car);
                      }}
                    />
                  ))}

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
