import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Heart } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useSavedListings } from "@/context/SavedListingsContext";
import ListingRatingLine from "@/features/listings/components/ListingRatingLine";

const fallbackPhoto =
  "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80";

export default function CarCard({ car, distanceKm }) {
  const { isAuthenticated } = useAuth();
  const { isSaved, toggleSaved } = useSavedListings();
  const navigate = useNavigate();
  const location = useLocation();
  const listingId = car.listingId || car.id;
  const favorite = isSaved(listingId);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const row1Title = `${car.make || car.brand || "Car"} ${car.model || ""} ${car.year || ""}`.trim();
  const details = car.details || "Automatic • 5 Seats";
  const carouselImages = useMemo(() => {
    const all = Array.isArray(car.images) && car.images.length ? car.images : [];
    if (all.length) return all;
    const fallback = [car.image, car.photos?.[0]].filter(Boolean);
    return fallback.length ? fallback : [fallbackPhoto];
  }, [car.image, car.images, car.photos]);
  const hasCarousel = carouselImages.length > 1;
  const visibleDots = carouselImages.slice(0, 5);

  const handleNextImage = () => {
    if (!hasCarousel) return;
    setCurrentImageIndex((idx) => (idx + 1) % carouselImages.length);
  };

  const handlePrevImage = () => {
    if (!hasCarousel) return;
    setCurrentImageIndex((idx) => (idx - 1 + carouselImages.length) % carouselImages.length);
  };

  const distanceText = useMemo(() => {
    if (car.locationText) return car.locationText;
    if (distanceKm == null) return "Location unavailable";
    return `${distanceKm.toFixed(1)} km away`;
  }, [car.locationText, distanceKm]);

  const href = car.listingId
    ? `/app/listings/${car.listingId}`
    : `/app/listings/${car.id}`;

  const handleFavoriteClick = async (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (!isAuthenticated) {
      const redirectTo = encodeURIComponent(`${location.pathname}${location.search}`);
      navigate(`/login?redirect_to=${redirectTo}`);
      return;
    }
    try {
      await toggleSaved(listingId);
    } catch {
      // ponytail: heart revert handled in context
    }
  };

  return (
    <article className="group rounded-[2rem] border-2 border-black bg-vroom-surface p-3 shadow-neoCard transition-transform hover:-translate-y-2">
      <Link to={href} className="block">
        <div className="relative aspect-[4/3] w-full overflow-hidden rounded-[1.5rem] border-2 border-black bg-vroom-sage">
          <img
            src={carouselImages[currentImageIndex] || fallbackPhoto}
            alt={row1Title}
            className="h-full w-full object-cover transition-transform duration-500 hover:scale-110"
          />

          {hasCarousel && (
            <>
              <button
                type="button"
                aria-label="Previous image"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handlePrevImage();
                }}
                className="absolute left-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border-2 border-black bg-vroom-surface text-black opacity-0 shadow-sm transition group-hover:opacity-100 hover:scale-105"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                aria-label="Next image"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleNextImage();
                }}
                className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border-2 border-black bg-vroom-surface text-black opacity-0 shadow-sm transition group-hover:opacity-100 hover:scale-105"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </>
          )}

          <button
            type="button"
            aria-label={favorite ? "Remove from saved listings" : "Save listing"}
            aria-pressed={favorite}
            onClick={handleFavoriteClick}
            className="absolute right-3 top-3 z-10 rounded-full border-2 border-black bg-white/80 p-1 transition hover:scale-110"
          >
            <Heart
              className={`h-6 w-6 transition ${
                favorite ? "fill-red-500 text-red-500" : "fill-black/20 text-white stroke-[2.25]"
              }`}
            />
          </button>

          {hasCarousel && (
            <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-1.5">
              {visibleDots.map((_, idx) => {
                const active = idx === currentImageIndex % visibleDots.length;
                return (
                  <span
                    key={idx}
                    className={`h-1.5 w-1.5 rounded-full transition ${
                      active ? "bg-white scale-110" : "bg-white/60"
                    }`}
                  />
                );
              })}
            </div>
          )}
        </div>

        <div className="mt-4 flex flex-col gap-1.5">
          <div className="flex items-start justify-between gap-2">
            <p className="truncate text-lg font-extrabold text-black">{row1Title}</p>
            <div className="shrink-0">
              <ListingRatingLine
                listing={car}
                className="text-[14px] font-semibold text-black"
              />
            </div>
          </div>

          <p className="truncate text-[14px] font-semibold text-vroom-muted">{details}</p>
          <p className="truncate text-[14px] font-medium text-vroom-muted2">{distanceText}</p>

          <div className="mt-2 flex items-center justify-between gap-2">
            <p className="text-lg text-black">
              <span className="font-extrabold">${car.pricePerDay}</span>
              <span className="font-semibold text-sm"> / day</span>
            </p>
            <span className="rounded-full border-2 border-black border-b-4 bg-vroom-accent px-4 py-1.5 text-sm font-extrabold text-white transition group-hover:translate-y-[-1px]">
              Book now
            </span>
          </div>
        </div>
      </Link>
    </article>
  );
}
