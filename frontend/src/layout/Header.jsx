import {
  Globe,
  Mail,
  Menu,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { addDays, format } from "date-fns";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useGoogleMaps } from "@/context/GoogleMapsProvider";
import AuthModal from "@/shared/components/AuthModal";
import UserAvatar from "@/shared/components/UserAvatar";
import UserMenuDropdown from "@/layout/header/UserMenuDropdown";
import CollapsedSearchPill from "@/layout/header/CollapsedSearchPill";
import WhereSuggestionsDropdown from "@/layout/header/WhereSuggestionsDropdown";
import WhenDateDropdown from "@/layout/header/WhenDateDropdown";
import VroomLogo from "@/layout/VroomLogo";
import { defaultDateRangeFromToday, startOfToday } from "@/shared/lib/datePicker";
import { usePlacesAutocomplete } from "@/shared/hooks/usePlacesAutocomplete";
import { resolvePredictionCoordinates } from "@/shared/lib/placesAutocomplete";

export default function Header({ onSearch, onHome }) {
  const navigate = useNavigate();
  const { isAuthenticated, isAdmin, user, logout } = useAuth();
  const canAdmin = isAdmin;
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
  const todayDate = startOfToday();
  const tomorrowDate = addDays(todayDate, 1);
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
    const today = startOfToday();
    const day = today.getDay();
    const daysUntilSaturday = (6 - day + 7) % 7 || 7;
    const saturday = addDays(today, daysUntilSaturday);
    const sunday = addDays(saturday, 1);
    setSelectedRange({ from: saturday, to: sunday });
  };

  const sectionBaseClass =
    "h-full flex flex-col justify-center rounded-full px-5 transition font-semibold";
  const getSectionClass = (section) =>
    activeSection === section
      ? `${sectionBaseClass} bg-[#FCFCE5] shadow-[4px_4px_0px_0px_rgba(24,59,30,0.45)]`
      : `${sectionBaseClass} hover:bg-[#dbe8be]`;

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

      <header className="fixed inset-x-0 top-0 z-50 w-full border-b-4 border-black bg-[#FFFEF0] shadow-md transition-all">
        <div className="flex flex-col gap-4 px-4 py-3 sm:px-5 md:flex-row md:items-center md:justify-between md:px-6 md:py-3.5 lg:px-7 xl:px-8">
          <div className="flex items-center justify-between md:w-auto">
            <Link
              to="/"
              onClick={() => {
                setIsSearchExpanded(false);
                onHome?.();
              }}
              className="flex items-center"
            >
              <VroomLogo />
            </Link>
            <div ref={mobileUserMenuRef} className="relative flex items-center gap-1 md:hidden">
              {isAuthenticated && (
                <Link
                  to="/app/messages"
                  className="rounded-full border-2 border-black bg-[#F8AFA1] p-2 text-[#2D5A27] transition hover:scale-105"
                  aria-label="Messages"
                >
                  <Mail className="h-6 w-6" />
                </Link>
              )}
              <button
                onClick={() => setIsUserMenuOpen((open) => !open)}
                className="flex items-center gap-1.5 rounded-full border-2 border-black bg-[#FCFCE5] p-1 pl-2.5 transition hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                aria-label="User menu"
              >
                <Menu className="h-6 w-6 text-[#2D5A27]" />
                {isAuthenticated ? (
                  <UserAvatar user={user} className="h-9 w-9 text-sm ring-2 ring-[#E34B31]" />
                ) : (
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#FFD166] text-sm font-extrabold text-[#2D5A27]">
                    G
                  </div>
                )}
              </button>
              {isUserMenuOpen && (
                <UserMenuDropdown
                  isAuthenticated={isAuthenticated}
                  user={user}
                  onLogin={() => openAuthModal("login")}
                  onSignup={() => openAuthModal("signup")}
                  onOpenAccount={() => {
                    navigate("/app/account");
                    setIsUserMenuOpen(false);
                  }}
                  onOpenTrips={() => {
                    navigate("/app/trips");
                    setIsUserMenuOpen(false);
                  }}
                  onOpenMessages={() => {
                    navigate("/app/messages");
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
              <div className="relative mx-auto flex h-[4.6rem] w-full max-w-2xl items-center rounded-full border-4 border-black bg-white shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
                <button
                  onClick={() => setActiveSection("where")}
                  className={getSectionClass("where")}
                >
                  <span className="text-sm font-extrabold uppercase text-[#2D5A27]">Where go?</span>
                  <input
                    value={searchQuery}
                    onChange={(event) => {
                      setSearchQuery(event.target.value);
                      setSelectedCoordinates(null);
                    }}
                    placeholder="Search destinations"
                    className="w-44 bg-transparent text-sm text-[#2D5A27] outline-none placeholder:text-[#46634b]"
                  />
                </button>

                <div className="h-8 w-[2px] bg-black" />

                <button
                  onClick={() => setActiveSection("when")}
                  className={getSectionClass("when")}
                >
                  <span className="text-sm font-extrabold uppercase text-[#2D5A27]">Select dates</span>
                  <span className="text-xs text-[#35593b]">{whenLabel}</span>
                </button>

                <button
                  onClick={handleSearch}
                  className="mr-2 flex items-center gap-1.5 rounded-full border-4 border-black border-b-4 border-r-4 bg-[#E34B31] px-4 py-2 text-sm font-extrabold text-white transition hover:scale-110 active:translate-x-1 active:translate-y-1 active:border-0"
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
            <button className="hidden cursor-pointer items-center gap-1.5 rounded-full border-4 border-black border-b-4 border-r-4 bg-[#FCFCE5] px-3 py-1.5 text-xs font-bold transition hover:translate-y-[-1px] active:translate-x-1 active:translate-y-1 active:border-0 md:flex">
              <SlidersHorizontal className="h-4 w-4 text-[#2D5A27]" />
              Filters
            </button>
            <button
              onClick={handleHostClick}
              className="rounded-full border-4 border-black border-b-4 border-r-4 bg-[#E34B31] px-4 py-2 text-sm font-extrabold text-white transition hover:translate-y-[-1px] hover:scale-105 active:translate-x-1 active:translate-y-1 active:border-0"
            >
              {isAdmin ? "Admin dashboard" : "Host your car"}
            </button>
            <button
              className="rounded-full border-2 border-black bg-[#FFD166] p-2.5 hover:scale-105"
              aria-label="Language selector"
            >
              <Globe className="h-5 w-5 text-[#2D5A27]" />
            </button>
            {isAuthenticated && (
              <Link
                to="/app/messages"
                className="rounded-full border-2 border-black bg-[#F8AFA1] p-2.5 text-[#2D5A27] transition hover:scale-105"
                aria-label="Messages"
              >
                <Mail className="h-5 w-5" />
              </Link>
            )}
            <div ref={desktopUserMenuRef} className="relative">
              <button
                onClick={() => setIsUserMenuOpen((open) => !open)}
                className="flex items-center gap-1.5 rounded-full border-2 border-black bg-[#FCFCE5] p-1.5 pl-2.5 transition hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                aria-label="User menu"
              >
                <Menu className="h-6 w-6 text-[#2D5A27]" />
                {isAuthenticated ? (
                  <UserAvatar user={user} className="h-9 w-9 text-sm ring-2 ring-[#E34B31]" />
                ) : (
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#FFD166] text-sm font-extrabold text-[#2D5A27]">
                    G
                  </div>
                )}
              </button>
              {isUserMenuOpen && (
                <UserMenuDropdown
                  isAuthenticated={isAuthenticated}
                  user={user}
                  onLogin={() => openAuthModal("login")}
                  onSignup={() => openAuthModal("signup")}
                  onOpenAccount={() => {
                    navigate("/app/account");
                    setIsUserMenuOpen(false);
                  }}
                  onOpenTrips={() => {
                    navigate("/app/trips");
                    setIsUserMenuOpen(false);
                  }}
                  onOpenMessages={() => {
                    navigate("/app/messages");
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
