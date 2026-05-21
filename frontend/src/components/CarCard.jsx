import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Heart, Star } from "lucide-react";
import { Link } from "react-router-dom";

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
        <div className="relative aspect-[20/19] overflow-hidden rounded-2xl">
          <img
            src={carouselImages[currentImageIndex] || fallbackPhoto}
            alt={row1Title}
            className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.02] group-hover:brightness-95"
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
                className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/90 text-gray-900 h-7 w-7 rounded-full flex items-center justify-center shadow-sm hover:scale-105 hover:bg-white transition opacity-0 group-hover:opacity-100"
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
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/90 text-gray-900 h-7 w-7 rounded-full flex items-center justify-center shadow-sm hover:scale-105 hover:bg-white transition opacity-0 group-hover:opacity-100"
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
            className="absolute right-3 top-3 rounded-full p-1 backdrop-blur-sm"
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

        <div className="mt-3 space-y-0.5 leading-tight">
          <div className="flex items-start justify-between gap-2">
            <p className="truncate font-semibold text-gray-900">{row1Title}</p>
            <div className="flex shrink-0 items-center gap-1 text-sm text-gray-900">
              <Star className="h-4 w-4 fill-current" />
              <span>{Number(car.rating ?? 4.9).toFixed(2)}</span>
            </div>
          </div>

          <p className="text-sm text-zinc-500">{details}</p>
          <p className="text-sm text-zinc-500">{distanceText}</p>

          <p className="mt-1 text-gray-900">
            <span className="font-semibold">${car.pricePerDay}</span>
            <span className="font-normal"> / day</span>
          </p>
        </div>
      </Link>
    </article>
  );
}
