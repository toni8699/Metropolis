import {
  CarFront,
  ChevronLeft,
  ChevronRight,
  Globe,
  MapPin,
  Menu,
  Search,
  SlidersHorizontal,
  UserCircle2,
} from "lucide-react";
import { format } from "date-fns";
import { useJsApiLoader } from "@react-google-maps/api";
import { DayPicker } from "react-day-picker";
import "react-day-picker/style.css";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

export default function Header({ onSearch, onHome }) {
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const [activeSection, setActiveSection] = useState("where");
  const [location, setLocation] = useState("montreal-core");
  const [searchQuery, setSearchQuery] = useState("montreal-core");
  const [placePredictions, setPlacePredictions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [placesError, setPlacesError] = useState("");
  const [selectedCoordinates, setSelectedCoordinates] = useState(null);
  const [selectedRange, setSelectedRange] = useState();
  const searchContainerRef = useRef(null);
  const autocompleteServiceRef = useRef(null);
  const geocoderRef = useRef(null);
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const { isLoaded: isPlacesLoaded, loadError: placesLoadError } = useJsApiLoader({
    id: "google-maps-script",
    googleMapsApiKey: apiKey || "",
    libraries: ["places"],
  });

  useEffect(() => {
    function closeOnClickOutside(event) {
      if (!isSearchExpanded) return;
      if (
        searchContainerRef.current &&
        !searchContainerRef.current.contains(event.target)
      ) {
        setIsSearchExpanded(false);
      }
    }

    function closeOnEsc(event) {
      if (event.key === "Escape") {
        setIsSearchExpanded(false);
      }
    }

    document.addEventListener("mousedown", closeOnClickOutside);
    document.addEventListener("keydown", closeOnEsc);

    return () => {
      document.removeEventListener("mousedown", closeOnClickOutside);
      document.removeEventListener("keydown", closeOnEsc);
    };
  }, [isSearchExpanded]);

  const whenLabel =
    selectedRange?.from && selectedRange?.to
      ? `${format(selectedRange.from, "MMM d")} - ${format(
          selectedRange.to,
          "MMM d",
        )}`
      : "Add dates";
  const collapsedWhenLabel =
    selectedRange?.from && selectedRange?.to ? whenLabel : "Any week";
  const todayDate = new Date();
  const tomorrowDate = new Date(todayDate);
  tomorrowDate.setDate(todayDate.getDate() + 1);
  const previewNextSaturday = new Date(todayDate);
  previewNextSaturday.setDate(
    todayDate.getDate() + (((6 - todayDate.getDay() + 7) % 7) || 7),
  );
  const previewNextSunday = new Date(previewNextSaturday);
  previewNextSunday.setDate(previewNextSaturday.getDate() + 1);

  const geocodeAddress = (address) =>
    new Promise((resolve, reject) => {
      if (!geocoderRef.current) {
        reject(new Error("Geocoder unavailable"));
        return;
      }
      geocoderRef.current.geocode({ address }, (results, status) => {
        if (
          status === "OK" &&
          results?.[0]?.geometry?.location &&
          typeof results[0].geometry.location.lat === "function" &&
          typeof results[0].geometry.location.lng === "function"
        ) {
          const point = results[0].geometry.location;
          resolve({ lat: point.lat(), lng: point.lng() });
          return;
        }
        reject(new Error("Could not resolve address coordinates"));
      });
    });

  const handleSearch = async () => {
    const trimmedLocation = location.trim();
    let coordinates = selectedCoordinates;
    if (!coordinates && trimmedLocation && geocoderRef.current) {
      try {
        coordinates = await geocodeAddress(trimmedLocation);
        setSelectedCoordinates(coordinates);
      } catch {
        coordinates = null;
      }
    }

    onSearch?.({
      location: trimmedLocation,
      pickupDate: selectedRange?.from
        ? format(selectedRange.from, "yyyy-MM-dd")
        : "",
      returnDate: selectedRange?.to ? format(selectedRange.to, "yyyy-MM-dd") : "",
      coordinates,
    });
    setIsSearchExpanded(false);
  };

  useEffect(() => {
    if (!isPlacesLoaded || !window.google?.maps) return;

    try {
      if (!autocompleteServiceRef.current && window.google.maps.places) {
        autocompleteServiceRef.current =
          new window.google.maps.places.AutocompleteService();
      }
      if (!geocoderRef.current) {
        geocoderRef.current = new window.google.maps.Geocoder();
      }
    } catch {
      setPlacesError("Google Places failed to initialize.");
    }
  }, [isPlacesLoaded]);

  useEffect(() => {
    if (!isSearchExpanded || activeSection !== "where") return;
    if (!searchQuery.trim()) {
      setPlacePredictions([]);
      setIsLoading(false);
      setPlacesError("");
      return;
    }
    if (placesLoadError) {
      setPlacePredictions([]);
      setPlacesError("Google Maps failed to load.");
      return;
    }
    if (!autocompleteServiceRef.current) {
      setPlacePredictions([]);
      setPlacesError("Location suggestions are not ready yet.");
      return;
    }

    let isCancelled = false;
    const debounceId = window.setTimeout(async () => {
      setIsLoading(true);
      setPlacesError("");
      try {
        await new Promise((resolve) => {
          autocompleteServiceRef.current.getPlacePredictions(
            {
              input: searchQuery,
              types: ["geocode"],
            },
            (predictions, status) => {
              if (isCancelled) {
                resolve();
                return;
              }
              if (
                status === window.google.maps.places.PlacesServiceStatus.OK &&
                predictions
              ) {
                setPlacePredictions(predictions);
              } else if (
                status ===
                window.google.maps.places.PlacesServiceStatus.ZERO_RESULTS
              ) {
                setPlacePredictions([]);
              } else {
                setPlacePredictions([]);
                setPlacesError("Could not fetch location suggestions.");
              }
              resolve();
            },
          );
        });
      } catch {
        if (!isCancelled) {
          setPlacePredictions([]);
          setPlacesError("Could not fetch location suggestions.");
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }, 300);

    return () => {
      isCancelled = true;
      window.clearTimeout(debounceId);
    };
  }, [searchQuery, isSearchExpanded, activeSection, placesLoadError]);

  const geocodePlace = (placeId) =>
    new Promise((resolve, reject) => {
      if (!geocoderRef.current) {
        reject(new Error("Geocoder unavailable"));
        return;
      }
      geocoderRef.current.geocode({ placeId }, (results, status) => {
        if (
          status === "OK" &&
          results?.[0]?.geometry?.location &&
          typeof results[0].geometry.location.lat === "function" &&
          typeof results[0].geometry.location.lng === "function"
        ) {
          const point = results[0].geometry.location;
          resolve({ lat: point.lat(), lng: point.lng() });
          return;
        }
        reject(new Error("Could not resolve place coordinates"));
      });
    });

  const setToday = () => {
    const today = new Date();
    setSelectedRange({ from: today, to: today });
  };

  const setTomorrow = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setSelectedRange({ from: tomorrow, to: tomorrow });
  };

  const setNextWeekend = () => {
    const today = new Date();
    const day = today.getDay();
    const daysUntilSaturday = (6 - day + 7) % 7 || 7;
    const saturday = new Date(today);
    saturday.setDate(today.getDate() + daysUntilSaturday);
    const sunday = new Date(saturday);
    sunday.setDate(saturday.getDate() + 1);
    setSelectedRange({ from: saturday, to: sunday });
  };

  const sectionBaseClass =
    "h-full flex flex-col justify-center rounded-full px-6 transition";
  const getSectionClass = (section) =>
    activeSection === section
      ? `${sectionBaseClass} bg-white shadow-md`
      : `${sectionBaseClass} hover:bg-gray-200`;

  return (
    <>
      {isSearchExpanded && (
        <div
          className="fixed inset-0 bg-black/25 z-40"
          onClick={() => setIsSearchExpanded(false)}
        />
      )}

      <header className="fixed inset-x-0 top-0 z-50 w-full border-b bg-white transition-all">
        <div className="flex flex-col gap-5 px-4 py-5 sm:px-6 md:flex-row md:items-center md:justify-between md:px-10 md:py-6 lg:px-12 xl:px-20">
          <div className="flex items-center justify-between md:w-auto">
            <Link
              to="/"
              onClick={() => {
                setIsSearchExpanded(false);
                onHome?.();
              }}
              className="flex items-center gap-3 text-indigo-600"
            >
              <CarFront className="h-12 w-12" />
              <span className="text-4xl font-extrabold">DriveBnb</span>
            </Link>
            <button
              className="flex items-center gap-2 rounded-full border p-1 pl-3 transition hover:shadow-md md:hidden"
              aria-label="User menu"
            >
              <Menu className="h-5 w-5 text-gray-700" />
              <UserCircle2 className="h-9 w-9 fill-gray-500 text-gray-500" />
            </button>
          </div>

          <div ref={searchContainerRef} className="relative w-full md:w-auto md:px-3">
            {!isSearchExpanded ? (
              <button
                onClick={() => {
                  setActiveSection("where");
                  setSearchQuery(location);
                  setIsSearchExpanded(true);
                }}
                className="mx-auto flex h-20 w-full max-w-xl cursor-pointer items-center rounded-full border border-gray-300 bg-white py-3 pl-6 pr-3 shadow-sm transition hover:shadow-md md:max-w-2xl"
              >
                <div className="min-w-[150px] flex-1 px-3 text-center text-xl font-bold text-gray-900 sm:min-w-[260px]">
                  {location || "Anywhere"}
                </div>
                <div className="mx-2 h-6 w-[1px] flex-shrink-0 bg-gray-300" />
                <div className="min-w-[150px] flex-1 px-3 text-center text-lg text-gray-700 sm:min-w-[280px]">
                  {collapsedWhenLabel}
                </div>
                <div className="ml-2 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white">
                  <Search className="h-6 w-6" strokeWidth={3} />
                </div>
              </button>
            ) : (
              <div className="relative mx-auto flex h-24 w-full max-w-3xl items-center rounded-full border border-gray-200 bg-gray-100 shadow-sm">
                <button
                  onClick={() => setActiveSection("where")}
                  className={getSectionClass("where")}
                >
                  <span className="text-sm font-bold">Where</span>
                  <input
                    value={searchQuery}
                    onChange={(event) => {
                      setSearchQuery(event.target.value);
                      setSelectedCoordinates(null);
                    }}
                    placeholder="Search destinations"
                    className="w-64 bg-transparent text-lg text-gray-700 outline-none"
                  />
                </button>

                <button
                  onClick={() => setActiveSection("when")}
                  className={getSectionClass("when")}
                >
                  <span className="text-sm font-bold">When</span>
                  <span className="text-lg text-gray-700">{whenLabel}</span>
                </button>

                <button
                  onClick={handleSearch}
                  className="mr-2 flex items-center gap-2 rounded-full bg-indigo-600 px-7 py-4 text-lg font-semibold text-white transition hover:bg-indigo-700"
                >
                  <Search className="h-5 w-5" />
                  <span>Search</span>
                </button>

                {activeSection === "when" && (
                  <div className="absolute top-[80px] left-1/2 z-50 flex w-[700px] -translate-x-1/2 gap-8 rounded-[2rem] border border-gray-200 bg-white p-8 shadow-2xl">
                    <div className="flex w-1/3 flex-col gap-4">
                      <button
                        onClick={setToday}
                        className="cursor-pointer rounded-2xl border border-gray-200 p-4 text-left transition hover:border-gray-900"
                      >
                        <p className="text-sm font-semibold text-gray-900">Today</p>
                        <p className="text-sm text-gray-500">
                          {format(todayDate, "EEE, MMM d")}
                        </p>
                      </button>
                      <button
                        onClick={setTomorrow}
                        className="cursor-pointer rounded-2xl border border-gray-200 p-4 text-left transition hover:border-gray-900"
                      >
                        <p className="text-sm font-semibold text-gray-900">
                          Tomorrow
                        </p>
                        <p className="text-sm text-gray-500">
                          {format(tomorrowDate, "EEE, MMM d")}
                        </p>
                      </button>
                      <button
                        onClick={setNextWeekend}
                        className="cursor-pointer rounded-2xl border border-gray-200 p-4 text-left transition hover:border-gray-900"
                      >
                        <p className="text-sm font-semibold text-gray-900">
                          Next weekend
                        </p>
                        <p className="text-sm text-gray-500">
                          {format(previewNextSaturday, "MMM d")} -{" "}
                          {format(previewNextSunday, "MMM d")}
                        </p>
                      </button>
                    </div>

                    <div className="w-2/3">
                      <DayPicker
                        mode="range"
                        numberOfMonths={2}
                        selected={selectedRange}
                        onSelect={setSelectedRange}
                        className="rdp-airbnb"
                        classNames={{
                          month_caption: "pb-4 text-center text-lg font-semibold",
                          weekdays: "mb-3",
                          weekday:
                            "text-xs font-medium text-gray-400 uppercase tracking-wide",
                          day: "h-12 w-12 p-0",
                          day_button:
                            "h-12 w-12 rounded-full flex items-center justify-center font-medium border border-transparent hover:border-gray-900",
                          selected: "bg-gray-900 text-white rounded-full border-gray-900",
                          range_start:
                            "bg-gray-900 text-white rounded-full border-gray-900",
                          range_end:
                            "bg-gray-900 text-white rounded-full border-gray-900",
                          range_middle:
                            "bg-gray-100 text-gray-900 rounded-none border-transparent",
                        }}
                        components={{
                          Chevron: ({ orientation, ...props }) =>
                            orientation === "left" ? (
                              <ChevronLeft {...props} className="h-5 w-5" />
                            ) : (
                              <ChevronRight {...props} className="h-5 w-5" />
                            ),
                        }}
                      />
                    </div>
                  </div>
                )}

                {activeSection === "where" && (
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
                              onClick={async () => {
                                setLocation(title);
                                setSearchQuery(title);
                                setPlacesError("");
                                try {
                                  const coords = await geocodePlace(
                                    prediction.place_id,
                                  );
                                  setSelectedCoordinates(coords);
                                } catch {
                                  setSelectedCoordinates(null);
                                }
                                setActiveSection("when");
                              }}
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
                      <p className="px-2 py-6 text-center text-sm text-red-500">
                        {placesError}
                      </p>
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
                )}
              </div>
            )}
          </div>

          <div className="hidden items-center gap-1 md:flex">
            <button className="hidden cursor-pointer items-center gap-2 rounded-full border border-gray-300 px-5 py-3 text-base font-semibold transition hover:border-gray-900 md:flex">
              <SlidersHorizontal className="h-5 w-5" />
              Filters
            </button>
            <button className="rounded-full px-5 py-3 text-base font-semibold hover:bg-gray-100">
              Host your car
            </button>
            <button
              className="rounded-full p-3 hover:bg-gray-100"
              aria-label="Language selector"
            >
              <Globe className="h-6 w-6 text-gray-700" />
            </button>
            <button
              className="flex items-center gap-2 rounded-full border p-2 pl-4 transition hover:shadow-md"
              aria-label="User menu"
            >
              <Menu className="h-5 w-5 text-gray-700" />
              <UserCircle2 className="h-10 w-10 fill-gray-500 text-gray-500" />
            </button>
          </div>
        </div>
      </header>
    </>
  );
}
