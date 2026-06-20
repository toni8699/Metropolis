import { Globe, Mail, Search, SlidersHorizontal } from "lucide-react";
import { addDays, format } from "date-fns";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useGoogleMaps } from "@/context/GoogleMapsProvider";
import AuthModal from "@/shared/components/AuthModal";
import HeaderUserMenu from "@/layout/header/HeaderUserMenu";
import CollapsedSearchPill from "@/layout/header/CollapsedSearchPill";
import WhereSuggestionsDropdown from "@/layout/header/WhereSuggestionsDropdown";
import WhenDateDropdown from "@/layout/header/WhenDateDropdown";
import VroomLogo from "@/layout/VroomLogo";
import { defaultDateRangeFromToday, startOfToday } from "@/shared/lib/datePicker";
import { nextWeekendRange } from "@/shared/lib/weekendDates";
import { useClickOutside } from "@/shared/hooks/useClickOutside";
import { usePlacesAutocomplete } from "@/shared/hooks/usePlacesAutocomplete";
import { resolvePredictionCoordinates } from "@/shared/lib/placesAutocomplete";
import { useOptionalBrowseFilters } from "@/features/browse/hooks/useBrowseFilters.jsx";

export default function Header({ onSearch, onHome }) {
  const navigate = useNavigate();
  const { isAuthenticated, isAdmin, user, logout, ensureVerifiedEmail } = useAuth();
  const showHostDashboard = isAuthenticated && !isAdmin;
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState("login");
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("where");
  const [location, setLocation] = useState("montreal-core");
  const [searchQuery, setSearchQuery] = useState("montreal-core");
  const [selectedCoordinates, setSelectedCoordinates] = useState(null);
  const [selectedRange, setSelectedRange] = useState(defaultDateRangeFromToday);
  const searchContainerRef = useRef(null);
  const geocoderRef = useRef(null);
  const mobileUserMenuRef = useRef(null);
  const desktopUserMenuRef = useRef(null);
  const { isLoaded: isPlacesLoaded, loadError: placesLoadError } = useGoogleMaps();
  const {
    predictions: placePredictions,
    isLoading,
    placesError,
    setPlacesError,
  } = usePlacesAutocomplete(searchQuery, {
    enabled: isSearchExpanded && activeSection === "where",
    debounceMs: 300,
    mapsReady: isPlacesLoaded,
    placesLoadError,
  });
  const browseFilters = useOptionalBrowseFilters();

  const closeSearch = useCallback(() => setIsSearchExpanded(false), []);
  const closeMenu = useCallback(() => setIsUserMenuOpen(false), []);
  const toggleMenu = useCallback(() => setIsUserMenuOpen((open) => !open), []);

  useClickOutside(searchContainerRef, closeSearch, isSearchExpanded);

  useEffect(() => {
    if (!isSearchExpanded) return undefined;
    const onEsc = (event) => {
      if (event.key === "Escape") closeSearch();
    };
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, [isSearchExpanded, closeSearch]);

  useEffect(() => {
    if (!isUserMenuOpen) return undefined;
    const onClickOutside = (event) => {
      const inMobile = mobileUserMenuRef.current?.contains(event.target);
      const inDesktop = desktopUserMenuRef.current?.contains(event.target);
      if (!inMobile && !inDesktop) closeMenu();
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [isUserMenuOpen, closeMenu]);

  const whenLabel =
    selectedRange?.from && selectedRange?.to
      ? `${format(selectedRange.from, "MMM d")} - ${format(selectedRange.to, "MMM d")}`
      : "Add dates";
  const collapsedWhenLabel =
    selectedRange?.from && selectedRange?.to ? whenLabel : "Any week";
  const todayDate = startOfToday();
  const tomorrowDate = addDays(todayDate, 1);
  const { saturday: previewNextSaturday, sunday: previewNextSunday } = nextWeekendRange();

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
      pickupDate: selectedRange?.from ? format(selectedRange.from, "yyyy-MM-dd") : "",
      returnDate: selectedRange?.to ? format(selectedRange.to, "yyyy-MM-dd") : "",
      coordinates,
    });
    closeSearch();
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
  }, [isPlacesLoaded, setPlacesError]);

  const setToday = () => {
    const today = startOfToday();
    setSelectedRange({ from: today, to: today });
  };

  const setTomorrow = () => {
    const tomorrow = addDays(startOfToday(), 1);
    setSelectedRange({ from: tomorrow, to: tomorrow });
  };

  const setNextWeekend = () => {
    const { saturday, sunday } = nextWeekendRange();
    setSelectedRange({ from: saturday, to: sunday });
  };

  const sectionBaseClass =
    "h-full flex flex-col justify-center rounded-full px-5 transition font-semibold";
  const getSectionClass = (section) =>
    activeSection === section
      ? `${sectionBaseClass} bg-vroom-surface shadow-neoSm`
      : `${sectionBaseClass} hover:bg-vroom-sage`;

  const openAuthModal = (mode = "login") => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
    closeMenu();
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
    if (!ensureVerifiedEmail()) {
      return;
    }
    navigate("/host");
  };

  const handleLogout = () => {
    logout();
    closeMenu();
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

  const menuProps = {
    isAuthenticated,
    user,
    isUserMenuOpen,
    onToggleMenu: toggleMenu,
    onLogin: () => openAuthModal("login"),
    onSignup: () => openAuthModal("signup"),
    onOpenAccount: () => {
      navigate("/app/account");
      closeMenu();
    },
    onOpenTrips: () => {
      navigate("/app/trips");
      closeMenu();
    },
    onOpenSaved: () => {
      navigate("/app/saved");
      closeMenu();
    },
    onOpenMessages: () => {
      navigate("/app/messages");
      closeMenu();
    },
    onOpenHostDashboard: () => {
      navigate("/host/dashboard");
      closeMenu();
    },
    onOpenAdminDashboard: () => {
      navigate("/admin");
      closeMenu();
    },
    onLogout: handleLogout,
    showHostDashboard,
    isAdmin,
  };

  return (
    <>
      {isSearchExpanded && (
        <div className="fixed inset-0 z-40 bg-black/25" onClick={closeSearch} />
      )}

      <header className="sticky top-0 z-50 w-full border-b-4 border-black bg-vroom-surface shadow-md">
        <div className="container-x flex flex-col gap-4 py-3 md:flex-row md:items-center md:justify-between md:py-3.5">
          <div className="flex items-center justify-between md:w-auto">
            <Link
              to="/"
              onClick={() => {
                closeSearch();
                onHome?.();
              }}
              className="flex items-center"
            >
              <VroomLogo />
            </Link>
            <HeaderUserMenu menuRef={mobileUserMenuRef} variant="mobile" {...menuProps} />
          </div>

          <div ref={searchContainerRef} className="relative w-full md:w-auto md:px-2">
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
              <div className="relative mx-auto flex h-[4.6rem] w-full max-w-2xl items-center rounded-full border-4 border-black bg-white shadow-neo">
                <button
                  type="button"
                  onClick={() => setActiveSection("where")}
                  className={getSectionClass("where")}
                >
                  <span className="text-sm font-extrabold uppercase text-vroom-text">Where go?</span>
                  <input
                    value={searchQuery}
                    onChange={(event) => {
                      setSearchQuery(event.target.value);
                      setSelectedCoordinates(null);
                    }}
                    placeholder="Search destinations"
                    className="w-44 bg-transparent text-sm text-vroom-text outline-none placeholder:text-vroom-muted2"
                  />
                </button>

                <div className="h-8 w-[2px] bg-black" />

                <button
                  type="button"
                  onClick={() => setActiveSection("when")}
                  className={getSectionClass("when")}
                >
                  <span className="text-sm font-extrabold uppercase text-vroom-text">Select dates</span>
                  <span className="text-xs text-vroom-muted">{whenLabel}</span>
                </button>

                <button
                  type="button"
                  onClick={handleSearch}
                  className="neo-btn-primary mr-2 flex items-center gap-1.5 px-4 py-2 text-sm hover:scale-110"
                >
                  <Search className="h-4 w-4" />
                  <span>Go</span>
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

          <div className="hidden items-center gap-2 md:flex">
            {browseFilters ? (
              <button
                type="button"
                onClick={browseFilters.openFilterModal}
                className="neo-btn-secondary relative flex cursor-pointer items-center gap-1.5 px-3 py-1.5 text-xs"
              >
                <SlidersHorizontal className="h-4 w-4 text-vroom-text" />
                Filters
                {browseFilters.filtersActive ? (
                  <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full border border-black bg-vroom-coral px-1 text-[10px] font-bold">
                    !
                  </span>
                ) : null}
              </button>
            ) : null}
            <button type="button" onClick={handleHostClick} className="neo-btn-primary px-4 py-2 text-sm hover:scale-105">
              {isAdmin ? "Admin dashboard" : "Host your car"}
            </button>
            <button
              type="button"
              className="rounded-full border-2 border-black bg-vroom-gold p-2.5 hover:scale-105"
              aria-label="Language selector"
            >
              <Globe className="h-5 w-5 text-vroom-text" />
            </button>
            {isAuthenticated && (
              <Link
                to="/app/messages"
                className="rounded-full border-2 border-black bg-vroom-coral p-2.5 text-vroom-text transition hover:scale-105"
                aria-label="Messages"
              >
                <Mail className="h-5 w-5" />
              </Link>
            )}
            <HeaderUserMenu menuRef={desktopUserMenuRef} variant="desktop" {...menuProps} />
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
