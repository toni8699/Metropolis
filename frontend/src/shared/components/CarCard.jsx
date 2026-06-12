import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Heart } from "lucide-react";
import { Link } from "react-router-dom";
import ListingRatingLine from "@/features/listings/components/ListingRatingLine";

const fallbackPhoto =
  "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80";

export default function CarCard({ car, distanceKm }) {
  const [isFavorite, setIsFavorite] = useState(Boolean(car.favorite));
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

  return (
    <article className="group">
      <Link to={href} className="block">
        <div className="relative aspect-[4/3] w-full overflow-hidden rounded-xl bg-gray-100">
          <img
            src={carouselImages[currentImageIndex] || fallbackPhoto}
            alt={row1Title}
            className="h-full w-full object-cover transition-transform duration-300 hover:scale-[1.02]"
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
                className="absolute left-2 top-1/2 -translate-y-1/2 flex h-7 w-7 items-center justify-center rounded-full bg-white/90 text-gray-900 shadow-sm transition hover:scale-105 hover:bg-white opacity-0 group-hover:opacity-100"
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
                className="absolute right-2 top-1/2 -translate-y-1/2 flex h-7 w-7 items-center justify-center rounded-full bg-white/90 text-gray-900 shadow-sm transition hover:scale-105 hover:bg-white opacity-0 group-hover:opacity-100"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </>
          )}

          <button
            type="button"
            aria-label="Toggle favorite"
            onClick={(e) => {
              e.preventDefault();
              setIsFavorite((v) => !v);
            }}
            className="absolute top-3 right-3 z-10 rounded-full p-1 hover:scale-110 transition"
          >
            <Heart
              className={`h-6 w-6 transition ${
                isFavorite ? "fill-red-500 text-red-500" : "fill-black/20 text-white stroke-[2.25]"
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

        <div className="mt-3 flex flex-col gap-1">
          <div className="flex items-start justify-between gap-2">
            <p className="truncate text-[15px] font-semibold text-gray-900">{row1Title}</p>
            <div className="shrink-0">
              <ListingRatingLine
                listing={car}
                className="text-[14px] font-normal text-gray-900"
              />
            </div>
          </div>

          <p className="truncate text-[14px] font-light text-gray-500">{details}</p>
          <p className="truncate text-[14px] font-light text-gray-500">{distanceText}</p>

          <p className="mt-1 text-[15px] text-gray-900">
            <span className="font-semibold">${car.pricePerDay}</span>
            <span className="font-normal"> / day</span>
          </p>
        </div>
      </Link>
    </article>
  );
}
