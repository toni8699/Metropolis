import {
  CarFront,
  Globe,
  Menu,
  Search,
  SlidersHorizontal,
  UserCircle2,
} from "lucide-react";
import { format } from "date-fns";
import { useJsApiLoader } from "@react-google-maps/api";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AuthModal from "./AuthModal";
import UserMenuDropdown from "./header/UserMenuDropdown";
import CollapsedSearchPill from "./header/CollapsedSearchPill";
import WhereSuggestionsDropdown from "./header/WhereSuggestionsDropdown";
import WhenDateDropdown from "./header/WhenDateDropdown";
import {
  fetchPlacePredictions,
  resolvePredictionCoordinates,
} from "../lib/placesAutocomplete";

export default function Header({ onSearch, onHome }) {
  const navigate = useNavigate();
  const { isAuthenticated, isAdmin, logout } = useAuth();
  const canAdmin = isAdmin;
  const showHostDashboard = isAuthenticated && !isAdmin;
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState("login");
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("where");
  const [location, setLocation] = useState("montreal-core");
  const [searchQuery, setSearchQuery] = useState("montreal-core");
  const [placePredictions, setPlacePredictions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [placesError, setPlacesError] = useState("");
  const [selectedCoordinates, setSelectedCoordinates] = useState(null);
  const [selectedRange, setSelectedRange] = useState();
  const searchContainerRef = useRef(null);
  const geocoderRef = useRef(null);
  const mobileUserMenuRef = useRef(null);
  const desktopUserMenuRef = useRef(null);
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

  useEffect(() => {
    if (!isUserMenuOpen) return undefined;
    const onClickOutside = (event) => {
      const isInsideMobile =
        mobileUserMenuRef.current &&
        mobileUserMenuRef.current.contains(event.target);
      const isInsideDesktop =
        desktopUserMenuRef.current &&
        desktopUserMenuRef.current.contains(event.target);
      if (!isInsideMobile && !isInsideDesktop) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [isUserMenuOpen]);

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
    navigate("/");
  };

  useEffect(() => {
    if (!isPlacesLoaded || !window.google?.maps) return;

    try {
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
    if (!window.google?.maps?.places) {
      setPlacePredictions([]);
      setPlacesError("Location suggestions are not ready yet.");
      return;
    }

    let isCancelled = false;
    const debounceId = window.setTimeout(async () => {
      setIsLoading(true);
      setPlacesError("");
      try {
        const predictions = await fetchPlacePredictions(searchQuery, {
          types: ["geocode"],
        });
        if (!isCancelled) {
          setPlacePredictions(predictions);
        }
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

  const openAuthModal = (mode = "login") => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
    setIsUserMenuOpen(false);
  };

  const handleHostClick = () => {
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }
    if (isAdmin) {
      navigate("/admin");
      return;
    }
    navigate("/host");
  };

  const handleLogout = () => {
    logout();
    setIsUserMenuOpen(false);
    navigate("/");
  };

  const handlePickPrediction = async (prediction, title) => {
    setLocation(title);
    setSearchQuery(title);
    setPlacesError("");
    try {
      const coords = await resolvePredictionCoordinates(prediction);
      setSelectedCoordinates(coords);
    } catch {
      setSelectedCoordinates(null);
    }
    setActiveSection("when");
  };

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
            <div ref={mobileUserMenuRef} className="relative md:hidden">
              <button
                onClick={() => setIsUserMenuOpen((open) => !open)}
                className="flex items-center gap-2 rounded-full border p-1 pl-3 transition hover:shadow-md"
                aria-label="User menu"
              >
                <Menu className="h-5 w-5 text-gray-700" />
                <UserCircle2 className="h-9 w-9 fill-gray-500 text-gray-500" />
              </button>
              {isUserMenuOpen && (
                <UserMenuDropdown
                  isAuthenticated={isAuthenticated}
                  onLogin={() => openAuthModal("login")}
                  onSignup={() => openAuthModal("signup")}
                  onOpenTrips={() => {
                    navigate("/app/trips");
                    setIsUserMenuOpen(false);
                  }}
                  onOpenHostDashboard={() => {
                    navigate("/host/dashboard");
                    setIsUserMenuOpen(false);
                  }}
                  onOpenAdminDashboard={() => {
                    navigate("/admin");
                    setIsUserMenuOpen(false);
                  }}
                  onLogout={handleLogout}
                  showHostDashboard={showHostDashboard}
                  canAdmin={canAdmin}
                />
              )}
            </div>
          </div>

          <div ref={searchContainerRef} className="relative w-full md:w-auto md:px-3">
            {!isSearchExpanded ? (
              <CollapsedSearchPill
                location={location}
                collapsedWhenLabel={collapsedWhenLabel}
                onOpen={() => {
                  setActiveSection("where");
                  setSearchQuery(location);
                  setIsSearchExpanded(true);
                }}
              />
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
                  <WhenDateDropdown
                    todayDate={todayDate}
                    tomorrowDate={tomorrowDate}
                    previewNextSaturday={previewNextSaturday}
                    previewNextSunday={previewNextSunday}
                    setToday={setToday}
                    setTomorrow={setTomorrow}
                    setNextWeekend={setNextWeekend}
                    selectedRange={selectedRange}
                    setSelectedRange={setSelectedRange}
                  />
                )}

                {activeSection === "where" && (
                  <WhereSuggestionsDropdown
                    isLoading={isLoading}
                    placePredictions={placePredictions}
                    placesError={placesError}
                    searchQuery={searchQuery}
                    onPickPrediction={handlePickPrediction}
                  />
                )}
              </div>
            )}
          </div>

          <div className="hidden items-center gap-1 md:flex">
            <button className="hidden cursor-pointer items-center gap-2 rounded-full border border-gray-300 px-5 py-3 text-base font-semibold transition hover:border-gray-900 md:flex">
              <SlidersHorizontal className="h-5 w-5" />
              Filters
            </button>
            <button
              onClick={handleHostClick}
              className="rounded-full px-5 py-3 text-base font-semibold hover:bg-gray-100"
            >
              {isAdmin ? "Admin dashboard" : "Host your car"}
            </button>
            <button
              className="rounded-full p-3 hover:bg-gray-100"
              aria-label="Language selector"
            >
              <Globe className="h-6 w-6 text-gray-700" />
            </button>
            <div ref={desktopUserMenuRef} className="relative">
              <button
                onClick={() => setIsUserMenuOpen((open) => !open)}
                className="flex items-center gap-2 rounded-full border p-2 pl-4 transition hover:shadow-md"
                aria-label="User menu"
              >
                <Menu className="h-5 w-5 text-gray-700" />
                <UserCircle2 className="h-10 w-10 fill-gray-500 text-gray-500" />
              </button>
              {isUserMenuOpen && (
                <UserMenuDropdown
                  isAuthenticated={isAuthenticated}
                  onLogin={() => openAuthModal("login")}
                  onSignup={() => openAuthModal("signup")}
                  onOpenTrips={() => {
                    navigate("/app/trips");
                    setIsUserMenuOpen(false);
                  }}
                  onOpenHostDashboard={() => {
                    navigate("/host/dashboard");
                    setIsUserMenuOpen(false);
                  }}
                  onOpenAdminDashboard={() => {
                    navigate("/admin");
                    setIsUserMenuOpen(false);
                  }}
                  onLogout={handleLogout}
                  showHostDashboard={showHostDashboard}
                  canAdmin={canAdmin}
                />
              )}
            </div>
          </div>
        </div>
      </header>
      <AuthModal
        isOpen={isAuthModalOpen}
        mode={authModalMode}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </>
  );
}
