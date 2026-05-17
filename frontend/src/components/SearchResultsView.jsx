import { useMemo, useState } from "react";
import {
  GoogleMap,
  InfoWindow,
  OverlayView,
  useJsApiLoader,
} from "@react-google-maps/api";
import { List, Map as MapIcon } from "lucide-react";
import CarGrid from "./CarGrid";

const fallbackCenter = { lat: 45.5017, lng: -73.5673 };

function PriceMarker({ car, isActive, onClick }) {
  return (
    <OverlayView
      position={{ lat: car.lat, lng: car.lng }}
      mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
    >
      <button
        onClick={onClick}
        className={`cursor-pointer rounded-full border border-gray-200 px-3 py-1.5 text-sm font-bold shadow-md transition-transform hover:scale-105 ${
          isActive ? "bg-gray-900 text-white" : "bg-white text-gray-900"
        }`}
      >
        ${car.pricePerDay}
      </button>
    </OverlayView>
  );
}

export default function SearchResultsView({ cars = [], cityLabel = "Montreal" }) {
  const [activeId, setActiveId] = useState(null);
  const [isMapFullscreen, setIsMapFullscreen] = useState(false);
  const [selectedCar, setSelectedCar] = useState(null);
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const { isLoaded } = useJsApiLoader({
    id: "search-results-map",
    googleMapsApiKey: apiKey || "",
  });

  const mapCars = useMemo(
    () => cars.filter((c) => Number.isFinite(c.lat) && Number.isFinite(c.lng)),
    [cars]
  );

  const center = useMemo(() => {
    if (mapCars.length === 0) return fallbackCenter;
    const latAvg = mapCars.reduce((sum, c) => sum + c.lat, 0) / mapCars.length;
    const lngAvg = mapCars.reduce((sum, c) => sum + c.lng, 0) / mapCars.length;
    return { lat: latAvg, lng: lngAvg };
  }, [mapCars]);

  return (
    <div className="w-full">
      <div className="flex w-full flex-col md:flex-row">
        <section
          className={`w-full px-4 py-6 sm:px-6 lg:px-8 transition-all duration-300 ${
            isMapFullscreen ? "hidden" : "md:w-[55%] xl:w-[60%]"
          }`}
        >
          <h2 className="mb-6 text-xl font-semibold">{cars.length} cars in {cityLabel}</h2>
          <div className="mb-4 md:hidden">
            <button
              onClick={() => setIsMapFullscreen(true)}
              className="mx-auto flex items-center gap-2 rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium shadow-sm"
            >
              <MapIcon className="h-4 w-4" />
              Show map
            </button>
          </div>
          <CarGrid
            cars={cars}
            compact
            distanceById={Object.fromEntries(cars.map((c) => [c.id, c.distanceKm]))}
          />
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
                  onClick={() => setSelectedCar(null)}
                  options={{ disableDefaultUI: true, zoomControl: true }}
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
                    <InfoWindow
                      position={{ lat: selectedCar.lat, lng: selectedCar.lng }}
                      onCloseClick={() => setSelectedCar(null)}
                    >
                      <a
                        href={`/listings/${selectedCar.listingId || selectedCar.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block w-64 overflow-hidden rounded-xl bg-white shadow-xl"
                      >
                        <img
                          src={selectedCar.image || selectedCar.photos?.[0]}
                          alt={selectedCar.title || `${selectedCar.make} ${selectedCar.model}`}
                          className="h-32 w-full object-cover"
                        />
                        <div className="space-y-1 p-3">
                          <p className="text-sm font-semibold text-gray-900">
                            {selectedCar.make || selectedCar.brand} {selectedCar.model}{" "}
                            {selectedCar.year || ""}
                          </p>
                          <p className="text-sm text-gray-600">★ {Number(selectedCar.rating || 4.9).toFixed(2)}</p>
                          <p className="text-sm text-gray-900">
                            <span className="font-semibold">${selectedCar.pricePerDay}</span> / day
                          </p>
                        </div>
                      </a>
                    </InfoWindow>
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
